import pytest
from pydantic import ValidationError
from models import LeadCreate, LeadOut
from datetime import datetime


def test_lead_create_minimal_valid():
    lead = LeadCreate(contact="k@test.de", consent=True)
    assert lead.contact == "k@test.de"
    assert lead.consent is True
    assert lead.name is None
    assert lead.source is None
    assert lead.comment is None


def test_lead_create_all_fields():
    lead = LeadCreate(
        name="Klaus",
        contact="k@test.de",
        source="web",
        comment="VW Tiguan",
        consent=True,
    )
    assert lead.name == "Klaus"
    assert lead.source == "web"


def test_lead_create_consent_false_raises():
    with pytest.raises(ValidationError):
        LeadCreate(contact="k@test.de", consent=False)


def test_lead_create_missing_contact_raises():
    with pytest.raises(ValidationError):
        LeadCreate(consent=True)


def test_lead_out_valid():
    lead = LeadOut(
        id=1,
        created_at=datetime(2026, 6, 25, 10, 0, 0),
        name=None,
        contact="k@test.de",
        source=None,
        comment=None,
        consent=True,
    )
    assert lead.id == 1
    assert lead.contact == "k@test.de"
