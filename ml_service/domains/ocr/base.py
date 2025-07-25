import concurrent.futures
import logging
import re
from abc import ABC, abstractmethod
from typing import Callable, ParamSpec

from PIL import Image

P = ParamSpec("P")

CONFIDENCE_THRESHOLD = 0.6  # Default confidence threshold for OCR results
IMPORTANT_KEYWORDS = {
    "масло",
    "фильтр",
    "замена",
    "ремонт",
    "свеча",
    "руб",
    "дата",
    "работы",
    "пробег",
    "топливо",
    "колодки",
    "тормоза",
    "аккумулятор",
    "замена масла",
    "замена фильтра",
    "замена свечей",
    "техническое обслуживание",
    "ТО",
    "тех",
    "обслуживание",
    "сервис",
    "обслуживание",
    "ремонт двигателя",
    "ремонт трансмиссии",
    "ремонт подвески",
    "ремонт тормозов",
    "замена колодок",
    "замена тормозов",
    "замена аккумулятора",
    "замена жидкости",
    "замена масла в двигателе",
}
NOISE_THRESHOLD = 5
DENSITY_THRESHOLD = 0.001


class OCRResult:
    def __init__(
        self, text: str, confidence: float, engine: str, error: Exception | None = None
    ) -> None:
        self.text = text
        self.confidence = confidence
        self.engine = engine
        self.error = error

    def __repr__(self) -> str:
        return f"OCRResult(confidence={self.confidence:.2f}, engine={self.engine})"


class BaseOCRHandler(ABC):
    def __init__(
        self, next_handler: "BaseOCRHandler | None" = None, timeout: float | None = None
    ) -> None:
        self.next_handler = next_handler
        self.timeout = timeout

    @property
    def name(self) -> str:
        """
        Returns the name of the OCR handler.
        """
        return self.__class__.__name__

    def get_empty_result(self, error: str | Exception | None = None) -> OCRResult:
        error = (
            error
            if isinstance(error, Exception)
            else Exception(error)
            if error
            else None
        )
        return OCRResult(text="", confidence=0.0, engine=self.name, error=error)

    def run_with_timeout(
        self, func: Callable[P, OCRResult], *args: P.args, **kwargs: P.kwargs
    ) -> OCRResult | None:
        """
        Runs the given function with a timeout using concurrent futures.
        If the function does not complete within the timeout, it will return None.
        If an exception occurs, it will be logged and None will be returned.
        """
        if not self.timeout:
            return func(*args, **kwargs)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                result = future.result(timeout=self.timeout)
                return result
            except concurrent.futures.TimeoutError:
                logging.warning(
                    f"OCR {self.name} processing timed out after {self.timeout} seconds."
                )
                return None
            except Exception as e:
                logging.error(f"Error in OCR processing: {e}.")
                return None

    def should_skip(self, image: Image.Image) -> bool:
        """
        Override this method in subclasses to implement specific skipping criteria.
        False by default.
        """
        return False

    def can_accept(self, result: OCRResult) -> bool:
        """
        Determines if the handler can accept the result based on its confidence.
        Override this method in subclasses to implement specific acceptance criteria.
        """
        if result.error:
            logging.error(f"OCR {self.name} encountered an error: {result.error}.")
            return False
        return result.confidence >= CONFIDENCE_THRESHOLD

    @abstractmethod
    def _process_image(self, image: Image.Image) -> OCRResult:
        """
        Abstract method to process the image and return an OCRResult.
        Subclasses must implement this method.
        """
        pass

    def process(self, image: Image.Image) -> OCRResult:
        """
        Processes the image using the OCR handler.
        If the image should be skipped, it will pass the image to the next handler if available.
        If the result is accepted, it will return the result.
        If the result is rejected, it will pass the image to the next handler if available.
        If no next handler is available, it will return an empty OCRResult.
        """
        if self.should_skip(image):
            logging.warning(f"OCR {self.name} skipping image.")
            if self.next_handler:
                logging.info(
                    f"OCR {self.name} passing image to next handler: {self.next_handler.name}"
                )
                return self.next_handler.process(image)
            else:
                logging.error(
                    f"OCR {self.name} has no next handler to pass the image to."
                )
                return OCRResult(text="", confidence=0.0, engine=self.name)

        result = self.run_with_timeout(self._process_image, image)
        if result and self.can_accept(result):
            logging.debug(f"OCR {self.name} accepted result: {result}")
            return result
        elif self.next_handler:
            logging.warning(f"OCR {self.name} rejected result: {result}")
            logging.info(
                f"OCR {self.name} passing result to next handler: {self.next_handler.name}"
            )
            return self.next_handler.process(image)
        else:
            logging.error(f"OCR {self.name} has no next handler to pass the result to.")
            return OCRResult(
                text="",
                confidence=0.0,
                engine=self.name,
                error=Exception("No next handler available."),
            )

    def estimate_basic_confidence(self, text: str, image: Image.Image) -> float:
        """
        Estimates the basic confidence of the OCR result based on the length of the text.
        This is a placeholder method and can be overridden in subclasses for more complex logic.
        """
        text = text.strip()
        if not text:
            return 0.0

        # Basic confidence based on text length
        confidence = min(len(text) / 100, 0.7)

        # bonus for important keywords
        bonus = 0.05 * sum(
            1 for word in text.lower().split() if word in IMPORTANT_KEYWORDS
        )

        # check date
        if re.search(r"\d{2}[./-]\d{2}[./-]\d{2,4}", text):
            bonus += 0.2

        # noise
        if sum(c in "@#$%^&*~" for c in text) > NOISE_THRESHOLD:
            confidence *= 0.5

        # check for density of text in the image
        density = len(text) / (image.width * image.height)
        if density < DENSITY_THRESHOLD:
            confidence *= 0.5

        logging.debug(
            f"Estimated basic confidence for OCR result: {confidence:.2f}"
            f" (text length: {len(text)}, bonus: {bonus:.2f})"
        )
        return min(confidence + bonus, 1.0)
