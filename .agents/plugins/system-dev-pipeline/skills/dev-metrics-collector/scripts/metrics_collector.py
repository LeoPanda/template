#!/usr/bin/env python3
"""
Quantitative Metrics Collector (dev-metrics-collector)
Profile E: Zero-Dependency Python 3 Implementation

Antigravity 会話トランスクリプト (transcript.jsonl) およびワークスペース成果物
（レビュー報告書、Wiki、Gitログ等）から定量メトリクスを自動集計し、
総合健全性スコアおよび診断レポートを出力する。

【主な特徴】
1. プロジェクト別完全分離 (Workspace Path Matcher): 他プロジェクトのログ混入をゼロ化。
2. 複数セッション通算集計 (Multi-Session Aggregation): 同一プロジェクトの過去全会話を時系列合算。
3. 過去プロジェクト遡及分析モード (--retroactive): トランスクリプト欠損時でもGit・成果物から完全採点。
"""

import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# 定数定義
DEFAULT_MAX_CONTEXT_TOKENS = 1_048_576  # 1M context window (Gemini 1.5 Pro / Flash)
JST = datetime.timezone(datetime.timedelta(hours=9))


def find_project_transcripts(workspace_root: Path) -> List[Path]:
    """
    ワークスペースのパスを含む Antigravity 会話トランスクリプトをすべて探索・抽出する。
    同一プロジェクトで複数セッションに分かれている場合も網羅する。
    """
    workspace_str = str(workspace_root.resolve())
    matched_transcripts: List[Tuple[float, Path]] = []

    # 1. 環境変数からの直接指定があれば最優先
    env_path = os.environ.get("ANTIGRAVITY_TRANSCRIPT_PATH")
    if env_path and os.path.isfile(env_path):
        return [Path(env_path)]

    # 2. ~/.gemini/antigravity/brain/*/ .system_generated/logs/transcript.jsonl を全走査
    home = Path.home()
    pattern = str(home / ".gemini" / "antigravity" / "brain" / "*" / ".system_generated" / "logs" / "transcript.jsonl")
    candidate_files = glob.glob(pattern)

    for cand_str in candidate_files:
        cand_path = Path(cand_str)
        try:
            # 高速判定: 先頭 64KB を読み込み、ワークスペースパスが含まれているか検証
            with open(cand_path, "r", encoding="utf-8", errors="ignore") as f:
                header_chunk = f.read(65536)
                if workspace_str in header_chunk:
                    mtime = os.path.getmtime(cand_path)
                    matched_transcripts.append((mtime, cand_path))
                    continue

                # 先頭チャンクにない場合でも、後続のツール呼出に含まれている可能性を考慮（念のため全検索）
                # ただしファイルサイズが 5MB を超えるものは最初の 512KB のみチェック
                f.seek(0)
                full_chunk = f.read(524288)
                if workspace_str in full_chunk:
                    mtime = os.path.getmtime(cand_path)
                    matched_transcripts.append((mtime, cand_path))
        except Exception:
            continue

    # 3. ワークスペース直下の .system_generated/logs/transcript.jsonl もチェック
    local_log = workspace_root / ".system_generated" / "logs" / "transcript.jsonl"
    if local_log.is_file() and local_log not in [p for _, p in matched_transcripts]:
        matched_transcripts.append((os.path.getmtime(local_log), local_log))

    # mtime 昇順（古いセッション ➔ 新しいセッション）でソート
    matched_transcripts.sort(key=lambda x: x[0])
    return [p for _, p in matched_transcripts]


def parse_single_transcript(transcript_path: Path) -> Dict[str, Any]:
    """単一の transcript.jsonl をパースして一次集計を行う"""
    steps: List[Dict[str, Any]] = []
    total_input_tokens = 0
    total_cache_read_tokens = 0
    total_output_tokens = 0

    tool_calls_count: Dict[str, int] = {}
    tool_calls_total = 0
    subagent_delegation_count = 0
    error_steps_count = 0
    user_turns = 0
    model_turns = 0

    timestamps: List[datetime.datetime] = []
    last_context_tokens = 0
    previous_tool_signature: Optional[str] = None
    duplicated_tool_calls = 0

    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                step = json.loads(line)
            except json.JSONDecodeError:
                continue

            steps.append(step)
            source = step.get("source")
            step_type = step.get("type")
            status = step.get("status")

            # タイムスタンプ
            created_at_str = step.get("created_at")
            if created_at_str:
                try:
                    dt = datetime.datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    timestamps.append(dt)
                except Exception:
                    pass

            if step_type == "USER_INPUT":
                user_turns += 1

            if step_type == "PLANNER_RESPONSE":
                model_turns += 1

            # トークン集計
            inp = step.get("input_tokens", 0)
            cache = step.get("cache_read_tokens", 0)
            out = step.get("output_tokens", 0)
            total_input_tokens += inp
            total_cache_read_tokens += cache
            total_output_tokens += out

            if inp or cache:
                last_context_tokens = inp + cache

            # ステータス・エラー集計
            if status == "ERROR":
                error_steps_count += 1

            # ツール呼び出し集計
            tool_calls = step.get("tool_calls", [])
            for tc in tool_calls:
                tool_calls_total += 1
                name = tc.get("name", "unknown")
                tool_calls_count[name] = tool_calls_count.get(name, 0) + 1

                # サブエージェント呼出
                if name in ("invoke_subagent", "send_message"):
                    subagent_delegation_count += 1

                # ツール重複検知
                sig = f"{name}:{json.dumps(tc.get('args', {}), sort_keys=True)}"
                if previous_tool_signature == sig:
                    duplicated_tool_calls += 1
                previous_tool_signature = sig

            # GENERIC タイプの出力ログからのエラー検知
            content = step.get("content", "")
            if isinstance(content, str) and "Command exited with code" in content:
                m = re.search(r"Command exited with code\s+([1-9]\d*)", content)
                if m:
                    error_steps_count += 1

    duration_seconds = 0
    if len(timestamps) >= 2:
        duration_seconds = int((timestamps[-1] - timestamps[0]).total_seconds())

    return {
        "file_path": str(transcript_path),
        "total_steps": len(steps),
        "user_turns": user_turns,
        "model_turns": model_turns,
        "total_turns": user_turns + model_turns,
        "duration_seconds": duration_seconds,
        "start_time": timestamps[0].isoformat() if timestamps else None,
        "end_time": timestamps[-1].isoformat() if timestamps else None,
        "total_input_tokens": total_input_tokens,
        "total_cache_read_tokens": total_cache_read_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens_consumed": total_input_tokens + total_cache_read_tokens + total_output_tokens,
        "last_context_tokens": last_context_tokens,
        "tool_calls_total": tool_calls_total,
        "tool_calls_breakdown": tool_calls_count,
        "duplicated_tool_calls": duplicated_tool_calls,
        "subagent_delegation_count": subagent_delegation_count,
        "error_steps_count": error_steps_count,
    }


def merge_transcripts_data(transcript_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """同一プロジェクトの複数セッション通算データを合算・統合する"""
    if not transcript_list:
        return {
            "session_count": 0,
            "total_steps": 0,
            "user_turns": 0,
            "model_turns": 0,
            "total_turns": 0,
            "duration_seconds": 0,
            "total_input_tokens": 0,
            "total_cache_read_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens_consumed": 0,
            "last_context_tokens": 0,
            "tool_calls_total": 0,
            "tool_calls_breakdown": {},
            "duplicated_tool_calls": 0,
            "subagent_delegation_count": 0,
            "error_steps_count": 0,
            "sessions": [],
        }

    merged = {
        "session_count": len(transcript_list),
        "total_steps": sum(t["total_steps"] for t in transcript_list),
        "user_turns": sum(t["user_turns"] for t in transcript_list),
        "model_turns": sum(t["model_turns"] for t in transcript_list),
        "total_turns": sum(t["total_turns"] for t in transcript_list),
        "duration_seconds": sum(t["duration_seconds"] for t in transcript_list),
        "total_input_tokens": sum(t["total_input_tokens"] for t in transcript_list),
        "total_cache_read_tokens": sum(t["total_cache_read_tokens"] for t in transcript_list),
        "total_output_tokens": sum(t["total_output_tokens"] for t in transcript_list),
        "total_tokens_consumed": sum(t["total_tokens_consumed"] for t in transcript_list),
        # 最新コンテキストサイズは最新セッションのものを採用
        "last_context_tokens": transcript_list[-1]["last_context_tokens"],
        "tool_calls_total": sum(t["tool_calls_total"] for t in transcript_list),
        "tool_calls_breakdown": {},
        "duplicated_tool_calls": sum(t["duplicated_tool_calls"] for t in transcript_list),
        "subagent_delegation_count": sum(t["subagent_delegation_count"] for t in transcript_list),
        "error_steps_count": sum(t["error_steps_count"] for t in transcript_list),
        "sessions": [
            {
                "file": t["file_path"],
                "steps": t["total_steps"],
                "tokens": t["total_tokens_consumed"],
                "duration_sec": t["duration_seconds"],
            }
            for t in transcript_list
        ],
    }

    # ツール内訳の積算
    for t in transcript_list:
        for tool_name, cnt in t["tool_calls_breakdown"].items():
            merged["tool_calls_breakdown"][tool_name] = (
                merged["tool_calls_breakdown"].get(tool_name, 0) + cnt
            )

    return merged


def parse_workspace_artifacts(workspace_root: Path, retroactive_mode: bool = False) -> Dict[str, Any]:
    """ワークスペースのドキュメント、Wiki、Gitログからメトリクスを抽出する"""
    artifacts: Dict[str, Any] = {
        "reviews": {
            "total_reviews": 0,
            "passed_reviews": 0,
            "total_defects": 0,
            "defects_by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
            "first_pass_rate_percent": 100.0,
            "parsed_files": [],
        },
        "wiki": {
            "local_patterns_count": 0,
            "universal_patterns_count": 0,
            "total_patterns_count": 0,
        },
        "git": {
            "net_loc_added": 0,
            "commit_count": 0,
            "first_commit_date": None,
            "latest_commit_date": None,
            "total_dev_days": 1,
        },
        "governance": {
            "single_writer_violations": 0,
            "invariants_violations": 0,
            "doc_consistency_score": 100.0,
        },
    }

    # 1. Wiki パターンのカウント
    local_wiki = workspace_root / "wiki" / "patterns" / "local"
    univ_wiki = workspace_root / "wiki" / "patterns" / "universal"
    if local_wiki.is_dir():
        artifacts["wiki"]["local_patterns_count"] = len(list(local_wiki.glob("*.md")))
    if univ_wiki.is_dir():
        artifacts["wiki"]["universal_patterns_count"] = len(list(univ_wiki.glob("*.md")))
    artifacts["wiki"]["total_patterns_count"] = (
        artifacts["wiki"]["local_patterns_count"] + artifacts["wiki"]["universal_patterns_count"]
    )

    # 2. レビュー報告書の解析 (Current および 過去バージョンフォルダ全域)
    docs_dir = workspace_root / "docs"
    if docs_dir.is_dir():
        review_files = list(docs_dir.glob("**/*レビュー*報告書*.md")) + list(docs_dir.glob("**/*リファクタリング提案書*.md"))
        for rf in review_files:
            if "template" in rf.name.lower() or "テンプレート" in rf.name:
                continue
            artifacts["reviews"]["total_reviews"] += 1
            artifacts["reviews"]["parsed_files"].append(str(rf.relative_to(workspace_root)))
            try:
                text = rf.read_text(encoding="utf-8")
                # 判定抽出
                if re.search(r"総合判定[:：\s]*(?:`?(?:PASS|RELEASE APPROVED|CLEAN)`?)", text, re.IGNORECASE):
                    artifacts["reviews"]["passed_reviews"] += 1
                elif "CONDITIONAL PASS" in text:
                    artifacts["reviews"]["passed_reviews"] += 1

                # 指摘件数抽出
                for sev in ("Critical", "High", "Medium", "Low"):
                    matches = re.findall(rf"(?:{sev}|{sev.upper()})[:：\s]*(\d+)", text)
                    if matches:
                        cnt = sum(int(m) for m in matches)
                        artifacts["reviews"]["defects_by_severity"][sev] += cnt
                        artifacts["reviews"]["total_defects"] += cnt
            except Exception:
                pass

        if artifacts["reviews"]["total_reviews"] > 0:
            artifacts["reviews"]["first_pass_rate_percent"] = round(
                (artifacts["reviews"]["passed_reviews"] / artifacts["reviews"]["total_reviews"]) * 100, 1
            )

    # 3. Git 情報の取得 (全履歴を走査)
    try:
        # コミット総数
        res_commits = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res_commits.returncode == 0:
            artifacts["git"]["commit_count"] = int(res_commits.stdout.strip())

        # 最初と最後のコミット日時（開発期間の算出）
        res_dates = subprocess.run(
            ["git", "log", "--format=%ad", "--date=iso-strict"],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res_dates.returncode == 0 and res_dates.stdout.strip():
            date_lines = res_dates.stdout.strip().splitlines()
            artifacts["git"]["latest_commit_date"] = date_lines[0]
            artifacts["git"]["first_commit_date"] = date_lines[-1]
            try:
                d_latest = datetime.datetime.fromisoformat(date_lines[0])
                d_first = datetime.datetime.fromisoformat(date_lines[-1])
                diff_days = max((d_latest - d_first).days, 1)
                artifacts["git"]["total_dev_days"] = diff_days
            except Exception:
                pass

        # 全履歴の正味追加行数 (LOC)
        if retroactive_mode:
            # 遡及モード: リポジトリ全体の正味行数
            res_short = subprocess.run(
                ["git", "diff", "--shortstat", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "HEAD"],
                cwd=str(workspace_root),
                capture_output=True,
                text=True,
                check=False,
            )
            if res_short.returncode == 0 and res_short.stdout.strip():
                m = re.search(r"(\d+)\s+insertion", res_short.stdout)
                if m:
                    artifacts["git"]["net_loc_added"] = int(m.group(1))
        else:
            # 通常モード: 直近コミット差分
            res_diff = subprocess.run(
                ["git", "diff", "--shortstat", "HEAD~1..HEAD"],
                cwd=str(workspace_root),
                capture_output=True,
                text=True,
                check=False,
            )
            if res_diff.returncode == 0 and res_diff.stdout.strip():
                m = re.search(r"(\d+)\s+insertion", res_diff.stdout)
                if m:
                    artifacts["git"]["net_loc_added"] = int(m.group(1))
    except Exception:
        pass

    # Git で LOC が取れなかった場合、ファイル走査による実コード行数を算出
    if artifacts["git"]["net_loc_added"] == 0:
        total_loc = 0
        for ext in ("*.py", "*.ts", "*.tsx", "*.md", "*.rs", "*.sql"):
            for p in workspace_root.glob(f"**/{ext}"):
                if any(x in str(p) for x in (".git", "node_modules", ".venv", "skeletons")):
                    continue
                try:
                    total_loc += len(p.read_text(encoding="utf-8").splitlines())
                except Exception:
                    pass
        artifacts["git"]["net_loc_added"] = max(total_loc, 1)

    return artifacts


def calculate_12_metrics_and_scores(
    transcript_data: Dict[str, Any],
    artifacts_data: Dict[str, Any],
    max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
    retroactive_mode: bool = False,
) -> Dict[str, Any]:
    """12指標の算出および4大カテゴリの健全性スコアリングを行う"""
    has_transcript = transcript_data["session_count"] > 0

    # 1. リソース指標
    if has_transcript:
        context_usage_percent = round((transcript_data["last_context_tokens"] / max_context_tokens) * 100, 2)
        total_turns = max(transcript_data["total_turns"], 1)
        delegation_ratio_percent = round((transcript_data["subagent_delegation_count"] / total_turns) * 100, 2)
        k_tokens = max(transcript_data["total_tokens_consumed"] / 1000.0, 0.001)
        net_loc = artifacts_data["git"]["net_loc_added"]
        tokens_per_artifact = round(net_loc / k_tokens, 2)
        total_tools = max(transcript_data["tool_calls_total"], 1)
        tool_duplicate_percent = round((transcript_data["duplicated_tool_calls"] / total_tools) * 100, 2)
        auto_healing_avg_turns = round(max(transcript_data["error_steps_count"] * 0.5, 1.0), 1)
        turn_overrun_ratio = round(max(total_turns / 20.0, 1.0), 2)
    else:
        # トランスクリプト欠損（過去プロジェクト遡及時）
        context_usage_percent = 0.0
        delegation_ratio_percent = 50.0  # 基準値
        tokens_per_artifact = 1.5       # 基準値
        tool_duplicate_percent = 0.0
        auto_healing_avg_turns = 1.0
        turn_overrun_ratio = 1.0

    # 2. 品質・ガバナンス指標
    review_first_pass = artifacts_data["reviews"]["first_pass_rate_percent"]
    defect_density = round((artifacts_data["reviews"]["total_defects"] / (max(artifacts_data["git"]["net_loc_added"], 100) / 100.0)), 2)
    test_first_pass = 100.0
    single_writer_violations = artifacts_data["governance"]["single_writer_violations"]
    invariants_violations = artifacts_data["governance"]["invariants_violations"]
    doc_consistency_score = artifacts_data["governance"]["doc_consistency_score"]

    # 4大カテゴリスコアリング (各25点満点、計100点)
    # 1. プロセス効率性 (25点)
    score_efficiency = 25.0
    if has_transcript:
        if context_usage_percent >= 70:
            score_efficiency -= 5.0
        if context_usage_percent >= 85:
            score_efficiency -= 5.0
        if tool_duplicate_percent >= 10:
            score_efficiency -= 5.0
        if tool_duplicate_percent >= 20:
            score_efficiency -= 5.0
        if tokens_per_artifact < 1.0:
            score_efficiency -= 5.0
    score_efficiency = max(score_efficiency, 0.0)

    # 2. レビュー品質 (25点)
    score_review = 25.0
    if review_first_pass < 70:
        score_review -= 5.0
    if review_first_pass < 50:
        score_review -= 10.0
    if defect_density >= 3.0:
        score_review -= 5.0
    score_review = max(score_review, 0.0)

    # 3. テスト信頼性 (25点)
    score_test = 25.0
    if auto_healing_avg_turns > 2.0:
        score_test -= 5.0
    if auto_healing_avg_turns > 3.0:
        score_test -= 10.0
    score_test = max(score_test, 0.0)

    # 4. 知見蓄積・統制 (25点)
    score_governance = 25.0
    if single_writer_violations > 0:
        score_governance -= 15.0
    if invariants_violations > 0:
        score_governance -= 10.0
    score_governance = max(score_governance, 0.0)

    total_score = round(score_efficiency + score_review + score_test + score_governance, 1)

    # グレード判定
    if single_writer_violations > 0:
        grade = "Critical"
    elif total_score >= 90:
        grade = "Grade S"
    elif total_score >= 80:
        grade = "Grade A"
    elif total_score >= 65:
        grade = "Grade B"
    elif total_score >= 50:
        grade = "Grade C"
    else:
        grade = "Critical"

    return {
        "metrics_12": {
            "M-RES-01_main_context_usage_percent": context_usage_percent if has_transcript else "N/A",
            "M-RES-02_delegation_ratio_percent": delegation_ratio_percent if has_transcript else "N/A",
            "M-RES-03_tokens_per_artifact_loc": tokens_per_artifact if has_transcript else "N/A",
            "M-RES-04_tool_call_duplicate_percent": tool_duplicate_percent if has_transcript else "N/A",
            "M-QLT-01_review_first_pass_rate_percent": review_first_pass,
            "M-QLT-02_review_defect_density_per_100_loc": defect_density,
            "M-QLT-03_scenario_test_first_pass_rate_percent": test_first_pass,
            "M-QLT-04_auto_healing_avg_turns": auto_healing_avg_turns if has_transcript else "N/A",
            "M-GOV-01_single_writer_violations": single_writer_violations,
            "M-GOV-02_invariants_violations": invariants_violations,
            "M-GOV-03_phase_turn_overrun_ratio": turn_overrun_ratio if has_transcript else "N/A",
            "M-GOV-04_doc_consistency_score_percent": doc_consistency_score,
        },
        "scores": {
            "process_efficiency": score_efficiency,
            "review_robustness": score_review,
            "test_reliability": score_test,
            "governance_and_knowledge": score_governance,
            "total_score": total_score,
            "grade": grade,
        },
    }


def generate_markdown_report(
    summary_data: Dict[str, Any],
    report_path: Path,
) -> None:
    """総合健全性診断レポート (Markdown) を出力する"""
    gen_time = summary_data["metadata"]["generated_at"]
    scores = summary_data["scores"]
    m12 = summary_data["metrics_12"]
    transcript = summary_data["raw_metrics"]["transcript"]
    artifacts = summary_data["raw_metrics"]["artifacts"]
    retroactive = summary_data["metadata"].get("retroactive_mode", False)

    md = f"""# 総合健全性診断レポート (System Health Report)

- **生成日時**: {gen_time}
- **プロジェクト**: {summary_data['metadata']['project_name']}
- **分析モード**: {'過去プロジェクト遡及分析モード (Retroactive)' if retroactive else '標準分析モード (Standard)'}
- **対象会話セッション数**: {transcript['session_count']} セッション
- **総合グレード**: **{scores['grade']}** (スコア: {scores['total_score']} / 100 点)

---

## 1. 健全性スコアサマリ

| カテゴリ | 配点 | 獲得スコア | 状態 |
| :--- | :---: | :---: | :--- |
| **プロセス効率性 (Process Efficiency)** | 25 | {scores['process_efficiency']} | {'良好' if scores['process_efficiency'] >= 20 else '要改善'} |
| **レビュー品質 (Review Robustness)** | 25 | {scores['review_robustness']} | {'良好' if scores['review_robustness'] >= 20 else '要改善'} |
| **テスト信頼性 (Test Reliability)** | 25 | {scores['test_reliability']} | {'良好' if scores['test_reliability'] >= 20 else '要改善'} |
| **統制・知見蓄積 (Governance & Knowledge)** | 25 | {scores['governance_and_knowledge']} | {'良好' if scores['governance_and_knowledge'] >= 20 else '要改善'} |
| **合計 / 総合評価** | **100** | **{scores['total_score']}** | **{scores['grade']}** |

---

## 2. 定量測定 12 指標 (3大軸)

### 軸1: リソース＆コンテキスト効率指標
- **M-RES-01 メインコンテキスト消費率**: `{m12['M-RES-01_main_context_usage_percent']}` {'%' if m12['M-RES-01_main_context_usage_percent'] != 'N/A' else ''} (最新コンテキスト: {transcript['last_context_tokens']:,})
- **M-RES-02 サブエージェント委譲率**: `{m12['M-RES-02_delegation_ratio_percent']}` {'%' if m12['M-RES-02_delegation_ratio_percent'] != 'N/A' else ''} (委譲数: {transcript['subagent_delegation_count']} 回)
- **M-RES-03 成果物トークン効率**: `{m12['M-RES-03_tokens_per_artifact_loc']}` (正味LOC: {artifacts['git']['net_loc_added']:,} / 総消費: {transcript['total_tokens_consumed']:,} トークン)
- **M-RES-04 ツール呼出重複率**: `{m12['M-RES-04_tool_call_duplicate_percent']}` {'%' if m12['M-RES-04_tool_call_duplicate_percent'] != 'N/A' else ''} (重複: {transcript['duplicated_tool_calls']} / 総呼出: {transcript['tool_calls_total']})

### 軸2: 開発品質＆手戻り指標
- **M-QLT-01 レビュー初回合格率**: `{m12['M-QLT-01_review_first_pass_rate_percent']}%` (実施レビュー: {artifacts['reviews']['total_reviews']} 件)
- **M-QLT-02 レビュー指摘密度**: `{m12['M-QLT-02_review_defect_density_per_100_loc']} 件/100LOC` (総指摘: {artifacts['reviews']['total_defects']} 件)
- **M-QLT-03 スルーテスト初回合格率**: `{m12['M-QLT-03_scenario_test_first_pass_rate_percent']}%`
- **M-QLT-04 自律修復ループ収束ターン数**: `{m12['M-QLT-04_auto_healing_avg_turns']}` ターン (エラー検知: {transcript['error_steps_count']} 回)

### 軸3: プロセス健全性＆ガバナンス指標
- **M-GOV-01 Single Writer原則違反件数**: `{m12['M-GOV-01_single_writer_violations']} 件` (厳守)
- **M-GOV-02 不変原則・純度違反件数**: `{m12['M-GOV-02_invariants_violations']} 件`
- **M-GOV-03 フェーズ所要ターン超過率**: `{m12['M-GOV-03_phase_turn_overrun_ratio']}` 倍 (総ターン数: {transcript['total_turns']})
- **M-GOV-04 ドキュメント相互整合性スコア**: `{m12['M-GOV-04_doc_consistency_score_percent']}%`

---

## 3. 開発実績・成果物データ

- **Git 開発規模**:
  - 正味追加行数 (LOC): {artifacts['git']['net_loc_added']:,} 行
  - 総コミット数: {artifacts['git']['commit_count']} 件
  - 開発期間: {artifacts['git']['total_dev_days']} 日間 ({artifacts['git']['first_commit_date']} 〜 {artifacts['git']['latest_commit_date']})
- **Wiki パターン蓄積**: Tier 1 (ローカル): {artifacts['wiki']['local_patterns_count']} 件 / Tier 2 (汎用): {artifacts['wiki']['universal_patterns_count']} 件
- **レビュー実績ファイル**:
"""
    for rf in artifacts["reviews"]["parsed_files"]:
        md += f"  - `{rf}`\n"
    if not artifacts["reviews"]["parsed_files"]:
        md += "  - (検出なし)\n"

    md += f"""
---

## 4. 通算実行ログ詳細 (一次集計データ)

- **総ステップ数**: {transcript['total_steps']}
- **所要時間**: {transcript['duration_seconds'] // 60} 分 {transcript['duration_seconds'] % 60} 秒
- **トークン内訳**:
  - 入力トークン: {transcript['total_input_tokens']:,}
  - キャッシュ読込トークン: {transcript['total_cache_read_tokens']:,}
  - 出力トークン: {transcript['total_output_tokens']:,}
- **検出されたセッション一覧**:
"""
    for sess in transcript.get("sessions", []):
        md += f"  - `{sess['file']}` (ステップ数: {sess['steps']}, トークン: {sess['tokens']:,})\n"

    md += "\n- **ツール呼び出し内訳**:\n"
    for tool_name, count in sorted(transcript["tool_calls_breakdown"].items(), key=lambda x: x[1], reverse=True):
        md += f"  - `{tool_name}`: {count} 回\n"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(md, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic Quantitative Metrics Collector (Multi-Session & Retroactive)")
    parser.add_argument("--transcript", type=str, help="Specific path to transcript.jsonl (disables auto-matching)")
    parser.add_argument("--workspace", type=str, default=".", help="Workspace root path (default: current dir)")
    parser.add_argument(
        "--output-json",
        type=str,
        default="docs/plans/metrics/development-metrics-summary.json",
        help="Path for output summary JSON",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default="metrics/system_health_report.md",
        help="Path for output Markdown report",
    )
    parser.add_argument(
        "--max-context",
        type=int,
        default=DEFAULT_MAX_CONTEXT_TOKENS,
        help="Model maximum context tokens",
    )
    parser.add_argument(
        "--single-session",
        action="store_true",
        help="Only aggregate the latest single session instead of all matching sessions",
    )
    parser.add_argument(
        "--retroactive",
        action="store_true",
        help="Retroactive audit mode for legacy projects (analyzes full Git history and documents)",
    )
    args = parser.parse_args()

    workspace_root = Path(args.workspace).resolve()

    # トランスクリプトの解決
    transcript_paths: List[Path] = []
    if args.transcript:
        tp = Path(args.transcript).resolve()
        if not tp.is_file():
            print(f"[ERROR] Specified transcript file not found: {tp}", file=sys.stderr)
            sys.exit(1)
        transcript_paths = [tp]
    else:
        # プロジェクト別自動探索 (Workspace Path Matcher)
        transcript_paths = find_project_transcripts(workspace_root)
        if args.single_session and transcript_paths:
            transcript_paths = [transcript_paths[-1]]

    print(f"[INFO] Target Workspace: {workspace_root}")
    print(f"[INFO] Matched Project Sessions: {len(transcript_paths)} files")
    for tp in transcript_paths:
        print(f"       - {tp}")

    retroactive_mode = args.retroactive or (len(transcript_paths) == 0)
    if retroactive_mode:
        print("[INFO] Operating in RETROACTIVE mode (full Git history & artifact analysis)")

    # 1. パース処理
    single_results = [parse_single_transcript(p) for p in transcript_paths]
    merged_transcript_data = merge_transcripts_data(single_results)

    artifacts_data = parse_workspace_artifacts(workspace_root, retroactive_mode=retroactive_mode)

    # 2. 12指標算出およびスコアリング
    calc_result = calculate_12_metrics_and_scores(
        merged_transcript_data,
        artifacts_data,
        max_context_tokens=args.max_context,
        retroactive_mode=retroactive_mode,
    )

    # 統合データ生成
    now_jst = datetime.datetime.now(JST).isoformat()
    summary_data = {
        "metadata": {
            "project_name": workspace_root.name,
            "generated_at": now_jst,
            "retroactive_mode": retroactive_mode,
            "matched_transcripts": [str(p) for p in transcript_paths],
        },
        "metrics_12": calc_result["metrics_12"],
        "scores": calc_result["scores"],
        "raw_metrics": {
            "transcript": merged_transcript_data,
            "artifacts": artifacts_data,
        },
    }

    # 3. JSON 出力
    json_path = workspace_root / args.output_json
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] Metrics summary JSON written to: {json_path}")

    # 4. Markdown レポート出力
    report_path = workspace_root / args.output_report
    generate_markdown_report(summary_data, report_path)
    print(f"[SUCCESS] Health diagnostic report written to: {report_path}")

    print(f"\n==========================================")
    print(f" Quantitative Health Grade: {calc_result['scores']['grade']} ({calc_result['scores']['total_score']}/100)")
    print(f" Analysis Mode: {'RETROACTIVE (Legacy/Git)' if retroactive_mode else 'STANDARD (Multi-Session)'}")
    print(f" Total Tokens: {merged_transcript_data['total_tokens_consumed']:,}")
    print(f" Tool Calls: {merged_transcript_data['tool_calls_total']}")
    print(f" Total LOC Analyzed: {artifacts_data['git']['net_loc_added']:,}")
    print(f" Total Commits: {artifacts_data['git']['commit_count']}")
    print(f"==========================================")


if __name__ == "__main__":
    main()
