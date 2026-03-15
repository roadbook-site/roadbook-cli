# Roadbook Server

This directory contains the server-side components of the Roadbook project.

## Quick Start

### 1. Documentation
Please refer to the [Handoff Document](docs/handoff.md) for detailed information on the current status, architecture, and testing procedures.

### 2. Running the Server
```bash
# Activate virtual environment
# .venv\Scripts\Activate.ps1

# Start the server (Port 8090)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
```

### 3. Database
The server connects to a PostgreSQL database running in Docker on the `small` (192.168.0.106) machine.
To initialize the database with an admin user:
```bash
python -m scripts.init_db
```

## Features Implemented
- **API**: FastAPI application with basic CRUD for Roadbooks and Users.
- **Database**: PostgreSQL + pgvector for vector search capabilities.
- **Client Integration**: CLI commands (`push`, `pull`, `remote list`) are functional.

See [docs/handoff.md](docs/handoff.md) for more details.
