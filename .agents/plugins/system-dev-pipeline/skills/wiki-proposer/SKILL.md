---
name: wiki-proposer
description: "PHASE 8 において Tier 2 汎用Wikiパターンから行番号非依存の標準化知見原票 (CLAIM-*.md) を生成し、Central Knowledge Hub (~/.gemini/knowledge-hub/inbox/) への投函と提示サマリ更新を行うスキル。"
---

# 標準化知見原票起案・投函 (wiki-proposer) スキル V2.3

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **委譲先 (監査時)**: 🛡️ 品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) (Semantic Auditor)
- **適用フェーズ**: PHASE 8 (知見昇格フェーズ) および システム改訂完了時

---

## 1. 入力情報
- `./wiki/patterns/universal/` 配下の汎用知見パターン群（Tier 2、未昇格のもの）
- 現行のパイプライン資産（`rules/AGENTS.md`, `rules/CORE_INVARIANTS.md`, `skills/*/SKILL.md`）
- `PROJECT_STATE.md`（プロジェクト名、選定プロファイル、`EXECUTION_MODE`）

---

## 2. V2.3 における重要原則（Patch-Free & State/Lineage 分離）
1. **Unified Diff（`.patch`）および個別 `PURPOSE.md` 生成の完全廃止**:
   - 行番号ズレによる競合（Hunk Conflict）と管理分散を根絶するため、`.patch` ファイルや `skills/*/PURPOSE.md` は一切生成しない。
2. **標準化知見原票（Knowledge Claim MD）への統一**:
   - すべての Tier 2 知見は、セマンティック・アンカー（対象ファイル名＋セクション見出し＋統合種別）を持つ自己完結型の Markdown 原票 `CLAIM-{YYYYMMDD}-{PROJECT_SLUG}-{PAT_ID}.md` として生成する。
3. **コンテキスト純度（State と Lineage の完全分離）**:
   - 原票内の「セクション3: 抽象化された処方箋・推奨ルール」には、プロジェクト固有名詞やパターンID・原票ID等の履歴記述を一切含めない純粋な規範文のみを記述する。

---

## 3. 処理手順

### Step 1: パターンの蒸留と一般化 (Spoke Gate)
`./wiki/patterns/universal/` の Tier 2 パターンを精査し、特定案件のディレクトリ名・テーブル名・固有API名などの固有名詞を排除して、全案件（または該当プロファイル全般）で通用する抽象ルールへと蒸留する。

### Step 2: 標準化知見原票 (`CLAIM-*.md`) の生成と投函
以下の標準フォーマットに従い、`./promotions/CLAIM-{YYYYMMDD}-{PROJECT_SLUG}-{PAT_ID}.md` に控えを出力するとともに、環境共通の `~/.gemini/knowledge-hub/inbox/`（未初期化の場合は `pipeline-reconciler.sh --init-hub` を実行）へ投函（コピー）する。

```markdown
---
schema_version: "2.3.0"
claim_id: "CLAIM-{YYYYMMDD}-{PROJECT_SLUG}-{PAT_ID}"
pattern_id: "{PAT_ID}"
title: "知見タイトル"
created_at: "YYYY-MM-DDTHH:MM:SS+09:00"
source_project_profile: "Profile A"
applicable_profiles: ["ALL"]
category: "SYS"
severity: "HIGH"
target_candidates:
  - file: "rules/AGENTS.md"
    section_anchor: "## 対象セクション見出し"
    integration_type: "SUBSUMPTION" # SUBSUMPTION / SCOPED_BRANCH / NEW_RULE
status: "INBOX_PENDING"
consolidated_from: []
---

# 知見タイトル

## 1. 発生コンテキストと前提条件 (Context & Preconditions)
- 発生フェーズ・技術環境・適用スコープ条件

## 2. 事象と根本原因分析 (Problem & Root Cause Analysis)
- 発生事象と根本原因 (RCA)

## 3. 抽象化された処方箋・推奨ルール (Distilled Prescription)
- [固有名詞・履歴IDを一切含まない、パイプライン文書または Local Overlay へそのまま統合可能な簡潔な規範文]

## 4. 既存ルールとの意味的関係・統合指針 (Semantic Integration Guide)
- コア不変原則（INV-01〜10）との整合性および既存文面へのインプレース統合方針

## 5. 検証エビデンス (Verification Evidence)
- 解消・再現確認結果
```

### Step 3: 提示サマリ `./TEMPLATE_PROMOTIONS.md` の更新
ユーザーが昇格採否を判断できるよう、生成した原票ID、対象アンカー、統合種別、処方箋要約を `./TEMPLATE_PROMOTIONS.md` に記録する。

### Step 4: 🛡️ qa-engineer による 3段階意味的整合性監査（新・複合検証ゲート）の呼び出し
投函した原票に対し、🛡️ `qa-engineer` へ新・複合検証ゲート（Gate 1: コア不変原則監査、Gate 2: 4分類相互矛盾監査、Gate 3: 過剰適合・アンカー実在検証、Gate 4: 純度・絶対行数バジェット検証）の実行を委譲し、監査結果を受けてコンダクターが `ask_question` モーダルでユーザー承認を仰ぐ。
