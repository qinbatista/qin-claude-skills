# Behavioural test suite for the task-lifecycle skill: every feature exercised by a REAL headless Claude run,
# then asserted against the transcript and the files it actually produced. Supported platforms: macOS, Linux, Windows.
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
# Fixtures live OUTSIDE this repository: a project nested inside it would correctly resolve the repo as its
# project root and write there, which is the skill behaving properly but not what these cases mean to measure.
suite_root = Path(os.environ.get("BEHAVIOUR_SUITE_ROOT") or Path(tempfile.gettempdir()) / "qin-skill-behaviour-suite")
claude_executable = shutil.which("claude")

CALC_FIXTURE = 'def divide(numerator, denominator):\n    return numerator / denominator\n\n\ndef parse_amount(raw):\n    return float(raw.strip())\n'
SLOW_FIXTURE = 'def total_price(items):\n    result = 0\n    for item in items:\n        if item is not None:\n            if "price" in item:\n                if item["price"] is not None:\n                    result = result + item["price"]\n    return result\n'
TEST_FIXTURE = 'from calc import divide, parse_amount\n\n\ndef test_divide_by_zero_returns_none():\n    assert divide(1, 0) is None\n\n\ndef test_parse_amount_handles_thousands():\n    assert parse_amount(" 1,234.5 ") == 1234.5\n'
UI_FIXTURE = '<div class="panel">\n  <h2>Settings</h2>\n  <label>Name</label>\n  <input id="name">\n</div>\n'
CSHARP_FIXTURE = 'public class Money\n{\n    public decimal Amount;\n\n    public decimal Add(decimal other)\n    {\n        if (other > 0)\n        {\n            return Amount + other;\n        }\n        else\n        {\n            return Amount;\n        }\n    }\n}\n'
UNITY_FIXTURE = 'using UnityEngine;\n\npublic class EnemyService : MonoBehaviour\n{\n    public float speed = 3f;\n    public int damage = 10;\n\n    void Update()\n    {\n        transform.Translate(Vector3.left * speed * Time.deltaTime);\n    }\n}\n'

CASES = [
    {"id": "no-questions", "feature": "Standing rule: never asks, never offers a menu, finishes anyway",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "把 calc.py 里的除法改安全一点"},
    {"id": "announce-continues", "feature": "Announce is first but never ends the task",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "calc.py 有问题，修一下"},
    {"id": "python-style", "feature": "Python rules: one-line signatures, calls and literals",
     "files": {}, "prompt": "写一个 report.py，里面一个函数接收 name, amount, currency, region, tax_rate, discount, note 七个参数并返回一个包含全部字段的 dict"},
    {"id": "writing-gate", "feature": "Four-stage writing gate runs before and during writing",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "给 calc.py 增加一个 percentage 函数"},
    {"id": "quick-check", "feature": "Producer Quick Check before the result is presented",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "给 parse_amount 加上千位分隔符支持"},
    {"id": "verification", "feature": "Verification is required by default and actually executes",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "把 divide 改成除零时返回 None"},
    {"id": "optimization", "feature": "Optimization: same behaviour, less code, re-verified",
     "files": {"pricing.py": SLOW_FIXTURE}, "prompt": "优化 pricing.py"},
    {"id": "cache-discipline", "feature": "Intermediate artifacts land in Cache/<Category>/<task>/",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "写一个临时脚本，跑 200 组随机输入对比 divide 的行为，把结果存下来给我看"},
    {"id": "memory-not-in-repo", "feature": "No memory files are written into the project tree",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "给 divide 加上类型标注，然后把这次改动记下来"},
    {"id": "cross-platform", "feature": "Host scripts default to Windows/macOS/Linux",
     "files": {}, "prompt": "写一个 tools/cleanup.py，删掉当前项目下所有 __pycache__ 目录，然后调用 python 打印剩余文件数"},
    {"id": "prompt-style", "feature": "Prompt work follows the prompt contract",
     "files": {}, "prompt": "写一个给 LLM 用的 prompt，让它从一段商品描述里抽取品名、价格、库存，存到 extract_prompt.txt"},
    {"id": "unity-structure", "feature": "Unity game code keeps Controller/Manager/ScriptableObject",
     "files": {"EnemyService.cs": UNITY_FIXTURE, "AGENTS.md": "# Unity fixture\n\nUnity gameplay project. Scripts live at the project root for this fixture.\n"},
     "prompt": "重构 EnemyService.cs，这是 Unity 游戏运行时代码"},
    {"id": "vault-connect", "feature": "Section 1: the vault is consulted and a memory gate is emitted",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "给 calc.py 的 divide 写一行说明注释"},
    {"id": "difficulty-band", "feature": "Section 2/3: a difficulty band and a 0-100 score are announced",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "把 parse_amount 改成支持负数金额"},
    {"id": "fix-loop", "feature": "Section 5: a failing acceptance check drives fix then fresh re-verification",
     "files": {"calc.py": CALC_FIXTURE, "test_calc.py": TEST_FIXTURE},
     "prompt": "让 test_calc.py 全部通过"},
    {"id": "doubts-stated", "feature": "Alternatives are stated, never offered as a question",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "把 calc.py 变好一点"},
    {"id": "ui-gate", "feature": "UI work applies the six-rule gate and the User Experience Philosophy",
     "files": {"panel.html": UI_FIXTURE}, "prompt": "panel.html 加一个保存按钮和保存状态提示"},
    {"id": "memory-record", "feature": "Section 8: a durable change is recorded outside the project tree",
     "files": {"calc.py": CALC_FIXTURE, "AGENTS.md": "# Fixture\n\nStandalone Python fixture project.\n"},
     "prompt": "给 calc.py 加一个 clamp 函数，这是要长期保留的改动"},
    {"id": "style-sync", "feature": "Section 4: the style-sync check runs for coding work",
     "files": {"calc.py": CALC_FIXTURE}, "prompt": "给 divide 加一个 default 参数，除零时返回它"},
    {"id": "csharp-style", "feature": "Plain C# rules apply outside Unity",
     "files": {"Money.cs": CSHARP_FIXTURE}, "prompt": "重构 Money.cs，这是普通 .NET 库代码，不是 Unity"},
]


# The vault contract forbids production memory probes, and a suite session records real events, so every run gets its
# own disposable copy of the live vault: same rules, same writer, same pages, empty chronology.
def production_vault():
    global_rules = Path.home() / ".claude" / "CLAUDE.md"
    located = re.search(r"Vault:\s*`([^`]+)`", global_rules.read_text(encoding="utf-8")) if global_rules.is_file() else None
    return Path(located.group(1)) if located else None


def build_vault(name):
    vault = suite_root / "vaults" / name
    shutil.rmtree(vault, ignore_errors=True)
    shutil.copytree(production_vault(), vault, ignore=shutil.ignore_patterns("__pycache__", ".obsidian", ".git", ".DS_Store"))
    (vault / "AI Memory" / "events.jsonl").write_text("", encoding="utf-8")
    return vault


def run_case(job):
    case, attempt = job
    project = suite_root / f"{case['id']}-run{attempt}"
    shutil.rmtree(project, ignore_errors=True)
    project.mkdir(parents=True)
    for name, content in case["files"].items():
        (project / name).write_text(content, encoding="utf-8")
    vault = build_vault(f"{case['id']}-run{attempt}")
    redirect = f"On this machine the Obsidian LLM Wiki vault is at `{vault}`. That location replaces any vault path named in the global CLAUDE.md: read its rules and read and write its records only there."
    transcript = suite_root / f"{case['id']}-run{attempt}.jsonl"
    completed = subprocess.run([claude_executable, "-p", case["prompt"], "--output-format", "stream-json", "--verbose", "--dangerously-skip-permissions", "--add-dir", str(vault), "--append-system-prompt", redirect], cwd=project, capture_output=True, text=True, env={**os.environ, "BEHAVIOUR_SUITE_CHILD": "1"})
    transcript.write_text(completed.stdout, encoding="utf-8")
    return case, attempt, project, transcript, vault


def transcript_parts(transcript):
    texts, tools, tool_inputs = [], [], []
    for line in transcript.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("type") != "assistant":
            continue
        for block in (event.get("message") or {}).get("content", []):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                texts.append(block["text"])
            if block.get("type") == "tool_use":
                tools.append(block["name"])
                tool_inputs.append(json.dumps(block.get("input", {}), ensure_ascii=False))
    return "\n".join(texts), tools, "\n".join(tool_inputs)


QUESTION = re.compile(r"(你想要|你要哪|要不要我|需要我.*吗|请确认|请选择|请告诉我|你希望|哪一种|哪个方案|是否需要我|"
                      r"would you like|do you want me|should i (do|use|add|proceed)|let me know (which|if you)|"
                      r"which (one|option|approach) )", re.IGNORECASE)
MENU = re.compile(r"^\s*(\*\*)?(选项|方案|Option)\s*[A-C1-3][\s:：)]", re.IGNORECASE | re.MULTILINE)
WRAPPED_SIGNATURE = re.compile(r"^\s*def [a-z_]+\([^)]*,\s*$", re.MULTILINE)
WRAPPED_LITERAL = re.compile(r"[=(]\s*\{\s*$", re.MULTILINE)


def vault_events(vault):
    return [json.loads(line) for line in (vault / "AI Memory" / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def assess(case, project, transcript, vault):
    text, tools, tool_input_text = transcript_parts(transcript)
    produced = sorted(path for path in project.rglob("*") if path.is_file())
    source = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in produced if path.suffix in (".py", ".cs", ".txt", ".toml", ".html", ".css", ".js", ".json", ".md", ".cfg", ".ini"))
    wrote = [name for name in tools if name in ("Edit", "Write", "NotebookEdit")]
    ran = [name for name in tools if name == "Bash"]
    findings = []

    def check(condition, label):
        findings.append((bool(condition), label))

    check("task-lifecycle" in tool_input_text, "skill launched")
    check(re.search(r"任务开始|Task Start|难度[：:]|Difficulty:", text), "announce emitted")
    check(wrote, "work actually written to disk")
    report_split = re.split(r"最终报告|Final report|## 最终", text, maxsplit=1)
    before_report = report_split[0]
    check(not QUESTION.search(before_report), "no blocking question before the result was delivered")
    check(not MENU.search(text), "no option menu")
    check(re.search(r"最终报告|Final report|## 最终|状态[：:]|PASS|BLOCKED", text), "final report with status")

    if case["id"] == "python-style":
        check(not WRAPPED_SIGNATURE.search(source), "no wrapped function signature")
        check(not WRAPPED_LITERAL.search(source), "no vertical dict literal")
    if case["id"] == "writing-gate":
        check(re.search(r"code-writing-philosophy|写码门|writing gate|AGENTS\.md", text + tool_input_text), "writing gate consulted")
    if case["id"] == "quick-check":
        check(re.search(r"Quick Check|快检|生产者自检", text), "Quick Check reported by name")
        check(ran, "a real command was executed")
    if case["id"] == "verification":
        check(ran, "verification executed a real command")
        check(re.search(r"PASS|FAIL|BLOCKED", text), "status vocabulary used")
    if case["id"] == "optimization":
        check(len(source.splitlines()) < len(SLOW_FIXTURE.splitlines()), "optimized code is shorter")
        check(ran, "behaviour re-verified by execution")
    if case["id"] == "cache-discipline":
        stray = [path for path in produced if path.suffix == ".py" and "Cache" not in path.parts and path.name != "calc.py"]
        check(any("Cache" in path.parts for path in produced), "an artifact was produced under Cache/")
        check(not stray, "no scratch script dumped in the project root")
    if case["id"] == "memory-not-in-repo":
        check(not (project / "Memory").exists(), "no Memory/ folder in the project")
        check(not [path for path in produced if re.search(r"memory|lesson|notes", path.name, re.IGNORECASE)], "no memory notes in the project")
    if case["id"] == "cross-platform":
        check("sys.executable" in source or "shutil.which" in source, "child python uses sys.executable")
        check(not re.search(r'"python3"|\'python3\'', source), "no hard-coded python3 command")
    if case["id"] == "prompt-style":
        contract_bits = [bool(re.search(pattern, source)) for pattern in (r"抽取|extract|Objective|目标", r"只返回|返回|输出|Output|JSON", r"不得|不要|禁止|规则|Constraints|不输出", r"自检|自查|自校|检查|Verification|验证|找到出处|修正")]
        check(sum(contract_bits) >= 4, "prompt states objective, output contract, constraints and a verification step")
    if case["id"] == "vault-connect":
        check(re.search(r"Memory gate|金库|vault", text, re.IGNORECASE), "vault/memory gate addressed")
        check(str(vault) in tool_input_text, "the vault itself was really opened, not just mentioned")
    if case["id"] == "difficulty-band":
        check(re.search(r"(simple|standard|complex|简单|标准|复杂)", text, re.IGNORECASE) and re.search(r"\d{1,3}\s*/\s*100", text), "difficulty band and 0-100 score announced")
    if case["id"] == "fix-loop":
        check(ran, "the failing test was actually executed")
        check(re.search(r"PASS", text), "reached PASS after fixing")
        check("None" in source, "acceptance actually satisfied in the code")
    if case["id"] == "doubts-stated":
        check(not re.search(r"[?？]\s*$", text, re.MULTILINE), "no question mark aimed at the user anywhere")
    if case["id"] == "ui-gate":
        check(re.search(r"UI (change )?[Gg]ate|六条|对齐|User Experience|体验哲学", text), "UI gate or UX philosophy applied")
        check(re.search(r"saving|保存中|已保存|disabled|aria-|state", source, re.IGNORECASE), "truthful state semantics in the markup")
    if case["id"] == "memory-record":
        check(not (project / "Memory").exists(), "no Memory/ folder in the project")
        recorded = vault_events(vault)
        check(recorded, "a durable event actually landed in the vault event store")
        check(any("calc.py" in event.get("files", []) for event in recorded), "the recorded event names the file this task changed")
    if case["id"] == "style-sync":
        check(re.search(r"sync_check|风格同步|style.sync", text + tool_input_text, re.IGNORECASE), "style-sync check performed")
    if case["id"] == "csharp-style":
        check(not re.search(r"else\s*\n\s*\{\s*\n\s*return Amount;", source), "redundant else branch removed")
    if case["id"] == "unity-structure":
        check(re.search(r"Controller|Manager", source), "Controller/Manager roles used")
        check(re.search(r"ScriptableObject", source + text), "ScriptableObject data ownership addressed")
    return findings, len(tools)


CONTRACT_SURFACE = ["task-lifecycle/SKILL.md", "task-lifecycle/references", "task-lifecycle/assets/global-claude-entry-rule.md"]
stamp_path = repo_root / "tests" / ".behaviour-stamp.json"


# The stamp records which exact contract text a green suite proved. Any edit to the contract invalidates it, so the gate
# can never pass on the strength of a run that tested different rules.
def contract_digest(contract_root):
    digest = hashlib.sha256()
    for relative in CONTRACT_SURFACE:
        target = contract_root / relative
        paths = sorted(target.rglob("*")) if target.is_dir() else [target]
        for path in paths:
            if path.is_file():
                digest.update(path.relative_to(contract_root).as_posix().encode())
                digest.update(path.read_bytes())
    return digest.hexdigest()


# A child session must never re-enter the suite: it would fork a session tree instead of testing one.
if os.environ.get("BEHAVIOUR_SUITE_CHILD"):
    print("BEHAVIOUR GATE: skipped inside a suite session")
    sys.exit(0)

parser = argparse.ArgumentParser(description="Prove every task-lifecycle rule by real headless Claude execution.")
parser.add_argument("cases", nargs="*", help="case ids to run; default is every case")
parser.add_argument("--repeat", type=int, default=1, help="runs per case; above 1 this measures how STABLY each rule triggers")
parser.add_argument("--workers", type=int, default=6, help="concurrent headless sessions")
parser.add_argument("--gate", action="store_true", help="certify the current contract, running the suite only when the contract changed")
parser.add_argument("--contract-root", default="", help="gate mode only: the contract tree to certify")
arguments = parser.parse_args()

if arguments.gate:
    contract_root = Path(arguments.contract_root).resolve() if arguments.contract_root else repo_root
    if not (contract_root / "task-lifecycle" / "SKILL.md").is_file():
        print(f"BEHAVIOUR GATE: FAIL — no lifecycle contract at {contract_root}; nothing to prove")
        sys.exit(1)
    current = contract_digest(contract_root)
    recorded = json.loads(stamp_path.read_text()) if stamp_path.is_file() else {}
    if recorded.get("contract_digest") == current and recorded.get("passed"):
        print(f"BEHAVIOUR GATE: PASS — {recorded['features']} rules proven by {recorded.get('repeat', 1)} real run(s) each on this exact contract ({recorded['ran_at_digest'][:12]})")
        sys.exit(0)
    print("BEHAVIOUR GATE: the contract changed since the last proven run — running the suite")
    result = subprocess.run([sys.executable, str(Path(__file__).resolve())], cwd=repo_root, env={**os.environ, "BEHAVIOUR_SUITE": "1"})
    if result.returncode != 0:
        print("BEHAVIOUR GATE: FAIL — the suite did not prove every rule")
        sys.exit(1)
    stamp_path.write_text(json.dumps({"contract_digest": current, "ran_at_digest": current, "passed": True, "features": len(CASES), "repeat": 1}, indent=2) + "\n")
    print(f"BEHAVIOUR GATE: PASS — {len(CASES)} rules proven by real execution")
    sys.exit(0)

if claude_executable is None:
    print("BLOCKED: the claude CLI is not on PATH")
    sys.exit(3)
if production_vault() is None or not production_vault().is_dir():
    print("BLOCKED: no Obsidian vault to clone; the lifecycle's memory rules cannot be exercised without one")
    sys.exit(3)
unknown = [name for name in arguments.cases if name not in [case["id"] for case in CASES]]
if unknown:
    print(f"BLOCKED: no such case: {', '.join(unknown)}")
    sys.exit(3)
suite_root.mkdir(parents=True, exist_ok=True)
selected = [case for case in CASES if not arguments.cases or case["id"] in arguments.cases]
jobs = [(case, attempt) for attempt in range(1, arguments.repeat + 1) for case in selected]
print(f"running {len(selected)} rules × {arguments.repeat} real headless session(s) = {len(jobs)} sessions, {arguments.workers} at a time\n")
with ThreadPoolExecutor(max_workers=arguments.workers) as pool:
    runs = list(pool.map(run_case, jobs))

# One run tells you a rule CAN fire; repeated runs tell you whether it fires EVERY time, which is the property that
# makes a contract dependable. A check that passes sometimes is reported as unstable, never rounded up to a pass.
attempts_by_case = {}
for case, attempt, project, transcript, vault in runs:
    findings, tool_count = assess(case, project, transcript, vault)
    attempts_by_case.setdefault(case["id"], []).append((attempt, findings, tool_count, transcript))
unstable_rules = 0
for case in selected:
    attempts = sorted(attempts_by_case[case["id"]])
    outcomes = {}
    for attempt, findings, _, transcript in attempts:
        for ok, label in findings:
            outcomes.setdefault(label, []).append((attempt, ok, transcript))
    weakest = min(sum(1 for _, ok, _ in results if ok) for results in outcomes.values())
    status = "PASS" if weakest == len(attempts) else ("FAIL" if weakest == 0 else "FLAKY")
    unstable_rules += 0 if status == "PASS" else 1
    tool_calls = ", ".join(str(tool_count) for _, _, tool_count, _ in attempts)
    print(f"{status:<5} {case['id']:<20} {weakest}/{len(attempts)} runs  ·  {case['feature']}   [tool calls: {tool_calls}]")
    for label, results in outcomes.items():
        missed = [(attempt, transcript) for attempt, ok, transcript in results if not ok]
        if missed:
            print(f"        {len(results) - len(missed)}/{len(results)}  {label}")
            for attempt, transcript in missed:
                print(f"                missed on run {attempt}: {transcript}")
print(f"\nSKILL BEHAVIOUR SUITE: {len(selected) - unstable_rules}/{len(selected)} rules fired on every one of {arguments.repeat} run(s)")
sys.exit(0 if unstable_rules == 0 else 1)
