# REV-3: 自動テスト・実結合E2E・感覚センサー検証手順書 (v3.0.0)

- **改訂依頼番号**: `v3.0.0` (`PLAN-V300-001`)
- **フェーズ**: `REV-3` (6段階標準改訂パイプライン 第3段階)
- **親計画書**: [00_v3.0.0改訂基本計画書.md](./00_v3.0.0改訂基本計画書.md)

---

## 1. フェーズ目的
改修したコアスクリプト群（AIハーネス V3）および改訂ライフサイクル制御が、正常系だけでなく異常系（アリバイテスト、空実装、未起票改変、`REV-4` 未承認クローズ等）を確実に機械遮断できることを実ファイル・一時ディレクトリを用いた自動検証で実証する。

---

## 2. 実施タスクリスト

- [ ] **T3-1: `traceability_checker.py` の実I/O検証テスト**
  1. `docs/plans/シナリオテスト計画書.md` にのみ `[REQ-F99]` が記載されている場合、未検証（`BLOCKED`）として遮断されることを確認。
  2. テストファイル先頭コメントにのみ `[REQ-F01]` があり、テスト関数自体が `assert True`（トートロジー）または `expect(btn).toBeInTheDocument()` のみ（浅いアサーション）である場合、カバレッジから除外され `BLOCKED` となることを確認。
  3. 有効な3階層アサーションを持つテスト関数に `[REQ-F01]` が紐づいている場合のみ `PASS` となることを確認。
- [ ] **T3-2: `harness_guard.py` の実I/O検証テスト**
  1. `HG-001`: FE 280行 / BE 450行のファイルが `WARN`（Exit Code 0）となり、FE 360行 / BE 560行のファイルが `BLOCK`（Exit Code 1）となることを確認。
  2. `HG-010`: `def generate_xml(): pass` や `return "<!-- Generated -->"`、`onClick={() => {}}` を含むコードが `BLOCK` されることを確認。
  3. `HG-011`: `PRODUCTION_ACTIVE` かつ改訂 `IDLE` 状態で `backend/` 等のファイルをステージングした際に `BLOCK` されることを確認。
- [ ] **T3-3: `state_manager.py` の6段階改訂ライフサイクル & Invariants Gate 検証テスト**
  1. `start-revision` 実行時に `REV-1`〜`REV-6` の6手順書とチェックリストが生成され、`session_mode` が `"DEV_PIPELINE"` になることを確認。
  2. `record-approval --phase REV_4` を実行する前の状態で `complete-revision` を呼び出した際、`[INV-REV-04]` エラーで Exit Code 1 遮断されることを確認。
  3. `record-approval --phase REV_4` 実行後、および `qa_runtime_evidence.json`・メトリクス配置後に `complete-revision` が正常完了することを確認。

---

## 3. 完了判定条件（Exit Criteria）
- 上記 T3-1〜T3-3 の全正常系・異常系検証ケースが期待通りの Exit Code とメッセージを出力して PASS すること。
- `skeletons/common/scripts/` と `.agents/plugins/system-dev-pipeline/scripts/` の差分が 0（完全一致）であること。
