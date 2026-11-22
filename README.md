# Mara & Sebas — 21 August 2027

Three bundled wedding invitations × three languages (EN · ES · FR) = nine standalone pages, all deployed to Vercel from this repo.

## Live URLs

Append `?guest=Name` to personalize. Append `&plus=1` to enable the plus-one question. The query string is preserved when guests switch languages via the EN · ES · FR pills in the top-right of each page.

**English (default)** — existing invitation links stay valid; nobody needs a new URL:

| Tier | URL path | Who it's for |
|---|---|---|
| 1 — Aperitivo only | `/3uj45y3uwwge/` | Guests invited to the 14:00 aperitivo |
| 2 — Wedding | `/5p8nngv0iuof/` | Ceremony + dinner + party |
| 3 — Wedding + stay | `/u22bagintj4n/` | Everything + 1 night hotel + brunch |

**Spanish** — add `/es/`:

| Tier | URL path |
|---|---|
| 1 | `/3uj45y3uwwge/es/` |
| 2 | `/5p8nngv0iuof/es/` |
| 3 | `/u22bagintj4n/es/` |

**French** — add `/fr/`:

| Tier | URL path |
|---|---|
| 1 | `/3uj45y3uwwge/fr/` |
| 2 | `/5p8nngv0iuof/fr/` |
| 3 | `/u22bagintj4n/fr/` |

Each URL serves a standalone bundle. Content from the other tiers is **stripped at build time** — not CSS-hidden — so a tier-1 guest viewing source cannot see tier-3 content. The language dictionaries ship complete inside each bundle, so sending a guest any locale URL works as the starting point.

Example invitation links:
```
https://<vercel-domain>/5p8nngv0iuof/?guest=Alex
https://<vercel-domain>/5p8nngv0iuof/es/?guest=Alex&plus=1
https://<vercel-domain>/u22bagintj4n/fr/?guest=Jordan&plus=1
```

## Layout

```
.
├── index.html                      (legacy; delete after guests move to new links)
├── 3uj45y3uwwge/index.html         tier 1 bundle, English (canonical)
├── 3uj45y3uwwge/es/index.html      tier 1 bundle, Spanish
├── 3uj45y3uwwge/fr/index.html      tier 1 bundle, French
├── 5p8nngv0iuof/… (same pattern)   tier 2 bundles
├── u22bagintj4n/… (same pattern)   tier 3 bundles
└── src/                            (not served — see .vercelignore)
    ├── template.html               master tier-aware + i18n-tokenized source
    ├── build.py                    tier × locale builder
    ├── apps-script.gs              RSVP endpoint for Google Apps Script
    └── locales/
        ├── en.json                 canonical English strings
        ├── es.json                 Spanish translations
        └── fr.json                 French translations
```

## Rebuild

After editing `src/template.html` or any `src/locales/*.json`, rebuild **all 9 bundles** in one shot:

```sh
python3 src/build.py all
```

…or a single bundle:

```sh
python3 src/build.py 2 5p8nngv0iuof/es/ es
```

Commit the changed `*/index.html` files; Vercel auto-deploys on push.

## Editing copy

1. **Pure wording tweak** (e.g. change the thank-you line) — edit all three `src/locales/*.json` files under the same key, then rebuild.
2. **Structural change** (add a new field or section) — edit `src/template.html`, add `__T_NEW_KEY__` placeholders where strings appear, add the matching entry to `T_TOKENS` at the top of `src/build.py`, add the string to all three `locales/*.json` files, then rebuild.

## Editing hotel details (tier 3)

In `src/locales/*.json`, the `stay` block holds the hotel name, address, check-in/out times, and the note. Edit in all three locale files, then rebuild (`python3 src/build.py all`).

## RSVP endpoint — one-time setup (~2 minutes)

1. Create a new Google Sheet; name the first tab `RSVPs`.
2. **Extensions → Apps Script.** Paste the entire contents of `src/apps-script.gs` into `Code.gs`.
3. Edit `NOTIFY_EMAIL` at the top of the script (defaults to `sebasgsu@gmail.com`).
4. **Deploy → New deployment.**
   - Type: *Web app*
   - Execute as: *Me*
   - Who has access: *Anyone*
5. Copy the deployment's web-app URL.
6. Open `src/template.html`, replace the line
   ```
   const ENDPOINT_URL = 'REPLACE_WITH_APPS_SCRIPT_URL';
   ```
   with your copied URL.
7. Rebuild all bundles (`python3 src/build.py all`) and commit + push.

Each submission appends a row to the sheet **and** emails you a formatted summary. The email is a safety net in case anything goes wrong with the sheet. The payload includes `tier` and `locale` so you can see which page the guest replied from.

> **Migrating an existing RSVP sheet.** The new `apps-script.gs` inserts a `locale` column at position 3. If you already have rows written with the old column layout, either (a) manually insert a blank `locale` column in column C of the existing `RSVPs` sheet before re-deploying the script, or (b) rename the current `RSVPs` tab to e.g. `RSVPs_v1` and let the script create a fresh tab with the new header.

## Repo visibility

If `the-seb-1/Mara-Sebas` is a public GitHub repo, the slug URLs are technically findable by browsing the repo tree. For a wedding this is fine (nobody's going to code-scan), but switching the repo to private removes this with zero downside.

## Removing the legacy root

The root `/index.html` still contains the pre-split tier-2 content. Delete it once all guests have the new tier-specific links:

```sh
git rm index.html
git commit -m "Remove legacy root invitation now that tiered links are live"
```
