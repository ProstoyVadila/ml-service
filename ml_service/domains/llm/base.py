import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any


class PromptRole(StrEnum):
    USER = auto()
    SYSTEM = auto()
    ASSISTENT = auto()
    # TOOL = auto()


@dataclass
class PromptMessage:
    role: PromptRole
    content: str


@dataclass
class LLMResponse:
    content: str | None
    source: str
    data: dict[str, Any] | None
    prompt: list[PromptMessage]
    json_output: bool
    error: Exception | str | None


class LLMClient(ABC):
    @abstractmethod
    def chat(self, prompt: list[PromptMessage], **kwargs: Any) -> LLMResponse:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def _prompt_to_messages(
        self, messages: list[PromptMessage]
    ) -> list[dict[str, str]]:
        return [
            {"role": message.role.value, "content": message.content}
            for message in messages
        ]

    def _get_content(self, data: dict[str, Any]) -> str | None:
        try:
            return data["choices"][0]["message"]["content"]
        except KeyError:
            logging.exception(f"cannot get content from {self.name} response: {data}")
