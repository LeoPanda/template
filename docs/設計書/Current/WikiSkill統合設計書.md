# WikiSkill 統合設計書 (WikiSkill Integration Architecture Specification)

文書バージョン: 1.0  
作成日: 2026-10-10  
対象バージョン: AI駆動システム開発ライフサイクルテンプレート V2.1  
ステータス: 策定完了 (Step 2 策定版)  

---

## 1. はじめに

### 1.1 背景と課題認識
AI駆動システム開発ライフサイクル V2.0 においては、コンダクター（Main）、設計（architect）、UI（ui-designer）、QA（qa-engineer）の協調体制と状態管理機構（`PROJECT_STATE.md`）により、高度な自律開発パイプラインが実現された。また、開発中の気づきや落とし穴を形式知化する枠組みとして [エージェント間知見蓄積運用基準書.md](../V2.0/エージェント間知見蓄積運用基準書.md) が整備され、Actionable Knowledge（状況・現象・根本原因・処方箋）の蓄積が図られてきた。

しかし、先行検討資料 [V2.1へ向けた検討課題.md](../../検討課題/V2.1/V2.1へ向けた検討課題.md) および [WikiSkill導入評価書.md](../../検討課題/V2.1/WikiSkill導入評価書.md) で指摘されている通り、従来の自己進化・改善ループには2つの構造的欠陥が存在していた：

1. **ロールバックに伴う知見喪失（Catastrophic Forgetting）**:
   - 手順書（`SKILL.md`）やプロンプトの修正案を適用した結果、検証テストでスコアが悪化してロールバックを実行した場合、「なぜ失敗したのか」「どのような改善案を試してダメだったのか」という貴重な診断ログや失敗知見まで手順書と一緒に破棄されてしまう。この結果、将来のサイクルで同一の過ちを繰り返す「先祖返り」や「堂々巡りの試行錯誤」が発生する。
2. **推論時のコンテキスト汚染と過剰適合（Overfitting）**:
   - 蓄積された過去のトラブル事例やエラーログを生のままエージェントの推論プロンプトへ注入すると、コンテキスト長を浪費するだけでなく、特定事例に特化した場当たり的な分岐コードを記述し始め、スキルの汎化性能が著しく低下する。

### 1.2 目的と位置付け
本文書は、[V2.1検討方針書.md](./V2.1検討方針書.md) の **「テーマ 2: WikiSkill型 永続ナレッジ自己進化ループシステムの導入」** に基づき、Google Research および Virginia Tech が提唱した **WikiSkill** アーキテクチャ（[wikiskill.md](../../検討課題/V2.1/wikiskill.md)）を本システム開発ライフサイクルへ本格統合するための設計仕様を定義するものである。

実行ログ（Raw）と実行手順書（Skills）の中間に、**決してロールバックされない「永続的 Wiki 層（Persistent Knowledge Layer）」** を配置し、推論エージェントとWikiの分離（Context Isolation）、複合検証ゲート（Composite Gating）、および自動枝刈り（Wiki Compactor）を組み合わせることで、**「失敗から恒久的に学び続け、かつ過学習を起こさない安全な自己進化パイプライン」** を構築する。

---

## 2. WikiSkill 統合アーキテクチャの全容

### 2.1 3層ストレージモデルと境界定義
WikiSkill アーキテクチャは、システム内のデータを性質の異なる3つの層に厳密に分離して管理する。

```
┌────────────────────────────────────────────────────────────────────────┐
│                      WikiSkill 3層ストレージアーキテクチャ              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [1. Raw Layer (実行ログ層)]                                           │
│    ・格納先: .system_generated/logs/, docs/plans/scenario-test/       │
│    ・特性:   完全イミュータブル（追記のみ、変更・削除不可）            │
│    ・内容:   ReAct推論トレース、ツール入出力、テスト実行結果ログ       │
│                                                                        │
│                              │ サンプリング & 根本原因分析 (RCA)       │
│                              ▼                                         │
│  [2. Wiki Layer (永続ナレッジ層)] <─── ※ 決してロールバックされない永続層│
│    ・格納先: ./wiki/ (プロジェクトルート配下)                            │
│    ・特性:   永続蓄積（スキル検証が不合格になっても破棄されない）      │
│    ・内容:   patterns/*.md (構造化知見), logs.md (採否履歴),          │
│              skill-impact.md (因果追跡)                                │
│                                                                        │
│                              │ 蒸留・一般化 (Generalization)           │
│                              ▼                                         │
│  [3. Skills Layer (実行手順層)]   <─── ※ 評価次第でロールバックされる実行層│
│    ・格納先: .agents/plugins/system-dev-pipeline/skills/, rules/       │
│    ・特性:   可変・アトミック更新（検証不合格時は直前状態へリセット）  │
│    ・内容:   SKILL.md (実行手順), PURPOSE.md (変更意図・Wikiリンク)   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 コア設計原則

#### 原則 1: 推論とWikiの分離原則 (Context Isolation)
* **内容**: 通常の開発タスクを実行する推論エージェント（`conductor`, `architect`, `backend-engineer`, `ui-designer` 等）には、**`wiki/patterns/` や生ログを一切見せない**。
* **理由**:
  1. トークン消費の肥大化を防ぎ、メインコンテキスト寿命を最大化する。
  2. 過去の特定エラーに過剰適合（Overfitting）した場当たり的コード（ワークアラウンドの乱発）を抑止し、標準規約・抽象化手順に準拠したクリーンな実装を担保する。
  3. 推論エージェントが参照するのは、Wikiから十分に検証・蒸留された `skills/SKILL.md` および `rules/` のみとする。

#### 原則 2: ナレッジの非破壊的永続性 (Knowledge Non-Destructibility)
* **内容**: スキル更新案（Patch）が検証ゲートでリジェクト（不合格）となり、Skills 層がロールバックされた場合でも、**Wiki 層に記録された知見（失敗原因、試みたアプローチ、リジェクト理由）は一切削除・ロールバックしない**。
* **効果**: 「過去に試して失敗した無効なアプローチ」が永続的にインデックス化され、次回の自己進化サイクルで同一の誤ったパッチが再提案されるのを完全に防止する。

#### 原則 3: 二層分離の厳格適用 (Two-Tier Separation)
* **内容**: [エージェント間知見蓄積運用基準書V2.1.md](./エージェント間知見蓄積運用基準書V2.1.md) に定義された「Tier 1: プロジェクト固有知見」と「Tier 2: 全体共通知見」の峻別を、Wiki パターン登録およびスキル昇格の判定ガードレールとして強制する。
  - **Tier 1 (プロジェクト固有)**: 障害・手戻り時の一次診断ログとして `wiki/patterns/local/` に記録されるが、**推論エージェントへの提供正本は `docs/` (設計書・仕様書) および `PROJECT_STATE.md`** とする。各フェーズ完了時にドキュメントへ即時逆同期することで、推論エージェントは Context Isolation を維持したまま仕様として最新知見を消費できる（共通スキルへの昇格は原則禁止）。
  - **Tier 2 (全体共通)**: `wiki/patterns/universal/` に蓄積され、PHASE 8 や改訂完了時に Skill Proposer と複合検証ゲート（Gating）を経て、テンプレート側の `skills/` や `rules/` へ安全に昇格・自己進化させる。
* **効果**: プロジェクト固有の業務仕様がテンプレート共通の `SKILL.md` に混入する汚染事故を防止するとともに、推論エージェントが必要な個別業務知識を `docs/` 経由で確実に取得できる。

---

## 3. 3層ストレージモデルの物理配置とデータ仕様

本システム環境（Antigravity ワークスペース）における物理ディレクトリ構成およびファイル仕様を以下のように規定する。

```
workspace/
├── .system_generated/
│   └── logs/
│       ├── raw_traces/                          <-- [Raw Layer]
│       │   ├── 20261010_phase4_build.log
│       │   └── 20261010_phase6_test_run.log
│       └── transcript.jsonl
│
├── wiki/                                        <-- [Wiki Layer] (プロジェクトルート配下・Git管理・永続)
│   ├── patterns/                                <-- パターン別構造化知見
│   │   ├── local/                               <-- Tier 1: プロジェクト固有 (docs/逆同期・仕様正本化)
│   │   │   └── PAT-LOC-001_discount_rounding_error.md
│   │   ├── universal/                           <-- Tier 2: テンプレート共通 (スキル自己進化用)
│   │   │   ├── PAT-ENV-001_docker_port_conflict.md
│   │   │   ├── PAT-CODE-001_fastify_cors_preflight.md
│   │   │   └── PAT-TEST-001_playwright_hydration_timeout.md
│   │   └── rejected/                            <-- 検証ゲート不合格・失敗履歴
│   ├── logs.md                                  <-- スキル提案採否・検証スコアログ
│   ├── skill-impact.md                          <-- パターンとスキルの因果追跡
│   └── archive/                                 <-- Compactorによる退避領域
│
├── docs/                                        <-- [Tier 1 正本] 各種設計書・仕様書
│   ├── plans/                                   <-- レビュー報告書・テストログ
│   └── ...
├── metrics/                                     <-- 定量メトリクス集計領域
│   └── turns/
├── rules/                                       <-- プロジェクト適用ルール
│   └── AGENTS.md
├── PROJECT_STATE.md                             <-- 進行状態管理 (EXECUTION_MODE 記録)
├── TEMPLATE_PROMOTIONS.md                       <-- Tier 2 知見昇格申請バッファ
│
└── .agents/plugins/system-dev-pipeline/         <-- [Skills Layer] (※ LOCAL_STANDALONE 時。GLOBAL_PLUGIN 時は ~/.gemini/ 配下)
    ├── skills/
    │   ├── dev-phase4-env-build/
    │   │   ├── SKILL.md
    │   │   └── PURPOSE.md                       <-- Wikiリンクと変更意図
    │   └── ...
    └── rules/
        ├── AGENTS.md
        └── PURPOSE.md
```

### 3.1 Raw Layer (`.system_generated/logs/raw_traces/`)
* **ライフサイクル**: 各フェーズ実行時に自動生成される。開発案件内では追記・蓄積のみ。
* **データ構造**:
  - コマンド実行標準出力・エラー出力（Docker build、npm test、linter出力）
  - Antigravity ツール呼び出しログ（入力引数、実行結果、スタックトレース）
  - テスト自動実行時のシナリオ別合否ログおよびスナップショット

### 3.2 Wiki Layer (`<project-root>/wiki/`)
Wiki層は、プロジェクトルート直下に配置され、Gitリポジトリ内で追跡され、**スキルのロールバック操作（`git checkout` 等）の対象外（パス指定除外）** として保護される。プラグイン配置形態（グローバル vs ローカル同梱）に関わらず、すべての知見は必ずプロジェクト配下の `./wiki/` に一次蓄積される（ローカル・ファースト蓄積原則）。詳細は [テンプレート配置形態およびナレッジ境界設計書.md](./テンプレート配置形態およびナレッジ境界設計書.md) を参照。

#### (1) `wiki/patterns/` の二層構造
知見の汚染と過学習を防ぐため、パターンディレクトリを二層に厳密分離する（詳細は [エージェント間知見蓄積運用基準書V2.1.md](./エージェント間知見蓄積運用基準書V2.1.md) を参照）：
- **`patterns/local/PAT-LOC-xxx_{識別名}.md` (Tier 1: プロジェクト固有知見)**:
  - 業務仕様、個別画面、独自DB、特定APIに起因する知見の一次診断記録。
  - 各フェーズ完了時に **`docs/` (仕様書・設計書) および `PROJECT_STATE.md` へ逆同期（ドキュメント正本化）** され、推論エージェントは仕様書経由で消費する。
- **`patterns/universal/PAT-{CAT}-xxx_{識別名}.md` (Tier 2: 全体共通知見)**:
  - FW挙動、Docker、型安全、共通テスト手順、エージェント行動規範。
  - PHASE 8 や改訂完了時に Skill Proposer によって読み込まれ、`skills/` や `rules/` の改善パッチとして起案・昇格される。

#### (2) `wiki/logs.md`
スキル修正案の提案履歴、実行された検証結果、採否（Adopted / Rejected）、およびスコア差分を時系列で追記する台帳。

#### (3) `wiki/skill-impact.md`
どのWikiパターンが、どのスキルのどのバージョンに反映され、品質指標（テスト合格率や実行時間）にどう寄与したかを逆引き追跡する因果マッピング。

### 3.3 Skills Layer (`.agents/plugins/system-dev-pipeline/skills/`, `rules/`)
* **ライフサイクル**: 通常は読み取り専用。自己進化ループ（PHASE 8 または改訂サイクル）においてのみパッチ適用され、検証ゲートを通過した場合に確定コミットされる。不合格時は直前の Git コミット（またはバックアップディレクトリ）へ瞬時にリセットされる。
* **`PURPOSE.md`**: 各スキルディレクトリ直下に配置され、現在のスキルバージョンが「どの Wiki パターンを解決するために」「どのような動機で」策定されたかを明記するメタデータ。

---

## 4. 4大コンポーネントとエージェント責務マッピング

WikiSkill アーキテクチャを構成する4つのコンポーネントを、本システムのマルチエージェント体制へ明確にマッピングする。

```
┌────────────────────────────────────────────────────────────────────────┐
│                   WikiSkill コンポーネント・エージェント連携図          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   【1. Inference Agent (推論層)】                                       │
│     ・アクター: 👑 conductor, 📐 architect, 💻 backend-engineer,        │
│                 🎨 ui-designer                                         │
│     ・動作:     Skills層 (SKILL.md) のみを参照し開発・実装を実行        │
│     ・ガード:   Wiki層へのアクセス禁止 (Context Isolation)             │
│                                                                        │
│                               │ 実行トレース・エラーログ               │
│                               ▼                                        │
│   【2. Wiki Maintainer (維持層)】                                      │
│     ・アクター: 🛡️ qa-engineer (テスト/監査モード), dev-doc-reviewer   │
│     ・動作:     障害・手戻りログから根本原因を分析し、patterns/*.md へ │
│                 永続記録。Tier 1 / Tier 2 の自動仕分けを実施           │
│                                                                        │
│                               │ 構造化ナレッジ & 採否履歴              │
│                               ▼                                        │
│   【3. Skill Proposer (提案層)】                                       │
│     ・アクター: 👑 conductor (知見昇格モード / wiki-proposer)          │
│     ・動作:     蓄積パターンから共通改善パッチ (Patch) を立案し、       │
│                 PURPOSE.md と共に Skills層へ仮適用                     │
│                                                                        │
│                               │ スキル更新案 (Patch)                   │
│                               ▼                                        │
│   【4. Gating & Rollback (検証ゲート層)】                              │
│     ・アクター: 🛡️ qa-engineer (検証ベンチマーク実行モード)             │
│     ・動作:     複合検証ゲート（静的解析・整合性・全テスト）を実行     │
│                 ├─ [PASS]  ──► スキル確定マージ & logs.md 採択記録     │
│                 └─ [FAIL]  ──► スキル層のみリセット & logs.md 失敗記録 │
│                                (※ Wiki層は完全保持)                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.1 各コンポーネントの詳細責務

| コンポーネント | 担当アクター / スキル | 実行フェーズ | 詳細動作とガードレール |
| :--- | :--- | :--- | :--- |
| **1. Inference Agent** | 👑 `conductor`<br>📐 `architect`<br>💻 `backend-engineer`<br>🎨 `ui-designer` | PHASE 2〜5<br>改訂作業 | ・整理済みの `SKILL.md` および `rules/` のみに基づいて設計・実装を行う。<br>・プロンプトに `wiki/` の内容を読み込ませることを禁止する。 |
| **2. Wiki Maintainer** | 🛡️ `qa-engineer`<br>⚙️ `wiki-maintainer` | PHASE 3, 5.5, 6<br>テスト自律修復時 | ・設計レビュー不合格、コード品質指摘、テスト失敗、自律修復ループ発生時に、その根本原因（RCA）を即座に抽出し、`wiki/patterns/` へ新規登録・追記する。<br>・同時に、Tier 1（プロジェクト固有）か Tier 2（テンプレート共通）かを判定する。 |
| **3. Skill Proposer** | 👑 `conductor`<br>⚙️ `wiki-proposer` | PHASE 8<br>（知見昇格工程） | ・Tier 2 に仕分けられた `wiki/patterns/` と過去の `wiki/logs.md` を読み込む。<br>・重複した失敗の回避や手順最適化を目的とした `SKILL.md` の改変パッチを生成する。<br>・変更理由を記述した `PURPOSE.md` を作成する。 |
| **4. Gating & Rollback** | 🛡️ `qa-engineer`<br>（品質判定） | PHASE 8 検証時<br>テンプレート更新時 | ・仮適用されたスキルを用いて検証スイート（後述の複合検証ゲート）を実行する。<br>・全項目合格時のみ Git コミットを実行し、不合格時は `skills/` の変更を破棄して直前状態へロールバックする。<br>・合否判定とスコア差分を `wiki/logs.md` に永続追記する。 |

---

## 5. ナレッジ蓄積・昇格ライフサイクル（フェーズ別パイプライン）

新規開発ライフサイクル（PHASE 1〜8）および本番運用改訂プロセスにおける、WikiSkill の具体的な動作シーケンスを規定する。

```
PHASE 1〜5 (通常開発) ──► PHASE 3 / 5.5 / 6 (障害検知 & 即時Wiki記録)
                                  │
                                  ▼ [Wiki Maintainer: patterns/*.md 永続化]
                                  │
PHASE 7 (総合監査)    ──► PHASE 8 (知見昇格 & 自己進化ループ)
                                  │
                                  ├─► 1. Wikiパターンの集約・抽出 (Proposer)
                                  ├─► 2. SKILL.md パッチ作成 & PURPOSE.md 更新
                                  ├─► 3. 複合検証ゲート実行 (Gating)
                                  │     ├─ [合格] スキル昇格・確定マージ
                                  │     └─ [不合格] スキル層ロールバック (Wiki保持)
                                  └─► 4. Wiki Compactor による定期枝刈り
```

### 5.1 PHASE 3 / 5.5 / 6 における即時Wiki蓄積 (Fail Fast, Record Immediately)
手戻りやエラーが発生した現場において、知識が新鮮なうちに Wiki Maintainer が即座に記録を行う。

1. **PHASE 3（基本設計レビュー）**:
   - `dev-review-arch` で重大なアーキテクチャ欠陥（循環参照、認可漏れ、SPOF）が検知された場合、`qa-engineer` は是正指示と同時に `wiki/patterns/PAT-ARCH-xxx.md` を作成する。
2. **PHASE 5.5（コード品質レビュー）**:
   - `dev-review-code` で顕著な重複コードや型アンチパターンが検出された場合、`wiki/patterns/PAT-CODE-xxx.md` に再発防止パターンを記録する。
3. **PHASE 6（スルーテスト自動修復ループ）**:
   - テスト失敗および自動修復（Auto-Healing）が実行された際、何がエラーの原因であり、どう修正して修復したかを `qa-engineer` が `wiki/patterns/PAT-TEST-xxx.md` に記録する。

### 5.2 PHASE 8 における自己進化サイクルの実行手順
プロジェクト完了時（PHASE 8: ドキュメント改訂管理の開始）において、テンプレート自体のスキル進化を以下の手順で安全に実行する。

1. **知見の収集とTier判定**:
   - 👑 コンダクターが `dev-phase8-rules` を起動。
   - プロジェクト内で蓄積された `wiki/patterns/` を走査し、Tier 2（全体共通知見）に該当するパターンを抽出し、`./TEMPLATE_PROMOTIONS.md`（昇格候補提示サマリ）へ集約・提示。
2. **ユーザー承認と昇格先ルーティング判定**:
   - ユーザーに対し `./TEMPLATE_PROMOTIONS.md` の確認・承認を要請。
   - `PROJECT_STATE.md` に記録された `EXECUTION_MODE`（`GLOBAL_PLUGIN` または `LOCAL_STANDALONE`）を判定（詳細は [テンプレート配置形態およびナレッジ境界設計書.md](./テンプレート配置形態およびナレッジ境界設計書.md) を参照）。
3. **スキル改善案（Patch）の起案**:
   - Skill Proposer (`wiki-proposer`) が、対象パターンと `wiki/logs.md`（過去の棄却履歴）を参照し、重複改善を回避しながら `SKILL.md` の更新パッチを作成。
   - `PURPOSE.md` にターゲットパターンIDと改定意図を記録。
4. **仮適用とバックアップ**:
   - 現行の `skills/` をバックアップ領域（または作業ブランチ `evolution/temp-patch`）に退避し、パッチを適用。
5. **複合検証ゲートの実行**:
   - 🛡️ `qa-engineer` が次章で定義する検証テスト群（静的解析、ドキュメント整合性、シナリオテスト、トークン効率）を実行。
6. **判定とモード別確定コミット / ロールバック**:
   - **合格時**:
     - **`LOCAL_STANDALONE` モード**: プロジェクトローカルの `.agents/plugins/system-dev-pipeline/skills/` を正式採用として Git コミット。
     - **`GLOBAL_PLUGIN` モード**: エクスポート先ディレクトリ（`./promotions/`）が存在しない場合は自動生成（`mkdir -p ./promotions`）した上で、プロジェクト直下に `./promotions/v2.1_universal_patterns.patch`（または Markdown 形式の昇格差分ファイル）をエクスポートし、グローバル資産への反映手順をユーザーへ案内。
     - `wiki/logs.md` に `[Adopted]` を記録し、`wiki/skill-impact.md` を更新。
   - **不合格時**: `skills/` をバックアップから即座に復元（ロールバック）。`wiki/logs.md` に `[Rejected]`、失敗したテストケース、および棄却理由を記録。**`wiki/` 領域のファイルは一切戻さない**。

---

## 6. 複合検証ゲート（Composite Gating Criteria）と安全なロールバック設計

自律エージェントのスキル更新において、単一の数値指標のみに依存すると局所最適や破壊的副作用を見落とす危険がある。本システムでは、4つの独立した検証関門からなる **「複合検証ゲート」** を採用する。

### 6.1 複合検証ゲートの4大関門

```
┌────────────────────────────────────────────────────────────────────────┐
│                        複合検証ゲート (Composite Gating)                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [関門 1: 静的解析・リンター検証 (Syntax & Types)]                      │
│    ・TypeScript / Python コンパイルエラー: 0件                         │
│    ・Linter (ESLint, Ruff 等) エラー: 0件                              │
│                                                                        │
│                                   ▼ PASS                               │
│  [関門 2: ドキュメント相互整合性検証 (Doc Integrity)]                  │
│    ・dev-doc-reviewer による多次元クロスチェック                       │
│    ・仕様書・設計書間の未解決不整合・リンク切れ: 0件                   │
│                                                                        │
│                                   ▼ PASS                               │
│  [関門 3: リグレッション防止・シナリオテスト検証 (Scenario Pass)]      │
│    ・PHASE 6 標準シナリオテストスイート: 成功率 100% (全件パス)        │
│    ・過去のクリティカルバグ回帰テスト: 全件パス                        │
│                                                                        │
│                                   ▼ PASS                               │
│  [関門 4: コンテキスト効率・トークン評価 (Token Efficiency)]           │
│    ・改変後の SKILL.md トークン数増加が許容上限 (+20%) 以内であること   │
│    ・長大なコード片の埋め込みによるプロンプト肥大化がないこと          │
│                                                                        │
│                                   ▼ PASS                               │
│                         【全関門通過: 合格 (Adopted)】                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

| 関門 | 検証項目 | 合格基準 | 判定ツール / コマンド |
| :--- | :--- | :--- | :--- |
| **Gate 1: 静的解析** | 構文エラー、型不整合、未定義参照 | エラー 0 件 | `npm run lint` / `tsc --noEmit` / `ruff check` |
| **Gate 2: ドキュメント整合性** | 設計書・API仕様・READMEの記述矛盾 | 不整合 0 件 | `dev-doc-reviewer` スキル実行 |
| **Gate 3: シナリオテスト** | システム主要機能のE2E・結合動作 | 成功率 100% (Pass Rate = 1.0) | `dev-phase6-testing` (Playwright / Jest / pytest) |
| **Gate 4: コンテキスト効率** | スキル手順書の冗長化・プロンプト圧迫 | 行数増加 ≤ 20%、トークン増 ≤ 25% | `wc -l` および トークンカウンター |

### 6.2 ロールバック実行メカニズム
検証ゲートが1つでも不合格となった場合のロールバック手順を決定論的に定義する。

```bash
# ロールバック実行コマンドシーケンス（擬似コード）
function rollback_skills_keep_wiki() {
    echo "[Gating Failed] スキル更新案を棄却し、ロールバックを実行します..."
    
    # 1. Skills層およびRules層を作業ブランチまたはバックアップから復元
    git checkout HEAD -- .agents/plugins/system-dev-pipeline/skills/
    git checkout HEAD -- .agents/plugins/system-dev-pipeline/rules/
    
    # ※ 重要: ./wiki/ は checkout の対象に含めない (完全維持)
    
    # 2. 棄却ログを wiki/logs.md へ追記
    python3 scripts/record_rejection.py \
        --proposal-id "$PROPOSAL_ID" \
        --reason "$FAILURE_REASON" \
        --failed-gate "$FAILED_GATE"
        
    echo "[Rollback Complete] Skills層を復元しました。Wiki知識は正常に保持されています。"
}
```

---

## 7. Wiki Compactor（定期要約・アーカイブ・枝刈り機構）の設計

### 7.1 Wiki 肥大化の課題（The Wiki Bloat Problem）
Wiki層は追記型でロールバックされないため、多数のプロジェクトや開発サイクルを重ねると以下の問題が生じる：
1. **パターンの類似・重複**: 同一エラーに対する類似パターンが複数乱立し、Skill Proposer のインプットトークンを浪費する。
2. **知見の陳腐化**: ライブラリのバージョンアップやフレームワーク刷新により、過去の回避策が無効・不要になる。
3. **競合ルールの発生**: 過去のパターン A と新しいパターン B の推奨策が矛盾する。

### 7.2 Wiki Compactor のアーキテクチャ
これらの課題を解決するため、定期バッチ（またはパターン数が閾値（例: 30件）を超えた時点）で自律実行される **Wiki Compactor** を導入する。

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Wiki Compactor 実行フロー                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [1. パターンクラスタリング (Clustering)]                              │
│    ・wiki/patterns/ 配下の全ファイルを技術ドメイン・エラー種別で分類  │
│                                                                        │
│                                   ▼                                    │
│  [2. 類似・重複パターンの統合 (Consolidation)]                         │
│    ・同一根本原因を持つ複数パターンを包括的な1ファイルへ統合要約      │
│    ・旧パターンIDを新パターンの `Consolidated-From` メタデータへ記録   │
│                                                                        │
│                                   ▼                                    │
│  [3. 陳腐化・解決済みパターンの退避 (Archiving)]                       │
│    ・既に正式スキルへ恒久反映され、直近10サイクルで再発のないパターン  │
│    ・フレームワークのバージョンアップにより無効化したパターン          │
│    ・これらを wiki/patterns/ から wiki/archive/patterns/ へ移動        │
│                                                                        │
│                                   ▼                                    │
│  [4. インデックスの再構築 (Re-Indexing)]                               │
│    ・wiki/skill-impact.md およびパターン一覧インデックスを最新化       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 7.3 アーカイブ判定基準（Compactor Rules）
- **統合条件 (Consolidate)**: Jaccard類似度または意味的類似性が高く、対象ライブラリ・現象が同一である場合。
- **退避条件 (Archive)**:
  1. 当該パターンに基づく改善パッチが正式マージ（Adopted）されてから 5 プロジェクト以上が経過し、かつ一度も再発（リグレッション）していないこと。
  2. 対象となる技術スタックがプロジェクトで非推奨・廃止されたこと。

---

## 8. データフォーマット標準仕様

本システムで運用する各ファイルの標準フォーマットを規定する。

### 8.1 Wiki パターン定義フォーマット (`wiki/patterns/{category}_{pattern_id}.md`)
[エージェント間知見蓄積運用基準書.md](../V2.0/エージェント間知見蓄積運用基準書.md) のフォーマットを継承し、WikiSkill用のメタデータを拡張する。

```markdown
# [PAT-CODE-001]: FastifyとCORSのプリフライト競合回避

- **Pattern ID**: PAT-CODE-001
- **作成日**: 2026-10-10
- **更新日**: 2026-10-10
- **カテゴリ**: [ARCH / CODE / TEST / ENV / SEC]
- **ステータス**: [Active / Consolidated / Archived]
- **適用先スコープ**: Tier 2 (テンプレート昇格推奨)
- **関連スキル**: dev-phase4-env-build

## 1. 発生状況 (Context & Condition)
- 技術スタック: Fastify v4 + @fastify/cors + Next.js (SPA)
- 発生フェーズ: PHASE 4 実装後の API 疎通確認時

## 2. 現象・落とし穴 (Problem / Trap)
- フロントエンドからの認証ヘッダー付き POST リクエストに対し、OPTIONS プリフライトが 401 Unauthorized で拒否され、CORS エラーが発生する。

## 3. 根本原因 (Root Cause)
- グローバルの認証フック (`onRequest` または `preHandler`) が OPTIONS メソッドに対してもトークン検証を実行してしまい、OPTIONS リクエストが無条件に弾かれていた。

## 4. 処方箋・推奨ルール (Prescription / Rule)
- 認証フックの先頭に `if (request.method === 'OPTIONS') return;` を必ず設ける。
- または `@fastify/cors` のプラグイン登録を認証フックよりも前で確実に宣言すること。

## 5. 適用・検証履歴 (Lineage)
- 関連ログ: `wiki/logs.md` (Round-1, Proposal-003)
- 昇格先コミット: `git-rev-a1b2c3d` (`skills/dev-phase4-env-build/SKILL.md`)
```

### 8.2 スキル提案採否ログフォーマット (`wiki/logs.md`)
追記専用の Markdown テーブル形式を採用する。

```markdown
# WikiSkill Evolution & Proposal Logs

| Timestamp | Proposal ID | Target Skill | Linked Pattern | Gating Result | Baseline Score | New Score | Action | Reason / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-10-10 14:00 | PROP-20261010-01 | dev-phase4-env-build | PAT-CODE-001 | PASS | 0.850 | 1.000 | ADOPTED | 全関門クリア。OPTIONSフック是正手順追加 |
| 2026-10-10 16:30 | PROP-20261010-02 | dev-phase6-testing | PAT-TEST-004 | FAIL (Gate 3) | 1.000 | 0.920 | REJECTED | シナリオテスト2件がタイムアウト悪化 |
```

### 8.3 スキル目的メタデータフォーマット (`skills/{skill_name}/PURPOSE.md`)

```markdown
# Skill Purpose & Evolution Metadata

- **Target Skill**: dev-phase4-env-build
- **Current Version**: 2.1.0
- **Last Updated**: 2026-10-10
- **Linked Wiki Patterns**:
  - [PAT-CODE-001_fastify_cors_preflight.md](../../../../wiki/patterns/universal/PAT-CODE-001_fastify_cors_preflight.md)
  - [PAT-ENV-001_docker_port_conflict.md](../../../../wiki/patterns/universal/PAT-ENV-001_docker_port_conflict.md)

## Evolution History & Motivation
- **v2.1.0 (Round-1)**:
  - 理由: Fastify環境でのCORSプリフライト拒否障害（PAT-CODE-001）を根絶するため、Fastifyサーバー構築手順の認証フック設定項目に OPTIONS メソッド除外ガードレールを追加。
```

---

## 9. スキル・自動化実装設計

WikiSkill の運用を支える自動化ロジックおよび決定論的スキルの構成を定義する。

### 9.1 スキル構成一覧

| スキル名 | 格納パス | 主担当ロール | 機能概要 |
| :--- | :--- | :--- | :--- |
| **`wiki-maintainer`** | `.agents/plugins/system-dev-pipeline/skills/wiki-maintainer/` | 🛡️ `qa-engineer` | トレースやエラーログから根本原因を抽出し、`wiki/patterns/` へ新規登録・追記する。 |
| **`wiki-proposer`** | `.agents/plugins/system-dev-pipeline/skills/wiki-proposer/` | 👑 `conductor` | 蓄積された Wiki パターンから `SKILL.md` の改変パッチと `PURPOSE.md` を作成する。 |
| **複合検証ゲート (Gating)** | （`qa-engineer` 実行モード） | 🛡️ `qa-engineer` | 複合検証ゲートを実行し、合否判定とロールバックまたはコミットを制御する。 |
| **`wiki-compactor`** | `.agents/plugins/system-dev-pipeline/skills/wiki-compactor/` | 👑 `conductor` | パターンの重複統合・陳腐化退避（アーカイブ）を実行する。 |

### 9.2 オーケストレーションパイプライン（Python 擬似コード仕様）

```python
"""
WikiSkill オーケストレーション コアエンジン
"""
import os
import shutil
import subprocess
from typing import Dict, Any, List

class WikiSkillPipeline:
    def __init__(self, workspace_root: str):
        self.workspace = workspace_root
        self.raw_dir = os.path.join(workspace_root, ".system_generated/logs/raw_traces")
        self.wiki_dir = os.path.join(workspace_root, "wiki")
        self.skills_dir = os.path.join(workspace_root, ".agents/plugins/system-dev-pipeline/skills")
        self.rules_dir = os.path.join(workspace_root, ".agents/plugins/system-dev-pipeline/rules")
        self.backup_skills_dir = os.path.join(workspace_root, ".agents/backup/skills")

    def run_evolution_cycle(self, target_pattern_ids: List[str]) -> bool:
        """自己進化サイクルの実行"""
        print("[WikiSkill] 自己進化サイクルを開始します...")
        
        # 1. バックアップ作成 (ロールバック用)
        self._backup_skills_layer()
        
        try:
            # 2. Skill Proposer によるパッチ作成と適用
            proposal = self._generate_and_apply_patch(target_pattern_ids)
            
            # 3. 複合検証ゲート (Composite Gating) の実行
            gating_passed, gate_details = self._run_composite_gating()
            
            # 4. 判定記録 (Wiki層はロールバックされないため安全に記録)
            self._record_log(proposal, gating_passed, gate_details)
            
            if gating_passed:
                print(f"[WikiSkill] ゲート合格: パッチ {proposal['id']} を正式採用します。")
                self._commit_skills_layer(proposal)
                self._cleanup_backup()
                return True
            else:
                print(f"[WikiSkill] ゲート不合格: パッチ {proposal['id']} を棄却しロールバックします。")
                self._rollback_skills_layer()
                return False
                
        except Exception as e:
            print(f"[WikiSkill] 例外発生: {e}。緊急ロールバックを実行します。")
            self._rollback_skills_layer()
            raise

    def _run_composite_gating(self) -> (bool, Dict[str, Any]):
        """複合検証ゲートの実行 (静的解析 -> 整合性 -> テスト -> トークン効率)"""
        # Gate 1: 静的解析
        res1 = subprocess.run(["npm", "run", "lint"], cwd=self.workspace, capture_output=True)
        if res1.returncode != 0:
            return False, {"failed_gate": "Gate 1 (Linter)", "details": res1.stderr.decode()}

        # Gate 2: ドキュメント相互整合性 (dev-doc-reviewer)
        res2 = subprocess.run(["agy", "run", "dev-doc-reviewer"], cwd=self.workspace, capture_output=True)
        if res2.returncode != 0:
            return False, {"failed_gate": "Gate 2 (Doc Integrity)", "details": res2.stderr.decode()}

        # Gate 3: シナリオテスト (Pass Rate 100%)
        res3 = subprocess.run(["npm", "test"], cwd=self.workspace, capture_output=True)
        if res3.returncode != 0:
            return False, {"failed_gate": "Gate 3 (Scenario Tests)", "details": res3.stderr.decode()}

        # Gate 4: トークン肥大化チェック
        # (行数増加率が20%以内であることを確認)
        return True, {"failed_gate": None, "details": "All gates passed successfully."}

    def _rollback_skills_layer(self):
        """Skills層およびRules層のみを復元 (※ wiki/ は一切触らない)"""
        if os.path.exists(self.backup_skills_dir):
            shutil.rmtree(self.skills_dir)
            shutil.copytree(self.backup_skills_dir, self.skills_dir)
            print("[WikiSkill] Skills層を直前のバックアップから復元しました。Wiki層は保持されています。")

    def _backup_skills_layer(self):
        if os.path.exists(self.backup_skills_dir):
            shutil.rmtree(self.backup_skills_dir)
        shutil.copytree(self.skills_dir, self.backup_skills_dir)
```

---

## 10. 今後の移行計画とロードマップ

[V2.1検討方針書.md](./V2.1検討方針書.md) のロードマップに基づき、本設計書（Step 2）の成果を以下の順序でシステムへ反映する。

| ステップ | 実施内容 | 主な成果物 |
| :--- | :--- | :--- |
| **Step 2 (完了)** | **WikiSkill 統合設計の策定**<br>・3層ストレージモデル、Context Isolation、複合検証ゲート、Compactorの設計 | 本ドキュメント (`docs/V2.1/WikiSkill統合設計書.md`) |
| **Step 3 (次工程)** | **定量測定・フィードバック設計**<br>・トークン効率、品質指標、テンプレート還元サイクルの策定 | `docs/V2.1/定量測定・フィードバック設計書.md` |
| **Step 4** | **エージェント・スキル・テンプレート再構成**<br>・`./wiki/` 構造の初期展開<br>・`dev-phase8-rules` および `qa-engineer` への WikiSkill 機能実装 | `.agents/plugins/system-dev-pipeline/` 配下の改訂反映 |
| **Step 5** | **総合検証とV2.1正式リリース**<br>・モック開発案件での自己進化ループとロールバック検証<br>・V2.1 リリースノートおよび運用基準書の確定 | V2.1 リリースノート、運用基準書 |

---

## 11. 関連ドキュメント・リンク

- [テンプレート配置形態およびナレッジ境界設計書.md](./テンプレート配置形態およびナレッジ境界設計書.md) - テンプレート配置形態（グローバル/ローカル）とTier 1/2ナレッジ境界設計書
- [エージェント設計書V2.1.md](./エージェント設計書V2.1.md) - V2.1 5大エージェント協調・権限設計書
- [状態管理機構設計書V2.1.md](./状態管理機構設計書V2.1.md) - V2.1 Single Writer状態管理詳細設計書
- [動的登録フォールバック仕様書V2.1.md](./動的登録フォールバック仕様書V2.1.md) - コンダクター動的エージェントロード仕様書
- [エージェント推論モデル仕様および運用基準書V2.1.md](./エージェント推論モデル仕様および運用基準書V2.1.md) - モデル選定・運用基準書
- [パイプライン統合およびテンプレート再編集における配慮事項まとめV2.1.md](./パイプライン統合およびテンプレート再編集における配慮事項まとめV2.1.md) - 統合・再編集7大配慮事項
- [エージェント間知見蓄積運用基準書V2.1.md](./エージェント間知見蓄積運用基準書V2.1.md) - V2.1 知見蓄積・運用基準書 (Tier 1/2 二層分離・評価適正化)
- [定量測定・フィードバック設計書.md](./定量測定・フィードバック設計書.md) - V2.1 開発支援システム定量測定・フィードバック詳細設計書
- [レビューシステム設計書.md](./レビューシステム設計書.md) - V2.1 3大レビューシステムの詳細設計書
- [AI駆動システム開発フェーズ定義書V2.1.md](./AI駆動システム開発フェーズ定義書V2.1.md) - V2.1 開発ライフサイクル定義書
- [V2.1検討方針書.md](./V2.1検討方針書.md) - V2.1 全体検討方針と3大重点テーマ
- [wikiskill.md](../../検討課題/V2.1/wikiskill.md) - WikiSkill アーキテクチャと実装仕様解説書
- [WikiSkill導入評価書.md](../../検討課題/V2.1/WikiSkill導入評価書.md) - WikiSkill 導入評価書
- [V2.1へ向けた検討課題.md](../../検討課題/V2.1/V2.1へ向けた検討課題.md) - V2.1 拡張論点・検討課題集
- [エージェント間知見蓄積運用基準書.md](../V2.0/エージェント間知見蓄積運用基準書.md) - 旧V2.0の知見蓄積・運用基準書
- [AI駆動システム開発フェーズ定義書V2.md](../V2.0/AI駆動システム開発フェーズ定義書V2.md) - 旧V2.0のフェーズ定義
- [状態管理機構設計書.md](../V2.0/状態管理機構設計書.md) - 旧V2.0の状態管理仕様書
