"""Open the GitHub 'new release' form prefilled from the changelog.

A manual alternative to the automated ``release.yml`` flow: given a version,
it reads that version's notes from ``docs/history/wspkit.md`` and opens the
GitHub release form with the tag, title, and body filled in. It creates no
tags and publishes nothing -- that is ``release.py`` and the workflow.

Usage:  hatch run release:github <version>
"""

from __future__ import annotations

import argparse
import webbrowser
from urllib.parse import urlencode

import changelog

PROJECT = "Wspkit"
REPO_SLUG = "pythonomenology/wspkit"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="version to release, e.g. 0.0.1")
    args = parser.parse_args()

    version = args.version
    tag = f"v{version}"
    params = urlencode(
        {
            "tag": tag,
            "title": f"{PROJECT} v{version}",
            "body": changelog.extract(version),
        }
    )
    url = f"https://github.com/{REPO_SLUG}/releases/new?{params}"
    print(f"opening {url}")
    webbrowser.open_new_tab(url)


if __name__ == "__main__":
    main()
