from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

@dataclass
class IntentPlan:
    name : str
    description : str
    commands : List[List[str]]
    risk : str

class IntentParsor:
    def parse(self, intent :str) -> IntentPlan:
        text = intent.strip().lower()

        m = re.search(r"new feature branch(?: called| named)?\s+([a-zA-Z0-9._/-]+)",text)
        if m:
            branch = self._sanitize_branch(m.group(1))
            return IntentPlan(
                name="push_to_new_feature_branch",
                description=f"Create branch '{branch}' and push with upstream",
                commands=[["checkout", "-b", branch], ["push", "-u", "origin", branch]],
                risk="Medium",
            )
        
        if "undo last commit" in text and "keep" in text and "change" in text:
            return IntentPlan(
                name="push_current_branch",
                description="Push Current branch to remote",
                commands=[["push"]],
                risk="Medium",
            )
        
        raise ValueError(
            "Intent not recognized. Try: 'push this to new feature branch x', "
            "'undo last commit but keep changes', or 'create new branch x'."
        )
    
    def _sanitize_branch(self, raw: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9._/-]", "-",raw).strip("-.")
        return cleaned or "feature/update"