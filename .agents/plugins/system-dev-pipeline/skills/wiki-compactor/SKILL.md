---
name: wiki-compactor
description: "PHASE 8 または定期保守時において、プロジェクト内Wikiパターンの重複排除・アーカイブ、および Central Knowledge Hub の inbox 原票クラスタリング・Local Overlay 圧縮を行うスキル。"
---

# Wiki枝刈り・原票クラスタリング・Overlay圧縮 (wiki-compactor) スキル V2.3

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **適用フェーズ**: PHASE 8 完了時、Knowledge Hub 監査前、または定期保守時
- **対象領域**:
  1. プロジェクトローカルの `./wiki/` 配下（Spoke Wiki）
  2. 環境共通ナレッジハブ `~/.gemini/knowledge-hub/` 配下（Central Knowledge Hub）

---

## 1. 目的
蓄積された知見（Wikiパターンおよび Knowledge Hub 原票）が増大すると、重複提案やローカルオーバーレイ（`LOCAL_FEEDBACK_RULES.md`）の行数バジェット超過が生じます。`wiki-compactor` は Spoke と Hub の双方を整理・圧縮し、コンテキスト純度と検索性を維持します。

---

## 2. 処理手順

### Step 1: Spoke 内 `./wiki/patterns/` の重複統合とアーカイブ
1. **重複パターンの統合 (Merge)**:
   - `./wiki/patterns/` 配下を走査し、類似した根本原因や同一の解決策を持つパターンを単一の包括的パターンへ統合する。
2. **陳腐化・正本化済みパターンのアーカイブ (Archive)**:
   - 既に `./docs/` へ逆同期して正本化が完了した Tier 1 パターンや、フレームワーク更新等で無効化されたパターンを `./wiki/archive/` へ移動する。
3. **台帳整合性の修復 (Reconcile)**:
   - `./wiki/logs.md` および `./wiki/skill-impact.md` のステータスを `[Archived]` または `[Merged]` に更新する。

### Step 2: Hub 内 `~/.gemini/knowledge-hub/inbox/` の事前原票クラスタリング
1. 複数のプロジェクトから `~/.gemini/knowledge-hub/inbox/` に投函された未処理原票（`CLAIM-*.md`）をスキャンする。
2. 同一カテゴリ・同一アンカー・同一原因に対する類似原票が複数存在する場合は、YAML Frontmatter の `consolidated_from` リストに元の原票ID群を記録した上で、1枚の集約知見原票（Consolidated Claim MD）へ束ね、統合元の重複原票を `archive/` へ退避する。

### Step 3: Local Overlay (`LOCAL_FEEDBACK_RULES.md`) のバジェット監視と圧縮
1. `bash .agents/plugins/system-dev-pipeline/scripts/pipeline-reconciler.sh --status`（またはグローバルスクリプト）を実行し、`~/.gemini/knowledge-hub/overlay/LOCAL_FEEDBACK_RULES.md` の行数を確認する。
2. 行数が絶対上限（**80行**）の 80%（64行）を超えている場合、`active_claims/` 内の同カテゴリ原票をより上位の汎用原則へ再蒸留して統合するか、ユーザーへテンプレート本流（Immutable Core）への昇格コンパイルを案内する。
3. 統合後は `pipeline-reconciler.sh --rebuild-overlay` を実行してクリーンに再生成する。

---

## 3. 完了報告
整理作業完了後、以下の情報をユーザーへ報告します：
- Spoke 内：統合・アーカイブしたパターン数と現在の有効パターン総数（Tier 1 / Tier 2）
- Hub 内：クラスタリング集約した `inbox/` 原票数、および `LOCAL_FEEDBACK_RULES.md` の現在行数（/ 80行）
