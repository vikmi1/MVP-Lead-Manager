# Отчёт по практике — Lead-Capture Service

**Курс:** Профессия Вайб-кодер, zerocoder.ru  
**Студент:** Viktor  
**Дата:** 25.06.2026

---

## 1. Кому и какую задачу решает проект

Сервис предназначен для малого и среднего бизнеса (автосалоны, сервисные центры, агентства), которым нужно принимать заявки от клиентов через сайт. Клиент заполняет форму с контактными данными и согласием на обработку (DSGVO/GDPR), данные сохраняются в базе и немедленно уведомляют менеджера. Менеджер видит все заявки в отдельной веб-панели и может выгрузить их в CSV / JSON или удалить запись по требованию клиента (право на забвение, Art. 17 DSGVO).

---

## 2. Входные данные

Принимает `POST /lead` с JSON-телом:

| Поле | Тип | Обязательно | Описание |
|---|---|---|---|
| `contact` | string | **да** | Email или телефон клиента |
| `consent` | bool | **да** | Явное согласие на обработку данных (DSGVO) |
| `name` | string | нет | Имя клиента |
| `source` | string | нет | Тема / откуда узнал (например, «VW Tiguan», «Probefahrt») |
| `comment` | string | нет | Произвольный комментарий |

Пример минимального запроса:
```json
{"contact": "max@beispiel.de", "consent": true}
```

Пример полного запроса:
```json
{
  "contact": "max@beispiel.de",
  "name": "Max Müller",
  "source": "VW Tiguan Anfrage",
  "comment": "Interesse an Leasing",
  "consent": true
}
```

---

## 3. Выход / результат

При успешной заявке бизнес получает сразу три канала уведомления:

1. **Запись в SQLite** — поля id, created\_at, name, contact, source, comment, consent. Данные хранятся локально, на своём сервере.
2. **Строка в лог-файле** — `events.log` с временной меткой UTC, id заявки и контактом. Служит для отладки и аудита.
3. **Email менеджеру** — письмо «Neue Lead-Anfrage #N» через Gmail SMTP с полными данными заявки.
4. **Строка в Google Sheets** — через Apps Script Webhook (Datum, ID, Name, Kontakt, Betreff, Nachricht, Consent).

Ответ API:
```json
{"status": "ok", "message": "Anfrage gespeichert", "lead_id": 42}
```

Email и Sheets опциональны: если переменные окружения пустые, сервис пропускает канал без ошибки.

---

## 4. Архитектура

```
HTTP POST /lead
    │
    ▼
FastAPI endpoint (app.py)
    │  Pydantic v2 валидация (models.py)
    │  — contact обязателен, consent: bool обязателен
    │  — автоматический 422 при невалидных данных
    │
    ▼
database.create_lead() (database.py)
    │  INSERT в SQLite через стандартный sqlite3
    │  Возвращает lead_id (ROWID)
    │
    ▼
notifier.log_event()     — запись строки в events.log
notifier.send_email()    — SMTP STARTTLS → Gmail
notifier.send_to_sheet() — urllib.request POST → Apps Script Webhook
    │  Каждый канал в отдельном try/except:
    │  сбой email/Sheets не роллбэкит сохранение в БД
    │
    ▼
{"status": "ok", "lead_id": N}
```

Дополнительные эндпоинты:

| Путь | Доступ | Назначение |
|---|---|---|
| `GET /` | открытый | Клиентская форма (Jinja2 + fetch) |
| `GET /admin` | открытый | Панель менеджера (таблица + экспорт) |
| `GET /leads` | X-API-Key | REST: список заявок |
| `DELETE /lead/{id}` | X-API-Key | REST: удаление (DSGVO) |
| `GET /admin/export.csv` | открытый | Скачать CSV (UTF-8 BOM для Excel) |
| `GET /admin/export.json` | открытый | Скачать JSON |

---

## 5. Как запустить

```bash
git clone <repo-url>
cd lead-service
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env   # заполнить API_KEY минимально
uvicorn app:app --reload
```

- Форма клиента: http://localhost:8000  
- Панель менеджера: http://localhost:8000/admin  
- Swagger UI: http://localhost:8000/docs  

Подробная инструкция, настройка Gmail App Password и Apps Script — в [README.md](README.md).

---

## 6. Демонстрация

> *(Добавить ссылку на видео или скриншоты после записи)*

Предлагаемый сценарий демо:
1. Открыть http://localhost:8000 → заполнить форму → отправить
2. Открыть http://localhost:8000/admin → убедиться, что заявка появилась
3. Нажать «⬇ CSV» → открыть файл в Excel с правильными умлаутами
4. Проверить почту — письмо «Neue Lead-Anfrage #1»
5. Открыть Google Sheets — новая строка

---

## 7. Ошибки и как решал

**1. `jinja2` установился глобально, а не в .venv**  
Subagent запустил `pip install` без явного пути к интерпретатору venv. Сервер не видел шаблоны. Решение: всегда использовать `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

**2. Устаревший синтаксис `TemplateResponse` в Starlette 0.38+**  
Старый вызов `TemplateResponse("form.html", {"request": request})` вызывал DeprecationWarning и будет сломан в следующих версиях. Поправил на `TemplateResponse(request, "form.html")` — request передаётся первым позиционным аргументом.

**3. Несколько «мёртвых» процессов uvicorn занимали порт 8000**  
После добавления новых роутов старый процесс (запущенный до изменений) всё ещё держал порт. Браузер показывал `{"detail":"Not Found"}`. Решение: `Get-Process python | Stop-Process` — завершить все Python-процессы и запустить сервер заново.

**4. `UnicodeEncodeError` при тестовом print с кириллицей**  
Windows-консоль использует cp1252. `print("отправлено на", email)` падала с ошибкой, хотя email ушёл успешно. Решение: заменить на `print("EMAIL OK: sent to", email)` — только ASCII в print-отладке.

**5. Apps Script «Datei kann derzeit nicht geöffnet werden»**  
Конфликт нескольких Google-аккаунтов в браузере. Скрипт открывался под неверным аккаунтом. Решение: открыть в режиме инкогнито, войти только с тестовым аккаунтом.

---

## 8. Что улучшить в v2

| Направление | Описание |
|---|---|
| **Дедупликация** | Отклонять повторный `contact` за последние N минут (rate-limit по IP + contact) |
| **Деплой** | Dockerfile + docker-compose, деплой на Hetzner/netcup с HTTPS (Let's Encrypt) |
| **Авторизация /admin** | Сейчас панель открыта без пароля. Добавить HTTP Basic Auth или сессии |
| **Pagination в /admin** | При 1000+ заявках таблица тормозит. Добавить постраничный вывод |
| **Вебхук Slack/Telegram** | Уведомление в рабочий чат быстрее email |
| **Soft-delete** | Вместо физического удаления — пометка `deleted_at`, для аудиторского следа |
| **Миграции БД** | Сейчас схема создаётся через `CREATE TABLE IF NOT EXISTS`. При изменении схемы — ручная миграция. Добавить Alembic или простые версионированные SQL-скрипты |

---

## 9. Лог откликов (30 шт.)

> Заполнить по мере поступления ответов. Формат: площадка/чат → ссылка или скрин → дата → текст отклика.

| # | Площадка / чат | Ссылка / скрин | Дата | Текст отклика |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |
| 11 | | | | |
| 12 | | | | |
| 13 | | | | |
| 14 | | | | |
| 15 | | | | |
| 16 | | | | |
| 17 | | | | |
| 18 | | | | |
| 19 | | | | |
| 20 | | | | |
| 21 | | | | |
| 22 | | | | |
| 23 | | | | |
| 24 | | | | |
| 25 | | | | |
| 26 | | | | |
| 27 | | | | |
| 28 | | | | |
| 29 | | | | |
| 30 | | | | |
