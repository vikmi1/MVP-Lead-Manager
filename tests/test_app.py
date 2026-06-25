def test_post_lead_success(test_client):
    response = test_client.post("/lead", json={
        "contact": "k@test.de",
        "consent": True,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ok"
    assert data["message"] == "Anfrage gespeichert"
    assert isinstance(data["lead_id"], int)


def test_post_lead_all_fields(test_client):
    response = test_client.post("/lead", json={
        "name": "Klaus Müller",
        "contact": "k@test.de",
        "source": "Probefahrt",
        "comment": "VW Tiguan",
        "consent": True,
    })
    assert response.status_code == 201


def test_post_lead_missing_contact_returns_422(test_client):
    response = test_client.post("/lead", json={"consent": True})
    assert response.status_code == 422


def test_post_lead_consent_false_returns_422(test_client):
    response = test_client.post("/lead", json={
        "contact": "k@test.de",
        "consent": False,
    })
    assert response.status_code == 422


def test_get_leads_success(test_client):
    test_client.post("/lead", json={"contact": "a@test.de", "consent": True})
    test_client.post("/lead", json={"contact": "b@test.de", "consent": True})
    response = test_client.get("/leads", headers={"X-API-Key": "test-key"})
    assert response.status_code == 200
    leads = response.json()
    assert len(leads) == 2
    assert leads[0]["contact"] in ("a@test.de", "b@test.de")


def test_get_leads_missing_key_returns_422(test_client):
    response = test_client.get("/leads")
    assert response.status_code == 422


def test_get_leads_wrong_key_returns_401(test_client):
    response = test_client.get("/leads", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_get_leads_limit_param(test_client):
    for i in range(5):
        test_client.post("/lead", json={"contact": f"{i}@test.de", "consent": True})
    response = test_client.get("/leads?limit=3", headers={"X-API-Key": "test-key"})
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_delete_lead_success(test_client):
    post_resp = test_client.post("/lead", json={"contact": "k@test.de", "consent": True})
    lead_id = post_resp.json()["lead_id"]
    response = test_client.delete(f"/lead/{lead_id}", headers={"X-API-Key": "test-key"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_delete_lead_removes_from_db(test_client):
    post_resp = test_client.post("/lead", json={"contact": "k@test.de", "consent": True})
    lead_id = post_resp.json()["lead_id"]
    test_client.delete(f"/lead/{lead_id}", headers={"X-API-Key": "test-key"})
    leads = test_client.get("/leads", headers={"X-API-Key": "test-key"}).json()
    assert all(l["id"] != lead_id for l in leads)


def test_delete_nonexistent_lead_returns_404(test_client):
    response = test_client.delete("/lead/999", headers={"X-API-Key": "test-key"})
    assert response.status_code == 404


def test_delete_lead_wrong_key_returns_401(test_client):
    response = test_client.delete("/lead/1", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401
