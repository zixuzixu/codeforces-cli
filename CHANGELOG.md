# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0.0] - 2026-04-16

### Changed
- Migrated HTTP client from curl_cffi to nodriver (Chrome DevTools Protocol) to bypass Cloudflare Turnstile protection. Codeforces upgraded their anti-bot system and curl-based clients can no longer access the site.
- Browser runs in headed mode via Xvfb virtual display for Cloudflare compatibility. Requires `xvfb` package on headless systems.
- POST requests now use in-browser `fetch()` to maintain the authenticated browser session.
- Updated tests to work with the new browser-based client architecture.

### Added
- Cloudflare detection on both GET and POST responses. The CLI now raises a clear error instead of silently returning challenge HTML.
- Xvfb startup verification. Fails fast with a clear message if the virtual display fails to start.
- Timeout on browser operations (120s default) to prevent permanent hangs.
- Graceful Xvfb shutdown with fallback to SIGKILL on timeout.

## [0.1.0] - 2026-04-14

- Initial release with contest listing, problem download, submit, and status commands.
