"""Agent Terminal Execution - Safe command execution for AI agents."""

import os
import subprocess
import shlex
import re
from typing import List, Dict, Any, Optional, Tuple
from rich.console import Console

console = Console()

# 允许执行的命令白名单
ALLOWED_COMMANDS = {
    "python", "python3", "pip", "pip3", "pytest", "ruff", "black", "flake8",
    "npm", "npx", "node", "yarn", "go", "make", "cmake", "gcc", "g++",
    "git", "curl", "wget", "docker", "docker-compose", "ls", "cat", "head",
    "tail", "grep", "find", "wc", "sort", "uniq", "awk", "sed", "echo",
    "touch", "mkdir", "cp", "mv", "rm", "chmod", "which", "uname", "env",
    "hermes", "rigor", "bash", "sh"
}

# 禁止的危险命令
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",          # rm -rf /
    r"dd\s+if=/dev/zero",     # dd destructive
    r"mkfs",                  # Format disk
    r"fdisk",                 # Partition disk
    r"sudo\s+reboot",         # Reboot
    r"shutdown",              # Shutdown
    r"curl.*\|\s*bash",       # Pipe curl to bash
    r"wget.*\|\s*sh",         # Pipe wget to sh
]


class AgentTerminal:
    """Secure terminal execution environment for AI agents."""
    
    def __init__(self, workdir: str = None, timeout: int = 300):
        self.workdir = workdir or os.getcwd()
        self.timeout = timeout
        
    def is_command_allowed(self, command: str) -> tuple[bool, str]:
        """Check if command is allowed."""
        if not command.strip():
            return False, "Empty command"
            
        # Check dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Extract base command
        parts = command.split()
        base_cmd = parts[0].lower()
        
        # Handle paths like /usr/bin/python
        base_cmd = os.path.basename(base_cmd)
        
        if base_cmd not in ALLOWED_COMMANDS:
            return False, f"Command '{base_cmd}' not in allowed list"
            
        return True, "OK"
    
    def execute(self, command: str, check: bool = False) -> Dict[str, Any]:
        """Execute a command securely."""
        allowed, reason = self.is_command_allowed(command)
        if not allowed:
            return {
                "success": False,
                "error": reason,
                "stdout": "",
                "stderr": f"BLOCKED: {reason}",
                "returncode": -1
            }
            
        try:
            # Use shell=False for security, split command properly
            cmd_parts = shlex.split(command)
            
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.workdir,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            )
            
            return {
                "success": result.returncode == 0,
                "error": result.stderr.strip() if result.returncode != 0 else "",
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {self.timeout}s",
                "stdout": "",
                "stderr": "TIMEOUT",
                "returncode": -1
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Command not found: {command.split()[0]}",
                "stdout": "",
                "stderr": "NOT_FOUND",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def install_dependencies(self, project_dir: str = None) -> Dict[str, Any]:
        """Auto-detect and install project dependencies."""
        workdir = project_dir or self.workdir
        results = []
        
        # Python dependencies
        if os.path.exists(os.path.join(workdir, "requirements.txt")):
            r = self.execute(f"pip install -r requirements.txt")
            results.append({"type": "python", "result": r})
            
        if os.path.exists(os.path.join(workdir, "setup.py")):
            r = self.execute("pip install -e .")
            results.append({"type": "python-setup", "result": r})
            
        # Node.js dependencies
        if os.path.exists(os.path.join(workdir, "package.json")):
            r = self.execute("npm install")
            results.append({"type": "node", "result": r})
            
        # Go dependencies
        if os.path.exists(os.path.join(workdir, "go.mod")):
            r = self.execute("go mod download")
            results.append({"type": "go", "result": r})
            
        return {
            "success": all(r["result"]["success"] for r in results),
            "results": results
        }
    
    def run_tests(self, project_dir: str = None, test_type: str = "auto") -> Dict[str, Any]:
        """Run tests based on project type."""
        workdir = project_dir or self.workdir
        
        if test_type == "auto":
            # Detect test framework
            if os.path.exists(os.path.join(workdir, "pytest.ini")) or \
               os.path.exists(os.path.join(workdir, "pyproject.toml")):
                test_type = "pytest"
            elif os.path.exists(os.path.join(workdir, "package.json")):
                test_type = "npm"
                
        if test_type == "pytest":
            return self.execute("pytest -v --tb=short")
        elif test_type == "npm":
            return self.execute("npm test")
        else:
            return {"success": False, "error": "No test framework detected"}
