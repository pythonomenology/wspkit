"""Read and roll the Keep a Changelog file at ``docs/history/wspkit.md``.

Two subcommands:

* ``extract <version>`` prints the notes for one released version to stdout.
  The release workflow redirects this into ``--notes-file`` so the GitHub
  release body is the changelog section for the tag.
* ``release <version> [--date YYYY-MM-DD]`` moves everything under
  ``## Unreleased`` into a new ``## [version] - date`` section and leaves
  ``Unreleased`` empty, so a release captures exactly what was pending.

Run via ``hatch run release:notes <version>`` / ``hatch run release:changelog``.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path
from typing import NoReturn

CHANGELOG = Path(__file__).resolve().parents[1] / "docs" / "history" / "wspkit.md"

_UNRELEASED = "## Unreleased"
_SECTION = re.compile(r"^## ", re.MULTILINE)


def _read() -> str:
    try:
        return CHANGELOG.read_text(encoding="utf-8")
    except OSError as exc:
        _fail(f"cannot read {CHANGELOG}: {exc}")


def _fail(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _section_bounds(text: str, heading: str) -> tuple[int, int]:
    """Return the (start, end) offsets of the body under ``heading``.

    ``start`` is just after the heading line; ``end`` is the start of the
    next ``## `` heading (or end of file). Raises if the heading is absent.
    """
    marker = text.find(heading)
    if marker == -1:
        _fail(f"no {heading!r} section in {CHANGELOG.name}")
    body_start = text.index("\n", marker) + 1
    nxt = _SECTION.search(text, body_start)
    body_end = nxt.start() if nxt else len(text)
    return body_start, body_end


def extract(version: str) -> str:
    """Return the notes for ``version`` (without the heading line)."""
    text = _read()
    body_start, body_end = _section_bounds(text, f"## [{version}]")
    notes = text[body_start:body_end].strip("\n")
    if not notes:
        _fail(f"version {version} has an empty changelog section")
    return notes


def release(version: str, date: str) -> None:
    """Move the ``Unreleased`` body into a dated ``version`` section."""
    text = _read()
    if f"## [{version}]" in text:
        _fail(f"version {version} already has a changelog section")
    body_start, body_end = _section_bounds(text, _UNRELEASED)
    pending = text[body_start:body_end].strip("\n")
    if not pending:
        _fail("nothing under 'Unreleased' to release")
    new_block = f"{_UNRELEASED}\n\n## [{version}] - {date}\n\n{pending}\n"
    updated = text[: text.find(_UNRELEASED)] + new_block + text[body_end:]
    CHANGELOG.write_text(updated, encoding="utf-8")
    print(f"rolled 'Unreleased' into [{version}] - {date}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    extract_cmd = sub.add_parser("extract", help="print one version's notes")
    extract_cmd.add_argument("version")

    release_cmd = sub.add_parser("release", help="roll Unreleased into a version")
    release_cmd.add_argument("version")
    release_cmd.add_argument(
        "--date",
        default=datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d"),
        help="release date (defaults to today, UTC)",
    )

    args = parser.parse_args()
    if args.command == "extract":
        print(extract(args.version))
    else:
        release(args.version, args.date)


if __name__ == "__main__":
    main()
