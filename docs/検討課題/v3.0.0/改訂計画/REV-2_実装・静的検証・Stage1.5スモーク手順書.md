# REV-2: 実装・静的検証・Stage 1.5 スモーク手順書 (v3.0.0)

- **改訂依頼番号**: `v3.0.0` (`PLAN-V300-001`)
- **フェーズ**: `REV-2` (6段階標準改訂パイプライン 第2段階)
- **親計画書**: [00_v3.0.0改訂基本計画書.md](./00_v3.0.0改訂基本計画書.md)

---

## 1. フェーズ目的
確定した V3.0.0 仕様に基づき、コアスクリプト群（`traceability_checker.py`, `harness_guard.py`, `state_manager.py`）、ルール（`AGENTS.md`, `CORE_INVARIANTS.md`）、エージェント定義（5種）、スキル（19種）、テンプレート、スケルトン、および `doc_samples/`（10文書）を実装・更新し、静的検証ゲートを通過させる。

---

## 2. 実施タスクリスト

### 2.1 Track 1: コアスクリプト改修 & ミラー同期
- [ ] **`scripts/traceability_checker.py` の改修**:
  - `docs/plans/シナリオテスト計画書.md` の除外。
  - 有効テスト関数スコープ（Python AST / TS・JS・Rust テストブロック＋直上コメント）直結の `[REQ-*]` バインド実装。
  - 浅いアサーション（`toBeInTheDocument()` のみで状態遷移・副作用検証がないテスト）の検知・除外。
  - `--coverage-json` による動的カバレッジ閾値検証の追加。
- [ ] **`scripts/harness_guard.py` の改修**:
  - `HG-001` の2段階緩衝帯化（FE: 251〜350行 `WARN` / 351行〜 `BLOCK`、BE: 401〜550行 `WARN` / 551行〜 `BLOCK`）。
  - `HG-010`（明白な空実装・`NotImplementedError` 放置・ダミーコメント返却・空イベントハンドラ遮断）の実装。
  - `HG-011`（Path-Based Scope Guard：非開発モード・改訂未起票時のシステム本体コード変更遮断 / `PAT-SYS-016`）の実装。
- [ ] **`scripts/state_manager.py` の改修**:
  - `schema_version: "3.0.0"`, `capability_traits`, `session_mode` の追加と `set-mode` / `set-traits` 実装。
  - `start-revision` における `session_mode = "DEV_PIPELINE"` 自動昇格と `REV-1`〜`REV-6`（6段階）計画スケルトン自動生成。
  - `record-approval --phase REV_4` によるユーザー実機レビュー承認記録。
  - `validate_revision_closure_invariants()` への `[INV-REV-04]`（`REV-4` ユーザー承認必須）および `[INV-QA-01]`（`qa_runtime_evidence.json` 検証）の追加。
- [ ] **`skeletons/common/scripts/` へのミラーコピー**:
  - 上記3スクリプトを `skeletons/common/scripts/` へ完全同期。

### 2.2 Track 2 & 3: ルール・エージェント・全19スキルの更新
- [ ] `.agents/plugins/system-dev-pipeline/rules/AGENTS.md`（上限220行厳守）および `rules/CORE_INVARIANTS.md` の V3.0.0 更新（`PAT-SYS-015`, `PAT-SYS-016`, `REV-1`〜`REV-6` 統合）。
- [ ] `.agents/plugins/system-dev-pipeline/agents/*.md`（全5種、上限120行厳守）の更新。
- [ ] `.agents/plugins/system-dev-pipeline/skills/*/SKILL.md`（全19種、上限120行厳守）の更新。

### 2.3 Track 4: テンプレート・スケルトン・`doc_samples/` の更新
- [ ] `templates/システム改訂運用基準書.md` の `REV-1`〜`REV-6` 化。
- [ ] `templates/project_state.schema.json` および設計書・レビュー報告書テンプレートの V3.0.0 更新。
- [ ] `doc_samples/` 全10文書の V3.0.0 仕様同期。

---

## 3. 完了判定条件（Exit Criteria）
- `python3 .agents/plugins/system-dev-pipeline/scripts/harness_guard.py --all` が BLOCK 0件で PASS すること。
- `bash .agents/plugins/system-dev-pipeline/scripts/pipeline-reconciler.sh --audit-budget` が全ファイル行数上限以内・Lineage 混入 0件で PASS すること。
