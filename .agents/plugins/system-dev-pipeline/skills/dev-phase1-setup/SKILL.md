---
name: dev-phase1-setup
description: "新規システム開発プロジェクトの環境初期化を行うスキル。ディレクトリ構造、Wiki層受皿、メトリクス受皿、.env、PROJECT_STATE.md (EXECUTION_MODE記録)、TEMPLATE_PROMOTIONS.md、.code-workspace、docs配下の各種ドキュメント雛形を自動生成・配置する。"
---

# PHASE 1: プロジェクト初期化指示

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`)
- **副担当**: なし (メインエージェント直接実行)

新規アプリケーション開発プロジェクトの環境初期化を以下の手順に従って自動実行してください。

---

## 1. ディレクトリ構造および受皿の自動生成

プロジェクトルートに以下のディレクトリ群を作成してください。

### (1) ドキュメント・計画・ルール領域
- `./docs/`
- `./docs/plans/`
- `./docs/plans/scenario-test/`
- `./docs/plans/metrics/`
- `./rules/`

### (2) WikiLayer 受皿領域（ナレッジ蓄積層）
- `./wiki/patterns/local/` (Tier 1: プロジェクト固有仕様)
- `./wiki/patterns/universal/` (Tier 2: 全体共通知見)
- `./wiki/patterns/rejected/` (検証不合格知見)
- `./wiki/archive/` (陳腐化パターンのアーカイブ)

### (3) 定量メトリクス領域
- `./metrics/turns/` (ターン別一次データ)
- `./metrics/phases/` (フェーズ別集計データ)

---

## 2. `.gitignore` の自動設定・追記

プロジェクトルートの `.gitignore` を確認し、以下の一次データ領域が存在しない場合は追記してください：
```gitignore
# Antigravity Metrics Raw Turns
metrics/turns/
```

---

## 3. テンプレート参照パスの動的フォールバック解決と動作モード判定

テンプレート配置形態を以下の優先順位で動的に探索・解決します：
1. **ローカル探索**: `./.agents/plugins/system-dev-pipeline/templates/` が存在するか確認。
   - 存在する場合: `EXECUTION_MODE` を `LOCAL_STANDALONE` と判定。
2. **グローバル探索**: 上記が存在しない場合、`~/.gemini/config/plugins/system-dev-pipeline/templates/` を探索。
   - 存在する場合: `EXECUTION_MODE` を `GLOBAL_PLUGIN` と判定。

テンプレートの読み込み元パスを `TEMPLATE_DIR` として特定します。

---

## 4. 環境変数設定（.env）の配置

`TEMPLATE_DIR/.env.template` を読み込み、プロジェクトルートに `.env` を作成・保存してください。

---

## 5. プロジェクト状態管理および台帳の初期化

### (1) `PROJECT_STATE.md` の展開
`TEMPLATE_DIR/PROJECT_STATE.md.template` を読み込み、プロジェクトルート直下に `./PROJECT_STATE.md` を展開します。
- `{{PROJECT_NAME}}`: プロジェクトディレクトリ名
- `{{APP_VERSION}}`: `1.0.0`
- `{{UPDATED_AT}}`: 現在日時 (JST)
- `{{EXECUTION_MODE}}`: 判定された `LOCAL_STANDALONE` または `GLOBAL_PLUGIN`

### (2) `TEMPLATE_PROMOTIONS.md` の展開
`TEMPLATE_DIR/TEMPLATE_PROMOTIONS.md.template` を読み込み、プロジェクトルート直下に `./TEMPLATE_PROMOTIONS.md` を作成・保存します。

### (3) Wiki 台帳の初期化
以下の初期台帳ファイルを `./wiki/` 配下に作成・配置します（未存在時）：
- `./wiki/logs.md`:
  ```markdown
  # Wiki Pattern & Revision Logs

  | 日時 | パターンID | 分類 | 契機 | 概要 | 状態 |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  ```
- `./wiki/skill-impact.md`:
  ```markdown
  # Skill & Knowledge Impact Map

  | パターンID | 影響スキル / ファイル | 改善種別 | 効果測定 / メトリクス寄与 |
  | :--- | :--- | :--- | :--- |
  ```

---

## 6. IDE 設定（<プロジェクトフォルダ名>.code-workspace）の配置

`TEMPLATE_DIR/code-workspace.template` を読み込み、プロジェクトルートに `<プロジェクトフォルダ名>.code-workspace` を作成・保存してください。

---

## 7. ドキュメント雛形のコピーと初期化

`TEMPLATE_DIR` から以下のファイルを `docs/` ディレクトリにコピーしてください。
- `AI駆動システム開発手順書V2.1.md`
- `AI駆動システム開発フェーズ定義書V2.1.md`
- `要件定義書.md`
- `APIキー安全管理・一元化設計書.md`
- `AI駆動ロギングシステム仕様書.md`

また、開発ルールファイルを `TEMPLATE_DIR/../rules/`（またはグローバル）から `./rules/` へコピーしてください：
- `rules/dev-process-standards.md`
- `rules/システム改訂ルール.md` (テンプレートからコピー)

---

## 8. Antigravity IDE/CLI 設定の案内

Antigravityのセキュリティ管理画面（`Settings → Projects → <本プロジェクト名>`）にて、以下の推奨設定を手動設定いただく旨を案内してください：
- `fileAccessPolicy`: `AGENT_SETTING_POLICY_ASK`
- `sandboxMode`: `true`
- `autoExecutionPolicy`: `CASCADE_COMMANDS_AUTO_EXECUTION_EAGER`
- `artifactReviewMode`: `ARTIFACT_REVIEW_MODE_ALWAYS`

---

## 9. 状態更新と完了報告

1. `PROJECT_STATE.md` の PHASE 1 を完了に更新し、ステータスを `PHASE_2_REQUIREMENTS` へ進めてください。
2. 作成・配置したファイル一覧および動作モード（`EXECUTION_MODE`）を表示し、PHASE 2（要件定義）に進む準備が完了したことをユーザーに報告してください。
