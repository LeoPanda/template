---
name: template-pipeline-sync
description: グローバル環境 (~/.gemini/config/plugins/system-dev-pipeline および ~/.gemini/knowledge-hub) と本ワークスペース (.agents/plugins/system-dev-pipeline および rules/AGENTS.md) のパイプライン差分を比較・原因診断し、ユーザー承認に基づいて同期（Backport / Deploy / Cleanup）を実行する template プロジェクト専用スキル。新規改訂の開始前およびワークスペースのソース改変前に必ず実行する。
---

# パイプライン同期スキル (`template-pipeline-sync`)

## 目的と適用スコープ
本スキルは、`template` ワークスペースにおいてパイプラインの改訂・メンテナンスを行う際、グローバル環境とワークスペース正本のドリフト（乖離）および知見消失を防止するための**ワークスペース専用スキル**です。

以下の**3つのゲートタイミング**において、必ず本スキルを実行してください：
1. **【ゲート①：新規改訂の開始前】**: 次期バージョンの検討・設計書（`docs/設計書/Current/`）の作成・改訂に着手する直前。
2. **【ゲート②：ワークスペースのソース改変前】**: `.agents/plugins/system-dev-pipeline/` 配下のファイル（`agents/`, `rules/`, `skills/`, `skeletons/`, `templates/`）または `rules/AGENTS.md` を編集する直前。
3. **【ゲート③：改訂完了後のグローバル反映時】**: ワークスペースでの改訂・検証が完了し、グローバル環境へデプロイ反映する際。

---

## 作業手順

### Step 1: 差分比較と4分類原因診断の実行
最初に必ず以下のコマンドを実行し、現在の同期状態と差分の原因診断レポートを取得します。

```bash
bash .agents/skills/template-pipeline-sync/scripts/sync_pipeline.sh --status
```

- **判定が `[SYNCED]`（終了コード `0`）の場合**:
  - グローバルとワークスペースは完全一致しており、`.git/pipeline_sync_stamp`（同期証跡）も自動更新されています。そのまま改訂・改変作業へ進んでください。
- **判定が `[DRIFT_DETECTED]`（終了コード `2`）の場合**:
  - 必要に応じて該当ファイルの `diff -u` を確認し、Step 2 に従ってユーザーへ原因と推奨処置を報告してください。

### Step 2: 差分原因の報告とユーザー承認ゲート（Approval Gate）
差分が検出された場合、**独断でファイルを上書きしてはなりません**。以下の4分類に基づいて原因をユーザーへ報告し、実行する同期処理の承認を仰いでください。

| 診断分類 | 原因の説明 | 提案するコマンド（承認後に実行） |
| :--- | :--- | :--- |
| **原因A: グローバル先行**<br>*(Global Ahead)* | 別案件の開発（PHASE 8 等）で昇格された知見や `~/.gemini/knowledge-hub/` の未吸収原票がまだワークスペース正本へ還流（Backport）されていない。 | `bash .agents/skills/template-pipeline-sync/scripts/sync_pipeline.sh --backport` |
| **原因B: ワークスペース先行**<br>*(Workspace Ahead)* | 本 `template` ワークスペースでの改訂作業による変更であり、グローバル側へは未反映の状態。 | ・改訂作業中: そのまま作業続行<br>・リリース反映時: `bash .agents/skills/template-pipeline-sync/scripts/sync_pipeline.sh --deploy` |
| **原因C: 双方向変更**<br>*(Conflict)* | グローバル側での知見昇格と、ワークスペース側での編集が同一ファイルで競合している。 | 双方の Unified Diff を提示し、両方の変更を活かしたマージ案を承認後に適用する。 |
| **原因D: 環境汚染・残骸**<br>*(Artifacts)* | `.orig` / `.rej` 残骸ファイル、または `~/.gemini/config/plugins/` 直下の重複バックアップフォルダが存在する。 | `bash .agents/skills/template-pipeline-sync/scripts/sync_pipeline.sh --cleanup` |
| **共通ルール不一致**<br>*(Root Rules Drift)* | ワークスペースルートの `rules/AGENTS.md` 共通部（第1〜10節）とプラグイン正本に差分がある。 | `bash .agents/skills/template-pipeline-sync/scripts/sync_pipeline.sh --sync-root-rules` |

### Step 3: 承認後の同期実行と完了検証
1. ユーザーから承認を得たら、対応するオプション（`--backport` / `--deploy` / `--cleanup` / `--sync-root-rules`）を実行します。
2. スクリプト実行後、出力末尾の再診断レポートが **`🎉 判定結果: [SYNCED]`** となり、`.git/pipeline_sync_stamp` が更新されたことを確認してから次の作業へ進んでください。
