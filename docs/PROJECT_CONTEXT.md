# Project Context

_Last reconciled: 2026-11-08._

Repository: https://github.com/wujiajun/ai-backend-lab

## 1. Project Identity

The project has two equally important goals.

### Goal A: Agent Engineering Learning Lab

Learn and implement the engineering concepts required to build capable, reliable AI agents.

### Goal B: Production-grade Backend Reference Architecture

Evolve the same codebase into a reusable foundation for medium-to-large AI/Agent backend systems.

This is not intended to be a tutorial-only demo or a thin wrapper around an LLM API.

Learning should accumulate into a coherent architecture that can be reused in real projects without requiring a major redesign.

## 2. Intended Engineering Scope

The long-term scope includes:

- Agent runtime and orchestration.
- Tool calling and tool lifecycle management.
- Agent state management and checkpointing.
- Human approval and authorization.
- Reliable side-effect execution.
- Idempotency and duplicate suppression.
- Crash recovery and unknown-outcome handling.
- Reconciliation and safe retry strategies.
- Explicit service boundaries and ports/adapters.
- Microservice extraction and independent deployment.
- RPC contracts and service communication.
- Persistence, migrations, and transaction ownership.
- Concurrency control and distributed consistency.
- Security and service identity.
- Configuration and observability.
- Automated testing and operational readiness.
- Deployment and production evolution.

The sample order-management domain is a practical vehicle for implementing these patterns. It is not the ultimate product scope.

## 3. Owner and Engineering Background

Jason has roughly 18–20 years of software experience, including approximately 18 years focused on Java, backend services, and databases.

Previous experience includes:

- Java and Spring Boot.
- Dubbo and service-oriented architecture.
- API gateways and service discovery.
- Kubernetes and Docker.
- CI/CD.
- Redis and RabbitMQ.
- Elasticsearch.
- MySQL high availability and performance.
- Cloud infrastructure.

The current learning objective is to restore and deepen hands-on senior engineering ability while adding modern AI/Agent engineering skills.

Do not frame the work as management-only because of previous executive roles.

### Collaboration Implications

- Treat Jason as an experienced backend engineer, not a beginner.
- Avoid lengthy explanations of basic programming concepts.
- Explain Python-specific behavior and architectural trade-offs where they matter.
- Use concrete code paths, failure scenarios, and tests.
- Work one step at a time.
- Preserve the agreed learning sequence.
- Do not change scope or skip topics without agreement.

## 4. Technology Baseline

The repository currently uses:

- Python `>=3.12`
- `uv`
- FastAPI
- OpenAI Python SDK
- SQLAlchemy 2.x
- MySQL through PyMySQL
- Alembic
- Pydantic Settings
- HTTPX
- gRPC
- Protocol Buffers
- Tenacity
- Pytest
- pytest-asyncio
- Ruff
- Black
- grpcio-tools

The source package follows the `src/ai_backend_lab` layout.

Verify the current dependency versions from `pyproject.toml` and `uv.lock` before making dependency-related recommendations.

## 5. Current Sample Capabilities

The current source tree contains:

- Order domain and application functionality.
- An LLM-backed order assistant.
- An order Agent with `get_order` and `cancel_order` tools.
- Human approval for cancellation.
- Durable Agent run records.
- A separate tool execution ledger.
- A local order-command adapter.
- A gRPC order-command client adapter behind an application port.
- HTTP integration with a risk service.
- API error mapping.
- Request-ID-aware logging.

The exact implementation status and gaps are documented in:

- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`

Do not assume that the existence of an interface, class, or contract means the capability is fully integrated or production-ready.

## 6. Definition of Success

Success is not merely that an Agent can call a tool.

The architecture should be able to explain and test what happens when:

- The LLM returns malformed or schema-invalid tool arguments.
- A request is duplicated or retried.
- Two workers attempt to resume the same Agent run.
- A side effect succeeds but the caller times out.
- The process crashes after a downstream commit but before the local ledger is updated.
- A downstream service is unavailable.
- A downstream service returns an ambiguous result.
- An Agent run or tool execution is left in an intermediate state.
- A service moves from an in-process adapter to a remote RPC boundary.

The system should evolve toward explicit, observable, and recoverable behavior for these cases.

## 7. Scope Preferences

- Do not introduce unrelated Chinese-language or social-product features.
- Do not turn the repository into a collection of disconnected demos.
- Do not simplify away production concerns solely to make a lesson shorter.
- Do not introduce speculative infrastructure without explaining the concrete use case and trade-off.
- Do not modify the repository without explicit authorization.