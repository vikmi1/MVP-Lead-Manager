# Lead-Capture Service — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** MVP Lead-Capture сервис на FastAPI — принимает заявки через POST /lead, сохраняет в SQLite, уведомляет менеджера через log + email, предоставляет admin-эндпоинты под API-ключом.

**Architecture:** Модульная структура из 6 файлов с чёткими границами: app.py (роуты), models.py (схемы), database.py (SQLite), notifier.py (уведомления), auth.py (API-ключ), config.py (настройки). FastAPI + Pydantic v2 обеспечивают автоматическую валидацию и Swagger UI.

**Tech Stack:** FastAPI 0.115, Pydantic v2, SQLite (встроен), python-dotenv 1.0, uvicorn, pytest + httpx

---

## Файловая карта

| Файл | Создать / Изменить | Роль |
|---|---|---|
| `requirements.txt` | Создать | Зависимости проекта |
| `.env.example` | Создать | Шаблон конфигурации |
| `.gitignore` | Создать | Исключения git |
| `config.py` | Создать | Загрузка .env |
| `models.py` | Создать | Pydantic: LeadCreate, LeadOut |
| `database.py` | Создать | SQLite: init, create, get, delete |
| `auth.py` | Создать | FastAPI Dependency: X-API-Key |
| `notifier.py` | Создать | log_event() + send_email() |
| `app.py` | Создать | FastAPI app + три роута |
| `tests/conftest.py` | Создать | Pytest fixtures: tmp_db, test_client |
| `tests/test_models.py` | Создать | Тесты Pydantic-схем |
| `tests/test_database.py` | Создать | Тесты CRUD SQLite |
| `tests/test_auth.py` | Создать | Тесты проверки ключа |
| `tests/test_notifier.py` | Создать | Тесты log + email |
| `tests/test_app.py` | Создать | Интеграционные тесты роутов |
| `test_requests.http` | Создать | HTTP-файл для VS Code / JetBrains |
| `README.md` | Создать | Запуск за 5-10 мин + DSGVO |

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `config.py`

- [ ] **Step 1: Создать `requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.34.0
python-dotenv==1.0.1
pytest==8.3.4
httpx==0.27.0
```

- [ ] **Step 2: Установить зависимости**

```bash
pip install -r requirements.txt
```

Ожидаемый результат: `Successfully installed fastapi-0.115.0 ...`

- [ ] **Step 3: Создать `.env.example`**

```
API_KEY=сгенерируй-через-python-c-import-secrets-print-secrets-token-hex-32

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=your-app-password
MANAGER_EMAIL=manager@client.de

DB_PATH=leads.db
LOG_PATH=events.log
```

- [ ] **Step 4: Создать `.gitignore`**

```
.env
leads.db
events.log
__pycache__/
*.pyc
.pytest_cache/
.superpowers/
```

- [ ] **Step 5: Создать `config.py`**

```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "")
DB_PATH = os.getenv("DB_PATH", "leads.db")
LOG_PATH = os.getenv("LOG_PATH", "events.log")
```

- [ ] **Step 6: Скопировать `.env.example` в `.env` и заполнить**

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Вставить сгенерированный ключ в `.env` как значение `API_KEY`.

- [ ] **Step 7: Создать `tests/__init__.py`**

```bash
mkdir tests && touch tests/__init__.py
```

- [ ] **Step 8: Коммит**

```bash
git add requirements.txt .env.example .gitignore config.py tests/__init__.py
git commit -m "feat: project setup, config and dependencies"
```

---

## Task 2: Pydantic Models

**Files:**
- Create: `models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Написать failing тесты — `tests/test_models.py`**

```python
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
```

- [ ] **Step 2: Запустить тесты — убедиться, что они падают**

```bash
pytest tests/test_models.py -v
```

Ожидаемый результат: `ERROR` или `ModuleNotFoundError: No module named 'models'`

- [ ] **Step 3: Создать `models.py`**

```python
from datetime import datetime
from pydantic import BaseModel, field_validator


class LeadCreate(BaseModel):
    name: str | None = None
    contact: str
    source: str | None = None
    comment: str | None = None
    consent: bool

    @field_validator("consent")
    @classmethod
    def consent_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("consent must be true")
        return v


class LeadOut(BaseModel):
    id: int
    created_at: datetime
    name: str | None
    contact: str
    source: str | None
    comment: str | None
    consent: bool
```

- [ ] **Step 4: Запустить тесты — убедиться, что они проходят**

```bash
pytest tests/test_models.py -v
```

Ожидаемый результат: `5 passed`

- [ ] **Step 5: Коммит**

```bash
git add models.py tests/test_models.py
git commit -m "feat: add Pydantic models LeadCreate and LeadOut"
```

---

## Task 3: Database Layer

**Files:**
- Create: `database.py`
- Create: `tests/conftest.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Создать `tests/conftest.py`**

```python
import pytest
import database
import config


@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    return db_path


@pytest.fixture
def test_client(tmp_db, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DB_PATH", tmp_db)
    monkeypatch.setattr(config, "API_KEY", "test-key")
    monkeypatch.setattr(config, "LOG_PATH", str(tmp_path / "events.log"))
    monkeypatch.setattr(config, "SMTP_USER", "")
    from fastapi.testclient import TestClient
    import app as app_module
    with TestClient(app_module.app) as client:
        yield client
```

- [ ] **Step 2: Написать failing тесты — `tests/test_database.py`**

```python
import sqlite3
import pytest
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
```

- [ ] **Step 3: Запустить тесты — убедиться, что они падают**

```bash
pytest tests/test_database.py -v
```

Ожидаемый результат: `ERROR` или `ModuleNotFoundError: No module named 'database'`

- [ ] **Step 4: Создать `database.py`**

```python
import sqlite3
from datetime import datetime, timezone
from typing import Optional


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    with _get_conn(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME NOT NULL,
                name       TEXT,
                contact    TEXT NOT NULL,
                source     TEXT,
                comment    TEXT,
                consent    BOOLEAN NOT NULL
            )
        """)
        conn.commit()


def create_lead(
    db_path: str,
    name: Optional[str],
    contact: str,
    source: Optional[str],
    comment: Optional[str],
    consent: bool,
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    with _get_conn(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO leads (created_at, name, contact, source, comment, consent)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (created_at, name, contact, source, comment, consent),
        )
        conn.commit()
        return cursor.lastrowid


def get_leads(db_path: str, limit: int = 50, offset: int = 0) -> list[dict]:
    with _get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_lead(db_path: str, lead_id: int) -> bool:
    with _get_conn(db_path) as conn:
        cursor = conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        conn.commit()
        return cursor.rowcount > 0
```

- [ ] **Step 5: Запустить тесты — убедиться, что они проходят**

```bash
pytest tests/test_database.py -v
```

Ожидаемый результат: `9 passed`

- [ ] **Step 6: Коммит**

```bash
git add database.py tests/conftest.py tests/test_database.py
git commit -m "feat: add SQLite database layer with CRUD operations"
```

---

## Task 4: Auth Dependency

**Files:**
- Create: `auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Написать failing тесты — `tests/test_auth.py`**

```python
import pytest
from fastapi import HTTPException
import config
from auth import verify_api_key


def test_valid_key_passes(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "my-secret")
    result = verify_api_key("my-secret")
    assert result == "my-secret"


def test_invalid_key_raises_401(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "my-secret")
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key("wrong-key")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "unauthorized"


def test_empty_key_raises_401(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "my-secret")
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key("")
    assert exc_info.value.status_code == 401
```

- [ ] **Step 2: Запустить тесты — убедиться, что они падают**

```bash
pytest tests/test_auth.py -v
```

Ожидаемый результат: `ModuleNotFoundError: No module named 'auth'`

- [ ] **Step 3: Создать `auth.py`**

```python
from fastapi import Header, HTTPException
import config


def verify_api_key(x_api_key: str = Header(...)) -> str:
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")
    return x_api_key
```

- [ ] **Step 4: Запустить тесты — убедиться, что они проходят**

```bash
pytest tests/test_auth.py -v
```

Ожидаемый результат: `3 passed`

- [ ] **Step 5: Коммит**

```bash
git add auth.py tests/test_auth.py
git commit -m "feat: add API key auth dependency"
```

---

## Task 5: Notifier

**Files:**
- Create: `notifier.py`
- Create: `tests/test_notifier.py`

- [ ] **Step 1: Написать failing тесты — `tests/test_notifier.py`**

```python
import pytest
from unittest.mock import patch, MagicMock
import config
import notifier


def test_log_event_creates_file(tmp_path, monkeypatch):
    log_path = str(tmp_path / "events.log")
    monkeypatch.setattr(config, "LOG_PATH", log_path)
    notifier.log_event(42, "k@test.de", "web")
    assert (tmp_path / "events.log").exists()


def test_log_event_contains_lead_info(tmp_path, monkeypatch):
    log_path = str(tmp_path / "events.log")
    monkeypatch.setattr(config, "LOG_PATH", log_path)
    notifier.log_event(42, "k@test.de", "Probefahrt")
    content = open(log_path).read()
    assert "NEW LEAD id=42" in content
    assert "k@test.de" in content
    assert "Probefahrt" in content


def test_log_event_appends(tmp_path, monkeypatch):
    log_path = str(tmp_path / "events.log")
    monkeypatch.setattr(config, "LOG_PATH", log_path)
    notifier.log_event(1, "a@test.de", None)
    notifier.log_event(2, "b@test.de", None)
    lines = open(log_path).readlines()
    assert len(lines) == 2


def test_send_email_skips_when_smtp_not_configured(monkeypatch):
    monkeypatch.setattr(config, "SMTP_USER", "")
    # Должно завершиться без исключения
    notifier.send_email(1, "Klaus", "k@test.de", "web", None)


def test_send_email_calls_smtp_when_configured(monkeypatch):
    monkeypatch.setattr(config, "SMTP_USER", "from@test.de")
    monkeypatch.setattr(config, "SMTP_PASS", "pass123")
    monkeypatch.setattr(config, "MANAGER_EMAIL", "mgr@test.de")
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.test.de")
    monkeypatch.setattr(config, "SMTP_PORT", 587)

    mock_smtp_instance = MagicMock()
    with patch("notifier.smtplib.SMTP") as mock_smtp_class:
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
        notifier.send_email(1, "Klaus", "k@test.de", "web", "VW Tiguan")
        mock_smtp_class.assert_called_once_with("smtp.test.de", 587)
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("from@test.de", "pass123")


def test_send_email_logs_error_on_smtp_failure(monkeypatch, caplog):
    monkeypatch.setattr(config, "SMTP_USER", "from@test.de")
    monkeypatch.setattr(config, "SMTP_PASS", "pass")
    monkeypatch.setattr(config, "MANAGER_EMAIL", "mgr@test.de")
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.test.de")
    monkeypatch.setattr(config, "SMTP_PORT", 587)

    with patch("notifier.smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
        import logging
        with caplog.at_level(logging.ERROR, logger="notifier"):
            notifier.send_email(1, "Klaus", "k@test.de", None, None)
    assert "Failed to send email" in caplog.text
```

- [ ] **Step 2: Запустить тесты — убедиться, что они падают**

```bash
pytest tests/test_notifier.py -v
```

Ожидаемый результат: `ModuleNotFoundError: No module named 'notifier'`

- [ ] **Step 3: Создать `notifier.py`**

```python
import smtplib
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Optional
import config

logger = logging.getLogger(__name__)


def log_event(lead_id: int, contact: str, source: Optional[str]) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] NEW LEAD id={lead_id} contact={contact} source={source}\n"
    with open(config.LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def send_email(
    lead_id: int,
    name: Optional[str],
    contact: str,
    source: Optional[str],
    comment: Optional[str],
) -> None:
    if not all([config.SMTP_USER, config.SMTP_PASS, config.MANAGER_EMAIL]):
        logger.warning("Email config incomplete — skipping notification")
        return

    body = (
        f"Neue Lead-Anfrage #{lead_id}\n\n"
        f"Name:    {name or '—'}\n"
        f"Contact: {contact}\n"
        f"Source:  {source or '—'}\n"
        f"Comment: {comment or '—'}\n"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"Neue Lead-Anfrage #{lead_id}"
    msg["From"] = config.SMTP_USER
    msg["To"] = config.MANAGER_EMAIL

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(config.SMTP_USER, config.SMTP_PASS)
            smtp.send_message(msg)
    except Exception as e:
        logger.error(f"Failed to send email for lead {lead_id}: {e}")
```

- [ ] **Step 4: Запустить тесты — убедиться, что они проходят**

```bash
pytest tests/test_notifier.py -v
```

Ожидаемый результат: `6 passed`

- [ ] **Step 5: Коммит**

```bash
git add notifier.py tests/test_notifier.py
git commit -m "feat: add notifier with log and email support"
```

---

## Task 6: FastAPI Routes

**Files:**
- Create: `app.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Написать failing интеграционные тесты — `tests/test_app.py`**

```python
import pytest


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
```

- [ ] **Step 2: Запустить тесты — убедиться, что они падают**

```bash
pytest tests/test_app.py -v
```

Ожидаемый результат: `ERROR` или `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Создать `app.py`**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException

import config
import database
import notifier
from auth import verify_api_key
from models import LeadCreate, LeadOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db(config.DB_PATH)
    yield


app = FastAPI(title="Lead-Capture Service", version="1.0.0", lifespan=lifespan)


@app.post("/lead", status_code=201)
def create_lead(lead: LeadCreate):
    try:
        lead_id = database.create_lead(
            config.DB_PATH,
            lead.name,
            lead.contact,
            lead.source,
            lead.comment,
            lead.consent,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="db error")

    notifier.log_event(lead_id, lead.contact, lead.source)

    try:
        notifier.send_email(lead_id, lead.name, lead.contact, lead.source, lead.comment)
    except Exception:
        pass

    return {
        "status": "ok",
        "message": "Anfrage gespeichert",
        "lead_id": lead_id,
    }


@app.get("/leads", response_model=list[LeadOut])
def get_leads(
    limit: int = 50,
    offset: int = 0,
    _: str = Depends(verify_api_key),
):
    try:
        return database.get_leads(config.DB_PATH, limit, offset)
    except Exception:
        raise HTTPException(status_code=500, detail="db error")


@app.delete("/lead/{lead_id}")
def delete_lead(lead_id: int, _: str = Depends(verify_api_key)):
    deleted = database.delete_lead(config.DB_PATH, lead_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="not found")
    return {"status": "ok", "message": f"Lead {lead_id} deleted"}
```

- [ ] **Step 4: Запустить все тесты — убедиться, что они проходят**

```bash
pytest -v
```

Ожидаемый результат: все тесты проходят (`passed`)

- [ ] **Step 5: Запустить сервер вручную и открыть Swagger**

```bash
uvicorn app:app --reload
```

Открыть в браузере: `http://localhost:8000/docs`
Убедиться, что все три эндпоинта видны и доступны.

- [ ] **Step 6: Коммит**

```bash
git add app.py tests/test_app.py
git commit -m "feat: add FastAPI routes POST /lead, GET /leads, DELETE /lead/{id}"
```

---

## Task 7: HTTP Test File

**Files:**
- Create: `test_requests.http`

- [ ] **Step 1: Создать `test_requests.http`**

```http
### 1. Успешная заявка — все поля
POST http://localhost:8000/lead
Content-Type: application/json

{
  "name": "Klaus Müller",
  "contact": "k.mueller@email.de",
  "source": "Probefahrt-Formular",
  "comment": "Interessiert an VW Tiguan 2024, Mo-Fr",
  "consent": true
}

###

### 2. Успешная заявка — только обязательные поля
POST http://localhost:8000/lead
Content-Type: application/json

{
  "contact": "anna.schmidt@gmail.com",
  "consent": true
}

###

### 3. Ошибка 422 — нет поля contact
POST http://localhost:8000/lead
Content-Type: application/json

{
  "name": "Hans",
  "consent": true
}

###

### 4. Ошибка 422 — consent = false (DSGVO не принято)
POST http://localhost:8000/lead
Content-Type: application/json

{
  "contact": "hans@test.de",
  "consent": false
}

###

### 5. Получить все лиды (заменить YOUR_API_KEY)
GET http://localhost:8000/leads
X-API-Key: YOUR_API_KEY

###

### 6. Получить лиды с пагинацией
GET http://localhost:8000/leads?limit=10&offset=0
X-API-Key: YOUR_API_KEY

###

### 7. Ошибка 401 — неверный API-ключ
GET http://localhost:8000/leads
X-API-Key: wrong-key

###

### 8. Удалить лид (заменить ID и YOUR_API_KEY)
DELETE http://localhost:8000/lead/1
X-API-Key: YOUR_API_KEY

###

### 9. Ошибка 404 — лид не найден
DELETE http://localhost:8000/lead/99999
X-API-Key: YOUR_API_KEY

###

### 10. Ошибка 422 — нет заголовка X-API-Key
GET http://localhost:8000/leads
```

- [ ] **Step 2: Запустить сервер и прогнать все запросы вручную**

```bash
uvicorn app:app --reload
```

Открыть `test_requests.http` в VS Code (расширение REST Client) или JetBrains.
Запустить каждый запрос и убедиться в ожидаемых ответах.

- [ ] **Step 3: Коммит**

```bash
git add test_requests.http
git commit -m "test: add HTTP test file with 10 scenarios"
```

---

## Task 8: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Создать `README.md`**

```markdown
# Lead-Capture Service

MVP-сервис для приёма заявок (лидов) от клиентов. Сохраняет в SQLite, уведомляет менеджера через лог и email.

**Стек:** Python 3.11+, FastAPI, Pydantic v2, SQLite, uvicorn

---

## Запуск за 5–10 минут

### 1. Клонировать и установить зависимости

```bash
git clone <repo-url>
cd lead-service
pip install -r requirements.txt
```

### 2. Настроить конфигурацию

```bash
cp .env.example .env
```

Сгенерировать API-ключ:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Вставить в `.env` как `API_KEY=...`. Заполнить SMTP-настройки для email-уведомлений (опционально).

### 3. Запустить сервер

```bash
uvicorn app:app --reload
```

Swagger UI: http://localhost:8000/docs

### 4. Тестовый запрос

```bash
curl -X POST http://localhost:8000/lead \
  -H "Content-Type: application/json" \
  -d '{"contact": "test@example.de", "consent": true}'
```

---

## Смена API-ключа

1. Сгенерировать новый: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Заменить `API_KEY` в `.env`
3. Перезапустить: `uvicorn app:app --reload`

---

## Тесты

```bash
pytest -v
```

---

## DSGVO / Datenschutz

- Поле `consent: true` обязательно — фиксирует явное согласие пользователя
- `DELETE /lead/{id}` реализует право на забвение (Recht auf Löschung, Art. 17 DSGVO)
- `.env` и `leads.db` не коммитятся в git (`.gitignore`)
- Рекомендуемый срок хранения данных: **90 дней**
- Хостинг только на серверах в Германии / ЕС (Hetzner, STRATO, netcup)
- HTTPS обязателен при деплое (Let's Encrypt)
- Ссылка на Datenschutzerklärung должна быть рядом с формой на сайте клиента
```

- [ ] **Step 2: Коммит**

```bash
git add README.md
git commit -m "docs: add README with setup, API key management and DSGVO notes"
```

---

## Финальная проверка

- [ ] Запустить полный набор тестов:

```bash
pytest -v
```

Ожидаемый результат: все тесты проходят.

- [ ] Запустить сервер и проверить Swagger UI:

```bash
uvicorn app:app --reload
```

Открыть http://localhost:8000/docs и убедиться, что все три эндпоинта отображаются и доступны.
