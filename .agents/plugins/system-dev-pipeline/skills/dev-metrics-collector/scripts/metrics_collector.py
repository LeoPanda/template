#!/usr/bin/env python3
"""
Quantitative Metrics Collector (dev-metrics-collector)
Profile E: Zero-Dependency Python 3 CLI エントリーポイント
"""

import argparse
import sys
from pathlib import Path

# 同一ディレクトリの分割モジュールをインポート可能にする
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from parsers import (
    find_project_transcripts,
    merge_transcripts_data,
    parse_single_transcript,
    parse_workspace_artifacts,
)
from reporters import (
    generate_development_phase_report,
    generate_markdown_report,
    save_metrics_json,
)
from scoring import calculate_12_metrics
from metrics_types import MergedTranscriptData, SingleTranscriptSummary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Antigravity 会話ログおよび成果物から定量健全性スコアを集計・診断する"
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=".",
        help="対象ワークスペースのルートパス (デフォルト: カレントディレクトリ)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="metrics",
        help="レポートおよびJSONの出力先ディレクトリ (デフォルト: metrics)",
    )
    parser.add_argument(
        "--retroactive",
        action="store_true",
        help="過去プロジェクト遡及分析モード (トランスクリプト欠損時でもGit・成果物から採点)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="総合診断レポート・フェーズ推移レポート・JSONの全成果物を一括出力する",
    )
    parser.add_argument(
        "--sync-state",
        action="store_true",
        help="state_manager.py sync-metrics を自動実行し project_state.json/MD へ即時同期する (V2.6)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="詳細デバッグログを標準エラー出力へ表示する",
    )
    args = parser.parse_args()

    workspace_root = Path(args.workspace).resolve()
    output_dir = workspace_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.debug:
        print(f"[debug] Target workspace: {workspace_root}", file=sys.stderr)

    # 1. 会話トランスクリプトの探索とパース
    raw_summaries: list[SingleTranscriptSummary] = []
    if not args.retroactive:
        matched_transcripts = find_project_transcripts(workspace_root, debug=args.debug)
        if args.debug:
            print(f"[debug] Found {len(matched_transcripts)} transcript files.", file=sys.stderr)

        for tp in matched_transcripts:
            summary = parse_single_transcript(tp, debug=args.debug)
            raw_summaries.append(summary)

    merged_transcript = merge_transcripts_data(raw_summaries)

    # 2. 成果物メトリクスの抽出
    artifacts_data = parse_workspace_artifacts(
        workspace_root, retroactive_mode=args.retroactive, debug=args.debug
    )

    # 3. 12指標のスコアリング計算
    scoring_result = calculate_12_metrics(
        merged_transcript, artifacts_data, retroactive_mode=args.retroactive
    )

    # 4. レポート成果物の生成と保存
    # (a) 総合診断レポート
    markdown_report = generate_markdown_report(
        workspace_root, merged_transcript, artifacts_data, scoring_result, retroactive_mode=args.retroactive
    )
    health_report_path = output_dir / "system_health_report.md"
    health_report_path.write_text(markdown_report, encoding="utf-8")

    # (b) フェーズ推移レポート (PAT-SYS-004)
    phase_report_path = output_dir / "development_phase_report.md"
    if args.all or len(raw_summaries) > 0:
        phase_report = generate_development_phase_report(workspace_root, merged_transcript)
        phase_report_path.write_text(phase_report, encoding="utf-8")

    # (c) 集計サマリ JSON (PAT-SYS-003: metrics/ 配下へ統一)
    json_path = output_dir / "development-metrics-summary.json"
    save_metrics_json(
        json_path, workspace_root, merged_transcript, artifacts_data, scoring_result, retroactive_mode=args.retroactive
    )

    # (d) state_manager.py との自動連携 (V2.6)
    if args.sync_state:
        state_mgr = workspace_root / "scripts" / "state_manager.py"
        if not state_mgr.exists():
            state_mgr = SCRIPT_DIR.parent.parent.parent / "scripts" / "state_manager.py"
        if state_mgr.exists():
            try:
                import subprocess
                subprocess.run([sys.executable, str(state_mgr), "sync-metrics", "--path", str(json_path)], cwd=str(workspace_root), check=False)
            except Exception as e:
                if args.debug:
                    print(f"[debug] sync-state error: {e}", file=sys.stderr)

    # 5. CLI 標準出力サマリ
    print("=" * 76)
    print(f"📊 [dev-metrics-collector] 定量健全性スコア測定結果 ({workspace_root.name})")
    print("=" * 76)
    print(f"  総合スコア : {scoring_result.total_score} / 100 点")
    print(f"  品質グレード: {scoring_result.grade}")
    print("-" * 76)
    for cat_name, cat in scoring_result.categories.items():
        print(f"  ・{cat_name:<10}: {cat.weighted_score:>5.2f} / {cat.weight:>4.1f} 点 ({cat.score:>5.1f}点換算)")
    print("-" * 76)
    print(f"  ・通算セッション数: {merged_transcript.session_count} 回")
    print(f"  ・通算トークン消費: {merged_transcript.total_tokens_consumed:,} tokens")
    print(f"  ・ツール呼出総数  : {merged_transcript.tool_calls_total} 回")
    print(f"  ・正味開発規模(LOC): {artifacts_data.git_net_loc_added:,} 行")
    print("=" * 76)
    print(f"✅ 総合診断レポート  : {health_report_path.relative_to(workspace_root)}")
    if phase_report_path.exists():
        print(f"✅ フェーズ推移レポート: {phase_report_path.relative_to(workspace_root)}")
    print(f"✅ 集計サマリJSON   : {json_path.relative_to(workspace_root)}")


if __name__ == "__main__":
    main()
