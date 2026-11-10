# REV-5: 本番総合監査・成果物ビルド手順書 (v3.0.1)

- **改訂依頼番号**: `v3.0.1` (`PLAN-V301-001`)
- **フェーズ**: `REV-5` (6段階標準改訂パイプライン 第5段階)
- **親計画書**: [00_v3.0.1改訂基本計画書.md](./00_v3.0.1改訂基本計画書.md)

---

## 1. フェーズ目的

`REV-4` の実機テストレビューおよび対話的改修で発生した仕様・UI・ロジックの変更を正本設計書群へ完全反映し、**「第2段階：ドキュメント内容・相互整合性精査 (`dev-doc-reviewer`)」**、コード品質監査（`dev-review-code`）、およびシステム総合監査（`dev-review-system`）を実施して配布成果物を確定させる。

---

## 2. 実施タスクリスト

- [x] **T5-1: 第2段階：ドキュメント内容・相互整合性精査 (Semantic Cross-Check)**
  1. `REV-4` の対話的改修で生じた仕様・コードの変更差分を、`docs/設計書/Current/` 配下の関連設計書へ漏れなく逆反映する。
  2. 🛡️ `qa-engineer` が `dev-doc-reviewer` を実行し、要件定義 ⇔ 4大基本設計書 ⇔ 実装コード間の矛盾・誤植・説明不足を多次元クロスチェックし、自律修復（ヘッダーSemVer統一等）を実施。**判定: PASS (完全整合)**。
- [x] **T5-2: コード品質レビュー (`dev-review-code`)**
  - 🛡️ `qa-engineer` がコード全域を監査し、2段階行数制限の遵守、プレースホルダーや縮退実装の不在、モック混入ゼロを確認し、**`CLEAN` (合格)** 判定を獲得。
- [x] **T5-3: システム総合レビュー (`dev-review-system`)**
  - 本番モックOFF二重防御、IAP JWT有効化、平文シークレットゼロ、署名付き `qa_runtime_evidence.json` の適合性を監査し、**`RELEASE APPROVED` (リリース承認)** 判定を獲得。
- [x] **T5-4: スケルトン完全同期 & プラグイン確定**
  - `.agents/plugins/system-dev-pipeline/scripts/` と `skeletons/common/scripts/` のスクリプト群が `diff -u` で完全一致（差分0）であることを確認。
  - `.agents/plugins/system-dev-pipeline/plugin.json` および `PIPELINE_MANIFEST.json` のバージョンが `"3.0.1"` に更新されていることを確認。

---

## 3. 完了判定条件（Exit Criteria）

- ドキュメント相互整合性チェック（`dev-doc-reviewer`）がエラー 0 件で完了していること。
- `dev-review-code`（`CLEAN`）および `dev-review-system`（`RELEASE APPROVED`）が合格していること。
- スケルトンとの完全一致が確認されていること。
