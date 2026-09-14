# Orbit Browser v1.12 — Project Audit

## Verified in this workspace
- Python source files compile with `py_compile`.
- Required Windows internal-tab methods exist.
- Required Android project files exist.
- Website and games pages exist.
- Secret scanner reports no high-confidence secrets.
- Build cache / Python bytecode cleaned from release source.

## Release architecture
- Windows: GitHub Actions -> EXE + Portable EXE + Setup EXE.
- Android: GitHub Actions -> APK + AAB.
- Website: Netlify/static landing with direct download redirects.
- Backend: Render Web Service + PostgreSQL through environment variables.

## UX goals implemented
- Single-window desktop navigation.
- Internal pages as Orbit tabs.
- Fast mode is always active; no artificial performance toggle.
- Session tab recovery and last closed tab recovery.
- Keyboard shortcuts for common browser actions.
- Background sync and delayed update checks.
- Google default search with user-selectable providers.
- Themes persist without reload.
- Admin panel gated by role in UI and backend.

## Known verification boundary
A full native Windows executable launch and a full Android Gradle build are release-environment tests and should be executed by GitHub Actions before publishing a production release.
