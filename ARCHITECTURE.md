# How this project fits together

This explains every folder and file in `test-case-agent/`, what each one
does, and exactly how they call into each other for one run of the program.

## The one-sentence version

`main.py` reads your command-line arguments → hands them to
`agent/agent.py` → which reads your document, loads the instructions from
`skills/generate-test-cases/SKILL.md`, asks the LLM (via `tools/llm_client.py`)
to follow those instructions, cleans up the reply (`tools/normalize_test_cases.py`),
and writes it to an Excel file (`tools/write_excel.py`).

## The three-layer idea

| Layer | Folder | What lives here | Can it think/decide anything? |
|---|---|---|---|
| Agent | `agent/` | Python code that decides the *order* of steps | Only "what happens when" — no domain judgment |
| Skill | `skills/` | Plain **markdown** — instructions, not code | This is where all the QA judgment/knowledge lives, but it doesn't execute anything itself — it's just text handed to the LLM |
| Tools | `tools/` | Python code that does one concrete, mechanical thing each | No judgment calls — read a file, call an API, write a file |

The agent doesn't know how to write a good test case. The skill doesn't
know how to read a `.docx` file or talk to OpenRouter. Each piece only
knows its own job — that separation is the whole point of the exercise.

---

## Folder-by-folder, file-by-file

### `main.py` (project root)

The entry point — what you actually run (`python3 main.py ...`).

- Loads `.env` via `load_dotenv()` (so `OPENROUTER_API_KEY` etc. become
  available as environment variables).
- Defines the command-line flags: `--input`, `--req`, `--module`, `--out`,
  `--count`, `--screenshots`.
- Creates one `TestCaseAgent()` (from `agent/agent.py`) and calls
  `agent.run(...)` with those arguments.
- Prints the final "Done. N test cases written to ..." line.

It contains zero domain logic — it's purely "parse args, call the agent."

### `agent/` — the orchestrator

#### `agent/__init__.py`

Empty. Its only job is to make `agent/` importable as a Python package
(`from agent.agent import TestCaseAgent`), so this and `tools/__init__.py`
are structural, not functional.

#### `agent/agent.py`

The orchestrator. Defines `TestCaseAgent.run(...)`, which is the entire
pipeline, in order:

1. `read_document(input_path)` — from `tools/read_document.py` — turns
   your `.txt`/`.md`/`.docx`/`.pdf` file into plain text.
2. `load_skill(str(SKILL_PATH))` — from `agent/skill_loader.py` — loads
   `skills/generate-test-cases/SKILL.md` into a `Skill` object with
   `.name`, `.description`, `.body`.
3. Builds `task`: a plain-text string containing the module name, the
   optional `--count` hint, and the document text, wrapped between
   `--- SOURCE DOCUMENT ---` / `--- END DOCUMENT ---` markers.
4. `chat_json(skill.body, task, image_paths=screenshots)` — from
   `tools/llm_client.py` — this is **the exact moment the skill file gets
   used**: `skill.body` (everything in `SKILL.md` below the `---
   frontmatter ---`) is passed in as the `instructions` argument, i.e. it
   becomes the LLM's system prompt.
5. `normalize_test_cases(raw, req_id=req_id, module=module)` — from
   `tools/normalize_test_cases.py` — turns the LLM's raw JSON into row
   dicts.
6. `write_test_cases_to_excel(cases, output_path)` — from
   `tools/write_excel.py` — writes the `.xlsx` file.

`SKILL_PATH` (a constant near the top of the file) hardcodes which skill
folder to load: `skills/generate-test-cases/SKILL.md`. If you added a
second skill folder, this is the line you'd change (or extend) to use it.

#### `agent/skill_loader.py`

A tiny, dependency-free parser. `load_skill(path)`:

1. Reads the whole `SKILL.md` file as text.
2. Splits it into three parts on the `---` lines: (nothing) / frontmatter /
   body.
3. Parses the frontmatter as flat `key: value` lines into a dict (so
   `name: generate-test-cases` becomes `meta["name"] = "generate-test-cases"`).
4. Returns a `Skill(name=..., description=..., body=...)` dataclass.

This file doesn't know anything about test cases or QA — it would load
*any* correctly-formatted `SKILL.md`. It's generic infrastructure for
"skills are markdown files with frontmatter," same idea as
`../demo-project/.claude/skills/*/SKILL.md`.

### `skills/` — the instructions (markdown, not code)

#### `skills/generate-test-cases/SKILL.md`

This is **not executed** — it's read as plain text and stuffed into the
LLM's system prompt by `agent/agent.py` (step 4 above). It has two parts:

- **Frontmatter** (between the first two `---` lines): `name` and
  `description`. Currently only `name` is actually used in code (for the
  `[agent] loading skill: ...` log line and the
  `[agent] calling LLM per skill '...'` log line in `agent.py`).
  `description` isn't read by any code yet — it's there for a human
  skimming the file, and for future use if you ever build a registry that
  picks a skill by matching a task to its description.
- **Body** (everything after the second `---`): the actual instructions —
  who the LLM should act as, what inputs it might receive (document text,
  optional screenshots), the required JSON output schema, field-by-field
  writing guidance, priority/type definitions, required coverage rules, a
  worked example, and hard rules (no fabricating requirements, no
  commentary outside the JSON, etc.). This whole body becomes the `system`
  message sent to OpenRouter.

If you want the generated test cases to be different in any way — stricter
coverage rules, a different tone, additional required fields — **you edit
this markdown file**, not any Python file. That's the entire reason skills
are separated from code: changing behavior shouldn't require touching
logic.

### `tools/` — the concrete actions

#### `tools/__init__.py`

Empty, same purpose as `agent/__init__.py` — makes `tools/` an importable
package.

#### `tools/read_document.py`

`read_document(path)` — dispatches on file extension:
- `.txt` / `.md` → read as plain text directly.
- `.docx` → uses the `python-docx` library to pull paragraph text and
  table cell text.
- `.pdf` → uses the `pypdf` library to extract text per page.

Called once, by `agent/agent.py`, at the very start of `run()`.

#### `tools/llm_client.py`

The only file that talks to OpenRouter. Two pieces:

- `_client()` — builds an `OpenAI` SDK client pointed at OpenRouter's base
  URL (`https://openrouter.ai/api/v1`), using `OPENROUTER_API_KEY` from the
  environment. Raises a clear error if the key isn't set.
- `chat_json(instructions, task, image_paths=None)` — the function
  `agent.py` calls:
  - `instructions` is `skill.body` (see above) — the LLM's system prompt.
    This function appends one more line to it itself: "Respond with a
    single JSON object only..." — that formatting rule lives here, not in
    the skill file, because it's a mechanical requirement of *any* JSON-mode
    request, not domain knowledge.
  - `task` is the user message — the document text and module/count info
    built by `agent.py`.
  - If `image_paths` is given (from `--screenshots`), it switches to
    `OPENROUTER_VISION_MODEL` and builds a multimodal message (text +
    base64-encoded images via `_image_content_part`) instead of plain text.
    Otherwise it uses `OPENROUTER_MODEL`.
  - Sends the request, strips any stray ` ```json ` fences the model might
    add despite instructions, parses the reply as JSON, and returns the
    parsed `dict`. Raises `ValueError` if it isn't valid JSON.

#### `tools/normalize_test_cases.py`

`normalize_test_cases(raw, req_id, module)` — pure data reshaping, no LLM
calls, no file I/O. Takes the raw `{"test_cases": [...]}` dict the LLM
returned and, for each entry, builds a row dict with all the workbook
columns filled in: assigns a generated `test_case_id` like `TC_FR-USR-01_001`,
copies over `title`/`precondition`/`steps`/`test_data`/`expected_result`/
`priority`/`type`, sets `req_id` and `module` from the function's arguments
(not from the LLM), and hardcodes `execution: "Manual"` (this agent only
drafts test cases — it never runs/verifies them, so nothing it produces is
ever "Automatable").

#### `tools/write_excel.py`

`write_test_cases_to_excel(cases, output_path, sheet_name="Test Cases")` —
takes the list of row dicts from `normalize_test_cases` and writes them
into a real `.xlsx` file using `openpyxl`. `COLUMNS` at the top of the file
is the fixed header row — the same column names used by the workbooks in
`../demo-project`, so a generated file is compatible with that project's
`ingest_test_cases.py` if you ever wanted to feed one into it.
`_join_lines` turns a Python list (like `steps`) into a single cell with
one item per line, matching how the original manual workbooks store
multi-line steps.

### `input/`

Where you put source documents. Currently contains `sample_frd.md`, an
example FRD-style description of the "User Directory" screen, used in the
example command in `README.md`. Nothing here is code — it's just example
input.

### `output/`

Where generated `.xlsx` files land (e.g. `output/fr-usr-01.xlsx` from the
example command). Contains only a `.gitkeep` placeholder so the empty
folder exists before you've generated anything; generated `.xlsx` files
are gitignored.

### `requirements.txt`

The Python packages the project depends on: `openai` (used as an
OpenRouter-compatible client in `tools/llm_client.py`), `python-dotenv`
(loads `.env` in `main.py`), `openpyxl` (writes the `.xlsx` in
`tools/write_excel.py`), `python-docx` and `pypdf` (read `.docx`/`.pdf` in
`tools/read_document.py`).

### `.env.example` / `.env`

`.env.example` is checked in and documents the three environment variables
the code reads (all via `os.environ.get(...)` in `tools/llm_client.py`):
`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_VISION_MODEL`. You
copy it to `.env` and paste in your real key — `.env` is gitignored and is
never committed.

### `.gitignore`

Keeps `.env` (secrets), `venv/` (your local Python environment),
`__pycache__/`/`*.pyc` (compiled Python bytecode), and generated
`output/*.xlsx` files out of version control.

### `README.md`

Human-facing setup and usage instructions (how to install, how to run, what
`--screenshots` does). This file (`ARCHITECTURE.md`) goes one level deeper
— *why* the folders are shaped this way and exactly how each piece calls
the next.

### `venv/`

Your local Python virtual environment (created by
`python3 -m venv venv`). Not part of the project's logic — just an
isolated place for the packages in `requirements.txt` to live so they
don't pollute your system Python.

---

## Full trace of one run

Running:

```bash
python3 main.py --input input/sample_frd.md --req FR-USR-01 --module "User Directory" --out output/fr-usr-01.xlsx --count 10
```

steps through the code exactly like this:

```
main.py: main()
  load_dotenv()                          # .env → os.environ
  args = ap.parse_args()                 # --input, --req, --module, --out, --count, --screenshots
  agent = TestCaseAgent()                # agent/agent.py
  agent.run(input_path, req_id, module, output_path, count_hint, screenshots)

    agent/agent.py: TestCaseAgent.run()
      document_text = read_document(input_path)          # tools/read_document.py
      skill = load_skill(SKILL_PATH)                      # agent/skill_loader.py
        → reads skills/generate-test-cases/SKILL.md
        → returns Skill(name, description, body)
      task = f"Module...\n---SOURCE DOCUMENT---\n{document_text}\n..."
      raw = chat_json(skill.body, task, image_paths=screenshots)   # tools/llm_client.py
        → skill.body becomes the system prompt
        → task becomes the user message (+ images if any)
        → calls OpenRouter, parses reply as JSON
      cases = normalize_test_cases(raw, req_id, module)   # tools/normalize_test_cases.py
        → raw["test_cases"] list → list of row dicts, IDs assigned
      write_test_cases_to_excel(cases, output_path)       # tools/write_excel.py
        → writes output/fr-usr-01.xlsx

  print(f"Done. {len(cases)} test cases written to {args.out}")
```

## How data changes shape at each step

1. **File on disk** (`input/sample_frd.md`) →
2. **Plain text string** (`document_text`, from `read_document`) →
3. **Skill instructions + task text** (`skill.body`, `task` — what gets sent
   to the LLM) →
4. **Raw JSON from the model**:
   ```json
   { "test_cases": [ { "title": "...", "steps": [...], "priority": "High", "type": "Positive", ... } ] }
   ```
5. **Normalized row dicts** (from `normalize_test_cases`) — same fields,
   plus `req_id`, `test_case_id` (generated), `module`, `execution: "Manual"`:
   ```python
   {"req_id": "FR-USR-01", "test_case_id": "TC_FR-USR-01_001", "module": "User Directory",
    "title": "...", "steps": [...], "priority": "High", "type": "Positive", "execution": "Manual", ...}
   ```
6. **Rows in `output/fr-usr-01.xlsx`** — the same dicts, one row per case,
   under the fixed `COLUMNS` header from `tools/write_excel.py`.

## If you want to change something, here's where

| You want to... | Edit this file |
|---|---|
| Change how thorough/strict test case generation is, add new rules, change tone | `skills/generate-test-cases/SKILL.md` (markdown only) |
| Support a new input document type (e.g. `.html`) | `tools/read_document.py` |
| Switch LLM provider or model | `.env` (`OPENROUTER_MODEL` / `OPENROUTER_VISION_MODEL`) — no code change needed |
| Change the JSON→row mapping or the auto-generated Test Case ID format | `tools/normalize_test_cases.py` |
| Change the `.xlsx` columns or formatting | `tools/write_excel.py` |
| Add a new CLI flag | `main.py` (parse it) + `agent/agent.py` (use it) |
| Add a second skill (e.g. "generate-api-test-cases") | New folder `skills/generate-api-test-cases/SKILL.md`, then point `agent.py` at it (or add logic to pick a skill by name) |
