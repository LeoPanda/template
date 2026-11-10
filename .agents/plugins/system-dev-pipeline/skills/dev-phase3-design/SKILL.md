---
name: dev-phase3-design
description: "PHASE 3 基本設計書の自動作成および基本設計レビュー (dev-review-arch) ゲートへ接続するスキル。4大基本設計書を生成し、グランドデザイン新規格画面仕様書との整合性を保ち、指摘是正ループに対応する。"
---

# PHASE 3: 基本設計書の作成と設計レビュー連携

- **主担当エージェント**: 📐 設計・立案スペシャリスト (`architect`) (Model: `pro`)
- **画面仕様書担当**: 🎨 UI/UXデザイナー (`ui-designer`) (Model: `flash` / `pro`)
- **監査・レビュー担当**: 🛡️ 品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) (Model: `pro`)
- **委譲元 / 統括**: 👑 プロジェクトコンダクター (`conductor`)
- **完了ゲート**: 基本設計レビュー (`dev-review-arch`) 合格 (`PASS` または `CONDITIONAL PASS`) ＋ ユーザー承認必須

要件定義書および選定された展開プロファイルに基づき、基本設計書を作成・精査してください。

---

## 1. 担当設計書雛形の作成 & Executable Golden Fixtures 配置

1. **Executable Golden Fixtures 配置 (`tests/fixtures/golden/`)**:
   - 設計書本文への巨大サンプル直書き（トークン圧迫）を廃止し、期待入出力の具象サンプルを `tests/fixtures/golden/` 配下に実ファイル（例: `expected_output.json`, `expected_timeline.fcpxml`）として配置します。設計書からは相対リンクで参照します。
2. **4大基本設計書と画面振る舞い契約の策定**:
   - `docs/設計書/Current/技術要件定義書.md`: プロファイル適合構成、2段階行数制限、型自動同期、Aware UTC規約、標準コマンドシーケンス
   - `docs/設計書/Current/テーブルスキーマ定義書.md`: 生SQL手動DDL絶対禁止、Alembic前提、Aware UTC、Mermaid ER図
   - `docs/設計書/Current/ビジネスロジック仕様書.md`: 外部API二重キャッシュ、モック制御仕様、内部監視、Golden Fixtures 参照リンク
   - `docs/設計書/Current/画面仕様書.md`: 🎨 `ui-designer` が担当。グランドデザイン準拠、インタラクション4列契約テーブル（操作トリガー、呼び出しAPI/Payload、状態変化、エラー時挙動）を策定。

> [!IMPORTANT]
> - `architect` はいかなる場合も `run_command` を呼び出してはなりません。
> - `ui-designer` は画面仕様書作成時、テーブルスキーマ定義書のエンティティ名・カラム名・型定義とフォーム項目を完全一致させてください。

---

## 2. 基本設計レビュー (`dev-review-arch`) ゲート連携と是正ループ

1. 基本設計書および画面仕様書の作成完了後、コンダクターは 🛡️ `qa-engineer` に `dev-review-arch` を委譲します。
2. 🛡️ `qa-engineer` は二層構造（定常コア9項目 ＋ プロファイル適合監査、`traceability_checker.py --mode design`）で監査し、`docs/plans/基本設計レビュー結果報告書.md` を作成します。
3. **判定結果に応じたフロー**:
   - **`PASS` / `CONDITIONAL PASS`**: コンダクターは `python3 scripts/state_manager.py record-review --type arch --verdict PASS` を記録し、ユーザー承認を得て `python3 scripts/state_manager.py record-approval --phase PHASE_3` および `set-phase PHASE_4_IMPLEMENTATION` を実行して PHASE 4 へ進む。
   - **`REJECT`**: 📐 `architect` / 🎨 `ui-designer` へ是正が差し戻されます。指摘事項（250行制限未明記、生SQL残存、キャッシュ欠落、プロファイル不整合等）を修正し、再レビューを受けます。

---

## 3. 標準完了サマリの返却

作業完了後、呼び出し元エージェント（コンダクター）に対して、所定のフォーマットで完了サマリを返送してください。

```markdown
## 作業完了サマリ
- **担当エージェント**: architect
- **実施フェーズ / タスク**: PHASE 3 基本設計書作成
- **選定プロファイル**: Profile A (サーバーレス極小コストWeb型) / 等
- **ステータス**: SUCCESS / PENDING_USER_INPUT / FAILED
- **生成・更新ファイル一覧**:
  - docs/設計書/Current/技術要件定義書.md
  - docs/設計書/Current/テーブルスキーマ定義書.md
  - docs/設計書/Current/ビジネスロジック仕様書.md
- **設計の要点・特記事項**:
  - [定常コア9項目充足状況、Alembic前提、二重キャッシュ設計、モック制御仕様]
- **💡 獲得した知見・落とし穴 (Lessons Learned)**:
  - **事象**: [発生した課題・落とし穴（あれば、なければ「特になし」）]
  - **対策**: [回避策・推奨ルール]
  - **仕分け推奨**: Tier 1 (プロジェクト固有) / Tier 2 (全プロジェクト共通)
- **残課題 / Open Questions**:
  - [ユーザー確認が必要な事項（あれば）]
```
