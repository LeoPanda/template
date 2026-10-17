---
name: wiki-maintainer
description: "テスト失敗、レビュー指摘、自律修復発生時の根本原因分析（RCA）を実施し、プロジェクトローカルの wiki/patterns/ へ知見を永続化するスキル。"
---

# Wiki知見永続化・RCA (wiki-maintainer) スキル V2.3

- **主担当エージェント**: 🛡️ 品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) (Model: `pro`)
- **委譲元 / 統括**: 👑 プロジェクトコンダクター (`conductor`)
- **適用契機**: 設計レビュー不合格、コード品質指摘、テスト失敗、自律修復ループ発生時
- **厳格な記録境界ガードレール**: **知見の一次記録先は必ずプロジェクトローカルの `./wiki/` 配下に限定する。** グローバル領域や `~/.gemini/knowledge-hub/` への直接書き込みは本スキルでは絶対に行わない。

---

## 1. 入力情報
- エラーログ、スタックトレース、テスト失敗出力
- レビュー結果報告書（不合格要因、指摘箇所）
- 試行錯誤履歴、環境設定やライブラリのトラップ、選定プロファイル（Profile A〜D）

---

## 2. 処理手順

### Step 1: 根本原因分析 (RCA - Root Cause Analysis)
表層のエラーメッセージだけでなく、「なぜ発生したか」「どのような設計・実装・環境の落とし穴があったか」を掘り下げて特定する。

### Step 2: 二層分離（Two-Tier Separation）の仕分け判定
獲得した知見を以下の2つの層に厳格に分類する：

1. **Tier 1: プロジェクト固有仕様 (Local Domain / Specs)**
   - 業務ロジックの特殊仕様、個別画面の特有制約、対象システムの個別DB定義など。
   - 配置先: `./wiki/patterns/local/PAT-LOC-xxx_{識別名}.md`
   - **正本化フロー**: 各フェーズ完了ゲートにおいて `./docs/`（仕様書・設計書）および `./PROJECT_STATE.md` へ逆同期して案件内で完結させる（中央の Knowledge Hub へは持ち出さない）。
2. **Tier 2: 汎用パターン・共通落とし穴 (Universal Patterns / Pitfalls)**
   - フレームワーク挙動、Docker/コンテナ仕様、型安全性、共通テスト手順、エージェント行動規範など他案件でも再利用すべき汎用知見。
   - 配置先: `./wiki/patterns/universal/PAT-{CAT}-xxx_{識別名}.md` (`CAT`: `ARCH`, `CODE`, `TEST`, `ENV`, `SEC`, `SYS`)
   - **昇格フロー**: PHASE 8 において `wiki-proposer` が読み込み、標準化知見原票（`CLAIM-*.md`）へ変換して `~/.gemini/knowledge-hub/inbox/` へ投函する。

### Step 3: パターンファイルの作成・記録 (V2.3 拡張フォーマット)
PHASE 8 で標準化知見原票へシームレスに変換できるよう、発生プロファイル・適用対象プロファイル・統合候補アンカーを含めて生成する。

```markdown
# パターン概要タイトル

- **Pattern ID**: PAT-{CAT}-xxx
- **作成日**: YYYY-MM-DD
- **知見スコープ**: Tier 1 (プロジェクト固有 / Local) / Tier 2 (テンプレート共通 / Universal)
- **発生プロファイル**: [Profile A / Profile B / Profile C / Profile D / ALL]
- **適用対象プロファイル**: [ALL / Profile A / Profile D 等]
- **カテゴリ**: [ARCH / CODE / TEST / ENV / SEC / SYS]
- **重大度**: [CRITICAL / HIGH / MEDIUM / LOW]
- **ステータス**: Active
- **統合候補アンカー (Tier 2 の場合)**:
  - `rules/AGENTS.md` (`## 対象セクション見出し`)
  - `skills/対象スキル名/SKILL.md` (`## 対象セクション見出し`)

## 1. 発生状況・前提条件 (Context & Preconditions)
- 発生フェーズ・技術環境・適用スコープ条件

## 2. 現象・根本原因 (Problem & Root Cause Analysis)
- 発生事象の要約と真の根本原因 (RCA)

## 3. 抽象化された処方箋・推奨ルール (Distilled Prescription)
- プロジェクト固有名詞や履歴IDを含まない、汎用かつ簡潔な再発防止ルール文
```

### Step 4: 台帳ファイルの更新
- `./wiki/logs.md`: 発生事象、作成パターンID、仕分け結果を時系列で追記。
- `./wiki/skill-impact.md`: 影響するスキルや統合候補アンカーを記録。

---

## 3. 標準完了サマリの返却

コンダクターへ以下の形式でサマリを返送してください。

```markdown
## 作業完了サマリ
- **担当エージェント**: qa-engineer
- **実施フェーズ / タスク**: Wiki知見永続化・RCA (`wiki-maintainer`)
- **分類結果**: Tier 1 (local) / Tier 2 (universal)
- **保存先パス**: ./wiki/patterns/...
- **適用対象プロファイル**: [ALL / Profile A 等]
- **根本原因 (RCA) と処方箋概要**:
  - [エラーの根本原因と抽象化された再発防止策]
- **台帳更新**: ./wiki/logs.md, ./wiki/skill-impact.md 更新完了
```
