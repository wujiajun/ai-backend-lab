# Architecture Decisions — AI Backend Lab

## 1. Purpose

This document records architectural decisions and design principles relevant to AI Backend Lab.

It explains:

- What design is currently reflected in the implementation.
- Why the design exists.
- What alternatives were considered.
- What consequences and limitations follow.
- Which decisions remain incomplete or require confirmation.

This document is reconstructed from the known project architecture and historical source inspection.

**Important:** A design observed in source code is not automatically a formally approved decision by the user. Each entry therefore identifies its evidence and status.

## 2. Decision Status Definitions

| Status | Meaning |
|---|---|
| Observed | The design is reflected in the previously inspected source code. |
| Current direction | The design is an established architectural direction for the project. |
| Partial | The design has been started but is not fully integrated. |
| Proposed | A corrective or future design has been identified but is not confirmed as implemented. |
| Open | More investigation or an explicit decision is required. |

Do not change an entry to implemented or accepted without evidence.

---

## ADR-001 — Separate API, Application, Domain, and Infrastructure Responsibilities

**Status:** Current architectural direction.

### Context

The project needs to remain maintainable as Agent workflows and external integrations become more complex.

Putting API handling, business rules, database access, and vendor SDK calls into the same service would create tight coupling.

### Decision

Use clear architectural boundaries:

- API layer.
- Application layer.
- Domain layer.
- Ports.
- Infrastructure adapters.
- Persistence.

Application services coordinate use cases.

Domain logic should not depend on infrastructure.

Infrastructure-specific implementations should remain behind appropriate boundaries.

### Rationale

This provides:

- Testability.
- Replaceable infrastructure.
- Clearer ownership.
- Reduced vendor coupling.
- More predictable dependency direction.

### Consequences

- More explicit interfaces may be required.
- Dependency wiring must be managed.
- The architecture should avoid unnecessary abstractions that add no meaningful boundary.

---

## ADR-002 — Put LLM Provider Integration Behind LLMGateway

**Status:** Observed in the historical implementation.

### Context

Directly using a vendor SDK throughout application services would make the application dependent on a specific provider.

### Decision

Use an application-facing `LLMGateway` abstraction.

Implement provider-specific behavior in an adapter.

Historical implementation included an OpenAI-compatible adapter.

### Rationale

This allows:

- Provider replacement.
- Controlled testing.
- Centralized timeout and retry behavior.
- Centralized usage and latency tracking.
- Separation between Agent orchestration and provider SDK details.

### Consequences

The gateway contract should represent application needs rather than duplicate every provider SDK method.

Provider-specific capabilities must be handled deliberately.

The abstraction should not hide important differences between providers.

---

## ADR-003 — Put External Risk Integration Behind RiskGateway

**Status:** Observed in the historical implementation.

### Context

The Order Agent uses an external risk-related capability.

Application services should not depend directly on HTTPX or a particular external API.

### Decision

Use a `RiskGateway` port and an HTTPX-based adapter.

### Rationale

This separates application orchestration from:

- HTTP transport.
- Client configuration.
- Connection lifecycle.
- Timeout.
- Retry.
- External error translation.

### Consequences

The adapter owns transport-specific behavior.

The application receives a stable application-facing result or exception contract.

---

## ADR-004 — Use OrderCommandGateway for Order Commands

**Status:** Partial.

### Context

The Order Agent needs to execute business operations such as order cancellation.

The application should not be tied to whether the command is executed in-process or through RPC.

### Decision

Introduce an `OrderCommandGateway` port.

Known implementations:

- `LocalOrderCommandGateway`.
- A gRPC adapter.

The local adapter historically invoked the in-process Order service through `asyncio.to_thread()`.

### Rationale

This allows the application layer to depend on a stable command boundary.

It also provides a migration path from local execution to a remote service.

### Consequences

A gateway interface alone does not provide distributed reliability.

The remote implementation still needs:

- Runtime wiring.
- Client lifecycle management.
- A downstream service.
- Error translation.
- Durable idempotency.
- Integration tests.

### Current limitation

At the last known inspection, the composition still used the local gateway.

The gRPC integration was not complete.

---

## ADR-005 — Separate Agent Runs from Tool Executions

**Status:** Observed in the historical implementation.

### Context

An Agent run can invoke multiple tools.

A run can be interrupted while a specific tool is executing.

Persisting only the Agent run state is insufficient to determine whether an individual side effect has already happened.

### Decision

Use separate persistence concepts:

- `agent_runs`
- `tool_executions`

### Responsibilities

`agent_runs` tracks:

- Agent run lifecycle.
- Execution state.
- Checkpoint.
- Approval waiting.
- Completion.
- Failure.

`tool_executions` tracks:

- Individual tool invocation.
- Tool identity.
- Input intent.
- Execution state.
- Output.
- Timestamps.

### Rationale

The two records represent different lifecycles.

Separating them provides a foundation for tool-level idempotency, replay, audit, and recovery.

### Consequences

The application must coordinate the two lifecycles carefully.

An Agent run being marked `RUNNING` does not mean every tool execution is safe to repeat.

An Agent checkpoint does not replace the tool execution ledger.

---

## ADR-006 — Identify a Logical Tool Execution by (run_id, call_id)

**Status:** Observed in the historical implementation.

### Context

The same logical tool call may be encountered again when an Agent run is resumed or retried.

The application needs a stable identity for the operation.

### Decision

Use:

`(run_id, call_id)`

as the logical tool execution identity.

### Rationale

This allows the application to associate a tool call with one specific Agent run.

It also supports:

- Duplicate detection.
- Result replay.
- Intent mismatch detection.
- Execution audit.

### Consequences

The uniqueness constraint must be enforced at the persistence boundary.

Concurrent requests must not create two independent execution records for the same logical tool call.

The identity must remain stable across retries of the same logical operation.

---

## ADR-007 — Use an Intent Fingerprint to Detect Reused Identity with Different Input

**Status:** Observed in the historical implementation.

### Context

A caller might accidentally reuse the same logical tool-call identity with different arguments.

Replaying a result from a different operation would be incorrect.

### Decision

Canonicalize the tool arguments and calculate a SHA-256 intent fingerprint.

The historical ToolExecutor used this fingerprint to validate the relationship between the logical call identity and its arguments.

### Rationale

A stable fingerprint allows the system to detect whether the same logical call identity represents the same requested operation.

### Consequences

The canonicalization process must be deterministic.

The fingerprint must include all input fields that affect the operation's business intent.

If tool behavior changes in ways not represented by the input, additional versioning or operation metadata may be necessary.

A matching fingerprint does not prove that a remote side effect occurred exactly once.

---

## ADR-008 — Do Not Blindly Re-execute STARTED or UNKNOWN Tool Executions

**Status:** Observed in the historical implementation as a safety behavior.

### Context

A process may fail after a tool execution is claimed.

A downstream service may complete an operation while the local application receives a timeout.

The local application may therefore be unable to determine whether the side effect occurred.

### Decision

Do not automatically execute a tool again merely because its local execution record is not `COMPLETED`.

In particular, do not blindly re-execute `STARTED` or `UNKNOWN` records.

### Rationale

A repeated side effect may:

- Cancel an already cancelled order.
- Charge a customer twice.
- Send duplicate messages.
- Create duplicate external resources.
- Trigger irreversible business behavior.

### Consequences

The system needs an explicit recovery path.

Possible mechanisms include:

- Downstream idempotency.
- Downstream operation status queries.
- Reconciliation.
- Manual intervention.

This policy may reduce automatic availability when the outcome is uncertain, but it avoids unsafe duplicate execution.

---

## ADR-009 — Do Not Promise End-to-end Exactly-once Execution

**Status:** Current architectural principle.

### Context

The application interacts with remote services across network boundaries.

A timeout or connection failure can happen after a remote service has completed a side effect.

The caller cannot always determine the remote outcome.

### Decision

Do not claim that the complete Agent workflow guarantees exactly-once execution.

Use explicit mechanisms:

- Stable operation identity.
- Idempotency keys.
- Durable execution records.
- Downstream deduplication.
- Reconciliation.
- Safe retry rules.

### Rationale

A local database transaction cannot atomically include an arbitrary remote service unless a specific distributed transaction protocol and participating infrastructure are available.

A local execution ledger alone cannot guarantee exactly-once behavior across services.

### Consequences

Documentation and API contracts must describe the actual guarantees.

Prefer precise guarantees such as:

- Duplicate requests with the same idempotency key return the recorded result.
- A completed tool execution is replayed locally.
- An uncertain remote operation is reconciled before retry.

Do not use “exactly once” as a synonym for “we store an idempotency key.”

---

## ADR-010 — Downstream Services Must Participate in Durable Idempotency

**Status:** Required future capability; not implemented in the last known snapshot.

### Context

The local ToolExecutor can prevent some duplicate local executions.

However, it cannot independently prevent a remote service from performing the same business operation twice.

### Decision

A downstream service that performs a side effect should own durable deduplication for its business operation.

The caller should propagate a stable operation identity or idempotency key.

The downstream service should persist the operation identity and its outcome.

### Expected behavior

For a repeated request with the same key and same intent:

- Return or replay the original outcome.

For the same key with different intent:

- Reject the request.

For a concurrent duplicate request:

- Ensure that only one business operation is performed.

### Consequences

The downstream service needs its own persistence and concurrency strategy.

The gateway must not treat key propagation alone as proof of idempotency.

The downstream service implementation and integration tests are required.

---

## ADR-011 — Sensitive Tools Require Explicit Approval Policy

**Status:** Observed in the historical implementation.

### Context

Some Agent tools read information, while others change business state.

A model-generated tool request should not automatically authorize a sensitive business operation.

### Decision

Use explicit tool execution policy.

The historical Order Agent policy included:

| Tool | Approval required |
|---|---:|
| GetOrder | No |
| CancelOrder | Yes |

### Rationale

The LLM should not be the authority for business authorization.

The application owns approval policy.

### Consequences

Approval must be persisted and associated with the relevant run and operation.

Resume must verify the approval state.

A request to resume an Agent run must not bypass approval.

---

## ADR-012 — Parallel Execution Requires Explicit Tool Safety

**Status:** Observed in the historical implementation.

### Context

Some tool calls may be executed concurrently.

However, concurrent execution is not always safe.

### Decision

Only execute tools concurrently when their policies explicitly permit parallel execution.

The historical implementation had a sequential path and a parallel-safe path using `TaskGroup`.

The observed policies marked both GetOrder and CancelOrder as not parallel-safe.

### Rationale

Concurrency can introduce:

- Race conditions.
- Conflicting side effects.
- Ordering problems.
- Database contention.
- Non-deterministic business behavior.

### Consequences

Do not infer parallel safety from the fact that a tool is asynchronous.

Parallel safety must be based on business semantics and side-effect behavior.

---

## ADR-013 — Manage Long-lived External Clients Through Application Lifecycle

**Status:** Observed architectural direction.

### Context

HTTP and LLM clients manage external resources such as connection pools.

Creating a new client for every request can lead to inefficient resource usage and inconsistent lifecycle behavior.

### Decision

Manage long-lived external clients through the application lifecycle.

The historical FastAPI lifespan created and closed:

- HTTPX client.
- Asynchronous OpenAI client.

### Rationale

This provides:

- Explicit resource ownership.
- Reuse of connection pools.
- Predictable startup and shutdown.
- Cleaner dependency injection.

### Consequences

New long-lived integrations, including gRPC, should follow the same lifecycle discipline.

The application should not create unmanaged channels or clients inside arbitrary request handlers.

---

## ADR-014 — Use MySQL, SQLAlchemy, and Alembic for Persistence

**Status:** Observed in the historical implementation.

### Context

The project needs persistent Agent state, tool execution records, and business data.

### Decision

The implementation uses:

- MySQL.
- SQLAlchemy.
- Alembic.

### Rationale

This provides relational persistence, transaction support, schema constraints, and controlled schema evolution.

### Consequences

Schema changes should be represented by migrations.

Correctness-sensitive behavior should use database constraints and transaction boundaries where appropriate.

Tests must verify actual database behavior rather than relying only on in-memory substitutes.

---

## ADR-015 — Validate Tool Input Before Claiming a Side-effect Execution

**Status:** Proposed corrective design; historical implementation must be rechecked.

### Context

The previous repository inspection found that tool-specific Pydantic validation in `GetOrderTool.execute()` and `CancelOrderTool.execute()` appeared to occur after the ToolExecutor had created a `STARTED` execution record.

This could produce a misleading execution record when invalid input prevents the tool from performing any side effect.

### Proposed decision

Perform input validation before creating the side-effect execution claim.

The intended order is:

```text
Receive Tool Call
      |
      v
Resolve Tool
      |
      v
Validate Input
      |
      v
Compute Intent
      |
      v
Claim Execution
      |
      v
Execute Side Effect
      |
      v
Persist Result
```

### Rationale

Invalid input should not create an execution record that implies a side effect may have started.

### Consequences

The validation boundary must be clearly defined.

Validation should be deterministic and should not itself perform side effects.

If validation behavior changes the business intent, it must be reflected in the intent fingerprint or relevant operation version.

### Open question

Re-inspect the current ToolExecutor and tool implementations before deciding whether this issue still exists.

---

## ADR-016 — Keep gRPC Integration Behind the Gateway Boundary

**Status:** Partial.

### Context

The project has both a local Order command implementation and a gRPC adapter.

The application should not need to change its business orchestration when the command implementation moves from local execution to a remote service.

### Decision

Use `OrderCommandGateway` as the application boundary.

Keep gRPC-specific code in the adapter.

The Protobuf service contract defines the RPC interface.

### Rationale

This supports a gradual transition from local execution to a remote service.

It also prevents gRPC transport concerns from leaking into Agent application logic.

### Consequences

A complete gRPC implementation still requires:

- Runtime composition.
- Channel and stub lifecycle.
- Downstream service.
- Error translation.
- Durable downstream idempotency.
- Integration tests.
- Operational configuration.

The existence of the adapter does not mean the distributed integration is complete.

---

## ADR-017 — Preserve Historical Learning Sequence and Separate It from the Roadmap

**Status:** Current collaboration and documentation rule.

### Context

The project is both a software implementation and a structured learning process.

The historical Day 1–Day 11 sequence is important to the user's learning continuity.

Mixing historical lessons with future roadmap items can cause accidental renumbering or loss of prior learning records.

### Decision

Maintain separate documents:

- `docs/LEARNING_HISTORY.md` for historical lessons.
- `docs/ROADMAP.md` for future work.

Preserve original lesson numbering.

### Rationale

This protects the learning history while allowing future development plans to evolve.

### Consequences

Do not invent missing historical lessons.

Do not move future topics into historical records.

Do not mark lessons complete without supporting evidence.

---

## 3. Open Architectural Questions

The following questions require future investigation or explicit decisions.

### 3.1 UNKNOWN State Management

- What exact event changes a tool execution from `STARTED` to `UNKNOWN`?
- Which component owns the transition?
- Can the transition be made safely after a process restart?
- How is reconciliation initiated?
- How is reconciliation ownership protected?

### 3.2 Downstream Operation Records

- What is the downstream idempotency-key scope?
- How long are keys retained?
- How are concurrent duplicate requests handled?
- How are mismatched intents rejected?
- How are original results replayed?
- How is an operation queried after a timeout?

### 3.3 Agent Run Recovery

- How are stale `RUNNING` runs detected?
- What defines a stale run?
- Is a lease required?
- Who owns recovery?
- How is duplicate recovery prevented?
- How does recovery interact with approval?

### 3.4 Intermediate Checkpoints

- At which points should the Agent persist checkpoints?
- Should every completed tool execution update the Agent checkpoint?
- How are tool execution records reconciled with the latest Agent checkpoint?
- What happens if the checkpoint write fails after a tool succeeds?

### 3.5 Retry Ownership

- Which layer owns retries?
- Should retries happen in the gateway, ToolExecutor, or recovery worker?
- How are retry budgets enforced?
- How are duplicate retries prevented across multiple layers?

### 3.6 Distributed Execution

- Will Agent runs be executed by a worker pool?
- Will a message queue be introduced?
- How will worker ownership be represented?
- How will leases and heartbeats work?
- How will duplicate message delivery be handled?

These questions should be addressed in the appropriate future lessons.

## 4. Decision Maintenance Rules

When a new architectural decision is made:

1. Add a new numbered entry.
2. Record the context.
3. Record the decision.
4. Explain the rationale.
5. Explain consequences.
6. Record implementation status.
7. Link relevant source files or tests when known.
8. Update the entry if the decision changes.

Do not rewrite historical decisions to make the architecture appear more complete than it was.

A design proposal, an implemented interface, a wired runtime component, and a tested end-to-end behavior are four different things.

Keep those distinctions explicit.