from ml_service.domains.extractors.base import (
    BaseFieldExtractor,
    BaseMultiFieldExtractor,
    ExtractionField,
    ExtractionResult,
    ExtractorSource,
)


class FieldToMultiAdapter(BaseMultiFieldExtractor):
    def __init__(self, extractors: list[BaseFieldExtractor]) -> None:
        self.extractors = extractors
        self.fields = [e.field for e in extractors]
        self._cache: dict[str, list[ExtractionField]] = {}

    @property
    def source(self) -> ExtractorSource:
        return self.extractors[0].source  # предполагаем единый источник

    def extract_all(self, text: str) -> ExtractionResult:
        if text in self._cache:
            cached_fields = self._cache[text]
        else:
            cached_fields = [e.extract(text) for e in self.extractors]
            self._cache[text] = cached_fields

        avg_conf = (
            sum(f.confidence for f in cached_fields) / len(cached_fields)
            if cached_fields
            else 0.0
        )
        return ExtractionResult(
            content=cached_fields, confidence=avg_conf, source=self.source, error=None
        )
