"""Patch Generator: Analyzes errors and generates code fixes.

Uses deterministic rules + LLM templates to create targeted patches.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict, Optional


class ErrorParser:
    """Parses test/CI error output to extract file paths, line numbers, and error descriptions."""

    PATTERNS = [
        re.compile(r"(.*?):(\d+):\d+:\s*(.*(?:\n.*?){0,2})"),  # ruff/eslint
        re.compile(r"File \"(.*?)\", line (\d+)(.*)"),         # python traceback
        re.compile(r"FAILED (.*?::)(.*?)(?: - (.+))?"),        # pytest
    ]

    @classmethod
    def parse(cls, error_output: str) -> List[Dict]:
        """Extract file error locations and descriptions."""
        issues = []
        for line in error_output.split("\n"):
            line = line.strip()
            if not line:
                continue

            for pattern in cls.PATTERNS:
                match = pattern.search(line)
                if match:
                    groups = match.groups()
                    filepath = groups[0].strip().replace("::", "/").replace(".py:", ".py")
                    try:
                        lineno = int(groups[1])
                    except ValueError:
                        continue
                    msg = groups[2].strip() if len(groups) > 2 else ""
                    
                    if any(filepath.endswith(ext) for ext in (".py", ".js", ".ts", ".go", ".rs", ".java")):
                        issues.append({
                            "file": filepath,
                            "line": lineno,
                            "message": msg,
                            "raw_line": line,
                        })
                    break
        return issues


class PatchGenerator:
    """Generates code patches to fix identified issues."""

    def __init__(self, file_ops):
        self.file_ops = file_ops

    def generate_patch(self, filepath: str, line: int, error_msg: str) -> Optional[str]:
        """Generate a patch for a specific error."""
        # 1. Deterministic fixes
        det_patch = self._deterministic_fix(filepath, line, error_msg)
        if det_patch:
            return det_patch

        # 2. LLM-based fix (requires external API)
        return self._llm_generate_patch(filepath, line, error_msg)

    def _deterministic_fix(self, filepath: str, line: int, error_msg: str) -> Optional[str]:
        """Apply rule-based fixes for common errors."""
        error_lower = error_msg.lower()

        # Import errors -> suggest import
        name_match = re.search(r"name '(\w+)' is not defined", error_msg)
        if name_match:
            name = name_match.group(1)
            common_imports = {
                "os": "import os", "json": "import json", "re": "import re",
                "Path": "from pathlib import Path", "datetime": "from datetime import datetime",
                "typing": "from typing import List, Dict, Optional",
                "subprocess": "import subprocess", "asyncio": "import asyncio",
            }
            if name in common_imports:
                return common_imports[name]

        # F-string syntax error (Python < 3.12)
        if "f-string" in error_lower and "single" in error_lower:
            return "# Tip: Upgrade to Python 3.12+ or use .format() instead of nested f-strings"

        return None

    def _llm_generate_patch(self, filepath: str, line: int, error_msg: str) -> Optional[str]:
        """
        Placeholder for LLM-based patch generation.
        
        To implement:
        1. Read context around the error line.
        2. Construct prompt: "Fix the error in this code: ..."
        3. Call LLM API.
        4. Return the fixed code block.
        """
        # TODO: Integrate with LLM provider
        return None
