# Behavioural test suite for the task-lifecycle skill: every feature exercised by a REAL headless Claude run,
# then asserted against the transcript and the files it actually produced. Supported platforms: macOS, Linux.
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
# Fixtures live OUTSIDE this repository: a project nested inside it would correctly resolve the repo as its
# project root and write there, which is the skill behaving properly but not what these cases mean to measure.
suite_root = Path("/private/tmp/claude-501/-Users-qin-Documents-AIProject-qin-claude-skills/dd019ef8-44fe-442e-9044-c37f9ec134e0/scratchpad/skill-suite")
claude_executable = shutil.which("claude")

CALC_FIXTURE = 'def divide(numerator, denominator):\n    return numerator / denominator\n\n\ndef parse_amount(raw):\n    return float(raw.strip())\n'
SLOW_FIXTURE = 'def total_price(items):\n    result = 0\n    for item in items:\n        if item is not None:\n            if "price" in item:\n                if item["price"] is not None:\n                    result = result + item["price"]\n    return result\n'
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
]


def run_case(case):
    project = suite_root / case["id"]
    shutil.rmtree(project, ignore_errors=True)
    project.mkdir(parents=True)
    for name, content in case["files"].items():
        (project / name).write_text(content, encoding="utf-8")
    transcript = suite_root / f"{case['id']}.jsonl"
    completed = subprocess.run([claude_executable, "-p", case["prompt"], "--output-format", "stream-json", "--verbose", "--dangerously-skip-permissions"], cwd=project, capture_output=True, text=True)
    transcript.write_text(completed.stdout, encoding="utf-8")
    return case, project, transcript


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


def assess(case, project, transcript):
    text, tools, tool_input_text = transcript_parts(transcript)
    produced = sorted(path for path in project.rglob("*") if path.is_file())
    source = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in produced if path.suffix in (".py", ".cs", ".txt", ".toml"))
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
        check(re.search(r"Quick Check", text), "Quick Check reported")
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
    if case["id"] == "unity-structure":
        check(re.search(r"Controller|Manager", source), "Controller/Manager roles used")
        check(re.search(r"ScriptableObject", source + text), "ScriptableObject data ownership addressed")
    return findings, len(tools)


if claude_executable is None:
    print("BLOCKED: the claude CLI is not on PATH")
    sys.exit(3)
suite_root.mkdir(parents=True, exist_ok=True)
selected = [case for case in CASES if len(sys.argv) < 2 or case["id"] in sys.argv[1:]]
with ThreadPoolExecutor(max_workers=6) as pool:
    runs = list(pool.map(run_case, selected))

failed_cases = 0
for case, project, transcript in runs:
    findings, tool_count = assess(case, project, transcript)
    passed = all(ok for ok, _ in findings)
    failed_cases += 0 if passed else 1
    print(f"{'PASS' if passed else 'FAIL'}  {case['id']:<20} {tool_count:>3} tool calls  ·  {case['feature']}")
    for ok, label in findings:
        if not ok:
            print(f"        MISSED: {label}")
print(f"\nSKILL BEHAVIOUR SUITE: {len(runs) - failed_cases}/{len(runs)} features verified by real execution")
sys.exit(0 if failed_cases == 0 else 1)
