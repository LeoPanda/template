# AI駆動システム開発手順書V2.1（5大エージェント協調・3大レビューゲート・WikiSkill自己進化ループ統合版）

本文書は、Antigravityプラグイン `system-dev-pipeline` (V2.1) における **メインエージェント（コンダクター）、4つの専門サブエージェント（architect, backend-engineer, ui-designer, qa-engineer）、および決定論的スキル群** が協調し、プロジェクト進行状態（`PROJECT_STATE.md`）を一元管理しながら、3大レビューゲートとWikiSkill型永続ナレッジ自己進化ループを運用してシステム開発およびシステム改訂を推進するための具体的な手順、役割分担、および投入プロンプトを定義するものである。

---

## 1. 前提条件とエージェント協調体制

### 1.1 前提条件
1. Antigravity環境において、プラグイン `system-dev-pipeline`（v2.1.0以上）が有効化されていること。
2. 新規開発を行うプロジェクト用ディレクトリ（例: `template/<プロジェクト名>`）をAntigravityで開いていること。

### 1.2 役割分担アーキテクチャ (5大エージェント協調モデル)
- 👑 **プロジェクトコンダクター (`conductor` / メインエージェント / Model: `pro` または `inherit`)**:
  - 全体進行統括、ユーザー対話、進行フェーズ（PHASE 1〜8）の厳格管理。
  - `PROJECT_STATE.md` の一元更新（**Single Writer 原則**）。
  - インフラ・Git専任コマンド実行: Git操作（`dev-git-init`, `dev-git-release`）、本番デプロイ、DB強制上書き（`dev-db-overwrite`）、Dockerコンテナ全体の起動・停止。
  - サブエージェント動的登録フォールバック（未登録エージェント検知時の `define_subagent` 自動登録）。
  - レビュー指摘提案Diffの適用およびコンテナ再ビルド確認。
  - PHASE 8 における知見・メトリクス統括（`wiki-proposer`, `wiki-compactor`, `dev-metrics-collector`）。
- 📐 **設計・立案スペシャリスト (`architect` / サブエージェント / Model: `pro`)**:
  - 要件定義（システム展開プロファイル Profile A〜D 選定）、3大基本設計書（技術・スキーマ・ロジック）作成。
  - ウォークスルー後のバックエンドAPI仕様書同期。
  - ※ **【二重防御ガードレール】いかなる場合も `run_command` を呼び出してはならない。**
  - ※ 推論エージェントとして Wiki 層は直接参照せず、蒸留された `SKILL.md` および `rules/` のみに基づいて設計する（Context Isolation）。
- 💻 **バックエンドエンジニア (`backend-engineer` / サブエージェント / Model: `pro`)**:
  - バックエンドAPI、データベースモデル・マイグレーション、ビジネスロジック実装、コードレビュー指摘是正。
  - ※ コマンド実行はバックエンド構文チェック・単体テスト（`uv run`, `python`, `pytest`, `ruff check` 等）に限定。Git/デプロイ/DB上書き/コンテナ起動停止は厳禁。
  - ※ Wiki 層は直接参照しない（Context Isolation）。
- 🎨 **UI/UXデザイナー / FE (`ui-designer` / サブエージェント / Model: `flash` または `pro`)**:
  - `画面仕様書.md` 作成、モダンフロントエンド画面・UIコンポーネント実装、UI微調整。
  - ※ **コンポーネント行数制限の厳守**: 1コンポーネントあたり300行以下。
  - ※ コマンド実行はパッケージ導入（`npm install` 等）およびUIローカルビルド（`npm run build` 等）に限定。Git/デプロイ禁止。Context Isolation。
- 🛡️ **品質・テスト & 監査・QAスペシャリスト (`qa-engineer` / サブエージェント / Model: `pro`)**:
  - 3大レビュー（基本設計レビュー `dev-review-arch`、コード品質レビュー `dev-review-code`、システム総合レビュー `dev-review-system`）の実施。
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
新規開発プロジェクトの初期ディレクトリ構造、`.env`、受皿領域（WikiLayer, Metrics）、ドキュメント雛形、および状態管理ファイル（`PROJECT_STATE.md`, `TEMPLATE_PROMOTIONS.md`）を自動展開・初期化します。

#### 投入プロンプト
```text
dev-phase1-setup スキルを実行し、本プロジェクトの環境初期化を行ってください。
```

#### 主な作成・配置物
- ディレクトリ: `./docs/`, `./docs/plans/`, `./docs/plans/scenario-test/`, `./docs/plans/metrics/`, `./wiki/patterns/local/`, `./wiki/patterns/universal/`, `./wiki/patterns/rejected/`, `./wiki/archive/`, `./metrics/turns/`, `./metrics/phases/`, `./rules/`
- 状態管理・台帳: `./PROJECT_STATE.md` (EXECUTION_MODE 記録), `./TEMPLATE_PROMOTIONS.md`, `./wiki/logs.md`, `./wiki/skill-impact.md`
- 設定ファイル: `.env`, `.gitignore` (`metrics/turns/` 自動除外追加), `<プロジェクト名>.code-workspace`
- ドキュメント雛形: `docs/要件定義書.md`, `docs/AI駆動システム開発手順書V2.1.md`, `docs/AI駆動システム開発フェーズ定義書V2.1.md`, `docs/APIキー安全管理・一元化設計書.md`, `docs/AI駆動ロギングシステム仕様書.md`, `rules/dev-process-standards.md`, `rules/システム改訂ルール.md`
- **Antigravity IDE GUI設定の案内** (`Settings → Projects → <プロジェクト名>` での推奨権限設定案内)

---

### 2.2 PHASE 2: 要件定義
👑 コンダクターが 📐 `architect` にタスクを委譲し、システム展開プロファイル（Profile A〜D）を選定の上、`docs/要件定義書.md` を精査・構造化します。

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
- 📐 `architect`: `技術要件定義書.md`, `テーブルスキーマ定義書.md`, `ビジネスロジック仕様書.md` 作成
- 🎨 `ui-designer`: `画面仕様書.md` 作成
- 🛡️ `qa-engineer`: `dev-doc-reviewer` による多次元クロスチェック・自動修復ループ（不整合0件）
- 🛡️ `qa-engineer`: `dev-review-arch` による基本設計レビューゲート（定常コア＋選定プロファイル別監査、`docs/plans/基本設計レビュー結果報告書.md` 生成）

#### 投入プロンプト
```text
dev-phase3-design スキルを実行し、基本設計書を作成した上でドキュメント相互の整合性チェックおよび基本設計レビューを行ってください。
```

#### 承認ゲート
- ドキュメント整合性エラー0件および基本設計レビュー判定 `PASS`（または `CONDITIONAL PASS`）を確認後、👑 コンダクターが主要設計判断を提示。
- **【承認ゲート】ユーザーが「基本設計書の内容を承認します」と明示指示**することで、👑 コンダクターが `PROJECT_STATE.md` を更新し PHASE 4 へ進みます。

---

### 2.4 PHASE 4: 開発環境とシステム構築
設計書に基づき、ローカル開発環境（Docker）の構築、BE/FEソースコード実装、Gitリポジトリ初期化を行います。
- 👑 コンダクター: Docker環境構築統括
- 💻 `backend-engineer`: バックエンドAPI、DBモデル・マイグレーション、ビジネスロジック実装
- 🎨 `ui-designer`: フロントエンド画面・UIコンポーネント実装（1ファイル300行以下）
- ⚙️ `dev-git-init`: Gitリポジトリ初期化 (`.gitignore` 包含、`main` 初回コミット、`feature` 作業ブランチ作成)

> [!IMPORTANT]
> **【徹底ルール】PHASE 4以降のシステム修正後のDockerコンテナ再構成**  
> 本フェーズ以降、プログラムコードや設定等を修正した後は、変更を確実にコンポーネントへ反映させるため、**必ず `docker compose down` および `docker compose up --build -d` を実行して Docker コンテナをビルド・再構成する**。

#### 投入プロンプト
```text
dev-phase4-env-build スキルを実行し、docs/配下の設計ドキュメントに基づいて開発環境構築とシステム実装を行ってください。
```

---

### 2.5 PHASE 5: ウォークスルー動作確認とデバッグ
実際の画面操作による動作検証、指摘不具合の修正、および最新コードを正としたAPI仕様書の同期を行います。
- 👤 ユーザー: 画面操作・機能疎通検証
- 👑 コンダクター: 不具合修正統括（💻 BE / 🎨 UI）、修正後のコンテナ再構成 (`docker compose down` → `up --build -d`)
- 📐 `architect`: 実装コードを正としたAPI仕様同期 (`docs/バックエンドAPI仕様書.md`)
- 🛡️ `qa-engineer`: ドキュメント整合性の再確認

#### 投入プロンプト
```text
dev-phase5-walkthrough スキルを実行し、設計ドキュメントのファイナライズと同期を行ってください。
```

#### 承認ゲート
- **【承認ゲート】ユーザーが「ウォークスルー動作確認を承認します」と明示指示**することで、PHASE 5.5 へ進みます。

---

### 2.6 PHASE 5.5: コード品質・整合性レビュー & リファクタリング
ウォークスルー完了直後、テストコード作成（PHASE 6）の前にコードのエントロピー（重複・乱雑さ）を除去し、品質を整流化します。
- 🛡️ `qa-engineer`: `dev-review-code` スキルを実行し、DRY原則、単一責任、デッドコード排除、型安全性、ファイル行数制限（全体400行以下、UI300行以下）を監査。`docs/plans/コード品質レビュー及びリファクタリング提案書.md` (Unified Diff付き) を作成。
- 💻 `backend-engineer` / 🎨 `ui-designer`: 提案Diffを反映し、コードを最適化。
- 👑 コンダクター: 修正後のコンテナ再ビルド・疎通確認。

#### 投入プロンプト
```text
dev-review-code スキルを実行し、実装コード全域の品質レビューとリファクタリング提案を行ってください。
```

#### 承認ゲート
- レビュー判定 `CLEAN` を確認後、**【承認ゲート】ユーザーが「コードリファクタリングを承認します」と明示指示**することで、PHASE 6 へ進みます。

---

### 2.7 PHASE 6: スルーテスト環境の構築と実施
🛡️ `qa-engineer` がシナリオテスト計画書を作成し、自動テストスクリプト構築、テスト自動実行、修復ループを実行します。
- 🛡️ `qa-engineer`: `docs/plans/シナリオテスト計画書.md` 作成、自動テスト実行・修復ループ（最大5回）。
- **Wiki Maintainer 連携 (RCA即時記録)**: テスト失敗や環境トラップが発生した場合、🛡️ `qa-engineer` が `wiki-maintainer` 手順に基づき根本原因分析を行い、プロジェクトローカルの `./wiki/patterns/` へ即時記録。
- **【二重防御ガードレール】自律修復の制限**:
  - 自律修復の対象は「テストスクリプト」および「テスト環境設定」に限定。
  - プログラムコード起因のエラーを発見した場合、🛡️ `qa-engineer` はコード本体を直接修正せず、原因調査結果とUnified Diff修正案をコンダクターへ報告。
- **修正後のコンテナ再構成**: 修正後は必ず `docker compose down` → `up --build -d` を実行。

#### 投入プロンプト
```text
dev-phase6-testing スキルを実行し、シナリオテスト計画書の作成と自動テスト修復ループを実行してください。
```

#### 承認ゲート
- テスト成功率100%を確認後、**【承認ゲート】ユーザーが「リリース準備移行を承認します」と明示指示**することで、PHASE 7 へ進みます。

---

### 2.8 PHASE 7: 本番リリース
本番環境（Cloud Run等）へ初回デプロイを行い、本番セキュリティ設定を検証します。
- 👑 コンダクター: `docs/plans/本番適用作業手順書.md` 作成
- 🛡️ `qa-engineer`: `dev-review-system` によるシステム総合レビューゲート（平文キー排除、セキュリティ境界、ロールバック計画、ヘルスチェック）、判定: `RELEASE APPROVED` 確認
- 👑 コンダクター: 本番デプロイ実行（コンダクター専任）
- 🛡️ `qa-engineer`: IAM / IAP / Cloud Run セキュリティ監査

#### 投入プロンプト
```text
dev-phase7-release スキルを実行し、システム総合レビューの実施、本番適用作業手順書の作成、リリース実行、および本番セキュリティ設定の検証を行ってください。
```

#### 承認ゲート
- **【承認ゲート】ユーザーが「本番稼働確認を承認します」と明示指示**することで、PHASE 8 へ進みます。

---

### 2.9 PHASE 8: ドキュメント改訂管理の開始と自己進化ループの実行
本番運用移行に伴う定量メトリクス集計、WikiSkill型自己進化サイクル、改訂運用ルール適用、およびGit本番リリースを実行します。

#### 実行手順
1. **定量メトリクス集計**: 👑 コンダクターが `dev-metrics-collector` を実行し、開発健全性サマリ（`docs/plans/metrics/development-metrics-summary.json`）および診断レポート（`metrics/system_health_report.md`）を出力。
2. **自己進化パッチ立案**: 👑 コンダクターが `wiki-proposer` を実行し、`wiki/patterns/universal/` から Tier 2 知見を抽出して `SKILL.md` の改善パッチおよび `PURPOSE.md` を起案。`./TEMPLATE_PROMOTIONS.md` に集約・提示。
3. **複合検証ゲート (Gating)**: 🛡️ `qa-engineer` が複合検証（静的解析0件、ドキュメント整合性0件、全テストパス、トークン効率上限内）を実行。
4. **Wiki統合・アーカイブ**: 👑 コンダクターが `wiki-compactor` を実行し、Wikiパターンの重複統合・アーカイブ退避を実施。
5. **【承認ゲート】知見昇格レビュー**: ユーザーが `./TEMPLATE_PROMOTIONS.md` を確認し、明示的承認を行う。
6. **知見昇格ルーティング**:
   - `GLOBAL_PLUGIN` モード: プロジェクトルートの `./promotions/` 配下に差分パッチ（`v2.1_universal_patterns.patch`）をエクスポート。
   - `LOCAL_STANDALONE` モード: プロジェクトローカルの `.agents/plugins/system-dev-pipeline/skills/` を直接更新。
7. **GitHub本番リリース**: ⚙️ `dev-git-release` により `feature` を `main` へ Squash Merge（`Release v1.0.0`）、Push、次期 `feature` ブランチを切り直し。
8. **改訂ルール適用**: ⚙️ `dev-phase8-rules` により `rules/システム改訂ルール.md` をプロジェクトに適用。
9. **ステータス更新**: 👑 コンダクターが `PROJECT_STATE.md` を `PRODUCTION_ACTIVE` へ更新。

#### 投入プロンプト
```text
dev-phase8-rules スキルを実行し、定量メトリクス集計、自己進化サイクル、知見昇格レビュー、およびシステム改訂ルールを適用してください。
```

---

## 3. 本番リリース後のシステム改訂プロセス（REVISION LIFECYCLE）

本番稼働（PHASE 8完了）以降の変更・機能追加・不具合修正は、以下の厳格な改訂ライフサイクルに従って実施します。

```
                         ┌─────────────────────────────────┐
                         │   👤 ユーザー: 改訂依頼開始宣言    │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │ 👑 コンダクター: 状態ファイル更新 │
                         │   (改訂依頼番号: n.m.xxx 採番)   │
                         └────────────────┬────────────────┘
                                          │
    ┌─────────────────────────────────────┴─────────────────────────────────────┐
    │ 🔄 改訂ターン (Revision Turn: 1〜N回繰り返し)                             │
    │                                                                           │
    │  1. ユーザー指示 ──► 2. Plan作成 (👑/📐) ──► 3. レビュー & 承認 (👤)      │
    │                                                     │                     │
    │  5. コード品質レビュー (🛡️ 差分対象) ◄── 4. 改訂実行 (💻 BE / 🎨 FE)      │
    │     (DRY/不要コード排除/Diff適用)                                          │
    │        │                                                                  │
    │        ├─► [手戻り・エラー発生時] 🛡️ QA: wiki/patterns/ へ即時記録 (RCA)  │
    │        ▼                                                                  │
    │  6. ドキュメント履歴追記 & 文書化 (/revise-log/) ────────────────────────┘
    └─────────────────────────────────────┬─────────────────────────────────────┘
                                          │
                                          ▼ ユーザー: 改訂ターン完了宣言
                         ┌─────────────────────────────────┐
                         │ 🛡️ QA: シナリオテスト実施       │
                         │   (修復時は wiki/patterns/ 記録)│
                         └────────────────┬────────────────┘
                                          │ PASS (明示的承認ゲート)
                                          ▼
                         ┌─────────────────────────────────┐
                         │ 🛡️ QA: システム総合レビュー     │
                         │   (RELEASE APPROVED 確認)       │
                         └────────────────┬────────────────┘
                                          │ 承認 (明示的承認ゲート)
                                          ▼
                         ┌─────────────────────────────────┐
                         │ 👑 コンダクター: 本番デプロイ     │
                         │ 👑 Vn.m改訂レポート作成          │
                         │ 👤 知見昇格レビュー              │
                         │ 🔄 WikiSkill自己進化サイクル実行 │
                         │    (Proposer 提案 ──► Gate 検証) │
                         │ ⚙️ dev-git-release 実行          │
                         │ 👑 PROJECT_STATE.md 更新完了    │
                         └─────────────────────────────────┘
```

---

## 4. 随時実行用ユーティリティプロンプト一覧

#### ドキュメント相互整合性チェック（🛡️ `qa-engineer` 主担当）
```text
dev-doc-reviewer スキルを実行し、docs/ 配下の全ドキュメント間の整合性を精査・修正してください。
```

#### コード品質レビュー（🛡️ `qa-engineer` 主担当）
```text
dev-review-code スキルを実行し、ソースコード全域の品質監査とリファクタリングDiffを提示してください。
```

#### システム総合レビュー（🛡️ `qa-engineer` 主担当）
```text
dev-review-system スキルを実行し、本番リリースに向けたセキュリティ・耐障害性・ロールバック監査を行ってください。
```

#### Wikiナレッジの整理・アーカイブ（👑 コンダクター主担当）
```text
wiki-compactor スキルを実行し、wiki/patterns/ 配下の重複パターンの統合および陳腐化パターンのアーカイブ退避を行ってください。
```

#### 定量メトリクス集計・レポート生成（👑 コンダクター主担当）
```text
dev-metrics-collector スキルを実行し、開発定量メトリクスを集計してシステム健全性レポートを生成してください。
```

#### 本番適用後のデータベース上書き・再デプロイ（👑 コンダクター主担当）
```text
dev-db-overwrite スキルを実行し、データベースを含む開発環境のコンテナを本番環境へデプロイしてください。
```
