from fastapi import APIRouter

from ai_backend_lab.api.dependencies import (
    AgentRunServiceDep,
)
from ai_backend_lab.api.schemas.order_agent import (
    AgentApprovalRequestResponse,
    AgentResumeRequest,
    AgentRunRequest,
    AgentRunResponse,
)
from ai_backend_lab.application.order_agent.checkpoint import (
    AgentRunExecutionResult,
    AgentRunStatus,
)
from ai_backend_lab.application.order_agent.models import (
    AgentApprovalResult,
)

router = APIRouter(
    prefix="/agent/runs",
    tags=["Order Agent"],
)


@router.post("", response_model=AgentRunResponse)
async def start_agent_run(
    request: AgentRunRequest,
    service: AgentRunServiceDep,
) -> AgentRunResponse:
    execution = await service.start(
        user_message=request.message,
    )

    return _to_response(execution)


@router.post("/{run_id}/resume", response_model=AgentRunResponse)
async def resume_agent_run(
    run_id: str,
    request: AgentResumeRequest,
    service: AgentRunServiceDep,
) -> AgentRunResponse:
    execution = await service.resume(
        run_id=run_id,
        approved_call_ids=set(request.approved_call_ids),
        rejected_call_ids=set(request.rejected_call_ids),
    )

    return _to_response(execution)


@router.get("/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: str,
    service: AgentRunServiceDep,
) -> AgentRunResponse:
    checkpoint = await service.get(run_id)

    approval_requests: list[AgentApprovalRequestResponse] = []

    if checkpoint.state is not None:
        for tool_call in checkpoint.state.pending_tool_calls:
            approval_requests.append(
                AgentApprovalRequestResponse(
                    call_id=tool_call.call_id,
                    tool_name=tool_call.name,
                    arguments=tool_call.arguments,
                )
            )

    return AgentRunResponse(
        run_id=checkpoint.run_id,
        status=checkpoint.status.value,
        answer=checkpoint.answer,
        approval_requests=approval_requests,
    )


def _to_response(
    execution: AgentRunExecutionResult,
) -> AgentRunResponse:
    result = execution.result

    if isinstance(
        result,
        AgentApprovalResult,
    ):
        return AgentRunResponse(
            run_id=execution.run_id,
            status=(AgentRunStatus.WAITING_FOR_APPROVAL.value),
            approval_requests=[
                AgentApprovalRequestResponse(
                    call_id=request.call_id,
                    tool_name=request.tool_name,
                    arguments=request.arguments,
                )
                for request in result.requests
            ],
        )

    return AgentRunResponse(
        run_id=execution.run_id,
        status=AgentRunStatus.COMPLETED.value,
        answer=result.answer,
    )
