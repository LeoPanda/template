# REV-6: メトリクス・知見昇格・リリース手順書 (v3.0.1)

- **改訂依頼番号**: `v3.0.1` (`PLAN-V301-001`)
- **フェーズ**: `REV-6` (6段階標準改訂パイプライン 第6段階)
- **親計画書**: [00_v3.0.1改訂基本計画書.md](./00_v3.0.1改訂基本計画書.md)

---

## 1. フェーズ目的

定量メトリクスを集計し、Central Knowledge Hub との整合性を確認した上で、グローバル環境（`~/.gemini/config/plugins/system-dev-pipeline`）へのデプロイ同期（`template-pipeline-sync --deploy`）および Git リリース（`v3.0.1`）を完了する。

---

## 2. 実施タスクリスト

- [x] **T6-1: 定量メトリクス集計とレポート更新**
  - 👑 コンダクターが `python3 .agents/plugins/system-dev-pipeline/skills/dev-metrics-collector/scripts/metrics_collector.py --all` を実行し、健全性レポート（`metrics/system_health_report.md`）および集計サマリJSONを最新化。
- [x] **T6-2: Central Knowledge Hub 整合性確認**
  - `bash .agents/plugins/system-dev-pipeline/scripts/pipeline-reconciler.sh --status` を実行し、未処理原票ゼロ（`inbox: 0件`, `active_claims: 0件`）、および `Immutable Core Version: 3.0.1`（整合性維持）を確認。
- [x] **T6-3: グローバル環境へのデプロイ同期 (`template-pipeline-sync`)**
  - `bash .agents/skills/template-pipeline-sync/scripts/sync_pipeline.sh --deploy` を実行し、ワークスペース正本をグローバル環境（`~/.gemini/config/plugins/system-dev-pipeline`）へ反映完了。
  - 再診断レポートが **`🎉 判定結果: [SYNCED]`** となり、`.git/pipeline_sync_stamp` が更新されたことを確認。
- [x] **T6-4: Git 本番リリース (`dev-git-release`)**
  - 変更差分をステージング・コミットし、`main` ブランチへのマージ（Squash Merge）、バージョンタグ `v3.0.1` の付与、リモートプッシュ、および `feature` ブランチの再作成を完了。

---

## 3. 完了判定条件（Exit Criteria）

- 定量メトリクス集計が正常終了していること。
- Central Knowledge Hub との整合性が確認されていること。
- グローバル環境へのデプロイ同期が完了し、`sync_pipeline.sh --status` が `[SYNCED]` を返すこと。
- Git 本番リリース（タグ `v3.0.1` 付与）が完了していること。
