from collections import deque
from collections.abc import AsyncIterator
from typing import TypeVar

from pydantic import BaseModel

from ai_backend_lab.application.ports.llm import (
    LLMRequest,
    LLMResult,
    StructuredLLMResult,
)

T = TypeVar(
    "T",
    bound=BaseModel,
)


class FakeLLMGateway:
    def __init__(
        self,
        *,
        results: list[LLMResult] | None = None,
        structured_values: list[BaseModel] | None = None,
        stream_chunks: list[str] | None = None,
    ) -> None:
        self._results = deque(results or [])
        self._structured_values = deque(structured_values or [])
        self._stream_chunks = stream_chunks or []

        self.requests: list[LLMRequest] = []

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResult:
        self.requests.append(request)

        if not self._results:
            raise AssertionError("No fake LLM result configured.")

        return self._results.popleft()

    async def generate_structured(
        self,
        request: LLMRequest,
        output_type: type[T],
    ) -> StructuredLLMResult[T]:
        self.requests.append(request)

        if not self._structured_values:
            raise AssertionError("No fake structured value configured.")

        value = self._structured_values.popleft()

        if not isinstance(value, output_type):
            raise AssertionError(
                "Configured structured value " f"is not {output_type.__name__}."
            )

        return StructuredLLMResult(
            value=value,
        )

    async def stream(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]:
        self.requests.append(request)

        for chunk in self._stream_chunks:
            yield chunk
