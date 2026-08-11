# One-command health check. Supported platforms: macOS, Linux, Windows (pure pathlib + sys.executable, no shell).
import subprocess
import sys
from pathlib import Path

skill_root = Path(__file__).resolve().parent.parent
scripts_root = skill_root / "scripts"
check_only = "--check-only" in sys.argv


def run_script(script_name, *arguments):
    return subprocess.run([sys.executable, str(scripts_root / script_name), *arguments], capture_output=True, text=True)


gate = run_script("release_gate.py")
gate_output = (gate.stdout + gate.stderr).strip()
gate_ok = gate.returncode == 0 and bool(gate_output)
print(gate_output or f"release_gate.py produced no output (exit {gate.returncode}) — a gate that reports nothing cannot prove anything")

# sync_check exits 0 SAME/SKIPPED and 2 DRIFTED; DRIFTED is informational, anything else means the check itself broke.
style_sync = run_script("sync_check.py")
style_sync_ok = style_sync.returncode in (0, 2)
print(f"style-sync: {(style_sync.stdout or style_sync.stderr).strip() or 'no output'}{'' if style_sync_ok else f' [CHECK BROKEN exit={style_sync.returncode}]'}")

mirror = run_script("deploy_local.py", "--check")
mirror_ok = mirror.returncode == 0
mirror_summary = next((line for line in mirror.stdout.splitlines() if line.startswith(("CHECK:", "DEPLOYED:"))), "not checked — the release gate did not pass, so the mirror was never compared")
repaired = False
if mirror.returncode == 2 and gate_ok and not check_only:
    print("mirror: STALE — repairing from source")
    repair = run_script("deploy_local.py")
    print((repair.stdout + repair.stderr).strip())
    recheck = run_script("deploy_local.py", "--check")
    mirror_ok = recheck.returncode == 0
    repaired = mirror_ok
    mirror_summary = next((line for line in recheck.stdout.splitlines() if line.startswith(("CHECK:", "DEPLOYED:"))), mirror_summary)
mirror_state = "PASS" if mirror_ok else ("STALE (run without --check-only to repair)" if check_only and mirror.returncode == 2 else "NOT CHECKED" if not gate_ok else "FAIL")
print(f"mirror: {mirror_state}{' (repaired)' if repaired else ''} — {mirror_summary}")

healthy = gate_ok and style_sync_ok and mirror_ok
if gate.returncode == 3:
    print("SELF-CHECK: BLOCKED — run this from the qin-claude-skills source repository, not from the deployed mirror")
    sys.exit(1)
repo_broken_hint = " — a broken repo is repaired through the SKILL.md section 5 fix loop, not by this script" if not gate_ok else ""
print(f"SELF-CHECK: {'PASS' if healthy else 'FAIL' + repo_broken_hint}")
sys.exit(0 if healthy else 1)
