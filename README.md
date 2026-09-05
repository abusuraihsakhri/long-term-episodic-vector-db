# Long Term Episodic Vector Db

> **Domain:** Autonomous Agent Systems & Context State Architecture
> **Reference Guidelines & Standards:** `Distributed Systems RFC & State Machine Verification`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Long Term Episodic Vector Db** is an advanced analytical and computational platform implementing Hierarchical Navigable Small World (HNSW) pure Python vector database for long-term memory. It provides a multi-agent evaluation pipeline with cryptographic audit trails and PHI (Protected Health Information) outbound protection.

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization (ROUTINE, ELEVATED, CRITICAL_STAT) with automated operational action recommendations.
- **Multi-Agent Evaluation Pipeline**: InvariantQCWorker, SafetyEscalationWorker, and ProtocolConformanceWorker for comprehensive assessment.
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection.

---

## 🚀 Installation

### Local Development

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/long-term-episodic-vector-db.git
cd long-term-episodic-vector-db

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

### Docker Deployment

```bash
# Build and run with Docker Compose
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
docker compose up --build

# Or build and run manually
docker build -t long-term-episodic-vector-db .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") long-term-episodic-vector-db
```

---

## 💻 CLI Quickstart & Usage

### 1. Run Single Task Evaluation (Audit)
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Interactive Chat Query
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch Process CSV Records
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch FastAPI REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
| Argument | Description | Default |
|:---------|:------------|:--------|
| `--task-id` | Unique task / case identifier | `TASK-2026-001` |
| `--target` | Entity, patient key, or target identifier | `KEY-TARGET-01` |
| `--primary` | Primary domain measurement or score | `28.5` |
| `--secondary` | Secondary kinetic or confidence score | `14.2` |
| `--critical` | Enable emergency escalation flag | `False` |
| `--status` | Status code or phenotype descriptor | `DISCORDANT` |

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task / case identifier (1-128 chars) | Required |
| `target_identifier` | Entity or target key (1-128 chars) | Required |
| `primary_metric` | Primary measurement score (float) | Required |
| `secondary_metric` | Secondary kinetic score (float) | Optional (default: 0.0) |
| `is_critical_flag` | Emergency escalation trigger | Optional (default: False) |
| `status_descriptor` | Status code descriptor (1-64 chars) | Optional (default: "NOMINAL") |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation with full signature verification.
* **Secure Key Management:** Audit signing key sourced from `AUDIT_SECRET_KEY` environment variable with secure fallback generation.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Best Practices

- Always set `AUDIT_SECRET_KEY` to a secure random value in production:
  ```bash
  export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
  ```
- Never commit `.env` files containing secrets.
- The HMAC audit trail provides full chain verification including signature recomputation.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

Run security audit verification:

```bash
python cli.py verify-audit
```

---

## 🏗️ Project Structure

```
long-term-episodic-vector-db/
├── agents/                      # Core multi-agent evaluation pipeline
│   ├── __init__.py
│   ├── api.py                   # FastAPI REST endpoints
│   ├── base.py                  # Security, PHI Guard, HMAC Audit Trail
│   ├── learning.py              # Bayesian calibration engine
│   ├── llm_factory.py           # LLM provider factory
│   ├── metrics.py               # Prometheus metrics collector
│   ├── models.py                # Pydantic v2 data schemas
│   ├── streamer.py              # WebSocket telemetry broadcaster
│   ├── supervisor.py            # Master orchestrator
│   └── workers.py               # Specialized evaluation workers
├── episodic_vector_store/       # HNSW vector store engine
│   ├── __init__.py
│   ├── agents.py                # Sub-agent coordination
│   ├── cli.py                   # Alternate CLI entry point
│   ├── engine.py                # Core algorithmic engine
│   ├── models.py                # Data models
│   └── server.py                # FastAPI server factory
├── tests/                       # Pytest test suite
│   ├── test_enrichment.py
│   ├── test_episodic_vector_store.py
│   └── test_long_term_episodic_vector_db.py
├── web/                         # Operations console (HTML/JS)
├── cli.py                       # Primary CLI entry point
├── enrichment.py                # Enrichment feature suite
├── simulator.py                 # High-throughput stress tester
├── pyproject.toml               # Project metadata and build config
├── docker-compose.yml           # Container orchestration
└── Dockerfile                   # Container build definition
```

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
