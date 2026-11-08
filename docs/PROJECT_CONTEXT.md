# Project Context — AI Backend Lab

## 1. Project Overview

**Project name:** AI Backend Lab

**Repository:** `https://github.com/wujiajun/ai-backend-lab`

AI Backend Lab is a long-term engineering project combining structured Agent Engineering learning with the development of a production-oriented backend reference architecture.

It is not simply a tutorial project for calling an LLM API.

The project is intended to demonstrate how an AI Agent can be integrated into a reliable backend system, including execution lifecycle management, tool orchestration, persistence, idempotency, failure recovery, observability, and downstream service integration.

The project has two parallel objectives:

1. Develop practical Agent Engineering capability through a structured curriculum.
2. Build a reusable backend architecture that can serve as a reference for production AI/Agent applications.

Both objectives must be preserved.

## 2. User's Engineering Background

The user has approximately 20 years of software and internet industry experience, including approximately 18 years of Java, backend, and database development.

Previous technical experience includes:

- Java.
- Spring Boot.
- Dubbo.
- Distributed service architecture.
- API Gateway.
- ZooKeeper.
- Redis.
- RabbitMQ.
- Elasticsearch.
- MySQL.
- Database performance and high availability.
- Docker.
- Kubernetes.
- Jenkins.
- Cloud infrastructure.
- Backend system architecture and technical leadership.

The user's goal is to strengthen hands-on software engineering capability and extend that foundation into AI and Agent engineering.

The user does not need a beginner programming course.

The learning process should build on existing backend engineering knowledge and focus on the differences, new abstractions, and new reliability problems introduced by Python, LLMs, Agents, and AI-driven workflows.

## 3. Project Goals

### 3.1 Learning Goals

Develop practical knowledge of:

- Python backend engineering.
- FastAPI.
- SQLAlchemy.
- MySQL and Alembic.
- Asynchronous programming.
- External service integration.
- LLM abstraction and integration.
- Prompt management.
- Structured output.
- Tool calling.
- Agent loops.
- Agent state.
- Tool execution.
- Human approval.
- Checkpointing.
- Idempotency.
- Failure recovery.
- Distributed execution.
- Observability.
- Production reliability.

The user wants to learn these topics in a controlled sequence.

The curriculum's historical numbering must remain stable.

### 3.2 Engineering Goals

Build a backend architecture with:

- Clear domain boundaries.
- Application orchestration.
- Infrastructure adapters.
- Explicit dependency injection.
- Reliable resource lifecycle management.
- Persistent Agent runs.
- Persistent tool execution records.
- Safe side-effect execution.
- Idempotency and deduplication.
- Human approval.
- Concurrency control.
- Failure recovery.
- Testable external integrations.
- Structured logging and tracing.

### 3.3 Long-term Goal

The long-term goal is a robust Agent Runtime that can support more than a simple request-response interaction.

The runtime should eventually be able to:

- Execute multi-step Agent tasks.
- Invoke multiple tools.
- Persist execution state.
- Pause for human approval.
- Resume execution safely.
- Recover from process crashes.
- Handle uncertain downstream outcomes.
- Prevent duplicate side effects.
- Coordinate external services.
- Provide execution observability.
- Support reliable distributed execution.

## 4. Current Technology Direction

The current learning and implementation stack includes:

| Area | Technology |
|---|---|
| Language | Python 3.12 |
| Package and environment management | uv |
| API framework | FastAPI |
| Data validation | Pydantic |
| ORM | SQLAlchemy |
| Database | MySQL |
| Schema migration | Alembic |
| HTTP client | HTTPX |
| LLM integration | OpenAI-compatible SDK integration |
| RPC contract | Protocol Buffers / gRPC |
| Testing | pytest |
| Containerization | Docker |
| Deployment direction | Containerized backend services |

This table describes the project's technology direction and previously observed implementation. It does not guarantee that every component is fully integrated into the current runtime.

Always inspect the repository before making implementation claims.

## 5. Project Scope

The project currently centers on an Order Agent use case.

The use case provides a practical domain for learning:

- Retrieving order information.
- Evaluating order-related risk.
- Calling external services.
- Invoking tools.
- Cancelling an order.
- Requiring human approval for sensitive operations.
- Persisting Agent execution.
- Persisting tool execution records.
- Handling retries and duplicate requests.

The Order domain is a learning and reference use case.

The purpose is not to build a complete commercial order-management platform.

The purpose is to use a realistic business workflow to study Agent and backend reliability.

## 6. Core Engineering Problems

The project must address the following problems progressively.

### 6.1 LLM Integration

An application should not depend directly on a specific LLM vendor SDK.

The application should communicate through an abstraction such as `LLMGateway`.

Vendor-specific behavior belongs in an adapter.

### 6.2 Tool Calling

An LLM may request a tool invocation, but the LLM must not directly execute arbitrary application operations.

The application must:

1. Receive the tool call.
2. Resolve the tool through a registry.
3. Validate its input.
4. Apply execution policy.
5. Execute it through a controlled executor.
6. Persist the result.
7. Return the result to the Agent loop.

### 6.3 Agent State

An Agent run is a long-running application workflow.

Its state must be persisted independently of an individual HTTP request.

The system needs to distinguish:

- Running.
- Waiting for approval.
- Completed.
- Failed.

Additional recovery-related states may be introduced when the design requires them.

### 6.4 Tool Execution Reliability

An Agent run and a side-effecting tool execution are different concepts.

The system must track tool executions independently.

A process crash or network timeout can occur after a downstream operation has completed but before the local application records the result.

The system must not blindly repeat an operation when its outcome is uncertain.

### 6.5 Idempotency

A retry should not accidentally execute the same business operation twice.

The system needs stable tool-call identity and an intent fingerprint.

The downstream service must also participate in durable idempotency when side effects cross a service boundary.

### 6.6 Human Approval

Sensitive operations such as order cancellation should be subject to explicit approval policy.

Approval is part of the Agent workflow, not merely a user-interface feature.

### 6.7 Recovery

Persisting state is not equivalent to implementing recovery.

The runtime must eventually define:

- How interrupted runs are detected.
- How incomplete tool executions are identified.
- How uncertain outcomes are reconciled.
- Which operations may be retried.
- Which operations require human intervention.

## 7. Architectural Direction

The intended architecture separates:

- API layer.
- Application layer.
- Domain layer.
- Ports.
- Infrastructure adapters.
- Persistence.
- External service integrations.

The application layer should orchestrate use cases without depending directly on vendor-specific infrastructure.

Examples of architectural abstractions include:

- `LLMGateway`
- `RiskGateway`
- `OrderCommandGateway`
- `ToolExecutionStore`

Concrete implementations should remain behind appropriate boundaries.

The system should favor explicit dependency wiring and lifecycle management.

## 8. Development Environment

The user's development environment has included:

- macOS.
- MacBook Pro.
- Python 3.12.
- uv.
- IntelliJ IDEA.
- Visual Studio Code.
- A local project workspace under `/Development/ai-backend-lab`.

This is contextual information, not a guarantee of the current machine or repository state.

Do not assume local files are available to Claude unless the project directory has actually been opened.

## 9. Learning and Collaboration Preferences

The user expects:

- A structured curriculum.
- Stable lesson numbering.
- No silent topic changes.
- No unnecessary beginner explanations.
- Architecture-first explanations.
- Real-world engineering scenarios.
- Explicit trade-off analysis.
- Actual source inspection before code review.
- Honest implementation status.
- Tests and failure cases where appropriate.

The user prefers to understand why a design exists before implementing it.

Do not judge understanding solely by whether code runs.

## 10. Project Status Baseline

The following is a historical repository inspection snapshot, not a statement about the live repository at the time of every future session.

At the last known inspection:

- The project had implemented foundational FastAPI and database architecture.
- LLM integration was behind an `LLMGateway` abstraction.
- External risk integration was behind a `RiskGateway` abstraction.
- The Order Agent supported tool calling and Agent run persistence.
- Agent runs and tool executions were persisted separately.
- A tool execution ledger and intent fingerprint mechanism existed.
- A Protobuf contract and gRPC adapter existed for order commands.
- The composition still used `LocalOrderCommandGateway`.
- The gRPC adapter was not yet wired into the FastAPI composition and lifespan.
- A downstream gRPC server implementation was not present in the inspected repository snapshot.
- Durable downstream idempotency was not yet implemented.
- Full crash recovery and uncertain-outcome reconciliation were incomplete.

The last known repository inspection referenced commit:

`358736ef321610bf34ac70b4b0180a07ff76130d`

The last known explicit learning commit was associated with Day 11.7.

The repository must be re-inspected before relying on this snapshot.

## 11. Important Distinction: Learning Project vs Production Deployment

The project aims for production-grade design principles.

That does not mean every component is currently production-ready or deployed.

Use precise language:

- Production-oriented design.
- Production-grade target architecture.
- Implemented behavior.
- Partially implemented behavior.
- Planned capability.

Do not describe the entire project as production-ready without evidence.

## 12. Source of Truth

When information conflicts, use this priority:

1. Current source code.
2. Current tests and their actual execution results.
3. Current database migrations and schema.
4. Current Git history.
5. Current project documentation.
6. Historical conversation and learning records.

Historical records are valuable for learning continuity, but they must not override the actual current implementation.