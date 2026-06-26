"""Auto-Fix Loop — 当 CI 失败或测试报错时自动创建修复任务。"""

import os
import json
import subprocess
import sqlite3
from typing import Optional, Dict, Any
from rich.console import Console
from datetime import datetime

console = Console()


class AutoFixEngine:
    """当检测到 CI 失败或 Agent 终端执行失败时，自动创建修复任务。"""
    
    def __init__(self, hermes_home: str = None):
        self.hermes_home = hermes_home or os.getenv("HERMES_HOME", os.path.expanduser("~/.hermes"))
        self.kanban_db = os.path.join(self.hermes_home, "kanban", "board.db")

    def create_fix_task_from_ci(
        self,
        repo: str,
        pr_number: int,
        pr_url: str,
        ci_error: str,
        ci_platform: str = "github",
    ) -> Dict[str, Any]:
        """当 CI 失败时自动创建修复任务。"""
        
        task_title = f"[Auto-Fix] 修复 {repo} PR #{pr_number} 的 CI 失败"
        
        description = f"""## CI 失败报告

- **来源**: {ci_platform}
- **仓库**: {repo}
- **PR**: #{pr_number} ({pr_url})
- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 错误详情
```
{ci_error}
```

## 修复指引
1. 检查 PR #{pr_number} 的变更文件
2. 定位导致 CI 失败的原因（测试失败 / 代码风格 / 构建错误）
3. 修复代码并推送
4. 标记本任务完成
"""
        
        return self._create_kanban_task(
            title=task_title,
            description=description,
            assignee="backend-engineer",  # 默认分配给后端，可根据错误类型调整
            priority="high",
            labels=["auto-fix", "ci-failed"],
            metadata={
                "fix_type": "ci_failed",
                "repo": repo,
                "pr_number": pr_number,
                "pr_url": pr_url,
                "ci_platform": ci_platform,
            }
        )

    def create_fix_task_from_terminal(
        self,
        original_task_id: str,
        command: str,
        error_output: str,
    ) -> Dict[str, Any]:
        """当 Agent 终端执行报错时自动创建修复任务。"""
        
        task_title = f"[Auto-Fix] 修复命令执行失败: {command[:50]}..."
        
        description = f"""## 终端执行失败报告

- **触发任务**: {original_task_id}
- **命令**: `{command}`
- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 错误输出
```
{error_output}
```

## 修复指引
1. 分析错误原因
2. 修正命令或修复代码缺陷
3. 重新执行验证
"""
        
        return self._create_kanban_task(
            title=task_title,
            description=description,
            assignee="backend-engineer",
            priority="high",
            labels=["auto-fix", "terminal-error"],
            metadata={
                "fix_type": "terminal_failed",
                "original_task_id": original_task_id,
                "command": command,
            }
        )

    def _create_kanban_task(
        self,
        title: str,
        description: str,
        assignee: str,
        priority: str,
        labels: list,
        metadata: dict,
    ) -> Dict[str, Any]:
        """向 Hermes Kanban 数据库插入新任务。"""
        
        if not os.path.exists(self.kanban_db):
            console.print(f"[red]❌ Kanban 数据库不存在: {self.kanban_db}[/]")
            return {"success": False, "error": "Kanban DB not found"}
            
        try:
            conn = sqlite3.connect(self.kanban_db)
            cursor = conn.cursor()
            
            # Check if tasks table exists and create if needed
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'todo',
                        assignee TEXT,
                        priority TEXT DEFAULT 'medium',
                        labels TEXT DEFAULT '[]',
                        metadata TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            cursor.execute("""
                INSERT INTO tasks (title, description, status, assignee, priority, labels, metadata)
                VALUES (?, ?, 'todo', ?, ?, ?, ?)
            """, (
                title,
                description,
                assignee,
                priority,
                json.dumps(labels),
                json.dumps(metadata),
            ))
            
            conn.commit()
            task_id = cursor.lastrowid
            conn.close()
            
            console.print(f"[green]✅ 自动修复任务已创建: #{task_id} - {title}[/]")
            console.print(f"   分配给: {assignee} | 优先级: {priority}")
            
            return {
                "success": True,
                "task_id": task_id,
                "title": title,
                "assignee": assignee,
                "priority": priority,
            }
            
        except Exception as e:
            console.print(f"[red]❌ 创建修复任务失败: {e}[/]")
            return {"success": False, "error": str(e)}
