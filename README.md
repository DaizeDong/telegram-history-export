# telegram-history-export

Export your own Telegram message history, with context, into structured JSON, using Telegram's own
takeout API. Sibling to the discord and qq history tools, same shape, so a future export is a couple of
commands rather than a fresh investigation.

Chat history is private data. It never enters this repository. The telethon session is full account
credentials and lives in a private config directory, never in git. Only synthetic fixtures ship, and a
data boundary gate enforces it.

## Two steps

First log in once, yourself, in a real terminal. Telegram sends a code to your app, so this cannot run
unattended:

```
python tools/telegram_login.py
```

It writes a session to the private config directory and hard fails if the session is broken. Put your
api_id and api_hash (from https://my.telegram.org) in `telegram_api.json` in that directory first.

Then export, which can run unattended:

```
python tools/telegram_export.py --out ~/tg-out/telegram.jsonl
```

This pulls your dialogs through the takeout API, writes one JSON record per message with the other
party's words kept as context, and skips any folder whose title contains scrape so read only groups do
not drown the messages you wrote. Change or clear that with `--exclude-folder`.

## Why it is built this way

Telegram's takeout API is the same export the desktop app offers, so it is ToS clean and the server
rate limits it gently. The one real trap is the session. A session converted from the desktop tdata
folder connects and reports authorized but returns None from get_me(), so every message's out flag is
False and the whole export gets labelled not mine. Both tools hard fail on that, and authorship is
decided by the union of the out flag and sender id equals your id, not by the out flag alone. See
`docs/NOTES.md`.

## Config directory

Set `$TELEGRAM_HISTORY_EXPORT_CONFIG`, or the default `~/.telegram-history-export-config` is used. It
holds `telegram_api.json` with your api credentials and the `tg_session` file after login. Both are
private and must never be committed.

## Requirements

Python with `telethon`. Nothing else. The login step needs a real interactive terminal; the export step
does not.

## Output record

```
{"text", "is_me", "ctx": "dm"|"group", "ts", "sender", "conv", "is_forward",
 "sender_name", "sender_username", "conv_title"}
```

`sender` and `conv` are numeric ids and are what to key on, since a name is not unique and people change theirs. Records are appended in the order the takeout returns them.

`sender_name`, `sender_username` and `conv_title` are the readable identity Telegram had already handed us: a user's first and last name joined, or a group or channel title; the handle with no leading `@`; and the conversation's own name. They exist because numeric ids alone make an export unreadable to the person who owns it, and because they are free now and expensive later: telethon has already resolved the peer, whereas recovering the names afterwards means logging back in and re-querying every peer in the file. All three are best effort and are null, never empty strings, when there is nothing to give, which happens for deleted accounts, for channels with only a title, and for anonymous posts. See `docs/NOTES.md`.

## Data boundary

The session, the credentials, and the exported jsonl are all real run output. They are declared in
`.dataclass.json` and never committed. Tests run against synthetic records, so no real account is needed
to exercise the code.
