# Idea-parity benchmark: qin-claude-skills task-lifecycle vs qin-codex-skills.
# Supported platforms: macOS, Linux, Windows (pure pathlib + PATH-resolved git, no shell).
# if/elif rather than match/case: these scripts must run on the system Python 3.9 that ships with macOS.
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_text import in_force_text

skill_root = Path(__file__).resolve().parent.parent
repo_root = skill_root.parent
benchmark_path = skill_root / "assets" / "idea-parity-benchmark.json"

MINIMUM_IDEAS = 75
MAXIMUM_CLAUDE_SIDE_INVENTIONS = 2

parser = argparse.ArgumentParser(description="Score how completely the Claude task-lifecycle skill carries the qin-codex-skills lifecycle ideas.")
parser.add_argument("--upstream", help="path to a qin-codex-skills clone; defaults to Cache/Tools/qin-codex-skills, cloning it when absent")
parser.add_argument("--json", action="store_true", help="emit the machine-readable result instead of the human report")
parser.add_argument("--validate-only", action="store_true", help="check the benchmark's own shape offline and exit; no upstream clone needed")
parser.add_argument("--benchmark-file", help="score a different benchmark file; the release gate uses it to feed this validator a known-bad one")
arguments = parser.parse_args()

benchmark_path = Path(arguments.benchmark_file).expanduser().resolve() if arguments.benchmark_file else benchmark_path
try:
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
except (OSError, ValueError) as error:
    print(f"IDEA PARITY: BLOCKED — cannot read {benchmark_path.name}: {error}")
    sys.exit(3)


# The benchmark is its own authority, so it is validated before it is trusted: an emptied or gutted idea list must never
# read as "everything is ported", and an anchor like "." would prove only that a file is non-empty.
def benchmark_shape_error(loaded_benchmark):
    if not isinstance(loaded_benchmark, dict) or not isinstance(loaded_benchmark.get("ideas"), list):
        return "the benchmark must be a JSON object with an ideas list"
    if any(not isinstance(idea, dict) for idea in loaded_benchmark["ideas"]):
        return "every idea must be a JSON object"
    idea_ids = [idea.get("id") for idea in loaded_benchmark["ideas"]]
    if len(idea_ids) < MINIMUM_IDEAS or idea_ids != list(range(1, len(idea_ids) + 1)):
        return f"the benchmark must list at least {MINIMUM_IDEAS} ideas numbered 1..n; found {len(idea_ids)} with ids {idea_ids}"
    if not isinstance(loaded_benchmark.get("upstream_repo"), str) or not loaded_benchmark["upstream_repo"].startswith("http"):
        return "the benchmark must name the upstream_repo it compares against"
    if sum(1 for idea in loaded_benchmark["ideas"] if idea.get("upstream_evidence") is None) > MAXIMUM_CLAUDE_SIDE_INVENTIONS:
        return f"at most {MAXIMUM_CLAUDE_SIDE_INVENTIONS} ideas may skip the upstream side; the rest must be anchored on both"
    for idea in loaded_benchmark["ideas"]:
        if idea.get("status") not in ("ported", "inverted", "retired") or "upstream_evidence" not in idea or not isinstance(idea.get("claude_evidence"), dict):
            return f"idea {idea.get('id')} needs a status of ported/inverted/retired, an upstream_evidence key, and a claude_evidence object"
        evidence_blocks = [block for block in (idea["upstream_evidence"], idea["claude_evidence"]) if isinstance(block, dict)]
        if any(not block.get("patterns") or any(len(pattern) < 4 for pattern in block["patterns"]) for block in evidence_blocks):
            return f"idea {idea.get('id')} has an empty or over-broad anchor; every pattern must be a real phrase, not a wildcard"
        if any("file" not in block and "files" not in block for block in evidence_blocks):
            return f"idea {idea.get('id')} has an evidence block naming no file"
        if idea["status"] != "retired" and "file" not in idea["claude_evidence"]:
            return f"idea {idea.get('id')} is {idea['status']}, so its claude_evidence must name a single file"
    return ""


shape_error = benchmark_shape_error(benchmark)
if shape_error:
    print(f"IDEA PARITY: FAIL — {shape_error}")
    sys.exit(1)
if arguments.validate_only:
    print(f"IDEA PARITY: benchmark shape valid — {len(benchmark['ideas'])} ideas, {sum(1 for idea in benchmark['ideas'] if idea['upstream_evidence'] is not None)} anchored on both sides")
    sys.exit(0)


# An explicit --upstream must be a real git work tree: otherwise `git -C` walks up the tree and reports an unrelated repo's HEAD as upstream.
def resolve_upstream_clone(explicit_path):
    if explicit_path:
        explicit_clone = Path(explicit_path).expanduser().resolve()
        return (explicit_clone, "") if (explicit_clone / ".git").exists() else (None, f"{explicit_clone} is not a git clone of {benchmark['upstream_repo']}")
    cached_clone = repo_root / "Cache" / "Tools" / "qin-codex-skills"
    if (cached_clone / ".git").is_dir():
        return cached_clone, ""
    git_executable = shutil.which("git")
    if git_executable is None:
        return None, "git is not on PATH; pass --upstream <path to a qin-codex-skills clone>"
    cached_clone.parent.mkdir(parents=True, exist_ok=True)
    clone = subprocess.run([git_executable, "clone", "--quiet", benchmark["upstream_repo"], str(cached_clone)], capture_output=True, text=True)
    return (cached_clone, "") if clone.returncode == 0 else (None, f"cloning {benchmark['upstream_repo']} failed: {(clone.stderr or clone.stdout).strip()}")


def evidence_present(root, evidence):
    target = root / evidence["file"]
    if not target.is_file():
        return False, f"{evidence['file']} not found"
    missing_patterns = [pattern for pattern in evidence["patterns"] if not re.search(pattern, in_force_text(target), re.MULTILINE)]
    return not missing_patterns, f"{evidence['file']} missing {missing_patterns}" if missing_patterns else evidence["file"]


def evidence_absent(root, evidence):
    unreadable_files = [scanned_file for scanned_file in evidence["files"] if not (root / scanned_file).is_file()]
    if unreadable_files:
        return False, f"cannot scan missing files {unreadable_files}"
    leaks = [f"{scanned_file} :: {pattern}" for scanned_file in evidence["files"] for pattern in evidence["patterns"] if re.search(pattern, in_force_text(root / scanned_file), re.IGNORECASE)]
    return not leaks, f"leaked into {leaks}" if leaks else f"{len(evidence['files'])} active files clean"


upstream_root, resolve_error = resolve_upstream_clone(arguments.upstream)
if upstream_root is None:
    print(f"IDEA PARITY: BLOCKED — {resolve_error}")
    sys.exit(3)

git_executable = shutil.which("git")
upstream_head = subprocess.run([git_executable, "-C", str(upstream_root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() if git_executable else ""
try:
    stamped_commit = json.loads((skill_root / "references" / "UPSTREAM.json").read_text(encoding="utf-8")).get("commit", "unstamped")
except (OSError, ValueError):
    stamped_commit = "unreadable"

# 'ported' and 'inverted' both assert Claude-side text; 'inverted' marks an idea this repo deliberately does the OPPOSITE of
# and must say so out loud, which is why it is not modelled as plain absence.
verdict_when_satisfied = {"ported": "PORTED", "inverted": "INVERTED", "retired": "RETIRED"}
results = []
for idea in benchmark["ideas"]:
    upstream_ok, upstream_detail = (True, "n/a (Claude-side invention)") if idea["upstream_evidence"] is None else evidence_present(upstream_root, idea["upstream_evidence"])
    claude_ok, claude_detail = evidence_absent(repo_root, idea["claude_evidence"]) if idea["status"] == "retired" else evidence_present(repo_root, idea["claude_evidence"])
    unsatisfied_verdict = "LEAKED" if idea["status"] == "retired" else "MISSING"
    verdict = "STALE" if not upstream_ok else (verdict_when_satisfied[idea["status"]] if claude_ok else unsatisfied_verdict)
    results.append({"id": idea["id"], "idea": idea["idea"], "status": idea["status"], "verdict": verdict, "upstream": upstream_detail, "claude": claude_detail})

status_totals = {status: sum(1 for idea in benchmark["ideas"] if idea["status"] == status) for status in verdict_when_satisfied}
ported_ok, inverted_ok, retired_ok = (sum(1 for result in results if result["verdict"] == verdict) for verdict in ("PORTED", "INVERTED", "RETIRED"))
stale_anchors = sum(1 for result in results if result["verdict"] == "STALE")
parity_passed = ported_ok == status_totals["ported"] and inverted_ok == status_totals["inverted"] and retired_ok == status_totals["retired"] and stale_anchors == 0
coverage_percent = round(100.0 * (ported_ok + inverted_ok) / (status_totals["ported"] + status_totals["inverted"]), 1) if status_totals["ported"] + status_totals["inverted"] else 0.0

if arguments.json:
    print(json.dumps({"upstream_repo": benchmark["upstream_repo"], "upstream_head": upstream_head, "stamped_commit": stamped_commit, "ported": f"{ported_ok}/{status_totals['ported']}", "inverted": f"{inverted_ok}/{status_totals['inverted']}", "coverage_percent": coverage_percent, "retired_contained": f"{retired_ok}/{status_totals['retired']}", "stale_anchors": stale_anchors, "passed": parity_passed, "results": results}, indent=2))
    sys.exit(0 if parity_passed else 1)

print(f"IDEA-PARITY BENCHMARK — qin-claude-skills task-lifecycle vs {benchmark['upstream_repo']}")
print(f"upstream clone: {upstream_root} @ {upstream_head[:12] or 'unknown'} · stamped in UPSTREAM.json: {stamped_commit[:12]} · {'MATCHED' if upstream_head == stamped_commit else 'AHEAD OF STAMP (re-port before trusting a 100% score)'}")
print(f"{'':4}{'VERDICT':<9}IDEA")
for result in results:
    print(f"{result['id']:>3} {result['verdict']:<9}{result['idea']}")
    if result["verdict"] in ("STALE", "MISSING", "LEAKED"):
        print(f"      upstream: {result['upstream']}")
        print(f"      claude:   {result['claude']}")
print(f"SCORE: ported {ported_ok}/{status_totals['ported']} · deliberately inverted {inverted_ok}/{status_totals['inverted']} · idea coverage {coverage_percent}% · retired {retired_ok}/{status_totals['retired']} contained · stale upstream anchors {stale_anchors}")
print(f"IDEA PARITY: {'PASS' if parity_passed else 'FAIL'}")
sys.exit(0 if parity_passed else 1)
