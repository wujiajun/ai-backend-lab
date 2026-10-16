import asyncio
from typing import Any, cast

from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from ai_backend_lab.application.order_agent.exceptions import (
    ToolExecutionConflictError,
)
from ai_backend_lab.application.order_agent.tool_execution import (
    ToolExecutionRecord,
    ToolExecutionStatus,
    ToolExecutionStore,
)
from ai_backend_lab.infrastructure.database.models import (
    ToolExecutionModel,
)


class SqlAlchemyToolExecutionStore(ToolExecutionStore):
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    async def get(
        self,
        run_id: str,
        call_id: str,
    ) -> ToolExecutionRecord | None:
        return await asyncio.to_thread(
            self._get_sync,
            run_id,
            call_id,
        )

    def _get_sync(
        self,
        run_id: str,
        call_id: str,
    ) -> ToolExecutionRecord | None:
        with self._session_factory() as session:
            model = session.get(
                ToolExecutionModel,
                (
                    run_id,
                    call_id,
                ),
            )

            if model is None:
                return None

            return self._to_record(model)

    async def create(
        self,
        record: ToolExecutionRecord,
    ) -> None:
        await asyncio.to_thread(
            self._create_sync,
            record,
        )

    def _create_sync(
        self,
        record: ToolExecutionRecord,
    ) -> None:
        with self._session_factory() as session:
            model = ToolExecutionModel(
                run_id=record.run_id,
                call_id=record.call_id,
                tool_name=record.tool_name,
                intent_hash=record.intent_hash,
                status=record.status.value,
                output=record.output,
            )

            session.add(model)

            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()

                raise ToolExecutionConflictError(
                    "Tool execution already exists "
                    f"for run_id={record.run_id}, "
                    f"call_id={record.call_id}."
                ) from exc

    async def complete(
        self,
        run_id: str,
        call_id: str,
        output: str,
    ) -> ToolExecutionRecord:
        return await asyncio.to_thread(
            self._complete_sync,
            run_id,
            call_id,
            output,
        )

    def _complete_sync(
        self,
        run_id: str,
        call_id: str,
        output: str,
    ) -> ToolExecutionRecord:
        with self._session_factory() as session:
            raw_result = session.execute(
                update(ToolExecutionModel)
                .where(
                    ToolExecutionModel.run_id == run_id,
                    ToolExecutionModel.call_id == call_id,
                    ToolExecutionModel.status == ToolExecutionStatus.STARTED.value,
                )
                .values(
                    status=(ToolExecutionStatus.COMPLETED.value),
                    output=output,
                )
            )

            result = cast(
                CursorResult[Any],
                raw_result,
            )

            if result.rowcount != 1:
                session.rollback()

                raise ToolExecutionConflictError(
                    "Tool execution could not " "be completed."
                )

            session.commit()

            model = session.get(
                ToolExecutionModel,
                (
                    run_id,
                    call_id,
                ),
            )

            if model is None:
                raise ToolExecutionConflictError(
                    "Completed tool execution " "could not be loaded."
                )

            return self._to_record(model)

    @staticmethod
    def _to_record(
        model: ToolExecutionModel,
    ) -> ToolExecutionRecord:
        return ToolExecutionRecord(
            run_id=model.run_id,
            call_id=model.call_id,
            tool_name=model.tool_name,
            intent_hash=model.intent_hash,
            status=ToolExecutionStatus(model.status),
            output=model.output,
        )
