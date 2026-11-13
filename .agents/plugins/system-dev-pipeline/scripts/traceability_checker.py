#!/usr/bin/env python3
"""
traceability_checker.py - Requirements Traceability Matrix (RTM) Verifier (V3.0.0 Executable Contract)
Enforces 100% requirements coverage from docs to design and tests, and checks negative test ratio.
Strictly binds [REQ-*] to valid, non-tautological test function scopes and integrates dynamic coverage.
"""
import argparse
import ast
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REQ_PATTERN = re.compile(r"\[(REQ-(?:F|NF)[A-Za-z0-9_-]+)\]")
NEGATIVE_TEST_PATTERN = re.compile(r"(@test_type:\s*negative|abnormal|error|invalid|exception|fail|reject|boundary)", re.IGNORECASE)
IGNORE_TEST_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "coverage", ".agents"}
TEST_FUNC_PATTERN = re.compile(r"^\s*(?:async\s+)?(?:def\s+test_|fn\s+test_)|^\s*(?:it|test)\(")

# TS/JS shallow assertion detection patterns
SHALLOW_ASSERT_ONLY = re.compile(r"expect\([^)]+\)\.(toBeInTheDocument|toBeDefined|not\.toBeNull|toBeTruthy)\(\);?\s*$")
DEEP_INTERACTION_PATTERN = re.compile(r"(fireEvent|userEvent|waitFor|toHaveBeenCalled|toHaveBeenCalledWith|toHaveAttribute|toHaveTextContent|toHaveValue|toStrictEqual|toEqual)")

def is_test_file(path: Path) -> bool:
    parts = set(path.parts)
    if parts & IGNORE_TEST_DIRS:
        return False
    norm = str(path).replace("\\", "/").lower()
    return any(k in norm for k in ["/tests/", "/__tests__/", "/e2e/", ".test.", ".spec."]) or \
           path.name.startswith("test_") or path.name.endswith(("_test.py", "_test.rs"))

class Requirement:
    def __init__(self, req_id: str, title: str, category: str):
        self.req_id = req_id
        self.title = title
        self.category = category  # Functional or Non-Functional
        self.design_refs: list[str] = []
        self.test_refs: list[str] = []

def find_requirements_file(root: Path) -> Path | None:
    candidates = [
        root / "docs" / "設計書" / "Current" / "要件定義書.md",
        root / "docs" / "要件定義書.md",
        root / "docs" / "要件定義書_ProfileA.md",
    ]
    for c in candidates:
        if c.is_file():
            return c
    # 改訂計画書の探索 (docs/plans/*/00_*.md, docs/検討課題/**/00_*.md)
    for p in sorted(root.glob("docs/plans/*/00_*.md"), reverse=True):
        if p.is_file():
            return p
    for p in sorted(root.glob("docs/検討課題/**/00_*.md"), reverse=True):
        if p.is_file():
            return p
    return None

def extract_requirements(req_file: Path) -> dict[str, Requirement]:
    reqs: dict[str, Requirement] = {}
    content = req_file.read_text(encoding="utf-8")
    for line in content.splitlines():
        for match in REQ_PATTERN.finditer(line):
            req_id = match.group(1)
            title = line.replace(f"[{req_id}]", "").strip(" -*#:")
            category = "Non-Functional" if "NF" in req_id else "Functional"
            if req_id not in reqs:
                reqs[req_id] = Requirement(req_id, title, category)
    return reqs

def scan_design_docs(root: Path, reqs: dict[str, Requirement], req_file: Path | None = None):
    search_dirs = [root / "docs" / "設計書" / "Current", root / "docs"]
    doc_files = []
    req_path_resolved = req_file.resolve() if req_file and req_file.exists() else None
    for d in search_dirs:
        if d.is_dir():
            for p in d.glob("*.md"):
                if req_path_resolved and p.resolve() == req_path_resolved:
                    continue
                if p.name == "要件定義書.md":
                    continue
                doc_files.append(p)

    for doc in doc_files:
        try:
            text = doc.read_text(encoding="utf-8")
            for req_id, obj in reqs.items():
                if req_id in text:
                    obj.design_refs.append(doc.name)
        except Exception:
            pass

def check_python_test_validity(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[bool, str]:
    """PAT-TEST-003: テスト関数のAST妥当性（トートロジー・アリバイテスト検知）"""
    has_call = False
    has_assert = False
    tautology_assert = False

    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            if func_name not in ("print", "len", "str", "int", "bool"):
                has_call = True
        elif isinstance(node, ast.Assert):
            has_assert = True
            if isinstance(node.test, ast.Constant) and bool(node.test.value) is True:
                tautology_assert = True
            elif isinstance(node.test, ast.Compare):
                if isinstance(node.test.left, ast.Constant) and len(node.test.comparators) == 1 and isinstance(node.test.comparators[0], ast.Constant):
                    if node.test.left.value == node.test.comparators[0].value:
                        tautology_assert = True

    if tautology_assert:
        return False, "自己完結型定数アサーション (assert True / 1==1)"
    if not has_assert:
        return False, "アサーションが存在しません"
    if not has_call:
        return False, "実コード・API・モジュール呼出を伴わないローカル自己完結テスト"
    return True, "OK"

def get_preceding_comments(lines: list[str], start_line_0idx: int, max_lines: int = 3) -> str:
    """関数の直前最大 max_lines 行のコメント文字列を取得"""
    comments = []
    idx = start_line_0idx - 1
    while idx >= 0 and len(comments) < max_lines:
        line_str = lines[idx].strip()
        if line_str.startswith("#") or line_str.startswith("//") or line_str.startswith("/*") or line_str.startswith("*"):
            comments.append(line_str)
            idx -= 1
        elif not line_str:
            idx -= 1
        else:
            break
    comments.reverse()
    return "\n".join(comments)

def scan_test_artifacts(root: Path, reqs: dict[str, Requirement]) -> tuple[int, int]:
    """
    V3.0.0 Executable Contract-Driven RTM Scanner:
    1. docs/plans/シナリオテスト計画書.md を完全除外。
    2. 有効と判定されたテスト関数スコープ（Python AST 関数ノード / TS・JS・Rust の有効テストブロック＋直上3行コメント）
       に存在する [REQ-*] のみをカウントし、ファイル全文の単純マッチングを根絶。
    """
    test_files = []
    for ext in ["*.py", "*.ts", "*.tsx", "*.js", "*.rs"]:
        for p in root.rglob(ext):
            if is_test_file(p):
                test_files.append(p)

    total_tests = 0
    negative_tests = 0

    for tf in test_files:
        try:
            content = tf.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Python の場合は AST で関数単位の厳格スコープ解析
            if tf.suffix == ".py":
                try:
                    tree = ast.parse(content, filename=str(tf))
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                            is_valid, reason = check_python_test_validity(node)
                            if not is_valid:
                                print(f"⚠️ [トートロジーテスト検知・無効化] {tf.name}:{node.name} - {reason}", file=sys.stderr)
                                continue

                            total_tests += 1
                            func_text = ast.get_source_segment(content, node) or ""
                            # 直前3行コメント
                            pre_comments = get_preceding_comments(lines, node.lineno - 1, max_lines=3)
                            combined_scope_text = f"{pre_comments}\n{node.name}\n{func_text}"

                            if NEGATIVE_TEST_PATTERN.search(node.name) or NEGATIVE_TEST_PATTERN.search(func_text):
                                negative_tests += 1

                            # 有効関数スコープ内の REQ-* のみバインド
                            found_reqs = set(REQ_PATTERN.findall(combined_scope_text))
                            for req_id in found_reqs:
                                if req_id in reqs:
                                    ref_label = f"{tf.name}:{node.name}"
                                    if ref_label not in reqs[req_id].test_refs:
                                        reqs[req_id].test_refs.append(ref_label)
                    continue
                except SyntaxError:
                    pass

            # TS/JS/Rust テストブロック単位解析
            idx = 0
            num_lines = len(lines)
            while idx < num_lines:
                line = lines[idx]
                if TEST_FUNC_PATTERN.search(line):
                    # テストブロックの抽出 (次のテスト開始または15行)
                    block_lines = [line]
                    j = idx + 1
                    while j < num_lines and j < idx + 30:
                        if TEST_FUNC_PATTERN.search(lines[j]):
                            break
                        block_lines.append(lines[j])
                        j += 1
                    block_chunk = "\n".join(block_lines)

                    # 1. トートロジー検査
                    if "assert True" in block_chunk or "assert 1 == 1" in block_chunk or "expect(true).toBe(true)" in block_chunk:
                        print(f"⚠️ [トートロジーテスト検知・無効化] {tf.name}:{line.strip()}", file=sys.stderr)
                        idx = j
                        continue

                    # 2. 浅いアリバイテスト検査 (toBeInTheDocument等のみで操作・副作用検証なし)
                    has_deep_interaction = bool(DEEP_INTERACTION_PATTERN.search(block_chunk))
                    assert_lines = [ln.strip() for ln in block_lines if "expect(" in ln or "assert" in ln]
                    all_shallow = (
                        len(assert_lines) > 0 and
                        all(SHALLOW_ASSERT_ONLY.search(aln) for aln in assert_lines) and
                        not has_deep_interaction
                    )
                    if all_shallow:
                        print(f"⚠️ [浅いアリバイテスト検知・無効化] {tf.name}:{line.strip()} (DOM存在確認のみ・状態検証なし)", file=sys.stderr)
                        idx = j
                        continue

                    total_tests += 1
                    if NEGATIVE_TEST_PATTERN.search(line) or NEGATIVE_TEST_PATTERN.search(block_chunk):
                        negative_tests += 1

                    pre_comments = get_preceding_comments(lines, idx, max_lines=3)
                    combined_scope = f"{pre_comments}\n{block_chunk}"
                    found_reqs = set(REQ_PATTERN.findall(combined_scope))
                    for req_id in found_reqs:
                        if req_id in reqs:
                            ref_label = f"{tf.name}:{line.strip()[:30]}"
                            if ref_label not in reqs[req_id].test_refs:
                                reqs[req_id].test_refs.append(ref_label)
                    idx = j
                else:
                    if "@test_type: negative" in line:
                        negative_tests += 1
                    idx += 1
        except Exception:
            pass

    return total_tests, negative_tests

def check_coverage(root: Path, custom_path: str | None, min_coverage: float) -> tuple[bool, str, dict]:
    """動的カバレッジ（Branch / Line）検証 (V3.0.0)"""
    candidate_paths = []
    if custom_path:
        candidate_paths.append(Path(custom_path))
    candidate_paths.extend([
        root / "coverage" / "coverage-summary.json",
        root / "metrics" / "coverage.json"
    ])

    cov_file = None
    for p in candidate_paths:
        if p.is_file():
            cov_file = p
            break

    if not cov_file:
        return True, "カバレッジファイル未検出 (スキップ)", {}

    try:
        data = json.loads(cov_file.read_text(encoding="utf-8"))
        total = data.get("total", data)
        lines_pct = total.get("lines", {}).get("pct", 100.0)
        branches_pct = total.get("branches", {}).get("pct", 100.0)

        cov_summary = {"file": str(cov_file), "lines_pct": lines_pct, "branches_pct": branches_pct}
        if lines_pct < min_coverage or branches_pct < min_coverage:
            msg = f"カバレッジ基準未達 (Line: {lines_pct:.1f}%, Branch: {branches_pct:.1f}%, 基準: {min_coverage:.1f}%)"
            return False, msg, cov_summary
        return True, f"カバレッジ基準達成 (Line: {lines_pct:.1f}%, Branch: {branches_pct:.1f}%)", cov_summary
    except Exception as e:
        return False, f"カバレッジファイル解析エラー: {e}", {}

def generate_rtm_markdown(reqs: dict[str, Requirement], total_tests: int, neg_tests: int, neg_ratio: float, cov_msg: str = "") -> str:
    lines = [
        "# 要件トレーサビリティマトリクス (RTM: Requirements Traceability Matrix)",
        "",
        "- **生成ツール**: `scripts/traceability_checker.py` (V3.0.0 Executable Contract)",
        f"- **要件総数**: {len(reqs)} 件",
        f"- **総テストケース数**: {total_tests} 件 (うち異常系・境界値: {neg_tests} 件, 異常系比率: {neg_ratio:.1f}%)",
    ]
    if cov_msg:
        lines.append(f"- **動的カバレッジ検証**: {cov_msg}")
    lines.extend([
        "",
        "| 要件ID | 分類 | 要件概要 | 基本設計反映 | テスト関数直結反映 | 充足ステータス |",
        "| :--- | :---: | :--- | :--- | :--- | :---: |"
    ])
    for r in sorted(reqs.values(), key=lambda x: x.req_id):
        d_str = ", ".join(sorted(set(r.design_refs))) if r.design_refs else "❌ 未反映"
        t_str = ", ".join(sorted(set(r.test_refs))) if r.test_refs else "❌ 未検証"
        status = "✅ PASS" if (r.design_refs and r.test_refs) else "🚨 BLOCKED"
        lines.append(f"| {r.req_id} | {r.category} | {r.title} | {d_str} | {t_str} | {status} |")
    lines.append("")
    return "\n".join(lines)

def get_mock_mode_disabled(root: Path) -> bool:
    env_file = root / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("VITE_ENABLE_MOCK="):
                val = line.split("=", 1)[1].strip().strip('"\'').lower()
                return val in ("false", "0", "off", "no")
    return False

def get_active_revision_id(root: Path) -> str | None:
    state_file = root / "project_state.json"
    if state_file.is_file():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            return data.get("revisions", {}).get("active_revision_id")
        except Exception:
            pass
    return os.environ.get("ACTIVE_REVISION_ID")

def get_git_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN_COMMIT"

def emit_qa_runtime_evidence(root: Path, anomaly_test_ratio: float):
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload = {
        "active_revision_id": get_active_revision_id(root),
        "all_requirements_covered": True,
        "anomaly_test_ratio": round(anomaly_test_ratio, 2),
        "generated_at": now_utc,
        "git_commit_hash": get_git_commit_hash(),
        "mock_mode_disabled": get_mock_mode_disabled(root),
        "overall_status": "PASS"
    }
    payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    checksum = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    evidence_data = {**payload, "sha256_checksum": checksum}

    out_path = root / "metrics" / "qa_runtime_evidence.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(evidence_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📜 実結合QA実行証跡を出力しました: {out_path} (SHA-256: {checksum[:16]}...)")

def main():
    parser = argparse.ArgumentParser(description="Requirements Traceability Matrix Verifier (V3.0.0)")
    parser.add_argument("--mode", choices=["design", "full"], default="full",
                        help="Verification mode: 'design' for Phase 3, 'full' for Phase 6/7")
    parser.add_argument("--min-negative-ratio", type=float, default=20.0,
                        help="Minimum negative test ratio percentage (default: 20.0%%)")
    parser.add_argument("--coverage-json", type=str, default=None,
                        help="Path to coverage summary JSON (default: auto-detect coverage/coverage-summary.json)")
    parser.add_argument("--min-coverage", type=float, default=70.0,
                        help="Minimum code coverage percentage (default: 70.0%%)")
    args = parser.parse_args()

    root = Path.cwd()
    req_file = find_requirements_file(root)
    if not req_file:
        print("⚠️ 要件定義書が見つかりません。docs/設計書/Current/要件定義書.md を確認してください。", file=sys.stderr)
        sys.exit(0)

    reqs = extract_requirements(req_file)
    if not reqs:
        print("⚠️ 要件定義書から [REQ-*] ID が抽出されませんでした。", file=sys.stderr)
        sys.exit(0)

    scan_design_docs(root, reqs, req_file)
    design_uncovered = [r for r in reqs.values() if not r.design_refs]

    if args.mode == "design":
        print(f"🔍 [RTM DESIGN CHECK] 要件数: {len(reqs)} 件, 設計未反映: {len(design_uncovered)} 件")
        if design_uncovered:
            print("🚨 [BLOCKED] 基本設計書に反映されていない要件が存在します:", file=sys.stderr)
            for u in design_uncovered:
                print(f"  - [{u.req_id}] {u.title}", file=sys.stderr)
            sys.exit(1)
        print("✅ [PASS] 全要件が基本設計書群に 100% 反映されています。")
        sys.exit(0)

    # mode == full
    total_tests, neg_tests = scan_test_artifacts(root, reqs)
    neg_ratio = (neg_tests / total_tests * 100) if total_tests > 0 else 0.0
    test_uncovered = [r for r in reqs.values() if not r.test_refs]

    cov_ok, cov_msg, _ = check_coverage(root, args.coverage_json, args.min_coverage)

    rtm_md = generate_rtm_markdown(reqs, total_tests, neg_tests, neg_ratio, cov_msg)
    rtm_path = root / "docs" / "plans" / "要件トレーサビリティマトリクス(RTM).md"
    rtm_path.parent.mkdir(parents=True, exist_ok=True)
    rtm_path.write_text(rtm_md, encoding="utf-8")
    print(f"📋 RTMマトリクスを出力しました: {rtm_path}")

    has_error = False
    if design_uncovered or test_uncovered:
        has_error = True
        print(f"🚨 [RTM BLOCKED] 設計未反映: {len(design_uncovered)} 件, テスト未検証: {len(test_uncovered)} 件", file=sys.stderr)
        for u in test_uncovered:
            print(f"  - 未検証要件: [{u.req_id}] {u.title}", file=sys.stderr)

    if total_tests > 0 and neg_ratio < args.min_negative_ratio:
        has_error = True
        print(f"🚨 [RTM BLOCKED] 異常系テスト比率が基準未満です ({neg_ratio:.1f}% < 基準 {args.min_negative_ratio:.1f}%)", file=sys.stderr)

    if not cov_ok:
        has_error = True
        print(f"🚨 [RTM BLOCKED] {cov_msg}", file=sys.stderr)

    if has_error:
        sys.exit(1)

    emit_qa_runtime_evidence(root, neg_ratio)
    print("✅ [RTM FULL PASS] 全要件の設計・テスト 100% カバレッジおよび異常系比率基準を達成しました。")
    sys.exit(0)

if __name__ == "__main__":
    main()
