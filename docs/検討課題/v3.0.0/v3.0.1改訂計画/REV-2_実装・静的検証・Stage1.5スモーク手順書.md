# REV-2: 実装・静的検証・Stage 1.5 スモーク手順書 (v3.0.1)

- **改訂依頼番号**: `v3.0.1` (`PLAN-V301-001`)
- **フェーズ**: `REV-2` (6段階標準改訂パイプライン 第2段階)
- **親計画書**: [00_v3.0.1改訂基本計画書.md](./00_v3.0.1改訂基本計画書.md)

---

## 1. フェーズ目的

確定した設計仕様に基づき、コアスクリプト群（`harness_guard.py`, `state_manager.py`, `traceability_checker.py`）および規約・テンプレート群の差分実装を行い、静的検証（Hard Gate）およびインプロセス実I/Oスモークテストを通過させる。

---

## 2. 実施タスクリスト

- [x] **T2-1: `scripts/harness_guard.py` の改修**
  1. `HG-002` の拡張:
     - 検査対象パスに `backend/`（`tests/`, `.venv/` 等除く）および `src-tauri/` を追加。
     - モック生成関数（`generate_mock_*`, `dummy_*`, `Mock[A-Z0-9_]+`）およびメディアダミー生成文字列（`testsrc`, `sine=`, `anoisesrc`）の検知ロジックを追加。
     - Python AST による `except` 節内でのモック返却検知を追加。
  2. `HG-009` の拡張（文書衛生検査の強化）:
     - `docs/設計書/` 直下に `.md` ファイルが放置されている場合に `BLOCK`。
     - `docs/設計書/Current/` 配下にバージョン番号付きファイル（例: `*_v1.*.md`）や一時ファイル（`*.bak`, `*.tmp`, `*draft*`）が存在する場合に `BLOCK`。
- [x] **T2-2: `scripts/state_manager.py` の改修**
  1. `validate_revision_closure_invariants` のバグ修正:
     - `metrics/qa_runtime_evidence.json` が存在しない場合に即座に `[INV-QA-01]` で `BLOCK` する `else` 句を追加。
     - `revision_id` と `active_revision_id` の一致検査を追加。
     - ペイロードから再計算した SHA-256 チェックサムと `evidence_checksum` の照合ロジックを追加。
  2. `cmd_verify_review_readiness` の新設:
     - サブコマンド `verify-review-readiness` を追加。
     - `harness_guard.py --all` の呼び出し（違反 0 件）、ドキュメント衛生、モック解除状態（`.env` の `VITE_ENABLE_MOCK=false`、`project_state.json` の `mock_mode = DISABLED`）、署名付き `qa_runtime_evidence.json` の検証を一括実行。
- [x] **T2-3: `scripts/traceability_checker.py` の改修**
  1. 署名付き `qa_runtime_evidence.json` 自動生成機能の実装:
     - `--mode full` 合格時に、`.env` から `VITE_ENABLE_MOCK` の値を取得し、`active_revision_id`、Git HEAD、テスト結果、および SHA-256 チェックサム（`evidence_checksum`）を算出して `metrics/qa_runtime_evidence.json` を決定論的に書き出す。
- [x] **T2-4: 規約・テンプレート・スキルの改修**
  1. `rules/AGENTS.md`: コンダクターの `verify-review-readiness` 実行義務、モック出力の物理隔離規約、ドキュメント精査の2段階分離を追記。
  2. `templates/システム改訂運用基準書.md`: `REV-3` 完了条件への衛生整理および `verify-review-readiness` の追加、`REV-4` 前提条件の明文化、`REV-5` の位置づけ更新。
  3. `skills/dev-doc-reviewer/SKILL.md`: 第1段階（衛生整理）と第2段階（相互整合性監査）の責務分離を明記。
- [x] **T2-5: スケルトン同期 & Stage 1.5 スモークテスト**
  - 改修した3スクリプトを `skeletons/common/scripts/` 配下へ完全同報同期（`diff -u` 差分ゼロ確認）。
  - `python3 scripts/harness_guard.py --all` を実行し、既存コードに対する偽陽性（誤検知）がないことを確認。

---

## 3. 完了判定条件（Exit Criteria）

- 全対象スクリプトおよび規約ファイルの差分実装が完了していること。
- `python3 scripts/harness_guard.py --all` がエラー 0 件で PASS すること。
- `skeletons/common/scripts/` とワークスペース内 `scripts/` が完全一致していること。
