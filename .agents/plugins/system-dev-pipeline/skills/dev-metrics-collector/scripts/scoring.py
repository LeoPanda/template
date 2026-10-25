#!/usr/bin/env python3
"""
dev-metrics-collector スコアリング層モジュール (scoring.py)
Profile E: Zero-Dependency Python 3
12定量指標の算出、動的予算モデル、自律修復ターン実測値反映、グレード判定
"""

from typing import Dict, List
from metrics_types import ArtifactMetrics, CategoryScore, MergedTranscriptData, MetricItem, ScoringResult

DEFAULT_MAX_CONTEXT_TOKENS = 1_048_576


def calculate_12_metrics(
    transcript_data: MergedTranscriptData,
    artifacts_data: ArtifactMetrics,
    max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
    retroactive_mode: bool = False,
) -> ScoringResult:
    """12指標の算出および4大カテゴリの健全性スコアリングを行う"""
    has_transcript = transcript_data.session_count > 0

    if has_transcript:
        context_usage_percent = round((transcript_data.last_context_tokens / max_context_tokens) * 100, 2)
        total_turns = max(transcript_data.total_turns, 1)
        delegation_ratio_percent = round((transcript_data.subagent_delegation_count / total_turns) * 100, 2)
        k_tokens = max(transcript_data.total_tokens_consumed / 1000.0, 0.001)
        net_loc = artifacts_data.git_net_loc_added
        tokens_per_artifact = round(net_loc / k_tokens, 2)
        total_tools = max(transcript_data.tool_calls_total, 1)
        tool_duplicate_percent = round((transcript_data.duplicated_tool_calls / total_tools) * 100, 2)
        
        # M-QLT-04: パース層で追跡された実測平均修復ターン数（課題3解消）
        auto_healing_avg_turns = transcript_data.avg_healing_turns

        # M-GOV-03: セッション数連動の動的予算モデル（課題3解消）
        dynamic_budget = max(transcript_data.session_count * 25, 20)
        turn_overrun_ratio = round(max(total_turns / float(dynamic_budget), 1.0), 2)
    else:
        context_usage_percent = 0.0
        delegation_ratio_percent = 50.0
        tokens_per_artifact = 1.5
        tool_duplicate_percent = 0.0
        auto_healing_avg_turns = 1.0
        turn_overrun_ratio = 1.0

    critical_high_defects = (
        artifacts_data.defects_by_severity.get("Critical", 0) +
        artifacts_data.defects_by_severity.get("High", 0)
    )

    metrics_list: List[MetricItem] = [
        # 1. リソース効率指標 (25点)
        MetricItem(
            code="M-RES-01", name="最大コンテキスト消費率", category="リソース効率",
            value=context_usage_percent, unit="%", weight=8.0,
            raw_score=max(0.0, min(100.0, 100.0 - max(0.0, context_usage_percent - 50.0) * 2.0)),
            weighted_score=0.0, description="1Mウィンドウに対する最大消費率 (50%以下で満点)",
        ),
        MetricItem(
            code="M-RES-02", name="サブエージェント委譲率", category="リソース効率",
            value=delegation_ratio_percent, unit="%", weight=9.0,
            raw_score=max(0.0, min(100.0, delegation_ratio_percent * 2.0)) if delegation_ratio_percent <= 50.0 else max(0.0, min(100.0, 100.0 - (delegation_ratio_percent - 50.0) * 1.5)),
            weighted_score=0.0, description="全ターンに対するサブエージェント委譲率 (40-60%推奨)",
        ),
        MetricItem(
            code="M-RES-03", name="成果物トークン効率", category="リソース効率",
            value=tokens_per_artifact, unit="LOC/kTok", weight=8.0,
            raw_score=max(0.0, min(100.0, tokens_per_artifact * 50.0)),
            weighted_score=0.0, description="1kトークンあたりの追加コード行数 (2.0以上で満点)",
        ),

        # 2. 成果物品質指標 (35点)
        MetricItem(
            code="M-QLT-01", name="初回レビュー合格率", category="品質・堅牢性",
            value=artifacts_data.reviews_first_pass_rate, unit="%", weight=12.0,
            raw_score=artifacts_data.reviews_first_pass_rate, weighted_score=0.0,
            description="3大レビューゲートの初回合格率 (100%満点)",
        ),
        MetricItem(
            code="M-QLT-02", name="重大欠陥発生数", category="品質・堅牢性",
            value=critical_high_defects, unit="件", weight=10.0,
            raw_score=max(0.0, 100.0 - critical_high_defects * 25.0), weighted_score=0.0,
            description="レビューで指摘された Critical / High 件数 (0件満点)",
        ),
        MetricItem(
            code="M-QLT-03", name="重複ツール呼出率", category="品質・堅牢性",
            value=tool_duplicate_percent, unit="%", weight=6.0,
            raw_score=max(0.0, 100.0 - tool_duplicate_percent * 10.0), weighted_score=0.0,
            description="同一引数での連続ツール呼出率 (0%満点)",
        ),
        MetricItem(
            code="M-QLT-04", name="自律修復収束ターン数", category="品質・堅牢性",
            value=auto_healing_avg_turns, unit="ターン", weight=7.0,
            raw_score=max(0.0, min(100.0, 100.0 - max(0.0, auto_healing_avg_turns - 1.0) * 20.0)),
            weighted_score=0.0, description="エラー発生から修復完了までの平均ステップ数 (1-2ターン満点)",
        ),

        # 3. ナレッジ・進化指標 (15点)
        MetricItem(
            code="M-EVO-01", name="プロジェクト固有知見数", category="ナレッジ進化",
            value=artifacts_data.wiki_local_patterns, unit="件", weight=8.0,
            raw_score=min(100.0, artifacts_data.wiki_local_patterns * 25.0), weighted_score=0.0,
            description="wiki/patterns/local に記録された知見数 (4件以上で満点)",
        ),
        MetricItem(
            code="M-EVO-02", name="全体共通知見昇格数", category="ナレッジ進化",
            value=artifacts_data.wiki_universal_patterns, unit="件", weight=7.0,
            raw_score=min(100.0, artifacts_data.wiki_universal_patterns * 35.0), weighted_score=0.0,
            description="wiki/patterns/universal に昇格された汎用知見数 (3件以上で満点)",
        ),

        # 4. プロセス遵守指標 (25点)
        MetricItem(
            code="M-GOV-01", name="Single Writer 違反数", category="ガバナンス",
            value=artifacts_data.single_writer_violations, unit="件", weight=10.0,
            raw_score=max(0.0, 100.0 - artifacts_data.single_writer_violations * 50.0), weighted_score=0.0,
            description="PROJECT_STATE.md の不正更新件数 (0件満点)",
        ),
        MetricItem(
            code="M-GOV-02", name="不変則・規約逸脱件数", category="ガバナンス",
            value=artifacts_data.invariants_violations, unit="件", weight=8.0,
            raw_score=max(0.0, 100.0 - artifacts_data.invariants_violations * 50.0), weighted_score=0.0,
            description="生SQLや直書きモック等の規約逸脱件数 (0件満点)",
        ),
        MetricItem(
            code="M-GOV-03", name="動的ターン予算超過率", category="ガバナンス",
            value=turn_overrun_ratio, unit="倍", weight=7.0,
            raw_score=max(0.0, min(100.0, 100.0 - max(0.0, turn_overrun_ratio - 1.0) * 30.0)),
            weighted_score=0.0, description="動的ターン予算に対する所要ターン比率 (1.0倍以下満点)",
        ),
    ]

    # 加重スコア計算
    categories_map: Dict[str, CategoryScore] = {
        "リソース効率": CategoryScore(name="リソース効率", weight=25.0, score=0.0, weighted_score=0.0),
        "品質・堅牢性": CategoryScore(name="品質・堅牢性", weight=35.0, score=0.0, weighted_score=0.0),
        "ナレッジ進化": CategoryScore(name="ナレッジ進化", weight=15.0, score=0.0, weighted_score=0.0),
        "ガバナンス": CategoryScore(name="ガバナンス", weight=25.0, score=0.0, weighted_score=0.0),
    }

    total_score = 0.0
    for m in metrics_list:
        m.weighted_score = round((m.raw_score * m.weight) / 100.0, 2)
        total_score += m.weighted_score
        c = categories_map.get(m.category)
        if c:
            c.metrics.append(m)
            c.weighted_score += m.weighted_score

    for c in categories_map.values():
        c.score = round((c.weighted_score / c.weight) * 100.0, 1) if c.weight > 0 else 0.0
        c.weighted_score = round(c.weighted_score, 2)

    total_score = round(total_score, 1)

    # グレード判定
    if total_score >= 90.0:
        grade = "S (極めて優良 / Production Ready)"
    elif total_score >= 80.0:
        grade = "A (良好 / High Quality)"
    elif total_score >= 70.0:
        grade = "B (標準 / Acceptable)"
    elif total_score >= 60.0:
        grade = "C (改善推奨 / Needs Improvement)"
    else:
        grade = "D (規約不適合 / Warning)"

    return ScoringResult(
        total_score=total_score,
        grade=grade,
        categories=categories_map,
        metrics_list=metrics_list,
    )
