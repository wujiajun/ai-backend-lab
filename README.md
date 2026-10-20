# AI Backend Lab

A production-oriented AI backend and Agent engineering reference project built with Python, FastAPI, OpenAI, SQLAlchemy, MySQL, and gRPC.

This repository serves two purposes:

1. **Agent Engineering Learning Lab**  
   Learn and implement modern Agent concepts step by step, including tool calling, agent loops, state management, human approval, checkpointing, idempotency, crash recovery, distributed execution, observability, and more.

2. **Production-grade Backend Reference Architecture**  
   Evolve the same learning project into a reusable architectural foundation for medium-to-large production systems, rather than a disposable demo.

The goal is that patterns learned and implemented here can be reused directly when starting a real AI/Agent backend project with minimal architectural rework.

---

## Design Philosophy

This project intentionally avoids treating the LLM as the application architecture.

The LLM is one component inside a controlled backend runtime:

```text
Client
  ↓
FastAPI
  ↓
Application Services
  ↓
Agent Runtime
  ├── LLM Gateway
  ├── Tool Registry
  ├── Tool Executor
  ├── Human Approval
  ├── Execution Ledger
  └── Checkpoint / Recovery
          ↓
Ports / Gateways
          ↓
Infrastructure
  ├── MySQL
  ├── OpenAI
  ├── HTTP services
  └── gRPC services
```

Core principles:

- LLM decisions are not automatically authorized actions.
- Side effects must pass through explicit application boundaries.
- Business logic belongs in domain/application layers, not prompts.
- Agent state must survive process and request boundaries.
- Tool execution must be idempotent and recoverable.
- Service boundaries should support future microservice extraction.
- Infrastructure implementations must remain replaceable behind ports.
- Reliability, observability, testing, and migrations are part of the architecture, not afterthoughts.

---

## Current Architecture

```text
                           ┌─────────────────────┐
                           │      FastAPI        │
                           └──────────┬──────────┘
                                      │
                           ┌──────────▼──────────┐
                           │   AgentRunService   │
                           │                    │
                           │ start / resume/get │
                           └──────┬───────┬─────┘
                                  │       │
                      ┌───────────┘       └─────────────┐
                      │                                 │
             ┌────────▼─────────┐             ┌─────────▼─────────┐
             │ OrderAgentService│             │   AgentRunStore   │
             │                  │             │      MySQL        │
             └────────┬─────────┘             └───────────────────┘
                      │
             ┌────────▼─────────┐
             │   ToolExecutor   │
             │                  │
             │ claim / replay   │
             │ approval policy  │
             └──────┬─────┬────┘
                    │     │
       ┌────────────┘     └───────────────┐
       │                                  │
┌──────▼───────┐                  ┌───────▼─────────┐
│ GetOrderTool │                  │ CancelOrderTool │
└──────┬───────┘                  └───────┬─────────┘
       │                                  │
       │                           OrderCommandGateway
       │                                  │
       │                        ┌─────────┴─────────┐
       │                        │                   │
       │               Local Adapter        gRPC Adapter
       │                        │                   │
       ▼                        ▼                   ▼
 OrderService             OrderService       Order Service
                                              Microservice
```

Tool execution state is persisted separately:

```text
Agent Run State
→ agent_runs

Tool Side-effect Execution State
→ tool_executions
```

These solve different problems:

- `agent_runs` answers: **Where is the Agent execution now?**
- `tool_executions` answers: **Has this specific side-effect action already been executed?**

---

## Implemented Agent Capabilities

### Agent Runtime

- Multi-step Agent loop
- LLM tool calling
- Tool registry
- Sequential and parallel-safe tool execution
- Maximum Agent step budget
- Direct answers and tool-based answers
- Conversation state
- LLM continuation support
- Streaming Agent events

### Human-in-the-loop

Side-effect tools can require explicit approval.

```text
LLM proposes action
      ↓
Approval required
      ↓
Agent pauses
      ↓
Checkpoint persisted
      ↓
User approves / rejects
      ↓
Agent resumes
```

Current Agent API:

```text
POST /agent/runs
POST /agent/runs/{run_id}/resume
GET  /agent/runs/{run_id}
```

### Durable Agent Runs

Agent execution can survive HTTP request boundaries.

```text
Request #1
→ Agent starts
→ approval required
→ AgentState persisted
→ request ends

Request #2
→ run_id
→ checkpoint loaded
→ Agent resumes
```

`AgentRunService` manages the lifecycle of durable Agent runs.

### Optimistic Concurrency Control

Agent runs use version-based claiming before side-effect execution.

```text
Request A
claim version=2 ✅
version → 3

Request B
claim version=2 ❌
```

This prevents concurrent resume requests from both executing the same side-effect Tool.

### Tool Execution Ledger

Side-effect execution is tracked independently from Agent checkpoints.

A logical Tool action is identified by:

```text
(run_id, call_id)
```

and includes:

```text
tool_name
intent_hash
status
output
```

Current execution states:

```text
STARTED
COMPLETED
UNKNOWN
```

Completed executions can be replayed instead of re-executed.

### Intent Fingerprinting

Tool intent is fingerprinted using:

```text
tool name
+
canonicalized arguments
↓
SHA-256
```

This prevents an execution key from being silently reused for a different logical action.

### Stable Tool Execution Identity

A stable Tool execution key is generated as:

```text
run_id:call_id
```

Example:

```text
run_123:call_456
```

The key is propagated through the command boundary and is designed to become an end-to-end downstream idempotency key.

---

## Service Boundary Design

The Agent layer does not need to know whether a downstream service is local or remote.

Application contract:

```python
OrderCommandGateway
```

Current adapters:

```text
LocalOrderCommandGateway
GrpcOrderCommandGateway
```

This allows the same Agent application design to evolve from a modular monolith toward independently deployable services.

```text
Current local architecture

CancelOrderTool
→ LocalOrderCommandGateway
→ OrderService
```

```text
Microservice-oriented architecture

CancelOrderTool
→ GrpcOrderCommandGateway
→ Order Service
```

The Agent runtime itself does not need to be rewritten when the deployment boundary changes.

---

## gRPC Contracts

Service contracts are defined independently from application and domain models.

```text
contracts/
└── proto/
    └── ai_backend_lab/
        └── contracts/
            └── order/
                └── v1/
                    └── order_service.proto
```

Current contract:

```proto
service OrderCommandService {
  rpc CancelOrder(CancelOrderRequest)
      returns (CancelOrderResponse);
}
```

The request includes a durable idempotency key:

```proto
message CancelOrderRequest {
  string order_number = 1;
  string idempotency_key = 2;
}
```

Generated Python code lives under:

```text
src/ai_backend_lab/contracts/order/v1/
```

Generated protobuf files should not be edited manually.

Regenerate them with:

```bash
uv run python -m grpc_tools.protoc \
  -I contracts/proto \
  --python_out=src \
  --pyi_out=src \
  --grpc_python_out=src \
  contracts/proto/ai_backend_lab/contracts/order/v1/order_service.proto
```

---

## Project Structure

```text
ai-backend-lab/
├── alembic/
│   └── versions/
│
├── contracts/
│   └── proto/
│       └── ai_backend_lab/
│           └── contracts/
│               └── order/
│                   └── v1/
│                       └── order_service.proto
│
├── src/ai_backend_lab/
│   ├── api/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── dependencies.py
│   │   ├── errors.py
│   │   └── app.py
│   │
│   ├── application/
│   │   ├── order_agent/
│   │   ├── order_assistant/
│   │   ├── ports/
│   │   └── services.py
│   │
│   ├── contracts/
│   │   └── order/
│   │       └── v1/
│   │
│   ├── domain/
│   │   ├── models.py
│   │   └── exceptions.py
│   │
│   ├── infrastructure/
│   │   ├── agent/
│   │   ├── database/
│   │   ├── llm/
│   │   ├── order_commands/
│   │   └── risk.py
│   │
│   ├── observability/
│   │
│   ├── composition.py
│   └── config.py
│
└── tests/
    ├── api/
    ├── application/
    ├── domain/
    ├── fakes/
    └── infrastructure/
```

The project follows a ports-and-adapters / clean architecture style:

```text
API
 ↓
Application
 ↓
Domain

Application
 ↓
Ports
 ↑
Infrastructure Adapters
```

Infrastructure details should not leak into the core application layer.

---

## Technology Stack

- Python 3.12+
- FastAPI
- OpenAI API
- SQLAlchemy 2.x
- MySQL
- Alembic
- Pydantic
- gRPC
- Protocol Buffers
- HTTPX
- Tenacity
- Pytest
- Ruff
- uv

---

## Getting Started

### Install dependencies

```bash
uv sync
```

### Configure environment

Copy the example configuration:

```bash
cp .env.example .env
```

Configure at least:

```text
DATABASE_URL
TEST_DATABASE_URL

OPENAI_API_KEY
LLM_MODEL

RISK_SERVICE_BASE_URL
```

Additional service configuration is introduced as external service integrations are enabled.

### Apply database migrations

```bash
uv run alembic upgrade head
```

Current migrations include persistence for:

```text
orders
agent_runs
tool_executions
```

### Run the API

```bash
uv run uvicorn ai_backend_lab.api.app:app --reload
```

Health endpoint:

```text
GET /health
```

FastAPI OpenAPI documentation:

```text
/docs
```

---

## Testing

Run the full test suite:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
```

Tests are intentionally layered.

```text
Domain tests
→ pure business rules

Application tests
→ orchestration with fakes

Infrastructure tests
→ SQLAlchemy / persistence / integration

API tests
→ HTTP contracts and dependency overrides
```

The Agent tests avoid calling real LLM providers wherever possible so they remain deterministic and inexpensive.

The integration test database is isolated from the development database and uses Alembic migrations to maintain schema consistency.

---

## Reliability Model

The project deliberately separates several reliability concerns.

### Agent Checkpointing

Question answered:

```text
Where did the Agent stop?
```

Handled by:

```text
AgentRunCheckpoint
AgentRunStore
```

### Tool Execution Ledger

Question answered:

```text
Has this logical Tool action already been executed?
```

Handled by:

```text
ToolExecutionRecord
ToolExecutionStore
```

### Distributed Idempotency

Question answered:

```text
Can a downstream side effect safely survive retries,
timeouts, duplicate requests, crashes, and lost responses?
```

The architecture is evolving toward:

```text
stable idempotency key
+
Agent-side execution ledger
+
downstream durable deduplication
+
safe retry with the same key
+
unknown-outcome reconciliation
```

The long-term design does not rely on a shared database transaction between the Agent service and downstream domain services.

---

## Current Development Focus

Current work is focused on reliable side-effect execution in a microservice-oriented Agent architecture.

```text
Agent execution ledger                     ✅
Intent fingerprinting                      ✅
Agent-side completed-result replay          ✅
Execution claim protection                 ✅
OrderCommandGateway boundary               ✅
LocalOrderCommandGateway                   ✅
Versioned Protobuf contract                ✅
GrpcOrderCommandGateway                    ✅

Long-lived gRPC channel lifecycle          🚧
Production gRPC composition / wiring       🚧
Downstream durable idempotency             🚧
Unknown-outcome reconciliation             🚧
Safe retry policy                          🚧
```

The repository is intentionally allowed to contain transitional adapters while architectural boundaries are established incrementally.

---

## Production Evolution Roadmap

The repository is being evolved toward capabilities expected in mature production backend systems.

Planned areas include:

```text
Distributed idempotency
Unknown-outcome reconciliation
Retry and exponential backoff
Circuit breakers
Outbox / Inbox patterns
Reliable event delivery
Event-driven workflows

Structured logging
Metrics
Distributed tracing
Correlation IDs

Authentication
Authorization
Service-to-service identity
TLS / mTLS
Secrets management

Health and readiness probes
Graceful shutdown
Database pool management
Horizontal scaling

Contract testing
Concurrency testing
Failure injection
Compatibility and schema evolution

Agent evaluation
Guardrails
RAG
MCP
Planning
Multi-agent workflows
Long-running Agent execution
```

Capabilities are introduced incrementally and are expected to be implemented as real architectural patterns rather than demo-only placeholders.

---

## Architectural Goal

The long-term goal is not simply to build an Agent that can call tools.

It is to build an Agent backend where:

```text
LLMs can reason,
Tools can act,
Humans can control,
State can survive,
Failures can recover,
Side effects are safe,
Services can evolve independently,
and the system can be operated in production.
```

---

## Status

This project is actively evolving.

It should currently be considered a **learning and reference architecture under active development**, not a finished production deployment.

The architectural direction intentionally follows production-grade backend engineering practices so that the patterns, boundaries, and components developed here can later be reused in real systems.