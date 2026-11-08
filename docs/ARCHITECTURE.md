# Architecture and Verified Repository State

_Review snapshot: 2026-11-08._

Repository: `wujiajun/ai-backend-lab`

Branch: `main`

HEAD: `358736ef321610bf34ac70b4b0180a07ff76130d`

This document describes the repository state observed during the read-only review. It does not claim that every intended production capability is complete.

## 1. High-level Structure

The project follows a ports-and-adapters / clean-architecture direction.

```text
src/ai_backend_lab/
├── api/
│   ├── routers/
│   ├── schemas/
│   ├── app.py
│   ├── dependencies.py
│   └── errors.py
├── application/
│   ├── order_agent/
│   ├── order_assistant/
│   ├── ports/
│   └── services.py
├── contracts/
│   └── order/v1/              # Generated protobuf Python
├── domain/
├── infrastructure/
│   ├── agent/
│   ├── database/
│   ├── llm/
│   ├── order_commands/
│   └── risk.py
├── observability/
├── composition.py
└── config.py

contracts/proto/               # Source .proto contracts
alembic/versions/              # Database migrations
tests/
```

Intended dependency direction:

```text
API → Application → Domain
          ↓
         Ports
          ↑
Infrastructure adapters
```

Infrastructure-specific implementations should remain behind application ports.

## 2. Agent Request Path

The durable Agent API currently exposes:

```text
POST /agent/runs
POST /agent/runs/{run_id}/resume
GET  /agent/runs/{run_id}
```

The current application path is:

```text
FastAPI router
  → AgentRunService
    → OrderAgentService
      → LLMGateway
      → ToolRegistry
      → ToolExecutor
        → ToolExecutionStore
        → AgentTool
```

`api/dependencies.py` obtains application services through `composition.py`.

`OrderAgentService` implements:

- Agent execution loop.
- LLM continuation.
- Tool execution.
- Approval decisions.
- Step limits.
- Application-level streaming event generation.

The current Agent router does not expose a streaming HTTP endpoint.

## 3. Agent Run and Checkpoint Persistence

Relevant files:

- `application/order_agent/checkpoint.py`
- `application/order_agent/run_service.py`
- `infrastructure/agent/run_store.py`
- `infrastructure/agent/state_serializer.py`
- `infrastructure/database/models.py`

The `agent_runs` table stores:

- `run_id`
- Lifecycle `status`
- Serialized Agent `state`
- Final `answer`
- Optimistic-lock `version`
- Timestamps

Current statuses:

- `RUNNING`
- `WAITING_FOR_APPROVAL`
- `COMPLETED`
- `FAILED`

### Start Flow

`AgentRunService.start()`:

1. Creates an initial `RUNNING` record.
2. Executes the Agent.
3. Persists a waiting-for-approval checkpoint or completed result.
4. On a caught exception, attempts to mark the run as failed.

### Resume Flow

`AgentRunService.resume()`:

1. Loads a waiting checkpoint.
2. Calls `claim_for_resume()`.
3. Uses the expected version and waiting status in the SQL update.
4. Increments the version.
5. Continues execution after successfully claiming the run.

This is optimistic concurrency control intended to prevent two resume requests from both claiming the same run.

### Current Limitation

The current implementation does not persist a new Agent checkpoint after every individual tool step.

A process crash during an active run can leave a `RUNNING` row without a completed result or a resumable checkpoint.

No recovery/reaper workflow was found in the reviewed source tree.

## 4. Tool Execution Ledger

Relevant files:

- `application/order_agent/tool_execution.py`
- `application/order_agent/executor.py`
- `application/order_agent/tools.py`
- `infrastructure/agent/tool_execution_store.py`
- `infrastructure/database/models.py`
- `alembic/versions/4134694f61e3_add_tool_executions.py`

The `tool_executions` table is separate from `agent_runs`.

Its composite primary key is:

```text
(run_id, call_id)
```

It stores:

- Tool name.
- Intent hash.
- Execution status.
- Output.
- Timestamps.

The two persistence models have different responsibilities:

| Persistence | Responsibility |
|---|---|
| `agent_runs` | Overall Agent lifecycle, checkpoint, and approval state |
| `tool_executions` | Claim and result of an individual logical tool call |

Current tool execution statuses:

- `STARTED`
- `COMPLETED`
- `UNKNOWN`

### Current Executor Flow

The current executor:

1. Resolves the tool by name.
2. Parses JSON arguments.
3. Canonicalizes JSON using sorted keys and compact separators.
4. Builds a SHA-256 intent hash from the tool name and canonical arguments.
5. Looks up `(run_id, call_id)`.
6. Creates a `STARTED` record if none exists.
7. Executes the tool.
8. Persists `COMPLETED` with the output.
9. Replays stored output for an identical completed call.
10. Rejects reuse of the same key with a different tool or intent.
11. Refuses to blindly re-execute an existing `STARTED` or `UNKNOWN` record.

The SQLAlchemy store wraps synchronous SQLAlchemy session operations using `asyncio.to_thread()`.

### Important Gaps

**A. Tool-specific validation happens after the claim**

JSON parsing and canonicalization happen before the claim.

However, tool-specific Pydantic validation happens inside each tool's `execute()` method.

The executor creates the `STARTED` record before calling `tool.execute()`.

Therefore, schema-invalid arguments can create a `STARTED` ledger record even though the business operation was never attempted.

**B. No explicit UNKNOWN transition**

The `UNKNOWN` status exists, and the executor refuses to blindly replay it.

However, the store currently exposes `get`, `create`, and `complete`; no explicit persistence transition to `UNKNOWN` or reconciliation workflow was found.

**C. STARTED records can remain indefinitely**

An exception after the `STARTED` claim can leave the record in `STARTED`.

There is no complete recovery policy for stale `STARTED` records.

**D. Focused test coverage is incomplete**

No dedicated `ToolExecutor` or SQL tool-execution-store test module was found in the reviewed test tree.

## 5. Tool Policies and Approval

`AgentToolPolicy` currently contains:

- `parallel_safe`
- `requires_approval`

`GetOrderTool`:

- Does not require approval.
- Is marked non-parallel-safe.

`CancelOrderTool`:

- Requires approval.
- Is marked non-parallel-safe.

Both tools currently perform Pydantic argument validation inside `execute()`.

The executor supports sequential execution and a `TaskGroup` path when every tool in a batch declares itself parallel-safe.

## 6. Idempotency and Downstream Command Boundary

The application port is:

```text
application/ports/order_commands.py
```

Its port is named `OrderCommandGateway`.

The logical execution key is:

```text
{run_id}:{call_id}
```

The key is carried in `CancelOrderCommand`.

### Existing Adapters

**LocalOrderCommandGateway**

- Calls the in-process `OrderService`.
- Uses `asyncio.to_thread()`.
- Does not persist or enforce the command's idempotency key.

**GrpcOrderCommandGateway**

- Implements the same application boundary.
- Maps gRPC status codes to application integration errors.
- Sends the idempotency key in the protobuf request.

### Protobuf Contract

Source:

```text
contracts/proto/ai_backend_lab/contracts/order/v1/order_service.proto
```

The current contract defines one RPC:

```text
OrderCommandService.CancelOrder
```

Generated Python files are under:

```text
src/ai_backend_lab/contracts/order/v1/
```

### Critical Runtime Wiring Fact

Although the gRPC adapter and contract exist, the current `composition.py` constructs `LocalOrderCommandGateway`.

The current FastAPI lifespan creates and closes:

- An HTTPX client.
- An AsyncOpenAI client.

It does not create a gRPC channel or stub.

No downstream gRPC server implementation was found in the reviewed repository tree.

Therefore:

- A gRPC client adapter exists.
- The active runtime path remains local.
- Remote gRPC execution is not yet integrated end to end.
- Downstream durable idempotency is not yet implemented in this repository.

Do not describe these capabilities as completed.

## 7. Other Infrastructure and API Components

Verified components include:

- `OpenAILLMGateway` behind the `LLMGateway` port.
- `HttpRiskGateway` behind the `RiskGateway` port.
- HTTPX client usage.
- SQLAlchemy engine and session factory.
- Alembic migrations.
- FastAPI lifespan ownership for HTTPX and OpenAI clients.
- Request ID context middleware.
- Request-ID-aware logging.
- Centralized application exception mapping.
- Request-validation error mapping.

The `.env.example` contains placeholder configuration names for database, risk service, OpenAI, and Agent settings.

Never copy real local `.env` values into documentation.

## 8. Database Migrations

The current migration tree contains migrations for:

- Orders.
- Internal order ID / order number changes.
- `agent_runs`.
- `tool_executions`.

The test setup includes Alembic upgrade-to-head logic and guards intended to restrict integration tests to the `ai_backend_lab_test` database.

Do not change these guards casually.

## 9. Tests and Verification Limits

The current test tree contains API, application, domain, fake, and infrastructure tests.

Examples include:

- Agent API start/resume/get behavior.
- Agent run service approval/resume behavior.
- Agent run store round-trip behavior.
- Agent run optimistic claim behavior.
- Order repository and unit-of-work tests.
- Risk gateway tests.

This was a remote, read-only source review.

The following were not run during this review:

- Pytest.
- Ruff.
- Black.
- Type checking.
- Application startup.
- Database migrations.

Test health is therefore unverified until checked locally.