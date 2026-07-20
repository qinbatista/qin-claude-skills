import importlib.util
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "manage_auth_profiles.py"
MODULE_SPEC = importlib.util.spec_from_file_location("manage_auth_profiles", MODULE_PATH)
manage_auth_profiles = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(manage_auth_profiles)


FAKE_CREDENTIAL_PAYLOAD = {
    "claudeAiOauth": {
        "accessToken": "sk-ant-oat01-not-a-real-secret",
        "refreshToken": "sk-ant-ort01-not-a-real-secret",
        "expiresAt": 4102444800000,  # 2100-01-01T00:00:00Z, far future -> not expired
        "refreshTokenExpiresAt": 4104000000000,
        "scopes": ["user:inference", "user:profile"],
        "subscriptionType": "max",
        "rateLimitTier": "default_claude_max_20x",
    }
}
FAKE_EXPIRED_PAYLOAD = {
    "claudeAiOauth": {
        "accessToken": "sk-ant-oat01-expired",
        "refreshToken": "sk-ant-ort01-expired",
        "expiresAt": 946684800000,  # 2000-01-01T00:00:00Z, long past
        "scopes": ["user:inference"],
        "subscriptionType": "pro",
        "rateLimitTier": "default",
    }
}
FAKE_IDENTITY = {
    "userID": "user-123",
    "oauthAccount": {
        "emailAddress": "person@example.com",
        "organizationName": "Acme Corp",
        "organizationUuid": "org-uuid-1",
        "accountUuid": "acct-uuid-1",
        "seatTier": "pro",
        "billingType": "workspace",
    },
}


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class NoSecretLeakMixin:
    def assert_no_secret_strings(self, obj):
        blob = json.dumps(obj)
        self.assertNotIn("accessToken", blob)
        self.assertNotIn("refreshToken", blob)
        self.assertNotIn("not-a-real-secret", blob)
        self.assertNotIn("sk-ant-oat01", blob)
        self.assertNotIn("sk-ant-ort01", blob)


class FileBackedStoreTest(unittest.TestCase, NoSecretLeakMixin):
    """Exercises the file-store path (~/.claude/.credentials.json). No real ~/.claude or
    Keychain access ever happens: claude_home/home_dir are always a tempdir, and the
    keychain boundary is patched to fail so file-store detection wins deterministically."""

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

    def test_discover_profiles_reads_file_store_and_identity(self):
        profiles = manage_auth_profiles.discover_profiles(claude_home=self.claude_home, home_dir=self.home)
        self.assertEqual(len(profiles), 1)
        active = profiles[0]
        self.assertEqual(active["alias"], "active")
        self.assertEqual(active["store"], "file")
        self.assertTrue(active["active"])
        self.assertEqual(active["email"], "person@example.com")
        self.assertEqual(active["organization_name"], "Acme Corp")
        self.assertEqual(active["subscription_type"], "max")
        self.assertTrue(active["has_access_token"])
        self.assertTrue(active["has_refresh_token"])
        self.assertFalse(active["expired"])
        self.assert_no_secret_strings(profiles)

    def test_expired_token_is_flagged(self):
        write_json(self.claude_home / ".credentials.json", FAKE_EXPIRED_PAYLOAD)
        profiles = manage_auth_profiles.discover_profiles(claude_home=self.claude_home, home_dir=self.home)
        self.assertTrue(profiles[0]["expired"])
        self.assertEqual(manage_auth_profiles.status_label(profiles[0]), "ACTIVE EXPIRED")

    def test_missing_credentials_reports_none_store(self):
        (self.claude_home / ".credentials.json").unlink()
        profiles = manage_auth_profiles.discover_profiles(claude_home=self.claude_home, home_dir=self.home)
        self.assertEqual(profiles[0]["store"], "none")
        self.assertFalse(profiles[0]["has_access_token"])
        self.assertEqual(manage_auth_profiles.status_label(profiles[0]), "NO CREDENTIALS")

    def test_backup_is_dry_run_by_default_then_writes_with_yes(self):
        target = self.claude_home / "credentials_work.json"
        args = types.SimpleNamespace(claude_home=self.claude_home, home_dir=self.home, name="work", force=False, yes=False)
        manage_auth_profiles.command_backup(args)
        self.assertFalse(target.exists(), "dry-run must not write")

        args.yes = True
        manage_auth_profiles.command_backup(args)
        self.assertTrue(target.exists())
        snapshot = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(snapshot["identity_snapshot"]["email"], "person@example.com")
        self.assertEqual(snapshot["credential_payload"], FAKE_CREDENTIAL_PAYLOAD)

    def test_backup_refuses_to_overwrite_without_force(self):
        args = types.SimpleNamespace(claude_home=self.claude_home, home_dir=self.home, name="work", force=False, yes=True)
        manage_auth_profiles.command_backup(args)
        with self.assertRaises(ValueError):
            manage_auth_profiles.command_backup(args)
        args.force = True
        manage_auth_profiles.command_backup(args)  # does not raise

    def test_backup_and_list_round_trip_without_leaking_secrets(self):
        args = types.SimpleNamespace(claude_home=self.claude_home, home_dir=self.home, name="work", force=False, yes=True)
        manage_auth_profiles.command_backup(args)
        profiles = manage_auth_profiles.discover_profiles(claude_home=self.claude_home, home_dir=self.home)
        self.assertEqual([profile["alias"] for profile in profiles], ["active", "work"])
        backup_profile = profiles[1]
        self.assertEqual(backup_profile["store"], "backup-file")
        self.assertEqual(backup_profile["email"], "person@example.com")
        self.assertFalse(backup_profile["active"])
        self.assert_no_secret_strings(profiles)

    def test_switch_is_dry_run_by_default_and_requires_explicit_yes(self):
        backup_args = types.SimpleNamespace(claude_home=self.claude_home, home_dir=self.home, name="work", force=False, yes=True)
        manage_auth_profiles.command_backup(backup_args)
        write_json(self.claude_home / ".credentials.json", FAKE_EXPIRED_PAYLOAD)  # active now differs

        switch_args = types.SimpleNamespace(claude_home=self.claude_home, home_dir=self.home, selector="work", yes=False)
        manage_auth_profiles.command_switch(switch_args)
        still_active = json.loads((self.claude_home / ".credentials.json").read_text(encoding="utf-8"))
        self.assertEqual(still_active, FAKE_EXPIRED_PAYLOAD, "dry-run switch must not modify the active store")

        switch_args.yes = True
        manage_auth_profiles.command_switch(switch_args)
        switched = json.loads((self.claude_home / ".credentials.json").read_text(encoding="utf-8"))
        self.assertEqual(switched, FAKE_CREDENTIAL_PAYLOAD)

    def test_switch_rejects_unknown_selector(self):
        switch_args = types.SimpleNamespace(claude_home=self.claude_home, home_dir=self.home, selector="does-not-exist", yes=True)
        with self.assertRaises(ValueError):
            manage_auth_profiles.command_switch(switch_args)

    def test_switch_rejects_switching_to_active_alias(self):
        switch_args = types.SimpleNamespace(claude_home=self.claude_home, home_dir=self.home, selector="active", yes=True)
        with self.assertRaises(ValueError):
            manage_auth_profiles.command_switch(switch_args)

    def test_import_wraps_a_raw_credential_file_and_is_dry_run_by_default(self):
        source = self.home / "external-export.json"
        write_json(source, FAKE_EXPIRED_PAYLOAD)
        target = self.claude_home / "credentials_imported.json"
        args = types.SimpleNamespace(claude_home=self.claude_home, home_dir=self.home, source=source, name="imported", force=False, yes=False)
        manage_auth_profiles.command_import(args)
        self.assertFalse(target.exists())
        args.yes = True
        manage_auth_profiles.command_import(args)
        snapshot = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(snapshot["credential_payload"], FAKE_EXPIRED_PAYLOAD)
        self.assertEqual(snapshot["backed_up_from_store"], "import")

    def test_status_command_reports_active_only(self):
        args = types.SimpleNamespace(claude_home=self.claude_home, home_dir=self.home, json=True)
        with patch("builtins.print") as mock_print:
            manage_auth_profiles.command_status(args)
        printed = json.loads(mock_print.call_args[0][0])
        self.assertEqual(printed["alias"], "active")
        self.assert_no_secret_strings(printed)


class KeychainBackedStoreTest(unittest.TestCase, NoSecretLeakMixin):
    """Exercises the macOS Keychain fallback path. The `security` CLI boundary is always
    mocked via manage_auth_profiles.run_security_command -- the real Keychain is never
    touched by this test."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.home = Path(self.tempdir.name)
        self.claude_home = self.home / ".claude"
        self.claude_home.mkdir()
        # No .credentials.json file -> file store detection must fall through to keychain.
        write_json(self.home / ".claude.json", FAKE_IDENTITY)

    def fake_security_read(self, payload):
        def _run(args, timeout=10):
            self.assertIn("find-generic-password", args)
            self.assertIn(manage_auth_profiles.KEYCHAIN_SERVICE, args)
            result = types.SimpleNamespace()
            if payload is None:
                result.returncode = 44  # security's "item not found" code
                result.stdout = ""
            else:
                result.returncode = 0
                result.stdout = json.dumps(payload)
            return result

        return _run

    def test_discover_profiles_falls_back_to_keychain(self):
        with patch.object(manage_auth_profiles, "run_security_command", side_effect=self.fake_security_read(FAKE_CREDENTIAL_PAYLOAD)):
            profiles = manage_auth_profiles.discover_profiles(claude_home=self.claude_home, home_dir=self.home)
        self.assertEqual(profiles[0]["store"], "keychain")
        self.assertEqual(profiles[0]["email"], "person@example.com")
        self.assert_no_secret_strings(profiles)

    def test_no_file_and_no_keychain_item_reports_none(self):
        with patch.object(manage_auth_profiles, "run_security_command", side_effect=self.fake_security_read(None)):
            profiles = manage_auth_profiles.discover_profiles(claude_home=self.claude_home, home_dir=self.home)
        self.assertEqual(profiles[0]["store"], "none")

    def test_switch_writes_through_keychain_when_keychain_is_the_active_store(self):
        backup_target = self.claude_home / "credentials_work.json"
        write_json(backup_target, {
            "credential_payload": FAKE_CREDENTIAL_PAYLOAD,
            "identity_snapshot": {"email": "person@example.com"},
            "backed_up_from_store": "keychain",
            "backed_up_at": "2026-01-01T00:00:00+00:00",
        })
        write_calls = []

        def fake_write(payload, service=manage_auth_profiles.KEYCHAIN_SERVICE, account=None):
            write_calls.append((payload, service))
            return True

        with (
            patch.object(manage_auth_profiles, "run_security_command", side_effect=self.fake_security_read(FAKE_EXPIRED_PAYLOAD)),
            patch.object(manage_auth_profiles, "write_keychain_credentials", side_effect=fake_write),
        ):
            switch_args = types.SimpleNamespace(claude_home=self.claude_home, home_dir=self.home, selector="work", yes=True)
            manage_auth_profiles.command_switch(switch_args)

        self.assertFalse((self.claude_home / ".credentials.json").exists(), "keychain-active switch must not create a file store")
        self.assertEqual(len(write_calls), 1)
        self.assertEqual(write_calls[0][0], FAKE_CREDENTIAL_PAYLOAD)

    def test_write_keychain_credentials_never_receives_or_prints_secrets_in_its_own_call(self):
        captured = {}

        def fake_run_security(args, timeout=10):
            captured["args"] = args
            return types.SimpleNamespace(returncode=0, stdout="")

        with patch.object(manage_auth_profiles, "run_security_command", side_effect=fake_run_security):
            ok = manage_auth_profiles.write_keychain_credentials(FAKE_CREDENTIAL_PAYLOAD, account="tester")
        self.assertTrue(ok)
        self.assertIn("-a", captured["args"])
        self.assertIn("tester", captured["args"])
        self.assertIn(manage_auth_profiles.KEYCHAIN_SERVICE, captured["args"])


class SanitizationHelpersTest(unittest.TestCase):
    def test_extract_oauth_summary_never_includes_token_values(self):
        summary = manage_auth_profiles.extract_oauth_summary(FAKE_CREDENTIAL_PAYLOAD)
        self.assertNotIn("accessToken", summary)
        self.assertNotIn("refreshToken", summary)
        self.assertTrue(summary["has_access_token"])
        self.assertEqual(summary["scope_count"], 2)

    def test_extract_oauth_summary_handles_missing_payload(self):
        summary = manage_auth_profiles.extract_oauth_summary(None)
        self.assertFalse(summary["has_access_token"])
        self.assertIsNone(summary["expired"])

    def test_assert_no_secret_leak_raises_on_injected_secret_field(self):
        with self.assertRaises(AssertionError):
            manage_auth_profiles.assert_no_secret_leak({"accessToken": "leak"})

    def test_normalize_alias_slug_rejects_reserved_and_empty_names(self):
        with self.assertRaises(ValueError):
            manage_auth_profiles.normalize_alias_slug("")
        with self.assertRaises(ValueError):
            manage_auth_profiles.normalize_alias_slug("active")
        self.assertEqual(manage_auth_profiles.normalize_alias_slug("Work Laptop!"), "work_laptop")


if __name__ == "__main__":
    unittest.main()
