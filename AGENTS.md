# AGENTS.md

This file contains guidelines and commands for agentic coding agents working in this repository.

## Project Overview

This is a FastAPI backend for "Luna de Girasol", a floral shop inventory management system. The project uses:
- **Framework**: FastAPI with SQLModel for data modeling
- **Database**: Turso (SQLite-compatible cloud database)
- **ORM**: SQLAlchemy with SQLModel
- **Linting**: Ruff with extensive rule set
- **SQL Linting**: SQLFluff
- **Dependencies**: Managed with UV (Python 3.13+)

## Essential Commands

### Development & Testing
```bash
# Run development server with auto-reload
uvicorn api:app --reload

# Run server on specific port
uvicorn api:app --reload --port 8001

# Lint code (check for issues)
ruff check .

# Format code automatically
ruff format .

# Fix auto-fixable linting issues
ruff check . --fix

# Run SQL linter on SQL files (if any)
sqlfluff lint .

# Format SQL files
sqlfluff format .

# Check database connection
python database.py
```

### Single Test Commands
```bash
# Note: This project doesn't have a dedicated test suite yet
# To run a single test file when tests exist:
pytest tests/test_specific_file.py::test_function_name

# To run a specific test class:
pytest tests/test_specific_file.py::TestClassName

# To run with verbose output:
pytest -v tests/test_specific_file.py

# To run with coverage (when pytest is configured):
pytest --cov=src tests/test_specific_file.py
```

## Code Style Guidelines

### Import Organization
- Use isort (included in Ruff) for import sorting
- Standard library imports first, then third-party, then local imports
- Use absolute imports for local modules: `from api import app`, not `from .api import app`
- Import groups should be separated by blank lines

### Type Annotations
- All functions should have proper type annotations using modern syntax (`list[str]`, `dict[str, int]`)
- Use `str | None` instead of `Optional[str]`
- Required arguments should be typed, return types should be specified
- Database models use SQLModel typing conventions

### Naming Conventions
- **Classes**: PascalCase (`ProductCatalog`, `InventoryItem`)
- **Functions/Variables**: snake_case (`get_all_inventory`, `current_stock`)
- **Constants**: UPPER_SNAKE_CASE (`TURSO_URL`, `MAX_RETRIES`)
- **Files**: snake_case (`models.py`, `database.py`)
- **Database tables**: snake_case (`product_catalog`, `inventory_item`)

### Database Patterns
- All models inherit from `SQLModel` with `table=True` for database models
- Use separate Base/Create/Read/Update model classes:
  - `{Model}Base`: Common fields
  - `{Model}`: Database table model
  - `{Model}Create`: Input for creation
  - `{Model}Read`: Output for API responses
  - `{Model}Update`: Partial update input
- Use `Relationship()` for foreign key relationships
- Use `Field()` for constraints and default values

### Error Handling
- Use proper logging with `logging.getLogger(__name__)`
- Database operations should use context managers (`get_session_context()`, `transaction_context()`)
- Handle exceptions gracefully, commit on success, rollback on failure
- Return appropriate HTTP status codes from API endpoints

### FastAPI Patterns
- Use dependency injection for database sessions: `session: Session = Depends(get_session)`
- Include response models in route decorators: `@app.get("/inventory", response_model=list[InventoryItemRead])`
- Use tags for route organization: `tags=["Inventory"]`
- Add proper docstrings for all endpoints

### Code Structure
- **api.py**: FastAPI routes and endpoints
- **models.py**: SQLModel database models and Pydantic schemas
- **database.py**: Database connection, session management, health checks
- **backend.py**: Business logic and service functions
- Keep files focused on their primary responsibility

### Linting Configuration (from pyproject.toml)
- Line length: 88 characters
- Use Google-style docstrings (when implemented)
- Double quotes for strings
- Specific ruff rules enabled for code quality (see pyproject.toml for full list)

## Development Workflow

1. **Before committing**: Run `ruff check . --fix` and `ruff format .`
2. **Database changes**: Update models in `models.py`, consider migrations
3. **New endpoints**: Add to `api.py`, include proper response models and error handling
4. **Business logic**: Add to `backend.py` with proper session management
5. **Testing**: Create test files (when implemented) following pytest conventions

## Environment Setup

- Requires Python 3.13+
- Uses UV for dependency management
- Environment variables needed: `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`
- Virtual environment in `.venv/`

## Security Notes

- Database credentials are in `.env` file (never commit)
- All inputs should be validated through Pydantic models
- Use parameterized queries through SQLModel/SQLAlchemy (prevent SQL injection)