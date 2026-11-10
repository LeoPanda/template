#!/usr/bin/env python3
"""
harness_guard.py - AI Harness Hard Gate Static Enforcement Engine (Profile E)
Enforces architectural invariants before commit and review phases.
"""
import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Limits & Thresholds (V3.0.0 Two-Tier Line Limit)
FE_LINE_WARN = 250
FE_LINE_BLOCK = 350
BE_LINE_WARN = 400
BE_LINE_BLOCK = 550
IGNORE_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "coverage", ".agents"}

SECRET_PATTERNS = [
    (re.compile(r"AIza[0-9A-Za-z-_]{35}"), "Google API Key"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "OpenAI API Key"),
    (re.compile(r"ghp_[0-9a-zA-Z]{36}"), "GitHub Personal Access Token"),
    (re.compile(r"\b(YOUR_API_KEY_HERE|CHANGE_ME)\b"), "Unreplaced Placeholder"),
]
RAW_DDL_PATTERN = re.compile(r"\b(CREATE|ALTER|DROP)\s+TABLE\b", re.IGNORECASE)
ABSOLUTE_PATH_PATTERN = re.compile(r"\[.*?\]\((file:///|/Users/|/home/|[A-Za-z]:\\).*?\)")

# HG-002: Direct mock and media dummy patterns
MOCK_CALL_PATTERN = re.compile(
    r"\b(mockUsers|dummyData|MOCK_[A-Z0-9_]+|generate_mock_[a-zA-Z0-9_]+|dummy_[a-zA-Z0-9_]+|Mock[A-Z0-9_]+)\b"
)
MEDIA_DUMMY_PATTERN = re.compile(r"\b(testsrc|sine=|anoisesrc|color=black)\b")
SILENT_MOCK_FALLBACK = re.compile(r"catch\s*(\(.*?\))?\s*\{\s*return\s+.*?(mock|dummy)", re.IGNORECASE | re.DOTALL)
DAYLIGHT_DARK_CLASSES = re.compile(r"\b(?<!dark:)(text-(slate|zinc|gray|neutral)-(200|300)|bg-(slate|zinc|gray|neutral)-(900|950)|bg-blue-950)\b")

# HG-010: Anti-Placeholder & empty handler patterns
EMPTY_JSX_HANDLER = re.compile(r"(on[A-Z][a-zA-Z]+)=\{\s*\(\)\s*=>\s*\{\s*\}\s*\}")
DUMMY_GEN_COMMENT = re.compile(r"(<!--\s*(?:Generated|TODO|Placeholder|ダミー)\s*-->|placeholder_output)", re.IGNORECASE)

# PAT-DOC-003: Mermaid bracketed unquoted label pattern
MERMAID_UNQUOTED_BRACKET_LABEL = re.compile(r"-->\|([^\"\|\n]*[\(\)\[\]\{\}【】][^\"\|\n]*)\|")
# PAT-DOC-002: Document individual version in title
DOC_TITLE_VERSION_PATTERN = re.compile(r"^#\s+.*?\([Vv]\d+(\.\d+)*\)")

def get_git_staged_files() -> list[str]:
    try:
        out = subprocess.check_output(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], text=True)
        return [f.strip() for f in out.splitlines() if f.strip()]
    except Exception:
        return []

def collect_all_files(root: Path) -> list[str]:
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for f in filenames:
            rel = os.path.relpath(os.path.join(dirpath, f), root)
            result.append(rel)
    return result

class Violation:
    def __init__(self, rule_id: str, severity: str, file_path: str, message: str, line_no: int = 0, hint: str = ""):
        self.rule_id = rule_id
        self.severity = severity  # "BLOCK" or "WARN"
        self.file_path = file_path
        self.message = message
        self.line_no = line_no
        self.hint = hint

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "file": self.file_path, "line": self.line_no,
            "message": self.message, "hint": self.hint
        }

def check_file(rel_path: str, full_path: Path) -> list[Violation]:
    violations = []
    norm = rel_path.replace("\\", "/")
    if not full_path.is_file() or full_path.stat().st_size > 2 * 1024 * 1024:
        return violations

    try:
        content = full_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return violations
    lines = content.splitlines()
    line_count = len(lines)

    # HG-001: Two-Tier Line Limit (WARN: soft limit / BLOCK: hard limit)
    is_test = any(k in norm for k in ["/tests/", "/__tests__/", ".test.", ".spec."])
    is_gen = norm.endswith(".generated.ts") or "migrations/" in norm or "alembic/" in norm
    if not is_test and not is_gen:
        if (norm.startswith("frontend/src/") or norm.startswith("src/")) and norm.endswith((".tsx", ".ts", ".jsx", ".js")):
            if line_count > FE_LINE_BLOCK:
                violations.append(Violation("HG-001", "BLOCK", norm, f"フロントエンド行数ハード上限超過 ({line_count}行 > {FE_LINE_BLOCK}行)",
                                            hint="Hooksやサブコンポーネントへ物理分割してください。"))
            elif line_count > FE_LINE_WARN:
                violations.append(Violation("HG-001", "WARN", norm, f"フロントエンド行数ソフト上限超過 ({line_count}行 > {FE_LINE_WARN}行)",
                                            hint="PHASE 5.5 (dev-review-code) でHooks/サブコンポーネントへの分割を推奨します。"))
        elif (norm.startswith("backend/") and norm.endswith(".py")) or (norm.startswith("src-tauri/") and norm.endswith(".rs")):
            if line_count > BE_LINE_BLOCK:
                violations.append(Violation("HG-001", "BLOCK", norm, f"バックエンド行数ハード上限超過 ({line_count}行 > {BE_LINE_BLOCK}行)",
                                            hint="DTOやサービス層へモジュールを物理分割してください。"))
            elif line_count > BE_LINE_WARN:
                violations.append(Violation("HG-001", "WARN", norm, f"バックエンド行数ソフト上限超過 ({line_count}行 > {BE_LINE_WARN}行)",
                                            hint="PHASE 5.5 (dev-review-code) でサービス層/モジュール分割を推奨します。"))

    # HG-002: Direct mock in production code (FE / BE / Desktop)
    is_prod_code = any(norm.startswith(p) for p in [
        "src/components/", "src/pages/", "src/hooks/", "src/services/",
        "frontend/src/components/", "frontend/src/pages/", "frontend/src/hooks/", "frontend/src/services/",
        "backend/", "src-tauri/"
    ])
    is_exempt = "src/mocks/" in norm or is_test or any(k in norm for k in ["/.venv/", "/tests/", "/alembic/", "/migrations/"])
    if is_prod_code and not is_exempt:
        if MOCK_CALL_PATTERN.search(content):
            violations.append(Violation("HG-002", "BLOCK", norm, "直書きモック識別子 (mockUsers/dummyData/generate_mock_*/dummy_*/Mock*) を検出",
                                        hint="MSW (src/mocks/) または Fixtures へ移行し、本番コードからは直接参照しないでください。"))
        if SILENT_MOCK_FALLBACK.search(content):
            violations.append(Violation("HG-002", "BLOCK", norm, "サイレントモックフォールバック (catch return mock) を検出",
                                        hint="Fail-Fast原則に従い、本番通信エラー時は例外を即スローしてください。"))
        if MEDIA_DUMMY_PATTERN.search(content):
            violations.append(Violation("HG-002", "BLOCK", norm, "メディアダミー生成記述 (testsrc/sine=/anoisesrc/color=black) を検出",
                                        hint="Golden Fixtures (tests/fixtures/golden/) または実メディア生成ロジックを使用してください。"))

    # HG-003: Absolute paths in Markdown
    if norm.endswith(".md"):
        for idx, line in enumerate(lines, 1):
            if ABSOLUTE_PATH_PATTERN.search(line):
                violations.append(Violation("HG-003", "BLOCK", norm, "Markdown内絶対パスリンクを検出", line_no=idx,
                                            hint="ファイル間の相対パス (例: ../設計書.md) に書き換えてください。"))

    # HG-004: Raw SQL DDL in BE
    if norm.startswith("backend/") and norm.endswith(".py") and not any(k in norm for k in ["/tests/", "/alembic/", "/migrations/", "/.venv/"]):
        for idx, line in enumerate(lines, 1):
            if RAW_DDL_PATTERN.search(line) and not line.strip().startswith("#"):
                violations.append(Violation("HG-004", "BLOCK", norm, "生SQL DDL (CREATE/ALTER/DROP TABLE) を検出", line_no=idx,
                                            hint="SQLAlchemyモデル定義およびAlembicマイグレーションを使用してください。"))

    # HG-005: AST fitness for BE
    if norm.startswith("backend/") and norm.endswith(".py") and not any(k in norm for k in ["/tests/", "/alembic/", "/migrations/", "/.venv/"]):
        violations.extend(check_ast_fitness(norm, content))

    # HG-006: Daylight theme contrast static warning
    if norm.endswith((".tsx", ".jsx")) and not is_test:
        for idx, line in enumerate(lines, 1):
            if "className=" in line and DAYLIGHT_DARK_CLASSES.search(line):
                violations.append(Violation("HG-006", "WARN", norm, "Tailwind デイライト視認性違反の疑い (dark: なしの淡色/暗色単独指定)", line_no=idx,
                                            hint="セマンティックデザイントークンまたは明暗ペア指定 (例: bg-blue-50 text-blue-800 dark:...) を使用してください。"))

    # HG-007: Plaintext secrets & placeholders
    if not norm.endswith((".example", ".sample", ".schema.json", ".template")) and not norm.startswith(("docs/", "wiki/", "metrics/", "skeletons/", "templates/", "doc_samples/")) and norm != "scripts/harness_guard.py":
        for pattern, label in SECRET_PATTERNS:
            for idx, line in enumerate(lines, 1):
                if pattern.search(line) and not line.strip().startswith("#"):
                    violations.append(Violation("HG-007", "BLOCK", norm, f"平文シークレット/未置換プレースホルダー検出 ({label})", line_no=idx,
                                                hint="環境変数 (.env) または Pydantic Settings へ外出ししてください。"))

    # HG-008 (PAT-DOC-003): Mermaid bracketed unquoted label check
    if norm.endswith(".md") and not norm.startswith(("docs/設計書/v", "docs/設計書/V", "docs/検討課題/")):
        in_mermaid = False
        for idx, line in enumerate(lines, 1):
            if line.strip().startswith("```mermaid"):
                in_mermaid = True
                continue
            elif in_mermaid and line.strip().startswith("```"):
                in_mermaid = False
                continue
            if in_mermaid:
                m = MERMAID_UNQUOTED_BRACKET_LABEL.search(line)
                if m:
                    violations.append(Violation("HG-008", "BLOCK", norm, f"Mermaid矢印ラベル内の特殊記号・括弧がダブルクォートされていません: |{m.group(1)}|", line_no=idx,
                                                hint='矢印ラベル全体をダブルクォートで囲んでください (例: -->|"ラベル (補足)"|)。'))

    # HG-009 (PAT-DOC-002): Document hygiene & versioning invariants
    if norm.startswith("docs/設計書/") and norm.endswith(".md") and norm.count("/") == 2:
        violations.append(Violation("HG-009", "BLOCK", norm, "docs/設計書/ 直下に未整理の仕様書・設計書が放置されています",
                                    hint="docs/設計書/Current/ またはバージョン別退避ディレクトリ (docs/設計書/v* 等) へ整理・移動してください。"))

    if norm.startswith("docs/設計書/Current/"):
        fname = Path(norm).name
        fname_lower = fname.lower()
        if re.search(r"(_v\d+(\.\d+)*|-v\d+(\.\d+)*|\bv\d+(\.\d+)*)\.md$", fname_lower):
            violations.append(Violation("HG-009", "BLOCK", norm, f"正本設計書ファイル名に個別バージョン番号が含まれています: {fname}",
                                        hint="正本設計書ファイル名から個別バージョン番号を排除し、SemVer (APP_VERSION) で一元管理してください (例: 要件定義書.md)。"))
        if fname_lower.endswith((".bak", ".tmp", ".swp")) or "draft" in fname_lower:
            violations.append(Violation("HG-009", "BLOCK", norm, f"正本設計書ディレクトリ内に一時ファイル・下書きが残存しています: {fname}",
                                        hint="docs/検討課題/ へ移動するか、不要な一時ファイルを削除してください。"))

        if norm.endswith(".md"):
            for idx, line in enumerate(lines[:10], 1):
                if DOC_TITLE_VERSION_PATTERN.search(line):
                    violations.append(Violation("HG-009", "BLOCK", norm, f"正本設計書タイトルに個別バージョン番号が含まれています: {line.strip()}", line_no=idx,
                                                hint="正本設計書タイトルから個別バージョン番号を排除し、システム SemVer (APP_VERSION) で一元管理してください。"))

    # HG-010: Anti-Placeholder & empty JSX handlers (FE/BE common)
    if not is_test and not is_gen and not norm.startswith(("docs/", "wiki/", "metrics/", "skeletons/", "templates/", "doc_samples/")) and norm != "scripts/harness_guard.py":
        for idx, line in enumerate(lines, 1):
            if EMPTY_JSX_HANDLER.search(line):
                violations.append(Violation("HG-010", "BLOCK", norm, f"空JSXイベントハンドラ直書きを検出: {line.strip()}", line_no=idx,
                                            hint="イベント処理ロジックを実装するか、明示的な状態更新関数を呼び出してください。"))
            if DUMMY_GEN_COMMENT.search(line):
                violations.append(Violation("HG-010", "BLOCK", norm, f"ダミー・プレースホルダー生成コメントを検出: {line.strip()}", line_no=idx,
                                            hint="プレースホルダー文字列返却を排除し、実ビジネスロジックによる生成処理を実装してください。"))

    return violations

def check_ast_fitness(norm: str, content: str) -> list[Violation]:
    violations = []
    try:
        tree = ast.parse(content, filename=norm)
    except SyntaxError:
        return violations

    is_router = any(k in norm for k in ["/routers/", "/api/"]) or norm.startswith(("backend/app/routers", "backend/app/api", "backend/routers", "backend/api"))
    dto_count = 0

    for node in ast.walk(tree):
        # レイヤーバイパス: routers から models 直接参照
        if is_router:
            if isinstance(node, ast.ImportFrom):
                if node.module and ("models" in node.module.split(".") or node.module.endswith("models")):
                    violations.append(Violation("HG-005", "BLOCK", norm, "レイヤーバイパス: router から models への直接import",
                                                line_no=node.lineno, hint="services 層経由でアクセスしてください。"))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "models" in alias.name.split("."):
                        violations.append(Violation("HG-005", "BLOCK", norm, "レイヤーバイパス: router から models への直接import",
                                                    line_no=node.lineno, hint="services 層経由でアクセスしてください。"))
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if (isinstance(base, ast.Name) and "BaseModel" in base.id) or \
                       (isinstance(base, ast.Attribute) and "BaseModel" in base.attr):
                        dto_count += 1

        # 例外握りつぶし / サイレントモックフォールバック
        if isinstance(node, ast.ExceptHandler):
            is_pass = len(node.body) == 1 and (
                isinstance(node.body[0], ast.Pass) or
                (isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant) and node.body[0].value.value is Ellipsis)
            )
            if is_pass:
                violations.append(Violation("HG-005", "BLOCK", norm, "例外握りつぶし (except: pass / ...) を検出",
                                            line_no=node.lineno, hint="例外型を限定し、ログ記録または適切な例外再送出を行ってください。"))

            # HG-002: Python サイレントモックフォールバック検知 (except 節内での mock/dummy 返却)
            for stmt in node.body:
                if isinstance(stmt, ast.Return) and stmt.value:
                    val_str = ast.unparse(stmt.value) if hasattr(ast, "unparse") else ""
                    if re.search(r"\b(mock|dummy|MOCK_)", val_str, re.IGNORECASE):
                        violations.append(Violation("HG-002", "BLOCK", norm, f"Pythonサイレントモックフォールバックを検出 (except節内でモック/ダミー返却: {val_str})",
                                                    line_no=stmt.lineno, hint="Fail-Fast原則に従い、本番通信・処理エラー時は例外を即スローしてください。"))

    if is_router and dto_count > 2:
        violations.append(Violation("HG-005", "BLOCK", norm, f"DTO過多 ({dto_count}個): router内にBaseModelが直書き定義されています",
                                    hint="schemas/ などの独立モジュールへDTOを物理分離してください。"))

    # HG-010: Python AST empty function / placeholder detection
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_abstract = any(
                (isinstance(d, ast.Name) and d.id in ("abstractmethod", "overload")) or
                (isinstance(d, ast.Attribute) and d.attr in ("abstractmethod", "overload"))
                for d in node.decorator_list
            )
            if not is_abstract:
                body = [n for n in node.body if not (isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant) and isinstance(n.value.value, str))]
                if len(body) == 1:
                    stmt = body[0]
                    is_empty = False
                    if isinstance(stmt, ast.Pass):
                        is_empty = True
                    elif isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, "value", None), ast.Constant) and stmt.value.value is Ellipsis:
                        is_empty = True
                    elif isinstance(stmt, ast.Raise):
                        if isinstance(stmt.exc, ast.Call) and isinstance(stmt.exc.func, ast.Name) and stmt.exc.func.id == "NotImplementedError":
                            is_empty = True
                        elif isinstance(stmt.exc, ast.Name) and stmt.exc.id == "NotImplementedError":
                            is_empty = True
                    if is_empty:
                        violations.append(Violation("HG-010", "BLOCK", norm, f"明白な空実装・未実装関数を検出 ({node.name}: pass / ... / NotImplementedError)",
                                                    line_no=node.lineno, hint="機能オミット・縮退実装を排除し、実ロジックを実装してください。"))

    return violations

SYSTEM_CODE_PREFIXES = ("backend/", "frontend/", "src/", "src-tauri/", "docs/設計書/Current/")

def check_scope_guard(root: Path, target_files: list[str]) -> list[Violation]:
    """HG-011 / PAT-SYS-016: 非開発モード・改訂未起票時のシステム本体コード変更遮断"""
    state_file = root / "project_state.json"
    if not state_file.is_file():
        return []

    try:
        s = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return []

    meta = s.get("project_metadata", {})
    session_mode = meta.get("session_mode", "DEV_PIPELINE")
    current_status = s.get("current_status", "")
    rev = s.get("revisions", {})
    rev_status = rev.get("current_revision_status", "IDLE")

    is_production_idle = (current_status == "PRODUCTION_ACTIVE" and rev_status == "IDLE")
    is_content_mode = (session_mode == "CONTENT_PRODUCTION" and rev_status == "IDLE")

    if not (is_production_idle or is_content_mode):
        return []

    violations = []
    for f in target_files:
        norm = f.replace("\\", "/")
        if any(norm.startswith(prefix) for prefix in SYSTEM_CODE_PREFIXES):
            violations.append(Violation(
                "HG-011", "BLOCK", norm,
                "Scope Guard Violation: 非開発モードまたは改訂未起票状態でのシステム本体コード改変を検出しました",
                hint="python3 scripts/state_manager.py start-revision --id <ID> を実行してシステム改訂パイプラインへ自律昇格してください。"
            ))
    return violations

def enforce_dual_provisioning(root: Path):
    """PAT-ENV-001: Ensure .env exists if .env.example exists (Self-Healing)."""
    env_example = root / ".env.example"
    env_file = root / ".env"
    if env_example.is_file() and not env_file.exists():
        try:
            shutil.copy(env_example, env_file)
            print("🔧 [HARNESS GUARD Self-Healing] .env.example から .env を自動生成補完しました (Dual Provisioning).")
        except Exception as e:
            print(f"⚠️ [HARNESS GUARD] .env の自動生成補完に失敗しました: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="AI Harness Hard Gate Static Enforcement Engine")
    parser.add_argument("--all", action="store_true", help="Scan entire workspace")
    parser.add_argument("--staged", action="store_true", help="Scan git staged files only")
    parser.add_argument("--json-out", type=str, help="Output report to JSON file")
    args = parser.parse_args()

    root = Path.cwd()

    # PAT-ENV-001: Self-healing dual provisioning check
    enforce_dual_provisioning(root)

    if args.staged:
        files = get_git_staged_files()
    else:
        files = collect_all_files(root)

    all_violations: list[Violation] = []
    # HG-011: Path-based Scope Guard check
    all_violations.extend(check_scope_guard(root, files))

    for rel in files:
        full = root / rel
        if full.is_file():
            all_violations.extend(check_file(rel, full))

    block_violations = [v for v in all_violations if v.severity == "BLOCK"]
    warn_violations = [v for v in all_violations if v.severity == "WARN"]

    if args.json_out:
        out_p = Path(args.json_out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "summary": {"total": len(all_violations), "block": len(block_violations), "warn": len(warn_violations)},
            "violations": [v.to_dict() for v in all_violations]
        }
        out_p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if not all_violations:
        print("✅ [HARNESS GUARD] 規約違反は検出されませんでした (All Invariants Passed).")
        sys.exit(0)

    if warn_violations and not block_violations:
        print(f"⚠️ [HARNESS GUARD WARN] {len(warn_violations)} 件の警告があります (Phase 5で実測検証):")
        for w in warn_violations[:5]:
            print(f"  [{w.rule_id}] {w.file_path}:{w.line_no} - {w.message}")
        sys.exit(0)

    print(f"\n🚨 [HARNESS GUARD BLOCKED] {len(block_violations)} 件のアーキテクチャ規約違反を検出しました:", file=sys.stderr)
    print("-" * 80, file=sys.stderr)
    for v in block_violations:
        loc = f"{v.file_path}:{v.line_no}" if v.line_no else v.file_path
        print(f"[{v.rule_id}] {v.message}", file=sys.stderr)
        print(f"  - ファイル: {loc}", file=sys.stderr)
        if v.hint:
            print(f"  - 対処指示: {v.hint}", file=sys.stderr)
        print("-" * 80, file=sys.stderr)

    sys.exit(1)

if __name__ == "__main__":
    main()
