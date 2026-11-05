#!/usr/bin/env python3
"""
dev-metrics-collector パース層モジュール (parsers.py)
Profile E: Zero-Dependency Python 3
トランスクリプト探索・パース、Git・成果物解析、セッション時系列ソート
"""

import datetime
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from metrics_types import ArtifactMetrics, MergedTranscriptData, SingleTranscriptSummary

JST = datetime.timezone(datetime.timedelta(hours=9))


def _extract_start_time(transcript_path: Path) -> datetime.datetime:
    """トランスクリプト先頭から最初のステップ日時を抽出する"""
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    ca = data.get("created_at")
                    if ca:
                        dt = datetime.datetime.fromisoformat(ca)
                        return dt if dt.tzinfo else dt.replace(tzinfo=JST)
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        pass
    # フォールバック: mtime
    return datetime.datetime.fromtimestamp(os.path.getmtime(transcript_path), tz=JST)


def find_project_transcripts(workspace_root: Path, debug: bool = False) -> List[Path]:
    """
    ワークスペースのパスを含む会話トランスクリプトを探索・抽出する。
    mtime走査後、ログ内部の start_time 基準で昇順ソートする二段構え（課題2解消）。
    """
    workspace_str = str(workspace_root.resolve())
    matched_candidates: List[Path] = []

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
            with open(cand_path, "r", encoding="utf-8", errors="ignore") as f:
                header_chunk = f.read(65536)
                if workspace_str in header_chunk:
                    matched_candidates.append(cand_path)
                    continue

                f.seek(0)
                full_chunk = f.read(524288)
                if workspace_str in full_chunk:
                    matched_candidates.append(cand_path)
        except OSError as e:
            if debug:
                print(f"[debug] Transcript read error: {cand_path}: {e}", file=sys.stderr)
            continue

    # 3. ワークスペース直下の .system_generated/logs/transcript.jsonl もチェック
    local_log = workspace_root / ".system_generated" / "logs" / "transcript.jsonl"
    if local_log.is_file() and local_log not in matched_candidates:
        matched_candidates.append(local_log)

    # start_time（ISO 8601日時）基準で二段ソート（古いセッション ➔ 新しいセッション）
    dated_transcripts: List[Tuple[datetime.datetime, Path]] = [
        (_extract_start_time(p), p) for p in matched_candidates
    ]
    dated_transcripts.sort(key=lambda x: x[0])
    return [p for _, p in dated_transcripts]


def parse_single_transcript(transcript_path: Path, debug: bool = False) -> SingleTranscriptSummary:
    """単一 transcript.jsonl をパースして一次集計を行う（自律修復ターン実測追跡を含む）"""
    total_input_tokens = 0
    total_cache_read_tokens = 0
    total_output_tokens = 0

    tool_calls_count: Dict[str, int] = {}
    tool_calls_total = 0
    subagent_delegation_count = 0
    error_steps_count = 0
    user_turns = 0
    model_turns = 0
    user_prompts: List[str] = []

    timestamps: List[datetime.datetime] = []
    last_context_tokens = 0
    previous_tool_signature: Optional[str] = None
    duplicated_tool_calls = 0

    healing_turns_samples: List[int] = []
    current_error_start_idx: Optional[int] = None
    step_idx = 0

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    step = json.loads(line)
                except json.JSONDecodeError:
                    continue

                step_idx += 1
                source = step.get("source")
                step_type = step.get("type")
                status = step.get("status")

                created_at_str = step.get("created_at")
                if created_at_str:
                    try:
                        dt = datetime.datetime.fromisoformat(created_at_str)
                        timestamps.append(dt if dt.tzinfo else dt.replace(tzinfo=JST))
                    except ValueError:
                        pass

                if source == "USER_EXPLICIT" or step_type == "USER_INPUT":
                    user_turns += 1
                    content = step.get("content", "")
                    if content:
                        clean_text = re.sub(r"<[^>]+>", "", content).strip()
                        if clean_text:
                            user_prompts.append(clean_text)

                elif source in ("MODEL", "PLANNER") or step_type == "PLANNER_RESPONSE":
                    model_turns += 1

                # 自律修復ターンの実測追跡
                if status == "ERROR":
                    error_steps_count += 1
                    if current_error_start_idx is None:
                        current_error_start_idx = step_idx
                elif status == "DONE" and current_error_start_idx is not None:
                    healing_turns_samples.append(step_idx - current_error_start_idx)
                    current_error_start_idx = None

                tool_calls = step.get("tool_calls", [])
                if isinstance(tool_calls, list):
                    for tc in tool_calls:
                        if isinstance(tc, dict):
                            fn_name = tc.get("name") or tc.get("tool_name") or "unknown_tool"
                            tool_calls_total += 1
                            tool_calls_count[fn_name] = tool_calls_count.get(fn_name, 0) + 1
                            if fn_name == "invoke_subagent":
                                subagent_delegation_count += 1

                            args_str = json.dumps(tc.get("args", {}), sort_keys=True)
                            sig = f"{fn_name}:{args_str}"
                            if sig == previous_tool_signature:
                                duplicated_tool_calls += 1
                            previous_tool_signature = sig

                usage = step.get("usage") or step.get("token_usage") or {}
                if not isinstance(usage, dict):
                    usage = {}

                # 1. step 直下のキー（Antigravity 標準ログ仕様）を最優先で探索
                # 2. usage / token_usage 辞書（旧形式・外部SDK互換）を二重フォールバックで探索
                inp = step.get("input_tokens") or usage.get("input_tokens") or usage.get("prompt_tokens") or 0
                cache_read = (
                    step.get("cache_read_tokens")
                    or step.get("cache_read_input_tokens")
                    or usage.get("cache_read_input_tokens")
                    or usage.get("cached_content_token_count")
                    or 0
                )
                out = step.get("output_tokens") or usage.get("output_tokens") or usage.get("candidates_token_count") or 0

                total_input_tokens += inp
                total_cache_read_tokens += cache_read
                total_output_tokens += out
                if (inp + cache_read) > 0:
                    last_context_tokens = inp + cache_read

    except OSError as e:
        if debug:
            print(f"[debug] File access error on {transcript_path}: {e}", file=sys.stderr)

    start_time = timestamps[0] if timestamps else None
    end_time = timestamps[-1] if timestamps else None
    duration_seconds = max(int((end_time - start_time).total_seconds()), 0) if (start_time and end_time) else 0

    return SingleTranscriptSummary(
        file_path=str(transcript_path),
        total_steps=step_idx,
        user_turns=user_turns,
        model_turns=model_turns,
        total_turns=user_turns + model_turns,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration_seconds,
        total_input_tokens=total_input_tokens,
        total_cache_read_tokens=total_cache_read_tokens,
        total_output_tokens=total_output_tokens,
        total_tokens_consumed=total_input_tokens + total_output_tokens,
        last_context_tokens=last_context_tokens,
        tool_calls_total=tool_calls_total,
        tool_calls_breakdown=tool_calls_count,
        duplicated_tool_calls=duplicated_tool_calls,
        subagent_delegation_count=subagent_delegation_count,
        error_steps_count=error_steps_count,
        healing_turns_samples=healing_turns_samples,
        user_requests=user_prompts,
        first_user_request=user_prompts[0] if user_prompts else "",
    )


def merge_transcripts_data(transcript_list: List[SingleTranscriptSummary]) -> MergedTranscriptData:
    """同一プロジェクトの複数セッション通算データを合算・統合する"""
    if not transcript_list:
        return MergedTranscriptData(
            session_count=0, total_steps=0, user_turns=0, model_turns=0, total_turns=0,
            duration_seconds=0, total_input_tokens=0, total_cache_read_tokens=0,
            total_output_tokens=0, total_tokens_consumed=0, last_context_tokens=0,
            tool_calls_total=0, tool_calls_breakdown={}, duplicated_tool_calls=0,
            subagent_delegation_count=0, error_steps_count=0, avg_healing_turns=1.0,
            sessions=[], raw_summaries=[],
        )

    all_healing_samples: List[int] = []
    for t in transcript_list:
        all_healing_samples.extend(t.healing_turns_samples)

    if all_healing_samples:
        avg_healing = round(sum(all_healing_samples) / len(all_healing_samples), 1)
    else:
        # 実測値が未検出の場合はセッション正規化フォールバック
        session_cnt = max(len(transcript_list), 1)
        err_total = sum(t.error_steps_count for t in transcript_list)
        avg_healing = round(max((err_total / session_cnt) * 0.5, 1.0), 1)

    merged_tools: Dict[str, int] = {}
    for t in transcript_list:
        for tool_name, cnt in t.tool_calls_breakdown.items():
            merged_tools[tool_name] = merged_tools.get(tool_name, 0) + cnt

    return MergedTranscriptData(
        session_count=len(transcript_list),
        total_steps=sum(t.total_steps for t in transcript_list),
        user_turns=sum(t.user_turns for t in transcript_list),
        model_turns=sum(t.model_turns for t in transcript_list),
        total_turns=sum(t.total_turns for t in transcript_list),
        duration_seconds=sum(t.duration_seconds for t in transcript_list),
        total_input_tokens=sum(t.total_input_tokens for t in transcript_list),
        total_cache_read_tokens=sum(t.total_cache_read_tokens for t in transcript_list),
        total_output_tokens=sum(t.total_output_tokens for t in transcript_list),
        total_tokens_consumed=sum(t.total_tokens_consumed for t in transcript_list),
        last_context_tokens=transcript_list[-1].last_context_tokens,
        tool_calls_total=sum(t.tool_calls_total for t in transcript_list),
        tool_calls_breakdown=merged_tools,
        duplicated_tool_calls=sum(t.duplicated_tool_calls for t in transcript_list),
        subagent_delegation_count=sum(t.subagent_delegation_count for t in transcript_list),
        error_steps_count=sum(t.error_steps_count for t in transcript_list),
        avg_healing_turns=avg_healing,
        sessions=[
            {
                "file": t.file_path,
                "steps": t.total_steps,
                "tokens": t.total_tokens_consumed,
                "duration_sec": t.duration_seconds,
            }
            for t in transcript_list
        ],
        raw_summaries=transcript_list,
    )


def parse_workspace_artifacts(workspace_root: Path, retroactive_mode: bool = False, debug: bool = False) -> ArtifactMetrics:
    """ワークスペースのドキュメント、Wiki、Gitログからメトリクスを抽出する"""
    metrics = ArtifactMetrics()

    # 1. Wiki パターン数
    local_wiki = workspace_root / "wiki" / "patterns" / "local"
    univ_wiki = workspace_root / "wiki" / "patterns" / "universal"
    if local_wiki.is_dir():
        metrics.wiki_local_patterns = len(list(local_wiki.glob("*.md")))
    if univ_wiki.is_dir():
        metrics.wiki_universal_patterns = len(list(univ_wiki.glob("*.md")))
    metrics.wiki_total_patterns = metrics.wiki_local_patterns + metrics.wiki_universal_patterns

    # 2. レビュー報告書の解析
    docs_dir = workspace_root / "docs"
    if docs_dir.is_dir():
        review_files = list(docs_dir.glob("**/*レビュー*報告書*.md")) + list(docs_dir.glob("**/*リファクタリング提案書*.md"))
        for rf in review_files:
            if "template" in rf.name.lower() or "テンプレート" in rf.name:
                continue
            metrics.reviews_total += 1
            metrics.parsed_review_files.append(str(rf.relative_to(workspace_root)))
            try:
                text = rf.read_text(encoding="utf-8")
                # 判定抽出 (PAT-SYS-005: 太字・表記揺れ・括弧を包括)
                if re.search(
                    r"(?:総合(?:合否)?判定|判定結果|合否判定)[:：\s*]*[【\[(]?(?:`|\*\*|\s)*(?:PASS|RELEASE\s+APPROVED|CLEAN)(?:`|\*\*|\s)*[】\])]?",
                    text,
                    re.IGNORECASE,
                ) or "CONDITIONAL PASS" in text:
                    metrics.reviews_passed += 1

                for sev in ("Critical", "High", "Medium", "Low"):
                    matches = re.findall(rf"(?:{sev}|{sev.upper()})[:：\s]*(\d+)", text)
                    if matches:
                        cnt = sum(int(m) for m in matches)
                        metrics.defects_by_severity[sev] += cnt
                        metrics.defects_total += cnt
            except OSError as e:
                if debug:
                    print(f"[debug] Review parse error on {rf}: {e}", file=sys.stderr)

        if metrics.reviews_total > 0:
            metrics.reviews_first_pass_rate = round(
                (metrics.reviews_passed / metrics.reviews_total) * 100, 1
            )

    # 2.5 project_state.json レビュー結果直接補完 (V2.6)
    state_json = workspace_root / "project_state.json"
    if state_json.is_file():
        try:
            sdata = json.loads(state_json.read_text(encoding="utf-8"))
            for rk, rv in sdata.get("review_gates", {}).items():
                if isinstance(rv, dict) and rv.get("verdict") and rv["verdict"] != "PENDING":
                    if rv["verdict"] in ("PASS", "RELEASE APPROVED", "CLEAN", "CONDITIONAL PASS"):
                        metrics.reviews_passed = max(metrics.reviews_passed, 1)
                    for sev in ("Critical", "High", "Medium", "Low"):
                        metrics.defects_by_severity[sev] += rv.get(sev.lower(), 0)
        except Exception:
            pass
    # 3. Git 履歴解析
    try:
        res_commits = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=str(workspace_root), capture_output=True, text=True, check=False,
        )
        if res_commits.returncode == 0 and res_commits.stdout.strip():
            metrics.git_commit_count = int(res_commits.stdout.strip())

        res_dates = subprocess.run(
            ["git", "log", "--format=%ad", "--date=iso-strict"],
            cwd=str(workspace_root), capture_output=True, text=True, check=False,
        )
        if res_dates.returncode == 0 and res_dates.stdout.strip():
            lines = res_dates.stdout.strip().splitlines()
            metrics.git_latest_commit_date = lines[0]
            metrics.git_first_commit_date = lines[-1]
            try:
                d_latest = datetime.datetime.fromisoformat(lines[0])
                d_first = datetime.datetime.fromisoformat(lines[-1])
                metrics.git_total_dev_days = max((d_latest - d_first).days, 1)
            except ValueError:
                pass

        # 空ツリーハッシュとの差分による全履歴通算LOC
        res_diff = subprocess.run(
            ["git", "diff", "--shortstat", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "HEAD"],
            cwd=str(workspace_root), capture_output=True, text=True, check=False,
        )
        if res_diff.returncode == 0 and res_diff.stdout.strip():
            m = re.search(r"(\d+)\s+insertion", res_diff.stdout)
            if m:
                metrics.git_net_loc_added = int(m.group(1))
        elif not retroactive_mode:
            res_short = subprocess.run(
                ["git", "diff", "--shortstat", "HEAD~1..HEAD"],
                cwd=str(workspace_root), capture_output=True, text=True, check=False,
            )
            if res_short.returncode == 0 and res_short.stdout.strip():
                m = re.search(r"(\d+)\s+insertion", res_short.stdout)
                if m:
                    metrics.git_net_loc_added = int(m.group(1))
    except (subprocess.SubprocessError, OSError) as e:
        if debug:
            print(f"[debug] Git command error: {e}", file=sys.stderr)

    if metrics.git_net_loc_added == 0:
        total_loc = 0
        for ext in ("*.py", "*.ts", "*.tsx", "*.md", "*.rs", "*.sql"):
            for p in workspace_root.glob(f"**/{ext}"):
                if any(x in str(p) for x in (".git", "node_modules", ".venv", "skeletons")):
                    continue
                try:
                    total_loc += len(p.read_text(encoding="utf-8").splitlines())
                except OSError:
                    pass
        metrics.git_net_loc_added = max(total_loc, 1)

    return metrics
