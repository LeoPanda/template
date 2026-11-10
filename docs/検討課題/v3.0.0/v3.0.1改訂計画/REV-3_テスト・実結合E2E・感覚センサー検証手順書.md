# REV-3: 自動テスト・実結合E2E・感覚センサー検証手順書 (v3.0.1)

- **改訂依頼番号**: `v3.0.1` (`PLAN-V301-001`)
- **フェーズ**: `REV-3` (6段階標準改訂パイプライン 第3段階)
- **親計画書**: [00_v3.0.1改訂基本計画書.md](./00_v3.0.1改訂基本計画書.md)

---

## 1. フェーズ目的

改修したハーネスおよびスクリプト群が、モック混入、証跡改ざん、文書衛生違反を確実に機械遮断できることを実テストで検証する。また、**「第1段階：ドキュメント衛生・構造整理」** を実施し、新設された `state_manager.py verify-review-readiness` を完全に通過させて `REV-4`（実機レビュー）への突入準備を整える。

---

## 2. 実施タスクリスト

- [x] **T3-1: コアスクリプト群の自動検証テスト（正常系・異常系）**
  1. **`harness_guard.py` 検証**:
     - バックエンドコード内に `def generate_mock_video(): ...` や `testsrc`、`sine=440` を含むファイルが存在する場合、`HG-002` で `BLOCK` されることを確認。
     - `docs/設計書/` 直下に `.md` ファイルを置いた場合、または `docs/設計書/Current/` にバージョン番号付き文書（`*_v1.0.md`）を置いた場合、`HG-009` で `BLOCK` されることを確認。
  2. **`traceability_checker.py` 検証**:
     - `--mode full` 実行により、`metrics/qa_runtime_evidence.json` が正しいチェックサム（`evidence_checksum`）付きで自動生成されることを確認。
  3. **`state_manager.py` 検証**:
     - `metrics/qa_runtime_evidence.json` を削除した状態で `complete-revision` を呼んだ場合、`[INV-QA-01]` で `BLOCK` されることを確認（素通りバグ修正の確認）。
     - JSON の `evidence_checksum` を手動改ざんした場合、チェックサム不一致で `BLOCK` されることを確認。
- [x] **T3-2: 第1段階：ドキュメント衛生・構造整理 (Document Hygiene & Structure)**
  - ユーザーが `REV-4` で実機およびワークスペースを確認する前に、以下の衛生整理を完了させる：
    1. 作業用の一時メモ、重複ドラフト、不要な検証スクリプトの削除。
    2. `docs/設計書/Current/` 配下のファイル名が規約通りであり、タイトルから個別バージョン番号 `(V1.x)` が排除されていること（`HG-009` PASS）。
    3. ドキュメント内リンクがすべて相対パスであり、リンク切れがないこと（`HG-003` PASS）。
    4. 現時点で確定している仕様差分を正本設計書へ反映し、整然とした状態を確立。
- [x] **T3-3: Pre-Review Readiness Gate の機械検証**
  - モック解除（`.env` の `VITE_ENABLE_MOCK=false`、`project_state.json` の `mock_mode = DISABLED`）を確認。
  - 以下のコマンドを実行し、**ALL CLEAR** となることを確認する：
    ```bash
    python3 .agents/plugins/system-dev-pipeline/scripts/state_manager.py verify-review-readiness
    ```

---

## 3. 完了判定条件（Exit Criteria）

- T3-1 の全正常系・異常系テストが期待通りに PASS すること。
- ドキュメント衛生整理が完了し、`harness_guard.py --all` がエラー 0 件であること。
- `python3 scripts/state_manager.py verify-review-readiness` が Exit Code 0（PASS）を出力すること。
