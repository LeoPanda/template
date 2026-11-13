# REV-3: テスト・実結合検証・LiveProbe検証手順書 (v3.1.0)

- **改訂依頼番号**: `v3.1.0` (`PLAN-V310-001`)
- **フェーズ**: `REV-3` (6段階標準改訂パイプライン 第3段階)
- **親計画書**: [00_v3.1.0改訂基本計画書.md](./00_v3.1.0改訂基本計画書.md)
- **前フェーズ**: [REV-2_実装・静的検証・LiveProbe実装手順書.md](./REV-2_実装・静的検証・LiveProbe実装手順書.md)

---

## 1. フェーズ目的

REV-2 で実装した Live Invariant Probe、環境自己適応スケルトン、フェイルファスト機構の動作を、自動テスト・シミュレーション環境を通じて網羅的に検証する。また、第1段階ドキュメント衛生整理を完了させ、実機提示前ゲート（`verify-review-readiness`）の完全通過を達成する。

---

## 2. 実施タスクリスト

- [x] **T3-1: Live Invariant Probe の自動単体・異常系テスト実行**
  - 改修した `state_manager.py` の Live Probe に対し、以下のシナリオをテスト・検証する：
    1. **正常系**: 正しい設定でバックエンドが起動し、Deep Probe が 200 OK を返して `[LIVE PROBE PASS]` となること。
    2. **異常系 (起動時即死)**: DB パス不正や設定不備でプロセスが即死した場合、`stderr` のエラー内容が出力され、即座に `BLOCK`（Exit Code 1）となること。
    3. **異常系 (タイムアウト)**: サーバーが規定時間内に起動しない場合、タイムアウト保護が発動し、プロセスが強制終了されて `BLOCK` となること。
- [x] **T3-2: マスキング耐性シミュレーション検証**
  - 映画鑑賞記録システムで発生した事象（`DATABASE_URL` がコンテナパスでホストに存在しない状態）を意図的に再現し、共通スケルトンの `Smart Database URL Resolver` が自動フォールバックして正常起動することを実証する。
  - テストフィクスチャで環境変数を改変しなくても、本体コードだけで環境差異が吸収されることを確認する。
- [x] **T3-3: トレーサビリティ検証と署名付き証跡の発行**
  - `python3 scripts/traceability_checker.py --mode full` を実行し、全要件（`REQ-F-310-01`〜`03`）のカバレッジ 100%、異常系比率 20% 以上を確認する。
  - `metrics/qa_runtime_evidence.json` が正常に自動発行されることを確認する。
- [x] **T3-4: 第1段階 ドキュメント衛生・構造整理 (Document Hygiene)**
  - 一時作業ファイル、バックアップファイル（`*.bak` 等）の削除。
  - `docs/設計書/Current/` のファイル名正規化、相対リンク検証（`HG-003`）、Mermaid構文クォート検証（`HG-008`）。
- [x] **T3-5: 実機提示前ゲート (Pre-Review Readiness Gate) の機械検証**
  - `python3 scripts/state_manager.py verify-review-readiness` を実行する。
  - 以下の全項目がオールグリーンとなり、`[READINESS ALL PASS]` が出力されることを確認する：
    1. Harness Guard 静的検査（エラー 0 件）
    2. ドキュメント衛生検査（未整理ファイル 0 件）
    3. モック無効化検査（`VITE_ENABLE_MOCK=false`）
    4. QA証跡（`metrics/qa_runtime_evidence.json`）の署名一致
    5. **【新設】Live Invariant Probe による独立プロセス起動・DB実クエリ検証 (HTTP 200 OK)**

---

## 3. 完了判定条件（Exit Criteria）

- 全自動テストスイートが ALL PASS であること。
- `traceability_checker.py --mode full` により `qa_runtime_evidence.json` が発行されていること。
- `verify-review-readiness` を実行し、Live Probe を含めた全検査が完全合格すること。
