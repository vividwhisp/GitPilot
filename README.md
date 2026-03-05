# GitPilot

GitPilot is a local-first Git workflow assistant MVP.

This repository is being built in a guided mode:
- one file at a time
- full code explanation for each file
- user types code manually

## Current Progress

Implemented core modules:
- `core/git_handler.py`
- `core/diff_parser.py`
- `core/ai_client.py`
- `core/intent_parser.py`
- `core/risk_analyzer.py`
- `core/executor.py`

Scaffolded but not yet filled in this pass:
- `cli.py`
- `server.py`
- `main.py`
- `vscode-extension/` runtime wiring

## MVP Scope

Target MVP includes:
- Smart commit suggestion
- Commit risk warning
- Intent to Git command mapping
- Safe command execution checks
- VS Code extension wrapper

Out of scope for MVP:
- PR automation
- Team dashboard
- Analytics

## Tech Stack

Backend:
- Python
- FastAPI
- subprocess-based git integration

LLM:
- Local Ollama (default free path)
- Optional Hugging Face inference fallback

Frontend integration:
- VS Code extension (TypeScript)

## Install

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

## Development Flow

1. Implement backend core modules.
2. Add API surface in `server.py`.
3. Add CLI in `cli.py` and `main.py`.
4. Connect VS Code extension to local API.
5. Validate end-to-end in Extension Development Host.

## Project Layout

- `core/`: backend domain modules
- `server.py`: FastAPI endpoints for extension/CLI
- `cli.py`: terminal flow for smart commit + intent execution
- `main.py`: app entrypoint
- `vscode-extension/`: VS Code extension source/build/debug config
