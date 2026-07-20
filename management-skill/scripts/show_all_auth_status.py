#!/usr/bin/env python3
"""Show sanitized Claude Code credential status for the active store and every saved backup.

Optionally switches to a named backup first, but only when `--yes` is also given --
matching `manage_auth_profiles.py switch`'s dry-run-by-default, explicit-confirmation
contract. Never prints token values.
"""

import argparse
import importlib.util
import sys
from pathlib import Path


def load_manager():
    script_dir = Path(__file__).resolve().parent
    manager_path = script_dir / "manage_auth_profiles.py"
    spec = importlib.util.spec_from_file_location("manage_auth_profiles", manager_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_parser():
    parser = argparse.ArgumentParser(
        description="Show sanitized status for every saved Claude Code credential profile, optionally switching first."
    )
    parser.add_argument("selector", nargs="?", help="Optional backup alias or email to switch to before showing status")
    parser.add_argument("--yes", action="store_true", help="Explicit confirmation required to actually switch before showing status")
    parser.add_argument("--claude-home", type=Path, default=None, help="Path to ~/.claude (default: ~/.claude)")
    parser.add_argument("--home-dir", type=Path, default=None, help="Path containing .claude.json (default: home directory)")
    return parser


def main():
    args = build_parser().parse_args()
    module = load_manager()
    claude_home = (args.claude_home or module.default_claude_home()).expanduser().resolve()
    home_dir = (args.home_dir or module.default_home_dir()).expanduser().resolve()

    try:
        if args.selector:
            switch_args = argparse.Namespace(
                claude_home=claude_home,
                home_dir=home_dir,
                selector=args.selector,
                yes=args.yes,
            )
            module.command_switch(switch_args)
            if not args.yes:
                print()

        profiles = module.discover_profiles(claude_home=claude_home, home_dir=home_dir)
        module.print_profiles(profiles)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
