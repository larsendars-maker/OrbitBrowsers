Orbit Browser 1.9 patch

- /games and /games.html are served by the backend and /games is rewritten by Netlify.
- Website mini-games no longer depend on an API endpoint.
- Public stats now include visitors_today (distinct visitor keys for the current DB date).
- Internal desktop mini-games open in a regular Orbit tab, not a second window.
- Existing Notes/Admin/Help use the internal-tab system.
- Startup remains non-blocking: network/analytics are background operations.
