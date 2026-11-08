# Claude Code Working Agreement

This file defines stable collaboration and engineering rules. Current implementation status belongs in `docs/ROADMAP.md` and `docs/HANDOFF.md`.

## 1. Read Before Acting

At the beginning of a new session, read:

1. `CLAUDE.md`
2. `docs/PROJECT_CONTEXT.md`
3. `docs/ARCHITECTURE.md`
4. `docs/ROADMAP.md`
5. `docs/HANDOFF.md`
6. `README.md`

Then inspect the current repository state.

These documents preserve project context, but the checked-out source code, tests, migrations, and Git history remain authoritative.

## 2. Read-Only by Default

Do not modify repository files, create or delete files, run formatters that rewrite files, change dependencies, commit, push, create branches, or open PRs unless Jason explicitly authorizes the relevant action.

A request to inspect, explain, review, or plan is not permission to edit.

When implementation is requested:

- Stay within the explicitly authorized scope.
- Before a broad or ambiguous change, identify the files and behavior you intend to change.
- Do not bundle unrelated refactoring or cleanup.
- Never commit, push, or create a PR without separate explicit authorization.

## 3. Inspect Actual Code; Never Guess

Before making a code recommendation:

- Read the current implementation and its callers.
- Read relevant interfaces, protocols, data models, migrations, configuration, and tests.
- Confirm actual file paths, class names, method signatures, types, and dependency versions.
- Trace the runtime path through API, application, ports, composition, and infrastructure.
- Distinguish verified facts from assumptions and proposed designs.

Never invent files, classes, functions, signatures, configuration keys, or test fixtures.

Do not rely on an earlier chat answer when the current repository can be inspected.

If a required file or test is absent, say so explicitly. If behavior cannot be verified, label it as unverified.

## 4. Engineering Expectations

This project is intended to become a mature, reusable AI/Agent backend foundation, not a disposable demo.

Prefer:

- Explicit application boundaries and ports/adapters.
- Clear ownership of transactions and persistence.
- Durable idempotency for side effects.
- Safe handling of timeouts, retries, duplicate requests, process crashes, and unknown outcomes.
- Concurrency control and recovery strategies that can be tested.
- Explicit API contracts and versioned service contracts.
- Configuration, security, observability, migrations, and tests as first-class concerns.
- Small, reviewable changes with clear failure semantics.

Do not add abstractions or distributed-system machinery merely for appearance. Explain the concrete failure mode or future requirement that justifies them.

Avoid both demo-level shortcuts and speculative overengineering.

## 5. Collaboration Style

- Jason has roughly 18–20 years of software experience, with a strong Java/backend/database background. Do not teach basic programming concepts unless requested.
- Use concise, direct Chinese for discussion unless Jason asks for English.
- Keep code, identifiers, comments, and technical artifacts in idiomatic English.
- Explain important trade-offs and failure windows, not generic textbook material.
- Work in small, sequential steps.
- Do not skip ahead, change the agreed learning sequence, or introduce a new topic without a reason and user agreement.
- When correcting a previous recommendation, state what was wrong and why.
- Do not claim tests passed unless they were actually run. Report the exact command and result.

## 6. Tests and Quality

For each change:

1. Identify the relevant existing tests.
2. Inspect current test and fixture conventions.
3. Add focused tests for new behavior and failure cases.
4. Run the narrowest relevant tests.
5. Run broader tests and configured lint/type checks when appropriate.

Before reporting completion, state:

- Commands executed.
- Pass/fail results.
- Tests or checks not run.
- Any remaining limitations.

Do not silently change test databases, migrations, or developer environment settings.

## 7. Security

- Never print, copy into documentation, or expose real `.env` values, API keys, tokens, passwords, private URLs, or credentials.
- `.env.example` placeholders are safe to discuss; `.env` is not.
- Do not weaken authentication, authorization, validation, or idempotency to make a test pass.
- Treat model output and tool arguments as untrusted input.

## 8. Architecture Guardrails

- Keep LLM orchestration separate from business rules.
- An LLM proposing an action does not authorize that action.
- Side-effect tools must have explicit policy and approval behavior where appropriate.
- Keep Agent lifecycle/checkpoint state separate from per-tool side-effect execution records.
- Do not claim end-to-end idempotency merely because an idempotency key is generated or sent.
- Verify durable deduplication at the system that owns the side effect.
- A local adapter and a gRPC adapter are alternatives behind a port. Verify which one is actually wired into composition and runtime.
- Do not assume independently deployed services share a database transaction.

## 9. Required Reporting Format

For repository reviews and implementation work, clearly separate:

- **Verified current behavior**
- **Known gaps and risks**
- **Proposed change**
- **Tests and evidence**
- **Questions requiring Jason's decision**

Never present planned architecture as implemented functionality.