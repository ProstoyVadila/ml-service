import io
import logging
from enum import IntEnum
from typing import Any

import httpx
from PIL import Image

from ml_service.domains.ocr.base import BaseOCRHandler, OCRResult
from ml_service.utils.retry import Retry

retry = Retry()


# TODO(vadim): Add support for both ocr.space api engines in the chain


class OCRExitCode(IntEnum):
    """
    1: Parsed Successfully (Image / All pages parsed successfully)
    2: Parsed Partially (Only few pages out of all the pages parsed successfully)
    3: Image / All the PDF pages failed parsing (This happens mainly because the OCR engine fails to parse an image)
    4: Error occurred when attempting to parse (This happens when a fatal error occurs during parsing )
    """

    PARSED_SUCCESSFULLY = 1
    PARSED_PARTIALLY = 2
    FAILED_PARSING = 3
    ERROR_OCCURRED = 4


class OCRSpaceAPIHandler(BaseOCRHandler):
    """
    OCR handler for the OCR_SPACE API.
    https://ocr.space/OCRAPI
    """

    def __init__(
        self,
        api_key: str,
        next_handler: BaseOCRHandler | None = None,
        timeout: float | None = None,
    ) -> None:
        super().__init__(next_handler=next_handler, timeout=timeout)
        self.url = "https://api.ocr.space/parse/image"
        self.api_key = api_key
        self.limit_per_month = 25000
        self.max_size = 1 * 1024 * 1024
        self.httpx_timeout = httpx.Timeout(timeout) if timeout else None

    # TODO(vadim): Implement request per month limit checking using sqlite or cache or similar
    def should_skip(self, image: Image.Image) -> bool:
        """
        Determines if the image should be skipped based on its size.
        If the image is larger than 1 MB, it will be skipped.
        """
        with io.BytesIO() as buffer:
            image.save(buffer, format="PNG")
            size = buffer.tell()
            return size > self.max_size

    @property
    def _client(self) -> httpx.AsyncClient:
        """
        Returns an HTTP client for making requests to the OCR_SPACE API.
        """
        return (
            httpx.AsyncClient(timeout=self.httpx_timeout)
            if self.timeout
            else httpx.AsyncClient()
        )

    @retry(
        n_times=4,
        sleep_duration=0.7,
        increasing=True,
        allowed_exceptions=(
            httpx.RequestError,
            httpx.HTTPError,
        ),
    )
    async def _do_request(self, image: Image.Image) -> Any:
        """
        Sends the image to the OCR_SPACE API and returns the OCR result.
        """

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        files = {
            "file": ("image.png", buffer, "image/png"),
        }
        payload = {
            "apikey": self.api_key,
            "language": "rus",
            "filetype": "png",
        }

        async with self._client as client:
            response = await client.post(self.url, data=payload, files=files)
            logging.debug(f"OCR_SPACE API response status: {response.status_code}.")
            buffer.close()
            response.raise_for_status()
            return response.json()

    async def _process_image(self, image: Image.Image) -> OCRResult:
        try:
            data = await self._do_request(image)
            logging.debug(f"OCR_SPACE API response: {data}")

            exit_code = OCRExitCode(data.get("OCRExitCode", 4))
            if exit_code != OCRExitCode.PARSED_SUCCESSFULLY:
                error_message = data.get("ErrorMessage", "Unknown error") + data.get(
                    "ErrorDetails", ""
                )
                logging.error(
                    f"OCR_SPACE API failed with exit code {exit_code.name}: {error_message}"
                )
                return self.get_empty_result(error=error_message)

            parsed_results = data.get("ParsedResults", [])
            if not parsed_results:
                error_message = data.get(
                    "ErrorMessage", "No parsed results returned by OCR_SPACE API"
                )
                logging.error(
                    f"OCR_SPACE API returned no parsed results: {error_message}"
                )
                return self.get_empty_result(error=error_message)

            parsed_result = parsed_results[0]
            text: str = parsed_result.get("ParsedText", "")
            if not text.strip():
                error_message = "Empty parsed text returned by OCR_SPACE API"
                logging.error(error_message)
                return self.get_empty_result(error=error_message)
            text = text.replace("\r", "").replace("\n", "").strip()

            confidence = self.estimate_basic_confidence(text, image)
            return OCRResult(text=text, confidence=confidence, engine=self.name)

        except httpx.HTTPError as error:
            logging.error(f"Request to OCR_SPACE API failed: {error}")
            return self.get_empty_result(error=error)

        except Exception as error:
            logging.error(f"Error processing image with OCR_SPACE API: {error}")
            return self.get_empty_result(error=error)
