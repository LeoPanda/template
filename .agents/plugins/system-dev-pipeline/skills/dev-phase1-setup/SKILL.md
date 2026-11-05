---
name: dev-phase1-setup
description: "新規システム開発プロジェクトの環境初期化を行うスキル。Central Knowledge Hub未処理原票検知、静的スケルトン基盤展開、ディレクトリ構造、Wiki層・メトリクス受皿、.env、PROJECT_STATE.md、TEMPLATE_PROMOTIONS.md、docs配下の各種ドキュメント雛形を自動生成・配置する。"
---

# PHASE 1: プロジェクト初期化指示

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

## 2. Central Knowledge Hub の初期化と未処理原票の起動時検知
1. `bash "${PLUGIN_DIR}/scripts/pipeline-reconciler.sh" --init-hub` および `--status` を実行し、`~/.gemini/knowledge-hub/` の状態を診断します。
2. `inbox/` または `pending_approval/` に未反映・裁定待ちの知見原票（`CLAIM-*.md` / `REVIEW-*.md`）が存在する場合：
   - ユーザーへ未処理原票の存在をアラートし、必要に応じて 🛡️ `qa-engineer` による3段階意味的監査を実行した上で、**`ask_question` モーダル**で即時承認・裁定を行います。
   - 承認された原票は `pipeline-reconciler.sh --activate-claim <CLAIM>` により `overlay/LOCAL_FEEDBACK_RULES.md` へクリーン再生成反映し、本プロジェクトの PHASE 2 以降から即座に有効化します。

---

## 3. ディレクトリ構造および `.gitignore` の自動設定
1. **ディレクトリ作成**:
   - ドキュメント・計画・ルール: `./docs/設計書/Current/`, `./docs/検討課題/`, `./docs/plans/`, `./rules/`
   - Spoke Wiki 受皿: `./wiki/patterns/local/`, `./wiki/patterns/universal/`, `./wiki/patterns/rejected/`, `./wiki/archive/`
   - メトリクス・原票控え: `./metrics/`, `./promotions/`
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

   # Lockfiles whitelist (*.json 除外時も CI 再現性のため保護)
   !package-lock.json
   ```

---

## 4. 静的スケルトン層（`skeletons/`）と `.env` の自動展開 (Shift-Left)
1. `PLUGIN_DIR/skeletons/common/`（`scripts/`, `.githooks/`, `.github/workflows/ci.yml`, `.editorconfig`）をプロジェクトルートへコピーし、`git config core.hooksPath .githooks` を実行します。
2. 選定プロファイルに応じたスケルトン基盤を展開します（未存在時）：
   - **Profile A (ゴールデンパス)**: `skeletons/profile-a/`（`docker/`, `backend/`, `frontend/`）をコピーし、`chmod +x docker/entrypoint.sh` を付与。
   - **Profile D (ローカルデスクトップ型)**: `skeletons/profile-d/`（`src-tauri/`, `docker/`, `backend/`, `frontend/`）をコピー。
3. **Dual Provisioning 原則（ペア生成義務化）**:
   - `PLUGIN_DIR/templates/.env.template` からプロジェクトルートへ、Git管理用の **`.env.example`** とローカル実行用の実体 **`.env`**（`VITE_ENABLE_MOCK=true`）の**両方を必ずペアで自動展開・同期**します。
4. **品質管理設定ファイルの自動補完**:
   - ブラウンフィールド改訂・既存プロジェクト移行時、既存ディレクトリが存在する場合でも、`backend/pyproject.toml` や `.editorconfig` 等の品質管理設定ファイルが欠落している場合はスケルトンから自動補完します。

---

## 5. 状態管理台帳・ドキュメント雛形の初期化 (Single Writer 原則)
1. **状態管理台帳 (`project_state.json` / `PROJECT_STATE.md`) の初期化**:
   - `python3 scripts/state_manager.py init --name <プロジェクト名> --profile <選定プロファイル>` を実行し、機械正本 `project_state.json` とビュー `PROJECT_STATE.md` を決定論的に初期生成します。
2. **`TEMPLATE_PROMOTIONS.md` および Wiki 台帳の初期化**:
   - `PLUGIN_DIR/templates/TEMPLATE_PROMOTIONS.md.template` を `./TEMPLATE_PROMOTIONS.md` へ配置します。
   - `./wiki/logs.md`（時系列ログ表）および `./wiki/skill-impact.md`（影響マップ表）を初期化します。
3. **IDE 設定およびドキュメントディレクトリ構造の初期化**:
   - `PLUGIN_DIR/templates/code-workspace.template` から `<プロジェクト名>.code-workspace` を生成します。
   - `PLUGIN_DIR/templates/rules_AGENTS.md.template` を `./rules/AGENTS.md`（プロジェクト固有規約ファイル）へ配置します。
   - `PLUGIN_DIR/templates/システム改訂運用基準書.md` を `./docs/システム改訂運用基準書.md` へ配置します。
   - 必要に応じて `PLUGIN_DIR/templates/グランドデザイン/` 等の参照用ガイドラインのみを配置します。

---

## 6. Antigravity 推奨設定案内と完了報告
1. Antigravity 設定（`fileAccessPolicy: AGENT_SETTING_POLICY_ASK`, `sandboxMode: true`, `autoExecutionPolicy: CASCADE_COMMANDS_AUTO_EXECUTION_EAGER`, `artifactReviewMode: ARTIFACT_REVIEW_MODE_ALWAYS`）を案内します。
2. `python3 scripts/state_manager.py set-phase PHASE_2_REQUIREMENTS` を実行してステータスを進め、展開したファイル一覧・動作モード・Knowledge Hub 同期状態をユーザーへ報告してください。
