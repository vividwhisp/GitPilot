from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List

import requests

from core.git_handler import GitFileStat


@dataclass
class CommitSuggestion:
    title: str
    description: str
    bullets: List[str]


class FreeAIClient:
    """Free-first client: prefers local Ollama; falls back to Hugging Face free tier."""

    def __init__(self) -> None:
        self.provider = os.getenv("AI_PROVIDER", "ollama").lower()
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.hf_model = os.getenv("HF_MODEL", "HuggingFaceH4/zephyr-7b-beta")
        self.hf_token = os.getenv("HF_API_TOKEN", "")

    def generate_commit_suggestion(
        self,
        project_type: str,
        file_stats: List[GitFileStat],
        summary_points: List[str],
        diff_excerpt: str,
    ) -> CommitSuggestion:
        prompt = self._build_prompt(project_type, file_stats, summary_points, diff_excerpt)
        try:
            if self.provider == "huggingface":
                text = self._call_huggingface(prompt)
            else:
                text = self._call_ollama(prompt)
            parsed = self._parse_json_response(text)
            return CommitSuggestion(**parsed)
        except Exception:
            return self._fallback_suggestion(file_stats, summary_points)

    def _build_prompt(
        self,
        project_type: str,
        file_stats: List[GitFileStat],
        summary_points: List[str],
        diff_excerpt: str,
    ) -> str:
        files_block = "\n".join(f"- {f.path} (+{f.added} -{f.removed})" for f in file_stats) or "- Unknown"
        summary_block = "\n".join(f"- {s}" for s in summary_points) or "- No summary available"
        return (
            "You are a strict conventional commits assistant.\n"
            "Return ONLY valid JSON with keys: title, description, bullets.\n"
            "title must be conventional format: type(scope): subject\n"
            "bullets must be array of 2-4 short strings.\n\n"
            f"Project type: {project_type}\n"
            f"Files changed:\n{files_block}\n\n"
            f"Summary:\n{summary_block}\n\n"
            "Diff excerpt:\n"
            f"{diff_excerpt[:3500]}"
        )

    def _call_ollama(self, prompt: str) -> str:
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
        }
        response = requests.post(self.ollama_url, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    def _call_huggingface(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}
        url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 250, "return_full_text": False},
            "options": {"wait_for_model": True},
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "")
        return str(data)

    def _parse_json_response(self, text: str) -> dict:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model output did not contain JSON")
        raw = text[start : end + 1]
        parsed = json.loads(raw)
        title = parsed.get("title", "").strip()
        description = parsed.get("description", "").strip()
        bullets = [str(b).strip() for b in parsed.get("bullets", []) if str(b).strip()]
        if not title:
            raise ValueError("Missing title")
        return {
            "title": title,
            "description": description,
            "bullets": bullets[:4],
        }

    def _fallback_suggestion(self, file_stats: List[GitFileStat], summary_points: List[str]) -> CommitSuggestion:
        scope = "core"
        if file_stats and "/" in file_stats[0].path:
            scope = file_stats[0].path.split("/", 1)[0]
        title = f"chore({scope}): update changed files"
        description = "Apply staged code updates with summarized changes."
        bullets = summary_points[:3] if summary_points else ["Updated project files"]
        return CommitSuggestion(title=title, description=description, bullets=bullets)
