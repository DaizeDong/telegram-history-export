# Changelog

## Unreleased

- Each record now also carries `sender_name`, `sender_username` and `conv_title`, the readable identity telethon has already resolved at export time. Numeric ids alone make an export unreadable to its owner, and recovering the names later needs a fresh login and a re-query of every peer. All three are null when Telegram has nothing to give. The seven existing fields are unchanged.

## 0.1.0 (2026-08-30)

Initial release. Export your own Telegram history with context via the official takeout API.

- Interactive login (telegram_login.py) that hard fails if get_me() returns None, so a broken session never reaches the exporter.
- Export (telegram_export.py) with the union is-me rule, takeout session, per message context, and folder exclusion (default: any folder whose title contains scrape).
- Sessions and credentials live in a private config directory, never in the repo; output is written outside the repo.
- Synthetic unit tests and data boundary gates.
