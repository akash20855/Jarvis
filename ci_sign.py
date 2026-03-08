"""
JARVIS · ci_sign.py
Signs release APK using a keystore stored as GitHub Secret.
"""
import os
import base64
import subprocess
import argparse
from pathlib import Path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk",           required=True)
    parser.add_argument("--keystore-b64",  required=True)
    parser.add_argument("--key-alias",     required=True)
    parser.add_argument("--key-password",  required=True)
    args = parser.parse_args()

    # Decode keystore from base64 secret
    ks_path = Path("/tmp/jarvis.keystore")
    ks_path.write_bytes(base64.b64decode(args.keystore_b64))

    apk = Path(args.apk)

    # Sign with apksigner
    result = subprocess.run([
        "apksigner", "sign",
        "--ks",           str(ks_path),
        "--ks-key-alias", args.key_alias,
        "--ks-pass",      f"pass:{args.key_password}",
        "--key-pass",     f"pass:{args.key_password}",
        str(apk)
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✓ APK signed: {apk.name}")
    else:
        print(f"✗ Signing failed: {result.stderr}")
        # Don't fail the build — unsigned debug still works
