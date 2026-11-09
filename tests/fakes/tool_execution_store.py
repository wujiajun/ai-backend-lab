from dataclasses import replace

from ai_backend_lab.application.order_agent.exceptions import (
    ToolExecutionConflictError,
)
from ai_backend_lab.application.order_agent.tool_execution import (
    ToolExecutionRecord,
    ToolExecutionStatus,
)


class FakeToolExecutionStore:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], ToolExecutionRecord] = {}

    async def get(
        self,
        run_id: str,
        call_id: str,
    ) -> ToolExecutionRecord | None:
        return self._records.get((run_id, call_id))

    async def create(
        self,
        record: ToolExecutionRecord,
    ) -> None:
        key = (record.run_id, record.call_id)

        if key in self._records:
            raise ToolExecutionConflictError(
                f"Tool execution already exists for {key}."
            )

        self._records[key] = record

    async def complete(
        self,
        run_id: str,
        call_id: str,
        output: str,
    ) -> ToolExecutionRecord:
        key = (run_id, call_id)
        existing = self._records.get(key)

        if existing is None or existing.status != ToolExecutionStatus.STARTED:
            raise ToolExecutionConflictError(
                f"Tool execution {key} could not be completed."
            )

        completed = replace(
            existing,
            status=ToolExecutionStatus.COMPLETED,
            output=output,
        )
        self._records[key] = completed

        return completed
