#!/usr/bin/env python3
"""
scrub_notebooks_encoding.py: Utility to re-encode Jupyter notebooks as UTF-8.

This script finds .ipynb files (in args or under cwd), tests whether they are valid UTF-8,
and if not, decodes them as cp1252 and re-encodes as UTF-8. Optionally saves backups.
"""

import argparse
import sys
from pathlib import Path


def fix_file(path: Path, backup: bool = False) -> bool:
    """Return True if the file was re-encoded (had invalid UTF-8)."""
    raw = path.read_bytes()
    try:
        # If it decodes cleanly as UTF-8, nothing to do
        raw.decode('utf-8')
        return False
    except UnicodeDecodeError:
        # Decode cp1252 (Windows-1252) fallback, then write UTF-8
        text = raw.decode('cp1252')
        data = text.encode('utf-8')
        if backup:
            bak = path.with_suffix(path.suffix + '.bak')
            bak.write_bytes(raw)
        path.write_bytes(data)
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Re-encode Jupyter notebooks as UTF-8 (fallback from CP1252).'
    )
    parser.add_argument(
        'files', nargs='*', help='Paths to .ipynb files (default: all under cwd).'
    )
    parser.add_argument(
        '--backup', action='store_true',
        help='Save a .bak backup of original files before rewriting.'
    )
    args = parser.parse_args()

    if args.files:
        paths = [Path(f) for f in args.files]
    else:
        paths = list(Path('.').rglob('*.ipynb'))

    updated = []
    for path in paths:
        if not path.is_file():
            print(f"Skipping {path}: not a file", file=sys.stderr)
            continue
        try:
            if fix_file(path, backup=args.backup):
                updated.append(path)
                print(f"Re-encoded {path}")
        except Exception as e:
            print(f"Error processing {path}: {e}", file=sys.stderr)

    if updated:
        print(f"\nTotal notebooks re-encoded: {len(updated)}")
    else:
        print("All notebooks are valid UTF-8. No changes made.")


if __name__ == '__main__':
    main()