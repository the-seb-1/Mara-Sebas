#!/usr/bin/env python3
"""
Bundle tier- AND locale-specific invitation pages.

Each (tier, locale) pair is written to:
    <tier_slug>/              (locale=en, canonical path)
    <tier_slug>/es/
    <tier_slug>/fr/

Tier-aware markers in src/template.html:

    <!-- TIER:2,3 -->...<!-- /TIER -->   kept only when tier in {2,3}
    <!-- TIER:3 -->...<!-- /TIER -->      kept only when tier == 3

Build-time substitutions in src/template.html:

    __TIER__            → the integer tier value (used inside the Component script)
    __LANG__            → html lang code ('en' | 'es' | 'fr')
    __LOCALE__          → locale code quoted as JS string
    __LOCALE_DICT__     → full locale JSON injected as a JS object literal
    __T_<KEY>__         → escaped HTML substitution of any locale string
                          (keys below are hand-wired; keep this list in sync
                           with src/locales/*.json)
    __NAV_<CODE>_HREF__    → relative URL to the sibling-locale page
    __NAV_<CODE>_STYLE__   → inline-CSS: active link vs. muted link styling
    __NAV_<CODE>_CURRENT__ → 'page' on the active locale, 'false' otherwise

Usage:
    # one bundle:
    python3 src/build.py <tier:1|2|3> <output_dir> [locale:en|es|fr]
    # or all 9 at once:
    python3 src/build.py all
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_TEMPLATE = ROOT / "src" / "template.html"
LOCALES_DIR = ROOT / "src" / "locales"

TIER_SLUGS = {
    1: "3uj45y3uwwge",
    2: "5p8nngv0iuof",
    3: "u22bagintj4n",
}
LOCALES = ("en", "es", "fr")

TIER_BLOCK = re.compile(
    r"<!--\s*TIER:([\d,]+)\s*-->(.*?)<!--\s*/TIER\s*-->",
    re.DOTALL,
)
TEMPLATE_SCRIPT = re.compile(
    r'(<script type="__bundler/template">)(.*?)(</script>)',
    re.DOTALL,
)

# Map __T_XXX__ tokens → dotted locale key. Keep in sync with template.html.
T_TOKENS = {
    "__T_TITLE__": "title",

    # nav
    "__T_NAV_EN__": "nav.en",
    "__T_NAV_ES__": "nav.es",
    "__T_NAV_FR__": "nav.fr",

    # hero
    "__T_HERO_EYEBROW__": "hero.eyebrow",
    "__T_HERO_GETTING_MARRIED__": "hero.getting_married",
    "__T_HERO_DATE_DAY__": "hero.date_day",
    "__T_HERO_DATE_YEAR__": "hero.date_year",
    "__T_HERO_LOCATION__": "hero.location",
    "__T_HERO_PORTRAIT_PH__": "placeholders.hero_portrait",

    # countdown
    "__T_CD_ARRIVED_TITLE__": "countdown.arrived_title",
    "__T_CD_ARRIVED_SUB__": "countdown.arrived_sub",
    "__T_CD_DAYS__": "countdown.days",
    "__T_CD_HRS__": "countdown.hrs",
    "__T_CD_MIN__": "countdown.min",
    "__T_CD_SEC__": "countdown.sec",

    # schedule
    "__T_SCHED_EYEBROW__": "schedule.eyebrow",
    "__T_SCHED_TITLE__": "schedule.title",
    "__T_SCHED_SUB__": "schedule.sub",
    "__T_SCHED_DAY_ONE__": "schedule.day_one",
    "__T_SCHED_DAY_TWO__": "schedule.day_two",

    # dress code
    "__T_DRESS_EYEBROW__": "dress.eyebrow",
    "__T_DRESS_TITLE__": "dress.title",
    "__T_DRESS_SUB__": "dress.sub",
    "__T_DRESS_WOMEN__": "dress.women",
    "__T_DRESS_WOMEN_ITEM__": "dress.women_item",
    "__T_DRESS_MEN__": "dress.men",
    "__T_DRESS_MEN_ITEM__": "dress.men_item",
    "__T_DRESS_NOTE__": "dress.note",

    # venue
    "__T_VENUE_EYEBROW__": "venue.eyebrow",
    "__T_VENUE_TITLE__": "venue.title",
    "__T_VENUE_DIRECTIONS__": "venue.directions",
    "__T_VENUE_PHOTO_PH__": "venue.photo_placeholder",

    # story
    "__T_STORY_EYEBROW__": "story.eyebrow",
    "__T_STORY_TITLE__": "story.title",
    "__T_STORY_IMAGE_ALT__": "story.image_alt",

    # stay (tier 3)
    "__T_STAY_EYEBROW__": "stay.eyebrow",
    "__T_STAY_TITLE__": "stay.title",
    "__T_STAY_SUB__": "stay.sub",
    "__T_STAY_CHECKIN_LABEL__": "stay.check_in_label",
    "__T_STAY_CHECKOUT_LABEL__": "stay.check_out_label",

    # accommodation (tier 2)
    "__T_ACC_EYEBROW__": "accommodation.eyebrow",
    "__T_ACC_TITLE__": "accommodation.title",
    "__T_ACC_SUB__": "accommodation.sub",
    "__T_ACC_VIEW__": "accommodation.view_details",
    "__T_ACC_HOTEL_PH__": "accommodation.hotel_placeholder",

    # faq
    "__T_FAQ_EYEBROW__": "faq.eyebrow",
    "__T_FAQ_TITLE__": "faq.title",

    # rsvp
    "__T_RSVP_EYEBROW__": "rsvp.eyebrow",
    "__T_RSVP_TITLE__": "rsvp.title",
    "__T_RSVP_THANKS_H__": "rsvp.thank_you_heading",
    "__T_RSVP_EDIT__": "rsvp.edit",
    "__T_RSVP_REPLY_BY__": "rsvp.reply_by",
    "__T_RSVP_NAME__": "rsvp.name",
    "__T_RSVP_NAME_PH__": "rsvp.name_ph",
    "__T_RSVP_ATTEND__": "rsvp.attend",
    "__T_RSVP_ATT_YES__": "rsvp.attend_yes",
    "__T_RSVP_ATT_NO__": "rsvp.attend_no",
    "__T_RSVP_PLUS__": "rsvp.plus_one",
    "__T_RSVP_PLUS_YES__": "rsvp.plus_yes",
    "__T_RSVP_PLUS_NO__": "rsvp.plus_no",
    "__T_RSVP_GUEST__": "rsvp.guest_name",
    "__T_RSVP_GUEST_PH__": "rsvp.guest_name_ph",
    "__T_RSVP_DIET__": "rsvp.dietary",
    "__T_RSVP_DIET_NONE__": "rsvp.diet_none",
    "__T_RSVP_DIET_VEG__": "rsvp.diet_veg",
    "__T_RSVP_DIET_VEGAN__": "rsvp.diet_vegan",
    "__T_RSVP_ALLERGIES__": "rsvp.allergies",
    "__T_RSVP_ALLERGIES_PH__": "rsvp.allergies_ph",
    "__T_RSVP_BRUNCH_Q__": "rsvp.brunch_q",
    "__T_RSVP_BRUNCH_YES__": "rsvp.brunch_yes",
    "__T_RSVP_BRUNCH_NO__": "rsvp.brunch_no",
    "__T_RSVP_SONG__": "rsvp.song",
    "__T_RSVP_SONG_PH__": "rsvp.song_ph",
    "__T_RSVP_NOTE__": "rsvp.note",
    "__T_RSVP_OPTIONAL__": "rsvp.optional",
    "__T_RSVP_NOTE_PH__": "rsvp.note_ph",
    "__T_RSVP_ERROR__": "rsvp.error",
    "__T_RSVP_SEND__": "rsvp.send",
    "__T_RSVP_WITH_LOVE__": "rsvp.with_love",
    "__T_RSVP_FOOTER_DATE__": "hero.footer_date",
    "__T_RSVP_FLOATING__": "rsvp.floating",

    # intro envelope / video
    "__T_INTRO_PLAY_LABEL__": "intro.play_label",
    "__T_INTRO_TAP_BEGIN__": "intro.tap_begin",
    "__T_INTRO_SKIP__": "intro.skip",
    "__T_INTRO_VIDEO_HERE__": "intro.video_here",
    "__T_INTRO_DROP_MP4__": "intro.drop_mp4",
}


def resolve_original() -> Path:
    candidates = [ROOT / "index.html", ROOT / "Mara-Sebas" / "index.html"]
    for p in candidates:
        if p.exists():
            return p
    raise SystemExit(f"Cannot locate original index.html. Tried: {candidates}")


def load_locale(code: str) -> dict:
    return json.loads((LOCALES_DIR / f"{code}.json").read_text(encoding="utf-8"))


def get_dotted(d: dict, path: str) -> str:
    cur = d
    for part in path.split("."):
        cur = cur[part]
    if not isinstance(cur, str):
        raise KeyError(f"locale key is not a string: {path}")
    return cur


def html_escape(s: str) -> str:
    # Minimal escaping safe for innerHTML + attribute contexts we target.
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )


def strip_for_tier(template_html: str, tier: int) -> str:
    def keep(m: re.Match[str]) -> str:
        allowed = {int(x) for x in m.group(1).split(",")}
        return m.group(2) if tier in allowed else ""
    return TIER_BLOCK.sub(keep, template_html)


def apply_locale_tokens(html: str, locale_data: dict) -> str:
    for token, key_path in T_TOKENS.items():
        val = html_escape(get_dotted(locale_data, key_path))
        html = html.replace(token, val)
    return html


def nav_substitutions(locale: str) -> dict:
    """Relative hrefs from the current locale page to each sibling."""
    # Current locale path within the tier dir:
    #   en → <tier>/
    #   es → <tier>/es/
    #   fr → <tier>/fr/
    # So relative links from inside each page:
    rel = {
        "en": {"en": "./", "es": "./es/", "fr": "./fr/"},
        "es": {"en": "../", "es": "./",   "fr": "../fr/"},
        "fr": {"en": "../", "es": "../es/", "fr": "./"},
    }[locale]
    active_style   = "color:#3A312A; text-decoration:none; font-weight:600; border-bottom:1px solid #3A312A; padding-bottom:1px;"
    inactive_style = "color:#A9847A; text-decoration:none;"
    out = {}
    for code in ("en", "es", "fr"):
        up = code.upper()
        is_active = code == locale
        out[f"__NAV_{up}_HREF__"] = rel[code]
        out[f"__NAV_{up}_STYLE__"] = active_style if is_active else inactive_style
        out[f"__NAV_{up}_CURRENT__"] = "page" if is_active else "false"
    return out


def build_one(tier: int, locale: str, out_dir: Path) -> Path:
    original = resolve_original().read_text(encoding="utf-8")
    template_html = SOURCE_TEMPLATE.read_text(encoding="utf-8").rstrip("\n")
    locale_data = load_locale(locale)

    processed = strip_for_tier(template_html, tier)
    processed = processed.replace("__TIER__", str(tier))
    processed = processed.replace("__LANG__", locale_data.get("lang", locale))
    processed = processed.replace("__LOCALE__", locale)
    # inline the full locale dict as a JS object literal
    processed = processed.replace(
        "__LOCALE_DICT__",
        json.dumps(locale_data, ensure_ascii=False),
    )
    # nav link substitutions
    for k, v in nav_substitutions(locale).items():
        processed = processed.replace(k, v)
    # user-facing translated strings in the HTML
    processed = apply_locale_tokens(processed, locale_data)

    # Verify no stray i18n markers remain
    leftover = re.findall(r"__T_[A-Z0-9_]+__|__NAV_[A-Z0-9_]+__|__LOCALE_DICT__|__LOCALE__|__LANG__", processed)
    if leftover:
        raise SystemExit(f"Unreplaced tokens: {sorted(set(leftover))}")

    encoded = json.dumps(processed, ensure_ascii=False)
    encoded = encoded.replace("</", "<\\u002F")

    match = TEMPLATE_SCRIPT.search(original)
    if not match:
        raise SystemExit("Could not find __bundler/template script tag in original index.html")

    rebuilt = original[: match.start(2)] + "\n" + encoded + "\n  " + original[match.end(2):]

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(rebuilt, encoding="utf-8")
    return out_file


def build_all() -> None:
    for tier, slug in TIER_SLUGS.items():
        for locale in LOCALES:
            out_dir = ROOT / slug if locale == "en" else ROOT / slug / locale
            out_file = build_one(tier, locale, out_dir)
            size_mb = out_file.stat().st_size / (1024 * 1024)
            print(f"  tier={tier} locale={locale:<2}  →  {out_file.relative_to(ROOT)} ({size_mb:.2f} MB)")


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "all":
        build_all()
        return
    if len(sys.argv) not in (3, 4):
        sys.exit(
            "Usage:\n"
            "  python3 src/build.py all\n"
            "  python3 src/build.py <tier:1|2|3> <output_dir> [locale:en|es|fr]"
        )
    tier = int(sys.argv[1])
    if tier not in (1, 2, 3):
        sys.exit("tier must be 1, 2, or 3")
    out_dir = Path(sys.argv[2])
    locale = sys.argv[3] if len(sys.argv) == 4 else "en"
    if locale not in LOCALES:
        sys.exit(f"locale must be one of {LOCALES}")
    out_file = build_one(tier, locale, out_dir)
    size_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"Wrote {out_file} ({size_mb:.2f} MB, tier={tier}, locale={locale})")


if __name__ == "__main__":
    main()
