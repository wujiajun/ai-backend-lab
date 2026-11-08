# Handoff — AI Backend Lab

## 1. Purpose

This document provides the context needed for Claude to take over the AI Backend Lab project without losing the user's learning history, engineering goals, or current implementation context.

Claude should read this document together with:

- `CLAUDE.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/LEARNING_HISTORY.md`
- `docs/DECISIONS.md`

This document is a handoff snapshot.

It must be updated when the actual project state changes.

## 2. Project

**Project:** AI Backend Lab

**Repository:**

`https://github.com/wujiajun/ai-backend-lab`

The project combines:

1. Agent Engineering learning.
2. Production-oriented backend architecture development.

The long-term goal is a reliable Agent Runtime with persistent state, tool execution tracking, idempotency, approval, recovery, observability, and distributed service integration.

## 3. User Profile for Technical Collaboration

The user has approximately 20 years of software engineering experience and approximately 18 years of Java/backend/database experience.

The user is familiar with:

- Java.
- Spring Boot.
- Dubbo.
- Distributed services.
- Redis.
- RabbitMQ.
- Elasticsearch.
- MySQL.
- Docker.
- Kubernetes.
- Jenkins.

Do not teach basic programming concepts unnecessarily.

Focus on:

- Architecture.
- Engineering trade-offs.
- Runtime behavior.
- Reliability.
- Failure handling.
- Concurrency.
- Testing.
- Practical implementation.

Default explanation language is Chinese.

Source code, identifiers, and technical naming should normally remain in English.

## 4. Collaboration Rules

The user expects a structured learning process.

Mandatory rules:

- Preserve the existing Day and lesson sequence.
- Do not skip lessons.
- Do not change lesson numbering.
- Do not silently replace the agreed learning plan.
- Explain the engineering problem before implementation.
- Inspect actual source code before commenting on current implementation.
- Inspect tests and the real call chain.
- Clearly distinguish implemented, partially implemented, planned, and unknown.
- Do not claim tests pass unless they have actually been run.
- Do not modify files, commit, push, or create PRs without explicit authorization.

A request to review or explain code is not permission to modify the repository.

## 5. Historical Repository Snapshot

The last known repository inspection referenced:

`358736ef321610bf34ac70b4b0180a07ff76130d`

The commit message was:

`fix: update project description in pyproject.toml for clarity`

The commit timestamp was:

`2026-10-20T23:33:11Z`

The last known explicit learning commit was associated with Day 11.7:

`21028c67f7`

These are historical references.

Claude must inspect the current Git state before assuming that this is still the latest version.

## 6. Historical Implementation Status

At the previous repository inspection, the following had been observed.

### 6.1 Backend Foundation

The project had implemented foundational backend components including:

- FastAPI application structure.
- SQLAlchemy persistence.
- MySQL integration.
- Alembic migrations.
- Application composition.
- FastAPI lifespan management.
- Centralized API exception handling.
- Request ID middleware and logging.

The actual current implementation must be verified.

### 6.2 External Integrations

The project had:

- `LLMGateway` abstraction.
- OpenAI-compatible LLM adapter.
- `RiskGateway` abstraction.
- HTTPX-based risk adapter.

The historical FastAPI lifespan created and closed the HTTPX client and asynchronous OpenAI client.

### 6.3 Agent Runtime

The project had:

- Agent run creation.
- Agent execution.
- Tool registry and tool execution.
- Agent run persistence.
- Approval waiting state.
- Resume behavior.
- Agent run retrieval.
- Maximum-step and termination handling.

The historical Agent API included:

- `POST /agent/runs`
- `POST /agent/runs/{run_id}/resume`
- `GET /agent/runs/{run_id}`

An event generator existed in `OrderAgentService`, but a streaming HTTP endpoint was not observed in the historical snapshot.

### 6.4 Tool Execution Ledger

The project had separate concepts for:

- `agent_runs`
- `tool_executions`

The historical tool execution identity was:

`(run_id, call_id)`

The ToolExecutor:

- Canonicalized JSON arguments.
- Computed a SHA-256 intent hash.
- Created a `STARTED` execution record.
- Executed the tool.
- Stored completed output.
- Replayed completed results.
- Rejected a reused identity with a different intent.
- Avoided blindly re-executing `STARTED` or `UNKNOWN` records.

### 6.5 Order Command Integration

The project had:

- `OrderCommandGateway` port.
- `LocalOrderCommandGateway`.
- gRPC adapter.
- Protobuf contract.

The known contract path was:

`contracts/proto/ai_backend_lab/contracts/order/v1/order_service.proto`

The contract defined:

`OrderCommandService.CancelOrder`

Generated Python files were under:

`src/ai_backend_lab/contracts/order/v1/`

However, at the previous inspection:

- Runtime composition still used `LocalOrderCommandGateway`.
- The gRPC adapter was not fully wired into the FastAPI composition.
- The FastAPI lifespan did not manage the gRPC channel and stub.
- A downstream gRPC server implementation was not present.
- Durable downstream deduplication was not implemented.

Therefore, the gRPC integration was partial.

## 7. Known Technical Issues to Recheck

These issues were identified in the previous repository inspection.

Do not assume they remain unchanged. Verify them first.

### 7.1 Tool Validation Order

Tool-specific Pydantic validation in `GetOrderTool.execute()` and `CancelOrderTool.execute()` appeared to occur after the ToolExecutor created a `STARTED` record.

This could leave a false `STARTED` record when input validation fails before any side effect.

Check whether validation has been moved before the execution claim.

### 7.2 UNKNOWN State Transition

The historical `ToolExecutionStore` exposed operations equivalent to:

- `get`
- `create`
- `complete`

A complete transition to `UNKNOWN` and a reconciliation workflow were not found.

Check the current implementation.

### 7.3 Recovery

The historical implementation did not provide complete recovery for:

- Agent runs left in `RUNNING`.
- Tool executions left in `STARTED`.
- Remote operations with uncertain outcomes.

### 7.4 Test Coverage

The previous inspection did not find a dedicated ToolExecutor test module or dedicated SQL ToolExecutionStore test module.

Check the current test tree.

Do not assume that tests are missing without inspecting the current repository.

### 7.5 gRPC Runtime Integration

Check whether the following now exist:

- gRPC channel lifecycle.
- Stub construction.
- Runtime composition selection.
- Downstream server.
- Durable downstream idempotency.
- Integration tests.

## 8. Current Learning Position

The learning history records:

- Day 1: initial Python project and function exercise; formal completion not confirmed.
- Day 2: historical details not recovered.
- Day 3A: Python OOP and domain model; completed.
- Day 3B: Python engineering basics; completed.
- Day 4.7: API schema and domain boundary; completed.
- Day 5.1–5.3: completed.
- Day 5.4–5.6: completion status not recovered.
- Day 6.1–6.10: completed.
- Day 7.1–7.10: completed.
- Day 8.1–8.11: completed.
- Day 9.1–9.15: completed.
- Day 10.1–10.15: completed.
- Day 11.1–11.6: completed.
- Day 11.7: in progress at the last recorded checkpoint.
- Day 11.8–11.15: planned.

The detailed lesson index is in `docs/LEARNING_HISTORY.md`.

Do not invent the missing Day 2 or Day 4.5–4.6 historical records.

## 9. First Session Checklist for Claude

When opening the project for the first time:

### Step 1 — Read the Documentation

Read all seven migration documents.

Identify:

- Project goals.
- User's technical background.
- Collaboration constraints.
- Historical learning sequence.
- Current known architecture.
- Open technical issues.

### Step 2 — Verify the Repository

Inspect:

- Current branch.
- `git status`.
- Current HEAD.
- Recent commits.
- Project structure.
- `pyproject.toml`.
- Application entry point.
- Configuration.
- Database models.
- Migrations.
- Relevant tests.

Do not make changes during this initial inspection unless the user explicitly requests them.

### Step 3 — Verify Day 11.7

Inspect:

- `OrderCommandGateway`.
- `LocalOrderCommandGateway`.
- The gRPC adapter.
- Protobuf definitions.
- Generated code.
- Composition.
- FastAPI lifespan.
- Downstream service implementation.
- Idempotency propagation.
- Tests.

Determine exactly what has changed since the historical snapshot.

### Step 4 — Verify Tool Execution Reliability

Inspect:

- ToolExecutor.
- Tool definitions.
- Input validation.
- ToolExecutionStore.
- Database model.
- Migrations.
- Execution state transitions.
- Replay behavior.
- Concurrency protection.
- Tests.

### Step 5 — Report Findings

Provide a concise report containing:

1. Current repository state.
2. What is implemented.
3. What is partially implemented.
4. What remains planned.
5. Whether the historical Day 11.7 status has changed.
6. The next appropriate learning step.
7. Any differences between the documentation and current source.

Do not modify files until authorized.

## 10. Recommended Initial Prompt for Claude

The following prompt can be used after opening the repository:

```text
Please take over the AI Backend Lab project.

First, read all seven project documents:

- CLAUDE.md
- docs/PROJECT_CONTEXT.md
- docs/ARCHITECTURE.md
- docs/ROADMAP.md
- docs/HANDOFF.md
- docs/LEARNING_HISTORY.md
- docs/DECISIONS.md

Do not modify any files yet.

Inspect the actual repository, current Git state, source code, and relevant tests.

The historical handoff identifies Day 11.7 as the last in-progress lesson. Verify whether this is still accurate.

Pay particular attention to:

1. OrderCommandGateway and its adapters.
2. gRPC integration and application lifecycle.
3. ToolExecutor.
4. ToolExecutionStore.
5. Intent fingerprinting and replay behavior.
6. Tool input validation order.
7. UNKNOWN execution handling.
8. Agent run recovery.
9. Existing tests.

Report the actual current implementation status.

Distinguish implemented, partially implemented, planned, and unknown behavior.

Preserve the historical learning sequence. Do not skip or renumber lessons.

The user has approximately 20 years of software engineering experience, including approximately 18 years of Java/backend/database experience. Avoid beginner-level explanations and focus on architecture, engineering trade-offs, runtime behavior, reliability, and testing.

Use Chinese for explanations by default.

Do not modify files, commit, push, or create PRs without explicit authorization.

After the inspection, recommend the next appropriate step without changing the project.
```

## 11. Handoff Completion Rule

The handoff is complete only when Claude has:

- Read the project documents.
- Opened the actual repository.
- Verified the current Git state.
- Inspected the relevant source code.
- Inspected relevant tests.
- Reconciled the historical snapshot with the live implementation.

Reading these documents alone does not mean Claude has verified the project.

The repository remains the source of truth for implementation status.