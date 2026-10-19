**English** · [Deutsch](README.de.md) · [Русский](README.ru.md)

# Lead-Capture Service

An MVP service for collecting leads (inquiries) from customers. It includes a web form for customers and a manager page for viewing, deleting and exporting leads. Leads are stored in SQLite; the manager is notified via a log file and email, and every lead is also copied into a Google Sheet.

## Live demo

**[https://vibecoding.aithinglab.com/mvp-lead-manager/](https://vibecoding.aithinglab.com/mvp-lead-manager/)** — form, manager page ([/admin](https://vibecoding.aithinglab.com/mvp-lead-manager/admin)) and Swagger UI ([/docs](https://vibecoding.aithinglab.com/mvp-lead-manager/docs)).
The demo runs in demo mode: entries are public, email and Google Sheets are off, and the data is reset to sample leads every 30 minutes — please do not enter real personal data.

## Screenshots

| Customer inquiry form | Manager page |
|---|---|
| ![Inquiry form](screenshots/form.png) | ![Manager page with the list of leads](screenshots/admin.png) |

<details><summary>Swagger UI (REST API)</summary>

![Swagger UI](screenshots/swagger.png)
</details>

The UI is in German with a DE/RU language toggle.

**Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLite, Jinja2, uvicorn

**Features:**
- Customer web form + manager page
- Storage in SQLite
- Notifications: log file, email to the manager, automatic row in Google Sheets
- Export of leads to CSV and JSON
- REST API with API key authentication
- GDPR (DSGVO): consent, right to erasure, data on your own server

---

## Up and running in 5–10 minutes

### 1. Clone and install dependencies

```bash
git clone https://github.com/vikmi1/MVP-Lead-Manager.git
cd MVP-Lead-Manager
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Generate an API key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Put it into `.env` as `API_KEY=...`.

`.env` variables:

| Variable | Purpose | Required |
|---|---|---|
| `API_KEY` | Key for the protected endpoints `/leads`, `/lead/{id}` | yes |
| `SMTP_HOST` / `SMTP_PORT` | SMTP server (default `smtp.gmail.com:587`) | for email |
| `SMTP_USER` / `SMTP_PASS` | Login and App Password of the sender mailbox | for email |
| `MANAGER_EMAIL` | Where lead notifications are sent | for email |
| `SHEETS_WEBHOOK_URL` | URL of the Apps Script web app | for Google Sheets |
| `DB_PATH` / `LOG_PATH` | Path to the database and the log file | no (defaults exist) |

Email and Google Sheets are optional: if the variables are empty, the service simply skips these notifications. Setup is described in the sections below.

### 3. Start the server

```bash
uvicorn app:app --reload
```

| Page | URL |
|---|---|
| Customer form | http://localhost:8000 |
| Manager page | http://localhost:8000/admin |
| Swagger UI | http://localhost:8000/docs |

### 4. Test request

```bash
curl -X POST http://localhost:8000/lead \
  -H "Content-Type: application/json" \
  -d '{"contact": "test@example.de", "consent": true}'
```

---

## Web interface

| Page | Path | Description |
|---|---|---|
| Form | `/` | The customer enters contact details and gives GDPR consent |
| Manager | `/admin` | Table of leads, a "Löschen" (delete) button, CSV/JSON export buttons |

The form submits data via JavaScript `fetch()` without reloading the page. The "Löschen" button on the manager page deletes the record and refreshes the table.

---

## Data export

The `/admin` page has "⬇ CSV" and "⬇ JSON" buttons to download all leads.

| Method | Path | Description |
|---|---|---|
| GET | `/admin/export.csv` | Download all leads as CSV (with BOM so German umlauts display correctly in Excel) |
| GET | `/admin/export.json` | Download all leads as JSON |

---

## Email notifications (Gmail)

1. Enable **2-Step Verification** in the sender's Google account
2. Create an **App Password**: https://myaccount.google.com/apppasswords (16 characters)
3. Fill in `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=you@gmail.com
   SMTP_PASS=<16-character App Password without spaces>
   MANAGER_EMAIL=send-to@gmail.com
   ```
4. Restart the server. For every new lead the manager receives an email "Neue Lead-Anfrage #N".

Your regular Gmail password will not work — you need an App Password.

---

## Google Sheets (Apps Script webhook)

1. Create a Google Sheet with the headers: `Datum | ID | Name | Kontakt | Betreff | Nachricht | Consent`
2. **Extensions → Apps Script**, paste the code:
   ```javascript
   function doPost(e) {
     var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
     var data = JSON.parse(e.postData.contents);
     sheet.appendRow([
       new Date(), data.id, data.name, data.contact,
       data.source, data.comment, data.consent
     ]);
     return ContentService
       .createTextOutput(JSON.stringify({status: "ok"}))
       .setMimeType(ContentService.MimeType.JSON);
   }
   ```
3. **Deploy → New deployment** → type "Web app", access "Anyone"
4. Copy the URL (it ends with `/exec`) and put it into `.env`:
   ```
   SHEETS_WEBHOOK_URL=https://script.google.com/macros/s/.../exec
   ```
5. Restart the server. Every lead is automatically added to the sheet as a new row.

---

## API

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/lead` | public | Create a new lead |
| GET | `/leads` | X-API-Key | List all leads |
| DELETE | `/lead/{id}` | X-API-Key | Delete a lead (GDPR) |

Full documentation: http://localhost:8000/docs

---

## Rotating the API key

1. Generate a new one: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Replace `API_KEY` in `.env`
3. Restart: `uvicorn app:app --reload`

---

## GDPR (DSGVO) / data protection

- The field `consent: true` is required — it records the user's explicit consent
- `DELETE /lead/{id}` implements the right to erasure (Recht auf Löschung, Art. 17 GDPR)
- `.env` and `leads.db` are not committed to git (`.gitignore`)
- Recommended data retention period: **90 days**
- Hosting only on servers in Germany / the EU (Hetzner, STRATO, netcup)
- HTTPS is mandatory in production (Let's Encrypt)
- A link to the privacy policy (Datenschutzerklärung) must be placed next to the form on the customer's website
- ⚠️ With the Google Sheets integration enabled, lead data is sent to Google servers (USA). For strict GDPR compliance this must be stated in the privacy policy, or the integration must be disabled (leave `SHEETS_WEBHOOK_URL` empty)
