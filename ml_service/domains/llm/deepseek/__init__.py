import json
import logging
from typing import Any

import httpx

from ml_service.domains.llm.base import LLMClient, LLMResponse, PromptMessage
from ml_service.utils.retry import Retry

retry = Retry(verbose=True)


class DeepSeekClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
        timeout: float = 30,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = httpx.Timeout(timeout)
        self.base_url = "https://api.deepseek.com"
        self.url_path = "chat/completions"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=self.timeout, headers=self.headers, base_url=self.base_url
        )

    @retry(
        n_times=5,
        sleep_duration=1,
        increasing=True,
        allowed_exceptions=(httpx.HTTPError,),
    )
    async def _do_request(
        self, prompt: list[PromptMessage], **kwargs: Any
    ) -> dict[str, Any] | None:
        payload = {
            "model": kwargs.pop("model", self.model),
            "temperature": kwargs.pop("temperature", self.temperature),
            "messages": self._prompt_to_messages(prompt),
            "stream": False,
            **kwargs,
        }
        async with self._client as client:
            response = await client.post(self.url_path, json=payload)
            response.raise_for_status()
            return response.json()

    async def request_with_json_output(
        self, prompt: list[PromptMessage], **kwargs: Any
    ) -> dict[str, Any] | None:
        response_format = {"type": "json_object"}
        return await self._do_request(
            prompt=prompt, response_format=response_format, **kwargs
        )

    def _return_empty(
        self,
        prompt: list[PromptMessage],
        data: dict[str, Any] | None = None,
        json_output: bool = False,
        error: str | Exception | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            content=None,
            prompt=prompt,
            source=self.name,
            data=data,
            json_output=json_output,
            error=error,
        )

    async def chat(
        self, prompt: list[PromptMessage], json_output: bool = False, **kwargs: Any
    ) -> LLMResponse:
        try:
            data = (
                await self.request_with_json_output(prompt, **kwargs)
                if json_output
                else await self._do_request(prompt, **kwargs)
            )
            if not data:
                error = f"there is no data in response {prompt}"
                logging.error(error)
                return self._return_empty(prompt, data, json_output, error)

            content = self._get_content(data)
            if content and json_output:
                try:
                    _ = json.loads(content)
                except (json.JSONDecodeError, TypeError) as exc:
                    logging.exception(
                        f"got invalid json output from {self.name}: {data}"
                    )
                    return self._return_empty(prompt, data, json_output, exc)

            return LLMResponse(
                content=content,
                prompt=prompt,
                source=self.name,
                data=data,
                json_output=json_output,
                error=None,
            )
        except Exception as exc:
            logging.exception(f"got an error trying to chat with {self.name}")
            return self._return_empty(prompt, data, json_output, exc)
