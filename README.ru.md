[English](README.md) · [Deutsch](README.de.md) · **Русский**

# Lead-Capture Service

MVP-сервис для приёма заявок (лидов) от клиентов. Включает веб-форму для клиентов и страницу менеджера для просмотра, удаления и экспорта заявок. Сохраняет в SQLite, уведомляет менеджера через лог-файл и email, дублирует заявки в Google-таблицу.

## Живое демо

**[https://vibecoding.aithinglab.com/mvp-lead-manager/](https://vibecoding.aithinglab.com/mvp-lead-manager/)** — форма, страница менеджера ([/admin](https://vibecoding.aithinglab.com/mvp-lead-manager/admin)) и Swagger UI ([/docs](https://vibecoding.aithinglab.com/mvp-lead-manager/docs)).
Демо работает в демо-режиме: введённые данные видны всем, email и Google Sheets отключены, а каждые 30 минут база сбрасывается к примерам заявок — не вводите реальные персональные данные.

## Скриншоты

| Форма заявки для клиента | Страница менеджера |
|---|---|
| ![Форма заявки](screenshots/form.png) | ![Страница менеджера со списком заявок](screenshots/admin.png) |

<details><summary>Swagger UI (REST API)</summary>

![Swagger UI](screenshots/swagger.png)
</details>

**Стек:** Python 3.11+, FastAPI, Pydantic v2, SQLite, Jinja2, uvicorn

**Возможности:**
- Веб-форма для клиента + страница менеджера
- Хранение в SQLite
- Уведомления: лог-файл, email менеджеру, автозапись в Google Sheets
- Экспорт заявок в CSV и JSON
- REST API с авторизацией по ключу
- DSGVO: согласие, право на удаление, данные на своём сервере

---

## Запуск за 5–10 минут

### 1. Клонировать и установить зависимости

```bash
git clone https://github.com/vikmi1/MVP-Lead-Manager.git
cd MVP-Lead-Manager
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

Вставить в `.env` как `API_KEY=...`.

Переменные `.env`:

| Переменная | Назначение | Обязательно |
|---|---|---|
| `API_KEY` | Ключ для защищённых эндпоинтов `/leads`, `/lead/{id}` | да |
| `SMTP_HOST` / `SMTP_PORT` | SMTP-сервер (по умолчанию `smtp.gmail.com:587`) | для email |
| `SMTP_USER` / `SMTP_PASS` | Логин и App Password почты-отправителя | для email |
| `MANAGER_EMAIL` | Куда приходят уведомления о заявках | для email |
| `SHEETS_WEBHOOK_URL` | URL Apps Script веб-приложения | для Google Sheets |
| `DB_PATH` / `LOG_PATH` | Путь к базе и лог-файлу | нет (есть значения по умолчанию) |

Email и Google Sheets опциональны: если переменные пустые, сервис просто пропускает эти уведомления. Настройка — в разделах ниже.

### 3. Запустить сервер

```bash
uvicorn app:app --reload
```

| Страница | URL |
|---|---|
| Форма для клиента | http://localhost:8000 |
| Страница менеджера | http://localhost:8000/admin |
| Swagger UI | http://localhost:8000/docs |

### 4. Тестовый запрос

```bash
curl -X POST http://localhost:8000/lead \
  -H "Content-Type: application/json" \
  -d '{"contact": "test@example.de", "consent": true}'
```

---

## Веб-интерфейс

| Страница | Путь | Описание |
|---|---|---|
| Форма | `/` | Клиент вводит контакт, даёт согласие DSGVO |
| Менеджер | `/admin` | Таблица заявок, кнопка Löschen, кнопки экспорта CSV/JSON |

Форма отправляет данные через JavaScript fetch(), без перезагрузки страницы. Кнопка «Löschen» на странице менеджера удаляет запись и обновляет таблицу.

---

## Экспорт данных

На странице `/admin` есть кнопки «⬇ CSV» и «⬇ JSON» для выгрузки всех заявок.

| Метод | Путь | Описание |
|---|---|---|
| GET | `/admin/export.csv` | Скачать все заявки в CSV (с BOM — корректные умляуты в Excel) |
| GET | `/admin/export.json` | Скачать все заявки в JSON |

---

## Email-уведомления (Gmail)

1. Включить **2-Step Verification** в Google-аккаунте отправителя
2. Создать **App Password**: https://myaccount.google.com/apppasswords (16 символов)
3. Заполнить в `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=твой@gmail.com
   SMTP_PASS=<16-символьный App Password без пробелов>
   MANAGER_EMAIL=куда-слать@gmail.com
   ```
4. Перезапустить сервер. При каждой новой заявке менеджеру уходит письмо «Neue Lead-Anfrage #N».

Обычный пароль Gmail не подойдёт — нужен именно App Password.

---

## Google Sheets (Apps Script Webhook)

1. Создать Google-таблицу с заголовками: `Datum | ID | Name | Kontakt | Betreff | Nachricht | Consent`
2. **Расширения → Apps Script**, вставить код:
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
3. **Развернуть → Новое развёртывание** → тип «Веб-приложение», доступ «Все»
4. Скопировать URL (заканчивается на `/exec`) и вписать в `.env`:
   ```
   SHEETS_WEBHOOK_URL=https://script.google.com/macros/s/.../exec
   ```
5. Перезапустить сервер. Каждая заявка автоматически добавляется строкой в таблицу.

---

## API

| Метод | Путь | Доступ | Описание |
|---|---|---|---|
| POST | `/lead` | открытый | Создать новую заявку |
| GET | `/leads` | X-API-Key | Список всех заявок |
| DELETE | `/lead/{id}` | X-API-Key | Удалить заявку (DSGVO) |

Полная документация: http://localhost:8000/docs

---

## Смена API-ключа

1. Сгенерировать новый: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Заменить `API_KEY` в `.env`
3. Перезапустить: `uvicorn app:app --reload`

---

## DSGVO / Datenschutz

- Поле `consent: true` обязательно — фиксирует явное согласие пользователя
- `DELETE /lead/{id}` реализует право на забвение (Recht auf Löschung, Art. 17 DSGVO)
- `.env` и `leads.db` не коммитятся в git (`.gitignore`)
- Рекомендуемый срок хранения данных: **90 дней**
- Хостинг только на серверах в Германии / ЕС (Hetzner, STRATO, netcup)
- HTTPS обязателен при деплое (Let's Encrypt)
- Ссылка на Datenschutzerklärung должна быть рядом с формой на сайте клиента
- ⚠️ При включённой интеграции с Google Sheets данные заявок передаются на серверы Google (США). Для строгого DSGVO это нужно отразить в Datenschutzerklärung или отключить интеграцию (оставить `SHEETS_WEBHOOK_URL` пустым)
