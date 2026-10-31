# template ワークスペース ローカル開発・改訂規約

本ファイルは `template` ワークスペース固有のローカル開発・改訂規約です。
システム開発プロセスの標準規約はプラグイン正本（`.agents/plugins/system-dev-pipeline/rules/AGENTS.md`）で一元定義されており、本ファイルにはワークスペース固有の運用ルールのみを定義します（重複防止・ノイズ輻輳防止）。

---

## 1. パイプライン改訂作業におけるグローバル・ワークスペース同期規約
1. **専用スキル（`template-pipeline-sync`）による同期義務**:
   - グローバル環境（`~/.gemini/config/plugins/system-dev-pipeline/` および `~/.gemini/knowledge-hub/`）と本ワークスペース（`.agents/plugins/system-dev-pipeline/`）のドリフト・知見消失を防止するため、以下のタイミングで必ず [template-pipeline-sync](../.agents/skills/template-pipeline-sync/SKILL.md) スキル（`bash .agents/skills/template-pipeline-sync/scripts/sync_pipeline.sh --status`）を実行しなければならない：
     - **ゲート①（新規改訂の開始前）**: 次期バージョンの検討・設計書（`docs/設計書/Current/`）の作成・改訂を開始する直前。
     - **ゲート②（ワークスペースのソース改変前）**: `.agents/plugins/system-dev-pipeline/` 配下のファイルまたは本ファイルを編集する直前。
     - **ゲート③（改訂完了後のグローバル反映時）**: ワークスペースでの改訂成果をグローバル環境へデプロイ反映する際。
2. **原因診断レポートとユーザー承認の必須化**:
   - 差分が検出された場合は、盲目的な上書きコピー（`cp -r` 等）を行わず、差分の原因（グローバル先行・ワークスペース先行・双方向変更・残骸汚染）をユーザーへ報告し、**必ずユーザーの承認を得てから**同期処理（`--backport` / `--deploy` / `--cleanup`）を実行する。
3. **ルール重複の厳格排除と Git Pre-commit ガード**:
   - プラグイン共通規約（`AI駆動システム開発プロセス標準規約` の第0〜10節）を本ファイルに転記・重複させてはならない。
   - `.git/hooks/pre-commit` により、プラグイン共通規約の重複混入（二重読み込みによるノイズ・輻輳）や未同期のグローバル先行差分がある状態でのコミットは機械的にブロックされる。
