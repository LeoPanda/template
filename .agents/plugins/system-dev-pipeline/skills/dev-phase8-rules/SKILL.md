---
name: dev-phase8-rules
description: "PHASE 8 メトリクス集計、Wiki進化提案、複合検証ゲート、知見昇格ルーティング（2層プロファイル対応）、Git本番リリース、および改訂運用ルールの適用を行うスキル。"
---

# PHASE 8: メトリクス集計・知見昇格と改訂管理体制への移行 V2.2

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **連携スキル**:
  - 📊 `dev-metrics-collector` (定量測定・総合健全性レポート)
  - 💡 `wiki-proposer` (スキル進化提案・PURPOSE.md生成)
  - 🛡️ `qa-engineer` (Gating Tester: 複合検証ゲート)
  - 🧹 `wiki-compactor` (Wiki枝刈り・整理)
  - ⚙️ `dev-git-release` (GitHub本番リリース・ブランチ刷新)
- **承認ゲート**: 👤 ユーザーによる知見昇格レビューの明示的承認必須

本番リリースが完了したシステムに対し、メトリクス集計、知見昇格、GitHub本番リリース、および今後の改訂作業ルールを適用してください。

---

## 作業手順

### 1. 定量メトリクス集計と総合健全性診断 (`dev-metrics-collector`)
- `dev-metrics-collector` スキルを実行し、全フェーズの実績データを統合します。
- `docs/plans/metrics/development-metrics-summary.json` および `metrics/system_health_report.md` を生成し、プロジェクト総合グレード (A〜D) を算出・報告します。

### 2. Wikiスキル自己進化提案と検証 (`wiki-proposer` 連携)
1. `wiki-proposer` を実行し、`./wiki/patterns/universal/` 配下のTier 2知見から改善パッチを立案します。
   - **V2.2 重点昇格観点**: 2層プロファイル体系（Profile A/B/C/D ＋ アドオン）、Alembicマイグレーション知見、直書きモック排除・MSW制御、フロント250行制限、Aware UTC等の新規ルールに関するプラクティスを優先抽出します。
2. 対象スキルの `PURPOSE.md` を生成・更新します。
3. 提案サマリを `./TEMPLATE_PROMOTIONS.md` に追記します。
4. 🛡️ `qa-engineer` に複合検証ゲート（Gating）を実行させ、パッチの安全性を確認します。

### 3. 知見昇格レビューと昇格ルーティング（承認ゲート）
- ユーザーに `./TEMPLATE_PROMOTIONS.md` を提示し、昇格採否の承認を得ます。
- `PROJECT_STATE.md` の `EXECUTION_MODE` を参照して安全に分岐します：
  - **`GLOBAL_PLUGIN` モード時**:
    - グローバル領域への直接書き込みを行わず、`./promotions/` ディレクトリを自動生成（`mkdir -p ./promotions`）した上で差分パッチ（`./promotions/*.patch`）を出力・案内します。
  - **`LOCAL_STANDALONE` モード時**:
    - 承認された知見をローカルプラグイン資産（`.agents/plugins/system-dev-pipeline/`）へ反映します。

### 4. Wiki層の整理・枝刈り (`wiki-compactor`)
- `wiki-compactor` を実行し、重複パターンの統合、陳腐化パターンのアーカイブ（`./wiki/archive/`）、台帳（`./wiki/logs.md`）の整合性確認を行います。

### 5. GitHub本番リリースおよび開発ブランチ刷新 (`dev-git-release`)
- コンダクター専任で `dev-git-release` スキルを実行し、未コミット変更の自動確定、`.env` からのバージョン取得、`main` ブランチへの Squash Merge（`Release v1.0.0`）、GitHub（SSH経由）へのPush、旧 `feature` ブランチの削除、および最新 `main` からの新規 `feature` ブランチ作成を行います。

### 6. システム改訂ルールの配置とプロジェクト全体ルールの適用
- プラグインの `templates/システム改訂ルール.md` を `rules/システム改訂ルール.md` にコピー・保存します。
- プロジェクトルート直下に以下のファイルを生成・適用します：
  - `AGENTS.md`: Antigravity エージェント運用ルール（コンダクター基本動作規範、Single Writer、サブエージェント協調）
  - `GEMINI.md`: プロジェクト共通プロンプト・開発ルール
  - `.agents/rules/system-revision.md`: 今後の改訂時のドキュメント更新強制ルール
- ルール内に **「修正後のコンテナ再構成徹底ルール (`docker compose down` ＋ `up --build -d`)」** および **「改訂完了時の `dev-git-release` 実行」** を明記します。

### 7. 状態管理の更新
- `PROJECT_STATE.md` のステータスを `PRODUCTION_ACTIVE` へ更新し、改訂管理体制への移行を完了してください。

