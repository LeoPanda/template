#!/usr/bin/env python3
"""
dev-metrics-collector レポート生成層モジュール (reporters.py)
Profile E: Zero-Dependency Python 3
Markdown 総合健全性診断レポート、フェーズ推移レポート、メトリクスJSON出力
"""

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List

from metrics_types import ArtifactMetrics, MergedTranscriptData, ScoringResult

JST = datetime.timezone(datetime.timedelta(hours=9))


def generate_markdown_report(
    workspace_root: Path,
    transcript_data: MergedTranscriptData,
    artifacts_data: ArtifactMetrics,
    scoring: ScoringResult,
    retroactive_mode: bool = False,
) -> str:
    """総合健全性診断レポート (Markdown) を生成する"""
    now_jst = datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    project_name = workspace_root.name

    lines: List[str] = [
        f"# プロジェクト総合健全性診断レポート ({project_name})",
        "",
        f"- **測定日時**: {now_jst}",
        f"- **対象ワークスペース**: `{workspace_root.resolve()}`",
        f"- **測定モード**: {'遡及集計モード (--retroactive)' if retroactive_mode else '標準集計モード (トランスクリプト + 成果物)'}",
        f"- **解析セッション数**: {transcript_data.session_count} 回",
        f"- **総合健全性スコア**: **{scoring.total_score} / 100 点**",
        f"- **総合品質グレード**: **{scoring.grade}**",
        "",
        "---",
        "",
        "## 1. カテゴリ別評価サマリ",
        "",
        "| カテゴリ | 配点比重 | 獲得スコア | 100点換算 | 評価状況 |",
        "| :--- | :---: | :---: | :---: | :--- |",
    ]

    for cat_name, cat in scoring.categories.items():
        status = "🟢 良好" if cat.score >= 80.0 else ("🟡 標準" if cat.score >= 60.0 else "🔴 要改善")
        lines.append(f"| **{cat_name}** | {cat.weight}% | {cat.weighted_score} 点 | {cat.score} 点 | {status} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. 12指標詳細測定結果",
        "",
        "| コード | 指標名 | カテゴリ | 実測値 | 配点 | 獲得点 | 評価基準概要 |",
        "| :---: | :--- | :--- | :---: | :---: | :---: | :--- |",
    ])

    for m in scoring.metrics_list:
        lines.append(
            f"| `{m.code}` | {m.name} | {m.category} | **{m.value} {m.unit}** | {m.weight}点 | {m.weighted_score}点 | {m.description} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. 開発リソース & セッション情報",
        "",
        f"- **通算会話ターン数**: {transcript_data.total_turns} ターン (ユーザー: {transcript_data.user_turns} / モデル: {transcript_data.model_turns})",
        f"- **総所要時間**: {round(transcript_data.duration_seconds / 60.0, 1)} 分 ({transcript_data.duration_seconds} 秒)",
        f"- **総消費トークン**: {transcript_data.total_tokens_consumed:,} tokens (入力: {transcript_data.total_input_tokens:,} / 出力: {transcript_data.total_output_tokens:,})",
        f"- **キャッシュ読取トークン**: {transcript_data.total_cache_read_tokens:,} tokens",
        f"- **ツール呼出総数**: {transcript_data.tool_calls_total} 回 (サブエージェント委譲: {transcript_data.subagent_delegation_count} 回)",
        f"- **正味開発規模 (LOC)**: {artifacts_data.git_net_loc_added:,} 行 (Git 全履歴通算挿入行数)",
        f"- **総コミット数**: {artifacts_data.git_commit_count} コミット",
        f"- **レビュー完了数**: {artifacts_data.reviews_total} 件 (初回合格: {artifacts_data.reviews_passed} 件 / 初回合格率: {artifacts_data.reviews_first_pass_rate}%)",
        f"- **蓄積ナレッジ数**: 合計 {artifacts_data.wiki_total_patterns} 件 (ローカル: {artifacts_data.wiki_local_patterns} 件 / 汎用昇格: {artifacts_data.wiki_universal_patterns} 件)",
        "",
        "### セッション別内訳",
        "",
        "| No | トランスクリプトパス | ステップ数 | 消費トークン | 所要時間 |",
        "| :---: | :--- | :---: | :---: | :---: |",
    ])

    for idx, s in enumerate(transcript_data.sessions, 1):
        rel_p = s["file"]
        if "/.gemini/" in rel_p:
            rel_p = "~" + rel_p[rel_p.index("/.gemini/"):]
        lines.append(
            f"| {idx} | `{rel_p}` | {s['steps']} | {s['tokens']:,} | {round(s['duration_sec'] / 60.0, 1)}分 |"
        )

    lines.append("")
    return "\n".join(lines)


def generate_development_phase_report(
    workspace_root: Path,
    transcript_data: MergedTranscriptData,
) -> str:
    """開発フェーズ・改訂ターン別推移レポート (Markdown) を生成する (PAT-SYS-004)"""
    now_jst = datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    project_name = workspace_root.name

    lines: List[str] = [
        f"# 開発フェーズ別推移レポート ({project_name})",
        "",
        f"- **集計日時**: {now_jst}",
        f"- **対象セッション総数**: {len(transcript_data.raw_summaries)} 回",
        "",
        "---",
        "",
        "## 1. セッション別実行サマリ",
        "",
        "| No | 開始日時 (JST) | 所要時間 | ターン数 (User/Model) | エラー数 | 実測修復ターン | 主なリクエスト概要 |",
        "| :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]

    for idx, s in enumerate(transcript_data.raw_summaries, 1):
        st_str = s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "不明"
        dur_min = f"{round(s.duration_seconds / 60.0, 1)}分"
        turns_str = f"{s.total_turns} ({s.user_turns}/{s.model_turns})"
        err_str = f"{s.error_steps_count}件"
        
        # 実測修復ターン数
        heal_str = f"{round(sum(s.healing_turns_samples) / len(s.healing_turns_samples), 1)}ターン" if s.healing_turns_samples else "-"

        # Markdownテーブル内パイプ文字エスケープ (PAT-SYS-004)
        req_summary = s.first_user_request.replace("|", "\\|").replace("\n", " ").strip()[:60]
        if not req_summary:
            req_summary = "(自動実行または継続ターン)"

        lines.append(
            f"| {idx} | {st_str} | {dur_min} | {turns_str} | {err_str} | {heal_str} | {req_summary} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 2. ツール呼出頻度サマリ",
        "",
        "| ツール名 | 呼出回数 | 構成比 |",
        "| :--- | :---: | :---: |",
    ])

    total_tools = max(transcript_data.tool_calls_total, 1)
    for t_name, cnt in sorted(transcript_data.tool_calls_breakdown.items(), key=lambda x: x[1], reverse=True):
        ratio = round((cnt / total_tools) * 100, 1)
        lines.append(f"| `{t_name}` | {cnt} 回 | {ratio}% |")

    lines.append("")
    return "\n".join(lines)


def save_metrics_json(
    output_path: Path,
    workspace_root: Path,
    transcript_data: MergedTranscriptData,
    artifacts_data: ArtifactMetrics,
    scoring: ScoringResult,
    retroactive_mode: bool = False,
) -> None:
    """メトリクス集計JSONを保存する (PAT-SYS-003)"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.datetime.now(JST).isoformat(timespec="seconds")

    cat_alias_map = {
        "リソース効率": "resource",
        "品質・堅牢性": "quality",
        "ナレッジ進化": "evolution",
        "ガバナンス": "governance",
    }
    category_scores_dict: Dict[str, Any] = {}
    for name, c in scoring.categories.items():
        category_scores_dict[name] = {"score": c.score, "weighted_score": c.weighted_score, "weight": c.weight}
        if name in cat_alias_map:
            category_scores_dict[cat_alias_map[name]] = c.weighted_score

    data = {
        "project_name": workspace_root.name,
        "collected_at": now_iso,
        "mode": "retroactive" if retroactive_mode else "standard",
        "summary": {
            "total_score": scoring.total_score,
            "grade": scoring.grade,
            "category_scores": category_scores_dict,
            "total_tokens": transcript_data.total_tokens_consumed,
            "total_tool_calls": transcript_data.tool_calls_total,
            "net_loc": artifacts_data.git_net_loc_added,
        },
        "metrics_12": [
            {
                "code": m.code,
                "name": m.name,
                "category": m.category,
                "value": m.value,
                "unit": m.unit,
                "weight": m.weight,
                "raw_score": m.raw_score,
                "weighted_score": m.weighted_score,
                "description": m.description,
            }
            for m in scoring.metrics_list
        ],
        "resources": {
            "session_count": transcript_data.session_count,
            "total_turns": transcript_data.total_turns,
            "user_turns": transcript_data.user_turns,
            "model_turns": transcript_data.model_turns,
            "duration_seconds": transcript_data.duration_seconds,
            "total_tokens_consumed": transcript_data.total_tokens_consumed,
            "total_input_tokens": transcript_data.total_input_tokens,
            "total_output_tokens": transcript_data.total_output_tokens,
            "total_cache_read_tokens": transcript_data.total_cache_read_tokens,
            "last_context_tokens": transcript_data.last_context_tokens,
            "tool_calls_total": transcript_data.tool_calls_total,
            "tool_calls_breakdown": transcript_data.tool_calls_breakdown,
            "duplicated_tool_calls": transcript_data.duplicated_tool_calls,
            "subagent_delegation_count": transcript_data.subagent_delegation_count,
            "error_steps_count": transcript_data.error_steps_count,
            "avg_healing_turns": transcript_data.avg_healing_turns,
        },
        "artifacts": {
            "git_net_loc_added": artifacts_data.git_net_loc_added,
            "git_commit_count": artifacts_data.git_commit_count,
            "git_total_dev_days": artifacts_data.git_total_dev_days,
            "reviews_total": artifacts_data.reviews_total,
            "reviews_passed": artifacts_data.reviews_passed,
            "reviews_first_pass_rate": artifacts_data.reviews_first_pass_rate,
            "defects_total": artifacts_data.defects_total,
            "defects_by_severity": artifacts_data.defects_by_severity,
            "wiki_local_patterns": artifacts_data.wiki_local_patterns,
            "wiki_universal_patterns": artifacts_data.wiki_universal_patterns,
            "wiki_total_patterns": artifacts_data.wiki_total_patterns,
        },
    }

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
