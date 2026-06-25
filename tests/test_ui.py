def test_get_form_page_returns_200(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_admin_page_returns_200(test_client):
    response = test_client.get("/admin")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_admin_page_shows_leads(test_client):
    test_client.post("/lead", json={"name": "Klaus", "contact": "k@test.de", "consent": True})
    response = test_client.get("/admin")
    assert b"Klaus" in response.content
    assert b"k@test.de" in response.content


def test_get_admin_page_empty_state(test_client):
    response = test_client.get("/admin")
    assert response.status_code == 200


def test_admin_delete_redirects_to_admin(test_client):
    post_resp = test_client.post("/lead", json={"contact": "k@test.de", "consent": True})
    lead_id = post_resp.json()["lead_id"]
    response = test_client.post(f"/admin/delete/{lead_id}", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"


def test_admin_delete_removes_lead(test_client):
    post_resp = test_client.post("/lead", json={"contact": "del@test.de", "consent": True})
    lead_id = post_resp.json()["lead_id"]
    test_client.post(f"/admin/delete/{lead_id}")
    admin_resp = test_client.get("/admin")
    assert b"del@test.de" not in admin_resp.content


def test_form_page_contains_contact_field(test_client):
    response = test_client.get("/")
    assert b"Anfrage senden" in response.content
    assert b"consent" in response.content
    assert b"contact" in response.content


def test_admin_page_contains_table_headers(test_client):
    response = test_client.get("/admin")
    assert b"Kontakt" in response.content
    assert b"Datum" in response.content
    assert b"L\xc3\xb6schen" in response.content


def test_admin_page_shows_empty_message_when_no_leads(test_client):
    response = test_client.get("/admin")
    assert b"Noch keine Anfragen" in response.content


def test_admin_page_contains_export_buttons(test_client):
    response = test_client.get("/admin")
    assert b"/admin/export.csv" in response.content
    assert b"/admin/export.json" in response.content


def test_export_csv_returns_csv_with_leads(test_client):
    test_client.post("/lead", json={"name": "Klaus", "contact": "k@test.de", "consent": True})
    response = test_client.get("/admin/export.csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert "leads.csv" in response.headers["content-disposition"]
    assert "contact" in response.text  # header row
    assert "k@test.de" in response.text


def test_export_json_returns_json_with_leads(test_client):
    test_client.post("/lead", json={"name": "Anna", "contact": "a@test.de", "consent": True})
    response = test_client.get("/admin/export.json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert "leads.json" in response.headers["content-disposition"]
    data = response.json()
    assert any(lead["contact"] == "a@test.de" for lead in data)


def test_export_csv_empty_has_header_row(test_client):
    response = test_client.get("/admin/export.csv")
    assert response.status_code == 200
    assert "contact" in response.text
