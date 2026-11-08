# Learning History — AI Backend Lab

## 1. Purpose

This document records the historical Agent Backend learning curriculum from Day 1 through Day 11.

It preserves:

- Original lesson numbering.
- Learning order.
- Historical topics.
- Known completion status.
- Known implementation milestones.
- Missing historical information.

This document is a learning history, not a new syllabus.

Do not renumber lessons or invent missing historical topics.

## 2. Status Definitions

| Status | Meaning |
|---|---|
| Completed | Historical learning record indicates the lesson was completed. |
| In progress | The lesson had started but completion was not confirmed. |
| Planned | The lesson was part of the future learning sequence. |
| Unknown | Historical information is insufficient to determine the lesson or its status. |

A completed learning lesson does not automatically mean every related production feature is complete.

## 3. Day 1 — Python Project Setup and First Function

**Status:** Exercise started; formal completion not confirmed.

### Known topics

- Initial Python project setup.
- `uv init`.
- Project environment setup.
- Writing the first Python function.
- Basic function behavior.
- Filtering values from a collection.

### Known exercise

Function:

`get_large_orders(amounts)`

Expected behavior:

Return order amounts greater than or equal to `100`.

Example input:

```python
amounts = [80.0, 120.0, 300.0, 90.0, 180.0]
```

Expected output:

```python
[120.0, 300.0, 180.0]
```

The exercise was started.

The historical record does not confirm formal lesson completion.

## 4. Day 2 — Historical Record Not Recovered

**Status:** Unknown.

The detailed Day 2 lesson title and learning content were not recovered from the available historical records.

Do not invent a Day 2 topic.

Preserve the Day 2 placeholder until the original conversation, notes, or repository history can be recovered.

## 5. Day 3A — Python OOP and Domain Model

**Status:** Completed.

### Topics

- Python classes.
- Instance methods.
- `self`.
- Static methods.
- Class methods.
- Properties.
- Dataclasses.
- Frozen dataclasses.
- Mutable and immutable objects.
- `default_factory`.
- Domain model design.

### Learning objectives

Understand how Python models domain concepts and how Python's object model differs from familiar Java conventions.

Important areas included:

- Object behavior.
- Instance state.
- Class-level behavior.
- Encapsulation through properties.
- Dataclass-generated behavior.
- Mutable default pitfalls.
- Immutable domain objects.

### Completion

The historical learning record marks Day 3A as completed.

## 6. Day 3B — Python Engineering Basics

**Status:** Completed.

Day 3B was separated from the earlier Day 4 engineering-basics sequence.

The historical record indicates that these topics were originally numbered Day 4.1–4.4 and were later reorganized as Day 3B.

Do not treat them as additional lessons that need to be repeated.

### Topics

- `pyproject.toml`.
- Python project configuration.
- `uv`.
- Package structure.
- Import organization.
- pytest.
- Unit testing.
- Exception testing.
- Test fixtures.
- Arrange–Act–Assert (AAA).

### Learning objectives

Understand how to organize and test a maintainable Python backend project.

The focus was on engineering structure rather than isolated Python syntax.

### Completion

The historical learning record marks Day 3B as completed.

## 7. Day 4 — API and Application Boundary

### Day 4.1–4.4 — Historical Numbering Reorganization

**Status:** Completed under Day 3B.

These lessons correspond to the engineering-basics topics described in Day 3B.

The historical record indicates that the original Day 4.1–4.4 numbering was reorganized into Day 3B.

Do not duplicate these lessons in the current curriculum.

### Day 4.5–4.6

**Status:** Unknown.

The exact historical lesson titles and completion states were not recovered.

Do not invent their content.

### Day 4.7 — API Schema and Domain Boundary

**Status:** Completed.

### Topics

- API response schema.
- Domain model and API model separation.
- `OrderResponse`.
- Pydantic response models.
- FastAPI `response_model`.
- `None` versus HTTP 404.
- API contract design.

### Learning objectives

Understand why API response models should not automatically expose internal domain or persistence models.

Understand the distinction between:

- A resource that does not exist.
- A valid operation that produces no value.
- A response representation.
- An internal domain object.

The historical record marks Day 4.7 as completed.

## 8. Day 5 — FastAPI Application Design

### Day 5.1 — POST and Pydantic Request Validation

**Status:** Completed.

Topics:

- POST endpoint design.
- Request body.
- Pydantic request models.
- Input structure validation.

### Day 5.2 — API Validation vs Domain Validation

**Status:** Completed.

Topics:

- Request validation.
- Domain validation.
- Responsibilities of API and domain layers.
- Avoiding business rules in transport-layer schemas.

### Day 5.3 — HTTPException

**Status:** Completed.

Topics:

- FastAPI `HTTPException`.
- HTTP status codes.
- API-level error handling.

### Day 5.4 — Domain Exception Mapping

**Status:** Completion status not recovered.

Known topic:

- Mapping domain and application exceptions to API responses.
- Separating business errors from HTTP transport errors.
- Centralized error translation.

### Day 5.5 — Dependency Injection

**Status:** Completion status not recovered.

Known topic:

- Dependency injection.
- FastAPI dependency boundaries.
- Application dependency management.

### Day 5.6 — Repository Pattern

**Status:** Completion status not recovered.

Known topic:

- Repository abstraction.
- Persistence boundary.
- Application service interaction with repositories.
- Separation of business logic and database implementation.

The historical topic names are known, but formal completion of Day 5.4–5.6 was not confirmed.

## 9. Day 6 — SQLAlchemy and Database Engineering

**Status:** Day 6.1–6.10 completed.

### Day 6.1 — SQLAlchemy and JPA Concepts

Topics:

- SQLAlchemy overview.
- Comparison with familiar JPA/Hibernate concepts.
- ORM responsibilities.
- Session concepts.

### Day 6.2 — Domain Model vs ORM Model

Topics:

- Domain model.
- ORM persistence model.
- Mapping between domain and database representations.
- Avoiding infrastructure leakage into the domain.

### Day 6.3 — Docker MySQL and Engine

Topics:

- MySQL through Docker.
- SQLAlchemy Engine.
- Database connectivity.
- Connection configuration.

### Day 6.4 — ORM and Alembic

Topics:

- SQLAlchemy ORM.
- Alembic.
- Schema migration.
- Database schema evolution.

### Day 6.5 — Session and CRUD

Topics:

- SQLAlchemy Session.
- Create, read, update, and delete operations.
- Persistence lifecycle.

### Day 6.6 — Repository Implementation

Topics:

- Repository implementation.
- Persistence abstraction.
- Application-to-repository interaction.

### Day 6.7 — Transaction and Unit of Work

Topics:

- Transaction boundaries.
- Commit and rollback.
- Unit of Work concepts.
- Coordinating persistence operations.

### Day 6.8 — Unit of Work and Composition Root

Topics:

- Unit of Work in larger applications.
- Dependency construction.
- Composition root.
- Coordinating repositories and transactions.

### Day 6.9 — FastAPI Request-scoped Database Integration

Topics:

- Database dependency integration.
- Request-scoped Session.
- Session lifecycle.
- Dependency cleanup.

### Day 6.10 — Layered Testing

Topics:

- Database-related tests.
- Layered test strategy.
- Integration testing.
- Test setup and cleanup.

The historical record marks Day 6.1–6.10 as completed.

## 10. Day 7 — FastAPI Backend Architecture

**Status:** Day 7.1–7.10 completed.

### Day 7.1 — APIRouter

Topics:

- Route modularization.
- APIRouter.
- API organization.

### Day 7.2 — Composition Root and Dependency Boundaries

Topics:

- Composition root.
- Dependency construction.
- Layer boundaries.
- Explicit dependency wiring.

### Day 7.3 — Configuration

Topics:

- Application configuration.
- Environment-based configuration.
- Configuration management.

### Day 7.4 — Lifespan and Engine Lifecycle

Topics:

- FastAPI lifespan.
- Application startup.
- Application shutdown.
- Engine lifecycle.
- Resource ownership.

### Day 7.5 — API Error Contract

Topics:

- Consistent API errors.
- Error response contracts.
- Error handling boundaries.

### Day 7.6 — Database Constraints

Topics:

- Database-level constraints.
- Data integrity.
- Database constraints versus application validation.

### Day 7.7 — ID Strategy

Topics:

- Identifier strategy.
- ID generation.
- Identifier behavior in persistence and APIs.

### Day 7.8 — Pagination, Filtering, and Sorting

Topics:

- Pagination.
- Filtering.
- Sorting.
- Query parameter design.
- API query behavior.

### Day 7.9 — Logging and Request Context

Topics:

- Structured logging.
- Request context.
- Request ID.
- Traceability across application layers.

### Day 7.10 — Tests and Final Verification

Topics:

- Backend integration tests.
- Final verification.
- Reviewing architecture boundaries.
- Validating the completed backend foundation.

The historical record marks Day 7.1–7.10 as completed.

## 11. Day 8 — Asynchronous Programming and External Services

**Status:** Day 8.1–8.11 completed.

### Day 8.1 — async and await

Topics:

- Python asynchronous programming.
- Coroutines.
- `async`.
- `await`.

### Day 8.2 — FastAPI def vs async def

Topics:

- Synchronous endpoints.
- Asynchronous endpoints.
- Execution behavior in FastAPI.
- Blocking versus non-blocking operations.

### Day 8.3 — RiskGateway Port

Topics:

- External service abstraction.
- RiskGateway.
- Application-facing gateway contract.

### Day 8.4 — HTTPX AsyncClient and Adapter

Topics:

- HTTPX.
- AsyncClient.
- External HTTP integration.
- Adapter implementation.

### Day 8.5 — Client Lifecycle

Topics:

- HTTP client lifecycle.
- Resource reuse.
- Application startup and shutdown.
- Connection management.

### Day 8.6 — Timeout

Topics:

- External request timeout.
- Timeout configuration.
- Failure behavior.
- Timeout versus business failure.

### Day 8.7 — Retry, Backoff, and Jitter

Topics:

- Retry behavior.
- Exponential backoff.
- Jitter.
- Transient failures.
- Retry limitations.

Tenacity was included in the historical learning context.

### Day 8.8 — External Error Translation

Topics:

- External service errors.
- Error translation.
- Application-facing exceptions.
- Avoiding infrastructure error leakage.

### Day 8.9 — Concurrency

Topics:

- Concurrent external calls.
- Asynchronous execution.
- Concurrency control.
- Practical implications for backend services.

### Day 8.10 — Testing

Topics:

- External gateway tests.
- Mocking or controlling external dependencies.
- Asynchronous test behavior.

### Day 8.11 — Wrap-up

Topics:

- Review of asynchronous external service integration.
- Review of lifecycle and error handling.
- Review of tests.

The historical record marks Day 8.1–8.11 as completed.

## 12. Day 9 — LLM Integration

**Status:** Day 9.1–9.15 completed.

### Day 9.1 — LLM Architecture

Topics:

- LLM integration architecture.
- Application-to-LLM boundary.
- Provider abstraction.

### Day 9.2 — LLMGateway

Topics:

- LLMGateway port.
- Application-facing LLM interface.
- Separation of application logic and provider SDK.

### Day 9.3 — LLM Adapter and OpenAI Integration

Topics:

- OpenAI-compatible SDK.
- Provider adapter.
- Concrete LLM integration.

### Day 9.4 — Lifecycle and Configuration

Topics:

- LLM client configuration.
- Client lifecycle.
- Application resource management.

### Day 9.5 — Messages, Roles, and Prompts

Topics:

- Message structures.
- System, user, and assistant roles.
- Prompt construction.
- Conversation context.

### Day 9.6 — Structured Output

Topics:

- Structured responses.
- Schema-based output.
- Validation of LLM-generated data.

### Day 9.7 — Prompt Management

Topics:

- Prompt organization.
- Prompt management.
- Separation of prompts and application logic.

### Day 9.8 — Timeout, Retry, and Error Handling

Topics:

- LLM timeout.
- Retry behavior.
- Provider errors.
- Error translation.
- Failure handling.

### Day 9.9 — Token, Cost, and Latency

Topics:

- Token usage.
- LLM cost.
- Request latency.
- Usage observability.

### Day 9.10 — Streaming

Topics:

- Streaming responses.
- Incremental output.
- Streaming integration considerations.

### Day 9.11 — Tool and Function Calling

Topics:

- Tool calling.
- Function calling.
- Tool definitions.
- LLM-generated tool requests.
- Application-controlled execution.

### Day 9.12 — Application Boundary

Topics:

- Application orchestration.
- LLM boundary.
- Separation between LLM behavior and business logic.

### Day 9.13 — Testing

Topics:

- LLM integration testing.
- Controlled dependencies.
- Testing structured output and tool-call behavior.

### Day 9.14 — OrderAssistant Feature

Topics:

- Building an OrderAssistant feature.
- Integrating the LLM with an existing business use case.
- Applying the LLM architecture to an actual application flow.

### Day 9.15 — Wrap-up

Topics:

- Review of LLM integration.
- Review of provider abstraction.
- Review of tool calling.
- Review of the completed OrderAssistant feature.

The historical record marks Day 9.1–9.15 as completed.

## 13. Day 10 — Agent Engineering

**Status:** Day 10.1–10.15 completed.

### Day 10.1 — Agent Loop

Topics:

- Agent execution loop.
- LLM and tool interaction.
- Multi-step execution.

### Day 10.2 — Agent State

Topics:

- Agent state.
- Execution context.
- State persistence considerations.

### Day 10.3 — Tool Registry and Executor

Topics:

- Tool registry.
- Tool lookup.
- Tool execution boundary.
- Separation of tool definition and execution.

### Day 10.4 — Agent Loop Implementation

Topics:

- Implementing the Agent loop.
- Processing LLM responses.
- Handling tool calls.
- Continuing execution.

### Day 10.5 — Maximum Steps and Stop Conditions

Topics:

- Maximum execution steps.
- Termination conditions.
- Preventing infinite Agent loops.

### Day 10.6 — Multiple Tools

Topics:

- Multiple tool calls.
- Tool selection.
- Tool result handling.
- Multi-tool orchestration.

### Day 10.7 — Side-effecting Tools and Approval

Topics:

- Side-effecting tools.
- Tool execution policy.
- Human approval.
- Sensitive business operations.

### Day 10.8 — Tool Errors and Recovery

Topics:

- Tool execution errors.
- Error propagation.
- Agent behavior after tool failure.
- Recovery considerations.

### Day 10.9 — Conversation History

Topics:

- Conversation history.
- Message persistence.
- Context construction.
- Conversation continuity.

### Day 10.10 — Streaming

Topics:

- Agent streaming.
- Incremental output.
- Streaming considerations in multi-step execution.

### Day 10.11 — Observability and Trace

Topics:

- Agent execution observability.
- Traceability.
- Execution context.
- Tool-level visibility.

### Day 10.12 — Persistence and Checkpoint

Topics:

- Agent persistence.
- Checkpoints.
- State restoration.
- Resume considerations.

### Day 10.13 — Agent Testing

Topics:

- Agent loop tests.
- Tool execution tests.
- State transition tests.
- Controlled LLM behavior.

### Day 10.14 — Complete Order Agent API

Topics:

- Complete Order Agent API workflow.
- Agent run endpoints.
- Tool orchestration.
- Application integration.

### Day 10.15 — Wrap-up

Topics:

- Review of the Agent architecture.
- Review of the Order Agent implementation.
- Review of persistence and execution flow.

The historical record marks Day 10.1–10.15 as completed.

## 14. Day 11 — Idempotency and Reliable Tool Execution

Day 11 focuses on reliable side-effect execution.

The central problem:

An Agent may invoke a tool that changes business state. A process crash, network timeout, duplicate request, or retry can cause the same logical operation to be executed more than once.

The learning objective is to design an execution model that can distinguish completed work, incomplete work, and uncertain outcomes.

### Day 11.1 — Checkpoint vs Idempotency

**Status:** Completed.

Topics:

- Agent checkpoint.
- Tool execution record.
- Why checkpointing does not guarantee safe side-effect execution.
- Difference between workflow progress and business-operation deduplication.

### Day 11.2 — Execution Ledger

**Status:** Completed.

Topics:

- Tool execution ledger.
- Persisting individual tool calls.
- Execution identity.
- Execution status.
- Auditability.

### Day 11.3 — Idempotency Key and Intent Fingerprint

**Status:** Completed.

Topics:

- Idempotency key.
- Logical tool-call identity.
- Canonicalized arguments.
- Intent fingerprint.
- SHA-256 hashing.
- Detecting a reused key with different input.

### Day 11.4 — Database Model and Store

**Status:** Completed.

Topics:

- Tool execution database model.
- Tool execution persistence.
- Store abstraction.
- Database uniqueness.
- Execution record lifecycle.

### Day 11.5 — Claim, Execute, Record, and Replay

**Status:** Completed.

Topics:

- Claiming an execution.
- Executing a tool.
- Persisting completion.
- Replaying a completed result.
- Rejecting intent mismatch.
- Avoiding blind re-execution.

### Day 11.6 — ToolExecutor Integration

**Status:** Completed.

Topics:

- Integrating the execution ledger into ToolExecutor.
- Centralizing tool execution.
- Applying idempotency checks.
- Managing execution state.
- Connecting tool execution with Agent orchestration.

### Day 11.7 — Downstream Gateway / RPC Idempotency

**Status:** In progress at the last recorded checkpoint.

Topics:

- Downstream gateway abstraction.
- RPC boundary.
- Propagating idempotency information.
- Local versus remote execution.
- Protobuf service contract.
- gRPC adapter.
- Downstream deduplication requirements.

Known historical implementation evidence:

- `OrderCommandGateway` port.
- `LocalOrderCommandGateway`.
- gRPC adapter.
- Protobuf `OrderCommandService.CancelOrder` contract.
- Generated Python contract files.

Known historical limitations:

- The application composition still used the local gateway.
- The gRPC adapter was not fully wired into runtime composition.
- The FastAPI lifespan did not manage the gRPC channel and stub.
- A downstream gRPC server was not present in the inspected snapshot.
- Durable downstream deduplication was not implemented.

The lesson must not be marked complete merely because the contract and client adapter exist.

### Day 11.8 — Unknown Outcome and Reconciliation

**Status:** Planned.

Topics:

- Unknown execution outcome.
- Timeout ambiguity.
- Local and remote state reconciliation.
- Safe handling of uncertain operations.

### Day 11.9 — External API Idempotency

**Status:** Planned.

Topics:

- Cross-service idempotency.
- Idempotency-key propagation.
- Downstream durable deduplication.
- Duplicate request replay.

### Day 11.10 — Stuck-run Recovery

**Status:** Planned.

Topics:

- Stale Agent runs.
- Stale tool executions.
- Recovery ownership.
- Safe resume.
- Recovery concurrency.

### Day 11.11 — Retry Policy

**Status:** Planned.

Topics:

- Retryable and non-retryable errors.
- Backoff.
- Jitter.
- Retry budgets.
- Idempotency-aware retry behavior.

### Day 11.12 — Audit and Observability

**Status:** Planned.

Topics:

- Agent audit trail.
- Tool execution audit trail.
- Correlation.
- Structured logs.
- Execution metrics.
- Operational visibility.

### Day 11.13 — Failure and Concurrency Tests

**Status:** Planned.

Topics:

- Failure injection.
- Duplicate calls.
- Concurrent claims.
- Timeout after downstream success.
- Concurrent resume.
- Recovery tests.

### Day 11.14 — Resilient Cancel Flow

**Status:** Planned.

Topics:

- Complete cancellation workflow.
- Approval.
- Idempotent execution.
- Unknown outcomes.
- Reconciliation.
- Recovery.
- Auditability.

### Day 11.15 — Wrap-up

**Status:** Planned.

Topics:

- Complete Day 11 architecture review.
- Review idempotency design.
- Review failure handling.
- Review recovery.
- Review tests.
- Document remaining limitations.

## 15. Overall Historical Progress Summary

| Day / Section | Historical status |
|---|---|
| Day 1 | Exercise started; formal completion unknown |
| Day 2 | Historical content not recovered |
| Day 3A | Completed |
| Day 3B | Completed |
| Day 4.1–4.4 | Reorganized into Day 3B |
| Day 4.5–4.6 | Unknown |
| Day 4.7 | Completed |
| Day 5.1–5.3 | Completed |
| Day 5.4–5.6 | Completion not confirmed |
| Day 6.1–6.10 | Completed |
| Day 7.1–7.10 | Completed |
| Day 8.1–8.11 | Completed |
| Day 9.1–9.15 | Completed |
| Day 10.1–10.15 | Completed |
| Day 11.1–11.6 | Completed |
| Day 11.7 | In progress at last recorded checkpoint |
| Day 11.8–11.15 | Planned |

## 16. Historical Record Integrity Rules

This document is reconstructed from available historical learning records and repository evidence.

Some lesson titles or completion states were not recovered.

The following must remain explicitly unknown until supporting evidence is found:

- Day 2 detailed content.
- Day 4.5–4.6 detailed content.
- Day 5.4–5.6 completion status.
- Formal Day 1 completion status.

Do not fill these gaps with a newly invented curriculum.

If the original conversations, lesson notes, or commits are recovered later:

1. Compare the recovered evidence with this document.
2. Update only the affected entries.
3. Preserve original numbering.
4. Record the source of the correction where useful.

The purpose of this document is to preserve the actual learning journey, not to create a cleaner but historically inaccurate syllabus.