# Architecture — AI Backend Lab

## 1. Purpose

This document describes the architectural direction and the last known implementation state of AI Backend Lab.

It is intended to help contributors understand:

- The major architectural layers.
- The responsibilities of core components.
- How an Agent run is executed.
- How tools are invoked.
- How side effects are tracked.
- How idempotency is handled.
- What is implemented and what remains incomplete.

This document must be updated when the actual architecture changes.

**Important:** Implementation descriptions below are based on a historical repository inspection. Re-inspect the current source before treating any detail as current.

## 2. Architectural Principles

The project follows these principles:

1. Separate business logic from infrastructure.
2. Keep application orchestration independent of vendor SDKs.
3. Use ports and adapters at meaningful boundaries.
4. Make resource lifecycle explicit.
5. Persist long-running Agent execution state.
6. Track side-effecting tool executions independently.
7. Treat retries and duplicate requests as reliability problems.
8. Do not assume exactly-once execution.
9. Test failure scenarios, not only successful responses.
10. Keep the architecture understandable and maintainable.

## 3. High-level Architecture

The intended architecture is:

```text
                    Client
                      |
                      v
                FastAPI API Layer
                      |
                      v
             Application Services
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Agent       Order       Application
       Service     Service      Policies
          |
          v
       Agent Loop
          |
          v
      LLMGateway
          |
          v
      LLM Adapter
          |
          v
      External LLM Provider

Agent Loop
    |
    v
 Tool Registry
    |
    v
 Tool Executor
    |
    +-----------------------------+
    |              |              |
    v              v              v
 Tool A         Tool B         Tool C
    |              |              |
    v              v              v
 Application   Gateway        Gateway
 Services      / Adapter      / Adapter

Persistence:
    |
    +-- Agent Runs
    |
    +-- Agent Checkpoints
    |
    +-- Tool Executions
    |
    +-- Business Data
```

This is a conceptual architecture. The actual source code and dependency wiring remain authoritative.

## 4. Architectural Layers

### 4.1 API Layer

Responsibilities:

- Expose HTTP endpoints.
- Validate incoming request structure.
- Resolve request-scoped dependencies.
- Translate application results into HTTP responses.
- Map application and domain errors to API error contracts.

The API layer should not contain business workflows or vendor-specific LLM orchestration.

The Agent API historically included:

- `POST /agent/runs`
- `POST /agent/runs/{run_id}/resume`
- `GET /agent/runs/{run_id}`

Verify the current route definitions before relying on these paths.

### 4.2 Application Layer

Responsibilities:

- Coordinate use cases.
- Manage Agent execution.
- Apply application-level policies.
- Coordinate repositories and gateways.
- Manage transaction boundaries.
- Coordinate approval and resume operations.

Application services should depend on abstractions rather than concrete external SDKs.

Examples observed in the project include:

- Agent run orchestration.
- Order Agent orchestration.
- Tool execution coordination.
- Order command coordination.

### 4.3 Domain Layer

Responsibilities:

- Represent business concepts.
- Encapsulate business rules.
- Define domain-level validation.
- Avoid infrastructure dependencies.

Domain models should not depend on FastAPI, HTTPX, OpenAI SDKs, or database sessions.

### 4.4 Ports

Ports define the interfaces through which application logic interacts with external capabilities.

Examples observed in the project include:

- `LLMGateway`
- `RiskGateway`
- `OrderCommandGateway`
- `ToolExecutionStore`

Ports should express application needs rather than expose vendor-specific SDK details.

### 4.5 Infrastructure Adapters

Adapters implement ports using concrete technologies.

Examples include:

- OpenAI-compatible LLM adapter.
- HTTPX-based risk adapter.
- Local order command adapter.
- gRPC order command adapter.
- SQLAlchemy persistence adapters.

The application should be able to select an implementation through composition rather than changing its business logic.

## 5. LLM Integration

### 5.1 LLMGateway

The application communicates with the LLM through an abstraction.

Conceptually:

```text
Application
    |
    v
LLMGateway
    |
    v
OpenAI Adapter
    |
    v
External LLM API
```

The purpose is to prevent application services from depending directly on a vendor SDK.

### 5.2 Responsibilities

The LLM integration should handle:

- Message construction.
- Role management.
- Prompt construction.
- Structured output.
- Tool/function calling.
- Streaming where supported.
- Timeout.
- Retry policy.
- Provider error translation.
- Token usage.
- Cost and latency observability.

The LLM is a reasoning and response-generation component.

It is not the owner of business authorization, persistence, idempotency, or side-effect execution.

## 6. Agent Runtime

### 6.1 Agent Run

An Agent run represents one logical execution of an Agent task.

It may involve:

- Multiple LLM calls.
- Multiple tool calls.
- State transitions.
- Approval pauses.
- Checkpoints.
- Completion or failure.

The run lifecycle must be persisted independently of the HTTP request that started it.

The previously observed lifecycle states included:

- `RUNNING`
- `WAITING_FOR_APPROVAL`
- `COMPLETED`
- `FAILED`

Additional states may be required for recovery and cancellation, but should not be introduced without a clear design.

### 6.2 AgentRunService

The service is responsible for coordinating the Agent run lifecycle.

Historically observed responsibilities included:

- Creating a run.
- Persisting its initial state.
- Executing the Agent workflow.
- Saving waiting-for-approval state.
- Saving completion state.
- Marking execution failures.
- Resuming a run.
- Using an expected version when claiming a run for resume.

The version-based resume claim helps prevent two concurrent requests from resuming the same run simultaneously.

### 6.3 Agent Loop

The Agent loop coordinates the interaction between the LLM and tools.

Conceptually:

```text
Start Agent Run
      |
      v
Build LLM Context
      |
      v
Call LLM
      |
      v
Inspect LLM Response
      |
      +---- Final Answer ----> Complete Run
      |
      +---- Tool Calls
                |
                v
           Resolve Tools
                |
                v
           Execute Tools
                |
                v
          Append Results
                |
                v
          Continue Loop
```

The loop needs explicit limits and termination conditions.

These include:

- Maximum execution steps.
- Final response detection.
- Tool call handling.
- Tool execution errors.
- Approval pauses.
- Run cancellation or failure.

Do not allow an Agent loop to run indefinitely.

## 7. Tool Architecture

### 7.1 Tool Registry

The registry resolves a tool name to a registered tool implementation.

The LLM may request a tool by name, but it cannot decide which arbitrary Python function is safe to execute.

The application controls the registry.

### 7.2 Tool Policy

Each tool should have an explicit execution policy.

Relevant policy attributes include:

- Whether approval is required.
- Whether parallel execution is safe.
- Whether the tool has side effects.
- Whether retries are safe.
- Whether the operation requires downstream idempotency.

The historical implementation had these policies:

| Tool | Approval required | Parallel-safe |
|---|---:|---:|
| GetOrder | No | No |
| CancelOrder | Yes | No |

These are historical observed values and should be checked against current source.

### 7.3 Tool Executor

The Tool Executor is the controlled execution boundary for tools.

Its responsibilities include:

1. Resolve the tool.
2. Validate input.
3. Identify the logical tool call.
4. Compute an intent fingerprint.
5. Claim or load the tool execution record.
6. Apply idempotency behavior.
7. Execute the tool when safe.
8. Persist the result.
9. Return the recorded or newly produced result.

A tool should not bypass this boundary when it performs a side effect that needs reliable execution tracking.

### 7.4 Sequential and Parallel Execution

The historical implementation included:

- Sequential execution.
- A parallel path using `TaskGroup` when all relevant tools were marked parallel-safe.

Parallel execution should be allowed only when the policies and business semantics permit it.

A tool being technically asynchronous does not automatically mean it is safe to execute concurrently.

## 8. Agent Runs vs Tool Executions

These are separate persistence concepts.

### 8.1 Agent Runs

`agent_runs` represents the lifecycle of an Agent task.

It answers questions such as:

- Which Agent task is running?
- What is its current state?
- Is it waiting for approval?
- Has it completed?
- Has it failed?
- Which checkpoint should be resumed?

### 8.2 Tool Executions

`tool_executions` represents an individual tool invocation within an Agent run.

It answers questions such as:

- Which tool was invoked?
- Which logical tool call was it?
- What input intent was associated with it?
- Did execution start?
- Did it complete?
- Is its outcome uncertain?
- Can the recorded result be replayed?

The historical design used a uniqueness key based on:

`(run_id, call_id)`

The recorded fields included:

- Tool name.
- Intent hash.
- Execution status.
- Output.
- Timestamps.

The historical statuses included:

- `STARTED`
- `COMPLETED`
- `UNKNOWN`

The exact current schema must be checked in the models and migrations.

### 8.3 Why They Must Be Separate

An Agent run may invoke several tools.

A run can be interrupted while one tool is executing.

If the system stores only the Agent run state, it cannot reliably determine whether an individual side effect already happened.

Separating the two records provides a foundation for:

- Tool-level idempotency.
- Result replay.
- Uncertain-outcome handling.
- Recovery.
- Auditability.
- Per-tool execution observability.

## 9. Idempotency and Intent Fingerprinting

### 9.1 Logical Tool Call Identity

The historical design used:

`(run_id, call_id)`

This identifies a logical tool call within a particular Agent run.

### 9.2 Intent Fingerprint

The executor canonicalizes the tool arguments and computes a SHA-256 hash.

Conceptually:

```text
Tool name
    +
Canonicalized arguments
    |
    v
Intent representation
    |
    v
SHA-256
    |
    v
Intent hash
```

The purpose is to ensure that the same logical call identity is not reused for a different operation.

### 9.3 Expected Behavior

For a tool execution record:

- If no record exists, claim the execution.
- If a completed record exists with the same intent, replay its stored result.
- If the same logical call has a different intent, reject the request.
- If the previous execution is still started or its outcome is unknown, do not blindly execute it again.

This protects against some duplicate execution scenarios.

It does not provide end-to-end exactly-once execution.

### 9.4 Important Limitation

A local tool execution ledger cannot guarantee that a remote service performed a business operation exactly once.

Consider:

```text
Local application
      |
      v
Send cancellation request
      |
      v
Remote service performs cancellation
      |
      v
Network response is lost
      |
      v
Local application sees timeout
```

The local application cannot infer that cancellation failed.

It may have succeeded remotely.

This is why downstream idempotency and reconciliation are necessary.

## 10. Tool Execution Failure Model

The execution lifecycle must account for:

### 10.1 Failure Before Side Effect

The process fails before sending the downstream request.

The operation may be safe to retry, but the system must know that the request was never dispatched or have a reliable way to establish that fact.

### 10.2 Failure During Side Effect

The process or network fails while the downstream request is being processed.

The outcome may be unknown.

### 10.3 Failure After Side Effect

The downstream operation succeeds, but the local process crashes before recording completion.

The local ledger may still show `STARTED`.

Blindly executing again can cause duplicate side effects.

### 10.4 Recovery Requirement

The system needs an explicit strategy for uncertain execution outcomes.

Potential mechanisms include:

- Downstream idempotency keys.
- Operation status queries.
- Reconciliation.
- Durable downstream execution records.
- Human intervention for unresolved cases.

The exact strategy depends on the downstream service's capabilities.

## 11. Human Approval

Sensitive operations should be controlled by application policy.

The historical Order Agent policy required approval for `CancelOrder`.

The intended flow is:

```text
Agent Requests CancelOrder
          |
          v
Tool Policy Check
          |
          v
Approval Required
          |
          v
Persist Waiting State
          |
          v
Wait for Human Decision
          |
          v
Resume Agent Run
          |
          v
Execute Approved Operation
```

Approval must be tied to the relevant operation and execution context.

A resume request must not accidentally bypass the original approval requirement.

## 12. Order Command Gateway

The project introduced an `OrderCommandGateway` port.

Known implementations included:

- `LocalOrderCommandGateway`
- A gRPC adapter

### 12.1 LocalOrderCommandGateway

The local adapter invokes the in-process Order service.

The historical implementation used `asyncio.to_thread()` for the synchronous operation.

This provides a local implementation behind the same application boundary.

It does not automatically provide distributed reliability or durable downstream idempotency.

### 12.2 gRPC Adapter

A Protobuf contract was present at:

`contracts/proto/ai_backend_lab/contracts/order/v1/order_service.proto`

It defined:

`OrderCommandService.CancelOrder`

Generated Python contract files were present under:

`src/ai_backend_lab/contracts/order/v1/`

The gRPC adapter propagated an idempotency-related key.

### 12.3 Historical Integration Status

At the last known repository inspection:

- The `OrderCommandGateway` port existed.
- The local adapter existed.
- The gRPC adapter existed.
- The Protobuf contract existed.
- The application composition still selected `LocalOrderCommandGateway`.
- The gRPC adapter was not wired into the FastAPI application composition.
- The application lifespan did not manage a gRPC channel and stub.
- A downstream gRPC server implementation was not present.
- Durable downstream deduplication was not implemented.

Therefore, the gRPC path was **partially implemented**, not a completed distributed command architecture.

Re-inspect the current source before using this status.

## 13. Application Lifecycle

External resources should be managed explicitly.

Historically observed FastAPI lifespan responsibilities included:

- Creating and closing the HTTPX client.
- Creating and closing the asynchronous OpenAI client.

The historical snapshot did not show gRPC channel lifecycle management.

When gRPC integration is completed, resource management should be consistent with the application's lifecycle design.

Do not create long-lived clients independently inside every request or tool call without a justified reason.

## 14. Persistence and Database

The project uses:

- SQLAlchemy.
- MySQL.
- Alembic.

Database schema changes should be represented through migrations.

The test database observed in the historical snapshot was:

`ai_backend_lab_test`

The test configuration used Alembic upgrades to prepare the database.

The current migration configuration and test setup must be verified before executing database commands.

## 15. Testing Strategy

Testing should cover multiple layers.

### 15.1 Unit Tests

Examples:

- Domain behavior.
- Tool input validation.
- Intent fingerprint generation.
- Tool policy.
- Agent loop termination.
- Error translation.

### 15.2 Application Tests

Examples:

- Agent run lifecycle.
- Approval behavior.
- Resume behavior.
- Tool execution orchestration.
- Replay behavior.
- Intent mismatch behavior.

### 15.3 Persistence Tests

Examples:

- Tool execution uniqueness.
- Transaction behavior.
- Concurrent claims.
- State transitions.
- Migration correctness.

### 15.4 Integration Tests

Examples:

- FastAPI endpoints.
- MySQL persistence.
- External gateway adapters.
- LLM adapter behavior with controlled dependencies.
- gRPC integration when fully wired.

### 15.5 Failure and Concurrency Tests

Examples:

- Process interruption after claim.
- Timeout after downstream success.
- Duplicate tool call.
- Same call ID with different arguments.
- Concurrent resume.
- Concurrent execution claims.
- Unknown downstream outcome.
- Recovery of stale execution records.

A successful happy-path test is not enough to establish reliability.

## 16. Known Historical Gaps and Risks

The following issues were identified in the previous repository inspection.

They must be rechecked against the current source.

### 16.1 Validation After Execution Claim

The tool-specific Pydantic validation in `GetOrderTool.execute()` and `CancelOrderTool.execute()` was observed to occur after the execution had been claimed as `STARTED`.

This creates a risk:

1. The executor records `STARTED`.
2. Tool-specific validation fails.
3. No side effect occurs.
4. The record may remain `STARTED`.

The intended improvement is to validate tool arguments before claiming the execution record, or otherwise define a safe validation-failure state transition.

### 16.2 Incomplete UNKNOWN Lifecycle

The historical `ToolExecutionStore` exposed operations equivalent to:

- `get`
- `create`
- `complete`

A clear `mark UNKNOWN` transition and reconciliation workflow were not found in the inspected implementation.

### 16.3 No Complete Crash Recovery

The historical implementation did not provide a complete recovery process for interrupted Agent runs.

A process crash could leave a run in `RUNNING`.

A tool execution could remain `STARTED`.

### 16.4 Limited Tool Execution Test Coverage

The historical inspection did not find a dedicated ToolExecutor test module or a dedicated SQL ToolExecutionStore test module.

This must be verified against the current repository.

### 16.5 gRPC Integration Incomplete

The gRPC adapter and contract existed, but the complete runtime and downstream service integration were not present in the inspected snapshot.

### 16.6 Exactly-once Is Not Guaranteed

The current local ledger design cannot independently guarantee exactly-once execution across service boundaries.

A durable downstream idempotency mechanism and reconciliation strategy are required.

## 17. Architecture Evolution Direction

The architecture should evolve in the following order:

1. Complete and verify the existing tool execution ledger.
2. Make validation and execution claiming safe.
3. Define explicit uncertain-outcome transitions.
4. Add reconciliation.
5. Add downstream idempotency.
6. Implement reliable recovery for interrupted runs.
7. Complete approval and resume reliability.
8. Improve audit and observability.
9. Complete distributed gateway integration.
10. Add failure and concurrency testing.
11. Evaluate distributed Agent execution only after the single-process reliability model is clear.

This sequence is a technical direction, not authorization to change the repository.

## 18. Final Architecture Rule

Always distinguish between:

- A concept explained in the curriculum.
- An interface defined in code.
- An adapter implemented in code.
- An adapter wired into runtime composition.
- An external service actually available.
- A behavior covered by tests.
- A behavior verified under failure conditions.

These are different levels of completion.