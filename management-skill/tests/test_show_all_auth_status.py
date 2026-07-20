import importlib.util
import json
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch


MANAGER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "manage_auth_profiles.py"
MANAGER_SPEC = importlib.util.spec_from_file_location("manage_auth_profiles", MANAGER_PATH)
manage_auth_profiles = importlib.util.module_from_spec(MANAGER_SPEC)
MANAGER_SPEC.loader.exec_module(manage_auth_profiles)

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "show_all_auth_status.py"
SPEC = importlib.util.spec_from_file_location("show_all_auth_status", SCRIPT_PATH)
show_all_auth_status = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(show_all_auth_status)


FAKE_CREDENTIAL_PAYLOAD = {
    "claudeAiOauth": {
        "accessToken": "sk-ant-oat01-not-a-real-secret",
        "refreshToken": "sk-ant-ort01-not-a-real-secret",
        "expiresAt": 4102444800000,
        "scopes": ["user:inference"],
        "subscriptionType": "max",
        "rateLimitTier": "default",
    }
}
FAKE_IDENTITY = {"userID": "user-123", "oauthAccount": {"emailAddress": "person@example.com", "organizationName": "Acme"}}


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class ShowAllAuthStatusTest(unittest.TestCase):
    """`show_all_auth_status.py` never touches the real ~/.claude or Keychain: --claude-home
    and --home-dir always point at a tempdir, and the keychain read is patched off so file-
    store detection is deterministic."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.home = Path(self.tempdir.name)
        self.claude_home = self.home / ".claude"
        self.claude_home.mkdir()
        write_json(self.claude_home / ".credentials.json", FAKE_CREDENTIAL_PAYLOAD)
        write_json(self.home / ".claude.json", FAKE_IDENTITY)
        self.keychain_patch = patch.object(manage_auth_profiles, "read_keychain_credentials", return_value=None)
        self.keychain_patch.start()
        self.addCleanup(self.keychain_patch.stop)
        # show_all_auth_status.py loads its own copy of manage_auth_profiles via
        # importlib file-location loading; patch that loaded copy's keychain reader too.
        self.loaded_manager = show_all_auth_status.load_manager()
        self.loaded_keychain_patch = patch.object(self.loaded_manager, "read_keychain_credentials", return_value=None)
        self.loaded_keychain_patch.start()
        self.addCleanup(self.loaded_keychain_patch.stop)

    def run_main(self, argv):
        with patch.object(sys, "argv", ["show_all_auth_status.py", *argv]), patch("sys.stdout", new_callable=StringIO) as stdout:
            with patch.object(show_all_auth_status, "load_manager", return_value=self.loaded_manager):
                show_all_auth_status.main()
        return stdout.getvalue()

    def test_no_selector_only_prints_status_and_never_switches(self):
        output = self.run_main(["--claude-home", str(self.claude_home), "--home-dir", str(self.home)])
        self.assertIn("active", output)
        self.assertIn("person@example.com", output)
        self.assertNotIn("accessToken", output)
        self.assertNotIn("sk-ant-oat01", output)

    def test_selector_without_yes_does_not_switch(self):
        write_json(self.claude_home / "credentials_work.json", {
            "credential_payload": FAKE_CREDENTIAL_PAYLOAD,
            "identity_snapshot": {"email": "work@example.com"},
            "backed_up_from_store": "file",
            "backed_up_at": "2026-01-01T00:00:00+00:00",
        })
        original = (self.claude_home / ".credentials.json").read_text(encoding="utf-8")
        output = self.run_main(["work", "--claude-home", str(self.claude_home), "--home-dir", str(self.home)])
        self.assertEqual((self.claude_home / ".credentials.json").read_text(encoding="utf-8"), original)
        self.assertIn("Re-run with --yes", output)
        self.assertNotIn("accessToken", output)

    def test_selector_with_yes_switches_then_reports_status(self):
        write_json(self.claude_home / "credentials_work.json", {
            "credential_payload": FAKE_CREDENTIAL_PAYLOAD,
            "identity_snapshot": {"email": "work@example.com"},
            "backed_up_from_store": "file",
            "backed_up_at": "2026-01-01T00:00:00+00:00",
        })
        output = self.run_main(["work", "--yes", "--claude-home", str(self.claude_home), "--home-dir", str(self.home)])
        self.assertIn("Switched active credentials to 'work'", output)
        self.assertNotIn("accessToken", output)
        self.assertNotIn("sk-ant-oat01", output)

    def test_unknown_selector_exits_nonzero_without_traceback_leak(self):
        with patch.object(sys, "argv", ["show_all_auth_status.py", "ghost", "--yes", "--claude-home", str(self.claude_home), "--home-dir", str(self.home)]):
            with self.assertRaises(SystemExit) as raised:
                show_all_auth_status.main()
        self.assertEqual(raised.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
