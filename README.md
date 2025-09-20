# Church Manager v4

AI-powered WhatsApp bot for church volunteer scheduling and ministry management using natural language processing.

## 🚀 Quick Start

```bash
# Install dependencies
poetry install

# Run the application
poetry run uvicorn main:app --reload

# Access API documentation
# http://localhost:8000/docs
```

## 📋 Overview

Church Manager v4 transforms WhatsApp conversations into structured church management actions. Users interact naturally through WhatsApp, and our LangGraph-powered AI agents understand intent and execute appropriate actions.

### Key Features

- 💬 **Natural Language Interface** - Chat naturally via WhatsApp
- 🤖 **AI-Powered** - LangGraph agents process and understand intent
- 📅 **Smart Scheduling** - Generate monthly schedules automatically
- 👥 **Volunteer Management** - Assign and track ministry volunteers
- 🧠 **Conversation Memory** - Maintains context across messages

## 📚 Documentation

- [Architecture Overview](docs/architecture.md) - System design and tech stack
- [LangGraph Agents](docs/langgraph-agents.md) - AI agent implementation
- [Database Schema](docs/database.md) - Data model and relationships
- [API Reference](docs/api.md) - WAHA webhook integration
- [Development Guide](docs/development.md) - Setup and development

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **AI Orchestration**: LangGraph
- **Database**: PostgreSQL + SQLAlchemy
- **WhatsApp**: WAHA (WhatsApp HTTP API)
- **Validation**: Pydantic
- **Testing**: pytest

## 💬 Usage Example

```
User: "Create schedule for all Sundays in January"
Bot: "Created 4 Sunday services for January. Need volunteers?"

User: "Yes, assign Maria to worship team on the 14th"  
Bot: "Maria assigned to worship team for January 14th"
```

## 🎯 Project Goals

- Internal church use (hundreds of users max)
- Single webhook endpoint for WAHA
- Clean, maintainable code (DRY, KISS, SOLID)
- No over-engineering

## 📝 License

Internal use only

---

For detailed information, explore the documentation links above.