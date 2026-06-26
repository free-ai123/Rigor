"""RAG Knowledge Engine — 基于 SQLite FTS5 的轻量级语义/全文检索。"""

import os
import glob
import re
import sqlite3
from typing import List, Dict, Any, Optional
from rich.console import Console

console = Console()


class KnowledgeEngine:
    """
    基于 Obsidian 知识库 (Markdown 文件) 的全文搜索引擎。
    使用 SQLite FTS5，零额外依赖，纯 Python + SQLite。
    """
    
    def __init__(self, vault_path: str = None, db_path: str = None):
        self.vault_path = vault_path or os.path.join(os.path.dirname(__file__), "../../rigor-knowledge")
        self.db_path = db_path or os.path.expanduser("~/.hermes/rigor-knowledge.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """初始化 FTS5 表结构。"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                title, content, path, category,
                tokenize='trigram'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_meta (
                path TEXT PRIMARY KEY,
                title TEXT,
                category TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def index_vault(self) -> Dict[str, Any]:
        """索引整个知识库目录。"""
        if not os.path.exists(self.vault_path):
            return {"success": False, "error": f"Vault path not found: {self.vault_path}"}
            
        # Find all Markdown files
        md_files = glob.glob(os.path.join(self.vault_path, "**/*.md"), recursive=True)
        
        # Filter out hidden dirs and templates
        md_files = [f for f in md_files if "/99-" not in f and "/00-" not in f]
        
        indexed_count = 0
        skipped_count = 0
        
        cursor = self.conn.cursor()
        
        for filepath in md_files:
            try:
                # Check if already indexed
                cursor.execute("SELECT 1 FROM knowledge_meta WHERE path = ?", (filepath,))
                if cursor.fetchone():
                    skipped_count += 1
                    continue
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract title from first heading or filename
                title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else os.path.splitext(os.path.basename(filepath))[0]
                
                # Extract category from path
                parts = filepath.replace(self.vault_path, '').strip('/').split('/')
                category = parts[0] if len(parts) > 1 else "root"
                
                # Insert into FTS5
                cursor.execute("""
                    INSERT INTO knowledge_fts (title, content, path, category)
                    VALUES (?, ?, ?, ?)
                """, (title, content, filepath, category))
                
                # Insert meta
                cursor.execute("""
                    INSERT INTO knowledge_meta (path, title, category)
                    VALUES (?, ?, ?)
                """, (filepath, title, category))
                
                indexed_count += 1
                
            except Exception as e:
                console.print(f"[yellow]⚠️  Failed to index {filepath}: {e}[/]")
                continue
        
        self.conn.commit()
        
        console.print(f"[green]✅ 知识库索引完成: {indexed_count} 新文件, {skipped_count} 已存在[/]")
        
        return {
            "success": True,
            "indexed": indexed_count,
            "skipped": skipped_count,
            "total": len(md_files),
        }

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """全文 + 语义搜索知识库。"""
        
        if not os.path.exists(self.vault_path):
            return []
            
        # Auto-index if empty
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge_meta")
        if cursor.fetchone()[0] == 0:
            self.index_vault()
            
        try:
            # FTS5 search
            cursor.execute("""
                SELECT title, content, path, category, rank
                FROM knowledge_fts
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, n_results))
            
            rows = cursor.fetchall()
            
            formatted = []
            for row in rows:
                content_preview = row["content"][:300] + "..." if len(row["content"]) > 300 else row["content"]
                formatted.append({
                    "title": row["title"],
                    "path": row["path"],
                    "category": row["category"],
                    "rank": row["rank"],
                    "content_preview": content_preview,
                })
                
            return formatted
            
        except Exception as e:
            console.print(f"[red]Search Error: {e}[/]")
            # Fallback: simple LIKE search
            return self._fallback_search(query, n_results)

    def _fallback_search(self, query: str, n_results: int) -> List[Dict[str, Any]]:
        """FTS5 失败时的回退方案。"""
        cursor = self.conn.cursor()
        terms = query.split()
        like_clause = " OR ".join([f"content LIKE ?" for _ in terms])
        params = [f"%{t}%" for t in terms] + [n_results]
        
        cursor.execute(f"""
            SELECT title, content, path, category
            FROM knowledge_fts
            WHERE {like_clause}
            LIMIT ?
        """, params)
        
        formatted = []
        for row in cursor.fetchall():
            content_preview = row["content"][:300] + "..." if len(row["content"]) > 300 else row["content"]
            formatted.append({
                "title": row["title"],
                "path": row["path"],
                "category": row["category"],
                "rank": 0,
                "content_preview": content_preview,
            })
        return formatted

    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息。"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge_meta")
            count = cursor.fetchone()[0]
            return {
                "success": True,
                "total_documents": count,
                "db_path": self.db_path,
                "vault_path": self.vault_path,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def close(self):
        self.conn.close()
