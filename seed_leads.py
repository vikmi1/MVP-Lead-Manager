import urllib.request
import urllib.error
import json

URL = "http://localhost:8000/lead"

LEADS = [
    {"name": "Klaus Müller",    "contact": "k.mueller@email.de",    "source": "Probefahrt",        "comment": "VW Tiguan 2024, Mo-Fr verfügbar",        "consent": True},
    {"name": "Anna Schneider",  "contact": "+49 171 234 5678",       "source": "Kundendienst",      "comment": "Inspektion Golf 8, bitte morgens",       "consent": True},
    {"name": None,              "contact": "info@firma-bauer.de",    "source": "Flottenvertrag",    "comment": "Anfrage für 5 Fahrzeuge",                "consent": True},
    {"name": "Thomas Richter",  "contact": "t.richter@web.de",       "source": "Probefahrt",        "comment": "Audi A4 oder A6 — noch unentschlossen", "consent": True},
    {"name": "Maria Kovač",     "contact": "+49 160 987 6543",       "source": "Gebrauchtwagen",    "comment": "Budget ca. 15.000 €, SUV bevorzugt",    "consent": True},
    {"name": "Stefan Wolf",     "contact": "stefan.wolf@gmail.com",  "source": "Reifenwechsel",     "comment": None,                                    "consent": True},
    {"name": "Julia Braun",     "contact": "j.braun@outlook.de",     "source": "Finanzierung",      "comment": "Leasing-Angebot für Skoda Octavia",     "consent": True},
    {"name": None,              "contact": "+49 152 111 2233",       "source": None,                "comment": "Bitte zurückrufen nach 18 Uhr",         "consent": True},
    {"name": "Peter Hoffmann",  "contact": "p.hoffmann@t-online.de", "source": "Unfallschaden",     "comment": "Frontschaden nach Auffahrunfall",        "consent": True},
    {"name": "Lena Zimmermann", "contact": "lena.z@icloud.com",      "source": "Probefahrt",        "comment": "BMW 3er oder Mercedes C-Klasse",        "consent": True},
]

def post_lead(lead: dict) -> dict:
    data = json.dumps(lead).encode("utf-8")
    req = urllib.request.Request(
        URL, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

ok = 0
for i, lead in enumerate(LEADS, 1):
    try:
        result = post_lead(lead)
        print(f"[{i:02d}] OK   id={result['lead_id']}  {lead['contact']}")
        ok += 1
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[{i:02d}] ERR  {e.code}  {lead['contact']}  {body}")
    except Exception as e:
        print(f"[{i:02d}] FAIL {lead['contact']}  {e}")

print(f"\n{ok}/{len(LEADS)} leads sent OK.")
