import logging

import pytesseract
from PIL import Image
from pytesseract import Output

from ml_service.domains.ocr.base import BaseOCRHandler, OCRResult


class TesseractOCRHandler(BaseOCRHandler):
    def __init__(
        self,
        lang: str = "rus+eng",
        next_handler: BaseOCRHandler | None = None,
        timeout: float | None = None,
    ) -> None:
        super().__init__(next_handler=next_handler, timeout=timeout)
        self.lang = lang

    def _process_image(self, image: Image.Image) -> OCRResult:
        try:
            data = pytesseract.image_to_data(
                image, lang=self.lang, output_type=Output.DICT
            )

            texts = data.get("text", [])
            confs = data.get("conf", [])

            valid_confidences = [float(conf) for conf in confs if conf != "-1"]
            text_fragments = [text for text in texts if text.strip()]

            if not text_fragments:
                error_msg = "Tesseract returned no valid text."
                logging.warning(error_msg)
                return self.get_empty_result(error=error_msg)

            full_text = (
                " ".join(text_fragments).replace("\r", "").replace("\n", "").strip()
            )
            confidence = (
                sum(valid_confidences) / len(valid_confidences) / 100.0
                if valid_confidences
                else 0.0
            )

            return OCRResult(text=full_text, confidence=confidence, engine=self.name)

        except Exception as error:
            logging.error(f"Error processing image with Tesseract: {error}")
            return self.get_empty_result(error=error)
