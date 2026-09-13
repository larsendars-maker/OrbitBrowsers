# Настройка Admin для Larsenda

1. В Render → Orbit API → Environment добавь:

- `ORBIT_FOUNDER_USERNAME=Larsenda`
- `ORBIT_FOUNDER_EMAIL=<email аккаунта Larsenda>`
- `ORBIT_FOUNDER_PASSWORD=<временный сильный пароль>`

2. Сделай Manual Deploy.

3. При старте API создаст/обновит аккаунт Larsenda и выставит `role=admin`, титул `Создатель Orbit`, а также выдаст системные титулы `creator` и `admin`.

4. В браузере после повторного входа роль придёт из `/api/auth/session`, поэтому пункт «Админ-панель» появится автоматически.

5. На сайте открой `/admin` и войди под Larsenda. Все административные API требуют серверную роль `admin`; скрытие пункта в интерфейсе не является защитой само по себе.

После первого входа пароль лучше заменить на личный, а `ORBIT_FOUNDER_PASSWORD` удалить или заменить в Render.
