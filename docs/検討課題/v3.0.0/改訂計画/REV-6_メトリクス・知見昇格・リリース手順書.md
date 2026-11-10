# REV-6: メトリクス・知見昇格・リリース手順書 (v3.0.0)

- **改訂依頼番号**: `v3.0.0` (`PLAN-V300-001`)
- **フェーズ**: `REV-6` (6段階標準改訂パイプライン 第6段階 ※旧 `REV-5` からシフト)
- **親計画書**: [00_v3.0.0改訂基本計画書.md](./00_v3.0.0改訂基本計画書.md)

---

## 1. フェーズ目的
Central Knowledge Hub の Upgrade Reconciler を実行して Overlay 知見（`PAT-SYS-015`, `PAT-SYS-016`）を正式に `archive/upstreamed/` へ退役させ、ローカルオーバーレイ（`LOCAL_FEEDBACK_RULES.md`）をクリーン化した上で、グローバル環境（`~/.gemini/config/plugins/system-dev-pipeline`）へのデプロイ同期および Git リリースを完了する。

---

## 2. 実施タスクリスト

- [x] **T6-1: Central Knowledge Hub Upgrade & Overlay クリーンリセット**
  - `bash .agents/plugins/system-dev-pipeline/scripts/pipeline-reconciler.sh --upgrade` を実行。
  - `active_claims/CLAIM-20261107-promotion-video-maker-PAT-SYS-015.md` および `active_claims/CLAIM-20261109-promotion-video-maker-PAT-SYS-016.md` が ID一致（Pattern A）により `archive/upstreamed/` へ自動退役し、`~/.gemini/knowledge-hub/overlay/LOCAL_FEEDBACK_RULES.md` がアクティブ 0 件の初期状態にクリーン再生成されたことを確認。
- [x] **T6-2: グローバル環境へのデプロイ同期 (`template-pipeline-sync`)**
  - ユーザー承認のもと、`bash .agents/skills/template-pipeline-sync/scripts/sync_pipeline.sh --deploy` を実行。
  - 再診断レポートが **`🎉 判定結果: [SYNCED]`**（Global ⇔ Workspace 差分 0件、未本流化知見 0件）となり、`.git/pipeline_sync_stamp` が更新されたことを確認。
- [x] **T6-3: Git コミット & リリース**
  - 変更差分および `.env` (`APP_VERSION=3.0.0`) を確認し、ユーザーの明示的指示に従って Git コミット・リリースを実施。

---

## 3. 完了判定条件（Exit Criteria）
- `pipeline-reconciler.sh --status` において `active_claims: 0件`, `inbox: 0件`, `Immutable Core Version: 3.0.0 (吸収済パターン: 32件)` となっていること。
- `sync_pipeline.sh --status` が `[SYNCED]`（終了コード 0）を返すこと。
