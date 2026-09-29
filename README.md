# test-case-agent

A small POC agent whose only job is: **given a requirement document, produce
manual test cases in an .xlsx file** — no browser automation, no Playwright.
(That part lives in the separate `../demo-project`.)

## Folder map

- `agent/` — the orchestrator (Python code). Knows the *order* of steps —
  read doc, load skill, call LLM, normalize, write file — not the details of
  any one step.
- `skills/` — **plain markdown instructions**, not code. Each skill is a
  folder with a `SKILL.md` (frontmatter `name`/`description` + a body that
  tells the LLM what job to do and what JSON shape to reply in). This is the
  same convention `../demo-project` uses for its own skills — a skill is
  "job instructions handed to an LLM," never executable logic.
- `tools/` — the concrete actions (Python code): read a document, call the
  OpenRouter API, turn the LLM's JSON reply into rows, write an `.xlsx`
  file. Tools are mechanical — no judgment calls, no prompts.
- `input/` — put your FRD / screen-spec documents here (`.txt`, `.md`,
  `.docx`, `.pdf`). A sample is already in there.
- `output/` — generated `.xlsx` test-case files land here.

**Agent vs. skill vs. tool, in one line:** the agent decides *when* to do
something, the skill (markdown) describes *what a good result looks like*,
and a tool (code) actually *does* it.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# then paste your OpenRouter API key into .env
```

Get a free key at https://openrouter.ai/keys — the default model in
`.env.example` (`meta-llama/llama-3.1-8b-instruct:free`) has a free tier.

## Run it

```bash
python3 main.py \
  --input input/sample_frd.md \
  --req FR-USR-01 \
  --module "User Directory" \
  --out output/fr-usr-01.xlsx \
  --count 10
```

This reads the document, asks the LLM to generate test cases following a
fixed JSON schema, and writes them into `output/fr-usr-01.xlsx` with the
same columns used in the `demo-project` workbooks (Req ID, Test Case ID,
Module, Title, Precondition, Test Steps, Test Data, Expected Result,
Priority, Type, Execution).

Every generated test case is marked `Execution = Manual` — this agent only
drafts test cases, it doesn't verify them against a live app. If you want a
case automated and live-verified, that's the separate pipeline in
`../demo-project`.

### Optional: screenshots

Pass `--screenshots path/to/image.png ...` to attach screenshots of the
screen alongside the document text. This switches the model used to
`OPENROUTER_VISION_MODEL` in `.env` — most free text-only models can't see
images, so a vision-capable model is required for this to have any effect.
