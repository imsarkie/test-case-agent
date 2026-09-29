# Setup — what you need before running this project

This lists everything to have installed/ready on your machine before
`python3 main.py ...` will work. It's separate from `README.md` (which
assumes setup is already done) and `ARCHITECTURE.md` (which explains how
the code works, not how to prepare your machine).

## 1. A code editor (optional, but recommended)

Any editor works since this is plain Python + markdown files. If you don't
already have one: [VS Code](https://code.visualstudio.com/) is a common
free choice — install it, then `File → Open Folder` and pick
`test-case-agent/`. Not strictly required — you can edit files and run
commands with any editor + terminal.

## 2. Python 3.10 or newer

The code uses modern type hints (`str | None`), which need Python 3.10+.

Check what you have:

```bash
python3 --version
```

This machine has `Python 3.14.7` already installed at `/opt/homebrew/bin/python3`
(via Homebrew), so nothing to do here if you're on the same machine. If you
ever need to install/upgrade Python on macOS:

```bash
brew install python3
```

(Get Homebrew itself from https://brew.sh if you don't have it.)

`pip` (Python's package installer) comes bundled with Python 3 — no
separate install needed. Confirm with `pip3 --version`.

## 3. A terminal

macOS's built-in Terminal app (or iTerm2, or VS Code's integrated
terminal) — anything that runs `zsh` or `bash`. All commands in this
project are run from here.

## 4. This project's Python packages

These are project-specific, not system-wide — installed into an isolated
virtual environment so they don't affect anything else on your machine:

```bash
cd /Users/sarkie/Development/office/test-case-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` lists: `openai`, `python-dotenv`, `openpyxl`,
`python-docx`, `pypdf` — see `ARCHITECTURE.md` for what each one is used
for.

You'll need to run `source venv/bin/activate` again every time you open a
new terminal session before running `python3 main.py`.

## 5. An OpenRouter API key

This is what actually powers the LLM calls — without it, the agent will
run right up to the point of asking the LLM and then fail with a clear
"OPENROUTER_API_KEY is not set" error.

1. Create a free account at https://openrouter.ai
2. Generate a key at https://openrouter.ai/keys
3. In the project folder:
   ```bash
   cp .env.example .env
   ```
4. Open `.env` in your editor and paste the key after `OPENROUTER_API_KEY=`

The default model in `.env.example`
(`meta-llama/llama-3.1-8b-instruct:free`) has a free tier, so no payment
method should be required to try this. Free-tier models occasionally
change or get rate-limited — if generation fails with a model error, check
https://openrouter.ai/models?max_price=0 for the current free list and
update `OPENROUTER_MODEL` in `.env`.

If you plan to use `--screenshots`, you also need a vision-capable free
model in `OPENROUTER_VISION_MODEL` — see the comment above it in
`.env.example`.

## 6. Nothing else

No Node.js, no Playwright, no browser, no database — this project
(`test-case-agent`) only drafts test cases as an `.xlsx` file. It doesn't
need any of the browser-automation setup that `../demo-project` needs.

## Quick check that everything's ready

```bash
cd /Users/sarkie/Development/office/test-case-agent
source venv/bin/activate
python3 main.py --input input/sample_frd.md --req FR-USR-01 --module "User Directory" --out output/fr-usr-01.xlsx --count 10
```

- If it fails with `OPENROUTER_API_KEY is not set` → everything except
  step 5 is done correctly; go paste your key into `.env`.
- If it fails with `ModuleNotFoundError` → step 4 wasn't completed, or you
  forgot to `source venv/bin/activate` first.
- If it finishes and prints `Done. N test cases written to ...` → you're
  fully set up.
