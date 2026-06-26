"""Safe file operations for AI agents — read, write, search, patch."""

from __future__ import annotations

import os
import re
import subprocess
import difflib
from pathlib import Path
from typing import List, Optional, Tuple


class FileOps:
    """
    Safe file operations with workspace sandboxing.
    All operations are constrained to `workspace_root`.
    """

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    def _safe_path(self, path: str) -> Path:
        """Resolve and validate that path is within workspace."""
        resolved = (self.workspace_root / path).resolve()
        if not str(resolved).startswith(str(self.workspace_root)):
            raise PermissionError(f"Path '{path}' is outside workspace")
        return resolved

    def read_file(self, path: str, offset: int = 1, limit: int = 500) -> str:
        """Read file content with pagination."""
        p = self._safe_path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not p.is_file():
            raise IsADirectoryError(f"Not a file: {path}")

        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        start = max(0, offset - 1)
        end = start + limit if limit > 0 else len(lines)
        content = "".join(lines[start:end])

        header = f"// Lines {start + 1}-{min(end, len(lines))} of {len(lines)}\n"
        return header + content

    def write_file(self, path: str, content: str) -> str:
        """Write content to file, creating parent dirs as needed."""
        p = self._safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written: {path} ({len(content)} bytes)"

    def search_files(
        self, pattern: str, target: str = "content", path: str = ".", file_glob: Optional[str] = None, limit: int = 50
    ) -> List[str]:
        """Search file contents or find files by glob."""
        root = self._safe_path(path)

        if target == "files":
            # Find files by glob
            matches = list(root.rglob(file_glob or pattern))
            return [str(m.relative_to(self.workspace_root)) for m in matches[:limit]]

        # Search content with regex
        results = []
        rglob_pattern = file_glob or "**/*"
        for p in root.rglob(rglob_pattern):
            if not p.is_file():
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(content.split("\n"), 1):
                    if re.search(pattern, line):
                        results.append(f"{p.relative_to(self.workspace_root)}:{i}: {line.strip()}")
                        if len(results) >= limit:
                            break
            except Exception:
                continue
            if len(results) >= limit:
                break

        return results

    def patch_file(self, path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
        """Targeted find-and-replace in a file."""
        p = self._safe_path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = p.read_text(encoding="utf-8")

        if old_string not in content:
            # Try fuzzy match
            lines_old = old_string.strip().split("\n")
            lines_content = content.split("\n")
            for i in range(len(lines_content) - len(lines_old) + 1):
                block = "\n".join(lines_content[i:i + len(lines_old)])
                # Simple similarity check
                if len(lines_old) > 2:
                    import difflib
                    ratio = difflib.SequenceMatcher(None, old_string.strip(), block.strip()).ratio()
                    if ratio > 0.8:
                        old_string = block
                        break

        if old_string not in content:
            raise ValueError(f"String not found in {path}")

        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)

        p.write_text(new_content, encoding="utf-8")
        return f"Patch applied: {path}"

    def list_dir(self, path: str = ".", max_depth: int = 2) -> List[str]:
        """List directory contents."""
        p = self._safe_path(path)
        results = []
        self._walk_dir(p, "", results, 0, max_depth)
        return results

    def _walk_dir(self, current: Path, prefix: str, results: list, depth: int, max_depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(current.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return

        for entry in entries:
            if entry.name.startswith((".", "__pycache__", "node_modules", ".git")):
                continue
            rel = f"{prefix}{entry.name}"
            if entry.is_dir():
                results.append(f"📁 {rel}/")
                self._walk_dir(entry, f"{rel}/", results, depth + 1, max_depth)
            else:
                size = entry.stat().st_size
                size_str = f"{size}" if size < 1024 else f"{size // 1024}K"
                results.append(f"  📄 {rel} ({size_str})")
