# Security

- Реальные секреты не хранятся в Git.
- `.env`, ключи, сертификаты, keystore и credentials исключены через `.gitignore`.
- Production secrets должны храниться в Render/GitHub Secrets.
- Пароли пользователей хранятся только в виде хеша.
- APK/EXE артефакты не хранятся в исходном дереве.
- Публичные релизы не должны содержать `database`, access tokens, private keys или реальные credentials.
