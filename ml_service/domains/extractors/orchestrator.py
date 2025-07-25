import logging
import time

from ml_service.domains.extractors.base import (
    ExtractionResult,
    ExtractorSource,
    ExtractorSourceType,
)
from ml_service.domains.extractors.strategies import BaseOrchestratorStrategy


class ExtractorOrchestrator:
    def __init__(self, strategy: BaseOrchestratorStrategy | None = None) -> None:
        self.strategy = strategy

    def set_strategy(self, strategy: BaseOrchestratorStrategy) -> None:
        self.strategy = strategy

    def run(self, text: str) -> ExtractionResult:
        if not self.strategy:
            raise ValueError("No strategy set for ExtractorOrchestrator")

        logging.info(f"[Orchestrator] Running strategy: {self.strategy.name}")
        start = time.time()

        try:
            result = self.strategy.run(text)
            elapsed = time.time() - start
            logging.info(
                f"[Orchestrator] Strategy {self.strategy.name} completed in {elapsed:.2f}s"
            )
            return result

        except Exception as e:
            logging.exception(
                f"[Orchestrator] Strategy {self.strategy.name} failed with exception: {e}"
            )
            source = self.strategy._extractors[0].source
            return ExtractionResult(
                content=None,
                confidence=0.0,
                source=source
                if source
                else ExtractorSource("none", ExtractorSourceType.LOCAL),
                error=e,
                data=None,
            )
