"""Screenshot folder + manifest handling. Pure Python, no macOS dependencies."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

_NUMBERED = re.compile(r"^(\d+)_")


def default_dir() -> Path:
    return Path(os.environ.get("SHOTLOG_DIR", Path.home() / "shotlog")).expanduser()


def slugify(text: str, limit: int = 60) -> str:
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in text.strip())
    return slug[:limit] or "shot"


class Store:
    def __init__(self, base: Path | None = None) -> None:
        self.base = Path(base) if base else default_dir()
        self.base.mkdir(parents=True, exist_ok=True)
        self.manifest = self.base / "manifest.json"

    # -- manifest -----------------------------------------------------------
    def load(self) -> list[dict]:
        if not self.manifest.exists():
            return []
        try:
            data = json.loads(self.manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.manifest.rename(self.base / f"manifest.corrupt-{stamp}.json")
            return []
        return data if isinstance(data, list) else []

    def save(self, items: list[dict]) -> None:
        tmp = self.manifest.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.manifest)

    # -- naming -------------------------------------------------------------
    def next_path(self, name: str) -> Path:
        """Next numbered path. Uses the highest existing number, so deleting a
        file never causes the next capture to overwrite another one."""
        numbers = [0]
        for p in self.base.glob("*.png"):
            m = _NUMBERED.match(p.name)
            if m:
                numbers.append(int(m.group(1)))
        for e in self.load():
            m = _NUMBERED.match(e.get("file", ""))
            if m:
                numbers.append(int(m.group(1)))
        n = max(numbers) + 1
        return self.base / f"{n:03d}_{slugify(name)}.png"

    # -- entries ------------------------------------------------------------
    def register(self, path: Path, source: str, activity: str = "", command: str = "",
                 result: str = "", **extra: str) -> dict:
        entry = {
            "file": path.name,
            "source": source,
            "date": datetime.now().isoformat(timespec="seconds"),
            "activity": activity,
            "command": command,
            "result": result,
            **extra,
        }
        items = self.load()
        items.append(entry)
        self.save(items)
        return entry

    def update(self, file: str, **fields: str) -> dict | None:
        items = self.load()
        for e in items:
            if e.get("file") == file:
                e.update({k: v for k, v in fields.items() if v})
                self.save(items)
                return e
        return None

    def export_markdown(self, title: str = "Screenshots") -> Path:
        lines = [f"# {title}", ""]
        for e in self.load():
            if not (self.base / e["file"]).exists():
                continue
            lines.append(f"## {e.get('activity') or e['file']}")
            lines.append("")
            lines.append(f"![{e['file']}]({e['file']})")
            lines.append("")
            if e.get("command"):
                lines += ["```", e["command"], "```", ""]
            if e.get("result"):
                lines += [e["result"], ""]
            lines += [f"<sub>{e.get('source', '')} · {e.get('date', '')}</sub>", ""]
        out = self.base / "report.md"
        out.write_text("\n".join(lines), encoding="utf-8")
        return out
