"""shotlog MCP server: capture macOS windows into a numbered, captioned evidence log."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .store import Store

mcp = FastMCP("shotlog")
store = Store()


def _windows() -> list[dict]:
    import Quartz  # macOS only; imported lazily so the store stays portable

    opts = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
    out = []
    for w in Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID) or []:
        if w.get("kCGWindowLayer", 1) != 0:
            continue
        b = w.get("kCGWindowBounds", {})
        if b.get("Width", 0) < 200 or b.get("Height", 0) < 150:
            continue
        out.append({
            "id": int(w["kCGWindowNumber"]),
            "app": w.get("kCGWindowOwnerName", ""),
            "title": w.get("kCGWindowName", "") or "",
            "size": f"{int(b['Width'])}x{int(b['Height'])}",
        })
    return out  # front-most first


@mcp.tool()
def list_windows() -> list[dict]:
    """List visible windows (id, app, title, size). The first one is the front-most."""
    return _windows()


@mcp.tool()
def save_screenshot(
    name: str,
    app: str = "",
    title_contains: str = "",
    activity: str = "",
    command: str = "",
    result: str = "",
) -> dict:
    """Capture ONE macOS window and save it numbered in the shotlog folder.

    - name: short slug, e.g. "step1_install".
    - app / title_contains: pick the window (e.g. app="Terminal"). Empty = front-most window.
    - activity / command / result: caption stored in the manifest and used by export_report.
    """
    wins = _windows()
    if app:
        wins = [w for w in wins if app.lower() in w["app"].lower()]
    if title_contains:
        wins = [w for w in wins if title_contains.lower() in w["title"].lower()]
    if not wins:
        return {"error": "Window not found. Call list_windows to see what is available."}
    win = wins[0]
    path = store.next_path(name)
    r = subprocess.run(
        ["screencapture", "-x", "-o", f"-l{win['id']}", str(path)],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not path.exists() or path.stat().st_size == 0:
        return {
            "error": "screencapture failed. Grant 'Screen Recording' permission to your terminal/"
                     "MCP host in System Settings > Privacy & Security.",
            "detail": r.stderr.strip(),
        }
    entry = store.register(path, f"mac:{win['app']} — {win['title']}", activity, command, result)
    return {"path": str(path), **entry}


@mcp.tool()
def pull_remote_screenshots(
    host: str,
    user: str,
    remote_dir: str = "Pictures/Screenshots",
    prefix: str = "remote",
) -> dict:
    """Fetch new PNG screenshots from another machine over SCP (e.g. a Windows laptop where
    Win+PrtScn saves to Pictures\\Screenshots) and add them to the log.
    Requires an SSH server on that machine and key-based auth (no password prompt)."""
    tmp = store.base / "_remote_tmp"
    tmp.mkdir(exist_ok=True)
    r = subprocess.run(
        ["scp", "-p", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
         f"{user}@{host}:{remote_dir}/*.png", str(tmp)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        for f in tmp.glob("*.png"):
            f.unlink()
        if "No such file" in r.stderr or "no matches" in r.stderr.lower():
            return {"new": [], "total": 0, "note": f"No PNG files in {remote_dir}."}
        return {"error": "scp failed", "detail": r.stderr.strip()}

    known = {(e.get("source"), e.get("original"), e.get("original_size"))
             for e in store.load()}
    source = f"remote:{host}"
    new = []
    for f in sorted(tmp.glob("*.png"), key=lambda p: p.stat().st_mtime):
        size = str(f.stat().st_size)
        if (source, f.name, size) in known:
            f.unlink()
            continue
        dest = store.next_path(f"{prefix}_{f.stem}")
        f.rename(dest)
        store.register(dest, source, original=f.name, original_size=size)
        new.append(dest.name)
    return {"new": new, "total": len(new)}


@mcp.tool()
def update_caption(file: str, activity: str = "", command: str = "", result: str = "") -> dict:
    """Fill in or fix the caption (activity, command, result) of a saved screenshot."""
    entry = store.update(file, activity=activity, command=command, result=result)
    return entry or {"error": f"{file} is not in the manifest"}


@mcp.tool()
def list_screenshots() -> list[dict]:
    """List every logged screenshot with its caption, in order."""
    return store.load()


@mcp.tool()
def export_report(title: str = "Screenshots") -> dict:
    """Write report.md in the shotlog folder: every screenshot with its caption, in order.
    Convert it to PDF/DOCX with any tool (e.g. pandoc)."""
    return {"path": str(store.export_markdown(title))}


def main() -> None:
    if sys.platform != "darwin":
        sys.exit("shotlog-mcp captures windows with macOS APIs and only runs on macOS.")
    mcp.run()


if __name__ == "__main__":
    main()
