/**
 * Mara & Sebas RSVP endpoint — Google Apps Script web app.
 *
 * Deploy steps (one-time, ~2 minutes):
 *
 *   1. Create a new Google Sheet. Rename the first tab "RSVPs".
 *   2. Extensions → Apps Script. Paste this entire file into Code.gs.
 *   3. Edit NOTIFY_EMAIL below to the address you want submission alerts at.
 *   4. Click Deploy → New deployment.
 *        Type: Web app
 *        Execute as: Me
 *        Who has access: Anyone
 *      Copy the resulting web-app URL.
 *   5. Paste that URL into src/template.html at the line that sets
 *      ENDPOINT_URL (currently REPLACE_WITH_APPS_SCRIPT_URL).
 *   6. Rebuild: python3 src/build.py 1|2|3 <slug>/
 *
 * Re-deploying: Deploy → Manage deployments → pencil icon → "New version" → Deploy.
 *
 * The client POSTs application/x-www-form-urlencoded with mode:'no-cors',
 * so Apps Script's default (no CORS headers) is fine — the row is written
 * regardless of what the opaque response looks like to the client.
 */

const NOTIFY_EMAIL = 'sebasgsu@gmail.com';   // ← change if you want alerts elsewhere
const SHEET_NAME   = 'RSVPs';

const COLUMNS = [
  'timestamp',
  'tier',
  'guest',
  'plusAllowed',
  'name',
  'attend',
  'bringGuest',
  'guestName',
  'dietary',
  'allergies',
  'song',
  'brunch',
  'message',
  'submittedAt',
  'userAgent',
];

function doPost(e) {
  try {
    const params = (e && e.parameter) || {};
    const sheet = getOrCreateSheet();
    const row = COLUMNS.map(function (k) {
      if (k === 'timestamp') return new Date();
      return params[k] || '';
    });
    sheet.appendRow(row);
    try { notify(params); } catch (mailErr) {
      console.error('MailApp.sendEmail failed: ' + mailErr);
    }
    return json({ ok: true });
  } catch (err) {
    console.error('doPost error: ' + err);
    return json({ ok: false, error: String(err) });
  }
}

/** Handy for pinging the URL from a browser to confirm it's live. */
function doGet() {
  return json({ ok: true, hint: 'POST form-encoded RSVPs here.' });
}

function getOrCreateSheet() {
  const ss = SpreadsheetApp.getActive();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(COLUMNS);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, COLUMNS.length).setFontWeight('bold');
  }
  return sheet;
}

function notify(params) {
  if (!NOTIFY_EMAIL) return;
  const tierLabel = { '1': 'Aperitivo', '2': 'Wedding', '3': 'Wedding + Stay' }[params.tier] || ('tier ' + params.tier);
  const attend = params.attend === 'yes' ? '✓ Joyfully accepts' : (params.attend === 'no' ? '✗ Regretfully declines' : '(not set)');
  const dietaryLabel = { 'none': 'No restrictions', 'veg': 'Vegetarian', 'vegan': 'Vegan' }[params.dietary] || '(not set)';
  const subject = 'RSVP · ' + (params.name || 'unknown') + ' · ' + attend + ' · ' + tierLabel;

  const lines = [
    'Name: ' + (params.name || ''),
    'Tier: ' + tierLabel,
    'Guest link personalization: ' + (params.guest || '(none)'),
    'Response: ' + attend,
    '',
    'Plus-one allowed by link: ' + (params.plusAllowed === '1' ? 'yes' : 'no'),
    'Bringing plus-one: ' + (params.bringGuest || '(not set)'),
    'Plus-one name: ' + (params.guestName || ''),
    '',
    'Dietary: ' + dietaryLabel,
    'Allergies / notes: ' + (params.allergies || '(none)'),
    'Song: ' + (params.song || '(none)'),
    'Brunch (tier 3): ' + (params.brunch || '(n/a)'),
    '',
    'Message: ' + (params.message || '(none)'),
    '',
    'Submitted at: ' + (params.submittedAt || ''),
    'User-agent: ' + (params.userAgent || ''),
  ];

  MailApp.sendEmail({
    to: NOTIFY_EMAIL,
    subject: subject,
    body: lines.join('\n'),
  });
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
