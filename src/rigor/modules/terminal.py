"""Agent Terminal Execution - Safe command execution for AI agents."""

import os
import re
import secrets
import shlex
import subprocess
import time
from typing import Any

from rich.console import Console

console = Console()

# 允许执行的命令白名单。保持保守：网络、shell、删除和容器控制命令不默认开放。
ALLOWED_COMMANDS = {
    "python",
    "python3",
    "pip",
    "pip3",
    "pytest",
    "ruff",
    "black",
    "flake8",
    "npm",
    "npx",
    "node",
    "yarn",
    "go",
    "make",
    "cmake",
    "gcc",
    "g++",
    "git",
    "ls",
    "cat",
    "head",
    "tail",
    "grep",
    "find",
    "wc",
    "sort",
    "uniq",
    "awk",
    "sed",
    "echo",
    "touch",
    "mkdir",
    "which",
    "uname",
    "env",
    "hermes",
    "rigor",
}

# 禁止的危险命令
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",  # rm -rf /
    r"dd\s+if=/dev/zero",  # dd destructive
    r"mkfs",  # Format disk
    r"fdisk",  # Partition disk
    r"sudo\s+reboot",  # Reboot
    r"shutdown",  # Shutdown
    r"curl.*\|\s*bash",  # Pipe curl to bash
    r"wget.*\|\s*sh",  # Pipe wget to sh
]

BLOCKED_ARGUMENTS = {
    "python": {"-c"},
    "python3": {"-c"},
    "find": {"-exec", "-delete"},
    "git": {"reset", "clean", "checkout", "switch", "restore", "push"},
}


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

        try:
            parts = shlex.split(command)
        except ValueError as e:
            return False, f"Invalid command syntax: {e}"

        if not parts:
            return False, "Empty command"

        # Extract base command
        base_cmd = parts[0].lower()

        # Handle paths like /usr/bin/python
        base_cmd = os.path.basename(base_cmd)

        if base_cmd not in ALLOWED_COMMANDS:
            return False, f"Command '{base_cmd}' not in allowed list"

        blocked = BLOCKED_ARGUMENTS.get(base_cmd, set())
        if any(part in blocked for part in parts[1:]):
            return False, f"Command '{base_cmd}' contains blocked argument"

        return True, "OK"

    def execute(self, command: str, check: bool = False) -> dict[str, Any]:
        """Execute a command securely."""
        allowed, reason = self.is_command_allowed(command)
        if not allowed:
            return {"success": False, "error": reason, "stdout": "", "stderr": f"BLOCKED: {reason}", "returncode": -1}

        try:
            # Use shell=False for security, split command properly
            cmd_parts = shlex.split(command)

            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.workdir,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )

            return {
                "success": result.returncode == 0,
                "error": result.stderr.strip() if result.returncode != 0 else "",
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {self.timeout}s",
                "stdout": "",
                "stderr": "TIMEOUT",
                "returncode": -1,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Command not found: {command.split()[0]}",
                "stdout": "",
                "stderr": "NOT_FOUND",
                "returncode": -1,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "stdout": "", "stderr": str(e), "returncode": -1}

    def install_dependencies(self, project_dir: str = None) -> dict[str, Any]:
        """Auto-detect and install project dependencies."""
        workdir = project_dir or self.workdir
        results = []

        # Python dependencies
        if os.path.exists(os.path.join(workdir, "requirements.txt")):
            r = self.execute("pip install -r requirements.txt")
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

        return {"success": all(r["result"]["success"] for r in results), "results": results}

    def run_tests(self, project_dir: str = None, test_type: str = "auto") -> dict[str, Any]:
        """Run tests based on project type."""
        workdir = project_dir or self.workdir

        if test_type == "auto":
            if os.path.exists(os.path.join(workdir, "pytest.ini")) or os.path.exists(
                os.path.join(workdir, "pyproject.toml")
            ):
                test_type = "pytest"
            elif os.path.exists(os.path.join(workdir, "package.json")):
                test_type = "npm"

        if test_type == "pytest":
            return self.execute("pytest -v --tb=short")
        elif test_type == "npm":
            return self.execute("npm test")
        else:
            return {"success": False, "error": "No test framework detected"}

    # =========================================================
    # 自主环境配置 (Autonomous Environment Configuration)
    # =========================================================

    def setup_environment(self, project_dir: str = None) -> list[dict[str, Any]]:
        """Execute the full 5-layer environment setup sequence."""
        workdir = project_dir or self.workdir
        results = []

        # Layer 1: Dependencies (Already implemented, reuse)
        console.print("[cyan]📦 [Layer 1] 正在安装项目依赖...[/]")
        dep_res = self.install_dependencies(workdir)
        results.append({"layer": "dependencies", "result": dep_res})

        # Layer 2: System Dependencies
        console.print("[cyan]🔧 [Layer 2] 正在检查系统依赖...[/]")
        sys_res = self.check_system_deps(workdir)
        results.append({"layer": "system_deps", "result": sys_res})

        # Layer 3: Environment Variables
        console.print("[cyan]🔑 [Layer 3] 正在配置环境变量...[/]")
        env_res = self.setup_env_vars(workdir)
        results.append({"layer": "env_vars", "result": env_res})

        # Layer 4: Database Initialization
        console.print("[cyan]🗄️ [Layer 4] 正在初始化数据库...[/]")
        db_res = self.setup_database(workdir)
        results.append({"layer": "database", "result": db_res})

        return results

    def check_system_deps(self, project_dir: str = None) -> dict[str, Any]:
        """Layer 2: Detect and install common system-level binaries."""
        workdir = project_dir or self.workdir
        # Heuristic: Look for usage of specific tools in code or config
        required_tools = []

        # Check for Docker
        if os.path.exists(os.path.join(workdir, "Dockerfile")):
            required_tools.append("docker")
            required_tools.append("docker-compose")  # or docker compose

        # Check for ffmpeg (audio/video processing)
        # (Simplified: just checking common needs for now)

        missing = []
        for tool in required_tools:
            if not self._command_exists(tool):
                missing.append(tool)

        if missing:
            return {
                "success": False,
                "error": f"Missing system tools: {', '.join(missing)}. Please install manually.",
                "suggestion": f"Try: sudo apt-get install {' '.join(missing)}",
            }
        return {"success": True, "message": "All system dependencies found"}

    def _command_exists(self, cmd):
        try:
            subprocess.run(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    def setup_env_vars(self, project_dir: str = None) -> dict[str, Any]:
        """Layer 3: Generate .env file from .env.example or common patterns."""
        workdir = project_dir or self.workdir
        env_file = os.path.join(workdir, ".env")
        example_file = os.path.join(workdir, ".env.example")

        if os.path.exists(env_file):
            return {"success": True, "message": ".env already exists, skipping."}

        env_vars = {}

        if os.path.exists(example_file):
            with open(example_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        if val == "" or "placeholder" in val.lower() or "changeme" in val.lower():
                            env_vars[key] = self._generate_secret(key)
                        else:
                            env_vars[key] = val

        # Heuristic: If no .env.example, generate common defaults
        if not env_vars:
            env_vars["DATABASE_URL"] = "sqlite:///./data.db"
            env_vars["SECRET_KEY"] = secrets.token_urlsafe(32)
            env_vars["DEBUG"] = "True"

        with open(env_file, "w") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")

        return {"success": True, "message": f".env created with {len(env_vars)} variables."}

    def _generate_secret(self, key: str) -> str:
        if "KEY" in key.upper() or "SECRET" in key.upper() or "TOKEN" in key.upper():
            return secrets.token_urlsafe(32)
        if "URL" in key.upper():
            return "sqlite:///./data.db"
        return "changeme"

    def setup_database(self, project_dir: str = None) -> dict[str, Any]:
        """Layer 4: Run DB migrations automatically."""
        workdir = project_dir or self.workdir
        results = []

        # Django
        if os.path.exists(os.path.join(workdir, "manage.py")):
            r = self.execute("python manage.py migrate --no-input")
            results.append({"framework": "django", "result": r})

        # SQLAlchemy / Alembic
        elif os.path.exists(os.path.join(workdir, "alembic.ini")):
            r = self.execute("alembic upgrade head")
            results.append({"framework": "alembic", "result": r})

        # Node.js (Prisma)
        elif os.path.exists(os.path.join(workdir, "prisma", "schema.prisma")):
            r = self.execute("npx prisma migrate deploy")
            results.append({"framework": "prisma", "result": r})

        # Node.js (Sequelize/Knex) - check package.json scripts
        elif os.path.exists(os.path.join(workdir, "package.json")):
            import json

            with open(os.path.join(workdir, "package.json")) as f:
                pkg = json.load(f)
            scripts = pkg.get("scripts", {})
            if "db:migrate" in scripts:
                r = self.execute("npm run db:migrate")
                results.append({"framework": "npm-script", "result": r})

        return {"success": all(r["result"].get("success", False) for r in results), "details": results}

    def start_service(self, project_dir: str = None, port: int = None) -> dict[str, Any]:
        """Layer 5: Detect framework and start the service + health check."""
        workdir = project_dir or self.workdir

        # Detect Framework
        start_cmd = None

        if os.path.exists(os.path.join(workdir, "manage.py")):
            start_cmd = "python manage.py runserver"
        elif os.path.exists(os.path.join(workdir, "app/main.py")) or os.path.exists(
            os.path.join(workdir, "src/main.py")
        ):
            # FastAPI/Flask usually in main.py
            if (
                "uvicorn" in open(os.path.join(workdir, "requirements.txt")).read()
                if os.path.exists(os.path.join(workdir, "requirements.txt"))
                else False
            ):
                start_cmd = "uvicorn app.main:app --reload"
        elif os.path.exists(os.path.join(workdir, "package.json")):
            import json

            with open(os.path.join(workdir, "package.json")) as f:
                pkg = json.load(f)
            scripts = pkg.get("scripts", {})
            if "start" in scripts:
                start_cmd = "npm start"
            elif "dev" in scripts:
                start_cmd = "npm run dev"

        if not start_cmd:
            return {"success": False, "error": "Could not detect service start command."}

        # Start service in background (simulated via simple execution for now)
        # Note: For real background, we'd use subprocess.Popen and store the PID
        console.print(f"[cyan]🚀 Starting service: {start_cmd}[/]")
        try:
            proc = subprocess.Popen(shlex.split(start_cmd), cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Give it some time to boot
            time.sleep(5)

            # Check if process is still running
            if proc.poll() is None:
                return {"success": True, "message": f"Service started (PID: {proc.pid})", "pid": proc.pid}
            else:
                _, stderr = proc.communicate()
                return {"success": False, "error": f"Service failed to start: {stderr.decode()}"}

        except Exception as e:
            return {"success": False, "error": str(e)}
