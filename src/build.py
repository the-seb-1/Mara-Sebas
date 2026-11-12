#!/usr/bin/env python3
"""
Bundle a tier-specific invitation page.

Reads the original bundled index.html, replaces the inner template with a
tier-stripped version of src/template.html, and writes the result to the
destination folder.

Tier-aware markers in src/template.html:

    <!-- TIER:2,3 -->...<!-- /TIER -->   kept only when tier in {2,3}
    <!-- TIER:3 -->...<!-- /TIER -->      kept only when tier == 3

The token __TIER__ is replaced with the integer tier value anywhere it appears
(used inside the inline Component script).

Usage:
    python3 src/build.py <tier:1|2|3> <output_dir>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_INDEX = ROOT / "Mara-Sebas" / "index.html"  # fallback — see resolve_original()
SOURCE_TEMPLATE = ROOT / "src" / "template.html"

TIER_BLOCK = re.compile(
    r"<!--\s*TIER:([\d,]+)\s*-->(.*?)<!--\s*/TIER\s*-->",
    re.DOTALL,
)
TEMPLATE_SCRIPT = re.compile(
    r'(<script type="__bundler/template">)(.*?)(</script>)',
    re.DOTALL,
)


def resolve_original() -> Path:
    """Find the original bundled index.html. Prefers repo root."""
    candidates = [ROOT / "index.html", ROOT / "Mara-Sebas" / "index.html"]
    for p in candidates:
        if p.exists():
            return p
    raise SystemExit(f"Cannot locate original index.html. Tried: {candidates}")


def strip_for_tier(template_html: str, tier: int) -> str:
    def keep(match: re.Match[str]) -> str:
        allowed = {int(t) for t in match.group(1).split(",")}
        return match.group(2) if tier in allowed else ""

    out = TIER_BLOCK.sub(keep, template_html)
    out = out.replace("__TIER__", str(tier))
    return out


def rebuild(tier: int, out_dir: Path) -> Path:
    original = resolve_original().read_text(encoding="utf-8")
    # Strip the file-end newline (editors add one, the original encoded
    # template had none) so a byte-identical round-trip stays possible.
    template_html = SOURCE_TEMPLATE.read_text(encoding="utf-8").rstrip("\n")
    processed = strip_for_tier(template_html, tier)
    # ensure_ascii=False keeps accented chars as raw UTF-8 (Sebastián, é, …);
    # the surrounding file is UTF-8 and the original encoder did the same.
    encoded = json.dumps(processed, ensure_ascii=False)
    # Escape every </ as </ so the embedded JSON can't prematurely close
    # the surrounding <script type="__bundler/template"> tag. JSON parsers
    # read / back as /.
    encoded = encoded.replace("</", "<\\u002F")

    match = TEMPLATE_SCRIPT.search(original)
    if not match:
        raise SystemExit("Could not find __bundler/template script tag in original index.html")

    rebuilt = original[: match.start(2)] + "\n" + encoded + "\n  " + original[match.end(2) :]

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(rebuilt, encoding="utf-8")
    return out_file


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Usage: build.py <tier:1|2|3> <output_dir>")
    tier = int(sys.argv[1])
    if tier not in (1, 2, 3):
        sys.exit("tier must be 1, 2, or 3")
    out_dir = Path(sys.argv[2])
    out_file = rebuild(tier, out_dir)
    size_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"Wrote {out_file} ({size_mb:.2f} MB, tier={tier})")


if __name__ == "__main__":
    main()
