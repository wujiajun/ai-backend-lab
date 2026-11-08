# Roadmap — AI Backend Lab

## 1. Purpose

This document defines the future development direction of AI Backend Lab.

It is intentionally different from `docs/LEARNING_HISTORY.md`.

- `LEARNING_HISTORY.md` records what has already been studied and the historical lesson sequence.
- `ROADMAP.md` records what remains to be completed and what should be developed next.

Do not move historical lesson details into this document unless they are needed to explain the next milestone.

Do not change historical lesson numbering.

## 2. Long-term Objective

Build a reliable Agent Runtime and a production-oriented backend reference architecture.

The target system should support:

- Multi-step Agent execution.
- Tool orchestration.
- Persistent Agent state.
- Human approval.
- Safe resume.
- Tool execution tracking.
- Idempotency.
- Uncertain-outcome reconciliation.
- Crash recovery.
- Downstream service integration.
- Distributed execution.
- Observability.
- Failure and concurrency testing.

The project should evolve incrementally.

Do not introduce distributed complexity before the single-process execution and persistence model is reliable.

## 3. Roadmap Principles

### 3.1 Preserve the Learning Sequence

Continue from the existing Day 1–Day 11 curriculum.

The historical Day 11 sequence must retain its original numbering:

- Day 11.1 through Day 11.7.
- Day 11.8 through Day 11.15.

Do not skip a lesson or silently reorder it.

### 3.2 Build Reliability Before Adding Complexity

Prioritize:

1. Correct execution state.
2. Safe side-effect handling.
3. Idempotency.
4. Recovery.
5. Concurrency.
6. Observability.
7. Distributed integration.

Do not build a distributed Agent runtime on top of an incomplete local execution model.

### 3.3 Verify Before Implementing

Before starting a milestone:

- Inspect the current repository.
- Inspect relevant code and tests.
- Confirm what has already been implemented.
- Confirm whether previous work has changed.
- Avoid duplicating existing functionality.

The historical implementation snapshot is not a substitute for a live repository inspection.

### 3.4 Test Real Failure Scenarios

Reliability work must include tests for failure and concurrency.

A happy-path API response is not sufficient evidence that a reliability feature is complete.

## 4. Current Known Baseline

The last known repository inspection referenced:

`358736ef321610bf34ac70b4b0180a07ff76130d`

The last known explicit learning commit was associated with Day 11.7.

The following implementation state was observed at that time:

- Agent run persistence existed.
- Tool execution persistence existed.
- Tool execution identity used `(run_id, call_id)`.
- Tool arguments were canonicalized and hashed.
- Completed tool results could be replayed.
- Intent mismatch was rejected.
- `STARTED` and `UNKNOWN` executions were not blindly re-executed.
- `OrderCommandGateway` existed.
- Local and gRPC adapter implementations existed.
- The runtime composition still used the local adapter.
- The gRPC adapter was not fully wired into the application lifecycle.
- Downstream durable idempotency was not implemented.
- Complete uncertain-outcome reconciliation was not implemented.
- Complete Agent crash recovery was not implemented.

All of these items must be revalidated before starting new work.

## 5. Immediate Priority: Re-establish the Actual Baseline

**Priority: First action**

Before continuing the curriculum, inspect the live repository.

Required checks:

1. Confirm the repository and branch.
2. Inspect `git status`.
3. Inspect the current HEAD and recent commits.
4. Read the current `CLAUDE.md` and project documentation.
5. Inspect the Agent run implementation.
6. Inspect the ToolExecutor implementation.
7. Inspect tool execution persistence and migrations.
8. Inspect the OrderCommandGateway port and adapters.
9. Inspect application composition and lifespan.
10. Inspect relevant tests.
11. Run the relevant test suite if authorized and technically possible.

Record any differences between the historical snapshot and the live source.

Do not assume that the old snapshot is still accurate.

## 6. Day 11: Idempotency and Reliable Side-effect Execution

Day 11 is the current major learning and implementation milestone.

### 6.1 Day 11.7 — Downstream Gateway / RPC Idempotency

**Status: In progress at last recorded checkpoint.**

Historical objective:

Understand and implement the downstream boundary for idempotent business operations.

Topics include:

- Why local idempotency is not sufficient.
- Why a remote side effect may succeed even when the caller receives a timeout.
- How an idempotency key crosses a service boundary.
- Why the downstream service must persist its own execution result.
- How the local application and downstream service coordinate operation identity.
- How the same logical request can safely be replayed.

Historical implementation evidence included:

- `OrderCommandGateway`.
- `LocalOrderCommandGateway`.
- A gRPC adapter.
- A Protobuf `CancelOrder` contract.
- Propagation of an idempotency-related key.

However, the last known snapshot did not show a complete gRPC runtime integration or durable downstream deduplication.

Completion criteria:

- The user understands the difference between local and end-to-end idempotency.
- The gateway contract is clear.
- The local and remote execution responsibilities are explicit.
- The actual implementation status has been verified.
- The remaining gaps are documented.

Do not mark this lesson complete merely because a Protobuf contract or client adapter exists.

### 6.2 Day 11.8 — Unknown Outcome and Reconciliation

**Status: Planned.**

Topics:

- Why a timeout does not prove failure.
- The difference between `STARTED`, `COMPLETED`, and `UNKNOWN`.
- How to identify an uncertain tool execution.
- How to query downstream operation status.
- How to reconcile local and remote execution records.
- When an operation can be retried.
- When an operation must not be retried.
- When human intervention is required.

Expected result:

A clear and testable design for handling an execution whose actual outcome is uncertain.

### 6.3 Day 11.9 — External API Idempotency

**Status: Planned.**

Topics:

- Idempotency across HTTP and RPC boundaries.
- Stable operation identity.
- Idempotency-key propagation.
- Downstream deduplication.
- Request fingerprint validation.
- Duplicate request handling.
- Stored response replay.
- Key retention and lifecycle considerations.

Expected result:

A downstream API design that can safely handle repeated requests for the same logical business operation.

### 6.4 Day 11.10 — Stuck-run Recovery

**Status: Planned.**

Topics:

- Detecting stale `RUNNING` Agent runs.
- Detecting stale `STARTED` tool executions.
- Distinguishing a slow operation from a crashed process.
- Recovery ownership.
- Lease or timeout design where appropriate.
- Optimistic concurrency.
- Safe resume.
- Recovery of approval-waiting runs.
- Avoiding concurrent recovery of the same run.

Expected result:

A documented and testable recovery strategy for interrupted Agent runs.

### 6.5 Day 11.11 — Retry Policy

**Status: Planned.**

Topics:

- Retryable and non-retryable failures.
- Transient vs permanent errors.
- Retry budgets.
- Exponential backoff.
- Jitter.
- Timeout interaction.
- Idempotency requirements before retry.
- Retry ownership.
- Avoiding retry amplification.
- Manual intervention for unresolved operations.

Expected result:

A centralized and explicit retry policy that does not blindly repeat side effects.

### 6.6 Day 11.12 — Audit and Observability

**Status: Planned.**

Topics:

- Agent run audit trail.
- Tool execution audit trail.
- Correlation IDs.
- Request IDs.
- Run IDs.
- Tool-call IDs.
- Structured logging.
- Execution duration.
- LLM latency.
- Tool latency.
- Failure classification.
- Approval history.
- Sensitive-data handling.

Expected result:

The system should make it possible to understand what happened during an Agent run and why.

### 6.7 Day 11.13 — Failure and Concurrency Tests

**Status: Planned.**

Topics:

- Duplicate tool calls.
- Concurrent execution claims.
- Intent mismatch.
- Crash after execution claim.
- Timeout after downstream success.
- Duplicate resume requests.
- Stale run recovery.
- Concurrent cancellation attempts.
- Database uniqueness constraints.
- Transaction rollback.
- Replay behavior.

Expected result:

Automated tests that verify reliability behavior rather than only successful execution.

### 6.8 Day 11.14 — Resilient Cancel Flow

**Status: Planned.**

Topics:

- End-to-end cancellation workflow.
- Approval.
- Tool execution claim.
- Downstream idempotency.
- Timeout handling.
- Unknown outcome.
- Reconciliation.
- Result replay.
- Recovery.
- Audit trail.

Expected result:

An Order cancellation workflow that demonstrates the reliability principles developed throughout Day 11.

### 6.9 Day 11.15 — Day 11 Wrap-up

**Status: Planned.**

Topics:

- Review the complete Day 11 architecture.
- Review local and downstream idempotency.
- Review execution lifecycle.
- Review failure handling.
- Review recovery.
- Review tests.
- Review remaining limitations.
- Update documentation.
- Confirm the next learning milestone.

Expected result:

A coherent and documented implementation of the Day 11 reliability concepts.

## 7. Important Engineering Issue to Recheck

The previous repository inspection identified a potential problem:

Tool-specific Pydantic validation in `GetOrderTool.execute()` and `CancelOrderTool.execute()` appeared to happen after the ToolExecutor had created a `STARTED` execution record.

Potential failure:

1. The executor claims the tool execution.
2. The tool validates its arguments.
3. Validation fails.
4. No external operation occurs.
5. The record may remain `STARTED`.

This should be rechecked during the baseline inspection.

If it still exists, address it within the appropriate Day 11 lesson rather than silently ignoring it.

The intended principle is that invalid input should not create a misleading record suggesting that a side effect may have started.

## 8. Post-Day 11 Development Direction

The following are candidate future development phases.

They are not historical Day 12 lesson records, and their detailed numbering has not yet been established.

Do not invent Day 12.x or later numbering without agreement.

### Phase A — Complete the Agent Runtime Reliability Foundation

Potential topics:

- Explicit Agent run state machine.
- Intermediate checkpoints.
- Reliable resume.
- Durable tool execution ledger.
- Uncertain-outcome reconciliation.
- Safe retry.
- Cancellation.
- Recovery worker.
- Recovery ownership and concurrency.

### Phase B — Production Observability

Potential topics:

- Structured execution traces.
- Agent run dashboards.
- Tool-level metrics.
- LLM usage and cost tracking.
- Latency tracking.
- Error classification.
- Audit events.
- Operational alerting.

### Phase C — Distributed Execution

Potential topics:

- Distributed Agent workers.
- Queue-based execution.
- Worker ownership.
- Distributed leases.
- Heartbeats.
- Durable job scheduling.
- Duplicate delivery.
- Worker crash recovery.
- Cross-service idempotency.

Distributed execution should not begin until the local execution model has reliable state transitions and recovery semantics.

### Phase D — Human-in-the-loop Workflow

Potential topics:

- Approval records.
- Approval expiration.
- Rejection and cancellation.
- Resume authorization.
- Approval audit history.
- Multiple approval stages.
- Approval policy configuration.

### Phase E — Security and Governance

Potential topics:

- Tool authorization.
- Per-user and per-tenant access control.
- Tool allowlists.
- Sensitive operation policies.
- Input validation.
- Secret management.
- Audit and compliance requirements.
- Prompt injection and untrusted tool output handling.

### Phase F — Production Deployment

Potential topics:

- Containerized deployment.
- Configuration management.
- Health checks.
- Graceful shutdown.
- Database migration strategy.
- Deployment and rollback.
- CI/CD.
- Monitoring.
- Backup and recovery.
- Capacity and performance testing.

These phases are possible future directions, not commitments to implement every item.

## 9. Milestone Completion Criteria

A milestone is complete only when:

1. Its intended concepts have been explained.
2. Its implementation matches the agreed design.
3. Relevant tests have been executed.
4. Important failure scenarios have been considered.
5. The user understands the design and trade-offs.
6. Documentation reflects the actual implementation.
7. Remaining limitations are recorded.

Do not use the number of changed files or lines of code as a completion metric.

## 10. Roadmap Maintenance Rules

When updating this document:

- Keep historical learning records in `LEARNING_HISTORY.md`.
- Preserve original lesson numbers.
- Do not mark planned work as implemented.
- Do not mark untested work as tested.
- Do not remove unresolved issues without evidence.
- Update the current milestone only after confirming the actual repository state.
- Keep future phases separate from confirmed curriculum items.

The roadmap is a controlled engineering plan, not a list of speculative features.