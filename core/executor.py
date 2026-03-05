from __future__ import annotations

from typing import List

from core.git_handler import GitCommandError, GitHandler


FORBIDDEN_ARGS = {"--hard", "clean", "-fd", "--force"}


class SafeExecutor:
    def __init__(self, git_handler: GitHandler) -> None:
        self.git_handler = git_handler

    def execute_git(self, commands: List[List[str]]) -> List[str]:
        outputs: List[str] = []
        for cmd in commands:
            self._validate(cmd)
            outputs.append(self.git_handler.run_git_command(cmd))
        return outputs

    def _validate(self, cmd: List[str]) -> None:
        if not cmd:
            raise GitCommandError("Empty command is not allowed")
        if any(part in FORBIDDEN_ARGS for part in cmd):
            raise GitCommandError(f"Blocked unsafe command: {' '.join(cmd)}")