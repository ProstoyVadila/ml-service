from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any


class ExtractorSourceType(StrEnum):
    LOCAL = auto()
    EXTERNAL_API = auto()
    # EXTERNAL_OUR = auto()


@dataclass
class ExtractorSource:
    name: str  # e.g. "phi-2" or "deepseek"
    type: ExtractorSourceType


@dataclass
class ExtractionField:
    field: str
    value: str
    confidence: float
    source: ExtractorSource
    error: str | Exception | None = None


@dataclass
class ExtractionResult:
    content: list[ExtractionField] | None
    confidence: float
    source: ExtractorSource
    data: dict[str, Any] | None = None  # full model response if any
    error: str | Exception | None = None


class BaseFieldExtractor(ABC):
    """
    This is an abstract class for a single field extractor.
    """

    field: str

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    @abstractmethod
    def source(self) -> ExtractorSource:
        raise NotImplementedError

    @abstractmethod
    def extract(self, text: str) -> ExtractionField:
        """
        This method extract one field from text
        """
        raise NotImplementedError


class BaseMultiFieldExtractor(ABC):
    """
    This is an abstract class for an extractor which extracts all field at once.
    """

    fields: list[str]

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    @abstractmethod
    def source(self) -> ExtractorSource:
        raise NotImplementedError

    @abstractmethod
    def extract_all(self, text: str) -> ExtractionResult:
        """
        This method extract all fields from text
        """
        raise NotImplementedError
