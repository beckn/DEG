#!/usr/bin/env python3
"""Populate example JSON <details> blocks with referenced file contents. Avoid manual copy/pasting and potential errors.

To use this, embed following structure in your markdown file. 
You can use either absolute paths (from the repository root) or paths relative to the markdown file:

<details>
  <summary><a href="path/to/example.json">Example</a></summary>

  <!-- Existing content will be replaced -->
</details>

The script will match any <details> block where the href link contains "json" (case-insensitive).
Run this script to replace the content with the contents of the referenced JSON files.

from the repository root, run:
  python3 scripts/embed_example_json.py path/to/markdown_file.md
"""

from __future__ import annotations

import argparse
import re
import sys
from bisect import bisect_right
from pathlib import Path
from typing import Callable


# Regex pattern to match <details> blocks whose href link contains "json".
DETAILS_PATTERN = re.compile(
    r"(?P<header><details>\s*<summary>\s*<a\s+href=(?P<quote>[\"'])(?P<link>[^\"']*json[^\"']*)(?P=quote)[^>]*>"
    r"(?P<label>[^<]*)</a>\s*</summary>)"
    r"(?P<gap>\s*)"
    r"(?P<body>.*?)(?P<suffix></details>)",
    re.DOTALL | re.IGNORECASE,
)

CODE_FENCE_PATTERN = re.compile(r"```.*?```", re.DOTALL)


def build_code_fence_lookup(markdown_text: str) -> Callable[[int], bool]:
    """Return a callable that reports whether a position is inside a ``` code fence."""

    ranges = [match.span() for match in CODE_FENCE_PATTERN.finditer(markdown_text)]
    if not ranges:
        return lambda _: False

    starts = [start for start, _ in ranges]

    def _inside(position: int) -> bool:
        fence_index = bisect_right(starts, position) - 1
        if fence_index < 0:
            return False
        start, end = ranges[fence_index]
        return position < end

    return _inside


def replace_blocks(
    markdown_text: str,
    repo_root: Path,
    source_dir: Path,
    encoding: str,
) -> tuple[str, list[str]]:
    """Replace matching details blocks and return updated text with touched links."""

    touched_links: list[str] = []
    inside_code_fence = build_code_fence_lookup(markdown_text)

    def _replacement(match: re.Match[str]) -> str:
        if inside_code_fence(match.start()):
            return match.group(0)

        link = match.group("link").strip()
        if not link:
            raise SystemExit("Encountered details block with an empty link.")

        if link.startswith("/"):
            json_path = (repo_root / link.lstrip("/")).resolve()
        else:
            json_path = (source_dir / link).resolve()

        try:
            json_path.relative_to(repo_root)
        except ValueError as exc:
            raise SystemExit(f"Refusing to read outside repository: {json_path}") from exc

        try:
            json_text = json_path.read_text(encoding=encoding)
        except FileNotFoundError as exc:
            raise SystemExit(f"Referenced JSON file not found: {json_path}") from exc

        # if json_text.endswith("\n"):
        #     json_text = json_text.rstrip("\n")

        touched_links.append(link)
        replacement_body = f"\n```json\n{json_text}\n```\n"
        return f"{match.group('header')}\n{replacement_body}{match.group('suffix')}"

    updated_text, _ = DETAILS_PATTERN.subn(_replacement, markdown_text)
    return updated_text, touched_links


def main() -> None:
    """
    Command-line interface for embedding example JSON into markdown files.
    - Looks for <details> blocks whose summary is an anchor (<summary><a ...>...</a></summary>)
      where the href link contains the word "json" (case-insensitive).
      Replaces block content with JSON file contents.
    - json_file_link can be an absolute path (from repo root) or relative to the markdown file.
    - Supports dry-run mode to preview changes.

    Usage:
    python3 scripts/embed_example_json.py <markdown-file> [--dry-run] [--encoding <encoding>]

    e.g. 
    to preview changes without modifying the file:
    python3 scripts/embed_example_json.py docs/implementation-guides/v2/EV_Charging/EV_Charging.md --dry-run

    to update the file with embedded JSON:
    python3 scripts/embed_example_json.py docs/implementation-guides/v2/EV_Charging/EV_Charging.md 
    """

    parser = argparse.ArgumentParser(
        description="Inject referenced JSON into <details> blocks in a markdown file.",
        epilog=(
            "Example:\n"
            "  python3 scripts/embed_example_json.py "
            "docs/implementation-guides/v2/EV_Charging/EV_Charging.md"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("markdown", type=Path, help="Path to the markdown file to transform.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which blocks would change without modifying the file.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="File encoding for markdown and JSON files (default: %(default)s).",
    )

    args = parser.parse_args()

    markdown_path: Path = args.markdown
    if not markdown_path.is_file():
        raise SystemExit(f"Markdown file not found: {markdown_path}")

    repo_root = Path(__file__).resolve().parents[2]

    markdown_text = markdown_path.read_text(encoding=args.encoding)
    updated_text, touched_links = replace_blocks(
        markdown_text=markdown_text,
        repo_root=repo_root,
        source_dir=markdown_path.parent,
        encoding=args.encoding,
    )

    if not touched_links:
        print("No matching <details> blocks found.", file=sys.stderr)
        return

    if args.dry_run:
        print("Blocks to update:")
        for link in touched_links:
            print(f" - {link}")
        return

    markdown_path.write_text(updated_text, encoding=args.encoding)
    print(f"Updated {len(touched_links)} block(s).")


if __name__ == "__main__":
    main()
