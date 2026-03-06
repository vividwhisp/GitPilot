from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.ai_client import FreeAIClient
from core.diff_parser import infer_project_type, summarize_diff
from core.executor import SafeExecutor
from core.git_handler import GitCommandError, GitHandler
from core.intent_parser import IntentParser
from core.risk_analyzer import RiskAnalyzer


app = FastAPI(title="Git Workflow Intelligence MVP")


git = GitHandler(".")
ai = FreeAIClient()
parser = IntentParser()
risk_analyzer = RiskAnalyzer()
executor = SafeExecutor(git)


class IntentRequest(BaseModel):
    intent: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _build_smart_commit_payload() -> dict:
    file_stats = git.diff_numstat()
    diff_text = git.diff()
    summary = summarize_diff(file_stats, diff_text)

    suggestion = ai.generate_commit_suggestion(
        project_type=infer_project_type(file_stats),
        file_stats=file_stats,
        summary_points=summary,
        diff_excerpt=diff_text,
    )
    risk = risk_analyzer.analyze(file_stats, diff_text)

    return {
        "title": suggestion.title,
        "description": suggestion.description,
        "bullets": suggestion.bullets,
        "risk_level": risk.level,
        "risk_warnings": risk.warnings,
        "files": [f.__dict__ for f in file_stats],
    }


@app.get("/smart-commit/preview")
def smart_commit_preview() -> dict:
    try:
        return _build_smart_commit_payload()
    except GitCommandError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/smart-commit/execute")
def smart_commit_execute() -> dict:
    try:
        payload = _build_smart_commit_payload()
        title = payload["title"]
        description = payload["description"]
        bullets = payload["bullets"]

        body = description
        if bullets:
            body += "\n\n" + "\n".join(f"- {b}" for b in bullets)

        git.stage_all()
        git.commit(title, body)
        git.push()

        return {"title": title, "pushed": True}
    except GitCommandError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/intent/preview")
def intent_preview(req: IntentRequest) -> dict:
    try:
        plan = parser.parse(req.intent)
        return plan.__dict__
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/intent/execute")
def intent_execute(req: IntentRequest) -> dict:
    try:
        plan = parser.parse(req.intent)
        outputs = executor.execute_git(plan.commands)
        return {"executed": plan.commands, "outputs": outputs}
    except (ValueError, GitCommandError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
