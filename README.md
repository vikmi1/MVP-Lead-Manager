# Lead-Capture Service

MVP-сервис для приёма заявок (лидов) от клиентов. Включает веб-форму для клиентов и страницу менеджера для просмотра и удаления заявок. Сохраняет в SQLite, уведомляет менеджера через лог и email.

**Стек:** Python 3.11+, FastAPI, Pydantic v2, SQLite, Jinja2, uvicorn

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
| Менеджер | `/admin` | Таблица заявок с кнопкой Löschen |

Форма отправляет данные через JavaScript fetch(), без перезагрузки страницы. Кнопка «Löschen» на странице менеджера удаляет запись и обновляет таблицу.

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

## Тесты

```bash
pytest -v
```

44 теста: модели, база данных, авторизация, уведомления, API-роуты, UI-страницы.

---

## DSGVO / Datenschutz

- Поле `consent: true` обязательно — фиксирует явное согласие пользователя
- `DELETE /lead/{id}` реализует право на забвение (Recht auf Löschung, Art. 17 DSGVO)
- `.env` и `leads.db` не коммитятся в git (`.gitignore`)
- Рекомендуемый срок хранения данных: **90 дней**
- Хостинг только на серверах в Германии / ЕС (Hetzner, STRATO, netcup)
- HTTPS обязателен при деплое (Let's Encrypt)
- Ссылка на Datenschutzerklärung должна быть рядом с формой на сайте клиента
