"""
test_v310_pipeline.py - Pipeline v3.1.0 Invariant & Functional Verification Suite
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ["DEBUG"] = "true"
sys.path.insert(0, str(ROOT / ".agents" / "plugins" / "system-dev-pipeline" / "scripts"))
from state_manager import run_live_invariant_probe

def test_req_f_310_01_live_probe_skip_when_no_backend():
    """[REQ-F-310-01] バックエンドが存在しない環境ではLive Probeが安全にスキップされること"""
    with tempfile.TemporaryDirectory() as tmpdir:
        violations = run_live_invariant_probe(Path(tmpdir))
        assert violations == []

def test_req_f_310_01_live_probe_abnormal_immediate_crash():
    """[REQ-F-310-01] @test_type: negative バックエンド起動時クラッシュが検知・遮断されること"""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        b_dir = p / "backend" / "app"
        b_dir.mkdir(parents=True)
        (b_dir / "main.py").write_text("raise RuntimeError('DB Path Operational Error')", encoding="utf-8")
        violations = run_live_invariant_probe(p)
        assert len(violations) >= 1
        assert "[READINESS-PROBE]" in violations[0]

def test_req_f_310_02_smart_resolver_fallback_and_mkdir():
    """[REQ-F-310-02] コンテナ絶対パス不在時にローカルdata/へフォールバックし親ディレクトリを作成すること"""
    sys.path.insert(0, str(ROOT / ".agents" / "plugins" / "system-dev-pipeline" / "skeletons" / "profile-a" / "backend"))
    from core.config import Settings
    s = Settings(DATABASE_URL="sqlite:////app/data/test_v310.db", DEBUG=True, IAP_AUDIENCE="test")
    resolved = s.resolved_database_url
    assert "data/test_v310.db" in resolved
    assert Path("data").is_dir()

def test_req_f_310_02_smart_resolver_abnormal_validation():
    """[REQ-F-310-02] @test_type: negative 本番環境でのプレースホルダーまたは未設定IAP設定の拒否"""
    sys.path.insert(0, str(ROOT / ".agents" / "plugins" / "system-dev-pipeline" / "skeletons" / "profile-a" / "backend"))
    from core.config import Settings
    try:
        # 本番モード (DEBUG=False, IAP_AUDIENCE="") の検証
        Settings(DEBUG=False, IAP_AUDIENCE="", _env_file=None)
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "FATAL" in str(e) or "IAP_AUDIENCE" in str(e)

def test_req_f_310_03_three_stage_architecture_rule():
    """[REQ-F-310-03] 規約文書およびテンプレートに3ステージ体系が正しく反映されていること"""
    agents_rule = (ROOT / ".agents" / "plugins" / "system-dev-pipeline" / "rules" / "AGENTS.md").read_text(encoding="utf-8")
    assert "3ステージテスト体系" in agents_rule
    assert "Stage 1 (Unit & Contract)" in agents_rule
    assert "Stage 2 (Readiness Live Probe)" in agents_rule
    assert "Stage 3 (Full-Stack E2E & Sensorial)" in agents_rule

def test_req_f_310_03_abnormal_rejection_of_invalid_stages():
    """[REQ-F-310-03] @test_type: negative 細分化された旧ステージの残存拒否検証"""
    agents_rule = (ROOT / ".agents" / "plugins" / "system-dev-pipeline" / "rules" / "AGENTS.md").read_text(encoding="utf-8")
    # 旧表記 "Dual-Stage Testing Gate" が本文から排除されていること
    assert "Dual-Stage Testing Gate" not in agents_rule
