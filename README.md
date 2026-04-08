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

### 1) Configure environment

Create a `.env` file in the project root:

```env
APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/speech_to_speech
APP_STORAGE_ROOT=.data
APP_FFMPEG_COMMAND=ffmpeg
APP_FFMPEG_TIMEOUT_SECONDS=30
APP_ASR_COMMAND=whisper-cli
APP_ASR_MODEL_PATH=models/ggml-base.en.bin
APP_ASR_LANGUAGE=en
APP_ASR_TIMEOUT_SECONDS=120
APP_TTS_COMMAND=piper
APP_TTS_MODEL_PATH=models/en_US-lessac-medium.onnx
APP_TTS_CONFIG_PATH=
APP_TTS_TIMEOUT_SECONDS=60
APP_CORS_ORIGINS=http://localhost:3000
```

- `APP_DATABASE_URL` points to your PostgreSQL instance.
- `APP_STORAGE_ROOT` is local filesystem storage used for input/output audio objects.
- `APP_FFMPEG_COMMAND` points to the ffmpeg binary used for audio normalization.
- `APP_ASR_COMMAND`/`APP_ASR_MODEL_PATH` configure Whisper CLI transcription.
- `APP_TTS_COMMAND`/`APP_TTS_MODEL_PATH` configure Piper synthesis.
- timeout variables control external command execution limits in seconds.
- `APP_CORS_ORIGINS` is a comma-separated allowlist of frontend origins for browser CORS.

### Runtime prerequisites

The default adapters run external binaries, so these tools must be installed and discoverable:

- `ffmpeg`
- `whisper-cli` (from whisper.cpp) with a valid model file
- `piper` with a valid ONNX voice model (and optional config)

### 2) Ensure PostgreSQL database exists

Create the target database before starting the app. Example:

```sql
CREATE DATABASE speech_to_speech;
```

The app creates the `speech_jobs` table automatically on startup.

### 3) Start the API

To start the application, run:

```bash
uvicorn src.adapters.inbound.api.fastapi_app:app --reload
```

## API Documentation Generation

Generate the documentation from the running API and build a static HTML doc.

### 1) Call the OpenAPI endpoint and save the spec

From the project root (while the API is running on port 8000):

```powershell
Invoke-WebRequest http://localhost:8000/openapi.json -OutFile .\docs\openapi.json
```

### 2) Build static HTML documentation

From the project root:

```powershell
npx @redocly/cli build-docs .\docs\openapi.json --output .\docs\api-docs.html
```

### 3) Open the generated docs

```powershell
start .\docs\api-docs.html
```

### Optional live docs while API is running

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

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
