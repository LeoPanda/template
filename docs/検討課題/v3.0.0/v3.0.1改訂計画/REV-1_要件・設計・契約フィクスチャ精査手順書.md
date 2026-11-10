# REV-1: 要件・設計・契約フィクスチャ精査手順書 (v3.0.1)

- **改訂依頼番号**: `v3.0.1` (`PLAN-V301-001`)
- **フェーズ**: `REV-1` (6段階標準改訂パイプライン 第1段階)
- **親計画書**: [00_v3.0.1改訂基本計画書.md](./00_v3.0.1改訂基本計画書.md)
- **対象レポート**: [評価・考察レポート (EVAL-PL-002)](../評価考察_V3.0ハーネス死角フィードバックの客観的評価と改善設計案.md)

---

## 1. フェーズ目的

`EVAL-PL-002` で採択された3大対案（モック装着・排除の管理、証跡JSONの決定論的生成、ドキュメント精査の2段階分離と `REV-4` Pre-Review Gate 新設）の差分要件定義および基本設計仕様を確定し、正本設計書群（`docs/設計書/Current/`）および対象スクリプト改修仕様の整合性を精査する。

---

## 2. 実施タスクリスト

- [x] **T1-1: 差分要件の定義と採番 (`[REQ-*]`)**
  - 以下の3大要件を定義し、要件定義書（または本改訂計画）に反映する：
    - `[REQ-F-301-01]`: バックエンド・CLI本番コードにおけるモック生成識別子・ダミーメディア生成記述・例外フォールバックの機械的排除（`HG-002` 拡張）。
    - `[REQ-F-301-02]`: `qa_runtime_evidence.json` のエージェント手書き廃止、ツールによる署名付き自動生成、および `state_manager.py` における不在素通りバグ修正・チェックサム改ざん検証。
    - `[REQ-F-301-03]`: ドキュメント精査の2段階分離（`REV-3` 衛生整理 / `REV-5` 整合性精査）および `REV-4` 突入前物理検査コマンド（`state_manager.py verify-review-readiness`）の配備。
- [x] **T1-2: 改修スクリプトおよび規約テンプレートの差分設計**
  - `harness_guard.py`:
    - `HG-002`: 対象パスに `backend/`, `src-tauri/` を追加。正規表現に `generate_mock_*`, `testsrc`, `sine=`, `anoisesrc` を追加。
    - `HG-009`: `docs/設計書/Current/` のファイル名プレフィックス/サフィックス検査、一時ファイル（`*.bak`, `*draft*`）の排除、および `docs/設計書/` 直下の未整理ファイル検知を追加。
  - `traceability_checker.py`:
    - `--mode full` 成功時に `metrics/qa_runtime_evidence.json` を書き出すロジック（`.env` の `VITE_ENABLE_MOCK` 確認、`active_revision_id` 取得、SHA-256 チェックサム付与）を設計。
  - `state_manager.py`:
    - `cmd_verify_review_readiness` の設計（`harness_guard.py --all`、ドキュメント衛生、モック解除、最新証跡JSONの存在＆署名一致を一括チェック）。
    - `validate_revision_closure_invariants` の `else:` 欠落バグ修正とチェックサム再計算照合ロジックの設計。
  - 規約・スキル:
    - `rules/AGENTS.md`、`templates/システム改訂運用基準書.md`、`skills/dev-doc-reviewer/SKILL.md` の改定設計。
- [x] **T1-3: 基本設計レビュー (Approval Gate)**
  - 基本設計差分をレビューし、`traceability_checker.py --mode design` が 100% PASS することを確認する。

---

## 3. 完了判定条件（Exit Criteria）

- 差分要件（`REQ-F-301-01`〜`03`）が確定し、基本設計仕様が一意に定まっていること。
- 基本設計レビュー（`dev-review-arch`）が `PASS` であること。
