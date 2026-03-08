"""
JARVIS · ci_manifest.py
Generates version.json manifest for update server.
"""
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--apk",     required=True)
    args = parser.parse_args()

    apk   = Path(args.apk)
    sha   = hashlib.sha256(apk.read_bytes()).hexdigest()
    size  = round(apk.stat().st_size / 1024 / 1024, 1)

    manifest = {
        "version":   args.version,
        "built_at":  datetime.utcnow().isoformat() + "Z",
        "apk_url":   f"{{UPDATE_SERVER}}/apk/{apk.name}",
        "sha256":    sha,
        "size_mb":   size,
        "notes":     f"Auto-built v{args.version}",
        "min_android": 21,
    }

    out = Path("dist/version.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2))
    print(f"Manifest: {out}")
    print(f"  SHA256: {sha[:16]}...")
    print(f"  Size:   {size}MB")
