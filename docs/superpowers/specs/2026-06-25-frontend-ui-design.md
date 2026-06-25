# Frontend UI — Design Spec

**Дата:** 2026-06-25  
**Проект:** Lead-Capture Service — веб-интерфейс  
**Статус:** Утверждён

---

## 1. Цель

Добавить два HTML-страницы поверх существующего FastAPI API:
- Публичная форма для клиентов (Autohaus, и т.д.)
- Страница менеджера для просмотра и удаления заявок

Цель — демо-видео курса и реальное использование нетехническим менеджером.

---

## 2. Стек

| Компонент | Выбор |
|---|---|
| Шаблонизатор | **Jinja2** (стандарт FastAPI) |
| Стили | Чистый CSS (без фреймворков) |
| JS | Минимальный vanilla JS только для UX |
| Новые зависимости | `jinja2`, `python-multipart` |

---

## 3. Страницы

### 3.1 Форма для клиента — `GET /`

**Файл:** `templates/form.html`

**Поля:**
- Name (optional) — текстовый input
- E-Mail oder Telefon (обязательно) — текстовый input
- Betreff / Source (optional) — текстовый input
- Nachricht / Comment (optional) — textarea
- DSGVO checkbox — обязательно отмечен для отправки

**Поведение:**
- Форма отправляет `POST /lead` через JavaScript fetch()
- При успехе показывает сообщение: «Vielen Dank! Wir melden uns bald.»
- При ошибке (нет contact, нет consent) показывает сообщение об ошибке
- Ссылка на `/admin` в навигации

### 3.2 Страница менеджера — `GET /admin`

**Файл:** `templates/admin.html`

**Содержимое:**
- Таблица всех лидов из БД
- Колонки: №, Имя, Контакт, Betreff, Дата, Кнопка «Löschen»
- Кнопка «Löschen» отправляет `POST /admin/delete/{id}` и обновляет страницу
- Счётчик заявок вверху
- Ссылка «← Zur Anfrage-Seite» обратно на форму

**Доступ:** без авторизации (для MVP/демо)

---

## 4. Новые роуты в app.py

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/` | Отдаёт `form.html` |
| `GET` | `/admin` | Читает лиды из БД, отдаёт `admin.html` |
| `POST` | `/admin/delete/{lead_id}` | Удаляет лид, редиректит на `/admin` |

Роут `DELETE /lead/{id}` (API) остаётся без изменений — требует X-API-Key, для Swagger и программного использования.  
`POST /admin/delete/{lead_id}` — новый, **без API-ключа**, только для HTML-формы в браузере (MVP/демо).

---

## 5. Структура файлов

```
lead-service/
├── app.py                    ← добавить 3 новых роута + Jinja2 setup
├── templates/
│   ├── form.html             ← новый
│   └── admin.html            ← новый
├── static/
│   └── style.css             ← новый
└── requirements.txt          ← добавить jinja2, python-multipart
```

---

## 6. Дизайн страниц

### form.html — внешний вид
- Белая карточка по центру на светлом фоне
- Заголовок: «Neue Anfrage — [название компании]»
- Поля с немецкими лейблами
- Зелёная кнопка «Anfrage senden →»
- После успешной отправки: зелёное сообщение «Vielen Dank! Wir melden uns bald.»
- Внизу мелко: ссылка «Admin-Bereich →»

### admin.html — внешний вид
- Заголовок «Eingegangene Anfragen» + счётчик
- Таблица с чередованием строк
- Красная кнопка «Löschen» в каждой строке
- Ссылка «← Zurück zur Anfrage-Seite»

---

## 7. Обработка ошибок (Frontend)

| Ситуация | Что показывает форма |
|---|---|
| Нет contact | «Bitte geben Sie Ihre Kontaktdaten ein» |
| Нет consent | «Bitte stimmen Sie der Datenverarbeitung zu» |
| Сервер недоступен | «Ein Fehler ist aufgetreten. Bitte versuchen Sie es später.» |
| Успех | «Vielen Dank! Wir melden uns bald.» |

---

## 8. Что НЕ входит в этот spec

- Авторизация admin-страницы (будет в следующей версии)
- Email-уведомления (отдельный шаг)
- Мобильная адаптация (базовый responsive)
- Пагинация в таблице лидов
