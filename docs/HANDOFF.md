# Claude Handoff — Current Working Point

_Last reconciled: 2026-11-08._

## 1. Repository Snapshot

- Repository: https://github.com/wujiajun/ai-backend-lab
- Current branch: `main`
- Current HEAD: `358736ef321610bf34ac70b4b0180a07ff76130d`
- Latest commit: `fix: update project description in pyproject.toml for clarity`
- Latest commit timestamp: `2026-10-20T23:33:11Z`
- Latest explicit learning milestone: `Day 11.7`
- Day 11.7 commit: `21028c67f7`

The remote review was read-only.

No repository files were changed, no commits were created, and no tests were run during that review.

**Important:** Re-check the current branch and HEAD before relying on this snapshot.

## 2. Verified Current State

The current source tree contains:

- FastAPI API and dependency/composition wiring.
- Order domain and application code.
- An LLM-backed order assistant.
- `OrderAgentService`.
- `AgentRunService`.
- `ToolExecutor`.
- Tool registry.
- `GetOrderTool`.
- Approval-gated `CancelOrderTool`.
- SQLAlchemy persistence for `agent_runs`.
- SQLAlchemy persistence for `tool_executions`.
- Alembic migrations.
- `OrderCommandGateway`.
- Local and gRPC client adapters.
- Protobuf source and generated Python files.
- OpenAI infrastructure adapter.
- Risk-service infrastructure adapter.
- API, application, domain, and infrastructure tests.

### Important Findings

**1. Active composition still uses the local adapter.**

`GrpcOrderCommandGateway` exists but is not wired into `composition.py` or FastAPI lifespan.

**2. Tool-specific validation happens after the STARTED claim.**

Pydantic validation currently occurs inside the tool's `execute()` method, after the executor creates the `STARTED` ledger record.

**3. UNKNOWN is not a complete recovery mechanism.**

The status exists, but no explicit persistence transition or reconciliation workflow was found.

**4. The local adapter does not enforce the propagated idempotency key.**

Downstream durable deduplication is not implemented in this repository.

**5. Agent checkpoints are not persisted after every intermediate tool step.**

A crash during an active run can leave a run in `RUNNING` without a recovery workflow.

See `ARCHITECTURE.md` and `ROADMAP.md` for the detailed review.

## 3. Immediate Next Task

The latest concrete correctness issue is:

**Move tool-specific argument schema validation before the `ToolExecutionStore.create(STARTED)` claim.**

### Why This Matters

The current flow is:

1. `build_tool_intent_hash()` parses and canonicalizes JSON.
2. `ToolExecutor.execute()` creates the `STARTED` record.
3. The executor calls `tool.execute()`.
4. The concrete tool performs Pydantic schema validation.

Therefore, schema-invalid tool arguments can leave a `STARTED` record even though no business side effect was attempted.

### Suggested First Action for Claude

1. Re-read:
   - `application/order_agent/tools.py`
   - `application/order_agent/executor.py`
   - `application/order_agent/tool_execution.py`
   - `application/order_assistant/tools.py`
   - Relevant tests.

2. Propose the smallest coherent tool-validation contract that allows the executor to validate before claiming execution.

3. Identify focused tests for:
   - Malformed JSON.
   - Schema-invalid arguments.
   - Valid arguments.
   - Duplicate calls.
   - Completed-result replay.

4. Present the design proposal and wait for Jason's authorization before editing.

Do not jump straight to gRPC lifecycle wiring.

The gRPC adapter is not currently active in composition. The validation-before-claim issue is the latest concrete reliability issue under discussion.

## 4. Important Architecture Decisions

### Separate Agent Runs and Tool Executions

Keep `agent_runs` and `tool_executions` separate.

They have different responsibilities:

- `agent_runs`: Agent lifecycle, checkpoint, and approval state.
- `tool_executions`: Individual side-effect execution claim and result.

### Tool Execution Identity

Use `(run_id, call_id)` as the tool execution ledger identity.

Fingerprint the tool name plus canonical arguments to detect reuse of the same identity with a different intent.

### Stable Idempotency Key

Use:

```text
{run_id}:{call_id}
```

as the stable idempotency key across the application command boundary.

### Port and Adapter Boundary

Keep `OrderCommandGateway` as an application port.

Local and remote adapters should be interchangeable without changing Agent application logic.

### No False Exactly-Once Claims

Do not assume a local execution ledger provides end-to-end exactly-once semantics.

The service that owns the side effect must provide durable deduplication and a way to reconcile ambiguous outcomes.

### No Shared Transaction Assumption

Do not assume independently deployed services share one ACID transaction.

Design for independently committed work and explicit recovery.

## 5. Collaboration Rules for Claude

- Read `CLAUDE.md`, `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `ROADMAP.md`, and this file first.
- Re-check the current Git branch and HEAD.
- Inspect live source before relying on this handoff.
- Treat source code, tests, migrations, and current Git history as authoritative.
- Never invent paths, signatures, classes, or test results.
- Read-only by default.
- Do not modify files, dependencies, migrations, or Git state without Jason's explicit authorization.
- No commits, pushes, branches, or PRs without separate explicit authorization.
- Keep explanations concise and technically substantive.
- Treat Jason as an experienced backend engineer.
- Work one step at a time.
- Do not change the agreed learning sequence.

## 6. Claude Code Startup Prompt

Use the following as the first instruction in the new Claude session:

> Read `CLAUDE.md` and all files under `docs/` first.
>
> Then inspect the current repository branch, HEAD, source files, tests, and migrations to verify whether this handoff is still accurate.
>
> Do a read-only review only.
>
> Report the verified current state and focus on the next reliability issue: tool-specific schema validation currently occurs after the `STARTED` tool-execution claim.
>
> Propose the smallest design that moves validation before the claim and list the tests needed.
>
> Do not edit or create any repository files. Do not run formatters that rewrite files. Do not commit or push.
>
> Wait for my explicit authorization before making changes.

## 7. First-Session Verification Checklist

- [ ] Confirm current branch and HEAD.
- [ ] Check whether the repository changed since this snapshot.
- [ ] Read the current `AgentTool` protocol.
- [ ] Read both concrete tool implementations.
- [ ] Trace `ToolExecutor.execute()` from tool lookup through ledger claim and execution.
- [ ] Confirm the exact Pydantic schemas and validation exceptions.
- [ ] Inspect existing tests and fixtures.
- [ ] Confirm whether a validation hook has been added since this handoff.
- [ ] Return a concise design proposal.
- [ ] Make no edits until Jason explicitly authorizes them.