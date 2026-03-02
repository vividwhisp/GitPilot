from __future__ import annotations

from dataclasses import dataclass
from typing import List

from core.git_handler import GitFileStat


@dataclass
class RiskReport:
    level: str
    warnings: List[str]


class RiskAnalyzer:
    def analyze(self, file_stats: List[GitFileStat], diff_text: str) -> RiskReport:
        warnings: List[str] = []
        score = 0

        lowered = diff_text.lower()
        keyword_rules = {
            "auth": "Modifies authentication-related logic",
            "payment": "Touches payment-related code",
            "config": "Changes configuration behavior",
            "env": "Touches environment-variable handling",
        }

        for key, message in keyword_rules.items():
            if key in lowered:
                warnings.append(message)
                score += 2

        for stat in file_stats:
            if stat.path.lower().endswith(".env") or ".env" in stat.path.lower():
                warnings.append(f"Sensitive environment file changed: {stat.path}")
                score += 3
            if stat.removed >= 200 and stat.added <= 50:
                warnings.append(f"Large deletion detected in {stat.path} (-{stat.removed})")
                score += 3

        if score >= 6:
            level = "High"
        elif score >= 3:
            level = "Medium"
        else:
            level = "Low"

        return RiskReport(level=level, warnings=warnings)
