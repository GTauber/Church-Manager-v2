# Development Guide

## Prerequisites

- Python 3.13+
- Poetry (for dependency management)
- Docker & Docker Compose (for WAHA and PostgreSQL)
- Git

## Initial Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd church-manager-v4
```

### 2. Install Dependencies

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://church_user:church_pass@localhost:5432/church_db
DATABASE_ECHO=False

# WAHA Configuration
WAHA_API_URL=http://localhost:3000
WAHA_SESSION_NAME=default
WAHA_WEBHOOK_URL=http://host.docker.internal:8000/webhook

# Application
APP_ENV=development
APP_DEBUG=True
APP_HOST=0.0.0.0
APP_PORT=8000

# LangGraph / AI
OPENAI_API_KEY=your_openai_api_key_here
# Or use another provider
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Security
SECRET_KEY=your-secret-key-here-generate-with-openssl
WEBHOOK_SECRET=shared-secret-with-waha

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 4. Start Infrastructure

```bash
# Start WAHA and PostgreSQL
docker-compose up -d

# Verify services are running
docker-compose ps

# Check WAHA logs
docker-compose logs -f waha

# Check PostgreSQL logs
docker-compose logs -f postgres
```

### 5. Database Setup

```bash
# Create database migrations
alembic init alembic

# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Verify database
poetry run python -c "from app.core.database import engine; print('Database connected!')"
```

### 6. WAHA Setup

1. Access WAHA at http://localhost:3000
2. Scan QR code with WhatsApp
3. Verify connection status

```bash
# Check WAHA session status
curl http://localhost:3000/api/sessions/default

# Should return:
# {"status": "WORKING", ...}
```

## Project Structure

```
church-manager-v4/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── agents/              # LangGraph agents
│   │   ├── __init__.py
│   │   ├── router.py        # Intent routing
│   │   ├── memory.py        # Conversation memory
│   │   ├── intents/         # Intent handlers
│   │   │   ├── user.py
│   │   │   ├── schedule.py
│   │   │   └── ministry.py
│   │   └── workflows/       # LangGraph workflows
│   ├── api/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── webhook.py       # WAHA webhook
│   │   └── deps.py          # Dependencies
│   ├── core/                # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py        # Settings
│   │   ├── database.py      # DB connection
│   │   └── logging.py       # Logging setup
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── ministry.py
│   │   ├── schedule.py
│   │   └── base.py          # Base model
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── ministry.py
│   │   ├── schedule.py
│   │   └── waha.py          # WAHA payloads
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── ministry.py
│   │   └── schedule.py
│   └── repositories/        # Data access
│       ├── __init__.py
│       ├── base.py
│       └── user.py
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_agents/
│   ├── test_api/
│   ├── test_services/
│   └── test_repositories/
├── alembic/                 # Database migrations
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── docker-compose.yml       # Infrastructure
├── Dockerfile              # App container
├── pyproject.toml          # Poetry config
├── .env.example            # Environment template
└── README.md              # Project overview
```

## Development Workflow

### Running the Application

```bash
# Development mode with auto-reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
# http://localhost:8000/docs

# Access alternative API docs
# http://localhost:8000/redoc
```

### Code Style

The project follows these conventions:

```bash
# Format code with black
poetry run black app/ tests/

# Sort imports with isort
poetry run isort app/ tests/

# Type checking with mypy
poetry run mypy app/

# Linting with flake8
poetry run flake8 app/

# All checks at once
poetry run make lint
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_agents/test_router.py

# Run with verbose output
poetry run pytest -v

# Run only marked tests
poetry run pytest -m "unit"
```

### Test Structure

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def client():
    """Test client fixture"""
    from app.main import app
    return TestClient(app)

@pytest.fixture
def db_session():
    """Database session fixture"""
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
```

### Adding New Features

1. **Create Database Model** (if needed)
```python
# app/models/feature.py
from sqlalchemy import Column, String, UUID
from app.models.base import Base

class Feature(Base):
    __tablename__ = "features"
    
    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
```

2. **Create Pydantic Schema**
```python
# app/schemas/feature.py
from pydantic import BaseModel
from uuid import UUID

class FeatureCreate(BaseModel):
    name: str

class FeatureResponse(BaseModel):
    id: UUID
    name: str
    
    class Config:
        from_attributes = True
```

3. **Implement Service Layer**
```python
# app/services/feature.py
from app.repositories.feature import FeatureRepository

class FeatureService:
    def __init__(self, repository: FeatureRepository):
        self.repository = repository
    
    async def create_feature(self, data):
        return await self.repository.create(data)
```

4. **Add LangGraph Agent Handler**
```python
# app/agents/intents/feature.py
from langgraph.graph import StateGraph

async def handle_feature_intent(state):
    # Process intent
    # Call service
    # Return response
    pass
```

5. **Write Tests**
```python
# tests/test_services/test_feature.py
import pytest

@pytest.mark.asyncio
async def test_create_feature(feature_service):
    result = await feature_service.create_feature({"name": "Test"})
    assert result.name == "Test"
```

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add feature table"

# Create empty migration for custom SQL
alembic revision -m "Custom migration"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Migration Best Practices

1. Always review auto-generated migrations
2. Test migrations on a copy of production data
3. Include both upgrade and downgrade paths
4. Keep migrations small and focused

## Debugging

### Debug Mode

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()

# Enable debug logging
if settings.debug:
    logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

#### WAHA Connection Issues
```bash
# Check WAHA status
curl http://localhost:3000/api/sessions

# Restart WAHA
docker-compose restart waha

# View WAHA logs
docker-compose logs -f waha
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Connect to database
docker-compose exec postgres psql -U church_user -d church_db

# Reset database
alembic downgrade base
alembic upgrade head
```

#### LangGraph Agent Issues
```python
# Enable agent debugging
import langchain
langchain.debug = True

# Add logging to agents
import logging
logger = logging.getLogger(__name__)

async def agent_handler(state):
    logger.debug(f"State: {state}")
    # Process...
```

## Performance Optimization

### Database Queries

```python
# Use eager loading for relationships
from sqlalchemy.orm import joinedload

users = session.query(User).options(
    joinedload(User.ministries)
).all()

# Use bulk operations
session.bulk_insert_mappings(User, user_data)
session.commit()
```

### Async Operations

```python
# Use async/await throughout
async def process_webhook(data):
    async with get_session() as session:
        result = await session.execute(query)
        return result.scalars().all()
```

### Caching

```python
# Simple in-memory cache
from functools import lru_cache

@lru_cache(maxsize=100)
def get_ministry_by_name(name: str):
    return session.query(Ministry).filter_by(name=name).first()
```

## Deployment Checklist

- [ ] Set production environment variables
- [ ] Run database migrations
- [ ] Configure WAHA webhook URL
- [ ] Set up monitoring/logging
- [ ] Configure backups
- [ ] Set up SSL/HTTPS
- [ ] Configure rate limiting
- [ ] Test webhook endpoint
- [ ] Verify WhatsApp connection
- [ ] Run smoke tests

## Useful Commands

```bash
# View logs
docker-compose logs -f

# Access PostgreSQL
docker-compose exec postgres psql -U church_user -d church_db

# Reset everything
docker-compose down -v
docker-compose up -d
alembic upgrade head

# Export requirements (for non-Poetry deployments)
poetry export -f requirements.txt --output requirements.txt

# Update dependencies
poetry update

# Add new dependency
poetry add package-name

# Add dev dependency
poetry add --group dev package-name
```

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test
3. Run linting and tests
4. Commit with clear message
5. Push and create pull request

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [WAHA Documentation](https://waha.devlike.pro/)
- [Poetry Documentation](https://python-poetry.org/docs/)