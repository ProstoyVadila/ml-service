import json
import logging

from ml_service.domains.extractors.base import (
    BaseMultiFieldExtractor,
    ExtractionField,
    ExtractionResult,
    ExtractorSource,
    ExtractorSourceType,
)
from ml_service.domains.llm.base import LLMClient, PromptMessage, PromptRole


class DeepSeekMultiExtractor(BaseMultiFieldExtractor):
    def __init__(
        self,
        llm: LLMClient,
        fields: list[str] | None = None,
    ) -> None:
        self.llm = llm
        self.fields = fields or ["date", "mileage", "price", "works", "materials"]

    @property
    def source(self) -> ExtractorSource:
        return ExtractorSource(
            name=self.llm.name,
            type=ExtractorSourceType.EXTERNAL_API,
        )

    def _build_prompt(self, text: str) -> list[PromptMessage]:
        fields_str = ", ".join(self.fields)
        prompt_text = (
            "Ты помощник, который извлекает структурированные данные"
            " о техническом обслуживании автомобиля из неструктурированного текста.\n"
            f"Извлеки следующие поля: {fields_str}.\n"
            "Формат данных:\n"
            "- date — дата (например, '2024-03-15')\n"
            "- mileage — пробег в км (число)\n"
            "- price — сумма (в рублях)\n"
            "- works — список выполненных работ\n"
            "- materials — список использованных материалов\n\n"
            "Если поле не найдено — укажи пустую строку, null или пустой список.\n"
            "Ответь ТОЛЬКО в виде JSON:\n"
            '{"date": ..., "mileage": ..., "price": ..., "works": [...], "materials": [...]}.\n\n'
            f"Текст:\n{text}"
        )
        return [PromptMessage(role=PromptRole.USER, content=prompt_text)]

    def extract_all(self, text: str) -> ExtractionResult:
        prompt = self._build_prompt(text)
        response = self.llm.chat(prompt, json_output=True)

        fields: list[ExtractionField] = []
        if response.error or not response.content:
            logging.error(f"[DeepSeekMultiExtractor] error: {response.error}")
            for field in self.fields:
                fields.append(self._empty_field(field, response.error))
            return ExtractionResult(
                content=fields, confidence=0.0, source=self.source, error=response.error
            )

        try:
            parsed = json.loads(response.content)
            for field in self.fields:
                value = parsed.get(field, "")
                conf = 1.0 if value else 0.0
                fields.append(
                    ExtractionField(
                        field=field,
                        value=value,
                        confidence=conf,
                        source=self.source,
                        error=None,
                    )
                )
            avg_conf = (
                sum(f.confidence for f in fields) / len(fields) if fields else 0.0
            )
            return ExtractionResult(
                content=fields, confidence=avg_conf, source=self.source, error=None
            )

        except Exception as exc:
            logging.exception("[DeepSeekMultiExtractor] Failed to parse JSON response")
            for field in self.fields:
                fields.append(self._empty_field(field, exc))
            return ExtractionResult(
                content=fields, confidence=0.0, source=self.source, error=exc
            )

    def _empty_field(
        self, field: str, error: str | Exception | None
    ) -> ExtractionField:
        return ExtractionField(
            field=field,
            value="",
            confidence=0.0,
            source=self.source,
            error=error,
        )
