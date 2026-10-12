import asyncio
from dataclasses import replace
from typing import Any, cast

from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from ai_backend_lab.application.order_agent.checkpoint import (
    AgentRunCheckpoint,
    AgentRunStatus,
    AgentRunStore,
)
from ai_backend_lab.application.order_agent.exceptions import (
    AgentRunConflictError,
)
from ai_backend_lab.infrastructure.agent.state_serializer import (
    deserialize_agent_state,
    serialize_agent_state,
)
from ai_backend_lab.infrastructure.database.models import (
    AgentRunModel,
)


class SqlAlchemyAgentRunStore(AgentRunStore):
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    async def create(
        self,
        checkpoint: AgentRunCheckpoint,
    ) -> None:
        await asyncio.to_thread(
            self._create_sync,
            checkpoint,
        )

    def _create_sync(
        self,
        checkpoint: AgentRunCheckpoint,
    ) -> None:
        with self._session_factory() as session:
            model = AgentRunModel(
                run_id=checkpoint.run_id,
                status=checkpoint.status.value,
                state=self._serialize_state(checkpoint),
                answer=checkpoint.answer,
                version=checkpoint.version,
            )

            session.add(model)

            session.commit()

    async def get(
        self,
        run_id: str,
    ) -> AgentRunCheckpoint | None:
        return await asyncio.to_thread(
            self._get_sync,
            run_id,
        )

    def _get_sync(
        self,
        run_id: str,
    ) -> AgentRunCheckpoint | None:
        with self._session_factory() as session:
            model = session.get(
                AgentRunModel,
                run_id,
            )

            if model is None:
                return None

            return self._to_checkpoint(model)

    async def save(
        self,
        checkpoint: AgentRunCheckpoint,
        expected_version: int,
    ) -> AgentRunCheckpoint:
        return await asyncio.to_thread(
            self._save_sync,
            checkpoint,
            expected_version,
        )

    def _save_sync(
        self,
        checkpoint: AgentRunCheckpoint,
        expected_version: int,
    ) -> AgentRunCheckpoint:
        next_version = expected_version + 1

        with self._session_factory() as session:
            raw_result = session.execute(
                update(AgentRunModel)
                .where(
                    AgentRunModel.run_id == checkpoint.run_id,
                    AgentRunModel.version == expected_version,
                )
                .values(
                    status=(checkpoint.status.value),
                    state=(self._serialize_state(checkpoint)),
                    answer=checkpoint.answer,
                    version=next_version,
                )
            )

            result = cast(
                CursorResult[Any],
                raw_result,
            )

            if result.rowcount != 1:
                session.rollback()

                raise AgentRunConflictError(
                    "Agent run was modified " "by another request."
                )

            session.commit()

        return replace(
            checkpoint,
            version=next_version,
        )

    async def claim_for_resume(
        self,
        run_id: str,
        expected_version: int,
    ) -> AgentRunCheckpoint:
        return await asyncio.to_thread(
            self._claim_for_resume_sync,
            run_id,
            expected_version,
        )

    def _claim_for_resume_sync(
        self,
        run_id: str,
        expected_version: int,
    ) -> AgentRunCheckpoint:
        next_version = expected_version + 1

        with self._session_factory() as session:
            raw_result = session.execute(
                update(AgentRunModel)
                .where(
                    AgentRunModel.run_id == run_id,
                    AgentRunModel.version == expected_version,
                    AgentRunModel.status == (AgentRunStatus.WAITING_FOR_APPROVAL.value),
                )
                .values(
                    status=(AgentRunStatus.RUNNING.value),
                    version=next_version,
                )
            )

            result = cast(
                CursorResult[Any],
                raw_result,
            )

            if result.rowcount != 1:
                session.rollback()

                raise AgentRunConflictError("Agent run could not be claimed.")

            model = session.get(
                AgentRunModel,
                run_id,
            )

            if model is None:
                session.rollback()

                raise AgentRunConflictError(
                    "Agent run disappeared " "while being claimed."
                )

            session.commit()

            return self._to_checkpoint(model)

    @staticmethod
    def _serialize_state(
        checkpoint: AgentRunCheckpoint,
    ) -> dict | None:
        if checkpoint.state is None:
            return None

        return serialize_agent_state(checkpoint.state)

    @staticmethod
    def _to_checkpoint(
        model: AgentRunModel,
    ) -> AgentRunCheckpoint:
        state = None

        if model.state is not None:
            state = deserialize_agent_state(model.state)

        return AgentRunCheckpoint(
            run_id=model.run_id,
            status=AgentRunStatus(model.status),
            state=state,
            answer=model.answer,
            version=model.version,
        )
