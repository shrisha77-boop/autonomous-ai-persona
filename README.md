# SignalForge AI 🚀

An autonomous AI-powered technology persona that independently discovers, evaluates, remembers, and publishes AI & technology insights without requiring continuous human prompts.

Built for the **ABTalks Vibe Coding Hackathon**.

---

## 📖 Overview

SignalForge AI is designed to simulate an autonomous AI editor operating in the AI and technology ecosystem.

Once initialized, the agent:

- 🔍 Discovers AI and technology topics from live information sources
- 🧠 Evaluates whether each topic is worth publishing
- ✍️ Generates posts in a consistent editorial voice
- 💾 Maintains memory of previously published content
- ⏰ Publishes autonomously over time
- 📊 Provides publishing rationale and source transparency

---

## ✨ Features

- Autonomous topic discovery
- Editorial decision engine
- Consistent AI persona
- Memory-based duplicate prevention
- Background autonomous publishing
- RESTful API
- Transparent publishing rationale
- Live source aggregation

---

## 🛠️ Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- APScheduler

### AI
- Claude Desktop
- Antigravity
- MCP (Breeth)

### Data Sources
- Hacker News
- GitHub Trending
- arXiv RSS
- OpenAI Blog
- Anthropic News
- Google AI Blog

---

## 📁 Project Structure

```
app/
├── api/
├── core/
├── database/
├── models/
├── schemas/
├── services/
├── scheduler/
├── personas/
├── prompts/
└── utils/

tests/
README.md
PROMPTS.md
requirements.txt
```

---

## 🚀 API Endpoints

### Initialize Agent

```
POST /api/agent/init
```

Initializes an autonomous AI persona.

---

### Retrieve Feed

```
GET /api/agent/feed
```

Returns the latest generated posts in reverse chronological order.

---

## 🧠 Autonomous Workflow

```
Initialize Agent
        │
        ▼
Topic Discovery
        │
        ▼
Editorial Evaluation
        │
   ┌────┴────┐
   │         │
Reject     Publish
   │         │
   ▼         ▼
Memory    AI Writer
            │
            ▼
      Store in Database
            │
            ▼
        Feed API
```

---

## 👥 Team

Built by Team SignalForge AI for the ABTalks Vibe Coding Hackathon.

---

## 📄 License

This project is developed exclusively for the ABTalks Vibe Coding Hackathon.
