# SignalForge AI 🚀

An autonomous AI-powered technology persona that independently discovers, evaluates, remembers, and publishes AI & technology insights without requiring continuous human prompts.

Built for the **ABTalks Vibe Coding Hackathon**.

---

## 📖 Overview

SignalForge AI operates as an autonomous AI technology analyst. Once initialized by an evaluator via `POST /api/agent/init`, the system automatically enters a continuous background loop without requiring any further human intervention.

```text
POST /api/agent/init
        ↓
Agent Starts
        ↓
Scheduler Starts
        ↓
Live Topic Discovery (RSS, Hacker News, GitHub Trending, arXiv)
        ↓
Topic Aggregation, Deduplication & Scoring
        ↓
Memory Check (Skip previously published topics)
        ↓
Editorial Judgment (ACCEPT / REJECT)
        ↓
Persona Content Generation (Strict Grounding Rules via Ollama / LLM)
        ↓
Post Persistence (SQLite DB with Rationale & Source URLs)
        ↓
Sleep & Auto-Repeat Continuous Cycle
        ↓
Evaluator Observes via GET /api/agent/feed?agentId=...
```

---

## 🏗️ System Architecture

```text
                  SignalForge AI
                        │
                        ▼
              Multi-Source Discovery
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
         RSS       Hacker News    GitHub
          │             │          Trending
          └─────────────┼─────────────┘
                        ▼
                       arXiv
                        │
                        ▼
                 Topic Aggregator
                        │
                        ▼
                  Deduplication
                        │
                        ▼
                     Scoring
                        │
                        ▼
                 Topic Selection
                        │
                        ▼
                  Topic Adapter
                        │
                        ▼
                 TopicCandidate
                        │
                        ▼
                   AgentEngine
                    /       \
                   /         \
                  ▼           ▼
              Memory      EditorialEngine
                              │
                              ▼
                           Ollama
                              │
                              ▼
                        PersonaWriter
                              │
                              ▼
                        PostPublisher
                              │
                              ▼
                           SQLite
                              ▲
                              │
                         Scheduler
                              │
                              └──── repeat
```

---

## ✨ Core Features & Requirements Matrix

| Feature | Description | Implementation Status |
| :--- | :--- | :---: |
| **Topic Discovery** | Aggregate live topics from RSS (OpenAI, Google AI), Hacker News, GitHub Trending, and arXiv. | ✅ Complete |
| **Editorial Judgment** | Deterministic evaluation scoring alignment, AI relevance, recency, and source authority (Threshold: 60/100). | ✅ Complete |
| **Consistent Persona** | Enforces strict grounding rules (no hallucinations, no fake stats/links, AI domain focus). | ✅ Complete |
| **Memory System** | Agent-isolated database memory preventing re-publishing of previously processed topics. | ✅ Complete |
| **Autonomous Publishing** | Self-running scheduler requiring zero human prompts after single `/init` call. | ✅ Complete |
| **Hackathon API Contract** | `POST /api/agent/init` and `GET /api/agent/feed?agentId=...` matching spec. | ✅ Complete |
| **Rationale & Sources** | Exposes exact decision rationale and verified discovery source URLs. | ✅ Complete |

---

## 🚀 Quickstart & Setup Guide

### 1. Clone Repository & Setup Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-org/signalforge-ai.git
cd signalforge-ai

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

### 3. Environment Configuration

Create a `.env` file in the project root if customized values are required (defaults work out of the box):

```env
PROJECT_NAME="SignalForge AI"
DATABASE_URL="sqlite+aiosqlite:///./signalforge.db"
PUBLISH_INTERVAL_SECONDS=60
TOPIC_SCORE_THRESHOLD=60
OLLAMA_HOST="http://localhost:11434"
OLLAMA_MODEL="llama3.2:3b"
```

### 4. Install & Run Ollama (Optional for Local LLM)

```bash
# Download and install Ollama from https://ollama.com
# Pull required model:
ollama pull llama3.2:3b

# Ensure Ollama server is running on http://localhost:11434
```

> **Note**: SignalForge AI includes auto-recovery. If Ollama is not running, the system safely falls back to standard grounded generation without interrupting the continuous autonomous loop.

---

## 🏃 Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 Evaluator Workflow & API Specification

### Step 1: Initialize Agent

```http
POST /api/agent/init
Content-Type: application/json

{
  "persona": {
    "name": "Ada",
    "domain": "AI Security"
  }
}
```

**Response (200 OK)**:
```json
{
  "agentId": "550e8400-e29b-41d4-a716-446655440000"
}
```

*Calling this endpoint automatically starts the background autonomous scheduler loop.*

---

### Step 2: Retrieve Feed

```http
GET /api/agent/feed?agentId=550e8400-e29b-41d4-a716-446655440000
```

**Response (200 OK)**:
```json
{
  "posts": [
    {
      "id": "c613e51a-7b3b-4899-b1d6-446f25eb8f12",
      "createdAt": "2026-08-08T18:04:00Z",
      "text": "A new breakthrough in autonomous LLM security guardrails has been published...",
      "rationale": "Selected candidate topic 'LLM Security Guardrails' with editorial score 85/100. Current relevance: AI relevance detected (llm, agentic); Strong persona-domain alignment; Published within the last 24 hours. Selected over competing candidate topics in this cycle due to highest domain alignment and source credibility (arXiv AI).",
      "sources": [
        "https://arxiv.org/abs/2401.00001"
      ]
    }
  ]
}
```

---

## 🧪 Running Tests

To execute the complete test suite including unit tests, API tests, failure recovery tests, and the **Hackathon Evaluator Simulation**:

```bash
pytest -v -s tests/
```

---

## 🛠️ Troubleshooting

- **Database Locked Error**: SignalForge AI uses SQLite in `WAL` mode with a `busy_timeout` of 5000ms.
- **Ollama Connection Refused**: The scheduler automatically detects Ollama unavailability and uses a fallback provider to keep the agent operating continuously.
- **Source Downtime**: Multi-source aggregator isolates source failures using `asyncio.gather(return_exceptions=True)`. If Hacker News or RSS fails, remaining sources (GitHub/arXiv) continue uninterrupted.

---

## 📄 License

Developed for the ABTalks Vibe Coding Hackathon.
