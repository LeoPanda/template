# WikiSkill 統合設計書 (WikiSkill Integration Architecture Specification)

文書バージョン: 2.3  
作成日: 2026-10-10  
改訂日: 2026-10-18  
対象バージョン: AI駆動システム開発ライフサイクルテンプレート V2.3  
ステータス: 正式改訂版 (V2.3 Central Knowledge Hub・二段階進化・3段階意味的監査統合版)  
関連文書:
- [V2.3新知見フィードバック機構設計書.md](./V2.3新知見フィードバック機構設計書.md)
- [V2.3改変計画書.md](./V2.3改変計画書.md)
- [テンプレート配置形態およびナレッジ境界設計書.md](./テンプレート配置形態およびナレッジ境界設計書.md)
- [エージェント間知見蓄積運用基準書V2.3.md](./エージェント間知見蓄積運用基準書V2.3.md)
- [定量測定・フィードバック設計書.md](./定量測定・フィードバック設計書.md)
- [AI駆動システム開発フェーズ定義書V2.3.md](./AI駆動システム開発フェーズ定義書V2.3.md)
- [知見フィードバック機構の高度化と一元管理・監査・配布に関する検討課題.md](../../検討課題/V2.3/知見フィードバック機構の高度化と一元管理・監査・配布に関する検討課題.md)
- [wikiskill.md](../../検討課題/V2.1/wikiskill.md)

---

## 1. はじめに

### 1.1 背景と課題認識
AI駆動システム開発ライフサイクルにおいては、コンダクター（Main）、設計（`architect`）、バックエンド（`backend-engineer`）、UI（`ui-designer`）、QA（`qa-engineer`）の5大エージェント協調体制と状態管理機構（`PROJECT_STATE.md`）により、高度な自律開発パイプラインが実現されている。

V2.1 において Google Research および Virginia Tech が提唱した **WikiSkill** アーキテクチャ（[wikiskill.md](../../検討課題/V2.1/wikiskill.md)）を導入し、「ロールバックに伴う知見喪失（Catastrophic Forgetting）」と「推論時のコンテキスト汚染（Overfitting）」を解決する永続 Wiki 層を確立した。さらに V2.3 では、複数プロジェクト・複数環境での長期運用において顕在化した以下の **3つの構造的摩擦** を解消するため、**Central Knowledge Hub（`~/.gemini/knowledge-hub/`）および「Immutable Core ＋ Local Overlay」モデル**との完全統合を行った（詳細は [V2.3新知見フィードバック機構設計書.md](./V2.3新知見フィードバック機構設計書.md) 第6章を参照）：

1. **複数案件からのパッチ競合と分散環境の更新衝突**:
   - 行番号依存の `.patch` 出力や公式プラグイン直接書き換えを廃止し、セマンティック・アンカー付きの **「標準化知見原票（Knowledge Claim MD: `CLAIM-*.md`）」** による環境共通 Inbox 集約と、公式コアを汚さない **Local Overlay（`LOCAL_FEEDBACK_RULES.md`）への即時反映** へ進化させた。
2. **PHASE 8 複合検証ゲート（Gating）の検証対象ミスマッチ解消**:
   - PHASE 8 時点で既に完成しているアプリケーションの Linter や E2E テストを回す形骸化したゲートを廃止し、**「知見原票とパイプライン定義文書の意味的整合性（Core Invariants・4分類矛盾監査）およびコンテキスト純度・絶対行数バジェット」を検査する4大関門** へ刷新した。
3. **履歴追記によるプロンプト汚染と `PURPOSE.md` 分散ドリフトの解消**:
   - `SKILL.md` や `rules/AGENTS.md` 本文への `[PAT-xxx]` 等の履歴ID追記を全面禁止（State と Lineage の完全分離）し、各スキル直下に分散していた `PURPOSE.md` を廃止して **`FEEDBACK_LEDGER.md` および `PIPELINE_MANIFEST.json` へ一元統合** した。

### 1.2 目的と位置付け
本文書は、個別開発プロジェクト（Spoke）と環境共通ナレッジハブ（Hub）、および公式配布プラグイン（Immutable Core）を貫く **V2.3 WikiSkill 二段階進化・三層ストレージアーキテクチャ** の完全な設計仕様を定義するものである。

---

## 2. WikiSkill 統合アーキテクチャの全容（V2.3 Spoke-Hub-Core モデル）

### 2.1 3層ストレージモデルと Spoke / Hub / Core 境界定義
V2.3 における WikiSkill アーキテクチャは、データの性質に応じた3つのレイヤー（Raw / Wiki & Hub / Effective Skills）を、個別案件（Spoke）から環境共通ハブ（Hub）、テンプレート正本（Core）へとつなぐ多段構造で管理する。

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    V2.3 WikiSkill 3層ストレージ & 二段階進化アーキテクチャ             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [1. Raw Layer (実行ログ層 - Spoke Project)]                                           │
│    ・格納先: <project-root>/.system_generated/logs/, docs/plans/scenario-test/         │
│    ・特性:   完全イミュータブル（追記のみ、変更・削除不可）                            │
│    ・内容:   ReAct推論トレース、ツール入出力、テスト実行結果ログ                       │
│                                                                                        │
│                              │ サンプリング & 根本原因分析 (RCA: wiki-maintainer)      │
│                              ▼                                                         │
│  [2. Wiki & Knowledge Hub Layer (永続ナレッジ層 - 決してロールバックされない永続層)]   │
│    ◆ Spoke Wiki (<project-root>/wiki/):                                                │
│      ・patterns/local/ (Tier 1: 案件固有) ──► ./docs/ & PROJECT_STATE.md へ逆同期完結  │
│      ・patterns/universal/ (Tier 2: 汎用) ──► PHASE 8 で標準原票 CLAIM-*.md へ蒸留     │
│    ◆ Central Knowledge Hub (~/.gemini/knowledge-hub/):                                 │
│      ・inbox/ (未処理原票キュー), active_claims/ (適用中), archive/upstreamed/ (吸収済)│
│      ・rejected/ (監査不合格・棄却理由の永続記録), suspended/ (仕様衝突保留)           │
│      ・LOCAL_HUB_STATE.json (ローカルOverlay状態・履歴マニフェスト)                    │
│                                                                                        │
│                              │ 3段階意味的整合性監査 (Semantic Auditor) & 蒸留         │
│                              ▼                                                         │
│  [3. Effective Skills & Rules Layer (実行手順・規約層 - StateとLineageの完全分離)]     │
│    ◆ Layer 3-A: Local Overlay (~/.gemini/knowledge-hub/overlay/)                       │
│      ・LOCAL_FEEDBACK_RULES.md (上限80行: 当該PC環境の次案件から即時有効化)            │
│    ◆ Layer 3-B: Immutable Core (~/.gemini/config/plugins/system-dev-pipeline/)         │
│      ・rules/AGENTS.md (上限220行), rules/CORE_INVARIANTS.md (不変原則 INV-01〜10)     │
│      ・agents/*.md (上限120行), skills/*/SKILL.md (上限120行) ※履歴ノイズゼロ          │
│      ・PIPELINE_MANIFEST.json & FEEDBACK_LEDGER.md (系譜・適合履歴の一元管理正本)      │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 コア設計原則（V2.3 拡張版）

#### 原則 1: 推論とWiki・系譜の完全分離原則 (Context Isolation & State/Lineage Separation)
* **内容**:
  1. 通常の開発タスクを実行する推論エージェント（`conductor`, `architect`, `backend-engineer`, `ui-designer` 等）には、**`wiki/patterns/`、生ログ、および `FEEDBACK_LEDGER.md` を一切見せない**。
  2. 推論エージェントが参照する `rules/AGENTS.md`、`agents/*.md`、`skills/*/SKILL.md`、および `overlay/LOCAL_FEEDBACK_RULES.md` の本文（State）には、**`[PAT-SYS-001]` や `[CLAIM-...]` といった履歴識別子や過去の障害経緯（Lineage）を一切記述してはならない（1-C）**。
* **理由**:
  - トークン消費の肥大化とアテンション希釈（Context Dilution）を防ぎ、最重要原則の遵守率を最大化する。
  - 系譜情報はすべて `FEEDBACK_LEDGER.md` および `PIPELINE_MANIFEST.json` に隔離して追跡する。

#### 原則 2: ナレッジの非破壊的永続性 (Knowledge Non-Destructibility)
* **内容**: 知見原票（`CLAIM-*.md`）が 3段階意味的整合性監査（新複合検証ゲート）で不合格（`REJECTED`）となり、Overlay または Core への反映がロールバック（ブロック）された場合でも、**棄却された知見原票と「どのゲートでなぜ棄却されたか」の診断記録は `~/.gemini/knowledge-hub/rejected/` および案件内の `./wiki/logs.md` に永続保存し、一切削除しない**。
* **効果**: 「過去に試して不変原則違反や矛盾を引き起こした無効なルール案」が恒久的にインデックス化され、将来のプロジェクトで同一の誤った提案が繰り返されるのを完全に防止する。

#### 原則 3: 二層分離（Tier 1 / Tier 2）と Tier 2 の二段階進化サイクル
* **内容**:
  - **Tier 1 (プロジェクト固有知見)**: 障害・手戻り時の一次診断として `./wiki/patterns/local/` に記録された後、各フェーズ完了時に **`./docs/`（設計書・仕様書）および `./PROJECT_STATE.md` へ逆同期して案件内で完結**させる。中央の Knowledge Hub には一切流入させない。
  - **Tier 2 (全体共通知見)**: `./wiki/patterns/universal/` に記録された後、以下の **2段階進化サイクル** を経る：
    1. **第1段階（案件完了時：Spoke ➔ Hub/Overlay）**: PHASE 8 で標準化知見原票（`CLAIM-*.md`）として `~/.gemini/knowledge-hub/inbox/` へ投函され、3段階意味的監査を通過すると `overlay/LOCAL_FEEDBACK_RULES.md` へクリーン再生成反映される。公式プラグイン（Immutable Core）を1バイトも汚さず、同一PC環境の次案件から即座に有効化される。
    2. **第2段階（テンプレート改訂時：Overlay/Hub ➔ Immutable Core）**: パイプライン改訂時（`template` プロジェクト）に `active_claims/` や `inbox/` の原票群が公式の `SKILL.md` / `AGENTS.md` 本体へ蒸留・統合（本流昇格）され、新バージョン配布時に `Upgrade Reconciler` を通じて `Overlay` から自動退役（`archive/upstreamed/` へ移動）する。

---

## 3. 3つの物理スコープ配置とデータ仕様

```text
[1. 個別開発プロジェクト領域 (Spoke Workspace: <project-root>/)]
├── .system_generated/logs/                      <-- [Raw Layer]
├── wiki/                                        <-- [Spoke Wiki Layer] (Git管理・永続)
│   ├── patterns/
│   │   ├── local/                               <-- Tier 1: プロジェクト固有 (docs/へ逆同期完結)
│   │   ├── universal/                           <-- Tier 2: 汎用RCA一次記録 (CLAIM原票の元)
│   │   └── rejected/                            <-- 案件内棄却履歴
│   ├── logs.md                                  <-- プロジェクト内RCA・ゲート採否ログ
│   ├── skill-impact.md                          <-- パターンと原票/スキルの因果追跡
│   └── archive/                                 <-- Compactorによる退避領域
├── promotions/                                  <-- 生成された標準化知見原票 (CLAIM-*.md) の控え
├── docs/                                        <-- [Tier 1 正本] 各種設計書・仕様書
├── PROJECT_STATE.md                             <-- Single Writer 状態管理
└── TEMPLATE_PROMOTIONS.md                       <-- Tier 2 知見昇格(原票化)提示サマリ

[2. PC環境共通 ナレッジハブ領域 (Central Knowledge Hub: ~/.gemini/knowledge-hub/)]
├── inbox/                                       <-- [1-A/1-B] 未処理の標準化知見原票 (CLAIM-*.md)
├── pending_approval/                            <-- [2-A] バックグラウンド監査時の承認待ち (REVIEW-*.md)
├── overlay/                                     <-- [3-A] Immutable Coreを汚さない環境拡張層
│   ├── LOCAL_FEEDBACK_RULES.md                  <-- 蒸留済みローカル追加規約 (絶対上限 80行)
│   └── skills/*.overlay.md                      <-- スキル別補足ガードレール (必要時のみ)
├── active_claims/                               <-- 現在 overlay/ に反映中の有効原票の実体保管庫
├── archive/upstreamed/                          <-- [3-B] 公式Coreへ吸収完了し退役した原票
├── suspended/                                   <-- [3-B] 新Core仕様と衝突し一時保留された原票
├── rejected/                                    <-- [2-A] 意味的監査で棄却された原票と理由記録
└── LOCAL_HUB_STATE.json                         <-- ベースCore Verと適用中Claim IDの状態マニフェスト

[3. 公式プラグイン領域 (Immutable Core: ~/.gemini/config/plugins/system-dev-pipeline/)]
├── PIPELINE_MANIFEST.json                       <-- [3-C] バージョン・吸収済みパターンIDの機械可読正本
├── FEEDBACK_LEDGER.md                           <-- [3-C] 人間監査用の適合履歴・因果追跡台帳 (PURPOSE.md統合)
├── scripts/
│   └── pipeline-reconciler.sh                   <-- [3-B] Upgrade Reconciler & Hub管理スクリプト
├── rules/
│   ├── AGENTS.md                                <-- [1-C/2-B] 履歴ノイズゼロのコア規約 (上限 220行)
│   └── CORE_INVARIANTS.md                       <-- [2-A] コア不変原則カタログ (INV-01〜10)
├── agents/*.md                                  <-- [1-C/2-B] 履歴ノイズゼロのエージェント定義 (上限 120行)
└── skills/*/SKILL.md                            <-- [1-C/2-B] 履歴ノイズゼロのスキル定義 (上限 120行)
```

---

## 4. 4大コンポーネントとエージェント責務マッピング（V2.3）

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   V2.3 WikiSkill コンポーネント・エージェント連携図                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   【1. Inference Agent (推論層)】                                                      │
│     ・アクター: 👑 conductor, 📐 architect, 💻 backend-engineer, 🎨 ui-designer        │
│     ・動作:     Immutable Core (SKILL.md/AGENTS.md) + Local Overlay のみを参照し実行   │
│     ・ガード:   Wiki層・FEEDBACK_LEDGER.md へのアクセス禁止、本文内履歴IDゼロ          │
│                                                                                        │
│                               │ 実行トレース・レビュー指摘・テストエラーログ           │
│                               ▼                                                        │
│   【2. Wiki Maintainer (維持層)】                                                      │
│     ・アクター: 🛡️ qa-engineer (wiki-maintainer)                                       │
│     ・動作:     障害・手戻りからRCAを実施し、./wiki/patterns/{local,universal}/ へ記録 │
│                 Tier 1 は各フェーズ完了時に ./docs/ へ逆同期して完結                   │
│                                                                                        │
│                               │ Tier 2 パターン (./wiki/patterns/universal/)           │
│                               ▼                                                        │
│   【3. Knowledge Claim Proposer (原票起案・投函層)】                                   │
│     ・アクター: 👑 conductor (wiki-proposer)                                           │
│     ・動作:     .patch 生成を廃止。行番号非依存の標準化知見原票 (CLAIM-*.md) を生成し、│
│                 ~/.gemini/knowledge-hub/inbox/ (および ./promotions/) へ投函           │
│                                                                                        │
│                               │ 標準化知見原票 (CLAIM-*.md)                            │
│                               ▼                                                        │
│   【4. Semantic Auditor & Reconciler (3段階意味的監査・蒸留・調停層)】                 │
│     ・アクター: 🛡️ qa-engineer (監査判定) + 👑 conductor (ask_question承認・反映)      │
│     ・動作:     新・複合検証ゲート（4大関門）を実行                                    │
│                 ├─ [PASS + 承認] ──► active_claims/ 登録 & LOCAL_FEEDBACK_RULES.md     │
│                 │                    をクリーン再生成 (Immutable Coreは不変)           │
│                 ├─ [CONFLICT]    ──► ask_question モーダルでユーザー裁定               │
│                 └─ [FAIL/REJECT] ──► Overlay変更破棄 & rejected/ へ原票・理由を永続記録│
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 各コンポーネントの詳細責務

| コンポーネント | 担当アクター / スキル | 実行フェーズ | 詳細動作と V2.3 ガードレール |
| :--- | :--- | :--- | :--- |
| **1. Inference Agent** | 👑 `conductor`<br>📐 `architect`<br>💻 `backend-engineer`<br>🎨 `ui-designer` | PHASE 2〜7<br>改訂作業 | ・純粋な `SKILL.md`、`rules/AGENTS.md`、および `~/.gemini/knowledge-hub/overlay/LOCAL_FEEDBACK_RULES.md` のみに基づいて設計・実装を行う。<br>・プロンプトに `wiki/` や `FEEDBACK_LEDGER.md` を読み込ませることを禁止する。 |
| **2. Wiki Maintainer** | 🛡️ `qa-engineer`<br>⚙️ `wiki-maintainer` | PHASE 3, 5.5, 6<br>自律修復時 | ・レビュー不合格、コード品質指摘、テスト失敗時に根本原因（RCA）を抽出し、`./wiki/patterns/{local,universal}/` へ即時記録する。<br>・Tier 2 記録時は、標準原票化に必要な「発生プロファイル」「適用対象プロファイル」「セマンティック・アンカー候補」を併記する。 |
| **3. Claim Proposer** | 👑 `conductor`<br>⚙️ `wiki-proposer` | PHASE 8<br>（知見昇格工程） | ・`.patch` および `skills/*/PURPOSE.md` の生成は行わない。<br>・`./wiki/patterns/universal/` の知見から固有名詞を排除して抽象化し、標準化知見原票 `CLAIM-{YYYYMMDD}-{SLUG}-{PAT_ID}.md` を生成して `./promotions/` および `~/.gemini/knowledge-hub/inbox/` へ投函する。 |
| **4. Semantic Auditor & Gating** | 🛡️ `qa-engineer`<br>👑 `conductor` | PHASE 8 / PHASE 1検知 / Schedule / 新Ver適用時 | ・`inbox/` の原票に対し、第6章の「新・複合検証ゲート（3段階意味的整合性監査）」を実行する。<br>・対話時は `ask_question` モーダルで承認を得て `overlay/LOCAL_FEEDBACK_RULES.md` をクリーン再生成し、バックグラウンド（`/schedule`）時は非ブロッキングで `pending_approval/REVIEW-*.md` にステージングして通知終了する。 |
| **5. Wiki Compactor** | 👑 `conductor`<br>⚙️ `wiki-compactor` | PHASE 8 / 定期 | ・案件内の `./wiki/patterns/` の重複統合・アーカイブに加え、`~/.gemini/knowledge-hub/inbox/` 内の類似原票の事前クラスタリング集約（`consolidated_from` 記録）および `overlay/` の行数圧縮を担う。 |

---

## 5. ナレッジ蓄積・昇格ライフサイクル（フェーズ別パイプライン）

```
PHASE 1 (初期化 & Hub検知) ──► inbox/・pending_approval/ の未処理原票があれば即時決裁案内
   │
PHASE 2〜6 (開発・監査)   ──► PHASE 3 / 5.5 / 6 で障害検知 ➔ wiki-maintainer が ./wiki/patterns/ へ即時記録
   │                            ├─ [Tier 1: local/] ──► 各フェーズ完了時に ./docs/ & PROJECT_STATE.md へ逆同期完結
   │                            └─ [Tier 2: universal/] ──► 案件内でバッファリング
   │
PHASE 8 (自己進化ループ)
   ├─► 1. wiki-compactor: 重複パターンの整理・クラスタリング
   ├─► 2. wiki-proposer:  標準化知見原票 (CLAIM-*.md) を生成し ~/.gemini/knowledge-hub/inbox/ へ投函
   ├─► 3. qa-engineer:    新・複合検証ゲート (3段階意味的整合性監査: Gate 1〜4) をインライン実行
   ├─► 4. conductor:      ask_question モーダルによるユーザー承認・矛盾裁定
   │     ├─ [承認 (PASS)] ──► active_claims/ へ移動 & overlay/LOCAL_FEEDBACK_RULES.md をクリーン再生成
   │     │                    (※ LOCAL_STANDALONE でパイプライン自体を改訂中の場合は Core へ統合 & 台帳更新)
   │     └─ [棄却 (FAIL)] ──► Overlay変更なし & ~/.gemini/knowledge-hub/rejected/ へ原票と棄却理由を永続保存
   └─► 5. 次期Verリリース時: Upgrade Reconciler が PIPELINE_MANIFEST.json と照合し吸収済み原票を自動退役
```

---

## 6. 新・複合検証ゲート（V2.3 Knowledge & Prompt Gating）と非破壊ロールバック設計

V2.1〜V2.2 における旧複合検証ゲート（完成済みアプリの `npm run lint` や `npm test` を再実行する方式）は、プロンプト文書の変更に対して実質的に常に PASS してしまう形骸化課題があったため、V2.3 では **「提案された知見原票とパイプライン定義文書の意味的整合性・コンテキスト純度・絶対行数予算」を厳格に審査する4大関門** へ全面刷新する。

### 6.1 新・複合検証ゲートの4大関門（3段階意味的整合性監査の具現化）

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               V2.3 新・複合検証ゲート (Knowledge & Prompt Composite Gating)            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [New Gate 1 (Stage 1): 原票スキーマ ＆ コア不変原則 (Core Invariants) 監査]           │
│    ・CLAIM-*.md の YAML Frontmatter・必須5セクション構文が完全であること               │
│    ・rules/CORE_INVARIANTS.md (INV-01〜INV-10) に対する違反・緩和・バイパスが 0件      │
│                                                                                        │
│                                       ▼ PASS                                           │
│  [New Gate 2 (Stage 2): 既存ルール・他FBとの意味的相互矛盾監査 (4分類判定)]            │
│    ・Immutable Core / Local Overlay / 他原票との意味的関係を4分類で解析：              │
│      1. EQUIVALENT (重複) / 2. SUBSUMPTION (包含統合) / 3. SCOPED_BRANCH (条件分岐)    │
│    ・TRUE_CONTRADICTION (真の矛盾) が 0件であること（検出時は自動ブロック＆人間裁定）  │
│                                                                                        │
│                                       ▼ PASS                                           │
│  [New Gate 3 (Stage 3-A): 過剰適合 (Overfitting) 排除 ＆ アンカー実在性検証]           │
│    ・特定案件のディレクトリ名、テーブル名、固有API等の固有名詞混入が 0件であること     │
│    ・target_candidates の対象ファイルおよび section_anchor 見出しが実在しリンク切れ0件 │
│                                                                                        │
│                                       ▼ PASS                                           │
│  [New Gate 4 (Stage 3-B): コンテキスト純度 ＆ 絶対行数バジェット (Hard Budget) 検証]   │
│    ・統合後のルール/スキル本文に [PAT-xxx] や [CLAIM-xxx] 等の履歴ID混入が 0件 (1-C)   │
│    ・絶対行数上限（AGENTS.md: 220行, agents: 120行, SKILL.md: 120行, Overlay: 80行）以内│
│                                                                                        │
│                                       ▼ PASS                                           │
│                 【全関門通過: 承認モーダル (ask_question) ➔ クリーン反映】             │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

| 関門 | 検証項目 | 合格基準 | 不合格時の処置 |
| :--- | :--- | :--- | :--- |
| **New Gate 1**<br>(Invariants) | Frontmatter構文、`CORE_INVARIANTS.md`（INV-01〜10: Single Writer、250行制限、生SQL禁止、本番モックOFF等）との適合 | 不変原則違反 **0 件** | 即座に自動棄却（`~/.gemini/knowledge-hub/rejected/` へ移動し理由を永続記録） |
| **New Gate 2**<br>(Semantic Relation) | 既存 Core / Overlay / Inbox 内他原票との意味的関係（`EQUIVALENT` / `SUBSUMPTION` / `SCOPED_BRANCH` / `TRUE_CONTRADICTION`） | 真の矛盾 **0 件** | `TRUE_CONTRADICTION` 時は自動適用をブロックし、`ask_question` で対立内容と裁定案を提示 |
| **New Gate 3**<br>(Generalization) | 案件固有語彙の排除、統合先ファイル・セクション見出し（`section_anchor`）の実在性、相対パスリンク整合性 | 固有名詞 **0 件**<br>アンカー不整合 **0 件** | 汎用表現への再抽象化（Distillation Loop）を実行して再検査 |
| **New Gate 4**<br>(Purity & Budget) | 履歴メタデータ（`PAT-`, `CLAIM-`）の混入排除、ファイル種別ごとの絶対行数上限（Hard Line Budget）遵守 | 履歴ID混入 **0 件**<br>絶対行数上限以内 | 既存文面のインプレース圧縮・スクリプト外出しを実施して再検査（解消不能時は棄却・ロールバック） |

### 6.2 原票ベースのクリーン再生成と非破壊ロールバック
1. **Local Overlay への反映時**:
   - `~/.gemini/knowledge-hub/overlay/LOCAL_FEEDBACK_RULES.md` に対して行単位のパッチ当てや文字列置換は行わない。
   - 全関門を通過しユーザー承認を得た原票を `active_claims/` に格納し、`LOCAL_HUB_STATE.json` を更新した上で、`active_claims/` 内の有効原票群から `LOCAL_FEEDBACK_RULES.md` をクリーンに再生成する。
2. **ゲート不合格・棄却時のロールバック**:
   - いずれかの関門で FAIL（またはユーザーが棄却を選択）した場合、`active_claims/` および `overlay/LOCAL_FEEDBACK_RULES.md`（あるいはテンプレート改訂時の `skills/` / `rules/`）は一切変更せず直前状態を維持する。
   - 棄却された原票ファイルは `~/.gemini/knowledge-hub/rejected/` へ移動し、案件内の `./wiki/logs.md` に棄却理由と失敗関門を追記することで、**「失敗知見を失わない非破壊的ロールバック」** を実現する。

---

## 7. Wiki Compactor（原票クラスタリング・要約・アーカイブ機構）の設計

### 7.1 V2.3 における Compactor の3つの責務範囲
1. **Spoke 内 `./wiki/patterns/` の整理**:
   - 同一プロジェクト内で発生した類似パターンの統合、および `docs/` 正本化済み・昇格済みパターンの `./wiki/archive/` への退避。
2. **Hub 内 `~/.gemini/knowledge-hub/inbox/` の事前原票クラスタリング（Step 0）**:
   - 複数のプロジェクト（Project A, B, C）から `inbox/` に投函された未処理原票群をスキャンし、同一テーマ・同一原因の原票が複数存在する場合は、YAML Frontmatter の `consolidated_from` に元の `claim_id` リストを記録した上で、1枚の包括的な集約知見原票（Consolidated Claim MD）へ束ねる。
3. **Local Overlay（`LOCAL_FEEDBACK_RULES.md`）のコンテキスト圧縮**:
   - `active_claims/` の増加に伴い `LOCAL_FEEDBACK_RULES.md` が絶対行数上限（80行）に近づいた場合、同カテゴリの複数原票を上位原則へ統合蒸留するか、テンプレート本流（Immutable Core）への昇格コンパイルをコンダクター経由で促す。

---

## 8. データフォーマット標準仕様（V2.3）

### 8.1 プロジェクト内 Wiki パターン定義フォーマット (`./wiki/patterns/{local|universal}/PAT-*.md`)
開発中（PHASE 3, 5.5, 6）に `wiki-maintainer` が一次記録するフォーマット。V2.3 では標準化知見原票へシームレスに変換できるよう、プロファイル情報とセマンティック・アンカー候補を含める。

```markdown
# [PAT-SYS-001]: 外部CLIの非対話実行強制とバックグラウンド待機タイムアウト保護

- **Pattern ID**: PAT-SYS-001
- **作成日**: 2026-10-17
- **知見スコープ**: Tier 2 (テンプレート共通 / Universal)
- **発生プロファイル**: Profile A
- **適用対象プロファイル**: ALL
- **カテゴリ**: SYS
- **重大度**: HIGH
- **ステータス**: Active
- **統合候補アンカー**:
  - `rules/AGENTS.md` (`## 8.5 外部CLIの非対話実行とバックグラウンド待機タイムアウト保護`)
  - `skills/dev-phase7-release/SKILL.md` (`## 作業手順`)

## 1. 発生状況・前提条件 (Context & Preconditions)
- 発生フェーズ: PHASE 7 本番デプロイ実行時
- 技術環境: `gcloud`, `npm` 等の外部CLIを非対話シェル経由で実行する環境全般。

## 2. 現象・根本原因 (Problem & Root Cause Analysis)
- 事象: 確認プロンプト（`[Y/n]`）待ちでバックグラウンドプロセスが無限ハングアップした。
- 根本原因: 非対話フラグ（`--quiet` 等）の明示指定と待機タイムアウト保護が規約化されていなかったため。

## 3. 抽象化された処方箋・推奨ルール (Distilled Prescription)
- 外部CLIを実行する際は、確認プロンプト待ちハングを防ぐため必ず `--quiet`, `--yes` 等の非対話フラグを明示指定すること。
- バックグラウンド移行タスク待機時は `schedule` ツールでワンショット・タイムアウト監視を設定すること。
```

### 8.2 標準化知見原票フォーマット (`~/.gemini/knowledge-hub/inbox/CLAIM-{YYYYMMDD}-{SLUG}-{PAT_ID}.md`)
PHASE 8 で `wiki-proposer` が生成し、Knowledge Hub への投函および他環境還流（1-B）の共通単位となる自己完結型 Markdown スキーマ。詳細は [V2.3新知見フィードバック機構設計書.md](./V2.3新知見フィードバック機構設計書.md) 第3.2節を参照。

### 8.3 公式Core 適合履歴マニフェスト & 系譜台帳 (`PIPELINE_MANIFEST.json` / `FEEDBACK_LEDGER.md`)
従来各スキル直下に分散していた `skills/*/PURPOSE.md` は廃止し、プラグインルートの以下2ファイルへ完全統合する（詳細は [V2.3新知見フィードバック機構設計書.md](./V2.3新知見フィードバック機構設計書.md) 第5.3節を参照）：
1. **`PIPELINE_MANIFEST.json`**: パイプラインバージョン、不変原則バージョン、および公式吸収済みパターン（`absorbed_patterns`: `pattern_id`, `claim_ids`, `absorbed_in_version`, `integration_type`, `target_files`）を保持する機械可読マニフェスト。
2. **`FEEDBACK_LEDGER.md`**: どのバージョンで・どの知見原票が・どのファイルのどのセクションへ・どのような動機で統合蒸留されたかを一覧管理する人間監査用台帳。

---

## 9. スキル・自動化スクリプト構成（V2.3）

| スキル / スクリプト名 | 格納パス | 主担当ロール | V2.3 機能概要 |
| :--- | :--- | :--- | :--- |
| **`wiki-maintainer`** | `.agents/plugins/system-dev-pipeline/skills/wiki-maintainer/` | 🛡️ `qa-engineer` | エラー・手戻りからRCAを実施し、`./wiki/patterns/{local,universal}/` へプロファイル・アンカー情報付きで一次記録する。 |
| **`wiki-proposer`** | `.agents/plugins/system-dev-pipeline/skills/wiki-proposer/` | 👑 `conductor` | `./wiki/patterns/universal/` から固有名詞・履歴ノイズを除去した標準化知見原票（`CLAIM-*.md`）を生成し、`~/.gemini/knowledge-hub/inbox/` および `./promotions/` へ投函する。 |
| **Semantic Auditor**<br>（新複合検証ゲート） | （`qa-engineer` 監査モード & `dev-phase8-rules`） | 🛡️ `qa-engineer`<br>👑 `conductor` | 3段階意味的整合性監査（New Gate 1〜4）を実行し、`ask_question` 承認を経て `overlay/LOCAL_FEEDBACK_RULES.md` をクリーン再生成（または Schedule 時は `pending_approval/` へステージング）する。 |
| **`wiki-compactor`** | `.agents/plugins/system-dev-pipeline/skills/wiki-compactor/` | 👑 `conductor` | `./wiki/patterns/` の整理に加え、`inbox/` 原票の事前クラスタリング集約および `overlay/` の行数圧縮を実行する。 |
| **`pipeline-reconciler.sh`** | `.agents/plugins/system-dev-pipeline/scripts/pipeline-reconciler.sh` | 👑 `conductor`<br>👤 ユーザー | Knowledge Hub の初期化、状態確認（`--status`）、`LOCAL_FEEDBACK_RULES.md` のクリーン再生成（`--rebuild-overlay`）、および新バージョン Core 適用時の4分類マイグレーション調停（`--upgrade`）を実行する。 |

---

## 10. 関連ドキュメント・リンク

- [V2.3新知見フィードバック機構設計書.md](./V2.3新知見フィードバック機構設計書.md) - V2.3 Central Knowledge Hub・3段階意味的監査・Immutable Core / Local Overlay 統合仕様書
- [V2.3改変計画書.md](./V2.3改変計画書.md) - V2.3 全体改変計画書
- [テンプレート配置形態およびナレッジ境界設計書.md](./テンプレート配置形態およびナレッジ境界設計書.md) - 3つの物理スコープ境界（Spoke / Hub / Core）と配置形態設計書
- [エージェント間知見蓄積運用基準書V2.3.md](./エージェント間知見蓄積運用基準書V2.3.md) - Tier 1 / Tier 2 二層分離と二段階進化運用基準書
- [AI駆動システム開発フェーズ定義書V2.3.md](./AI駆動システム開発フェーズ定義書V2.3.md) - V2.3 開発ライフサイクル定義書
- [エージェント設計書V2.3.md](./エージェント設計書V2.3.md) - V2.3 5大エージェント協調・権限設計書
- [状態管理機構設計書V2.3.md](./状態管理機構設計書V2.3.md) - V2.3 Single Writer 状態管理詳細設計書
- [定量測定・フィードバック設計書.md](./定量測定・フィードバック設計書.md) - 定量測定・テンプレートフィードバック詳細設計書
