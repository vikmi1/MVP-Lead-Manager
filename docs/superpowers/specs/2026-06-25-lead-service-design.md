# Lead-Capture Сервис — Design Spec

**Дата:** 2026-06-25  
**Проект:** Учебный проект курса «Профессия Вайб-кодер» (zerocoder.ru)  
**Студент:** Viktor (Essen, NRW, DE)  
**Статус:** Утверждён

---

## 1. Цель

MVP-сервис приёма заявок (лидов) для малого бизнеса в Германии (KMU). Целевой пример клиента: Autohaus Borgmann, Essen — ~30–50 заявок в день, которые сейчас теряются в email.

Сервис решает: единая точка приёма → сохранение в БД → мгновенное уведомление менеджера.

---

## 2. Стек

| Компонент | Выбор | Обоснование |
|---|---|---|
| Фреймворк | **FastAPI** | Swagger UI на /docs, автовалидация через Pydantic, async из коробки |
| Валидация | **Pydantic v2** | Декларативные схемы, автоматические HTTP 422 |
| База данных | **SQLite** | Достаточно для KMU MVP, нет внешних зависимостей |
| Конфигурация | **python-dotenv** | Секреты в .env, не коммитятся в git |
| Email | **smtplib** | Встроен в Python, внешних библиотек не нужно |
| Сервер | **uvicorn** | Стандартный ASGI-сервер для FastAPI |

---

## 3. Архитектура

### 3.1 Поток данных

```
Клиент (HTML-форма / Postman)
        ↓ POST /lead | GET /leads | DELETE /lead/{id}
FastAPI app.py
  ├── models.py     — Pydantic валидация входящих данных
  ├── auth.py       — проверка X-API-Key (для admin-роутов)
  ├── config.py     — загрузка .env
  ├── database.py   — запись/чтение/удаление в SQLite
  └── notifier.py   — запись в events.log + отправка email
        ↓
HTTP 201/200 → {"status": "ok", "lead_id": 42}
```

### 3.2 Структура файлов

```
lead-service/
├── app.py                ← FastAPI app, три роута
├── models.py             ← Pydantic: LeadCreate, LeadOut
├── database.py           ← SQLite: init + create/get/delete
├── notifier.py           ← log_event() + send_email()
├── auth.py               ← API-ключ dependency
├── config.py             ← настройки из .env
├── leads.db              ← SQLite файл (в .gitignore)
├── events.log            ← хронологический лог заявок
├── .env                  ← секреты (в .gitignore)
├── .env.example          ← шаблон с пустыми значениями
├── requirements.txt      ← зависимости
├── test_requests.http    ← 5–10 тестовых запросов
└── README.md             ← запуск за 5–10 мин + DSGVO
```

---

## 4. API Контракт

### POST /lead
**Доступ:** открытый (вызывается с сайта клиента)

**Запрос:**
```json
{
  "name":    "Klaus Müller",
  "contact": "k.mueller@email.de",
  "source":  "Probefahrt-Formular",
  "comment": "Interessiert an VW Tiguan 2024",
  "consent": true
}
```

**Ответ HTTP 201:**
```json
{
  "status":  "ok",
  "message": "Anfrage gespeichert",
  "lead_id": 42
}
```

**Ошибки:**
- `422` — нет `contact`, `consent != true`, или невалидный JSON (Pydantic автоматически)
- `500` — БД недоступна → запись в events.log

---

### GET /leads
**Доступ:** защищён `X-API-Key`

**Query-параметры:** `?limit=50&offset=0` (опционально)

**Ответ HTTP 200:**
```json
[
  {
    "id": 42,
    "created_at": "2026-06-25T10:05:12",
    "name": "Klaus Müller",
    "contact": "k.mueller@email.de",
    "source": "Probefahrt-Formular",
    "comment": "Interessiert an VW Tiguan 2024",
    "consent": true
  }
]
```

**Ошибки:**
- `401` — нет или неверный API-ключ
- `500` — БД недоступна

---

### DELETE /lead/{id}
**Доступ:** защищён `X-API-Key`  
**Назначение:** DSGVO — право на забвение (Recht auf Löschung)

**Ответ HTTP 200:**
```json
{
  "status":  "ok",
  "message": "Lead 42 deleted"
}
```

**Ошибки:**
- `401` — нет или неверный API-ключ
- `404` — лид с таким id не найден

---

## 5. Модель данных

### SQLite — таблица `leads`

| Поле | Тип | Статус |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | автоинкремент |
| `created_at` | DATETIME | автоматически (utcnow) |
| `name` | TEXT | необязательно |
| `contact` | TEXT NOT NULL | **обязательно** |
| `source` | TEXT | необязательно |
| `comment` | TEXT | необязательно |
| `consent` | BOOLEAN | **обязательно, должно быть True** |

### Pydantic-схемы (models.py)

```python
class LeadCreate(BaseModel):
    name:    str | None = None
    contact: str
    source:  str | None = None
    comment: str | None = None
    consent: bool

    @field_validator('consent')
    def consent_must_be_true(cls, v):
        if not v:
            raise ValueError('consent must be true')
        return v

class LeadOut(BaseModel):
    id:         int
    created_at: datetime
    name:       str | None
    contact:    str
    source:     str | None
    comment:    str | None
    consent:    bool
```

---

## 6. Уведомления (notifier.py)

При каждой успешной записи лида выполняются **оба** действия:

**A — events.log:**
```
[2026-06-25 10:05:12] NEW LEAD id=42 contact=k.mueller@email.de source=Probefahrt-Formular
```

**B — Email (smtplib):**
```
To: manager@borgmann.de
Subject: Neue Lead-Anfrage #42
Body: Name, contact, source, comment, дата
```

Если email-отправка падает — ошибка логируется, HTTP-ответ не меняется (email не блокирует ответ).

---

## 7. Безопасность и DSGVO

### API-ключ
- Хранится в `.env` как `API_KEY=...`
- Генерируется: `python -c "import secrets; print(secrets.token_hex(32))"`
- Передаётся в заголовке: `X-API-Key: <ключ>`
- Смена: заменить в `.env` → перезапустить сервер
- `.env` и `leads.db` в `.gitignore`

### DSGVO
- `consent=true` — обязательное условие записи
- `DELETE /lead/{id}` — реализует право на забвение
- В README: указать срок хранения данных (рекомендуется 90 дней)
- Хостинг: только серверы в Германии/ЕС (Hetzner, STRATO, netcup)
- HTTPS обязателен при деплое

---

## 8. Конфигурация (.env)

```env
API_KEY=сгенерированный-ключ

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=app-password
MANAGER_EMAIL=manager@borgmann.de
```

---

## 9. Обработка ошибок

| Ситуация | HTTP | Действие |
|---|---|---|
| Нет `contact` | 422 | Pydantic автоматически |
| `consent != true` | 422 | field_validator в LeadCreate (ValueError → 422) |
| Неверный API-ключ | 401 | auth.py dependency |
| Лид не найден | 404 | database.py возвращает None |
| БД недоступна | 500 | try/except + запись в events.log |
| Email упал | — | Логируется, запрос не блокируется |

---

## 10. Тестирование (test_requests.http)

Минимум 5 запросов:
1. Успешный POST /lead со всеми полями
2. POST /lead без `contact` → 422
3. POST /lead с `consent: false` → 400
4. GET /leads с правильным API-ключом → 200
5. GET /leads без ключа → 401
6. DELETE /lead/1 с ключом → 200
7. DELETE /lead/999 → 404

---

## 11. Что сдавать (чеклист курса)

1. GitHub-репозиторий с чистой структурой и `.gitignore`
2. README с запуском за 5–10 минут и DSGVO-заметками
3. Демо-видео 2–3 мин: запрос → SQLite → уведомление
4. Демо-видео защиты проекта
5. Отчёт по практике
6. Лог откликов (таблица + скрины/ссылки)
