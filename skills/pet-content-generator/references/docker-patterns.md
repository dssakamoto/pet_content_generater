# Docker & Infrastructure Patterns Reference

## Table of Contents
- [Docker Compose Configuration](#docker-compose-configuration)
- [Environment Variables](#environment-variables)
- [Networking](#networking)
- [Volume Strategy](#volume-strategy)
- [Build & Run](#build--run)

## Docker Compose Configuration

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app/app          # hot-reload Python
      - backend-outputs:/app/app/outputs # persist generated files
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src         # hot-reload React
      - ./frontend/index.html:/app/index.html
    depends_on:
      - backend

volumes:
  backend-outputs:
```

## Environment Variables

`.env` file (loaded by backend only):

| Variable | Default | Description |
|---|---|---|
| `IMAGE_GENERATOR` | `mock` | Strategy: `mock`, `dalle`, `stability` |
| `OUTPUT_DIR` | `/app/app/outputs` | Generated file storage path |

Future keys (commented in `.env.example`):
- `OPENAI_API_KEY` for DALL-E integration
- `STABILITY_API_KEY` for Stability AI integration

## Networking

- Frontend → Backend: via Vite proxy using Docker service name `http://backend:8000`
- Browser → Frontend: `http://localhost:5173`
- Browser → Backend (direct): `http://localhost:8000` (available but not needed)
- CORS: backend allows `http://localhost:5173` origin

## Volume Strategy

| Volume | Type | Purpose |
|---|---|---|
| `./backend/app:/app/app` | Bind mount | Python source hot-reload |
| `backend-outputs` | Named volume | Persist generated images/videos across restarts |
| `./frontend/src:/app/src` | Bind mount | React source hot-reload |
| `./frontend/index.html:/app/index.html` | Bind mount | HTML hot-reload |

Named volume `backend-outputs` ensures generated content survives container restarts. Bind mounts enable live development without rebuilding containers.

## Build & Run

```bash
# First run
docker compose up --build

# Subsequent runs
docker compose up

# Rebuild single service
docker compose up --build backend

# View logs
docker compose logs -f backend
```

Prerequisites: Docker Desktop must be running.
