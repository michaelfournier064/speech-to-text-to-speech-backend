# speech-to-speech-backend

## Project Setup

Follow these steps to set up the project:

1. **Install pip** (if not already installed)
   - Windows: Download [get-pip.py](https://bootstrap.pypa.io/get-pip.py) and run `python get-pip.py`.
   - Linux/macOS: Usually pre-installed. Check with `pip --version`.

2. **Create a virtual environment**
   - Windows:

     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

   - Linux/macOS:

     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Running the App

To start the application, run:

```bash
uvicorn src.adapters.inbound.api.fastapi_app:app --reload
```

## Implemented Structure

The codebase now follows this clean architecture layout:

- `src/domain/speech_job` for entities, enums, and value objects
- `src/application/ports` for inbound contracts and service interfaces
- `src/application/use_cases` for orchestration logic
- `src/adapters/inbound/api` for FastAPI routes and schemas
- `src/adapters/outbound` for persistence, storage, speech, transcript, and audio adapters
- `src/bootstrap` for configuration and dependency wiring
- `tests/unit` and `tests/integration` for test suites
- `alembic` and `alembic.ini` for migration scaffolding
