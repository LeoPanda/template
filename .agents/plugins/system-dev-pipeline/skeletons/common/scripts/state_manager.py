#!/usr/bin/env python3
"""
state_manager.py - Deterministic State Ledger Manager (Profile E)
Manages project_state.json and renders PROJECT_STATE.md atomically.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

STATE_JSON_PATH = Path("project_state.json")
STATE_MD_PATH = Path("PROJECT_STATE.md")
METRICS_JSON_PATH = Path("metrics/development-metrics-summary.json")

PHASE_ORDER = [
    "PHASE_1_SETUP", "PHASE_2_REQUIREMENTS", "PHASE_3_DESIGN",
    "PHASE_4_IMPLEMENTATION", "PHASE_5_WALKTHROUGH", "PHASE_5_5_CODE_REVIEW",
    "PHASE_6_TESTING", "PHASE_7_RELEASE", "PHASE_8_EVOLUTION", "PRODUCTION_ACTIVE"
]

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()

def compute_checksum(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"

def atomic_write(path: Path, content: str):
    tmp = path.with_name(f"{path.name}.tmp_{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)

def load_state() -> dict:
    if not STATE_JSON_PATH.exists():
        print(f"❌ {STATE_JSON_PATH} が存在しません。'init' または 'migrate' を実行してください。", file=sys.stderr)
        sys.exit(1)
    return json.loads(STATE_JSON_PATH.read_text(encoding="utf-8"))

def save_and_render(state: dict, author: str = "conductor"):
    state["project_metadata"]["updated_at"] = now_iso()
    state["project_metadata"]["updated_by"] = author
    rendered_md = render_markdown(state)
    state["project_metadata"]["md_checksum"] = compute_checksum(rendered_md)
    atomic_write(STATE_JSON_PATH, json.dumps(state, ensure_ascii=False, indent=2))
    atomic_write(STATE_MD_PATH, rendered_md)
    print(f"✅ 台帳を更新し {STATE_MD_PATH} を再生成しました (Checksum: {state['project_metadata']['md_checksum'][:16]}...)")

def render_markdown(s: dict) -> str:
    meta = s.get("project_metadata", {})
    rev = s.get("revisions", {})
    met = s.get("metrics_summary", {})
    scores = met.get("category_scores", {})
    
    # 英語キーと日本語キーの両対応
    res_score = scores.get("resource", scores.get("リソース効率", "-"))
    qual_score = scores.get("quality", scores.get("品質・堅牢性", "-"))
    evo_score = scores.get("evolution", scores.get("ナレッジ進化", "-"))
    gov_score = scores.get("governance", scores.get("ガバナンス", "-"))

    traits = meta.get("capability_traits", [])
    traits_str = f" + Trait: {', '.join(traits)}" if traits else ""
    
    lines = [
        "# プロジェクト進行状態管理票 (PROJECT_STATE)",
        "",
        f"- **プロジェクト名**: {meta.get('project_name', '')}",
        f"- **現在のステータス**: {s.get('current_status', 'PHASE_1_SETUP')}",
        "- **システム展開プロファイル**:",
        "  - 第1層 (定常コア): Universal Core Specifications (Anti-God Component 250行制限 / 型同期 / Pydantic Settings / Aware UTC / CI / 構造化ログ / モック制御 / グランドデザイン) 適用中",
        f"  - 第2層 (展開プロファイル): {meta.get('deployment_profile', 'Profile A')}{traits_str}",
        f"- **モック動作モード (MOCK_MODE)**: {meta.get('mock_mode', 'ENABLED')}",
        f"- **セッション動作モード (SESSION_MODE)**: {meta.get('session_mode', 'DEV_PIPELINE')}",
        f"- **現行バージョン**: v{meta.get('app_version', '1.0.0')}",
        f"- **EXECUTION_MODE**: {meta.get('execution_mode', 'GLOBAL_PLUGIN')}",
        f"- **TEMPLATE_SOURCE**: {meta.get('template_source', '~/.gemini/config/plugins/system-dev-pipeline')}",
        f"- **Knowledge Hub 連携状態**: {meta.get('knowledge_hub_status', 'SYNCED')}",
        f"- **現在の作業ブランチ**: {meta.get('current_branch', 'main')}",
        f"- **最終更新日時**: {meta.get('updated_at', '')}",
        f"- **最終更新者**: 👑 プロジェクトコンダクター ({meta.get('updated_by', 'Single Writer')})",
        "",
        "---",
        "",
        "## 1. 開発フェーズ進捗一覧",
        ""
    ]
    for ph_key, ph_val in s.get("phases", {}).items():
        st = "x" if ph_val.get("status") == "COMPLETED" else " "
        appr = ph_val.get("approval_gate", {})
        appr_str = f" (承認日: {appr.get('approved_at', '')})" if appr.get("approved") else ""
        lines.append(f"- [{st}] **{ph_key}: {ph_val.get('title', ph_key)}**{appr_str}")
        for t in ph_val.get("tasks", []):
            mark = "x" if t.get("done") else " "
            lines.append(f"  - [{mark}] {t.get('title')}")

    lines.extend([
        "",
        "---",
        "",
        "## 2. プロジェクト定量メトリクスサマリ (最新集計)",
        f"- **総合健全性スコア**: {met.get('total_score', '未測定')} 点",
        f"- **総合品質グレード**: {met.get('grade', '-')}",
        "- **カテゴリ別スコア**:",
        f"  - リソース効率: {res_score} / 25.0 点",
        f"  - 品質・堅牢性: {qual_score} / 35.0 点",
        f"  - ナレッジ進化: {evo_score} / 15.0 点",
        f"  - ガバナンス  : {gov_score} / 25.0 点",
        f"- **通算トークン消費**: {met.get('total_tokens', '-')} tokens",
        f"- **通算ツール呼出数**: {met.get('total_tool_calls', '-')} 回",
        f"- **正味開発規模(LOC)**: {met.get('net_loc', '-')} 行",
        "- **成果物リンク**:",
        "  - [総合健全性診断レポート](./metrics/system_health_report.md)",
        "  - [開発フェーズ推移レポート](./metrics/development_phase_report.md)",
        "  - [定量メトリクス集計JSON](./metrics/development-metrics-summary.json)",
        "",
        "---",
        "",
        "## 3. システム改訂管理 (PHASE 8完了以降)",
        f"- **現在の改訂ステータス**: {rev.get('current_revision_status', 'IDLE')}",
        f"- **進行中の改訂依頼番号**: {rev.get('active_revision_id', 'なし')}",
        f"- **現行改訂ターン番号**: {rev.get('current_turn', '-')}",
        "",
        "### 改訂履歴テーブル",
        "| 改訂依頼番号 | 対象バージョン | ターン | ステータス | 主担当 | 概要 | 完了日 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ])
    for h in rev.get("history", []):
        lines.append(f"| {h.get('id')} | {h.get('version', '-')} | {h.get('turn', '-')} | {h.get('status')} | {h.get('author', 'conductor')} | {h.get('title')} | {h.get('completed_at', '-')} |")

    lines.extend(["", "---", "", "## 4. 未決事項 (Open Questions) & 決定事項 (Decisions)"])
    for q in s.get("open_questions", []):
        lines.append(f"- ❓ {q}")
    for d in s.get("decisions", []):
        lines.append(f"- 💡 [{d.get('date', '')}] {d.get('summary', '')}")
    lines.append("")
    return "\n".join(lines)

def cmd_init(args):
    schema_path = Path(__file__).resolve().parent.parent / "templates" / "project_state.schema.json"
    traits = [t.strip() for t in args.traits.split(",") if t.strip()] if getattr(args, "traits", None) else []
    state = {
        "schema_version": "3.0.0",
        "project_metadata": {
            "project_name": args.name or Path.cwd().name,
            "app_version": args.version or "1.0.0",
            "deployment_profile": args.profile or "Profile A",
            "capability_traits": traits,
            "session_mode": "DEV_PIPELINE",
            "mock_mode": "ENABLED",
            "execution_mode": "GLOBAL_PLUGIN",
            "template_source": "~/.gemini/config/plugins/system-dev-pipeline",
            "knowledge_hub_status": "SYNCED (Immutable Core v3.0.0 + Local Overlay)",
            "current_branch": "main",
            "updated_at": now_iso(),
            "updated_by": "conductor",
            "md_checksum": ""
        },
        "current_status": "PHASE_1_SETUP",
        "phases": {
            "PHASE_1": {"status": "IN_PROGRESS", "title": "プロジェクトの準備", "tasks": [
                {"id": "P1-T01", "title": "ディレクトリ・環境設定展開 (dev-phase1-setup)", "done": True},
                {"id": "P1-T02", "title": "Central Knowledge Hub 初期化 & 未処理原票確認", "done": True},
                {"id": "P1-T03", "title": "静的スケルトン基盤展開", "done": True},
                {"id": "P1-T04", "title": "環境変数初期化 (.env)", "done": True}
            ]},
            "PHASE_2": {"status": "PENDING", "title": "要件定義", "approval_gate": {"required": True, "approved": False}, "tasks": [
                {"id": "P2-T01", "title": "要件定義書作成・精査 (REQ-ID付与)", "done": False}
            ]},
            "PHASE_3": {"status": "PENDING", "title": "基本設計書の作成と整合性チェック", "approval_gate": {"required": True, "approved": False}, "tasks": [
                {"id": "P3-T01", "title": "4大基本設計書作成", "done": False},
                {"id": "P3-T02", "title": "基本設計レビュー (dev-review-arch) PASS", "done": False}
            ]},
            "PHASE_4": {"status": "PENDING", "title": "開発環境とシステム構築", "tasks": [
                {"id": "P4-T01", "title": "Docker/環境構築 & BE/FE実装", "done": False},
                {"id": "P4-T02", "title": "Git初期化 (dev-git-init)", "done": False},
                {"id": "P4-T03", "title": "Hard Gate (harness_guard.py) & CI検証 PASS", "done": False}
            ]},
            "PHASE_5": {"status": "PENDING", "title": "ウォークスルー動作確認とデバッグ", "approval_gate": {"required": True, "approved": False}, "tasks": [
                {"id": "P5-T01", "title": "ブラウザ感覚センサー検証 (Chrome DevTools MCP)", "done": False},
                {"id": "P5-T02", "title": "モック切替検証 & API仕様書同期", "done": False}
            ]},
            "PHASE_5_5": {"status": "PENDING", "title": "コード品質・整合性レビュー", "tasks": [
                {"id": "P55-T01", "title": "dev-review-code (CLEAN判定)", "done": False}
            ]},
            "PHASE_6": {"status": "PENDING", "title": "スルーテスト環境の構築と実施", "approval_gate": {"required": True, "approved": False}, "tasks": [
                {"id": "P6-T01", "title": "シナリオテスト & RTM検証 (traceability_checker.py)", "done": False}
            ]},
            "PHASE_7": {"status": "PENDING", "title": "本番リリース", "approval_gate": {"required": True, "approved": False}, "tasks": [
                {"id": "P7-T01", "title": "dev-review-system (RELEASE APPROVED)", "done": False},
                {"id": "P7-T02", "title": "本番デプロイ & セキュリティ検証", "done": False}
            ]},
            "PHASE_8": {"status": "PENDING", "title": "知見自己進化・メトリクス集計", "approval_gate": {"required": True, "approved": False}, "tasks": [
                {"id": "P8-T01", "title": "メトリクス集計 & 知見原票投函 (CLAIM-*)", "done": False},
                {"id": "P8-T02", "title": "本番リリース (dev-git-release)", "done": False}
            ]}
        },
        "review_gates": {
            "arch_review": {"verdict": "PENDING", "critical": 0, "high": 0, "medium": 0, "low": 0},
            "code_review": {"verdict": "PENDING", "critical": 0, "high": 0, "medium": 0, "low": 0},
            "system_review": {"verdict": "PENDING", "critical": 0, "high": 0, "medium": 0, "low": 0}
        },
        "metrics_summary": {"total_score": None, "grade": "-"},
        "revisions": {"current_revision_status": "IDLE", "active_revision_id": None, "current_turn": None, "history": []},
        "open_questions": [],
        "decisions": [],
        "infrastructure": {"git_commit": "-", "remote_url": "-", "container_status": "STOPPED", "production_url": "-"}
    }
    save_and_render(state)

def cmd_set_mode(args):
    state = load_state()
    mode = args.mode.upper()
    if mode not in ("DEV_PIPELINE", "CONTENT_PRODUCTION"):
        print(f"❌ 不正なセッションモードです: {mode} (DEV_PIPELINE または CONTENT_PRODUCTION を指定してください)", file=sys.stderr)
        sys.exit(1)
    state.setdefault("project_metadata", {})["session_mode"] = mode
    save_and_render(state)
    print(f"🔄 セッションモードを {mode} に更新しました。")

def cmd_set_traits(args):
    state = load_state()
    traits = [t.strip() for t in args.traits.split(",") if t.strip()]
    state.setdefault("project_metadata", {})["capability_traits"] = traits
    save_and_render(state)
    print(f"🔄 Capability Traits を更新しました: {traits}")

def check_review_readiness(state: dict) -> list[str]:
    """REV-4 実機レビュー突入前の前提条件を機械検証する (Readiness Hard Gate)"""
    violations = []
    root = Path.cwd()

    # 検査1: harness_guard.py --all の呼び出し (終了コード0, 違反0件)
    guard_script = Path(__file__).resolve().parent / "harness_guard.py"
    if guard_script.is_file():
        res = subprocess.run([sys.executable, str(guard_script), "--all"], capture_output=True, text=True)
        if res.returncode != 0:
            err_msg = res.stderr.strip() or res.stdout.strip()
            violations.append(f"[READINESS-HG] Harness Guard 規約違反が検出されました:\n{err_msg}")

    # 検査2: ドキュメント衛生検査 (Current配下の一時ファイル不在、docs/設計書/ 直下の未整理ファイル不在)
    docs_dir = root / "docs" / "設計書"
    if docs_dir.is_dir():
        for f in docs_dir.glob("*.md"):
            violations.append(f"[READINESS-DOC] docs/設計書/ 直下に未整理のファイルが放置されています: {f.name}")
        current_dir = docs_dir / "Current"
        if current_dir.is_dir():
            for f in current_dir.iterdir():
                fn = f.name.lower()
                if fn.endswith((".bak", ".tmp", ".swp")) or "draft" in fn or re.search(r"(_v\d+(\.\d+)*|-v\d+(\.\d+)*|\bv\d+(\.\d+)*)\.md$", fn):
                    violations.append(f"[READINESS-DOC] docs/設計書/Current/ 配下に不正な一時・バージョン付きファイルが存在します: {f.name}")

    # 検査3: モック解除状態 (.env の VITE_ENABLE_MOCK=false, project_state.json の mock_mode = DISABLED)
    env_mock = None
    env_file = root / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("VITE_ENABLE_MOCK="):
                env_mock = line.split("=", 1)[1].strip().strip('"\'').lower()
                break
    mock_mode_meta = state.get("project_metadata", {}).get("mock_mode", "").upper()
    if env_mock != "false":
        violations.append(f"[READINESS-MOCK] .env の VITE_ENABLE_MOCK が false ではありません (現状: {env_mock})。実データ結合モードに設定してください。")
    if mock_mode_meta != "DISABLED":
        violations.append(f"[READINESS-MOCK] project_state.json の mock_mode が DISABLED ではありません (現状: {mock_mode_meta})。")

    # 検査4: 最新の署名付き metrics/qa_runtime_evidence.json の実在およびチェックサム検証
    qa_path = root / "metrics" / "qa_runtime_evidence.json"
    if not qa_path.is_file():
        violations.append("[READINESS-QA] 実結合QA実行証跡 (metrics/qa_runtime_evidence.json) が存在しません。(実行必須: python3 scripts/traceability_checker.py --mode full)")
    else:
        try:
            qa_data = json.loads(qa_path.read_text(encoding="utf-8"))
            stored_cs = qa_data.get("sha256_checksum") or qa_data.get("evidence_checksum")
            payload = {k: v for k, v in qa_data.items() if k not in ("sha256_checksum", "evidence_checksum")}
            calc_cs = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
            if not stored_cs or stored_cs != calc_cs:
                violations.append("[READINESS-QA] metrics/qa_runtime_evidence.json のSHA-256署名チェックサム検証に失敗しました。")
            if not qa_data.get("mock_mode_disabled"):
                violations.append("[READINESS-QA] metrics/qa_runtime_evidence.json で mock_mode_disabled が true になっていません。")
            if qa_data.get("overall_status") != "PASS":
                violations.append(f"[READINESS-QA] metrics/qa_runtime_evidence.json の overall_status が PASS ではありません (現状: {qa_data.get('overall_status')})。")
        except Exception as e:
            violations.append(f"[READINESS-QA] metrics/qa_runtime_evidence.json の解析に失敗しました: {e}")

    # 検査5: Stage 2 Live Invariant Probe (完全分離サブプロセス一時起動＆実DBクエリ疎通検証)
    probe_violations = run_live_invariant_probe(root)
    violations.extend(probe_violations)

    return violations

def run_live_invariant_probe(root: Path) -> list[str]:
    """Stage 2: Live Invariant Probe - バックエンド独立プロセス一時起動＆実DBクエリ疎通検証"""
    backend_dirs = [
        (root / "backend" / "app" / "main.py", "backend.app.main:app", root),
        (root / "backend" / "core" / "main.py", "core.main:app", root / "backend"),
        (root / "backend" / "main.py", "backend.main:app", root),
    ]
    target_entry = None
    for file_path, module_spec, cwd_dir in backend_dirs:
        if file_path.is_file():
            target_entry = (file_path, module_spec, cwd_dir)
            break

    if not target_entry:
        return []

    file_path, module_spec, cwd_dir = target_entry

    probe_port = 8999
    for p in range(8999, 9050):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                probe_port = p
                break

    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    additional_paths = [str(root), str(root / "backend")]
    env["PYTHONPATH"] = os.pathsep.join(additional_paths + ([current_pythonpath] if current_pythonpath else []))

    cmd = [sys.executable, "-m", "uvicorn", module_spec, "--port", str(probe_port)]
    process = None
    violations = []
    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(cwd_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        start_time = time.time()
        timeout = 15.0
        success = False
        last_error = ""

        probe_urls = [
            f"http://127.0.0.1:{probe_port}/api/health?deep=true",
            f"http://127.0.0.1:{probe_port}/api/internal/health?deep=true",
            f"http://127.0.0.1:{probe_port}/health?deep=true"
        ]

        while time.time() - start_time < timeout:
            ret = process.poll()
            if ret is not None:
                stderr_output = process.stderr.read()
                last_error = f"プロセスが予期せず終了しました (Exit Code: {ret}):\n{stderr_output.strip()}"
                break

            for url in probe_urls:
                try:
                    req = urllib.request.Request(url, method="GET")
                    with urllib.request.urlopen(req, timeout=1.0) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            db_info = data.get("database", {})
                            db_connected = db_info.get("connected", True) if isinstance(db_info, dict) else (db_info == "connected")
                            if data.get("status") in ("healthy", "ok") and db_connected:
                                success = True
                                break
                except Exception as e:
                    last_error = str(e)
            if success:
                break
            time.sleep(0.5)

        if not success:
            if not last_error and process.poll() is None:
                last_error = "15秒以内に Deep Health Probe (HTTP 200 OK) に応答しませんでした (起動タイムアウト)。"
            violations.append(f"[READINESS-PROBE] Live Invariant Probe (サーバー実動＆実DB疎通) に失敗しました:\n{last_error}")

    except Exception as e:
        violations.append(f"[READINESS-PROBE] Live Invariant Probe 実行中に例外が発生しました: {e}")
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)

    return violations

def cmd_verify_review_readiness(args):
    state = load_state()
    violations = check_review_readiness(state)
    if violations:
        print("🚨 [READINESS BLOCKED] 実機レビュー準備検査 (verify-review-readiness) で違反を検出しました:", file=sys.stderr)
        for v in violations:
            print(f"  • {v}", file=sys.stderr)
        sys.exit(1)
    print("✅ [READINESS PASS] 実機レビュー (REV-4) 移行準備検査をすべてクリアしました (Hard Gate, 文書衛生, モック解除, QA署名証跡, Live Invariant Probe)。")
    sys.exit(0)

def normalize_phase_key(phase: str) -> str:
    p = phase.upper()
    if "5_5" in p or "55" in p:
        return "PHASE_5_5"
    for i in (1, 2, 3, 4, 5, 6, 7, 8):
        if p == f"PHASE_{i}" or p.startswith(f"PHASE_{i}_"):
            return f"PHASE_{i}"
    return phase

def cmd_set_phase(args):
    state = load_state()
    target = args.phase
    norm_target = normalize_phase_key(target)

    # Gate Interlock
    if norm_target in ("REV_4", "REV-4"):
        violations = check_review_readiness(state)
        if violations:
            print("🚨 [GATE BLOCKED] REV-4 移行前提条件 (verify-review-readiness) 未達成のため遷移できません:", file=sys.stderr)
            for v in violations:
                print(f"  • {v}", file=sys.stderr)
            sys.exit(1)
    elif norm_target == "PHASE_4":
        arch_v = state.get("review_gates", {}).get("arch_review", {}).get("verdict")
        if arch_v not in ("PASS", "CONDITIONAL PASS"):
            print(f"🚨 [GATE BLOCKED] 基本設計レビュー未合格 (現状: {arch_v}) のため PHASE 4 へ遷移できません。", file=sys.stderr)
            sys.exit(1)
    elif norm_target == "PHASE_6":
        code_v = state.get("review_gates", {}).get("code_review", {}).get("verdict")
        if code_v != "CLEAN":
            print(f"🚨 [GATE BLOCKED] コード品質レビュー未合格 (現状: {code_v}) のため PHASE 6 へ遷移できません。", file=sys.stderr)
            sys.exit(1)
    elif norm_target == "PHASE_7":
        sys_v = state.get("review_gates", {}).get("system_review", {}).get("verdict")
        if sys_v != "RELEASE APPROVED":
            print(f"🚨 [GATE BLOCKED] システム総合レビュー未合格 (現状: {sys_v}) のため PHASE 7 へ遷移できません。", file=sys.stderr)
            sys.exit(1)

    state["current_status"] = target
    for k, v in state.get("phases", {}).items():
        if k == norm_target:
            v["status"] = "IN_PROGRESS"
    save_and_render(state)

def cmd_complete_task(args):
    state = load_state()
    tid = args.id
    found = False
    for ph_key, ph in state.get("phases", {}).items():
        for t in ph.get("tasks", []):
            if t.get("id") == tid or (args.keyword and args.keyword.lower() in t.get("title", "").lower()):
                t["done"] = True
                found = True
                print(f"✅ タスク完了マーク: [{t.get('id')}] {t.get('title')}")
    if not found:
        print(f"⚠️ タスク ID '{tid}' が見つかりませんでした。", file=sys.stderr)
    save_and_render(state)

def cmd_record_review(args):
    state = load_state()
    rg = state.setdefault("review_gates", {})
    r_key = f"{args.type}_review"
    rg[r_key] = {
        "verdict": args.verdict,
        "critical": args.critical or 0,
        "high": args.high or 0,
        "medium": args.medium or 0,
        "low": args.low or 0,
        "report_path": args.report or "",
        "updated_at": now_iso()
    }
    save_and_render(state)

def cmd_record_approval(args):
    state = load_state()
    p_norm = args.phase.upper().replace("-", "_")
    approver = args.approver or "user"

    # 改訂フェーズ (REV_1〜REV_6) の場合
    if p_norm.startswith("REV_"):
        rev = state.setdefault("revisions", {})
        rev_phases = rev.setdefault("rev_phases", {})
        rev_target = rev_phases.setdefault(p_norm, {})
        rev_target["approved"] = True
        rev_target["approved_at"] = now_iso()
        rev_target["approver"] = approver
        rev_target["status"] = "COMPLETED"
        save_and_render(state)
        print(f"✅ 改訂フェーズ {p_norm} のユーザー承認を記録しました (Approver: {approver})")
        return

    ph = state.get("phases", {}).get(args.phase, {})
    gate = ph.setdefault("approval_gate", {})
    gate["approved"] = True
    gate["approved_at"] = now_iso()
    gate["approver"] = approver
    ph["status"] = "COMPLETED"
    save_and_render(state)

def cmd_sync_metrics(args):
    state = load_state()
    m_path = Path(args.path) if args.path else METRICS_JSON_PATH
    if not m_path.exists():
        print(f"⚠️ メトリクス集計ファイル {m_path} が存在しません。", file=sys.stderr)
        return
    m_data = json.loads(m_path.read_text(encoding="utf-8"))
    summary = m_data.get("summary", m_data)
    resources = m_data.get("resources", {})
    artifacts = m_data.get("artifacts", {})
    
    cat_scores = summary.get("category_scores", {})
    scores = {}
    key_mapping = {
        "resource": ["resource", "リソース効率"],
        "quality": ["quality", "品質・堅牢性"],
        "evolution": ["evolution", "ナレッジ進化"],
        "governance": ["governance", "ガバナンス"]
    }
    for eng_k, cands in key_mapping.items():
        val = None
        for cand in cands:
            if cand in cat_scores:
                c_val = cat_scores[cand]
                val = c_val.get("weighted_score", c_val) if isinstance(c_val, dict) else c_val
                break
        scores[eng_k] = val if val is not None else "-"

    state["metrics_summary"] = {
        "total_score": summary.get("total_score", summary.get("total_health_score")),
        "grade": summary.get("grade", summary.get("overall_grade", "-")),
        "category_scores": scores,
        "total_tokens": summary.get("total_tokens") or resources.get("total_tokens_consumed", "-"),
        "total_tool_calls": summary.get("total_tool_calls") or resources.get("tool_calls_total", "-"),
        "net_loc": summary.get("net_loc") or artifacts.get("git_net_loc_added", "-"),
        "last_collected_at": now_iso()
    }
    save_and_render(state)

def cmd_verify_integrity(args):
    state = load_state()
    if not STATE_MD_PATH.exists():
        print(f"❌ {STATE_MD_PATH} が存在しません。", file=sys.stderr)
        sys.exit(1)
    cur_text = STATE_MD_PATH.read_text(encoding="utf-8")
    actual_hash = compute_checksum(cur_text)
    expected_hash = state.get("project_metadata", {}).get("md_checksum", "")
    if actual_hash == expected_hash:
        print(f"✅ [INTEGRITY OK] {STATE_MD_PATH} と {STATE_JSON_PATH} の整合性は完全です ({actual_hash[:16]}...)")
        sys.exit(0)

    print(f"⚠️ [INTEGRITY MISMATCH] 手動直接編集を検知しました (Expected: {expected_hash[:12]}, Actual: {actual_hash[:12]})")
    if args.reconcile:
        # Reconcile open questions & decisions from text
        qs = re.findall(r"- ❓ (.*?)$", cur_text, re.MULTILINE)
        if qs:
            state["open_questions"] = list(dict.fromkeys(state.get("open_questions", []) + qs))
        save_and_render(state)
        print(f"🔄 手動追記分を {STATE_JSON_PATH} へマージ逆同期しました。")
        sys.exit(0)
    sys.exit(1)

def scaffold_revision_plan(rid: str, title: str):
    """start-revision 実行時に REV-1〜REV-6 準拠の計画スケルトンを自動生成する (V3.0.0)"""
    plans_dir = Path(f"docs/plans/{rid}改訂計画")
    plans_dir.mkdir(parents=True, exist_ok=True)
    
    # 現行 Overlay ルールの読み込み
    overlay_path = Path.home() / ".gemini" / "knowledge-hub" / "overlay" / "LOCAL_FEEDBACK_RULES.md"
    overlay_rules_text = ""
    if overlay_path.is_file():
        try:
            overlay_rules_text = overlay_path.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    if not overlay_rules_text:
        overlay_rules_text = "（現在適用中の追加ローカルオーバーレイ規約はありません）"

    plan_file = plans_dir / "00_改訂基本計画書.md"
    if not plan_file.exists():
        plan_content = f"""# 改訂基本計画書: [{rid}] {title}

- **改訂依頼番号**: {rid}
- **改訂タイトル**: {title}
- **起票日時**: {now_iso()}
- **ステータス**: 計画策定中 (REV-1)

---

## 1. 改訂概要および目的
- 対象改訂の目的、スコープ、背景を簡潔に記載してください。

---

## 2. 標準改訂フェーズ (REV-1〜REV-6) チェックリスト

- [ ] **REV-1: 要件・設計・契約フィクスチャ精査 (Planning, Design & Contracts)**
  - [ ] 差分要件定義書起草・精査 (`[REQ-Fxx]`, `[REQ-NFxx]`)
  - [ ] 差分基本設計書起草（技術・スキーマ・ロジック・画面仕様書）
  - [ ] Executable Golden Fixtures (`tests/fixtures/golden/`) 配置
  - [ ] 基本設計レビュー (`dev-review-arch` / `traceability_checker.py --mode design`) PASS
- [ ] **REV-2: 実装・静的検証・Stage 1 スモーク (Implementation, Hard Gate & Smoke)**
  - [ ] バックエンド/フロントエンド差分実装（行数制限 2段階緩衝帯 250/350, 400/550 遵守、空実装排除）
  - [ ] OpenAPI型同期 (Contract-First MSW)
  - [ ] Stage 1 インプロセス実I/O・物理ファイル生成＆パーサー検証
  - [ ] コミット前 Hard Gate (`python3 scripts/harness_guard.py --all`) PASS
- [ ] **REV-3: 自動テスト・実結合E2E・Stage 2 Live Probe 検証 (Automated E2E & Live Probe)**
  - [ ] シナリオテスト拡充（異常系比率20%以上、3階層深層アサーション、トートロジー排除）
  - [ ] Stage 3 前提モックOFF (`VITE_ENABLE_MOCK=false`) 実データ一気通貫E2E検証
  - [ ] ブラウザ感覚センサー検証（コンソールエラー0件、WCAG AA 4.5:1）
  - [ ] `traceability_checker.py --mode full` PASS & `qa_runtime_evidence.json` 出力
  - [ ] Stage 2 Live Probe 検証 (`python3 scripts/state_manager.py verify-review-readiness`) PASS
- [ ] **REV-4: 開発サーバー起動・ユーザー実機レビュー・改修 (User Live Review & Refinement)**
  - [ ] 実結合モード開発サーバー（Docker / Uvicorn + Vite dev / Tauri dev）起動
  - [ ] ユーザーへの実機動作デモ提示と実機テストレビュー要請
  - [ ] ユーザー指摘事項の対話的改修・再検証ループ
  - [ ] ユーザー実機レビュー承認取得 (`python3 scripts/state_manager.py record-approval --phase REV_4`)
- [ ] **REV-5: 本番総合監査・成果物ビルド (System Review & Production Build)**
  - [ ] コード品質レビュー (`dev-review-code`) CLEAN
  - [ ] システム総合レビュー (`dev-review-system`) RELEASE APPROVED
  - [ ] 本番成果物の物理ビルド（Profile D: `npm run tauri build` / Profile A: 本番コンテナ確認）
- [ ] **REV-6: メトリクス・知見昇格・リリース (Metrics, Evolution & Closure)**
  - [ ] 定量メトリクス集計 (`python3 scripts/metrics_collector.py --all --sync-state`)
  - [ ] RCA知見の整理・昇格 (`wiki-proposer`, `TEMPLATE_PROMOTIONS.md` 承認・反映)
  - [ ] Invariants Gate 自動検証 (`python3 scripts/state_manager.py complete-revision`) PASS

---

## 3. 適用必須ガードレール一覧 (起草時点 Overlay スナップショット)

```markdown
{overlay_rules_text}
```
"""
        plan_file.write_text(plan_content, encoding="utf-8")
        print(f"📄 改訂計画スケルトンを自動生成しました: {plan_file}")

    step_templates = [
        ("REV-1_要件・設計・契約フィクスチャ精査手順書.md", "REV-1: 要件定義・基本設計・Golden Fixture・RTM設計カバレッジ検証の手順"),
        ("REV-2_実装・静的検証・Stage1スモーク手順書.md", "REV-2: 実装・2段階行数制限・harness_guard・Stage 1実I/Oスモーク検証の手順"),
        ("REV-3_テスト・実結合E2E・Stage2LiveProbe検証手順書.md", "REV-3: シナリオテスト・モックOFF実結合E2E・感覚センサー・Stage 2 Live Probe検証の手順"),
        ("REV-4_開発サーバー起動・ユーザー実機レビュー・改修手順書.md", "REV-4: 開発サーバー起動・ユーザー実機テストレビュー・対話的改修の手順"),
        ("REV-5_本番総合監査・成果物ビルド手順書.md", "REV-5: コード/システム総合レビュー合格および本番バイナリ/成果物ビルドの手順"),
        ("REV-6_メトリクス・知見昇格・リリース手順書.md", "REV-6: メトリクス集計・知見昇格・Invariants検証・リリースの手順"),
    ]
    for filename, step_desc in step_templates:
        step_p = plans_dir / filename
        if not step_p.exists():
            step_p.write_text(f"# {step_desc}\n\n- 改訂依頼番号: {rid}\n- ステータス: 準備中\n", encoding="utf-8")

def validate_revision_closure_invariants(state: dict):
    """改訂クローズ時の前提条件を決定論的に機械検証する (Invariants Hard Gate)"""
    violations = []
    metadata = state.get("project_metadata", {})
    profile = metadata.get("deployment_profile", "")

    # 1. 本番成果物の物理実在性検証 (Profile別)
    if "Profile D" in profile or Path("src-tauri").is_dir():
        bundle_dirs = [
            Path("src-tauri/target/release/bundle"),
            Path("src-tauri/target/release")
        ]
        has_release_artifact = False
        for bdir in bundle_dirs:
            if bdir.is_dir():
                for f in bdir.rglob("*"):
                    if f.is_file() and not f.name.endswith((".d", ".rlib", ".rmeta")):
                        has_release_artifact = True
                        break
            if has_release_artifact:
                break
        if not has_release_artifact:
            violations.append(
                "[INV-REL-01] Profile D 本番アプリ成果物 (src-tauri/target/release/bundle/*) が未ビルドです。"
                " (実行必須: npm run tauri build)"
            )
    elif "Profile A" in profile:
        if not Path("Dockerfile").exists() and not Path("Dockerfile.prod").exists() and not Path("docker-compose.yml").exists():
            violations.append("[INV-REL-01] Profile A 本番コンテナ構成ファイル (Dockerfile / docker-compose.yml) が存在しません。")

    # 2. 定量メトリクス集計の最新実行検証
    metrics_json = METRICS_JSON_PATH
    if not metrics_json.exists():
        violations.append(
            "[INV-MET-01] 定量メトリクス集計ファイル (metrics/development-metrics-summary.json) が存在しません。"
            " (実行必須: python3 scripts/metrics_collector.py または dev-metrics-collector)"
        )
    else:
        try:
            m_data = json.loads(metrics_json.read_text(encoding="utf-8"))
            summary = m_data.get("summary", m_data)
            score = summary.get("total_score", summary.get("total_health_score"))
            if score is None:
                violations.append("[INV-MET-02] メトリクス集計JSONに total_score が算出されていません。")
        except Exception as e:
            violations.append(f"[INV-MET-03] メトリクス集計JSONの構文解析に失敗しました: {e}")

    # 3. Knowledge Hub 昇格知見の未処理残存検証
    promo_file = Path("TEMPLATE_PROMOTIONS.md")
    if promo_file.exists():
        content = promo_file.read_text(encoding="utf-8")
        if "[ ] 承認待ち" in content or "INBOX_PENDING" in content:
            violations.append(
                "[INV-HUB-01] TEMPLATE_PROMOTIONS.md に未承認・未処理の昇格知見原票が残存しています。"
                " (実行必須: ask_question によるユーザー承認 & pipeline-reconciler.sh --activate-claim)"
            )

    # 4. REV-4 ユーザー実機レビュー承認の検証 (V3.0.0)
    rev_phases = state.get("revisions", {}).get("rev_phases", {})
    rev_4 = rev_phases.get("REV_4", {})
    if not rev_4.get("approved"):
        violations.append(
            "[INV-REV-04] REV-4（開発サーバー起動・ユーザー実機テストレビュー）のユーザー承認が記録されていません。"
            " (実行必須: python3 scripts/state_manager.py record-approval --phase REV_4)"
        )

    # 5. 実結合QA実行証跡 (qa_runtime_evidence.json) 検証 (V3.0.0 / V3.0.1)
    qa_evidence_path = Path("metrics/qa_runtime_evidence.json")
    if qa_evidence_path.is_file():
        try:
            qa_data = json.loads(qa_evidence_path.read_text(encoding="utf-8"))
            if not qa_data.get("mock_mode_disabled"):
                violations.append("[INV-QA-01] metrics/qa_runtime_evidence.json で mock_mode_disabled が true になっていません (本番モックOFF未検証)。")
            if qa_data.get("overall_status") != "PASS":
                violations.append(f"[INV-QA-01] metrics/qa_runtime_evidence.json の overall_status が PASS ではありません (現状: {qa_data.get('overall_status')})。")

            # active_revision_id の一致検証
            cur_rid = state.get("revisions", {}).get("active_revision_id")
            ev_rid = qa_data.get("active_revision_id")
            if cur_rid and ev_rid and cur_rid != ev_rid:
                violations.append(f"[INV-QA-01] metrics/qa_runtime_evidence.json の active_revision_id ({ev_rid}) が現在の改訂ID ({cur_rid}) と一致しません。")

            # SHA-256 チェックサム照合による改ざん検証
            stored_checksum = qa_data.get("sha256_checksum") or qa_data.get("evidence_checksum")
            payload = {k: v for k, v in qa_data.items() if k not in ("sha256_checksum", "evidence_checksum")}
            calc_checksum = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
            if not stored_checksum or stored_checksum != calc_checksum:
                violations.append("[INV-QA-01] metrics/qa_runtime_evidence.json のSHA-256署名チェックサム検証に失敗しました (改ざん・不整合検知)。")
        except Exception as e:
            violations.append(f"[INV-QA-01] metrics/qa_runtime_evidence.json の解析に失敗しました: {e}")
    else:
        violations.append("[INV-QA-01] 実結合QA実行証跡 (metrics/qa_runtime_evidence.json) が存在しません。(実行必須: python3 scripts/traceability_checker.py --mode full)")

    if violations:
        print("❌ [HARD GATE BLOCKED] 改訂完了前提条件 (Invariants) 違反を検出しました:", file=sys.stderr)
        for v in violations:
            print(f"  • {v}", file=sys.stderr)
        print("\n上記の未完了タスクをすべて物理的に完了してから、再度 complete-revision を実行してください。", file=sys.stderr)
        sys.exit(1)

def cmd_start_revision(args):
    state = load_state()
    state.setdefault("project_metadata", {})["session_mode"] = "DEV_PIPELINE"
    rev = state.setdefault("revisions", {})
    rev["current_revision_status"] = "ACTIVE"
    rev["active_revision_id"] = args.id
    rev["rev_phases"] = {
        "REV_1": {"title": "要件・設計・契約フィクスチャ精査", "status": "IN_PROGRESS"},
        "REV_2": {"title": "実装・静的検証・Stage 1 スモーク", "status": "PENDING"},
        "REV_3": {"title": "自動テスト・実結合E2E・Stage 2 Live Probe 検証", "status": "PENDING"},
        "REV_4": {"title": "開発サーバー起動・ユーザー実機レビュー・改修", "status": "PENDING", "approved": False, "approved_at": None, "approver": None},
        "REV_5": {"title": "本番総合監査・成果物ビルド", "status": "PENDING"},
        "REV_6": {"title": "メトリクス・知見昇格・リリース", "status": "PENDING"}
    }
    branch_name = f"revision/{args.id}"
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=False)
        state["project_metadata"]["current_branch"] = branch_name
    except Exception:
        pass
    print(f"🚀 改訂起票: [{args.id}] {args.title} (Branch: {branch_name}, SessionMode: DEV_PIPELINE)")
    scaffold_revision_plan(args.id, args.title)
    save_and_render(state)

def cmd_complete_revision(args):
    state = load_state()
    if not getattr(args, "skip_invariants_check", False):
        validate_revision_closure_invariants(state)

    rev = state.setdefault("revisions", {})
    rid = args.id or rev.get("active_revision_id")
    target_version = args.version or state.get("project_metadata", {}).get("app_version", "1.0.0")
    if args.version:
        state["project_metadata"]["app_version"] = args.version

    turn = getattr(args, "turn", "1") or "1"
    author = getattr(args, "author", "conductor") or "conductor"

    history = rev.setdefault("history", [])
    history.append({
        "id": rid,
        "title": args.title or "機能改訂",
        "version": target_version,
        "turn": turn,
        "author": author,
        "status": "COMPLETED",
        "started_at": state.get("project_metadata", {}).get("updated_at", ""),
        "completed_at": now_iso(),
        "branch": state.get("project_metadata", {}).get("current_branch", "main")
    })
    rev["current_revision_status"] = "IDLE"
    rev["active_revision_id"] = None
    save_and_render(state, author=author)
    print(f"✅ 改訂完了: [{rid}] {args.title or '機能改訂'} (Version: {state.get('project_metadata', {}).get('app_version', '')})")

def main():
    p = argparse.ArgumentParser(description="AI Harness Deterministic State Ledger Manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--name", type=str); p_init.add_argument("--profile", type=str); p_init.add_argument("--version", type=str)
    p_init.add_argument("--traits", type=str, help="Comma-separated capability traits (e.g. local-api,media-export)")

    p_mode = sub.add_parser("set-mode")
    p_mode.add_argument("--mode", type=str, required=True, choices=["DEV_PIPELINE", "CONTENT_PRODUCTION"])

    p_traits = sub.add_parser("set-traits")
    p_traits.add_argument("--traits", type=str, required=True, help="Comma-separated capability traits")

    p_phase = sub.add_parser("set-phase")
    p_phase.add_argument("phase", type=str)
    p_task = sub.add_parser("complete-task")
    p_task.add_argument("--id", type=str, required=True); p_task.add_argument("--keyword", type=str)
    p_rev = sub.add_parser("record-review")
    p_rev.add_argument("--type", choices=["arch", "code", "system"], required=True)
    p_rev.add_argument("--verdict", type=str, required=True)
    for lvl in ["critical", "high", "medium", "low"]: p_rev.add_argument(f"--{lvl}", type=int)
    p_rev.add_argument("--report", type=str)

    p_app = sub.add_parser("record-approval")
    p_app.add_argument("--phase", type=str, required=True)
    p_app.add_argument("--approver", type=str)

    p_sync = sub.add_parser("sync-metrics")
    p_sync.add_argument("--path", type=str)

    p_int = sub.add_parser("verify-integrity")
    p_int.add_argument("--reconcile", action="store_true")

    p_readiness = sub.add_parser("verify-review-readiness", help="Verify readiness for REV-4 review")

    p_srev = sub.add_parser("start-revision")
    p_srev.add_argument("--id", type=str, required=True)
    p_srev.add_argument("--title", type=str, default="機能改訂")

    p_crev = sub.add_parser("complete-revision")
    p_crev.add_argument("--id", type=str)
    p_crev.add_argument("--title", type=str)
    p_crev.add_argument("--version", type=str)
    p_crev.add_argument("--turn", type=str, default="1")
    p_crev.add_argument("--author", type=str, default="conductor")
    p_crev.add_argument("--skip-invariants-check", action="store_true", help="緊急時用にInvariants検査をバイパス")

    args = p.parse_args()
    cmds = {
        "init": cmd_init, "set-mode": cmd_set_mode, "set-traits": cmd_set_traits,
        "set-phase": cmd_set_phase, "complete-task": cmd_complete_task,
        "record-review": cmd_record_review, "record-approval": cmd_record_approval,
        "sync-metrics": cmd_sync_metrics, "verify-integrity": cmd_verify_integrity,
        "verify-review-readiness": cmd_verify_review_readiness,
        "start-revision": cmd_start_revision, "complete-revision": cmd_complete_revision
    }
    cmds[args.cmd](args)

if __name__ == "__main__":
    main()
