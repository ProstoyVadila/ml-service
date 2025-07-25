from typing import Any

from autocare.ml.ocr.base import BaseOCRHandler


class OCRChainFactory:
    def __init__(
        self,
        handlers: list[tuple[type[BaseOCRHandler], dict[str, Any]]] | None = None,
        default_timeout: float | None = None,
    ) -> None:
        self.handlers = handlers if handlers else []
        self.default_timeout = default_timeout

    def add_ocr(
        self, handler_class: type[BaseOCRHandler], **kwargs: Any
    ) -> "OCRChainFactory":
        self.handlers.append((handler_class, kwargs))
        return self

    def create_chain(self) -> BaseOCRHandler:
        chain = None
        for handler_class, kwargs in reversed(self.handlers):
            timout = kwargs.pop("timeout", self.default_timeout)
            chain = handler_class(next_handler=chain, timeout=timout, **kwargs)
        if chain is None:
            raise ValueError("No handlers have been added to the chain.")
        return chain
