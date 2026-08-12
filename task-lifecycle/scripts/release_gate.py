# Retained-capability release gate. Supported platforms: macOS, Linux, Windows (pure pathlib + sys.executable, no shell).
# if/elif rather than match/case: these scripts must run on the system Python 3.9 that ships with macOS.
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_text import in_force_text

# Raise this whenever a capability is added: the floor is what stops the last entry being quietly dropped.
MINIMUM_CAPABILITIES = 36
REQUIRED_CHECK_KEYS = {"script": ["script", "args", "negative_control", "negative_control_fixture", "negative_control_diagnostic"], "contains": ["file", "patterns"], "section": ["file", "section", "patterns"], "absent": ["files", "patterns"], "absent_tree": ["root", "suffixes", "exclude", "patterns"], "repo_script": ["path", "args", "negative_control", "negative_control_fixture", "negative_control_diagnostic"], "missing": ["path"]}

skill_root = Path(__file__).resolve().parent.parent
repo_root = skill_root.parent
catalog_path = skill_root / "assets" / "retained-capability-catalog.json"

if not (repo_root / "PORTING.md").is_file():
    print(f"RELEASE GATE: BLOCKED — {repo_root} is not the qin-claude-skills source checkout; run the gate from the repository root")
    sys.exit(3)

try:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
except (OSError, ValueError) as error:
    print(f"RELEASE GATE: FAIL — cannot read assets/retained-capability-catalog.json: {error}")
    sys.exit(1)


# The catalog is the gate's own authority, so it is validated before it is trusted: a gutted catalog must never read as "nothing to check".
def catalog_shape_error(loaded_catalog):
    if not isinstance(loaded_catalog, dict):
        return "the catalog must be a JSON object"
    if not isinstance(loaded_catalog.get("capabilities"), list) or not isinstance(loaded_catalog.get("retired_architectures"), list):
        return "capabilities and retired_architectures must both be lists"
    if any(not isinstance(entry, dict) for entry in loaded_catalog["capabilities"]):
        return "every capability must be a JSON object"
    capability_ids = [entry.get("id") if isinstance(entry, dict) else entry for entry in loaded_catalog["capabilities"]]
    if len(capability_ids) < MINIMUM_CAPABILITIES or capability_ids != list(range(1, len(capability_ids) + 1)):
        return f"the catalog must define at least {MINIMUM_CAPABILITIES} capabilities numbered 1..n; found {len(capability_ids)} with ids {capability_ids}"
    for entry in loaded_catalog["capabilities"]:
        if not isinstance(entry.get("capability"), str) or not entry["capability"].strip():
            return f"capability {entry.get('id')} must carry a non-empty capability description"
        if not isinstance(entry.get("checks"), list) or not entry["checks"]:
            return f"capability {entry.get('id')} must carry a non-empty checks list; a capability with no checks proves nothing"
        for check in entry["checks"]:
            if not isinstance(check, dict) or check.get("kind") not in REQUIRED_CHECK_KEYS:
                return f"capability {entry.get('id')} has a check with an unknown kind {check.get('kind') if isinstance(check, dict) else check}"
            if any(key not in check for key in REQUIRED_CHECK_KEYS[check["kind"]]):
                return f"capability {entry.get('id')} has a {check['kind']} check missing one of {REQUIRED_CHECK_KEYS[check['kind']]}"
            # An empty or one-character anchor asserts nothing, so a check reduced to one cannot count as retained.
            if "patterns" in check and (not isinstance(check["patterns"], list) or not check["patterns"] or any(not isinstance(pattern, str) or len(pattern) < 4 for pattern in check["patterns"])):
                return f"capability {entry.get('id')} has a {check['kind']} check whose patterns are empty or shorter than 4 characters"
            if check["kind"] == "absent" and (not isinstance(check["files"], list) or not check["files"]):
                return f"capability {entry.get('id')} has an absent check scanning no files"
    return ""


shape_error = catalog_shape_error(catalog)
if shape_error:
    print(f"RELEASE GATE: FAIL — {shape_error}")
    sys.exit(1)


def contract_text(relative_path):
    return in_force_text(repo_root / relative_path)


def run_gate_script(script_name, raw_arguments, fixture_root="", repo_relative=False):
    arguments = [argument.replace("{repo_root}", str(repo_root)).replace("{skill_root}", str(skill_root)).replace("{fixture_root}", fixture_root) for argument in raw_arguments]
    script_path = repo_root / script_name if repo_relative else skill_root / "scripts" / script_name
    return subprocess.run([sys.executable, str(script_path), *arguments], capture_output=True, text=True, cwd=str(repo_root))


# A stub that exits 0 on everything satisfies any "did it pass?" test, so every checker must also REJECT a synthetic
# known-bad input. The fixture is written to a temp dir so the known-bad file never lives in the scanned repo.
def negative_control_result(check):
    with tempfile.TemporaryDirectory() as fixture_directory:
        for relative_name, content in check["negative_control_fixture"].items():
            fixture_file = Path(fixture_directory).joinpath(*relative_name.split("/"))
            fixture_file.parent.mkdir(parents=True, exist_ok=True)
            fixture_file.write_text(content, encoding="utf-8")
        control = run_gate_script(check.get("script") or check["path"], check["negative_control"], fixture_directory, repo_relative="path" in check)
        # The control must both reject the fixture AND explain why: an exit code alone is reproducible by a stub that
        # only sniffs argv, whereas the diagnostic text can only come from the checker actually inspecting the fixture.
        return control.returncode != 0 and bool(re.search(check["negative_control_diagnostic"], control.stdout + control.stderr)), f"exit={control.returncode}"


def run_retained_check(check):
    if check["kind"] in ("script", "repo_script"):
        repo_relative = check["kind"] == "repo_script"
        completed = run_gate_script(check.get("script") or check["path"], check["args"], repo_relative=repo_relative)
        control_rejected, control_detail = negative_control_result(check)
        return completed.returncode == 0 and control_rejected, f"{check.get('script') or check['path']} exit={completed.returncode}, negative control {control_detail}{'' if control_rejected else ' — the checker did not reject the known-bad fixture with its own diagnostic, so it proves nothing'}"
    if check["kind"] == "contains":
        if not (repo_root / check["file"]).is_file():
            return False, f"{check['file']} is missing"
        missing_patterns = [pattern for pattern in check["patterns"] if not re.search(pattern, contract_text(check["file"]))]
        return not missing_patterns, f"{check['file']} missing {missing_patterns}" if missing_patterns else f"{check['file']} carries {len(check['patterns'])} retained rules"
    if check["kind"] == "section":
        if not (repo_root / check["file"]).is_file():
            return False, f"{check['file']} is missing"
        section_bodies = re.findall(rf"^## {re.escape(check['section'])}[ \t]*$(.*?)(?=^## |\Z)", contract_text(check["file"]), re.MULTILINE | re.DOTALL)
        if len(section_bodies) != 1:
            return False, f"{check['file']} must have exactly one section headed exactly '## {check['section']}', found {len(section_bodies)}"
        missing_patterns = [pattern for pattern in check["patterns"] if not re.search(pattern, section_bodies[0])]
        return not missing_patterns, f"{check['file']} section '{check['section']}' missing {missing_patterns}" if missing_patterns else f"{check['file']} section '{check['section']}' carries {len(check['patterns'])} retained rules"
    if check["kind"] == "absent":
        unreadable_files = [scanned_file for scanned_file in check["files"] if not (repo_root / scanned_file).is_file()]
        if unreadable_files:
            return False, f"cannot scan missing files {unreadable_files}"
        retired_hits = [f"{scanned_file} :: {pattern}" for scanned_file in check["files"] for pattern in check["patterns"] if re.search(pattern, contract_text(scanned_file), re.IGNORECASE)]
        return not retired_hits, f"retired content present in {retired_hits}" if retired_hits else f"{len(check['files'])} active files free of {len(check['patterns'])} retired markers"
    if check["kind"] == "absent_tree":
        scanned_files = [path for path in sorted((repo_root / check["root"]).rglob("*")) if path.is_file() and path.suffix in check["suffixes"] and not set(check["exclude"]) & set(path.relative_to(repo_root).parts) and ".git" not in path.parts]
        foreign_hits = [f"{path.relative_to(repo_root)} :: {pattern}" for path in scanned_files for pattern in check["patterns"] if re.search(pattern, in_force_text(path), re.IGNORECASE)]
        return not foreign_hits, f"foreign model identifiers present in {foreign_hits}" if foreign_hits else f"{len(scanned_files)} files free of {len(check['patterns'])} foreign model identifiers"
    path_exists = (repo_root / check["path"]).exists()
    return not path_exists, f"{check['path']} must not exist in the repo" if path_exists else f"{check['path']} correctly absent"


# One error boundary for every check: an unreadable, unparsable or malformed target becomes a reported FAIL for that
# capability instead of a traceback that abandons the remaining ones half-checked.
def safe_run_retained_check(check):
    try:
        return run_retained_check(check)
    except Exception as error:
        return False, f"{check.get('kind')} check on {check.get('file') or check.get('script') or check.get('path')} raised {type(error).__name__}: {error}"


executed_checks, passed_checks, retained_capabilities = 0, 0, 0
print(f"RETAINED-CAPABILITY GATE — {len(catalog['capabilities'])} capabilities, {len(catalog['retired_architectures'])} retired architectures")
for entry in catalog["capabilities"]:
    check_results = [safe_run_retained_check(check) for check in entry["checks"]]
    entry_passed_checks = sum(1 for passed, _ in check_results if passed)
    executed_checks, passed_checks = executed_checks + len(check_results), passed_checks + entry_passed_checks
    retained_capabilities += 1 if entry_passed_checks == len(check_results) else 0
    print(f"{entry['id']:>2}. {'PASS' if entry_passed_checks == len(check_results) else 'FAIL'} [{entry_passed_checks}/{len(check_results)}] {entry['capability']}")
    for passed, detail in check_results:
        if not passed:
            print(f"      - {detail}")

gate_passed = retained_capabilities == len(catalog["capabilities"])
print(f"RELEASE GATE: {'PASS' if gate_passed else 'FAIL'} — {passed_checks}/{executed_checks} checks passed, {retained_capabilities}/{len(catalog['capabilities'])} capabilities retained")
sys.exit(0 if gate_passed else 1)
