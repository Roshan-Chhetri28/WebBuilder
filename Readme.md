# Menu2Site AI Backend

An agentic AI backend that converts restaurant menu PDFs into complete React websites using LangGraph and LangChain.

## Features

- **Multi-Agent Workflow**: Uses LangGraph to orchestrate specialized AI agents
- **PDF Processing**: Extracts text and structure from menu PDFs
- **Menu Structuring**: Parses menu data into organized categories and items
- **UI Design**: Generates modern, responsive design systems
- **Code Generation**: Creates complete React SPAs with routing
- **Validation**: Ensures generated code quality and correctness
- **Database Storage**: Stores generated code in PostgreSQL (Neon DB)

## Tech Stack

- **Backend**: FastAPI + uvicorn
- **AI Framework**: LangGraph + LangChain + OpenAI GPT-4
- **Database**: PostgreSQL (Neon DB) + SQLAlchemy
- **Package Manager**: uv
- **PDF Processing**: pdfplumber

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env with your OpenAI API key and Neon DB URL
   ```

3. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start the server**:
   ```bash
   uv run python -m app.main
   ```

## API Endpoints

- `POST /api/generate` - Upload PDF and generate React website
- `GET /api/restaurant/{id}` - Retrieve generated code for a restaurant
- `GET /api/restaurants` - List all restaurants
- `DELETE /api/restaurant/{id}` - Delete restaurant and code

## Agent Workflow

```
PDF Input → Extractor → Structurer → Designer → Generator ⇄ Validator → End
```

Each agent specializes in a specific task, with the validator ensuring code quality through iterative refinement.

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .
```
