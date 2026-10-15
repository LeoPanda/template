---
name: dev-review-arch
description: "PHASE 3 完了ゲートにおいて基本設計書群を多角的に監査し、定常コア8項目および展開プロファイル別観点からレビュー結果報告書を作成するスキル。"
---

# 基本設計レビュー (Basic Design Review) スキル V2.2

- **主担当エージェント**: 🛡️ 品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) (Model: `pro`)
- **委譲元 / 統括**: 👑 プロジェクトコンダクター (`conductor`)
- **適用フェーズ**: PHASE 3 完了ゲート
- **合否判定ゲート**: `PASS` または `CONDITIONAL PASS` で PHASE 4 へ進行可能。`REJECT` の場合は 📐 `architect` / 🎨 `ui-designer` へ是正差し戻し。

---

## 1. 入力ドキュメント
監査対象として以下のドキュメントを読み込みます：
- `docs/要件定義書.md`（選定されたシステム展開プロファイル: Profile A〜D）
- `docs/技術要件定義書.md`
- `docs/テーブルスキーマ定義書.md`
- `docs/ビジネスロジック仕様書.md`
- `docs/画面仕様書.md`

---

## 2. 監査観点（2層型レビューアーキテクチャ V2.2）

### 第1層: 定常的コア設計規範 (Universal Core Criteria - 全システム共通8項目)
1. **フロントエンド責務分離構造 (Anti-God Component)**:
   - 1ファイル最大250行制限、Custom Hooks/Servicesへの物理分離方針が明記されているか。
2. **型定義自動同期パイプライン**:
   - `openapi-typescript`（`npm run codegen:types`）による自動同期が設計されているか。手動二重定義を排除しているか。
3. **環境変数・シークレット厳格バリデーション**:
   - Pydantic Settings による起動時型検証およびプレースホルダー即死ガードレールが明記されているか。
4. **統一タイムゾーン運用**:
   - DB内部およびAPI通信は Aware UTC (ISO8601)、UI表示時のみ JST 変換する規約が徹底されているか。
5. **自動CIワークフロー**:
   - GitHub Actions CI による Lint, 型チェック, 単体・スモークテスト自動実行が設計されているか。
6. **構造化ロギング & クラッシュ耐性**:
   - JSTタイムスタンプおよび UUIDv4 `log_id` 自動バインド方針が明記されているか。
7. **モック制御アダプター層 (案C＋案A)**:
   - 環境変数 `VITE_ENABLE_MOCK` による明示的切替と、コンポーネント内直書きモックの原則禁止が明記されているか。
8. **画面グランドデザイン基礎規範**:
   - 4px/8px グリッド体系、HEX/px絶対値併記、ウィンドウ形態選定基準が画面仕様書に反映されているか。

### 第2層: システム展開プロファイル別適合監査
- **Profile A (サーバーレス極小コストWeb型 / ゴールデンパス)**:
  - Cloud Run `max-instances=1` 制約の記載があるか。
  - **Alembic マイグレーション前提**（生SQL手動DDLの完全禁止、`alembic upgrade head` 起動適用）が明記されているか。
  - **IAP JWT 署名二重検証ミドルウェア**（`core/auth.py`）の設計があるか。
  - 外部API二重キャッシュ戦略（TTLメモリ＋DB）が記載されているか。
  - 内部監視エンドポイント（`health`, `litestream`）が定義されているか。
- **Profile B (Web SSR / フルマネージドRDB型)**:
  - 水平スケーラビリティ、完全RDBトランザクション、SSRハイドレーション配慮。
- **Profile C (静的MPA / 超軽量ツール型)**:
  - 単一プロセス完結性、最小依存、HTMX遷移設計。
- **Profile D (PCローカルデスクトップアプリ型)**:
  - Frameless TitleBar セーフエリア設計、最小ウィンドウサイズ制約、IStorageAdapter / IRepository 抽象化。

---

## 3. レビュー結果の作成と判定

監査結果を `docs/plans/基本設計レビュー結果報告書.md` に出力します。

### 合否判定基準:
- **`PASS`**: 重大欠陥（Critical / High）が0件、かつMediumが軽微。
- **`CONDITIONAL PASS`**: Medium以下の指摘のみで、実装フェーズ中の対応方針が明確である場合。
- **`REJECT`**: Critical（定常コア8項目の重大欠落、生SQL前提、IAP検証漏れ、SPOF等）または High が1件以上存在。

---

## 4. 標準完了サマリの返却

コンダクターへ以下の形式でサマリを返送してください。重大な設計課題を発見した場合は、`wiki-maintainer` によるRCA記録も実施してください。

```markdown
## 作業完了サマリ
- **担当エージェント**: qa-engineer
- **実施フェーズ / タスク**: PHASE 3 基本設計レビュー (`dev-review-arch`)
- **選定プロファイル**: Profile A / 等
- **判定結果**: PASS / CONDITIONAL PASS / REJECT
- **生成ファイル**: docs/plans/基本設計レビュー結果報告書.md
- **定常コア8項目監査結果**: PASS (全8項目適合) / 要是正
- **指摘概要**:
  - Critical: X件
  - High: Y件
  - Medium/Low: Z件
- **主な指摘事項**:
  - [指摘内容と修正推奨案]
- **💡 獲得した知見・落とし穴 (Lessons Learned)**:
  - **事象**: [設計上のアンチパターンや落とし穴（あれば）]
  - **対策**: [推奨ルール]
  - **仕分け推奨**: Tier 1 / Tier 2
- **次のアクション**: [PASSならPHASE 4着手、REJECTならarchitect是正]
```
