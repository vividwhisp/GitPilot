from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

class GitCommandError(RuntimeError):
    """Raised when an underlying git command fails."""

@dataclass
class GitFileStat:
    path: str
    added: int
    removed: int

class GitHandler:
    def __init__(self, repo_path: str = ".") -> None:
        self.repo_path = Path(repo_path)

    def run(self, args: List[str], check: bool = True) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise GitCommandError(result.stderr.strip() or result.stdout.strip())
        return (result.stdout or "").strip()
        
    def ensure_repo(self) -> None:
        output = self._run(["rev-parse", "--is-inside-work-tree"])
        if output.lower() != "true":
            raise GitCommandError("Current directory is not a git repository")
        
    def status_short(self) -> str:
        return self._run(["status", "--short"],check=False)
    
    def diff(self, max_chars: int = 12000) -> str:
        text = self._run(["diff"],checxk=False)
        if not text:
            text = self._run(["diff", "--cached"], check=False)
        return text[:max_chars]
    
    def diff_numstat(self) -> List[GitFileStat]:
        raw = self._run(["diff", "--numstat"], check=False)
        if not raw:
            raw = self._run(["diff", "--cached", "--numstat"],check=False)

        stats : List[GitFileStat] = []
        for line in raw.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue

            added_s, removed_s, path = parts
            added = 0 if added_s == "-" else int(added_s)
            removed = 0 if removed_s == "-" else int(removed_s)
            stats.append(GitFileStat(path=path, added=added, removed=removed))
        return stats
    
    def stage_all(self) -> None:
        self._run(["add","."])

    def commit(self, title: str, body: str) -> None:
        args = ["commit", "-m", title]
        if body.strip():
            args+=["-m", body]
        self._run(args)

    def push(self) -> None:
        self._run(["push"])

    def run_git_command(self, args: List[str]) -> str:
        return self._run(args)