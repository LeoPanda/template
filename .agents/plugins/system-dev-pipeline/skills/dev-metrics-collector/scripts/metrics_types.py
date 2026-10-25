#!/usr/bin/env python3
"""
dev-metrics-collector 型スキーマ定義モジュール (types.py)
Profile E: Zero-Dependency Python 3 dataclasses スキーマ
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SingleTranscriptSummary:
    """単一 transcript.jsonl のパースサマリ"""
    file_path: str
    total_steps: int
    user_turns: int
    model_turns: int
    total_turns: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: int
    total_input_tokens: int
    total_cache_read_tokens: int
    total_output_tokens: int
    total_tokens_consumed: int
    last_context_tokens: int
    tool_calls_total: int
    tool_calls_breakdown: Dict[str, int] = field(default_factory=dict)
    duplicated_tool_calls: int = 0
    subagent_delegation_count: int = 0
    error_steps_count: int = 0
    healing_turns_samples: List[int] = field(default_factory=list)
    user_requests: List[str] = field(default_factory=list)
    first_user_request: str = ""


@dataclass
class MergedTranscriptData:
    """同一プロジェクト複数セッションの通算集計データ"""
    session_count: int
    total_steps: int
    user_turns: int
    model_turns: int
    total_turns: int
    duration_seconds: int
    total_input_tokens: int
    total_cache_read_tokens: int
    total_output_tokens: int
    total_tokens_consumed: int
    last_context_tokens: int
    tool_calls_total: int
    tool_calls_breakdown: Dict[str, int] = field(default_factory=dict)
    duplicated_tool_calls: int = 0
    subagent_delegation_count: int = 0
    error_steps_count: int = 0
    avg_healing_turns: float = 1.0
    sessions: List[Dict[str, Any]] = field(default_factory=list)
    raw_summaries: List[SingleTranscriptSummary] = field(default_factory=list)


@dataclass
class ArtifactMetrics:
    """Git・Wiki・レビュー報告書等から抽出された成果物メトリクス"""
    reviews_total: int = 0
    reviews_passed: int = 0
    reviews_first_pass_rate: float = 100.0
    defects_total: int = 0
    defects_by_severity: Dict[str, int] = field(default_factory=lambda: {"Critical": 0, "High": 0, "Medium": 0, "Low": 0})
    parsed_review_files: List[str] = field(default_factory=list)
    wiki_local_patterns: int = 0
    wiki_universal_patterns: int = 0
    wiki_total_patterns: int = 0
    git_net_loc_added: int = 0
    git_commit_count: int = 0
    git_first_commit_date: Optional[str] = None
    git_latest_commit_date: Optional[str] = None
    git_total_dev_days: int = 1
    single_writer_violations: int = 0
    invariants_violations: int = 0
    doc_consistency_score: float = 100.0


@dataclass
class MetricItem:
    """12の個別定量評価指標"""
    code: str
    name: str
    category: str
    value: Any
    unit: str
    weight: float
    raw_score: float
    weighted_score: float
    description: str


@dataclass
class CategoryScore:
    """カテゴリ別スコア"""
    name: str
    weight: float
    score: float
    weighted_score: float
    metrics: List[MetricItem] = field(default_factory=list)


@dataclass
class ScoringResult:
    """12指標総合スコアリング結果"""
    total_score: float
    grade: str
    categories: Dict[str, CategoryScore] = field(default_factory=dict)
    metrics_list: List[MetricItem] = field(default_factory=list)
