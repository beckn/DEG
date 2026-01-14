#!/usr/bin/env python3
"""Check for broken links in markdown files.

This script parses markdown files for links and reports any that are broken:
- Relative links (starting with ./ or ../) - resolved relative to the markdown file
- Root-relative links (starting with /) - resolved relative to the repository root
- Absolute HTTP/HTTPS links - checked via HEAD request

Usage:
    python3 scripts/check_links.py path/to/file.md
    python3 scripts/check_links.py **/*.md
    python3 scripts/check_links.py --skip-http path/to/file.md
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
import urllib.error
import urllib.parse
import ssl
from pathlib import Path
from typing import NamedTuple
from concurrent.futures import ThreadPoolExecutor, as_completed


class BrokenLink(NamedTuple):
    """Represents a broken link found in a markdown file."""
    file: Path
    line: int
    link: str
    reason: str


# Regex patterns for different link types in markdown
# Matches [text](url) style links
MARKDOWN_LINK_PATTERN = re.compile(
    r'\[(?P<text>[^\]]*)\]\((?P<url>[^)]+)\)'
)

# Matches <a href="url"> style links
HTML_LINK_PATTERN = re.compile(
    r'<a\s+[^>]*href\s*=\s*["\'](?P<url>[^"\']+)["\'][^>]*>',
    re.IGNORECASE
)

# Matches reference-style links [text][ref] and [ref]: url
REFERENCE_LINK_DEF_PATTERN = re.compile(
    r'^\s*\[(?P<ref>[^\]]+)\]:\s*(?P<url>\S+)',
    re.MULTILINE
)

# HTTP request timeout in seconds
HTTP_TIMEOUT = 10


def find_repo_root(start_path: Path) -> Path:
    """Find the repository root by looking for .git directory."""
    current = start_path.resolve()
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    # If no .git found, use the starting path's parent
    return start_path.resolve().parent


def extract_links_with_lines(content: str) -> list[tuple[str, int]]:
    """Extract all links from markdown content with their line numbers."""
    links: list[tuple[str, int]] = []
    lines = content.split('\n')

    # Build a map of character position to line number
    char_to_line: dict[int, int] = {}
    pos = 0
    for line_num, line in enumerate(lines, start=1):
        for i in range(len(line) + 1):  # +1 for newline
            char_to_line[pos + i] = line_num
        pos += len(line) + 1

    # Find markdown-style links [text](url)
    for match in MARKDOWN_LINK_PATTERN.finditer(content):
        url = match.group('url')
        # Strip fragment identifiers for file existence checks
        url_without_fragment = url.split('#')[0]
        if url_without_fragment:  # Skip pure anchor links like #section
            line_num = char_to_line.get(match.start(), 1)
            links.append((url_without_fragment, line_num))

    # Find HTML-style links <a href="url">
    for match in HTML_LINK_PATTERN.finditer(content):
        url = match.group('url')
        url_without_fragment = url.split('#')[0]
        if url_without_fragment:
            line_num = char_to_line.get(match.start(), 1)
            links.append((url_without_fragment, line_num))

    # Find reference-style link definitions [ref]: url
    for match in REFERENCE_LINK_DEF_PATTERN.finditer(content):
        url = match.group('url')
        url_without_fragment = url.split('#')[0]
        if url_without_fragment:
            line_num = char_to_line.get(match.start(), 1)
            links.append((url_without_fragment, line_num))

    return links


def check_http_link(url: str) -> str | None:
    """Check if an HTTP/HTTPS URL is accessible. Returns error message or None if OK."""
    try:
        # Create a context that doesn't verify SSL (some sites have issues)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            url,
            method='HEAD',
            headers={'User-Agent': 'Mozilla/5.0 (compatible; LinkChecker/1.0)'}
        )
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT, context=ctx) as response:
            if response.status >= 400:
                return f"HTTP {response.status}"
        return None
    except urllib.error.HTTPError as e:
        # Some servers don't support HEAD, try GET
        if e.code == 405:
            try:
                req = urllib.request.Request(
                    url,
                    method='GET',
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; LinkChecker/1.0)'}
                )
                with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT, context=ctx) as response:
                    return None
            except Exception as e2:
                return str(e2)
        return f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return f"URL Error: {e.reason}"
    except Exception as e:
        return str(e)


def check_local_link(link: str, md_file: Path, repo_root: Path) -> str | None:
    """Check if a local file link exists. Returns error message or None if OK."""
    # Decode URL-encoded paths (e.g., %20 for spaces)
    decoded_link = urllib.parse.unquote(link)

    if decoded_link.startswith('/'):
        # Root-relative path
        target = repo_root / decoded_link.lstrip('/')
    else:
        # Relative to the markdown file's directory
        target = md_file.parent / decoded_link

    target = target.resolve()

    if not target.exists():
        return f"File not found: {target}"
    return None


def check_links_in_file(
    md_file: Path,
    repo_root: Path,
    skip_http: bool = False,
    http_links_to_check: list[tuple[str, Path, int]] | None = None
) -> list[BrokenLink]:
    """Check all links in a markdown file and return broken ones."""
    broken: list[BrokenLink] = []

    try:
        content = md_file.read_text(encoding='utf-8')
    except Exception as e:
        broken.append(BrokenLink(md_file, 0, str(md_file), f"Cannot read file: {e}"))
        return broken

    links = extract_links_with_lines(content)

    for link, line_num in links:
        # Skip mailto: and data: links
        if link.startswith(('mailto:', 'data:', 'tel:', 'javascript:')):
            continue

        # Skip links that are too long (likely base64 or binary data)
        if len(link) > 500:
            continue

        # Check HTTP/HTTPS links
        if link.startswith(('http://', 'https://')):
            if skip_http:
                continue
            if http_links_to_check is not None:
                # Collect for batch checking later
                http_links_to_check.append((link, md_file, line_num))
            continue

        # Check local links
        error = check_local_link(link, md_file, repo_root)
        if error:
            broken.append(BrokenLink(md_file, line_num, link, error))

    return broken


def check_http_links_parallel(
    http_links: list[tuple[str, Path, int]],
    max_workers: int = 10
) -> list[BrokenLink]:
    """Check HTTP links in parallel and return broken ones."""
    broken: list[BrokenLink] = []

    # Deduplicate URLs while keeping track of all occurrences
    url_to_occurrences: dict[str, list[tuple[Path, int]]] = {}
    for url, md_file, line_num in http_links:
        if url not in url_to_occurrences:
            url_to_occurrences[url] = []
        url_to_occurrences[url].append((md_file, line_num))

    unique_urls = list(url_to_occurrences.keys())

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(check_http_link, url): url
            for url in unique_urls
        }

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                error = future.result()
                if error:
                    for md_file, line_num in url_to_occurrences[url]:
                        broken.append(BrokenLink(md_file, line_num, url, error))
            except Exception as e:
                for md_file, line_num in url_to_occurrences[url]:
                    broken.append(BrokenLink(md_file, line_num, url, str(e)))

    return broken


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Check for broken links in markdown files.'
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='Markdown files to check (supports glob patterns)'
    )
    parser.add_argument(
        '--skip-http',
        action='store_true',
        help='Skip checking HTTP/HTTPS links (only check local file links)'
    )
    parser.add_argument(
        '--repo-root',
        type=Path,
        help='Repository root directory (default: auto-detect from .git)'
    )

    args = parser.parse_args()

    # Collect all markdown files
    md_files: list[Path] = []
    for pattern in args.files:
        path = Path(pattern)
        if path.exists():
            md_files.append(path)
        else:
            # Try as glob pattern
            md_files.extend(Path('.').glob(pattern))

    if not md_files:
        print("No markdown files found.", file=sys.stderr)
        return 1

    # Determine repo root
    if args.repo_root:
        repo_root = args.repo_root.resolve()
    else:
        repo_root = find_repo_root(md_files[0])

    print(f"Repository root: {repo_root}", file=sys.stderr)
    print(f"Checking {len(md_files)} file(s)...", file=sys.stderr)

    all_broken: list[BrokenLink] = []
    http_links_to_check: list[tuple[str, Path, int]] = []

    # Check local links in all files
    for md_file in md_files:
        broken = check_links_in_file(
            md_file.resolve(),
            repo_root,
            skip_http=args.skip_http,
            http_links_to_check=http_links_to_check if not args.skip_http else None
        )
        all_broken.extend(broken)

    # Check HTTP links in parallel
    if http_links_to_check:
        print(f"Checking {len(http_links_to_check)} HTTP link(s)...", file=sys.stderr)
        http_broken = check_http_links_parallel(http_links_to_check)
        all_broken.extend(http_broken)

    # Report results
    if all_broken:
        print(f"\n{'='*60}")
        print(f"BROKEN LINKS FOUND: {len(all_broken)}")
        print(f"{'='*60}\n")

        # Group by file
        by_file: dict[Path, list[BrokenLink]] = {}
        for bl in all_broken:
            if bl.file not in by_file:
                by_file[bl.file] = []
            by_file[bl.file].append(bl)

        for file, links in sorted(by_file.items()):
            rel_path = file.relative_to(repo_root) if file.is_relative_to(repo_root) else file
            print(f"\n{rel_path}:")
            for bl in sorted(links, key=lambda x: x.line):
                print(f"  Line {bl.line}: {bl.link}")
                print(f"    → {bl.reason}")

        return 1
    else:
        print("\nAll links OK!", file=sys.stderr)
        return 0


if __name__ == '__main__':
    sys.exit(main())
