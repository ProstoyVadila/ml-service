import logging
from io import BytesIO

import easyocr
from PIL import Image

from ml_service.domains.ocr.base import BaseOCRHandler, OCRResult

EASYOCR_ITEM_LENGTH = 3


class EasyOCRHandler(BaseOCRHandler):
    def __init__(
        self,
        use_gpu: bool = False,
        languages: list[str] = ["ru", "en"],
        next_handler: BaseOCRHandler | None = None,
        timeout: float | None = None,
    ) -> None:
        super().__init__(next_handler=next_handler, timeout=timeout)
        self.languages = languages
        self.reader = easyocr.Reader(languages, gpu=use_gpu)

    def _process_image(self, image: Image.Image) -> OCRResult:
        try:
            with BytesIO() as buffer:
                image.save(buffer, format="PNG")
                buffer.seek(0)
                results = self.reader.readtext(
                    buffer.getvalue(), detail=1, paragraph=False
                )

            if not results or not isinstance(results, list):
                error_msg = "No text detected or invalid result format from EasyOCR."
                logging.error(error_msg)
                return self.get_empty_result(error=error_msg)

            text_parts = []
            confidences = []

            for item in results:
                if not isinstance(item, list | tuple):
                    continue
                if (
                    len(item) >= EASYOCR_ITEM_LENGTH
                    and isinstance(item[1], str)
                    and isinstance(item[2], float)
                ):
                    text_parts.append(item[1])
                    confidences.append(item[2])

            if not text_parts:
                error_msg = "No valid text blocks found in EasyOCR result."
                logging.warning(error_msg)
                return self.get_empty_result(error=error_msg)

            text = " ".join(text_parts).replace("\r", "").replace("\n", "").strip()
            confidence = sum(confidences) / len(confidences)

            return OCRResult(text=text, confidence=confidence, engine=self.name)

        except Exception as error:
            logging.error(f"Error processing image with EasyOCR: {error}")
            return self.get_empty_result(error=error)
