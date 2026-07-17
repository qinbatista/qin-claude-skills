#!/usr/bin/env python3
"""Adaptive model recommendation + experience ledger for Claude Code.

Faithful port of the Codex adaptive-model boundary-search algorithm
(obsidian_model_memory.py: _active_recommendation / _switch_details) onto
Claude Code's per-agent model routing (Agent tool `model` param / Workflow
`agent()` model+effort). Not a simplified "escalate on fail, reuse on pass"
cache — it actively probes ONE RUNG CHEAPER after a proven pass (downgrade),
escalates one rung on quality failure (upgrade), narrows an untested gap
between a known-fail and known-pass rung, and freezes once that boundary is
tight. Six switch directions, same vocabulary as Codex's Model Switch.md:
initial, upgrade, downgrade, freeze, no_switch, operational_fallback.

Commands:
  recommend --task-type T --module M [--file F] [--complexity easy|complex]
  record    --task-type T --module M [--file F] --model X --effort E
            --status pass|fail [--failure-class none|correctness|operational]
            [--tokens N] [--time-ms N] [--summary S]
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LADDER_PATH = SKILL_ROOT / "references" / "ladder.json"
LEDGER_PATH = SKILL_ROOT / "local" / "ledger.jsonl"

QUALITY_FAILURE_CLASSES = {"correctness"}
OPERATIONAL_FAILURE_CLASSES = {"operational"}


def load_ladder():
    return json.loads(LADDER_PATH.read_text(encoding="utf-8"))


def load_records():
    if not LEDGER_PATH.exists():
        return []
    records = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _pair(record):
    return f"{record['model']}|{record['effort']}"


def match_records(records, args):
    candidates = [r for r in records if r.get("task_type") == args.task_type]
    if not candidates:
        return [], "none"
    if args.file:
        file_matches = [r for r in candidates if r.get("file") == args.file]
        if file_matches:
            return file_matches, "file"
    if args.module:
        module_matches = [r for r in candidates if r.get("module") == args.module]
        if module_matches:
            return module_matches, "module"
    return candidates, "project_task"


def _quality_verdict(record):
    """pass/fail affect the boundary search; operational failures are noise (None)."""
    if record.get("status") == "fail" and record.get("failure_class") in QUALITY_FAILURE_CLASSES:
        return "fail"
    if record.get("status") == "pass" and record.get("failure_class", "none") == "none":
        return "pass"
    return None


def boundary_search(pairs, matched):
    """Port of Codex's _active_recommendation. Returns the next pair to try
    and why, by walking known pass/fail verdicts along the ordered ladder."""
    verdicts = {}
    for record in matched:
        pair = _pair(record)
        if pair not in pairs:
            continue
        verdict = _quality_verdict(record)
        if verdict is None:
            continue
        if verdict == "fail":
            verdicts[pair] = "fail"
        elif verdicts.get(pair) != "fail":
            verdicts[pair] = "pass"

    failed_pairs = [p for p, v in verdicts.items() if v == "fail"]
    failed_pair = max(failed_pairs, key=pairs.index) if failed_pairs else None
    passing_pairs = [
        p for p, v in verdicts.items()
        if v == "pass" and (failed_pair is None or pairs.index(p) > pairs.index(failed_pair))
    ]
    success_pair = min(passing_pairs, key=pairs.index) if passing_pairs else None

    if failed_pair is None and success_pair is None:
        return {"selected_pair": None, "trial": False, "state": "cold_start", "reason": "shared_cold_start"}

    if failed_pair is None:
        idx = pairs.index(success_pair)
        if idx == 0:
            return {"selected_pair": success_pair, "trial": False, "state": "frozen", "reason": "verified_floor_retained"}
        return {"selected_pair": pairs[idx - 1], "trial": True, "state": "provisional", "reason": "real_pass_one_rung_down"}

    if success_pair is None:
        idx = pairs.index(failed_pair)
        if idx + 1 < len(pairs):
            return {"selected_pair": pairs[idx + 1], "trial": True, "state": "quality_boundary", "reason": "quality_failure_one_rung_up"}
        return {"selected_pair": None, "trial": False, "state": "blocked", "reason": "quality_boundary_exhausted"}

    fi, si = pairs.index(failed_pair), pairs.index(success_pair)
    untested = [p for p in pairs[fi + 1:si] if p not in verdicts]
    if untested:
        return {"selected_pair": untested[0], "trial": True, "state": "quality_boundary", "reason": "quality_boundary_gap_trial"}
    return {"selected_pair": success_pair, "trial": False, "state": "frozen", "reason": "verified_quality_boundary"}


def switch_direction(prior_pair, selected_pair, reason, state):
    """Port of Codex's _switch_details direction derivation."""
    if state == "operational_fallback" or "operational_failure" in reason:
        return "operational_fallback"
    if prior_pair is None:
        return "initial"
    if "one_rung_down" in reason:
        return "downgrade"
    if "one_rung_up" in reason or "quality_failure" in reason:
        return "upgrade"
    if state == "frozen" or "retained" in reason or reason in ("verified_floor_retained", "verified_quality_boundary"):
        return "freeze"
    return "no_switch"


def _latest(records):
    # Ledger is append-only and read in file order, so list position is the
    # true ordering — recorded_at is second-resolution and ties under load,
    # which silently breaks max()-by-timestamp on same-second writes.
    return records[-1] if records else None


def recommend(args):
    ladder = load_ladder()
    pairs = ladder["pairs"]
    records = load_records()
    matched, specificity = match_records(records, args)

    latest = _latest(matched)
    prior_pair = _pair(latest) if latest else None

    # An operational failure at the pair we're about to reattempt means the
    # pick itself is broken (not a quality question the boundary search can
    # reason about, since operational failures produce no verdict) — escalate
    # immediately instead of repeating a broken pair forever.
    if latest and latest.get("failure_class") in OPERATIONAL_FAILURE_CLASSES:
        idx = pairs.index(prior_pair) if prior_pair in pairs else -1
        if idx + 1 < len(pairs):
            selected_pair = pairs[idx + 1]
            reason, state = "operational_failure_immediate_escalation", "operational_fallback"
            model, effort = selected_pair.split("|")
            return {
                "model": model, "effort": effort, "selected_pair": selected_pair,
                "prior_pair": prior_pair, "reason": reason, "state": state,
                "direction": switch_direction(prior_pair, selected_pair, reason, state),
                "matched_records": len(matched), "specificity": specificity,
            }

    result = boundary_search(pairs, matched)
    if result["selected_pair"] is None and result["state"] == "cold_start":
        cheap = ladder["cheap_first"]["complex_pair" if args.complexity == "complex" else "easy_pair"]
        selected_pair = f"{cheap['model']}|{cheap['effort']}"
        reason, state = "shared_cold_start", "cold_start"
    elif result["selected_pair"] is None:
        # ladder exhausted (blocked) — stay at the top rung and report it plainly
        selected_pair = pairs[-1]
        reason, state = result["reason"], result["state"]
    else:
        selected_pair, reason, state = result["selected_pair"], result["reason"], result["state"]

    model, effort = selected_pair.split("|")
    direction = switch_direction(prior_pair, selected_pair, reason, state)
    return {
        "model": model, "effort": effort, "selected_pair": selected_pair,
        "prior_pair": prior_pair, "reason": reason, "state": state,
        "direction": direction, "matched_records": len(matched), "specificity": specificity,
    }


def record(args):
    ladder = load_ladder()
    pairs = ladder["pairs"]
    new_pair = f"{args.model}|{args.effort}"

    records = load_records()
    matched, _ = match_records(records, args)
    latest = _latest(matched)
    prior_pair = _pair(latest) if latest else None

    if args.reason and args.state:
        reason, state = args.reason, args.state
    else:
        # reconstruct what recommend() would have said just before this write
        result = boundary_search(pairs, matched)
        reason = result["reason"]
        state = result["state"]

    direction = switch_direction(prior_pair, new_pair, reason, state)

    entry = {
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_type": args.task_type,
        "module": args.module or "",
        "file": args.file or "",
        "model": args.model,
        "effort": args.effort,
        "pair": new_pair,
        "prior_pair": prior_pair,
        "direction": direction,
        "reason": reason,
        "state": state,
        "status": args.status,
        "failure_class": args.failure_class,
        "tokens": args.tokens,
        "time_ms": args.time_ms,
        "summary": (args.summary or "")[:300],
    }
    entry["record_sha256"] = hashlib.sha256(
        json.dumps(entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, separators=(",", ":")) + "\n")
    return entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--task-type", required=True)
    common.add_argument("--module", default="")
    common.add_argument("--file", default="")

    rec = sub.add_parser("recommend", parents=[common])
    rec.add_argument("--complexity", choices=["easy", "complex"], default="easy")

    log = sub.add_parser("record", parents=[common])
    log.add_argument("--model", required=True)
    log.add_argument("--effort", required=True)
    log.add_argument("--status", choices=["pass", "fail"], required=True)
    log.add_argument("--failure-class", choices=["none", "correctness", "operational"], default="none")
    log.add_argument("--tokens", type=int, default=0)
    log.add_argument("--time-ms", type=int, default=0)
    log.add_argument("--summary", default="")
    log.add_argument("--reason", default="")
    log.add_argument("--state", default="")

    args = parser.parse_args()
    result = recommend(args) if args.command == "recommend" else record(args)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
