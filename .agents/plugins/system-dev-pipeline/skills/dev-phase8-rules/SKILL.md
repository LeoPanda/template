---
name: dev-phase8-rules
description: "PHASE 8 ドキュメント改訂管理スキルの適用。知見昇格レビュー、Git本番リリース、本番リリース完了後の改訂運用ルール（rules/システム改訂ルール.md, AGENTS.md, GEMINI.md）を適用・設定する。"
---

# PHASE 8: ドキュメント改訂管理ルールの自動設定と知見昇格

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`)
- **連携**: ⚙️ `dev-git-release`
- **承認ゲート**: 👤 ユーザーによる知見昇格レビューの明示的承認必須

本番リリースが完了したシステムに対し、知見昇格の実施、GitHub本番リリース、および今後の改訂作業・保守の変更履歴を厳格に管理するためのルールを適用してください。

## 作業手順

1. **知見昇格レビュー（承認ゲート）**:
   - プロジェクトルート直下の `./TEMPLATE_PROMOTIONS.md` を読み込み、蓄積された汎用知見（Tier 2候補）をユーザーへ提示してください。
   - ユーザーから明示的な昇格承認を得た知見について、プラグイン資産（`.agents/plugins/system-dev-pipeline/` 配下の `rules/`, `agents/`, `templates/`）へ反映してください。
   - `PROJECT_STATE.md` の知見昇格承認ゲートを更新してください。

2. **GitHub本番リリースおよび開発ブランチ刷新（dev-git-release の発動）**:
   - `dev-git-release` スキルを実行し、未コミット変更の自動確定、`.env` からのバージョン番号取得、`main` ブランチへの Squash Merge（`Release v1.0.0`）、GitHub（SSH経由）へのPush、旧 `feature` ブランチの削除、および最新 `main` からの新規 `feature` ブランチ作成を行ってください。

3. **システム改訂ルールの配置**:
   - プラグインの `templates/システム改訂ルール.md` を `rules/システム改訂ルール.md` にコピー・保存してください。

4. **プロジェクト全体ルールの適用**:
   - プロジェクトルート直下に以下のファイルを自動生成・適用してください。
     - `AGENTS.md`: Antigravity エージェント運用ルール（コンダクター基本動作規範、Single Writer、サブエージェント協調）
     - `GEMINI.md`: プロジェクト共通プロンプト・開発ルール
     - `.agents/rules/system-revision.md`: 今後の改訂時のドキュメント更新強制ルール
   - 各ルールファイル内に `rules/システム改訂ルール.md` を参照・遵守する旨を明記するとともに、**「システムの修正・改訂時にはソースコードの変更を確実に反映させるため、修正後に必ず `docker compose down` および `docker compose up --build -d` を実行し、Docker上のコンテナをビルド・再構成すること」**、および**「改訂完了時には `dev-git-release` スキルを実行して GitHub への本番反映と次期開発ブランチの刷新を行うこと」**のルールを含めてください。

5. **状態管理の更新**:
   - `PROJECT_STATE.md` のステータスを `PRODUCTION_ACTIVE` へ更新し、改訂管理体制への移行を完了してください。
