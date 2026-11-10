# REV-5: 本番総合監査・成果物ビルド手順書 (v3.0.0)

- **改訂依頼番号**: `v3.0.0` (`PLAN-V300-001`)
- **フェーズ**: `REV-5` (6段階標準改訂パイプライン 第5段階 ※旧 `REV-4` からシフト)
- **親計画書**: [00_v3.0.0改訂基本計画書.md](./00_v3.0.0改訂基本計画書.md)

---

## 1. フェーズ目的
`REV-4` のユーザー実機レビューおよび対話的改修が完了した最終状態のコード・ドキュメント群に対し、コード品質監査（`dev-review-code`）・ドキュメント相互整合性監査（`dev-doc-reviewer`）・システム総合監査（`dev-review-system`）を実施し、配布成果物・マニフェストを確定させる。

---

## 2. 実施タスクリスト

- [x] **T5-1: ドキュメント相互整合性 & ハーネスガード総合監査**
  - `python3 .agents/plugins/system-dev-pipeline/scripts/harness_guard.py --all` 実行（`HG-001`〜`HG-011` 違反ゼロ確認）。
  - `bash .agents/plugins/system-dev-pipeline/scripts/pipeline-reconciler.sh --audit-budget` 実行（`AGENTS.md` ≦ 220行、`agents/*.md` ≦ 120行、`skills/*/SKILL.md` ≦ 120行、Lineage ID 混入ゼロ確認）。
- [x] **T5-2: スケルトン・テンプレート同期監査**
  - `.agents/plugins/system-dev-pipeline/scripts/` と `.agents/plugins/system-dev-pipeline/skeletons/common/scripts/` の3スクリプト（`harness_guard.py`, `state_manager.py`, `traceability_checker.py`）が `diff -u` で完全一致していることを確認。
  - 全ての `REV-1`〜`REV-6` 記述に旧 `REV-1`〜`REV-5` の取り残しがないことを全文検索（`grep`）で確認。
- [x] **T5-3: バージョンマニフェスト・系譜台帳の V3.0.0 確定**
  - `.agents/plugins/system-dev-pipeline/.gemini-plugin/plugin.json` のバージョン `"3.0.0"` 確認。
  - `.agents/plugins/system-dev-pipeline/PIPELINE_MANIFEST.json` の `"version": "3.0.0"` および `PAT-SYS-015`, `PAT-SYS-016` の登録確認。
  - `.agents/plugins/system-dev-pipeline/FEEDBACK_LEDGER.md` の V3.0.0 系譜レコード記載確認。

---

## 3. 完了判定条件（Exit Criteria）
- 全ての機械的監査ゲートがエラー 0 件で PASS し、V3.0.0 パッケージ資産の完全性が確認されていること。
