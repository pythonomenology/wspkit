"""Prepare and trigger a wspkit release.

The version is derived from the git tag (hatch-vcs), so a release is just a
tag. This script does the surrounding bookkeeping:

1. Refuse unless on ``main`` with a clean working tree.
2. Roll ``docs/history/wspkit.md`` (``Unreleased`` -> ``[version] - date``)
   unless that section already exists, and confirm the notes are non-empty.
3. Commit the changelog, create annotated tag ``vX.Y.Z``, and push.

Pushing the tag triggers ``.github/workflows/release.yml``, which builds the
distributions, publishes to PyPI via Trusted Publishing, and creates the
immutable GitHub release with the changelog section as its notes.

Usage:  hatch run release:tag <version> [--date YYYY-MM-DD] [--no-push]
The bare minimum without this script is ``git tag vX.Y.Z && git push origin vX.Y.Z``.
"""

from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import changelog

REPO = Path(__file__).resolve().parents[1]


def _fail(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _git(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        ["git", *args],  # noqa: S607
        cwd=REPO,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return (result.stdout or "").strip()


def _preflight() -> None:
    branch = _git("rev-parse", "--abbrev-ref", "HEAD", capture=True)
    if branch != "main":
        _fail(f"releases are cut from 'main', not {branch!r}")
    if _git("status", "--porcelain", "--untracked-files=no", capture=True):
        _fail("tracked files have uncommitted changes; commit or stash first")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="version to release, e.g. 0.0.1")
    parser.add_argument("--date", default=None, help="release date YYYY-MM-DD (default: today, UTC)")
    parser.add_argument("--no-push", action="store_true", help="create the tag but do not push it")
    args = parser.parse_args()

    _preflight()

    version = args.version
    tag = f"v{version}"

    text = changelog.CHANGELOG.read_text(encoding="utf-8")
    if f"## [{version}]" not in text:
        date = args.date or datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d")
        changelog.release(version, date)
    changelog.extract(version)  # aborts if the section is missing or empty

    _git("add", "docs/history/wspkit.md")
    if _git("diff", "--cached", "--name-only", capture=True):
        _git("commit", "-m", f"Release {version}")
    _git("tag", "-a", tag, "-m", f"wspkit {version}")

    if args.no_push:
        print(f"created tag {tag}. Push it to release:  git push origin main {tag}")
        return

    _git("push", "origin", "main")
    _git("push", "origin", tag)
    print(f"pushed {tag}. release.yml will build, publish to PyPI, and cut the GitHub release.")


if __name__ == "__main__":
    main()
