---
name: wiki-proposer
description: "PHASE 8 において Tier 2 汎用Wikiパターンからスキル・ルール改善パッチを立案し、PURPOSE.md生成、昇格サマリ更新、動作モードに応じた差分出力を行うスキル。"
---

# スキル進化提案 (wiki-proposer) スキル

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **委譲先 (検証時)**: 🛡️ 品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) (Gating Tester)
- **適用フェーズ**: PHASE 8 (知見昇格フェーズ) および システム改訂完了時

---

## 1. 入力情報
- `./wiki/patterns/universal/` 配下の汎用知見パターン群（未昇格のもの）
- 現行のスキル群（`.agents/plugins/system-dev-pipeline/skills/`）および開発規約（`rules/dev-process-standards.md`）
- `PROJECT_STATE.md`（特に `EXECUTION_MODE`: `GLOBAL_PLUGIN` または `LOCAL_STANDALONE`）

---

## 2. 処理手順

### Step 1: パターンの蒸留と一般化
Tier 2 パターンを精査し、過剰適合（特定プロジェクトのみの個別コード名や変数名）を排除して、全プロジェクト共通で活用できる抽象ルールやベストプラクティスへと一般化・蒸留する。

### Step 2: 最小パッチ (Minimal Patch) の生成
改善すべき対象スキル（`SKILL.md`）または開発規範（`rules/dev-process-standards.md`）を特定し、最小限の差分パッチを生成する。既存の指示構造を無暗に破壊してはならない。

### Step 3: `PURPOSE.md` の作成・更新
変更対象スキルのディレクトリ直下に `PURPOSE.md`（例: `skills/dev-phase4-env-build/PURPOSE.md`）を作成または追記し、以下のメタデータを記録する：
- 解決対象の Wiki パターンID（例: `PAT-ERR-001`）
- 改訂動機・背景
- 期待される改善効果（テスト失敗率低減、手順簡略化など）

### Step 4: 提示サマリ `./TEMPLATE_PROMOTIONS.md` の更新
ユーザーが昇格採否を判断できるよう、提案内容、解決課題、対象ファイル、差分要約を `./TEMPLATE_PROMOTIONS.md` に追記・提示する。

### Step 5: 動作モード別の出力・昇格ルーティング
`PROJECT_STATE.md` の `EXECUTION_MODE` を参照して安全に処理を分岐する：

- **`GLOBAL_PLUGIN` モード時**:
  - グローバル領域への自動書き込みを **厳格に禁止**。
  - 出力先ディレクトリ `./promotions/` を自動生成（`mkdir -p ./promotions`）。
  - `./promotions/{skill_name}.patch` または `./promotions/rules.patch` として差分ファイルを出力する。
  - ユーザーに対し、プラグイン管理下での適用コマンドまたは手動確認を案内する。
- **`LOCAL_STANDALONE` モード時**:
  - ローカルの `.agents/plugins/system-dev-pipeline/` 配下の対象ファイルへの反映準備を行い、検証ゲートへ回す。

### Step 6: 🛡️ qa-engineer による複合検証ゲート (Gating) の呼び出し
パッチを適用した状態で、🛡️ `qa-engineer` へ検証を依頼し、4大関門（静的解析、ドキュメント整合性、シナリオテスト、コンテキスト効率）をパスしたか検証する。不合格時はロールバックする。
