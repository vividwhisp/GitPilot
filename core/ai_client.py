from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List

import requests

from core.git_handler import GitFileStat

@dataclass
class CommitSuggestion:
    title:str
    description:str
    bullets: List[str]

class FreeAiClient:
    """ Free-first client: prefers local ollama; falls back to hugging face free tier"""

    def __init__(self)  -> None:
        self.provider = os.getenv("AI_PROVODER", "ollama").lower()
        self.ollama_url = os.getenv("OLLAMA_URL", "https://localhost:11434/api/generate")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.hf_model = os.getenv("HF_MODEL", "HuggingFaceH4/zephyr-7b-beta")
        self.hf_token = os.getenv("HF_API_TOKEN", "")
    
    def generate_commit_suggestion(
            self,
            project_type: str,
            file_stats: List[GitFileStat],
            summary_points: List[str],
            diff_excerpt : str,
    ) -> CommitSuggestion:
        prompt = self._build_prompt(project_type, file_stats,summary_points, diff_excerpt)

        try:
            if self.provider == "huggingface":
                text = self._call_huggingface(prompt)
            else:
                text = self._call_ollama(prompt)

            parsed = self._parse_json_response(text)
            return CommitSuggestion
        except Exception:
            return self._fallback_suggestio(file_stats, summary_points)
        

        