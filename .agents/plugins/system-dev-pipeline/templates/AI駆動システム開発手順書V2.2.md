# AI駆動システム開発手順書 V2.2（Shift-Left & 静的スケルトン・モック制御統合版）

本文書は、Antigravityプラグイン `system-dev-pipeline` (V2.2) における **メインエージェント（コンダクター）、4つの専門サブエージェント（architect, backend-engineer, ui-designer, qa-engineer）、および決定論的スキル群** が協調し、プロジェクト進行状態（`PROJECT_STATE.md`）を一元管理しながら、2層プロファイル体系（定常コア8項目＋Profile A〜D）、静的スケルトン展開、3大レビューゲート、およびWikiSkill型永続ナレッジ自己進化ループを運用してシステム開発およびシステム改訂を推進するための具体的な手順、役割分担、および投入プロンプトを定義するものである。

---

## 1. 前提条件とエージェント協調体制

### 1.1 前提条件
1. Antigravity環境において、プラグイン `system-dev-pipeline`（v2.2.0以上）が有効化されていること。
2. 新規開発を行うプロジェクト用ディレクトリ（例: `template/<プロジェクト名>`）をAntigravityで開いていること。

### 1.2 役割分担アーキテクチャ (5大エージェント協調モデル)
- 👑 **プロジェクトコンダクター (`conductor` / メインエージェント / Model: `pro` または `inherit`)**:
  - 全体進行統括、ユーザー対話、進行フェーズ（PHASE 1〜8）の厳格管理。
  - **静的スケルトン（`skeletons/`）の初期展開**および `.env` モック環境変数初期化統括。
  - `PROJECT_STATE.md` の一元更新（**Single Writer 原則**）。
  - インフラ・Git専任コマンド実行: Git操作（`dev-git-init`, `dev-git-release`）、本番デプロイ、DB強制上書き（`dev-db-overwrite`）、Dockerコンテナ全体の起動・停止。
  - **標準コマンドシーケンスの統括実行**:
    - `alembic revision --autogenerate`, `alembic upgrade head`, `npm run codegen:types`, コミット前CI同等ローカル検証。
  - サブエージェント動的登録フォールバック（未登録エージェント検知時の `define_subagent` 自動登録）。
  - レビュー指摘提案Diffの適用およびコンテナ再ビルド確認。
  - PHASE 8 における知見・メトリクス統括（`wiki-proposer`, `wiki-compactor`, `dev-metrics-collector`）。
- 📐 **設計・立案スペシャリスト (`architect` / サブエージェント / Model: `pro`)**:
  - **2層プロファイル体系の設計義務化**: 要件定義（ディシジョンツリーによる Profile A〜D 選定）、4大基本設計書（技術・スキーマ・ロジック・画面）作成。
  - 外部API二重キャッシュ戦略、モックアップ制御仕様（案C＋案A）、Alembic前提スキーマ（Aware UTC, `user_id` 拡張性）の設計。
  - ウォークスルー後のバックエンドAPI仕様書同期。
  - ※ **【二重防御ガードレール】いかなる場合も `run_command` を呼び出してはならない。**
  - ※ 推論エージェントとして Wiki 層は直接参照せず、蒸留された `SKILL.md` および `rules/` のみに基づいて設計する（Context Isolation）。
- 💻 **バックエンドエンジニア (`backend-engineer` / サブエージェント / Model: `pro`)**:
  - バックエンドAPI、SQLAlchemyモデル、Alembicマイグレーション、ビジネスロジック実装、コードレビュー指摘是正。
  - **生SQL手動DDLの絶対禁止**、IAP JWT署名二重検証ミドルウェア（`auth.py`）実装、内部監視エンドポイント（`health.py`, `litestream.py`）実装。
  - ※ コマンド実行はバックエンド構文チェック・単体テスト（`uv run`, `python`, `pytest`, `ruff check` 等）に限定。Git/デプロイ/DB上書き/コンテナ起動停止は厳禁。
  - ※ Wiki 層は直接参照しない（Context Isolation）。
- 🎨 **UI/UXデザイナー / FE (`ui-designer` / サブエージェント / Model: `flash` または `pro`)**:
  - `画面仕様書.md` 作成（グランドデザイン新規格準拠）、モダンフロントエンド画面・UIコンポーネント実装、UI微調整。
  - ※ **Anti-God Component の徹底**: **1ファイル最大250行制限**、Custom Hooks/Servicesへの物理分離。
  - ※ **コンポーネント内直書きモックの原則禁止**: MSWハンドラー（`src/mocks/handlers.ts`）構築と環境変数（`VITE_ENABLE_MOCK`）切替の徹底。
  - ※ コマンド実行はパッケージ導入（`npm install` 等）およびUIローカルビルド（`npm run build` 等）に限定。Git/デプロイ禁止。Context Isolation。
- 🛡️ **品質・テスト & 監査・QAスペシャリスト (`qa-engineer` / サブエージェント / Model: `pro`)**:
  - 2層構造 3大レビューの厳格監査:
    - 基本設計レビュー (`dev-review-arch`): 定常コア8項目 ＋ 展開プロファイル別適合監査。
    - コード品質レビュー (`dev-review-code`): **1ファイル最大250行制限の機械的検査**、**直書きモック検出・排除**、型同期検証。
    - システム総合レビュー (`dev-review-system`): **本番モックOFF二重防御**、**IAP JWT署名検証有効化**、**Alembic起動時マイグレーション保証**、平文排除。
  - ドキュメント多次元整合性監査（`dev-doc-reviewer`、最大5回ループ、除外パスの遵守）。
  - スルーテスト計画策定・自動実行ループ（最大5回ループ）。
  - **Wiki Maintainer 責務**: レビュー不合格・テスト失敗・自律修復時の根本原因分析 (RCA) とローカル `./wiki/patterns/` への即時記録。
  - Gating Tester 責務: スキル改修パッチに対する複合検証ゲート（4大関門）の実行。
  - ※ **【コード直接改変禁止】** システム本体のプログラムコードに不具合を発見した場合は勝手に修正せず、原因調査結果とUnified Diff案をコンダクターへ報告する。
- ⚙️ **決定論的スキル群 (`system-dev-pipeline`)**:
  - フェーズ進行: `dev-phase1-setup` 〜 `dev-phase8-rules`
  - レビューゲート: `dev-review-arch`, `dev-review-code`, `dev-review-system`
  - ナレッジ & メトリクス: `wiki-maintainer`, `wiki-proposer`, `wiki-compactor`, `dev-metrics-collector`
  - インフラ & Git: `dev-git-init`, `dev-git-release`, `dev-db-overwrite`

---

## 2. 開発フェーズと実行手順 (PHASE 1〜8)

### 2.1 PHASE 1: プロジェクトの準備
新規開発プロジェクトの初期ディレクトリ構造、**静的スケルトン（`skeletons/common/`, `skeletons/profile-a/`）**、`.env`（`VITE_ENABLE_MOCK=true` 含む）、受皿領域（WikiLayer, Metrics）、ドキュメント雛形、および状態管理ファイル（`PROJECT_STATE.md`, `TEMPLATE_PROMOTIONS.md`）を自動展開・初期化します。

#### 投入プロンプト
```text
dev-phase1-setup スキルを実行し、本プロジェクトの環境初期化を行ってください。
```

#### 主な作成・配置物
- スケルトン展開: `./docker/`, `./backend/`, `./frontend/` (Profile A スケルトン初期配置)
- ディレクトリ: `./docs/`, `./docs/plans/`, `./docs/plans/scenario-test/`, `./docs/plans/metrics/`, `./wiki/patterns/local/`, `./wiki/patterns/universal/`, `./wiki/patterns/rejected/`, `./wiki/archive/`, `./metrics/turns/`, `./metrics/phases/`, `./rules/`
- 状態管理・台帳: `./PROJECT_STATE.md` (2層プロファイル・MOCK_MODE 記録), `./TEMPLATE_PROMOTIONS.md`, `./wiki/logs.md`, `./wiki/skill-impact.md`
- 設定ファイル: `.env` (`VITE_ENABLE_MOCK=true`), `.gitignore` (`wiki/`, `metrics/` 自動除外追加), `<プロジェクト名>.code-workspace`
- ドキュメント雛形: `docs/要件定義書.md`, `docs/AI駆動システム開発手順書V2.2.md`, `docs/AI駆動システム開発フェーズ定義書V2.2.md`, `docs/APIキー安全管理・一元化設計書.md`, `docs/AI駆動ロギングシステム仕様書.md`, `rules/AGENTS.md`, `rules/システム改訂ルール.md`
- **Antigravity IDE GUI設定の案内** (`Settings → Projects → <プロジェクト名>` での推奨権限設定案内)

---

### 2.2 PHASE 2: 要件定義
👑 コンダクターが 📐 `architect` にタスクを委譲し、2層構造プロファイル選定ディシジョンツリーに基づきプロファイル（Profile A〜D）を選定の上、定常コア8項目の非機能要件を自動バインドし、`docs/要件定義書.md` を精査・構造化します。

#### 投入プロンプト
```text
dev-phase2-requirements スキルを実行し、docs/要件定義書.md を精査して要件定義書の清書と詳細化を行ってください。
```

#### 承認ゲート
- 📐 `architect` の完了サマリと未決事項（Open Questions）を 👑 コンダクターが確認し、ユーザーへ提示します。
- **【承認ゲート】ユーザーが「要件定義書の内容を承認します」と明示指示**することで、👑 コンダクターが `PROJECT_STATE.md` を更新し PHASE 3 へ進みます。

---

### 2.3 PHASE 3: 基本設計書の作成と基本設計レビュー
要件定義書に基づき、基本設計書4種を作成し、ドキュメント整合性チェックおよび基本設計レビューゲートを実施します。
- 📐 `architect`: `技術要件定義書.md` (Profile A/D標準構成・250行制限・型同期明記), `テーブルスキーマ定義書.md` (Alembic前提・Aware UTC・`user_id` 拡張性), `ビジネスロジック仕様書.md` (外部API二重キャッシュ・モック制御仕様・内部監視エンドポイント) 作成
- 🎨 `ui-designer`: `画面仕様書.md` (グランドデザイン新規格準拠・HEX/px絶対値併記・ウィンドウ形態選定・Anti-God Component・直書きモック禁止) 作成
- 🛡️ `qa-engineer`: `dev-doc-reviewer` による多次元クロスチェック・自動修復ループ（不整合0件）
- 🛡️ `qa-engineer`: `dev-review-arch` による基本設計レビューゲート（定常コア8項目 ＋ 選定プロファイル別監査、`docs/plans/基本設計レビュー結果報告書.md` 生成）

#### 投入プロンプト
```text
dev-phase3-design スキルを実行し、基本設計書を作成した上でドキュメント相互の整合性チェックおよび基本設計レビューを行ってください。
```

#### 承認ゲート
- ドキュメント整合性エラー0件および基本設計レビュー判定 `PASS`（または `CONDITIONAL PASS`）を確認後、👑 コンダクターが主要設計判断を提示。
- **【承認ゲート】ユーザーが「基本設計書の内容を承認します」と明示指示**することで、👑 コンダクターが `PROJECT_STATE.md` を更新し PHASE 4 へ進みます。

---

### 2.4 PHASE 4: 開発環境とシステム構築
初期スケルトンを土台として、バックエンドとフロントエンドを完全分離して並行委譲実装し、Git初期化および標準コマンドシーケンスを自動実行します。
- 👑 コンダクター: Docker環境構築統括、Git初期化 (`dev-git-init`)
- 💻 `backend-engineer`: SQLAlchemyモデル定義、FastAPIルーター実装、IAP JWT署名検証ミドルウェア実装、内部監視エンドポイント実装
- 🎨 `ui-designer`: 業務UIコンポーネント実装 (**1ファイル最大250行制限**、Hooks/Services分離)、MSWハンドラー構築 (**直書きモック排除**)
- 👑 コンダクター: **標準コマンドシーケンス自動実行**:
  1. `docker compose exec backend alembic revision --autogenerate -m "Initial schema"`
  2. `docker compose exec backend alembic upgrade head`
  3. `docker compose exec frontend npm run codegen:types`
  4. コミット前CI同等ローカル検証 (`ruff check`, `pytest`, `npm run lint`, `npm run type-check`)
  5. コンテナ初回ビルド・疎通確認 (`docker compose up --build -d`)

#### 投入プロンプト
```text
dev-phase4-env-build スキルを実行し、開発環境およびシステム構築を進めてください。
```

---

### 2.5 PHASE 5: ウォークスルー動作確認とデバッグ
ユーザーによる画面操作・機能検証を実施し、**モック透過切替検証 (`VITE_ENABLE_MOCK=true/false`)** を行った上で不具合修正とAPI同期を行います。
- 👤 ユーザー: 画面操作・検証
- 👑 コンダクター: モック有効（MSW）と実API結合（FastAPI+SQLite）の透過切替検証
- 👑 コンダクター: 指摘不具合修正統括（BE: `backend-engineer`, FE: `ui-designer`）
- 📐 `architect`: 最新コードを正としたAPI仕様同期 (`docs/バックエンドAPI仕様書.md`)

#### 投入プロンプト
```text
dev-phase5-walkthrough スキルを実行し、ウォークスルー動作確認とモック透過切替検証を行ってください。
```

#### 承認ゲート
- **【承認ゲート】ユーザーが「ウォークスルー完了を承認します」と明示指示**することで、👑 コンダクターが `PROJECT_STATE.md` を更新し PHASE 5.5 へ進みます。

---

### 2.6 PHASE 5.5: コード品質・整合性レビュー & リファクタリング
🛡️ `qa-engineer` が全実装コードの品質・整合性を批判的に監査します。
- **監査項目**:
  - **1ファイル最大250行制限の機械的検査**
  - **コンポーネント内直書きモックの機械的検出・完全排除確認**
  - `codegen:types` による型定義同期検証
  - DRY原則・単一責任原則（SRP）・デッドコード排除
- 🛡️ `qa-engineer`: `docs/plans/コード品質レビュー及びリファクタリング提案書.md` (Unified Diff付き) 作成
- 💻 BE / 🎨 UI: 提案Diff反映・コード修正
- 👑 コンダクター: コンテナ再ビルド・疎通確認

#### 投入プロンプト
```text
dev-review-code スキルを実行し、コード品質レビューおよびリファクタリング提案を行ってください。
```

---

### 2.7 PHASE 6: スルーテスト環境の構築と実施
🛡️ `qa-engineer` がモック有効/無効双方での結合テストシナリオを策定し、自動テスト実行・ログ解析・修復ループを実行します。
- 🛡️ `qa-engineer`: `docs/plans/シナリオテスト計画書.md` 作成
- 🛡️ `qa-engineer`: 自動テスト実行・自律修復ループ (成功率100%達成まで最大5回反復)
- 🛡️ `qa-engineer`: Wiki Maintainer によるエラー根本原因（RCA）記録 (`wiki/patterns/`)

#### 投入プロンプト
```text
dev-phase6-testing スキルを実行し、シナリオテスト環境の構築と自動テストを実行してください。
```

#### 承認ゲート
- テスト成功率100%達成を確認後、**【承認ゲート】ユーザーが「リリース準備への移行を承認します」と明示指示**することで PHASE 7 へ進みます。

---

### 2.8 PHASE 7: 本番リリース
システム総合レビューゲートを通過した上で、本番適用作業手順書を作成し、本番デプロイを実行・検証します。
- 🛡️ `qa-engineer`: `dev-review-system` システム総合レビュー実行:
  - **本番用 `VITE_ENABLE_MOCK=false` 二重防御検証**
  - **IAP JWT 署名検証ミドルウェア有効化検証**
  - **`entrypoint.sh` による起動時 Alembic マイグレーション実行保証**
  - **Litestream レプリケーション設定および監視エンドポイント検証**
  - 平文シークレット完全排除、非root実行、ロールバック手順の完全性
- 👑 コンダクター: `docs/plans/本番適用作業手順書.md` 作成
- 👑 コンダクター: 本番環境（Cloud Run等）デプロイ実行
- 🛡️ `qa-engineer`: IAM / IAP セキュリティ設定監査

#### 投入プロンプト
```text
dev-phase7-release スキルを実行し、本番適用作業手順書の作成および本番デプロイ検証を行ってください。
```

#### 承認ゲート
- **【承認ゲート】ユーザーが「本番稼働確認を承認します」と明示指示**することで PHASE 8 へ進みます。

---

### 2.9 PHASE 8: ドキュメント改訂管理・自己進化の開始
定量メトリクス集計、WikiSkill自己進化ループ実行、Git本番リリース、および改訂運用ルールの適用を行います。
- 👑 コンダクター: 定量メトリクス集計 (`dev-metrics-collector`)
- 👑 コンダクター: `wiki-proposer` によるスキル改修案立案 & `PURPOSE.md` 生成
- 🛡️ `qa-engineer`: 複合検証ゲート実行 (判定: Adopted / Rejected)
- 👑 コンダクター: `wiki-compactor` によるWiki整理・枝刈り
- **【承認ゲート】ユーザーによる知見昇格レビュー承認 (./TEMPLATE_PROMOTIONS.md)**
- 👑 コンダクター: EXECUTION_MODE に応じた知見昇格実行 (パッチ出力 or プラグイン直接反映)
- ⚙️ `dev-git-release`: `feature` を `main` へ Squash Merge (`Release v1.0.0`)、Push、次期 `feature` 切り直し
- ⚙️ `dev-phase8-rules`: 改訂運用ルールファイル群の配置
- 👑 コンダクター: ステータスを `PRODUCTION_ACTIVE` へ移行
