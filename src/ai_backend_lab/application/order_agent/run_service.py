import logging
from uuid import uuid4

from ai_backend_lab.application.order_agent.checkpoint import (
    AgentRunCheckpoint,
    AgentRunExecutionResult,
    AgentRunStatus,
    AgentRunStore,
)
from ai_backend_lab.application.order_agent.exceptions import (
    AgentRunNotFoundError,
    AgentRunStateError,
)
from ai_backend_lab.application.order_agent.models import (
    AgentApprovalResult,
    AgentRunResult,
    ConversationState,
)
from ai_backend_lab.application.order_agent.service import OrderAgentService

logger = logging.getLogger(__name__)


class AgentRunService:
    def __init__(
        self,
        agent: OrderAgentService,
        store: AgentRunStore,
    ) -> None:
        self._agent = agent
        self._store = store

    async def start(
        self,
        user_message: str,
        conversation: ConversationState | None = None,
    ) -> AgentRunExecutionResult:
        run_id = f"run_{uuid4().hex}"

        initial = AgentRunCheckpoint(
            run_id=run_id,
            status=AgentRunStatus.RUNNING,
            state=None,
            version=1,
        )

        await self._store.create(initial)

        try:
            result = await self._agent.run(
                user_message=user_message,
                conversation=conversation,
            )
        except Exception:
            await self._mark_failed(initial)

            raise

        checkpoint = self._checkpoint_from_result(
            run_id=run_id,
            result=result,
            version=initial.version,
        )

        await self._store.save(
            checkpoint,
            expected_version=checkpoint.version,
        )

        return AgentRunExecutionResult(
            run_id=run_id,
            result=result,
        )

    async def resume(
        self,
        run_id: str,
        approved_call_ids: set[str],
        rejected_call_ids: set[str],
    ) -> AgentRunExecutionResult:
        checkpoint = await self._store.get(run_id)

        if checkpoint is None:
            raise AgentRunNotFoundError(f"Agent run not found: {run_id}")

        if checkpoint.status != AgentRunStatus.WAITING_FOR_APPROVAL:
            raise AgentRunStateError("Agent run is not waiting " "for approval.")

        if checkpoint.state is None:
            raise AgentRunStateError("Waiting agent run " "has no checkpoint state.")

        # IMPORTANT:
        # claim before executing any side-effect tool.
        claimed = await self._store.claim_for_resume(
            run_id=run_id,
            expected_version=(checkpoint.version),
        )

        if claimed.state is None:
            raise AgentRunStateError("Claimed agent run " "has no checkpoint state.")

        try:
            result = await self._agent.resume(
                state=claimed.state,
                approved_call_ids=approved_call_ids,
                rejected_call_ids=rejected_call_ids,
            )

        except Exception:
            await self._mark_failed(claimed)

            raise

        next_checkpoint = self._checkpoint_from_result(
            run_id=run_id,
            result=result,
            version=claimed.version,
        )

        await self._store.save(
            next_checkpoint,
            expected_version=(claimed.version),
        )

        return AgentRunExecutionResult(
            run_id=run_id,
            result=result,
        )

    async def get(
        self,
        run_id: str,
    ) -> AgentRunCheckpoint:
        checkpoint = await self._store.get(run_id)

        if checkpoint is None:
            raise AgentRunNotFoundError(f"Agent run not found: {run_id}")

        return checkpoint

    async def _mark_failed(
        self,
        checkpoint: AgentRunCheckpoint,
    ) -> None:
        failed = AgentRunCheckpoint(
            run_id=checkpoint.run_id,
            status=AgentRunStatus.FAILED,
            state=checkpoint.state,
            answer=None,
            version=checkpoint.version,
        )

        try:
            await self._store.save(
                failed,
                expected_version=(checkpoint.version),
            )

        except Exception:
            logger.exception(
                "Failed to persist failed " "agent run status " "run_id=%s",
                checkpoint.run_id,
            )

    @staticmethod
    def _checkpoint_from_result(
        run_id: str,
        result: AgentRunResult,
        version: int,
    ) -> AgentRunCheckpoint:
        if isinstance(
            result,
            AgentApprovalResult,
        ):
            return AgentRunCheckpoint(
                run_id=run_id,
                status=(AgentRunStatus.WAITING_FOR_APPROVAL),
                state=result.state,
                answer=None,
                version=version,
            )

        return AgentRunCheckpoint(
            run_id=run_id,
            status=AgentRunStatus.COMPLETED,
            state=None,
            answer=result.answer,
            version=version,
        )
