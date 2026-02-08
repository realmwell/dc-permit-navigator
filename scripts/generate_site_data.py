#!/usr/bin/env python3
"""
Generate site/js/permits-data.js from data/permits.json.

This embeds the permit database directly into the frontend so the
directory page works without any API calls. Run after any changes
to permits.json.

Usage:
    python scripts/generate_site_data.py
"""

import json
from pathlib import Path


def main():
    permits_path = Path("data/permits.json")
    output_path = Path("site/js/permits-data.js")

    with open(permits_path) as f:
        data = json.load(f)

    # Write as a JS global variable
    js_content = f"// Auto-generated from data/permits.json — do not edit directly\nwindow.PERMITS_DATA = {json.dumps(data, indent=2)};\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(js_content)

    print(f"Generated {output_path} ({len(data['permits'])} permits, {output_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
