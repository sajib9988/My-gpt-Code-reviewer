# AI Coding Agent Backend

FastAPI backend for the project-based AI coding agent platform.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

The health endpoint is available at `http://localhost:8000/health` and the OpenAPI UI at `http://localhost:8000/docs`.

Set `DATABASE_URL` to the PostgreSQL URL from `.env.example` when using Docker Compose. The default development configuration uses SQLite so the API can be started without external services.

## GitHub OAuth

Create a GitHub OAuth App with callback URL `http://localhost:8000/api/v1/github/callback`, then set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in `.env`. The backend encrypts the access token at rest and never returns it to clients.

GitHub endpoints are project-scoped where repository access is involved:

- `POST /api/v1/github/connect` creates a short-lived OAuth authorization URL.
- `GET /api/v1/github/callback` completes the server-side OAuth exchange.
- `GET /api/v1/github/connection` reports connection status without secrets.
- `GET /api/v1/github/projects/{project_id}/repositories` lists accessible repositories.
- `GET /api/v1/github/projects/{project_id}/file?path=...` reads a repository file.
- `GET /api/v1/github/projects/{project_id}/search?query=...` searches repository code.

## Repository scanning

- `POST /api/v1/projects/{project_id}/scan` scans the configured branch and indexes repository file metadata.
- `GET /api/v1/projects/{project_id}/scan` returns scan status, detected framework, languages, and file count.
- `GET /api/v1/projects/{project_id}/files?path=...` lists indexed files, optionally below a path prefix.

The first scanner runs synchronously for a simple local workflow. Its scanner service is isolated so it can be moved to a Redis worker when background processing is enabled.

## Agent workspace and LLM providers

- `POST /api/v1/projects/{project_id}/conversations` creates an isolated conversation.
- `GET /api/v1/conversations/{conversation_id}/messages` lists its messages.
- `POST /api/v1/conversations/{conversation_id}/messages` adds a user message.
- `POST /api/v1/projects/{project_id}/tasks` creates a project task.
- `PATCH /api/v1/tasks/{task_id}` updates task status.
- `POST /api/v1/projects/{project_id}/runs` queues an agent run.
- `GET /api/v1/runs/{run_id}/events` streams persisted agent events over SSE.
- `GET /api/v1/providers` lists supported provider types.

The provider abstraction currently supports Ollama and OpenRouter. Agents depend on the `LLMProvider` contract, so future OpenAI, Anthropic, or Gemini adapters can be added without changing agent routing code.

Run checks with:

```powershell
python -m pytest
python -m ruff check .
```
