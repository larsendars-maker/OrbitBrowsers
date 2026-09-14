# Security

- Не храните реальные API keys, пароли, токены, `.env`, сертификаты и приватные ключи в Git.
- Production secrets задаются только через GitHub Actions Secrets/Variables или секреты Render.
- `.gitignore` блокирует `.env`, ключи, сертификаты и локальные build outputs.
- Клиентские сборки не должны содержать `GEMINI_API_KEY`, `DATABASE_URL`, `ORBIT_FOUNDER_PASSWORD` или другие серверные секреты.
- Локальный токен аккаунта должен считаться чувствительными данными; не публикуйте каталог `%LOCALAPPDATA%\OrbitBrowser`.
