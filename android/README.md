Orbit Browser Android 1.1

Нативный Android-клиент Orbit. Сборка выполняется только через GitHub Actions.

## Обновления Android

GitHub Actions публикует только `OrbitBrowser.apk`. Для установки обновлений поверх уже установленного приложения APK должен быть подписан одним и тем же ключом. Добавь в Secrets репозитория:

- `ORBIT_ANDROID_KEYSTORE_B64` — keystore в Base64;
- `ORBIT_ANDROID_STORE_PASSWORD`;
- `ORBIT_ANDROID_KEY_ALIAS`;
- `ORBIT_ANDROID_KEY_PASSWORD`.

После этого Orbit сможет проверять новую версию, скачивать APK и передавать его системному установщику. Android всё равно может показать системное подтверждение установки.
