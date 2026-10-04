---
name: dev-phase1-setup
description: "新規システム開発プロジェクトの環境初期化を行うスキル。ディレクトリ構造、.env、PROJECT_STATE.md、TEMPLATE_PROMOTIONS.md、<プロジェクトフォルダ名>.code-workspace、docs配下の各種ドキュメント雛形を自動生成・配置する。"
---

# PHASE 1: プロジェクト初期化指示

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`)
- **副担当**: なし (メインエージェント直接実行)

新規アプリケーション開発プロジェクトの環境初期化を以下の手順に従って自動実行してください。

## 1. ディレクトリ構造の作成

プロジェクトルートに以下のディレクトリを作成してください。

- `./docs/`
- `./docs/plans/`
- `./rules/`

## 2. 環境変数設定（.env）の配置

プラグインの `templates/.env.template` を読み込み、プロジェクトルートに `.env` を作成・保存してください。

## 3. プロジェクト状態管理および知見昇格バッファの初期化

プラグインのテンプレートからプロジェクトルート直下に以下のファイルを展開・初期化してください。

1. `templates/PROJECT_STATE.md.template` → `./PROJECT_STATE.md`
   - `{{PROJECT_NAME}}`: プロジェクトディレクトリ名
   - `{{APP_VERSION}}`: `1.0.0`
   - `{{UPDATED_AT}}`: 現在日時 (JST)
2. `templates/TEMPLATE_PROMOTIONS.md.template` → `./TEMPLATE_PROMOTIONS.md`

## 4. IDE 設定（<プロジェクトフォルダ名>.code-workspace）の配置

プラグインの `templates/code-workspace.template` を読み込み、プロジェクトルートに `<プロジェクトフォルダ名>.code-workspace`（ファイル名はプロジェクトフォルダと同じ名前にし、拡張子を `.code-workspace` とする）を作成・保存してください。

## 5. ドキュメント雛形のコピーと初期化

プラグイン内の `templates/` から以下のファイルを `docs/` ディレクトリにコピーしてください。

- `AI駆動システム開発手順書V2.md`
- `AI駆動システム開発フェーズ定義書.md`
- `要件定義書.md`
- `APIキー安全管理・一元化設計書.md`
- `AI駆動ロギングシステム仕様書.md`

## 6. Antigravity IDE/CLI 設定の案内

Antigravityのセキュリティ管理画面（`Settings → Projects → <本プロジェクト名>`）にて、以下の推奨設定および Permission Grants（アクセス権限）を手動で設定いただく必要がある旨を提示・案内してください。

### 推奨設定 (`Settings → Projects → <本プロジェクト名>`)

- `fileAccessPolicy`: `AGENT_SETTING_POLICY_ASK`
- `sandboxMode`: `true`
- `autoExecutionPolicy`: `CASCADE_COMMANDS_AUTO_EXECUTION_EAGER`
- `artifactReviewMode`: `ARTIFACT_REVIEW_MODE_ALWAYS`

### Permission Grants

- `read_file`: `<プロジェクトルートパス>`, `~/.gemini`
- `write_file`: `<プロジェクトルートパス>`

## 7. 状態更新と完了報告

1. `PROJECT_STATE.md` の PHASE 1 のチェックボックスを更新し、ステータスを `PHASE_2_REQUIREMENTS` へ進めてください。
2. 作成・配置したファイル一覧およびAntigravity設定チェックリストを表示し、PHASE 2（要件定義）に進む準備が完了したことをユーザーに報告してください。
