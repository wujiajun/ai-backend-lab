# Roadmap and Implementation Status

_Status reconciled against repository `main` at `358736ef321610bf34ac70b4b0180a07ff76130d` on 2026-11-08._

"Implemented" means present in the inspected source tree. It does not mean independently runtime-tested during this review.

## 1. Implemented in the Current Source Tree

### Core Backend

- Python 3.12+ project managed with `uv`.
- FastAPI application.
- Dependency wiring and API routers.
- Pydantic request/response schemas.
- SQLAlchemy persistence.
- Alembic migrations.
- Order domain and application services.
- Repository and unit-of-work abstractions.
- OpenAI-backed `LLMGateway`.
- HTTPX-based risk-service gateway.
- Centralized API exception mapping.
- Request-ID-aware logging.

### Agent Runtime

- Multi-step `OrderAgentService` loop.
- LLM tool-call and continuation handling.
- Tool registry and tool definitions.
- Maximum Agent step budget.
- Sequential tool execution.
- Parallel-safe execution path.
- `get_order` tool.
- `cancel_order` tool.
- Human approval requirement for `cancel_order`.
- Agent application event-stream generator.

The current Agent router does not expose a streaming HTTP endpoint.

### Durable Run and Tool State

- `agent_runs` persistence.
- Agent checkpoint serialization/deserialization.
- Start, get, resume, and approval lifecycle.
- Optimistic version claim before resume-side-effect execution.
- Separate `tool_executions` table.
- SQLAlchemy tool execution store.
- Composite tool execution identity `(run_id, call_id)`.
- Canonical JSON intent representation.
- SHA-256 intent fingerprint.
- `STARTED`, `COMPLETED`, and `UNKNOWN` status values.
- Replay of identical completed tool calls.
- Rejection of intent-key reuse conflicts.

### Service Boundary Foundation

- `OrderCommandGateway` application port.
- `LocalOrderCommandGateway`.
- `GrpcOrderCommandGateway` client adapter.
- Versioned `order_service.proto` contract.
- Generated Python protobuf bindings.

## 2. Partially Implemented or Not End-to-End

### 2.1 Tool Argument Validation Before the Ledger Claim

Current behavior:

- JSON syntax is parsed before the ledger claim.
- Tool-specific Pydantic validation occurs inside `AgentTool.execute()`.
- The executor creates `STARTED` before calling `execute()`.

Impact:

Schema-invalid arguments can leave misleading `STARTED` records.

Target behavior:

1. Resolve the tool.
2. Parse and validate the complete argument schema.
3. Canonicalize the validated intent consistently.
4. Claim `(run_id, call_id)` as `STARTED`.
5. Execute using the already validated arguments.

Avoid a second inconsistent validation path.

### 2.2 Unknown Outcome Handling

Current behavior:

- `UNKNOWN` is a defined execution status.
- The executor refuses to blindly replay it.
- The store has no explicit mark-unknown transition.
- No reconciliation API or process was found.
- Stale `STARTED` records have no recovery policy.

A status enum alone is not a recovery mechanism.

### 2.3 End-to-End Idempotency

Current behavior:

- The Agent generates `{run_id}:{call_id}`.
- The key is passed through `CancelOrderCommand`.
- The local adapter does not persist or enforce the key.
- The gRPC request includes the key.
- No downstream service implementation or durable deduplication store exists in this repository.

Do not claim exactly-once side effects.

The current implementation provides a local execution ledger and an idempotency-key propagation foundation, not end-to-end exactly-once guarantees.

### 2.4 gRPC Runtime Integration

Current behavior:

- The gRPC client adapter exists.
- The protobuf contract exists.
- `composition.py` still selects `LocalOrderCommandGateway`.
- FastAPI lifespan does not own a gRPC channel or stub.
- No remote service endpoint/server implementation was found in the reviewed tree.

### 2.5 Agent Run Crash Recovery

Current behavior:

- Initial Agent run state is persisted.
- Approval checkpoints are durable.
- The run service does not checkpoint every intermediate tool step.
- A process crash can leave a `RUNNING` Agent run without a recovery workflow.

### 2.6 Test Coverage

Existing tests cover Agent API behavior, Agent run service, Agent run persistence, order repositories, and risk gateway behavior.

No dedicated `ToolExecutor` or `SqlAlchemyToolExecutionStore` test module was found in the reviewed test tree.

Tests were not executed during the remote review.

## 3. Recommended Next Work

### Priority 1 — Validate Tool Arguments Before the Ledger Claim

This is the most concrete unresolved correctness issue from the latest project discussion and is confirmed by the reviewed source.

Before coding:

- Re-read the current `AgentTool` protocol.
- Inspect both concrete tool implementations.
- Inspect the executor and intent-hash implementation.
- Inspect current test fixtures and conventions.
- Decide the smallest coherent validation contract.

Required test cases:

- Malformed JSON does not create a `STARTED` record.
- Schema-invalid arguments do not create a `STARTED` record.
- Valid arguments follow claim → execute → complete.
- Duplicate completed calls replay the stored result.
- Reused keys with different intent are rejected.

Do not assume a previously suggested method name or signature. Design from the current repository interfaces.

### Priority 2 — Test the Execution Ledger as a Reliability Boundary

Add focused tests for:

- First claim succeeds.
- Duplicate claim is handled safely.
- Same key with different tool/intent is rejected.
- Completed result is replayed without re-executing the side effect.
- Existing `STARTED` is not blindly executed again.
- `UNKNOWN` is not blindly retried.
- Completion only succeeds from the expected state.
- Database uniqueness and concurrency behavior.

Use existing fixtures and test database conventions.

### Priority 3 — Define Unknown-Outcome and Recovery Semantics

Explicitly define behavior for:

- Exception before a side effect is sent.
- Timeout while the downstream service may have committed.
- Process crash after downstream commit but before local completion.
- Stale `STARTED` records.
- Downstream status lookup.
- Reconciliation.
- Retry eligibility and backoff.

Do not turn `UNKNOWN` into an automatic retry.

An unknown outcome must be reconciled or safely deduplicated by the system that owns the side effect.

### Priority 4 — Complete Downstream Idempotency

The downstream order service must own durable deduplication for the idempotency key.

Ideally, deduplication and the order state change/result record should be committed atomically within the downstream service's transaction boundary.

The local Agent ledger alone cannot guarantee cross-service exactly-once behavior.

### Priority 5 — Wire gRPC Deliberately

When Jason chooses to move the runtime boundary:

- Add configuration for downstream endpoint and RPC timeout.
- Create a long-lived `grpc.aio` channel/stub in FastAPI lifespan.
- Close the channel during shutdown.
- Inject `GrpcOrderCommandGateway` through composition.
- Keep the `OrderCommandGateway` port stable.
- Add adapter and integration tests.
- Define TLS/mTLS and service identity before production use.

Do not start this wiring merely because the adapter class exists.

The current runtime still uses the local adapter.

### Priority 6 — Agent Run Recovery and Observability

After tool recovery semantics are defined:

- Decide which intermediate Agent states must be checkpointed.
- Define restart/reaper behavior for abandoned `RUNNING` runs.
- Add operational metrics and traces.
- Add structured events for Agent runs and tool executions.
- Define retention and sensitive-data handling for persisted prompts, arguments, and outputs.

## 4. Longer-Term Production Evolution

Potential future areas, to be designed when justified:

- Authentication and authorization.
- Service identity.
- Approval audit trails.
- Durable queues or outbox patterns.
- Workflow orchestration for asynchronous multi-service execution.
- Distributed tracing.
- Metrics and alerting.
- Operational dashboards.
- Containerization and deployment.
- CI and release/versioning.
- Environment promotion.
- Data retention, privacy, and redaction policies.

These are future directions, not claims about current implementation.

## 5. Learning Progression

The latest explicit learning milestone found in Git history is `Day 11.7`.

Preserve the existing step-by-step learning approach.

Do not skip to later topics or rewrite the learning roadmap without Jason's agreement.



## Historical Learning Curriculum Index — Day 1 to Day 11

This section records the actual learning sequence followed during the AI Backend Lab project. It is a historical curriculum index, not a newly designed syllabus.

The original day numbering and lesson order are preserved. Where historical records do not provide enough evidence, the missing details are explicitly marked rather than reconstructed by assumption.

### Status Legend

- **Completed** — explicitly confirmed as completed in the learning history.
- **In Progress** — the last confirmed learning status was in progress.
- **Recorded; Completion Unconfirmed** — the lesson was covered or implemented, but no explicit final completion confirmation was recovered.
- **Planned** — part of the recorded future learning sequence, not confirmed as completed.
- **Not Recovered** — the original lesson title or content could not be reliably recovered.

---

### Day 1 — Python Project Setup and First Implementation

**Recovered content; formal lesson title not recorded.**

- Python project initialization with `uv init`
- Virtual environment and `.venv`
- Python package structure under `src/ai_backend_lab/`
- Package initialization with `__init__.py`
- Running Python modules with `uv run`
- First function implementation: `get_large_orders(amounts)`
- Filtering order amounts greater than or equal to 100
- Expected result verification: `[120.0, 300.0, 180.0]`

**Status:** Exercise started and execution recorded; formal completion confirmation not recovered.

### Day 2 — Historical Lesson Record

The original Day 2 lesson title, subtopics, and exercise details could not be recovered reliably.

**Status:** Not Recovered. Do not invent a replacement lesson.

### Day 3 — Python OOP and Engineering Foundations

The original Day 3 material was reorganized into Day 3A and Day 3B to preserve a clearer learning sequence.

#### Day 3A — Python OOP / Domain Model

- Instance methods and `self`
- `@staticmethod`
- `@classmethod`
- `@property`
- Dataclass fundamentals and deeper usage
- Mutable vs. frozen dataclasses
- `default_factory`
- Refactoring domain logic using appropriate object-oriented design

**Status:** Completed.

#### Day 3B — Python Engineering Basics

- `pyproject.toml`
- Dependency management with `uv`
- Python project and package structure
- Module imports and package organization
- `pytest` fundamentals
- Unit testing
- Exception testing
- Fixtures and `conftest.py`
- Test naming conventions
- Arrange–Act–Assert (AAA) pattern
- Small-scale test refactoring

**Status:** Completed. Historical test results included four passing tests.

**Numbering note:** Some of this material was originally introduced under Day 4, then explicitly renumbered as Day 3B. Preserve Day 3B as the canonical numbering.

### Day 4 — API Schema and Domain Boundary

Some original Day 4 numbering was affected by the Day 3B renumbering.

#### Original Day 4.1–4.4

These topics were moved to Day 3B:

- Day 3B.1 — `pyproject.toml` and `uv` dependency management
- Day 3B.2 — `pytest` fundamentals
- Day 3B.3 — Unit tests and exception tests
- Day 3B.4 — Small-scale test refactoring

#### Day 4.5–4.6

Original lesson titles and contents were not recovered.

**Status:** Not Recovered.

#### Day 4.7 — API Schema / Domain Boundary

- Domain model vs. API response contract
- Why domain `Order` should not automatically become the public API response
- Introducing `OrderResponse`
- Pydantic `response_model`
- Matching route return types to response DTOs
- Handling `None` without mechanically converting every `None` into HTTP 404
- Distinguishing optional business results from resource-not-found semantics

**Status:** Completed.

### Day 5 — FastAPI API Layer and Application Boundaries

#### Day 5.1 — POST Request Body and Pydantic Validation

- `CreateOrderRequest`
- `POST /orders`
- JSON request body parsing
- Pydantic model validation
- `Field` constraints such as `min_length` and `gt`
- HTTP 201 response
- Swagger UI testing with valid and invalid requests

**Status:** Completed.

#### Day 5.2 — API Validation vs. Domain Validation

- API-level input validation
- Domain-level business invariants
- `InvalidOrderAmountError`
- Domain factory validation
- Unit testing domain invariants with pytest

**Status:** Completed.

#### Day 5.3 — HTTP Exception Handling

- FastAPI `HTTPException`
- HTTP status codes
- Separating HTTP errors from business logic

**Status:** Completed.

#### Day 5.4 — Domain Exception to HTTP Mapping

- Domain and application exceptions
- `OrderNotFoundError`
- `OrderCannotBeCancelledError`
- Global FastAPI exception handlers
- Mapping domain exceptions to HTTP 404 and 409
- Keeping routes free of duplicated business checks and repetitive `try/except` blocks

**Status:** Recorded; final completion confirmation not recovered.

#### Day 5.5 — Dependency Injection

- FastAPI `Depends`
- `Annotated`
- Dependency graph
- Injecting application services and repositories
- Keeping construction/wiring separate from business logic
- Routes depending on an application service rather than constructing infrastructure themselves

**Status:** Recorded; final completion confirmation not recovered.

#### Day 5.6 — Repository Pattern

- `OrderRepository` abstraction
- `InMemoryOrderRepository`
- Application services depending on repository abstractions
- Separating domain models from API response DTOs
- Mapping domain `Order` to `OrderResponse`
- Testing order lookup, missing orders, cancellation errors, and status changes

**Status:** Recorded; final completion confirmation not recovered.

**Historical note:** A possible Day 5.7 dependency-provider follow-up was discussed, but its formal inclusion and completion were not confirmed. It is therefore excluded from the canonical Day 5 sequence.

### Day 6 — Database Persistence and Unit of Work

#### Day 6.1 — SQLAlchemy / JPA Concepts

- SQLAlchemy fundamentals
- Relating SQLAlchemy concepts to familiar JPA patterns

#### Day 6.2 — Domain Model vs. ORM Model

- Domain model responsibilities
- ORM persistence model responsibilities
- Separating business objects from database mapping

#### Day 6.3 — Docker MySQL and SQLAlchemy Engine

- Running MySQL with Docker
- Database connection configuration
- `DATABASE_URL`
- SQLAlchemy Engine
- Database connection verification

#### Day 6.4 — SQLAlchemy ORM Model and Alembic Migration

- ORM model definition
- Table mapping
- Alembic initialization and configuration
- Migration generation
- Applying database migrations

#### Day 6.5 — Session and CRUD

- SQLAlchemy Session lifecycle
- Create, read, update, and delete
- Persistence operations
- Commit and rollback fundamentals

#### Day 6.6 — SQLAlchemy Repository

- Repository abstraction
- SQLAlchemy repository implementation
- Mapping between domain and persistence models

#### Day 6.7 — Transaction and Basic Unit of Work

- Transaction boundaries
- Commit and rollback
- Basic Unit of Work pattern

#### Day 6.8 — Large-Project Unit of Work and Composition Root

- Unit of Work as a transaction boundary
- Repositories independent from the Unit of Work
- Sharing a SQLAlchemy Session across repositories
- Assembling repositories and services in a Composition Root

#### Day 6.9 — FastAPI Request-Scoped Database Integration

- Request-scoped Session lifecycle
- FastAPI database dependency
- Composition of repositories, Unit of Work, and application services
- Ensuring the request owns the appropriate Session lifecycle

#### Day 6.10 — Layered Database Testing

- Domain tests
- Application tests using fakes
- Infrastructure integration tests with MySQL
- API tests using FastAPI TestClient
- Verifying transaction and persistence behavior

**Status:** Day 6.1–6.10 completed. The learning history explicitly records successful tests and formal Day 6 completion.

### Day 7 — Production-Oriented FastAPI Architecture

#### Day 7.1 — APIRouter

- Separating route modules
- `APIRouter`
- `include_router`
- Prefixes and tags
- Keeping application startup and health endpoints in the main application module

#### Day 7.2 — Composition Root and Dependency Boundaries

- Introducing `composition.py`
- Composition Root responsibility
- Separating application construction from FastAPI dependencies
- `api/dependencies.py`
- `OrderServiceDep`
- Dependency chain:
  Router → provider → `build_order_service` → Unit of Work → application service

#### Day 7.3 — Configuration Management

- `pydantic-settings`
- `BaseSettings`
- `.env`
- `.env.example`
- Environment-variable precedence
- Required `database_url`
- `@lru_cache`
- Keeping secrets out of Git

#### Day 7.4 — FastAPI Lifespan and Engine Lifecycle

- FastAPI startup and shutdown
- Application-scoped resources
- SQLAlchemy Engine lifecycle
- `engine.dispose()`
- Avoiding resource initialization during module import
- Managing long-lived application resources

#### Day 7.5 — API Error Contract

- Unified API error response
- Error code, message, and HTTP status
- Domain exception to API error mapping
- Global exception handlers
- Distinguishing 404, 409, and 422
- Keeping domain exceptions independent of HTTP

#### Day 7.6 — Database Constraints and Error Handling

- Database-level constraints
- Persistence errors
- Translating database failures into appropriate application/API behavior

#### Day 7.7 — ID Strategy

- Database-generated `BIGINT AUTO_INCREMENT` identifiers
- Unique business `order_number`
- Avoiding `len(repository.find_all()) + 1`
- Concurrency risks of application-generated sequential IDs
- Migration and schema evolution
- Mapper, repository, and API/test updates

#### Day 7.8 — Pagination, Filtering, and Sorting

- Pagination parameters
- Filtering
- Sorting
- Repository query behavior
- API query contract
- Dedicated pagination and sorting tests

#### Day 7.9 — Logging and Request Context

- Application logging
- Request context
- Request-level correlation
- Propagating useful context through application operations

#### Day 7.10 — Testing and Final Verification

- API and repository tests
- Layered test coverage
- Ruff verification
- Full pytest verification
- Closing remaining pagination and sorting test gaps

**Status:** Day 7.1–7.10 completed. Final history explicitly confirmed all tests and lint checks passed, with no remaining Day 7 TODOs.

### Day 8 — Async External Service Integration

#### Day 8.1 — Core Async/Await Mechanics

- Python asynchronous execution
- `async` and `await`
- Event-loop fundamentals

#### Day 8.2 — FastAPI `def` vs. `async def`

- Synchronous route execution
- Asynchronous route execution
- Blocking vs. non-blocking I/O
- Choosing the appropriate execution model

#### Day 8.3 — External Service Port / RiskGateway

- Defining an external-service port
- `RiskGateway`
- Keeping application logic independent of the external transport

#### Day 8.4 — HTTPX AsyncClient and HttpRiskGateway

- `httpx.AsyncClient`
- HTTP adapter implementation
- External risk-service integration
- Request and response mapping

#### Day 8.5 — AsyncClient Application Lifecycle

- Long-lived HTTP client
- Application-level resource ownership
- Client initialization and shutdown
- Reusing connections

#### Day 8.6 — Timeout

- External-service timeout
- Bounded waiting
- Timeout configuration
- Failure behavior when a dependency does not respond

#### Day 8.7 — Retry, Exponential Backoff, and Jitter

- Retry policy
- Exponential backoff
- Jitter
- Bounded retry attempts
- Tenacity
- Retrying only appropriate transient failures, such as connection/timeouts and selected HTTP statuses (429, 502, 503, 504)
- Keeping retry policy inside the infrastructure adapter rather than the application service

#### Day 8.8 — External Error Translation

- Mapping external-service failures into application-level errors
- Transient failure mapping
- `RiskServiceUnavailableError`
- HTTP 503 behavior
- Handling invalid status codes and malformed responses

#### Day 8.9 — Concurrent External Calls

- `asyncio.gather`
- `asyncio.TaskGroup`
- Concurrent external-service requests
- Understanding concurrency boundaries and failure behavior

#### Day 8.10 — External Service Testing

- Fake external-service implementations
- HTTPX `MockTransport`
- Successful and rejected responses
- Retry followed by success
- Timeout exhaustion
- No-retry behavior for authentication failures
- Invalid JSON and invalid response schema
- Deterministic external-service tests

#### Day 8.11 — Day 8 Wrap-up

- Consolidating the external-service architecture
- Reviewing async lifecycle, timeout, retry, error translation, concurrency, and tests

**Status:** Day 8.1–8.11 completed. The final session confirmed 8.9 and 8.10 completion and formally closed Day 8 before Day 9 began.

### Day 9 — LLM Backend Integration

#### Day 9.1 — LLM Integration Architecture

- Treating the LLM as an external backend capability
- Application and infrastructure boundaries
- Provider-independent application design

#### Day 9.2 — LLMGateway

- Defining the `LLMGateway` port
- LLM request/response contract
- Keeping provider SDK details outside application services

#### Day 9.3 — LLM Adapter

- Implementing the provider adapter
- OpenAI integration
- Mapping provider requests and responses

#### Day 9.4 — LLM Lifecycle and Configuration

- Client lifecycle
- API key and model configuration
- Application-level resource management

#### Day 9.5 — Messages, Roles, and Prompts

- Message structures
- System/user/assistant roles
- Prompt construction
- Conversation input

#### Day 9.6 — Structured Output

- Structured LLM responses
- Schema-constrained output
- Parsing and validation

#### Day 9.7 — Prompt Management

- Prompt organization
- Prompt templates
- Separating prompt content from orchestration code

#### Day 9.8 — Timeout, Retry, and Error Handling

- LLM timeout
- Retry boundaries
- Provider failure classification
- Application-level error translation

#### Day 9.9 — Token, Cost, and Latency Tracking

- Token usage
- Cost awareness
- Latency measurement
- Usage metadata

#### Day 9.10 — Streaming

- Streaming LLM responses
- Incremental output
- Streaming lifecycle and error considerations

#### Day 9.11 — Tool / Function Calling

- LLM tool-call responses
- Function-calling concepts
- Tool-call arguments and results

#### Day 9.12 — Tool / Application Boundary

- Separating model decisions from application execution
- Application-controlled tool execution
- Keeping business logic outside prompts

#### Day 9.13 — LLM Testing

- Fake LLM gateways
- Deterministic tests
- Avoiding unnecessary real provider calls

#### Day 9.14 — Small LLM Feature

- `POST /order-assistant/ask`
- `OrderAssistantService.answer_with_tools()`
- API schema and router
- Tool-enabled LLM interaction
- API tests

#### Day 9.15 — Day 9 Wrap-up

- Reviewing the LLM integration architecture
- Consolidating structured output, streaming, tool calling, error handling, and testing

**Status:** Day 9.1–9.15 completed. The small LLM feature and its tests were implemented, and Day 9 was formally declared complete.

### Day 10 — Agent Runtime

Day 10 introduced the formal Agent runtime, building on the LLM Gateway and Tool Calling work from Day 9.

#### Day 10.1 — Agent / Agent Loop

- Agent fundamentals
- Agent execution loop
- Model-driven next-step decisions

#### Day 10.2 — Agent State / Turn State

- `AgentState`
- Turn state
- Separating current execution state from conversation messages
- State transitions

#### Day 10.3 — Tool Registry and Executor

- Tool registry
- Tool definitions
- Tool lookup and dispatch
- Separating tool registration from execution

#### Day 10.4 — Agent Loop Implementation

- Connecting the LLM gateway and tool executor
- Repeated model/tool interaction
- Continuing or terminating an Agent turn

#### Day 10.5 — Stop Conditions and Maximum Steps

- Agent step budget
- Maximum-step protection
- Stop conditions
- Preventing unbounded Agent loops

#### Day 10.6 — Multi-Tool Execution

- Multiple tool calls
- Tool execution orchestration
- Tool result collection

#### Day 10.7 — Side-Effect Tools and Human Approval

- Read-only vs. side-effect tools
- Tool execution policies
- Approval requirements
- Pausing before sensitive actions

#### Day 10.8 — Tool Error and Recovery

- Tool execution errors
- Error propagation
- Agent recovery behavior
- Avoiding uncontrolled repeated execution

#### Day 10.9 — Conversation History

- Conversation messages
- Maintaining context across Agent turns
- Passing relevant history to the LLM

#### Day 10.10 — Streaming

- Agent event streaming
- Incremental execution events
- Streaming model and tool activity

#### Day 10.11 — Observability and Trace

- Agent execution tracing
- Tool-call visibility
- Execution diagnostics
- Structured execution events

#### Day 10.12 — Persistence and Checkpoint

- Durable Agent state
- Checkpoint serialization
- Database persistence
- Restoring execution state

#### Day 10.13 — Agent Testing

- Testing Agent orchestration
- Fake LLM gateway
- Fake tools
- Testing state transitions and tool execution
- Deterministic Agent tests

#### Day 10.14 — Complete Order Agent API

- Order Agent application integration
- Agent API schemas
- API router
- Dependency and composition wiring
- Start, resume, and get-run endpoints
- API integration tests

#### Day 10.15 — Day 10 Wrap-up

- Reviewing Agent runtime architecture
- Consolidating Agent loop, state, tools, approval, persistence, streaming, and testing

**Status:** Day 10.1–10.15 completed. The complete Agent Runtime learning sequence was explicitly marked 100% complete.

### Day 11 — Reliable Agent Actions

Day 11 focuses on reliable side-effect execution, idempotency, execution records, distributed service boundaries, and recovery.

#### Day 11.1 — Checkpoint Is Not Idempotency

- Difference between Agent checkpointing and side-effect idempotency
- Agent lifecycle vs. individual tool execution lifecycle
- Crash window between business side effect and Agent checkpoint persistence
- Why a separate execution ledger is required
- Unknown execution outcome

**Status:** Completed.

#### Day 11.2 — Tool Execution Ledger

- `ToolExecutionRecord`
- `ToolExecutionStatus`
- STARTED / COMPLETED / UNKNOWN
- Immutable execution records
- `ToolExecutionStore` port
- Store operations: `get`, `create`, and `complete`

**Status:** Completed.

#### Day 11.3 — Idempotency Key and Intent Fingerprint

- Logical execution identity: `(run_id, call_id)`
- Canonical JSON arguments
- Stable intent representation
- SHA-256 `intent_hash`
- Same key with the same intent
- Same key with a different intent must produce a conflict

**Status:** Completed.

#### Day 11.4 — ToolExecutionStore and Database Model

- `tool_executions` database table
- Composite primary key
- Foreign-key relationship
- Tool name and intent hash
- Execution status
- Output persistence
- Timestamps
- SQLAlchemy store implementation
- Alembic migration

**Status:** Completed.

#### Day 11.5 — Claim / Execute / Record / Replay

- Claiming an execution as STARTED
- Executing the logical tool action
- Recording COMPLETED output
- Replaying completed results
- Rejecting idempotency-key reuse with a different intent
- Blocking blind re-execution of STARTED or UNKNOWN records

**Status:** Completed.

#### Day 11.6 — ToolExecutor Integration

- Integrating `ToolExecutionStore` into `ToolExecutor`
- Intent validation and fingerprinting
- STARTED claim before side-effect execution
- COMPLETED result persistence
- Completed-result replay
- Intent conflict handling
- Blocking unsafe retries for unresolved execution records
- Propagating execution context through Agent run, resume, and streaming
- Production wiring with `SqlAlchemyToolExecutionStore`

**Status:** Completed.

#### Day 11.7 — Downstream Gateway / RPC Idempotency

- `OrderCommandGateway` application port
- `CancelOrderCommand`
- `CancelOrderResult`
- `AgentToolContext`
- Stable idempotency key propagation: `run_id:call_id`
- `LocalOrderCommandGateway`
- `GrpcOrderCommandGateway`
- Protobuf service contract
- `OrderCommandService.CancelOrder`
- Downstream request/response mapping
- Transport-independent application design

**Status:** In Progress at the last confirmed learning checkpoint (October 20, 2026).

**Important implementation boundary:** The local and gRPC adapter paths and Protobuf contract were introduced, but production gRPC composition/lifecycle wiring and downstream durable deduplication were not confirmed as complete. Do not describe end-to-end distributed idempotency as implemented.

#### Day 11.8 — Unknown Outcome and Reconciliation

- Persisting UNKNOWN execution outcomes
- Distinguishing definite failure from uncertain execution
- Reconciliation workflow
- Resolving whether a downstream side effect actually occurred

**Status:** Planned.

#### Day 11.9 — External API Idempotency

- Propagating idempotency keys to external services
- Downstream durable deduplication
- Atomic relationship between deduplication and business mutation

**Status:** Planned.

#### Day 11.10 — Stuck-Run Recovery

- Detecting stuck Agent runs
- Recovering interrupted execution
- Handling stale RUNNING states
- Safe recovery boundaries

**Status:** Planned.

#### Day 11.11 — Retry Policy

- Safe retry conditions
- Retry limits
- Retry behavior for transient failures
- Reusing stable idempotency keys
- Avoiding retries when execution outcome is unknown

**Status:** Planned.

#### Day 11.12 — Audit and Observability

- Execution audit trail
- Tool execution status visibility
- Correlation across Agent and downstream service boundaries
- Operational diagnostics

**Status:** Planned.

#### Day 11.13 — Failure and Concurrency Testing

- Duplicate execution requests
- Concurrent claims
- Conflicting intents
- Crash and timeout simulation
- Unknown outcome scenarios
- Downstream retry behavior

**Status:** Planned.

#### Day 11.14 — Resilient Cancel Flow

- End-to-end order cancellation
- Agent-side execution ledger
- Downstream gateway
- Durable downstream idempotency
- Failure recovery
- Reliable side-effect execution

**Status:** Planned.

#### Day 11.15 — Day 11 Wrap-up

- Reviewing reliable Agent action architecture
- Consolidating idempotency, execution ledger, gateway boundaries, recovery, retry, audit, and testing

**Status:** Planned.

---

### Curriculum Progress Summary

| Day | Main Focus | Last Confirmed Status |
|---|---|---|
| Day 1 | Python setup and first function | Exercise started |
| Day 2 | Historical lesson record | Not recovered |
| Day 3A | Python OOP / Domain Model | Completed |
| Day 3B | Python Engineering Basics | Completed |
| Day 4 | API Schema / Domain Boundary | Day 4.7 completed; 4.5–4.6 not recovered |
| Day 5 | FastAPI API Layer / Application Boundaries | 5.1–5.3 completed; 5.4–5.6 completion unconfirmed |
| Day 6 | SQLAlchemy / MySQL / Unit of Work | Completed |
| Day 7 | Production-Oriented FastAPI Architecture | Completed |
| Day 8 | Async External Service Integration | Completed |
| Day 9 | LLM Backend Integration | Completed |
| Day 10 | Agent Runtime | Completed |
| Day 11 | Reliable Agent Actions | 11.1–11.6 completed; 11.7 in progress; 11.8–11.15 planned |

### Historical Accuracy Rules

- Preserve the original Day 3A / Day 3B split.
- Do not restore Day 3B topics to Day 4.1–4.4.
- Do not invent Day 2 or Day 4.5–4.6 lesson titles.
- Do not mark Day 5.4–5.6 as explicitly completed without further evidence.
- Keep Day 11.7 separate from the downstream durable idempotency work that remains incomplete.
- Recheck the current repository and learning history before changing any status from In Progress or Planned to Completed.