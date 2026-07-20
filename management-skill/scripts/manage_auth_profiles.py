#!/usr/bin/env python3
"""Inspect and switch saved Claude Code credential profiles.

Claude Code edition of the Codex auth-profile manager. Codex kept every account as a
standalone ``~/.codex/auth_<name>.json`` file containing a self-describing JWT
``id_token``. Claude Code does not: it keeps exactly one active credential set, stored
either as the file ``~/.claude/.credentials.json`` (when present) or, on macOS, in the
Keychain under the generic-password service ``"Claude Code-credentials"`` -- read and
written through the ``security`` CLI. Account identity (email, organization) is not
embedded in the Claude OAuth token; it lives separately in ``~/.claude.json``.

To still support multiple named accounts, this script keeps local, explicit backup
snapshots at ``~/.claude/credentials_<name>.json``. Each snapshot bundles the credential
payload together with the identity fields that were active in ``~/.claude.json`` at
backup time, so a later ``list``/``status`` can show whose account a backup belongs to.

Never prints ``accessToken``/``refreshToken`` values. Switching the active store is
dry-run by default and requires ``--yes`` to actually write.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

KEYCHAIN_SERVICE = "Claude Code-credentials"
CREDENTIALS_FILENAME = ".credentials.json"
BACKUP_PREFIX = "credentials_"
IDENTITY_FILENAME = ".claude.json"
SECRET_FIELDS = ("accessToken", "refreshToken")


# ---------------------------------------------------------------------------
# Low-level, mockable boundaries: filesystem JSON I/O and the `security` CLI.
# ---------------------------------------------------------------------------


def load_json(path):
    try:
        with Path(path).open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def write_json_atomic(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_security_command(args, timeout=10):
    """Thin, mockable wrapper around the macOS `security` CLI."""
    return subprocess.run(["security", *args], capture_output=True, text=True, timeout=timeout)


def read_keychain_credentials(service=KEYCHAIN_SERVICE, account=None):
    args = ["find-generic-password", "-s", service, "-w"]
    if account:
        args[1:1] = ["-a", account]
    try:
        result = run_security_command(args)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout.strip())
    except ValueError:
        return None


def write_keychain_credentials(payload, service=KEYCHAIN_SERVICE, account=None):
    account = account or default_keychain_account()
    serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    args = ["add-generic-password", "-U", "-s", service, "-a", account, "-w", serialized]
    try:
        result = run_security_command(args)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def default_keychain_account():
    try:
        import getpass

        return getpass.getuser()
    except Exception:
        return "claude"


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def default_claude_home():
    return Path.home() / ".claude"


def default_home_dir():
    return Path.home()


def credentials_file_path(claude_home):
    return Path(claude_home) / CREDENTIALS_FILENAME


def identity_file_path(home_dir):
    return Path(home_dir) / IDENTITY_FILENAME


def backup_path_for(claude_home, slug):
    return Path(claude_home) / f"{BACKUP_PREFIX}{slug}.json"


def list_named_backups(claude_home):
    return sorted(Path(claude_home).glob(f"{BACKUP_PREFIX}*.json"))


def backup_alias(path):
    return Path(path).stem[len(BACKUP_PREFIX):]


def normalize_alias_slug(name):
    raw = (name or "").strip()
    if not raw:
        raise ValueError("Profile name cannot be empty.")
    slug = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
    if not slug:
        raise ValueError("Profile name must contain at least one letter or digit.")
    if slug == "active":
        raise ValueError("Profile name 'active' is reserved for the live credential store.")
    return slug


# ---------------------------------------------------------------------------
# Active-store detection and sanitized summaries
# ---------------------------------------------------------------------------


def detect_active_store(claude_home):
    if credentials_file_path(claude_home).exists():
        return "file"
    if read_keychain_credentials() is not None:
        return "keychain"
    return "none"


def load_active_credentials(claude_home):
    file_path = credentials_file_path(claude_home)
    if file_path.exists():
        return {"store": "file", "payload": load_json(file_path), "source": str(file_path)}
    keychain_payload = read_keychain_credentials()
    if keychain_payload is not None:
        return {"store": "keychain", "payload": keychain_payload, "source": f"keychain:{KEYCHAIN_SERVICE}"}
    return {"store": "none", "payload": None, "source": None}


def epoch_ms_to_local_text(value):
    if value is None:
        return None
    try:
        parsed = datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).astimezone()
    except (OSError, OverflowError, ValueError, TypeError):
        return None
    return parsed.strftime("%Y-%m-%d %H:%M:%S %Z")


def is_epoch_ms_expired(value, now=None):
    if value is None:
        return None
    now = now or datetime.now(timezone.utc)
    try:
        parsed = datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
    except (OSError, OverflowError, ValueError, TypeError):
        return None
    return parsed <= now


def extract_oauth_summary(credential_payload):
    """Sanitize a raw `{"claudeAiOauth": {...}}` payload. Never returns token values."""
    oauth = (credential_payload or {}).get("claudeAiOauth") or {}
    expires_at = oauth.get("expiresAt")
    return {
        "has_access_token": bool(oauth.get("accessToken")),
        "has_refresh_token": bool(oauth.get("refreshToken")),
        "expires_at_text": epoch_ms_to_local_text(expires_at),
        "expired": is_epoch_ms_expired(expires_at),
        "refresh_token_expires_at_text": epoch_ms_to_local_text(oauth.get("refreshTokenExpiresAt")),
        "subscription_type": oauth.get("subscriptionType"),
        "rate_limit_tier": oauth.get("rateLimitTier"),
        "scope_count": len(oauth.get("scopes") or []),
    }


def load_identity(home_dir):
    data = load_json(identity_file_path(home_dir)) or {}
    oauth_account = data.get("oauthAccount") or {}
    return {
        "user_id": data.get("userID"),
        "email": oauth_account.get("emailAddress"),
        "organization_name": oauth_account.get("organizationName"),
        "organization_uuid": oauth_account.get("organizationUuid"),
        "account_uuid": oauth_account.get("accountUuid"),
        "seat_tier": oauth_account.get("seatTier"),
        "billing_type": oauth_account.get("billingType"),
    }


def assert_no_secret_leak(sanitized):
    """Defense in depth: fail loudly if a sanitized dict ever grows a secret field."""
    for field in SECRET_FIELDS:
        if field in sanitized:
            raise AssertionError(f"refusing to emit secret field: {field}")
    return sanitized


# ---------------------------------------------------------------------------
# Profile discovery
# ---------------------------------------------------------------------------


def build_selector_variants(*values):
    variants = []
    for value in values:
        raw = (value or "").strip().lower()
        if raw:
            variants.append(raw)
    seen = set()
    unique = []
    for value in variants:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def build_active_profile_entry(claude_home, home_dir):
    active = load_active_credentials(claude_home)
    identity = load_identity(home_dir)
    entry = {
        "alias": "active",
        "store": active["store"],
        "source": active["source"],
        "active": True,
        **identity,
        **extract_oauth_summary(active["payload"]),
    }
    entry["selectors"] = build_selector_variants("active", entry.get("email"))
    return assert_no_secret_leak(entry)


def build_backup_profile_entry(path):
    alias = backup_alias(path)
    snapshot = load_json(path) or {}
    credential_payload = snapshot.get("credential_payload", snapshot)
    identity = snapshot.get("identity_snapshot") or {}
    entry = {
        "alias": alias,
        "store": "backup-file",
        "source": str(path),
        "active": False,
        "backed_up_at": snapshot.get("backed_up_at"),
        "backed_up_from_store": snapshot.get("backed_up_from_store"),
        "user_id": identity.get("user_id"),
        "email": identity.get("email"),
        "organization_name": identity.get("organization_name"),
        "organization_uuid": identity.get("organization_uuid"),
        "account_uuid": identity.get("account_uuid"),
        "seat_tier": identity.get("seat_tier"),
        "billing_type": identity.get("billing_type"),
        **extract_oauth_summary(credential_payload),
    }
    entry["selectors"] = build_selector_variants(alias, entry.get("email"))
    return assert_no_secret_leak(entry)


def discover_profiles(claude_home=None, home_dir=None):
    claude_home = Path(claude_home) if claude_home else default_claude_home()
    home_dir = Path(home_dir) if home_dir else default_home_dir()
    profiles = [build_active_profile_entry(claude_home, home_dir)]
    for path in list_named_backups(claude_home):
        profiles.append(build_backup_profile_entry(path))
    return profiles


def resolve_profile(profiles, selector):
    normalized = (selector or "").strip().lower()
    matches = [profile for profile in profiles if normalized in profile["selectors"]]
    if not matches:
        raise ValueError(f"No credential profile matched '{selector}'.")
    if len(matches) > 1:
        options = ", ".join(profile["alias"] for profile in matches)
        raise ValueError(f"Selector '{selector}' is ambiguous. Use one of: {options}")
    return matches[0]


# ---------------------------------------------------------------------------
# Sanitized console output
# ---------------------------------------------------------------------------


def status_label(profile):
    if profile["store"] in ("none",):
        return "NO CREDENTIALS"
    if profile.get("expired"):
        return "ACTIVE EXPIRED" if profile["active"] else "EXPIRED"
    if not profile.get("has_access_token"):
        return "ACTIVE INCOMPLETE" if profile["active"] else "INCOMPLETE"
    return "ACTIVE" if profile["active"] else "SAVED"


def format_profile_line(profile):
    segments = [
        f"{profile['alias']}",
        f"({status_label(profile)})",
        f"store={profile['store']}",
        f"email={profile.get('email') or 'unknown'}",
        f"org={profile.get('organization_name') or 'unknown'}",
        f"plan={profile.get('subscription_type') or 'unknown'}",
    ]
    if profile.get("expires_at_text"):
        segments.append(f"token-expires={profile['expires_at_text']}")
    if profile.get("backed_up_at"):
        segments.append(f"backed-up-at={profile['backed_up_at']}")
    return "  ".join(segments)


def print_profiles(profiles):
    for profile in profiles:
        print(format_profile_line(profile))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def command_list(args):
    profiles = discover_profiles(claude_home=args.claude_home, home_dir=args.home_dir)
    if args.json:
        print(json.dumps({"claude_home": str(args.claude_home), "profiles": profiles}, indent=2, ensure_ascii=False))
        return
    print_profiles(profiles)


def command_status(args):
    profiles = discover_profiles(claude_home=args.claude_home, home_dir=args.home_dir)
    active_profile = next(profile for profile in profiles if profile["active"])
    if args.json:
        print(json.dumps(active_profile, indent=2, ensure_ascii=False))
        return
    print(format_profile_line(active_profile))


def command_backup(args):
    active = load_active_credentials(args.claude_home)
    if active["store"] == "none":
        raise ValueError(
            "No active Claude Code credentials found "
            f"(checked {credentials_file_path(args.claude_home)} and Keychain item '{KEYCHAIN_SERVICE}')."
        )
    slug = normalize_alias_slug(args.name)
    target = backup_path_for(args.claude_home, slug)
    if target.exists() and not args.force:
        raise ValueError(f"Backup already exists: {target.name}. Use --force to overwrite it.")
    snapshot = {
        "credential_payload": active["payload"],
        "identity_snapshot": load_identity(args.home_dir),
        "backed_up_from_store": active["store"],
        "backed_up_at": datetime.now(timezone.utc).isoformat(),
    }
    if not args.yes:
        print(f"Would back up active {active['store']} credentials to {target}")
        return
    write_json_atomic(target, snapshot)
    print(f"Saved backup: {target}")


def command_import(args):
    source = args.source.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"Source credential file not found: {source}")
    payload = load_json(source)
    if payload is None:
        raise ValueError(f"Source file is not valid JSON: {source}")
    slug = normalize_alias_slug(args.name)
    target = backup_path_for(args.claude_home, slug)
    if target.exists() and not args.force:
        raise ValueError(f"Backup already exists: {target.name}. Use --force to overwrite it.")
    if "credential_payload" in payload:
        snapshot = payload
    else:
        snapshot = {
            "credential_payload": payload,
            "identity_snapshot": {},
            "backed_up_from_store": "import",
            "backed_up_at": datetime.now(timezone.utc).isoformat(),
        }
    if not args.yes:
        print(f"Would import {source} as profile '{slug}' ({target})")
        return
    write_json_atomic(target, snapshot)
    print(f"Imported profile: {target}")


def command_switch(args):
    profiles = discover_profiles(claude_home=args.claude_home, home_dir=args.home_dir)
    profile = resolve_profile(profiles, args.selector)
    if profile["store"] != "backup-file":
        raise ValueError("Can only switch to a saved backup profile (see `list` for aliases).")
    snapshot = load_json(Path(profile["source"])) or {}
    credential_payload = snapshot.get("credential_payload", snapshot)
    target_store = detect_active_store(args.claude_home)
    if target_store == "none":
        target_store = "file"
    if target_store == "file":
        destination = credentials_file_path(args.claude_home)
        description = f"Would write '{profile['alias']}' credentials to {destination}"
    else:
        destination = f"keychain:{KEYCHAIN_SERVICE}"
        description = f"Would update Keychain item '{KEYCHAIN_SERVICE}' with '{profile['alias']}' credentials"
    if not args.yes:
        print(description)
        print("Re-run with --yes to actually switch. Identity fields in ~/.claude.json are not touched.")
        return
    if target_store == "file":
        write_json_atomic(destination, credential_payload)
    else:
        if not write_keychain_credentials(credential_payload):
            raise ValueError(f"Failed to update Keychain item '{KEYCHAIN_SERVICE}'.")
    print(f"Switched active credentials to '{profile['alias']}' ({target_store}).")


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(description="Inspect and switch saved Claude Code credential profiles.")
    parser.add_argument("--claude-home", type=Path, default=default_claude_home(), help="Path to ~/.claude (default: ~/.claude)")
    parser.add_argument("--home-dir", type=Path, default=default_home_dir(), help="Path containing .claude.json (default: home directory)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List the active credential store and saved backup profiles")
    list_parser.add_argument("--json", action="store_true", help="Emit sanitized JSON output")
    list_parser.set_defaults(func=command_list)

    status_parser = subparsers.add_parser("status", help="Show sanitized status for the active credential store only")
    status_parser.add_argument("--json", action="store_true", help="Emit sanitized JSON output")
    status_parser.set_defaults(func=command_status)

    backup_parser = subparsers.add_parser("backup", help="Snapshot the active credentials into ~/.claude/credentials_<name>.json")
    backup_parser.add_argument("name", help="Backup name, for example 'work' or 'personal'")
    backup_parser.add_argument("--force", action="store_true", help="Overwrite an existing backup with the same name")
    backup_parser.add_argument("--yes", action="store_true", help="Actually write the backup (default: dry-run)")
    backup_parser.set_defaults(func=command_backup)

    import_parser = subparsers.add_parser("import", help="Import an external credential file as a saved backup profile")
    import_parser.add_argument("source", type=Path, help="Path to a credential JSON file to import")
    import_parser.add_argument("name", help="Backup name to store it under")
    import_parser.add_argument("--force", action="store_true", help="Overwrite an existing backup with the same name")
    import_parser.add_argument("--yes", action="store_true", help="Actually write the backup (default: dry-run)")
    import_parser.set_defaults(func=command_import)

    switch_parser = subparsers.add_parser("switch", help="Switch the active credential store to a saved backup profile")
    switch_parser.add_argument("selector", help="Backup alias or email to switch to")
    switch_parser.add_argument("--yes", action="store_true", help="Actually switch (default: dry-run, requires explicit confirmation)")
    switch_parser.set_defaults(func=command_switch)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.claude_home = args.claude_home.expanduser().resolve()
    args.home_dir = args.home_dir.expanduser().resolve()
    try:
        args.func(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
