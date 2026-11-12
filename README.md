# Mara & Sebas — 21 August 2027

Three bundled wedding invitations, one per invite tier. Deployed to Vercel from this repo.

## Live URLs

Append `?guest=Name` to personalize. Append `&plus=1` to enable the plus-one question.

| Tier | URL path | Who it's for |
|---|---|---|
| 1 — Aperitivo only | `/3uj45y3uwwge/` | Guests invited to the 14:00 aperitivo |
| 2 — Wedding | `/5p8nngv0iuof/` | Ceremony + dinner + party |
| 3 — Wedding + stay | `/u22bagintj4n/` | Everything + 1 night hotel + brunch |

Each URL serves a standalone bundle. Content from the other tiers is **stripped at build time** — not CSS-hidden — so a tier-1 guest viewing source cannot see tier-3 content.

Example invitation links:
```
https://<vercel-domain>/5p8nngv0iuof/?guest=Alex
https://<vercel-domain>/5p8nngv0iuof/?guest=Alex&plus=1
https://<vercel-domain>/u22bagintj4n/?guest=Jordan&plus=1
```

## Layout

```
.
├── index.html                  (legacy; delete after guests move to new links)
├── 3uj45y3uwwge/index.html     tier 1 bundle (aperitivo)
├── 5p8nngv0iuof/index.html     tier 2 bundle (wedding)
├── u22bagintj4n/index.html     tier 3 bundle (wedding + stay)
└── src/                        (not served — see .vercelignore)
    ├── template.html           master tier-aware source
    ├── build.py                wraps template into the bundler shell
    └── apps-script.gs          RSVP endpoint for Google Apps Script
```

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
7. Rebuild all three tiers (see "Rebuild" below) and commit + push.

Each submission appends a row to the sheet **and** emails you a formatted summary. The email is a safety net in case anything goes wrong with the sheet.

## Rebuild

After editing `src/template.html` (hotel name, copy tweaks, endpoint URL, etc.):

```sh
python3 src/build.py 1 3uj45y3uwwge/
python3 src/build.py 2 5p8nngv0iuof/
python3 src/build.py 3 u22bagintj4n/
```

Commit the changed `*/index.html` files; Vercel auto-deploys on push.

## Editing hotel details (tier 3)

In `src/template.html`, search for `tier 3 only — edit these when hotel is confirmed`. You'll find:

```js
const hotelName    = 'Hôtel to be confirmed';
const hotelAddress = 'Neuchâtel, Switzerland';
const checkIn      = 'Fri 21 Aug · after 15:00';
const checkOut     = 'Sat 22 Aug · before 12:00';
const stayNote     = 'Breakfast included. The booking is on us — just show your ID at reception.';
```

Edit, then rebuild tier 3 only (second-last line in the Rebuild section).

## Repo visibility

If `the-seb-1/Mara-Sebas` is a public GitHub repo, the slug URLs are technically findable by browsing the repo tree. For a wedding this is fine (nobody's going to code-scan), but switching the repo to private removes this with zero downside.

## Removing the legacy root

The root `/index.html` still contains the pre-split tier-2 content. Delete it once all guests have the new tier-specific links:

```sh
git rm index.html
git commit -m "Remove legacy root invitation now that tiered links are live"
```
