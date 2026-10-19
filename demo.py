import asyncio

import database

DEMO_LEADS = [
    ("Klaus Müller", "k.mueller@example.de", "Probefahrt", "VW Tiguan 2024, Mo-Fr verfügbar"),
    ("Anna Schneider", "+49 30 0000 0101", "Kundendienst", "Inspektion Golf 8, bitte morgens"),
    (None, "info@firma-bauer.example.de", "Flottenvertrag", "Anfrage für 5 Fahrzeuge"),
    ("Thomas Richter", "t.richter@example.de", "Probefahrt", "Audi A4 oder A6 — noch unentschlossen"),
    ("Maria Kovač", "+49 30 0000 0105", "Gebrauchtwagen", "Budget ca. 15.000 €, SUV bevorzugt"),
    ("Julia Braun", "j.braun@example.com", "Finanzierung", "Leasing-Angebot für Skoda Octavia"),
    ("Peter Hoffmann", "p.hoffmann@example.de", "Unfallschaden", "Frontschaden nach Auffahrunfall"),
    ("Lena Zimmermann", "lena.z@example.com", "Probefahrt", "BMW 3er oder Mercedes C-Klasse"),
]


def reset_demo_data(db_path: str) -> None:
    database.delete_all_leads(db_path)
    for name, contact, source, comment in DEMO_LEADS:
        database.create_lead(db_path, name, contact, source, comment, True)


async def reset_periodically(db_path: str, minutes: int) -> None:
    while True:
        await asyncio.sleep(minutes * 60)
        reset_demo_data(db_path)
