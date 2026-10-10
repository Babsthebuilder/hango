"""Command-line fixture validation for the one-command harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.fixtures.loader import validate_fixture_directory


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate HANGO synthetic fixtures")
    parser.add_argument("directory", type=Path, help="directory containing fixture JSON files")
    args = parser.parse_args()
    paths = validate_fixture_directory(args.directory)
    print(f"Validated {len(paths)} fixtures")


if __name__ == "__main__":
    main()
