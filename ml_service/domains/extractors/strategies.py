from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

from ml_service.domains.extractors.adapter import FieldToMultiAdapter
from ml_service.domains.extractors.base import (
    BaseFieldExtractor,
    BaseMultiFieldExtractor,
    ExtractionResult,
    ExtractorSource,
    ExtractorSourceType,
)

NONE_SOURCE = ExtractorSource("none", ExtractorSourceType.LOCAL)


class BaseOrchestratorStrategy(ABC):
    def __init__(
        self,
        field_extractors: list[BaseFieldExtractor | BaseMultiFieldExtractor],
        max_workers: int = 1,  # default single-threaded
    ) -> None:
        self._raw = field_extractors
        self._extractors = self._adapt(self._raw)
        self.max_workers = max_workers

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def _adapt(
        self, extractors: list[BaseFieldExtractor | BaseMultiFieldExtractor]
    ) -> list[BaseMultiFieldExtractor]:
        grouped: dict[tuple[str, str], list[BaseFieldExtractor]] = {}
        result: list[BaseMultiFieldExtractor] = []

        for e in extractors:
            if isinstance(e, BaseMultiFieldExtractor):
                result.append(e)
            elif isinstance(e, BaseFieldExtractor):
                key = (e.source.name, e.source.type)
                grouped.setdefault(key, []).append(e)
            else:
                raise TypeError(f"Unknown extractor type: {type(e)}")

        for group in grouped.values():
            result.append(FieldToMultiAdapter(group))

        return result

    @abstractmethod
    def run(self, text: str) -> ExtractionResult:
        raise NotImplementedError


class LocalOnlyStrategy(BaseOrchestratorStrategy):
    def run(self, text: str) -> ExtractionResult:
        for extractor in self._extractors:
            if extractor.source.type == ExtractorSourceType.LOCAL:
                result = extractor.extract_all(text)
                if result.confidence > 0:
                    return result
        return ExtractionResult([], 0.0, NONE_SOURCE)


class ExternalOnlyStrategy(BaseOrchestratorStrategy):
    def run(self, text: str) -> ExtractionResult:
        for extractor in self._extractors:
            if extractor.source.type == ExtractorSourceType.EXTERNAL_API:
                result = extractor.extract_all(text)
                if result.confidence > 0:
                    return result
        return ExtractionResult([], 0.0, NONE_SOURCE)


class ExternalAsBackupStrategy(BaseOrchestratorStrategy):
    def run(self, text: str) -> ExtractionResult:
        local_extractors = [
            e for e in self._extractors if e.source.type == ExtractorSourceType.LOCAL
        ]
        external_extractors = [
            e
            for e in self._extractors
            if e.source.type == ExtractorSourceType.EXTERNAL_API
        ]

        for extractor in local_extractors:
            result = extractor.extract_all(text)
            if result.confidence > 0:
                return result

        for extractor in external_extractors:
            result = extractor.extract_all(text)
            if result.confidence > 0:
                return result

        return ExtractionResult([], 0.0, NONE_SOURCE)


class AllExtractorsStrategy(BaseOrchestratorStrategy):
    def run(self, text: str) -> ExtractionResult:
        if self.max_workers > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(e.extract_all, text) for e in self._extractors
                ]
                results = [f.result() for f in futures]
        else:
            results = [e.extract_all(text) for e in self._extractors]

        return self._merge_best_confidence(results)

    def _merge_best_confidence(
        self, results: list[ExtractionResult]
    ) -> ExtractionResult:
        if not results:
            return ExtractionResult([], 0.0, NONE_SOURCE)

        best = max(results, key=lambda r: r.confidence, default=None)
        return best if best else ExtractionResult([], 0.0, NONE_SOURCE)
