import sqlite3
import database


def test_init_db_creates_leads_table(tmp_db):
    conn = sqlite3.connect(tmp_db)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='leads'"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_create_lead_returns_integer_id(tmp_db):
    lead_id = database.create_lead(
        tmp_db, name="Klaus", contact="k@test.de",
        source="web", comment=None, consent=True
    )
    assert isinstance(lead_id, int)
    assert lead_id == 1


def test_create_lead_increments_id(tmp_db):
    id1 = database.create_lead(tmp_db, None, "a@test.de", None, None, True)
    id2 = database.create_lead(tmp_db, None, "b@test.de", None, None, True)
    assert id2 == id1 + 1


def test_get_leads_returns_all(tmp_db):
    database.create_lead(tmp_db, None, "a@test.de", None, None, True)
    database.create_lead(tmp_db, None, "b@test.de", None, None, True)
    leads = database.get_leads(tmp_db)
    assert len(leads) == 2


def test_get_leads_respects_limit(tmp_db):
    for i in range(5):
        database.create_lead(tmp_db, None, f"{i}@test.de", None, None, True)
    leads = database.get_leads(tmp_db, limit=3)
    assert len(leads) == 3


def test_get_leads_contains_expected_fields(tmp_db):
    database.create_lead(tmp_db, "Klaus", "k@test.de", "web", "comment", True)
    leads = database.get_leads(tmp_db)
    row = leads[0]
    assert row["contact"] == "k@test.de"
    assert row["name"] == "Klaus"
    assert row["consent"] == 1


def test_delete_lead_returns_true(tmp_db):
    lead_id = database.create_lead(tmp_db, None, "x@test.de", None, None, True)
    result = database.delete_lead(tmp_db, lead_id)
    assert result is True


def test_delete_lead_removes_row(tmp_db):
    lead_id = database.create_lead(tmp_db, None, "x@test.de", None, None, True)
    database.delete_lead(tmp_db, lead_id)
    leads = database.get_leads(tmp_db)
    assert len(leads) == 0


def test_delete_nonexistent_returns_false(tmp_db):
    result = database.delete_lead(tmp_db, 999)
    assert result is False
