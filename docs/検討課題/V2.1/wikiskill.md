# WikiSkill アーキテクチャと実装仕様解説書
**Compiling Agent Experience into Persistent Knowledge for Skill Evolution**

---

## 1. 概要と背景

従来の自律型エージェントにおける自己改善ループ（Self-Evolution Loop）では、タスク実行ログから手順書（`SKILL.md` など）を直接修正し、検証スコアが悪化した場合は直前の状態へロールバックする手法が主流でした。しかしこの方式では、**「なぜ失敗したのか」「何を試して失敗したのか」という貴重な診断知識までスキルと一緒に破棄される**という構造的欠陥がありました。

Google Research と Virginia Tech が提唱した **WikiSkill** は、実行ログ（Raw Traces）と実行手順書（Skills）の中間に、**決してロールバックされない「永続的 Wiki 層（Persistent Knowledge Layer）」** を配置することでこの問題を解決しました。

---

## 2. 3層ストレージアーキテクチャ

WikiSkill は、エージェントの作業環境を明確に分離された3つのデータ層で管理します。

```
+---------------------------------------------------------------+
|                        WikiSkill 3層構造                      |
+---------------------------------------------------------------+

 [Raw Layer] (raw/)
   │  - 実行トレース (不変 / Immutable)
   │  - ツール入出力、推論思考ログ、最終結果
   ▼
 [Wiki Layer] (wiki/)  <─── ※ 決してロールバックされない永続層
   │  - 成功/失敗の根本原因 (wiki/patterns/*.md)
   │  - 過去の提案・採否・差分ログ (logs.md, skill-impact.md)
   ▼
 [Skills Layer] (skills/) <─── ※ 評価次第でロールバックされる実行層
      - 実行可能な手順書 (SKILL.md)
      - 動機・リンク情報 (PURPOSE.md)
```

### (1) Raw Layer (`raw/`)
* **役割**: タスク実行時の生のログ。
* **特性**: **完全イミュータブル（追記のみ、変更不可）**。
* **内容**: ReAct 形式の推論ステップ、Tool Calls の引数と戻り値、環境の例外、最終解答。

### (2) Wiki Layer (`wiki/`)
* **役割**: 生ログから抽出・一般化された構造化ナレッジベース。
* **特性**: **永続的（Gating でスキルが不合格になってもロールバックされない）**。
* **内容**:
  * `patterns/{category}_{pattern_id}.md`: エラー分類、失敗のトリガー、成功パターン。
  * `logs.md`: これまでに提案されたパッチ、検証スコア差分、採否の履歴。
  * `skill-impact.md`: どのパターンがどのスキルの性能向上に寄与したかの因果追跡。

### (3) Skills Layer (`skills/`)
* **役割**: 推論エージェントがタスク実行時にシステムプロンプトや外部ツール定義として直接読み込む実行可能コード・指示書。
* **特性**: **可変・ロールバック対象**（検証スコアが低下した場合は以前のコミットに戻る）。
* **内容**:
  * `SKILL.md`: 手順やルールの実体。
  * `PURPOSE.md`: そのスキル（またはパッチ）がどの Wiki パターンを解決するために作成されたかを示すメタデータ。

---

## 3. 4つのコンポーネントとライフサイクル

WikiSkill の進化ループは、役割の異なる4つの独立コンポーネントによって駆動します。

```
                  ┌──────────────────────────────┐
                  │ 1. Inference Agent (推論)    │
                  └──────────────┬───────────────┘
                                 │ 実行トレース
                                 ▼
                  ┌──────────────────────────────┐
                  │ 2. Wiki Maintainer (維持・整理)│
                  └──────────────┬───────────────┘
                                 │ 知識抽出・蓄積
                                 ▼
                  ┌──────────────────────────────┐
                  │ 3. Skill Proposer (スキル立案) │
                  └──────────────┬───────────────┘
                                 │ スキル更新案 (Patch)
                                 ▼
                  ┌──────────────────────────────┐
                  │ 4. Gating & Rollback (検証)  │
                  └──────────────┬───────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
           [合格: スコア向上]              [不合格: スコア低下]
            Skills層へマージ                  Skills層をリセット
                                        (※Wiki層の知識は保持)
```

### 1. Inference Agent（推論エージェント）
* タスクを実行する主体。
* **重要原則**: **Inference Agent には Wiki 層を直接見せない**。
  * アブレーション研究により、推論時に Wiki を直接参照させると、その場しのぎのパッチワーク的解決に依存し、スキル自体の汎化性能が低下することが判明しています。
  * 参照できるのは整理・蒸留された `skills/SKILL.md` のみです。

### 2. Wiki Maintainer（Wiki 保守エージェント）
* Raw トレースからサンプリングされた成功・失敗ログを分析。
* 失敗の根本原因（Root Cause Analysis）を導出し、`wiki/patterns/` を新規作成または更新。
* 過去の提案履歴と照合し、「過去に失敗したアプローチと同じ轍を踏んでいないか」をチェック。

### 3. Skill Proposer（スキル提案エージェント）
* 現在の `skills/`、蓄積された `wiki/patterns/`、および過去の `logs.md` をインプットとして受領。
* 特定の失敗パターンを克服するための `SKILL.md` の追加・修正パッチを作成。
* 同時に `PURPOSE.md` に「どの Wiki パターンを対象にした変更か」を記録。

### 4. Gating & Rollback（評価ゲート機構）
* 提案された新しい `SKILL.md` を適用した状態で、バリデーションデータセットを実行。
* スコア比較:
  $$Score_{\text{new}} > Score_{\text{baseline}}$$
  * **合格時**: 提案を採用し、新しいスキルバージョンとして確定。
  * **不合格時**: `skills/` を直前の状態にロールバック。ただし **Wiki Maintainer が記録した `wiki/` の知識や採否ログはそのまま残す**。

---

## 4. ディレクトリ構成とデータフォーマット

WikiSkill の実装における標準的なファイルツリーとデータ構造です。

```
workspace/
├── raw/
│   └── 20261005_task_042_trace.json
├── wiki/
│   ├── patterns/
│   │   ├── PAT-001_math_rounding_error.md
│   │   └── PAT-002_table_header_mismatch.md
│   ├── logs.md
│   └── skill-impact.md
└── skills/
    ├── math_solver/
    │   ├── SKILL.md
    │   └── PURPOSE.md
    └── spreadsheet_extractor/
        ├── SKILL.md
        └── PURPOSE.md
```

### データ例: `wiki/patterns/PAT-001_math_rounding_error.md`
```markdown
# PAT-001: 浮動小数点計算時の丸め誤差による不整合

## 発生状況
- 対象ドメイン: 数値解析 / 表データ集計
- 観測された挙動: 中間計算で Python の float をそのまま使用したため、最終判定で 0.0000001 のズレが発生しテスト不合格。

## 根本原因
- IEEE 754 浮動小数点の丸め誤差。
- `Decimal` モジュールまたは有理数表現を使用していない。

## 推奨介入策
- 通貨および厳密な数値一致が求められるタスクでは `decimal.Decimal` を強制する。
- スキル側に「小数の等価判定には丸め許容値（epsilon）を設ける」手順を明記すること。
```

### データ例: `skills/math_solver/PURPOSE.md`
```markdown
# Skill Purpose & Lineage
- Target Skill: math_solver
- Linked Wiki Pattern: PAT-001_math_rounding_error.md
- Motivation: 中間計算の丸め誤差によるテスト失敗を防止するため、計算手順に Decimal の使用を義務付け。
- Proposal Iteration: Round-3
```

---

## 5. 実装ロジック（Python 擬似コード）

WikiSkill のオーケストレーションパイプラインのコアロジックです。

```python
import os
import shutil
from typing import Dict, Any

class WikiSkillOrchestrator:
    def __init__(self, workspace_path: str, agent_llm, val_dataset):
        self.workspace = workspace_path
        self.raw_dir = os.path.join(workspace_path, "raw")
        self.wiki_dir = os.path.join(workspace_path, "wiki")
        self.skills_dir = os.path.join(workspace_path, "skills")
        self.backup_skills_dir = os.path.join(workspace_path, "skills_backup")
        
        self.llm = agent_llm
        self.val_dataset = val_dataset
        self.baseline_score = 0.0

    def run_evolution_cycle(self, train_tasks: list):
        # 1. Inference: 現在のスキルのみを用いてタスクを実行
        traces = []
        for task in train_tasks:
            trace = self._run_inference_agent(task, skills_path=self.skills_dir)
            self._save_raw_trace(trace)
            traces.append(trace)

        # 2. Wiki Maintenance: トレースを分析し Wiki を更新（永続化）
        sampled_failures = [t for t in traces if not t["success"]]
        sampled_successes = [t for t in traces if t["success"]]
        self._run_wiki_maintainer(sampled_failures, sampled_successes)

        # 3. Skill Proposal: Wiki と履歴を元にスキル修正案を作成
        # バックアップの作成（ロールバック用）
        self._backup_skills()
        
        proposal = self._run_skill_proposer()
        self._apply_patch_to_skills(proposal)

        # 4. Gating & Validation: 検証セットでの性能評価
        new_score = self._evaluate_skills(self.val_dataset)
        
        # 採否判定ログを記録（Wiki層に記録するため、破棄されない）
        self._record_proposal_log(proposal, new_score, self.baseline_score)

        if new_score > self.baseline_score:
            print(f"[Adopted] スコア向上: {self.baseline_score:.3f} -> {new_score:.3f}")
            self.baseline_score = new_score
            self._commit_skills()
        else:
            print(f"[Rejected] スコア改善なし: {new_score:.3f} <= {self.baseline_score:.3f}. ロールバック実行。")
            self._rollback_skills()
            # ※ 注意: self.wiki_dir はロールバックしない

    def _run_inference_agent(self, task: Dict[str, Any], skills_path: str) -> Dict[str, Any]:
        """推論エージェント。スキルのみを注入し、Wikiは見せない"""
        skills_content = self._load_all_skills(skills_path)
        prompt = f"Available Skills:\n{skills_content}\n\nTask: {task['query']}"
        # LLM実行とトレース生成
        return self.llm.execute_with_trace(prompt)

    def _run_wiki_maintainer(self, failures: list, successes: list):
        """ログを分析して patterns/*.md や logs.md を更新"""
        prompt = (
            "Analyze these traces. Extract recurring root causes of failure "
            "and update wiki/patterns with actionable advice."
        )
        # Wiki 領域のみを更新
        self.llm.update_wiki(self.wiki_dir, failures, successes)

    def _run_skill_proposer(self) -> Dict[str, Any]:
        """Wiki のパターンと過去ログを読んで SKILL.md の更新パッチを作成"""
        wiki_patterns = self._load_directory(os.path.join(self.wiki_dir, "patterns"))
        history_logs = self._read_file(os.path.join(self.wiki_dir, "logs.md"))
        
        prompt = f"Wiki Patterns:\n{wiki_patterns}\nHistory:\n{history_logs}\nPropose a skill edit."
        return self.llm.generate_skill_patch(prompt)

    def _rollback_skills(self):
        """Skills 層のみをバックアップから復元"""
        shutil.rmtree(self.skills_dir)
        shutil.copytree(self.backup_skills_dir, self.skills_dir)

    def _backup_skills(self):
        if os.path.exists(self.backup_skills_dir):
            shutil.rmtree(self.backup_skills_dir)
        shutil.copytree(self.skills_dir, self.backup_skills_dir)
```

---

## 6. 実装・運用上の注意点と技術課題

### (1) コンテキスト汚染の防止（Why hide Wiki from Inference?）
Inference Agent に `wiki/patterns/` を直接参照させると、プロンプトのコンテキスト長を圧迫するだけでなく、特定事例に過剰適合（Overfitting）した場当たり的な分岐コードを記述し始めます。
**「Wiki は抽象化・蓄積の場」「Skills は蒸留された実行手順」** という責務分離の厳守が性能の鍵となります。

### (2) Wiki Pruning（自動枝刈り）
Wiki は追記型でロールバックされないため、反復回数が進むとパターンファイルが肥大化します。
* **課題**: `Skill Proposer` が読み込むトークン数の増加と競合パターンの発生。
* **対策**: 数サイクルごとに「Wiki Compactor / Consolidator」エージェントを走らせ、重複したパターンを統合・陳腐化した記述をアーカイブする仕組みの実装が推奨されます。

### (3) Gating データセットの独立性
* ゲート判定で過学習を起こさないよう、検証セット（Validation Set）は推論エージェントが自己進化で参照する訓練タスクとは完全に分離されたベンチマークを用意する必要があります。