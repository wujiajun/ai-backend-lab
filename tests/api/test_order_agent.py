from fastapi.testclient import TestClient

from ai_backend_lab.api.app import app
from ai_backend_lab.api.dependencies import (
    get_agent_run_service,
)
from ai_backend_lab.application.order_agent.checkpoint import (
    AgentRunCheckpoint,
    AgentRunExecutionResult,
    AgentRunStatus,
)
from ai_backend_lab.application.order_agent.exceptions import (
    AgentRunNotFoundError,
)
from ai_backend_lab.application.order_agent.models import (
    AgentApprovalRequest,
    AgentApprovalResult,
    AgentResult,
    AgentState,
    AgentTrace,
    ConversationState,
)


def test_resume_rejects_conflicting_decision(
    client: TestClient,
) -> None:
    response = client.post(
        "/agent/runs/run-001/resume",
        json={
            "approved_call_ids": ["call-001"],
            "rejected_call_ids": ["call-001"],
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["code"] == "VALIDATION_ERROR"


class FakeAgentRunService:
    def __init__(
        self,
        start_result: AgentRunExecutionResult | None = None,
        resume_result: AgentRunExecutionResult | None = None,
        checkpoint: AgentRunCheckpoint | None = None,
    ) -> None:
        self._start_result = start_result
        self._resume_result = resume_result
        self.started_messages: list[str] = []
        self.resume_calls: list[tuple[str, set[str], set[str]]] = []
        self._checkpoint = checkpoint
        self.get_calls: list[str] = []

    async def start(
        self,
        user_message: str,
        conversation: ConversationState | None = None,
    ) -> AgentRunExecutionResult:
        if self._start_result is None:
            raise AssertionError("No fake start result configured.")

        self.started_messages.append(user_message)

        return self._start_result

    async def resume(
        self,
        run_id: str,
        approved_call_ids: set[str],
        rejected_call_ids: set[str],
    ) -> AgentRunExecutionResult:
        if self._resume_result is None:
            raise AssertionError("No fake resume result configured.")

        self.resume_calls.append(
            (
                run_id,
                approved_call_ids,
                rejected_call_ids,
            )
        )

        return self._resume_result

    async def get(
        self,
        run_id: str,
    ) -> AgentRunCheckpoint:
        if self._checkpoint is None:
            raise AssertionError("No fake checkpoint configured.")

        self.get_calls.append(run_id)

        return self._checkpoint


def test_start_agent_run_returns_completed_result(
    client: TestClient,
) -> None:
    fake_service = FakeAgentRunService(
        start_result=AgentRunExecutionResult(
            run_id="run-001",
            result=AgentResult(
                answer="Hello! How can I help?",
                steps=0,
                conversation=ConversationState(),
                trace=AgentTrace(),
            ),
        )
    )

    def override_get_agent_run_service() -> FakeAgentRunService:
        return fake_service

    app.dependency_overrides[get_agent_run_service] = override_get_agent_run_service

    response = client.post(
        "/agent/runs",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "run_id": "run-001",
        "status": "completed",
        "answer": "Hello! How can I help?",
        "approval_requests": [],
    }

    assert fake_service.started_messages == ["Hello"]


def test_start_agent_run_returns_approval_request(
    client: TestClient,
) -> None:
    state = AgentState(
        user_message="Cancel ORD-001.",
        conversation=ConversationState(),
    )

    fake_service = FakeAgentRunService(
        start_result=AgentRunExecutionResult(
            run_id="run-002",
            result=AgentApprovalResult(
                state=state,
                requests=[
                    AgentApprovalRequest(
                        call_id="call-001",
                        tool_name="cancel_order",
                        arguments=('{"order_number":"ORD-001"}'),
                    )
                ],
            ),
        )
    )

    def override_get_agent_run_service() -> FakeAgentRunService:
        return fake_service

    app.dependency_overrides[get_agent_run_service] = override_get_agent_run_service

    response = client.post(
        "/agent/runs",
        json={
            "message": "Cancel ORD-001.",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "run_id": "run-002",
        "status": "waiting_for_approval",
        "answer": None,
        "approval_requests": [
            {
                "call_id": "call-001",
                "tool_name": "cancel_order",
                "arguments": ('{"order_number":"ORD-001"}'),
            }
        ],
    }


def test_resume_agent_run_returns_completed_result(
    client: TestClient,
) -> None:
    fake_service = FakeAgentRunService(
        resume_result=AgentRunExecutionResult(
            run_id="run-001",
            result=AgentResult(
                answer="Order ORD-001 was cancelled.",
                steps=1,
                conversation=ConversationState(),
                trace=AgentTrace(),
            ),
        )
    )

    def override_get_agent_run_service() -> FakeAgentRunService:
        return fake_service

    app.dependency_overrides[get_agent_run_service] = override_get_agent_run_service

    response = client.post(
        "/agent/runs/run-001/resume",
        json={
            "approved_call_ids": [
                "call-001",
            ],
            "rejected_call_ids": [],
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "run_id": "run-001",
        "status": "completed",
        "answer": "Order ORD-001 was cancelled.",
        "approval_requests": [],
    }

    assert fake_service.resume_calls == [
        (
            "run-001",
            {"call-001"},
            set(),
        )
    ]


def test_get_completed_agent_run(
    client: TestClient,
) -> None:
    fake_service = FakeAgentRunService(
        checkpoint=AgentRunCheckpoint(
            run_id="run-001",
            status=AgentRunStatus.COMPLETED,
            answer=("Order ORD-001 was cancelled."),
            version=4,
            state=None,
        )
    )

    def override_get_agent_run_service() -> FakeAgentRunService:
        return fake_service

    app.dependency_overrides[get_agent_run_service] = override_get_agent_run_service

    response = client.get("/agent/runs/run-001")

    assert response.status_code == 200

    assert response.json() == {
        "run_id": "run-001",
        "status": "completed",
        "answer": "Order ORD-001 was cancelled.",
        "approval_requests": [],
    }

    assert fake_service.get_calls == ["run-001"]


def test_get_agent_run_returns_404_when_not_found(
    client: TestClient,
) -> None:
    class FakeNotFoundAgentRunService:
        async def get(
            self,
            run_id: str,
        ) -> AgentRunCheckpoint:
            raise AgentRunNotFoundError(f"Agent run not found: {run_id}")

    fake_service = FakeNotFoundAgentRunService()

    def override_get_agent_run_service() -> FakeNotFoundAgentRunService:
        return fake_service

    app.dependency_overrides[get_agent_run_service] = override_get_agent_run_service

    response = client.get("/agent/runs/run-missing")

    assert response.status_code == 404

    assert response.json() == {
        "code": "AGENT_RUN_NOT_FOUND",
        "message": ("Agent run not found: run-missing"),
        "details": None,
    }
