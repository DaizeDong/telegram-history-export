# Changelog

## Unreleased

- The guards and style submodules are gone. `tools/storage_paths.py` resolves the companion through the installed `fleet_guards` package (`companion_resolver(source_root=...)`), and a missing package is an error that names `pip install -e "$(git config --get fleet.guards)"`. The `.githooks/` shims run the local fleet-guards and fleet-style checkouts named by `git config fleet.guards` and `fleet.style`, and the pii-guard, dash-guard and fleet-sync workflows were removed.
- Each record now also carries `sender_name`, `sender_username` and `conv_title`, the readable identity telethon has already resolved at export time. Numeric ids alone make an export unreadable to its owner, and recovering the names later needs a fresh login and a re-query of every peer. All three are null when Telegram has nothing to give. The seven existing fields are unchanged.

## 0.1.0 (2026-08-30)

Initial release. Export your own Telegram history with context via the official takeout API.

- Interactive login (telegram_login.py) that hard fails if get_me() returns None, so a broken session never reaches the exporter.
- Export (telegram_export.py) with the union is-me rule, takeout session, per message context, and folder exclusion (default: any folder whose title contains scrape).
- Sessions and credentials live in a private config directory, never in the repo; output is written outside the repo.
- Synthetic unit tests and data boundary gates.
