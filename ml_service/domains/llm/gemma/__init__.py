# TODO(vadim): fix llama-cpp-python docker installation

# import logging
# import os
# from pathlib import Path
# from typing import Any

# from llama_cpp import (
#     ChatCompletionRequestResponseFormat,
#     CreateChatCompletionResponse,
#     Llama,
# )

# from autocare.ml.llm.base import LLMClient, LLMResponse, PromptMessage, PromptRole


# class Gemma2Client(LLMClient):
#     def __init__(self, model_path: Path, **kwargs: Any) -> None:
#         self.temperature = kwargs.pop("temperature", 0.3)
#         self.max_tokens = kwargs.pop("max_tokens", 512)
#         self.model_path = self._validate_model_path(model_path)
#         self.model_filename = self.model_path.stem
#         self.model = Llama(
#             model_path=str(self.model_path),
#             n_ctx=int(kwargs.pop("n_ctx", 2048)),
#             n_threads=int(kwargs.pop("n_threads", os.cpu_count())),
#             **kwargs,
#         )

#     @staticmethod
#     def _validate_model_path(path: Path) -> Path:
#         if path.is_file():
#             if "gemma" not in path.name.lower():
#                 raise ValueError(f"Provided file does not appear to be a Gemma model: {path.name}")
#             return path.resolve()

#         if path.is_dir():
#             # Ищем файл gemma*.gguf в папке
#             for file in path.glob("*.gguf"):
#                 if "gemma" in file.name.lower():
#                     return file.resolve()
#             raise FileNotFoundError(f"No Gemma .gguf model found in directory: {path}")

#         # Путь не существует вовсе
#         raise FileNotFoundError(f"Path does not exist: {path}")

#     @staticmethod
#     def _get_response_format(json_schema: dict[str, Any] | None = None) -> ChatCompletionRequestResponseFormat:
#         """
#         response_format={
#             "type": "json_object",
#             "schema": {
#                 "type": "object",
#                 "properties": {"team_name": {"type": "string"}},
#                 "required": ["team_name"],
#             },
#         },
#         """
#         if not json_schema:
#             return ChatCompletionRequestResponseFormat(type="text", schema=None)
#         return ChatCompletionRequestResponseFormat(
#             type="json_object",
#             schema=json_schema,
#         )

#     def _prompt_to_messages(self, prompt: list[PromptMessage]) -> list[dict[str, str]]:
#         filtered_messages = list(filter(lambda m: m.role != PromptRole.SYSTEM, prompt))
#         if len(prompt) != len(filtered_messages):
#             logging.warning(f"{self.name} doesn't support SYSTEM ROLE. Sytem prompts will be ignored.")
#         return super()._prompt_to_messages(filtered_messages)

#     def chat(
#         self, prompt: list[PromptMessage], json_schema: dict[str, Any] | None = None, **kwargs: Any
#     ) -> LLMResponse:
#         try:
#             messages = self._prompt_to_messages(prompt)
#             response: CreateChatCompletionResponse = self.model.create_chat_completion(
#                 messages,  # type: ignore
#                 temperature=self.temperature,
#                 max_tokens=kwargs.pop("max_tokens", self.max_tokens),
#                 response_format=self._get_response_format(json_schema),
#                 **kwargs,
#             )
#             data = dict(response)
#             content = self._get_content(data)
#             if not content:
#                 raise ValueError(f"{self.name} returned empty content")
#             return LLMResponse(
#                 content=content,
#                 source=self.name,
#                 data=data,
#                 prompt=prompt,
#                 json_output=True if json_schema else False,
#                 error=None,
#             )
#         except Exception as exc:
#             logging.exception(f"{self.name} chat failed")
#             return LLMResponse(
#                 content=None,
#                 source=self.name,
#                 data=None,
#                 prompt=prompt,
#                 json_output=True if json_schema else False,
#                 error=exc,
#             )
