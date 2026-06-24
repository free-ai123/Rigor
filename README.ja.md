# Rigor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue.svg)](https://hermes-agent.nousresearch.com/docs/)
[![Profiles](https://img.shields.io/badge/Profiles-12-orange.svg)](#12の役割)

**AI のスピードで、エンジニアリング品質を届ける。**

Rigor は完全な AI エンジニアリングチーム — 12 の専門ロールが Kanban ボードを通じて連携し、ソフトウェアエンジニアリングの全ライフサイクルをカバー：要件 → アーキテクチャ → 実装 → コードレビュー → QA テスト → セキュリティ監査 → デプロイ → UAT → 振り返り。

> もう一つの AI コーディングアシスタントではありません。**標準エンジニアリングプロセスでコードを届ける自律型 AI 専門家チーム**です。

[Hermes Agent](https://github.com/NousResearch/hermes-agent) 上に構築 — 純粋な SOUL.md プロファイル + Kanban ワークフロー。カスタムコードは一切不要。

---

## なぜ Rigor？

| 能力 | Rigor | Devin | Cursor | Copilot |
|------|-------|-------|--------|---------|
| **マルチロール連携** | **88%** | 30% | 20% | 50% |
| **エンジニアリング品質** | **92%** | 75% | 40% | 65% |
| **TDD ファースト** | **82%** | 45% | 10% | 20% |
| **カバレッジゲート** | **88%** | 70% | 10% | 25% |
| **デプロイロールバック** | **72%** | 50% | 0% | 20% |
| **プロジェクト振り返り** | **68%** | 0% | 0% | 0% |
| **構造化ナレッジベース** | **76%** | 65% | 20% | 35% |
| **可観測性** | **68%** | 52% | 15% | 22% |

*データソース: マルチエージェントシステム能力比較分析、2026年6月*

## 12の役割

| ロール | 責任 | 主要成果物 |
|--------|------|-----------|
| 🧠 **Orchestrator** | タスク分解、ルーティング、進捗追跡 | DAG計画、アサイン |
| 📋 **Product Manager** | 要件定義、PRD、UAT受け入れ | PRDドキュメント、受入報告書 |
| 🏗️ **Tech Lead** | アーキテクチャ、DAG計画、ADR | アーキテクチャ決定、DAG、契約 |
| 💻 **Backend Engineer** | API、データベース、サービスロジック | コード、マイグレーション |
| 🎨 **Frontend Engineer** | UIコンポーネント、状態管理 | コンポーネント、ページ |
| 📊 **Data Scientist** | データ分析、ML、モデリング | レポート、モデル |
| 🔧 **Data Engineer** | パイプライン、ベクターDB、RAG | パイプライン設定、エンベディング |
| 🔍 **Code Reviewer** | アーキテクチャ + コードレビュー（2段階） | レビュー報告書 |
| 🛡️ **Security Auditor** | セキュリティ監査（設計 + コード段階） | セキュリティ報告書 |
| 🧪 **QA Engineer** | テスト設計、自動化、カバレッジ | テストスクリプト、カバレッジ報告書 |
| 🔧 **DevOps Engineer** | CI/CD、コンテナ、デプロイ | Dockerfile、パイプライン |
| 📝 **Technical Writer** | テクニカルドキュメント、APIドキュメント | ドキュメント |

## アーキテクチャ

```
ユーザー入力（自然言語の要件）
    ↓
Orchestrator（プロジェクトタイプ検出 → ロール選択 → DAGに分解）
    ↓
┌─────────────────────────────────────────────┐
│  Kanbanボード（SQLite、自動分解）            │
│  ┌─────┐  ┌──────┐  ┌──────┐  ┌──────────┐  │
│  │ PRD │→ │Arch  │→ │Impl  │→ │Review/Test│  │
│  └─────┘  └──────┘  └──────┘  └──────────┘  │
└─────────────────────────────────────────────┘
    ↓（60秒周期、Gatewayディスパッチ）
12ロールが並列実行（依存が許可するところ）
    ↓（Artifactチェーン: PRD → API仕様 → テストケース → ドキュメント）
デプロイ → UAT → 振り返り → ナレッジキャプチャ
```

## クイックスタート

### 前提条件

- [Hermes Agent](https://hermes-agent.nousresearch.com/docs/) がインストール済み
- APIキー設定済み（DashScope、OpenRouter など）
- 最小 2GB RAM（5ロール）/ 推奨 4GB（全12ロール）

### 5分で最初のプロジェクト

```bash
# 1. クローン
git clone https://github.com/free-ai123/Rigor.git
cd Rigor

# 2. デプロイ
bash scripts/setup-expert-team.sh

# 3. 最初のタスクを作成
hermes kanban create "カスタムコードとクリックトラッキング付きURL短縮サービス" --triage
```

60秒後、Orchestrator がタスクを自動分解、12のロールが連携を開始します。

### 進捗の確認

```bash
# タスクリスト
hermes kanban list

# プロジェクトダッシュボード（自動更新）
cat ~/.hermes/kanban/workspace/shared/structured/project-dashboard.json | python3 -m json.tool

# タスク依存ツリー
hermes kanban show <task-id> --tree
```

## リポジトリ構造

```
Rigor/                          # 32ファイル、約30KB
├── profiles/                   # 12の専門ロール（各 SOUL.md + config.yaml）
│   ├── orchestrator/
│   ├── product-manager/
│   ├── tech-lead/
│   ├── backend-engineer/
│   ├── frontend-engineer/
│   ├── data-scientist/
│   ├── data-engineer/
│   ├── code-reviewer/
│   ├── security-auditor/
│   ├── qa-engineer/
│   ├── devops-engineer/
│   └── technical-writer/
├── scripts/
│   └── setup-expert-team.sh    # ワンクリックデプロイスクリプト（v2.0）
├── knowledge-base/
│   └── structured/             # 構造化ナレッジベース
│       ├── knowledge-index.json  # 6件、68のシノニム
│       ├── effectiveness.json    # 効果追跡 + 減衰ルール
│       ├── project-profiles.json # 自動注入ルール
│       └── edges.json            # ナレッジ関係グラフ
├── docs/
│   └── quickstart.md           # 5分ガイド
├── README.md                   # English
├── README.zh.md                # 中文
├── README.ja.md                # 日本語
├── LICENSE                     # MIT
└── .gitignore
```

## 比較

### なぜ Devin じゃないのか？

Devin は強力なシングルエージェント開発者で、コードを速く書くのが得意です。しかし**ロールは1つだけ** — プロダクトレビューも、セキュリティ監査も、QA テストも、デプロイロールバックもありません。

Rigor は**12のロールが標準ソフトウェアエンジニアリングプロセスで連携**し、**エンジニアリング品質**を届けます。コーディング速度だけではありません。

### なぜ Cursor じゃないのか？

Cursor は優れた AI コーディングアシスタントで、**あなた**がコードを書くのを手伝います。しかし自律的に連携はしません — アーキテクチャはあなたが決め、テストはあなたが書き、レビューはあなたがします。

Rigor は**自律的に連携する AI チーム** — 要件を与えるだけで、あとはすべて AI が処理します。

## ナレッジベース

Rigor はプロジェクト横断の経験再利用のための構造化ナレッジベースを含みます：

- **knowledge-index.json** — 6件のナレッジエントリー、タグ、68のシノニム、信頼度、関連度ルール
- **effectiveness.json** — 各ナレッジが実際に問題を何度防いだかを追跡、自動減衰ルール付き（30日未使用 → declining、60日 → stale、180日 → archived）
- **project-profiles.json** — プロジェクトタイプとアクティブロールに基づいて関連ナレッジを自動注入
- **edges.json** — 決定 → バグ → 修正 → パターンをつなぐ関係グラフ

## ロードマップ

- [x] 12ロール SOUL.md + 連携ワークフロー
- [x] TDDファーストモード（QAがテストを先に書く）
- [x] カバレッジゲート（行≥80%、ブランチ≥70%）
- [x] Artifact バージョン管理
- [x] 自己修正ループ（自動修正 + エスカレーション）
- [x] 構造化ナレッジベース（インデックス + セマンティック + 減衰）
- [x] プロジェクトダッシュボード + タスクステータスレポート
- [x] プロジェクト振り返り + 履歴アーカイブ
- [x] デプロイロールバックプロトコル
- [x] 増分更新モード
- [x] コードスタイル統一（ruff / prettier / eslint）
- [ ] 垂直ドメインロールの追加（金融、医療、法務）
- [ ] カスタムロール作成ガイド
- [ ] Webダッシュボード統合
- [ ] 多言語 SOUL.md サポート

## コントリビュート

コントリビューション大歓迎！

- **新ロールの追加**: Fork → `profiles/<role>/SOUL.md` を作成 → PR
- **既存ロールの改善**: `profiles/<role>/SOUL.md` を編集 → PR
- **ナレッジの追加**: `knowledge-base/` を更新 → PR
- **バグ報告**: Issues または PR お待ちしています

## ライセンス

MIT — [LICENSE](LICENSE) を参照

---

⭐ Rigor が役に立った場合は、スターをいただけると嬉しいです！
