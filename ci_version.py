"""
JARVIS · ci_version.py
Version manager for CI/CD pipeline.
Run by GitHub Actions to bump and track versions.
"""

import json
import argparse
from pathlib import Path

VERSION_FILE = Path("version.json")


def load():
    if VERSION_FILE.exists():
        return json.loads(VERSION_FILE.read_text())
    return {"major": 1, "minor": 0, "patch": 0}


def save(v):
    VERSION_FILE.write_text(json.dumps(v, indent=2))


def to_string(v):
    return f"{v['major']}.{v['minor']}.{v['patch']}"


def bump(kind="patch"):
    v = load()
    if kind == "major":
        v["major"] += 1
        v["minor"]  = 0
        v["patch"]  = 0
    elif kind == "minor":
        v["minor"] += 1
        v["patch"]  = 0
    else:
        v["patch"] += 1
    save(v)
    return to_string(v)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bump", choices=["patch","minor","major"])
    parser.add_argument("--get",  action="store_true")
    args = parser.parse_args()

    if args.bump:
        print(bump(args.bump))
    elif args.get:
        print(to_string(load()))
