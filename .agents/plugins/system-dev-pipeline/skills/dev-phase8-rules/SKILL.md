---
name: dev-phase8-rules
description: "PHASE 8 メトリクス集計、標準化知見原票 (CLAIM-*.md) の Knowledge Hub 投函、3段階意味的整合性監査、ask_question 承認による Local Overlay 即時再生成、Git本番リリース、および改訂運用ルールの適用を行うスキル。"
---

# PHASE 8: メトリクス集計・Knowledge Hub 知見昇格と改訂管理体制への移行 V2.3

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **連携スキル / ツール**:
  - 📊 `dev-metrics-collector` (定量測定・総合健全性レポート)
  - 🧹 `wiki-compactor` (Wiki枝刈り・原票クラスタリング・Overlay圧縮)
  - 💡 `wiki-proposer` (標準化知見原票 `CLAIM-*.md` 起案・Knowledge Hub 投函)
  - 🛡️ `qa-engineer` (Semantic Auditor: 3段階意味的整合性監査・新4大関門)
  - 🔄 `scripts/pipeline-reconciler.sh` (Local Overlay クリーン再生成・状態管理)
  - ⚙️ `dev-git-release` (GitHub本番リリース・ブランチ刷新)
- **承認ゲート**: 👤 `ask_question` モーダルによる知見昇格・競合裁定の明示的承認必須

本番リリースが完了したシステムに対し、メトリクス集計、Central Knowledge Hub を介した知見昇格、GitHub本番リリース、および改訂作業ルールを適用してください。

---

## 作業手順

### 1. 定量メトリクス集計と総合健全性診断 (`dev-metrics-collector`)
- `dev-metrics-collector` スキルを実行し、`docs/plans/metrics/development-metrics-summary.json` および `metrics/system_health_report.md` を生成してプロジェクト総合グレード (A〜D) を報告します。

### 2. Wiki整理と標準化知見原票の起案・Inbox投函 (`wiki-compactor` & `wiki-proposer`)
1. `wiki-compactor` を実行し、`./wiki/patterns/` の重複統合・アーカイブ、および `~/.gemini/knowledge-hub/inbox/` の事前原票クラスタリングを行います。
2. `wiki-proposer` を実行し、`./wiki/patterns/universal/` の Tier 2 知見から固有名詞と履歴IDを排除した **標準化知見原票（`CLAIM-{YYYYMMDD}-{SLUG}-{PAT_ID}.md`）** を生成し、`./promotions/` および `~/.gemini/knowledge-hub/inbox/` へ投函します（`.patch` や個別 `PURPOSE.md` は生成しません）。
3. 提案一覧を `./TEMPLATE_PROMOTIONS.md` に記録します。

### 3. 3段階意味的整合性監査（新・複合検証ゲート）の実行
🛡️ `qa-engineer`（Semantic Auditor）へ投函された原票の3段階監査（4大関門）を委譲します：
- **New Gate 1 (Invariants)**: `rules/CORE_INVARIANTS.md`（INV-01〜10）への違反が 0 件であること（違反時は即座に `pipeline-reconciler.sh --reject-claim` で `rejected/` へ移動）。
- **New Gate 2 (4分類相互矛盾監査)**: 既存 Core / Overlay / 他原票との関係を `EQUIVALENT`（重複）、`SUBSUMPTION`（包含統合）、`SCOPED_BRANCH`（条件分岐）、`TRUE_CONTRADICTION`（真の矛盾）で判定。
- **New Gate 3 (過剰適合排除 & アンカー実在)**: 固有名詞混入ゼロ、統合先ファイル・セクション見出しの実在確認。
- **New Gate 4 (純度 & 絶対行数バジェット)**: `pipeline-reconciler.sh --audit-budget` による履歴ID混入ゼロ・絶対行数上限遵守確認。
- ※ なお、`/schedule` バックグラウンド定期起動時は人間入力待ちを行わず、`pending_approval/REVIEW-*.md` に監査結果を出力して通知終了します。

### 4. `ask_question` モーダル承認ゲートと Local Overlay クリーン再生成
対話セッション中（インライン起動時）、コンダクターは `./TEMPLATE_PROMOTIONS.md` と統合プレビューを提示し、**`ask_question` ツール（選択式UIモーダル）** でユーザーの決裁を仰ぎます：
1. **通常の監査 PASS 時**:
   - `(Recommended) 承認して Local Overlay へ即時反映する` / `今回は保留する` / `棄却（rejected へ移動）する`
2. **矛盾・重複検出時（`TRUE_CONTRADICTION` 等）**:
   - `(Recommended) 適用スコープ条件（対象Profile等）を分岐させて両立させる` / `新知見で上書きする` / `既存ルールを維持し棄却する`
3. **承認後の反映ルーティング（Immutable Core 保護）**:
   - **`GLOBAL_PLUGIN` モード（通常案件）**: 公式プラグイン（Immutable Core）は1バイトも書き換えず、`pipeline-reconciler.sh --activate-claim <CLAIM>` を実行して `active_claims/` へ登録し、`~/.gemini/knowledge-hub/overlay/LOCAL_FEEDBACK_RULES.md`（上限80行）をクリーン再生成します。これにより次案件から即座に知見が有効化されます。
   - **`LOCAL_STANDALONE` モード（パイプライン正本改訂時）**: ローカルの `.agents/plugins/system-dev-pipeline/` へインプレース統合し、`PIPELINE_MANIFEST.json` と `FEEDBACK_LEDGER.md` を更新します。

### 5. GitHub本番リリースおよび開発ブランチ刷新 (`dev-git-release`)
- コンダクター専任で `dev-git-release` を実行し、`main` ブランチへの Squash Merge、バージョンタグ付与、Push、および新規 `feature` ブランチの再作成を行います。

### 6. システム改訂ルールの配置と状態管理の更新
- `templates/システム改訂ルール.md` を `rules/システム改訂ルール.md` に配置し、`AGENTS.md` / `GEMINI.md` / `.agents/rules/system-revision.md`（修正後の `docker compose down` ＋ `up --build -d` 徹底、`LOCAL_FEEDBACK_RULES.md` 参照フック、`dev-git-release` 実行を含む）を適用します。
- `PROJECT_STATE.md` のステータスを `PRODUCTION_ACTIVE` へ更新し、改訂管理体制への移行を完了してください。
