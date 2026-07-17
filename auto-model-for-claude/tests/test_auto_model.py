#!/usr/bin/env python3
"""Unit tests for the auto-model-for-claude boundary-search router.

Run: python3 -m unittest discover -s tests -v   (from the skill root)
Each test runs against an isolated temporary ledger — the private
local/ledger.jsonl is never touched.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

SKILL_ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("auto_model", SKILL_ROOT / "scripts" / "auto_model.py")
auto_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto_model)


def args(task_type, module="m", file="", complexity="easy"):
    return SimpleNamespace(task_type=task_type, module=module, file=file, complexity=complexity)


def record_args(task_type, model, effort, status, module="m", file="", failure_class="none",
                reason="", state="", tokens=0, time_ms=0, summary="test"):
    return SimpleNamespace(task_type=task_type, module=module, file=file, model=model,
                           effort=effort, status=status, failure_class=failure_class,
                           reason=reason, state=state, tokens=tokens, time_ms=time_ms,
                           summary=summary)


class AutoModelTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_ledger = auto_model.LEDGER_PATH
        auto_model.LEDGER_PATH = Path(self._tmp.name) / "ledger.jsonl"

    def tearDown(self):
        auto_model.LEDGER_PATH = self._original_ledger
        self._tmp.cleanup()

    # -- cold start --------------------------------------------------------
    def test_cold_start_easy(self):
        r = auto_model.recommend(args("t", complexity="easy"))
        self.assertEqual(r["selected_pair"], "haiku|low")
        self.assertEqual(r["direction"], "initial")
        self.assertEqual(r["reason"], "shared_cold_start")

    def test_cold_start_complex(self):
        r = auto_model.recommend(args("t", complexity="complex"))
        self.assertEqual(r["selected_pair"], "sonnet|high")

    # -- downgrade probe / freeze ------------------------------------------
    def test_pass_probes_one_rung_down(self):
        auto_model.record(record_args("t", "sonnet", "high", "pass"))
        r = auto_model.recommend(args("t"))
        self.assertEqual(r["selected_pair"], "sonnet|medium")
        self.assertEqual(r["direction"], "downgrade")
        self.assertEqual(r["reason"], "real_pass_one_rung_down")

    def test_boundary_freeze_when_fail_and_pass_adjacent(self):
        auto_model.record(record_args("t", "sonnet", "medium", "pass"))
        auto_model.record(record_args("t", "sonnet", "low", "fail", failure_class="correctness"))
        r = auto_model.recommend(args("t"))
        self.assertEqual(r["selected_pair"], "sonnet|medium")
        self.assertEqual(r["direction"], "freeze")
        self.assertEqual(r["reason"], "verified_quality_boundary")

    def test_floor_freeze(self):
        auto_model.record(record_args("t", "haiku", "low", "pass"))
        r = auto_model.recommend(args("t"))
        self.assertEqual(r["selected_pair"], "haiku|low")
        self.assertEqual(r["direction"], "freeze")
        self.assertEqual(r["reason"], "verified_floor_retained")

    # -- upgrade / exhaustion ----------------------------------------------
    def test_fail_escalates_one_rung_up(self):
        auto_model.record(record_args("t", "haiku", "low", "fail", failure_class="correctness"))
        r = auto_model.recommend(args("t"))
        self.assertEqual(r["selected_pair"], "haiku|medium")
        self.assertEqual(r["direction"], "upgrade")
        self.assertEqual(r["reason"], "quality_failure_one_rung_up")

    def test_ladder_exhausted_at_top(self):
        auto_model.record(record_args("t", "fable", "max", "fail", failure_class="correctness"))
        r = auto_model.recommend(args("t"))
        self.assertEqual(r["selected_pair"], "fable|max")
        self.assertEqual(r["reason"], "quality_boundary_exhausted")
        self.assertEqual(r["state"], "blocked")

    # -- gap trial ----------------------------------------------------------
    def test_gap_trial_between_fail_and_pass(self):
        auto_model.record(record_args("t", "haiku", "low", "fail", failure_class="correctness"))
        auto_model.record(record_args("t", "sonnet", "low", "pass"))
        r = auto_model.recommend(args("t"))
        self.assertEqual(r["selected_pair"], "haiku|medium")
        self.assertEqual(r["reason"], "quality_boundary_gap_trial")

    # -- operational fallback ------------------------------------------------
    def test_operational_failure_escalates_immediately(self):
        auto_model.record(record_args("t", "opus", "low", "fail", failure_class="operational"))
        r = auto_model.recommend(args("t"))
        self.assertEqual(r["selected_pair"], "opus|medium")
        self.assertEqual(r["direction"], "operational_fallback")

    def test_operational_record_direction_via_passthrough(self):
        auto_model.record(record_args("t", "opus", "low", "fail", failure_class="operational"))
        rec = auto_model.record(record_args(
            "t", "opus", "medium", "pass",
            reason="operational_failure_immediate_escalation", state="operational_fallback"))
        self.assertEqual(rec["direction"], "operational_fallback")

    # -- scoping tiers --------------------------------------------------------
    def test_file_scope_beats_module_scope(self):
        auto_model.record(record_args("t", "haiku", "low", "pass", module="mod-a"))
        auto_model.record(record_args("t", "sonnet", "high", "pass", module="mod-a", file="x.py"))
        r = auto_model.recommend(args("t", module="mod-a", file="x.py"))
        self.assertEqual(r["specificity"], "file")
        self.assertEqual(r["prior_pair"], "sonnet|high")

    # -- ledger integrity -------------------------------------------------------
    def test_record_appends_valid_jsonl_with_sha(self):
        auto_model.record(record_args("t", "haiku", "low", "pass", tokens=123, time_ms=45))
        lines = auto_model.LEDGER_PATH.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["pair"], "haiku|low")
        self.assertEqual(entry["tokens"], 123)
        self.assertEqual(len(entry["record_sha256"]), 16)

    def test_switch_direction_retained_substring_matches_codex(self):
        self.assertEqual(
            auto_model.switch_direction("a|b", "a|b", "verified_floor_retained", "provisional"),
            "freeze")


if __name__ == "__main__":
    unittest.main()
