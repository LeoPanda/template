# REV-6: メトリクス・知見昇格・リリース手順書 (v3.1.0)

- **改訂依頼番号**: `v3.1.0` (`PLAN-V310-001`)
- **フェーズ**: `REV-6` (6段階標準改訂パイプライン 最終段階)
- **親計画書**: [00_v3.1.0改訂基本計画書.md](./00_v3.1.0改訂基本計画書.md)
- **前フェーズ**: [REV-5_本番総合監査・成果物ビルド手順書.md](./REV-5_本番総合監査・成果物ビルド手順書.md)

---

## 1. フェーズ目的

改訂ライフサイクル全体の定量メトリクスを集計し、知見昇格原票を Central Knowledge Hub へ投函する。さらに、5大不変条件（Invariants Gate）を機械検証して改訂を正式クローズし、Git 本番リリースと既存プロジェクト（Movie Log 等）への移行案内ガイドを整備する。

---

## 2. 実施タスクリスト

- [x] **T6-1: 定量メトリクス集計 (dev-metrics-collector)**
  - 改訂にかかったトークン数、ツール実行回数、改修所要時間、テスト反復回数を機械集計し、健全性レポートを出力する。
- [x] **T6-2: 標準化知見の昇格 (CLAIM 原票投函)**
  - 本改訂（テストフィクスチャマスキングの教訓、Live Invariant Probe の設計、環境自己適応パターン）から得られた汎用知見を標準化原票（`CLAIM-*.md`）として Central Knowledge Hub（`~/.gemini/knowledge-hub/inbox/`）へ投函する。
- [x] **T6-3: 改訂クローズ Invariants Gate の機械検証**
  - `python3 scripts/state_manager.py complete-revision` を実行し、以下の 5大不変条件がすべて満たされていることを機械検証する：
    1. 成果物実在（ビルドパッケージ・スケルトン）
    2. 定量メトリクス算出済み
    3. 未処理知見原票ゼロ
    4. **REV-4 ユーザー実機承認記録済み (`review_approved_at`)**
    5. **最新の `qa_runtime_evidence.json` 検証済み**
- [x] **T6-4: Git 本番リリース (dev-git-release)**
  - `feature/v3.1.0` ブランチを `main` へ Merge Squash し、バージョンタグ `v3.1.0` を付与して Commit & Push を実行する。
- [x] **T6-5: 既存プロジェクト（Movie Log等）向け移行ガイドの配置**
  - 本流で実装された `state_manager.py` および共通スケルトンの更新内容を、障害が発生した Movie Log 等の既存プロジェクトへスムーズに適用・移行するための「v3.1.0 移行実践ガイド」を作成・配置する。

---

## 3. 完了判定条件（Exit Criteria）

- `state_manager.py complete-revision` が正常終了し、台帳の `active_revision_id` がクリアされていること。
- Git 本番リリース（タグ `v3.1.0`）が完了していること。
- 既存プロジェクト向け移行ガイドが配備されていること。
