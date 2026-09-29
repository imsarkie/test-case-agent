# Startup guide: evolving this into a FastAPI backend

This is a template/blueprint — like what Spring Initializr hands you as a starting skeleton — for what folder structure and files you'd create if you took the current CLI (`test-case-agent/`) and turned it into a FastAPI **backend service** — an HTTP API other things (a frontend, a script, `curl`) can call. This guide only covers the backend; no frontend is included or assumed.

**This describes a new project**, not a change to the existing `test-case-agent/` folder. Nothing here is installed or created yet — this is the plan to follow when you're ready to build it. A reasonable name for the new folder: `test-case-agent-service/`, as a sibling to `test-case-agent/` inside `office/`.

## What actually changes vs. the CLI version

The **agent / skills / tools** split doesn't change at all — that's the core idea and it survives the move untouched. What changes is everything *around* it:

| CLI version | Service version | Why |
|---|---|---|
| `main.py` parses `argparse` flags | FastAPI **routes** parse an HTTP request | The "trigger" is now an HTTP call, not a terminal command |
| You pass a file **path** (`--input`) | A caller **uploads** a file (multipart form) | There's no shared filesystem between an HTTP client and your server |
| Function call returns directly | The endpoint calls the agent directly and blocks until it's done, then returns the result | Keeps this purely a backend exercise — no background workers or job polling to design around |
| `.env` read via `os.environ.get(...)` | `.env` read via a typed **Settings** object (`pydantic-settings`) | FastAPI convention; gives you validation + autocomplete |
| Print statements for progress | Structured **logging** | A human isn't watching a terminal anymore |
| Nothing to test automatically | `tests/` with `pytest` + FastAPI's `TestClient` | You'll want CI/regression safety once there's an API contract to keep stable |

## Folder structure

```
test-case-agent-service/
├── app/
│   ├── __init__.py
│   ├── main.py                      # creates the FastAPI() app, includes routers, startup/shutdown hooks
│   │
│   ├── api/                         # HTTP layer only — no business logic here
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── test_cases.py        # POST /test-cases/generate, GET /test-cases/{result_id}/download
│   │
│   ├── models/                      # Pydantic request/response shapes (the HTTP "contract")
│   │   ├── __init__.py
│   │   └── schemas.py               # GenerateRequest, TestCase, GenerateResponse
│   │
│   ├── agent/                       # UNCHANGED IN SPIRIT — same orchestrator idea as the CLI
│   │   ├── __init__.py
│   │   ├── agent.py                 # TestCaseAgent — same run() logic, called by an API route instead of main.py
│   │   └── skill_loader.py          # identical to the CLI version
│   │
│   ├── skills/                      # UNCHANGED — still plain markdown, still no code
│   │   └── generate-test-cases/
│   │       └── SKILL.md             # copy straight over from test-case-agent/
│   │
│   ├── tools/                       # UNCHANGED IN SPIRIT — same four tools, same job each
│   │   ├── __init__.py
│   │   ├── read_document.py         # now reads from an uploaded file's temp path instead of a CLI arg path
│   │   ├── llm_client.py            # identical — still the only file that calls OpenRouter
│   │   ├── normalize_test_cases.py  # identical — pure data reshaping
│   │   └── write_excel.py           # identical — writes the .xlsx
│   │
│   ├── storage/                     # NEW — where uploaded docs and generated files actually live on disk
│   │   ├── __init__.py
│   │   └── files.py                 # save_upload(file) -> path, output_path(result_id) -> path
│   │
│   └── core/                        # NEW — cross-cutting setup
│       ├── __init__.py
│       └── config.py                # Settings(BaseSettings): OPENROUTER_API_KEY, OPENROUTER_MODEL, etc., loaded from .env
│
├── uploads/                         # gitignored — uploaded FRDs/screenshots land here temporarily
├── output/                          # gitignored — generated .xlsx files land here, served back via download endpoint
│
├── tests/
│   ├── __init__.py
│   └── test_test_cases_api.py       # spins up TestClient(app), hits the endpoints, asserts on responses
│
├── requirements.txt                 # fastapi, uvicorn[standard], python-multipart, pydantic-settings, + everything already in the CLI's requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## What goes in each new file

### `app/main.py`

```python
from fastapi import FastAPI
from app.api.routes import test_cases

app = FastAPI(title="Test Case Agent")
app.include_router(test_cases.router, prefix="/test-cases", tags=["test-cases"])
```

Nothing else. This file's only job is wiring — same spirit as `main.py` in
the CLI version, just for HTTP instead of the terminal.

### `app/api/routes/test_cases.py`

The two endpoints you'd realistically need:

- `POST /test-cases/generate` — accepts a multipart form (document file, `req_id`, `module`, `count`, optional screenshot files). Saves the upload via `storage/files.py`, calls `TestCaseAgent.run(...)` directly, and returns the generated test cases as JSON (`GenerateResponse`), including a `result_id` for the file it just wrote to `output/`.
- `GET /test-cases/{result_id}/download` — streams back that generated `.xlsx` file (`FileResponse`).

This file only translates HTTP ↔ Python calls. It never talks to the LLM, reads a document, or writes Excel directly — it calls straight into `agent/agent.py`, exactly like `main.py` did in the CLI. `POST /test-cases/generate` blocks until the agent finishes (this is a deliberate simplification to keep the project a plain synchronous backend — see the callout below).

### `app/models/schemas.py`

Pydantic versions of the dicts already flowing through `normalize_test_cases.py` today:

```python
from pydantic import BaseModel

class GenerateRequest(BaseModel):
    req_id: str
    module: str
    count: int | None = None

class TestCase(BaseModel):
    req_id: str
    test_case_id: str
    module: str
    title: str
    precondition: str
    steps: list[str]
    test_data: list[str]
    expected_result: str
    priority: str
    type: str
    execution: str

class GenerateResponse(BaseModel):
    result_id: str
    test_cases: list[TestCase]
```

### `app/core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openrouter_api_key: str
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct:free"
    openrouter_vision_model: str = "meta-llama/llama-3.2-11b-vision-instruct:free"

    class Config:
        env_file = ".env"

settings = Settings()
```

`tools/llm_client.py` would import `settings` from here instead of calling `os.environ.get(...)` directly — same values, just validated once at startup instead of scattered `.get()` calls.

### A note on going synchronous

`POST /test-cases/generate` blocks for as long as the LLM call takes
(10-60+ seconds) before responding — deliberately, to keep this a plain
request/response backend with no background workers, job store, or
polling to build. That's a fine trade for a learning project and for any
caller willing to wait on the request (a script, `curl`, a backend-to-backend
call). It does mean an HTTP client needs a long enough timeout, and it
won't scale to many concurrent requests without adding async job handling
back in later — worth knowing, not worth solving until it's actually a
problem.

### `app/storage/files.py`

Small helpers: `save_upload(upload_file) -> Path` (writes an uploaded `fastapi.UploadFile` into `uploads/<uuid>/...`) and `output_path(result_id) -> Path` (where `write_excel.py` should save to, and where the download endpoint reads from). `result_id` can just be a `uuid4()` generated per request in the route handler.

## New dependencies this would need

(Not installed — for when you're ready: `pip install fastapi "uvicorn[standard]" python-multipart pydantic-settings`, on top of everything already in the CLI's `requirements.txt`.)

- `fastapi` — the web framework itself.
- `uvicorn[standard]` — the server that actually runs a FastAPI app.
- `python-multipart` — required by FastAPI to accept file uploads.
- `pydantic-settings` — typed `.env` loading (replaces manual
  `os.environ.get(...)` calls).

