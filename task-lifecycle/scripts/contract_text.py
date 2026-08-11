# Shared contract-text normalization for the skill's own checkers. Supported platforms: macOS, Linux, Windows.
# A rule only counts where it is IN FORCE, so HTML comments, <details> blocks (closed or not) and fenced examples
# (backtick or tilde, any width, nested) are removed before any pattern is matched against a contract file.
import re

html_comment = re.compile(r"<!--.*?-->", re.DOTALL)
# Anchored to the start of a line so that merely NAMING `<details>` in prose cannot swallow the rest of the file;
# an unclosed block that really does open a line still runs to the end, which is what a reader would see.
details_block = re.compile(r"^[ \t]*<details\b.*?(?:</details\s*>|\Z)", re.DOTALL | re.IGNORECASE | re.MULTILINE)


def strip_inert_blocks(text):
    surviving_lines, open_fence = [], ""
    for line in details_block.sub("", html_comment.sub("", text)).splitlines():
        marker = line.lstrip()
        fence_character = marker[0] if marker[:1] in ("`", "~") else ""
        run = marker[:len(marker) - len(marker.lstrip(fence_character))] if fence_character else ""
        info_string = marker[len(run):]
        # An inline span such as ```json``` is not a fence opener; a real opener carries no backtick in its info string.
        if not open_fence and len(run) >= 3 and "`" not in info_string:
            open_fence = run
        elif open_fence and run[:1] == open_fence[:1] and len(run) >= len(open_fence) and not info_string.strip():
            open_fence = ""
        elif not open_fence:
            surviving_lines.append(line)
    return "\n".join(surviving_lines)


def in_force_text(path):
    return strip_inert_blocks(path.read_text(encoding="utf-8", errors="replace"))
