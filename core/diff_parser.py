from __future__ import annotations

from typing import List
from core.git_handler import GitFileStat

def infer_projrct_type(file_stats: List[GitFileStat]) -> str:
    if any(f.path.endswith(".py") for f in file_stats):
        return "Python"
    if any(f.path.endswith(".ts") or f.path.endswith(".tsx") for f in file_stats):
        return "TypeScript"
    if any(f.path.endswith(".js") for f in file_stats):
        return "JavaScript"
    return "Software project"

def summarize_diff(file_stats: List[GitFileStat], diff_text: str) -> List[str]:
    points : List[str] = []
    if not file_stats:
        return ["No tracked file diff found. There maybe only Untracked Files"]
    
    top_files = sorted(file_stats, key=lambda f:(f.added + f.removed),reverse=True)[:5]
    for item in top_files:
        points.append(f"Updated {item.path} (+ {item.added} -{item.removed})")

    added_defs = sum(
        1 for line in diff_text.splitlines()
        if line.startswith("+") and ("def" in line or "class" in line)
    )

    if added_defs:
        points.append(f"Introduced {added_defs} new function/class declarations")
    
    removed_lines = sum(f.removed for f in file_stats)

    if removed_lines > 0:
        points.append(f"Removed {removed_lines} lines across changed files")

    return points[:6]