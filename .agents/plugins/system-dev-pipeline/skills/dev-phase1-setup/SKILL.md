---
name: dev-phase1-setup
description: "新規システム開発プロジェクトの環境初期化を行うスキル。Central Knowledge Hub未処理原票検知、静的スケルトン基盤展開、ディレクトリ構造、Wiki層・メトリクス受皿、.env、PROJECT_STATE.md、TEMPLATE_PROMOTIONS.md、docs配下の各種ドキュメント雛形を自動生成・配置する。"
---

# PHASE 1: プロジェクト初期化指示 V2.3

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`)
- **連携エージェント**: 🛡️ `qa-engineer`（Knowledge Hub 未処理原票の監査時）

新規アプリケーション開発プロジェクトの環境初期化を以下の手順に従って自動実行してください。

---

## 1. テンプレート・スケルトン参照パスの解決と動作モード判定
以下の優先順位でプラグイン資産を探索し、`EXECUTION_MODE` を決定します：
1. **ローカル探索**: `./.agents/plugins/system-dev-pipeline/` が存在する場合 ➔ `EXECUTION_MODE=LOCAL_STANDALONE`（`PLUGIN_DIR=./.agents/plugins/system-dev-pipeline`）。
2. **グローバル探索**: `~/.gemini/config/plugins/system-dev-pipeline/` が存在する場合 ➔ `EXECUTION_MODE=GLOBAL_PLUGIN`（`PLUGIN_DIR=~/.gemini/config/plugins/system-dev-pipeline`）。
3. いずれも存在しない場合は環境エラーとして処理を停止し、プラグイン配置をユーザーに促します。

---

## 2. Central Knowledge Hub の初期化と未処理原票の起動時検知 (V2.3)
1. `bash "${PLUGIN_DIR}/scripts/pipeline-reconciler.sh" --init-hub` および `--status` を実行し、`~/.gemini/knowledge-hub/` の状態を診断します。
2. `inbox/` または `pending_approval/` に未反映・裁定待ちの知見原票（`CLAIM-*.md` / `REVIEW-*.md`）が存在する場合：
   - ユーザーへ未処理原票の存在をアラートし、必要に応じて 🛡️ `qa-engineer` による3段階意味的監査を実行した上で、**`ask_question` モーダル**で即時承認・裁定を行います。
   - 承認された原票は `pipeline-reconciler.sh --activate-claim <CLAIM>` により `overlay/LOCAL_FEEDBACK_RULES.md` へクリーン再生成反映し、本プロジェクトの PHASE 2 以降から即座に有効化します。

---

## 3. ディレクトリ構造および `.gitignore` の自動設定
1. **ディレクトリ作成**:
   - ドキュメント・計画・ルール: `./docs/`, `./docs/plans/`, `./docs/plans/scenario-test/`, `./docs/plans/metrics/`, `./rules/`
   - Spoke Wiki 受皿: `./wiki/patterns/local/`, `./wiki/patterns/universal/`, `./wiki/patterns/rejected/`, `./wiki/archive/`
   - メトリクス・原票控え: `./metrics/turns/`, `./metrics/phases/`, `./promotions/`
2. **`.gitignore` の確認・追記**:
   ```gitignore
   # Knowledge, Promotions & Metrics
   wiki/
   metrics/
   promotions/

   # Environment & Secrets
   .env
   *.pem
   *.key
   *.db
   ```

---

## 4. 静的スケルトン層（`skeletons/`）と `.env` の自動展開 (Shift-Left)
1. `PLUGIN_DIR/skeletons/common/`（`.github/workflows/ci.yml`, `.editorconfig`）をプロジェクトルートへコピーします。
2. 選定プロファイルに応じたスケルトン基盤を展開します（未存在時）：
   - **Profile A (ゴールデンパス)**: `skeletons/profile-a/`（`docker/`, `backend/`, `frontend/`）をコピーし、`chmod +x docker/entrypoint.sh` を付与。
   - **Profile D (ローカルデスクトップ型)**: `skeletons/profile-d/`（`src-tauri/`, `docker/`, `backend/`, `frontend/`）をコピー。
3. `PLUGIN_DIR/templates/.env.template`（またはスケルトン同梱 `.env.example`）から `.env` を生成し、`VITE_ENABLE_MOCK=true` が初期設定されていることを確認します。

---

## 5. 状態管理・台帳・ドキュメント雛形の配置
1. **`PROJECT_STATE.md` の展開**:
   - `PLUGIN_DIR/templates/PROJECT_STATE.md.template` から `./PROJECT_STATE.md` を生成し、`{{PROJECT_NAME}}`, `{{APP_VERSION}}` (`1.0.0`), `{{UPDATED_AT}}`, `{{EXECUTION_MODE}}`, `{{TEMPLATE_SOURCE}}` を埋め込みます。
2. **`TEMPLATE_PROMOTIONS.md` および Wiki 台帳の初期化**:
   - `PLUGIN_DIR/templates/TEMPLATE_PROMOTIONS.md.template` を `./TEMPLATE_PROMOTIONS.md` へ配置します。
   - `./wiki/logs.md`（時系列ログ表）および `./wiki/skill-impact.md`（影響マップ表）を初期化します。
3. **IDE 設定およびドキュメント雛形のコピー**:
   - `PLUGIN_DIR/templates/code-workspace.template` から `<プロジェクト名>.code-workspace` を生成します。
   - `PLUGIN_DIR/templates/` から `AI駆動システム開発手順書V2.2.md`（または最新版）、`AI駆動システム開発フェーズ定義書V2.2.md`（または最新版）、`要件定義書.md`、`APIキー安全管理・一元化設計書.md`、`AI駆動ロギングシステム仕様書.md`、および `グランドデザイン/` 一式を `./docs/` へコピーします。
   - `PLUGIN_DIR/rules/AGENTS.md` および `PLUGIN_DIR/templates/システム改訂ルール.md` を `./rules/` へコピーします。

---

## 6. Antigravity 推奨設定案内と完了報告
1. Antigravity 設定（`fileAccessPolicy: AGENT_SETTING_POLICY_ASK`, `sandboxMode: true`, `autoExecutionPolicy: CASCADE_COMMANDS_AUTO_EXECUTION_EAGER`, `artifactReviewMode: ARTIFACT_REVIEW_MODE_ALWAYS`）を案内します。
2. `PROJECT_STATE.md` の PHASE 1 を完了に更新してステータスを `PHASE_2_REQUIREMENTS` へ進め、展開したファイル一覧・動作モード・Knowledge Hub 同期状態をユーザーへ報告してください。
