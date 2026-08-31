# Telegram export: what to know before you trust the output

Short notes on the two things that actually matter here, so the next export does not repeat the mistakes
that made a first attempt worthless.

## Use takeout, not a scrape

`account.initTakeoutSession` is Telegram's official export my data path. It is ToS clean and the server
rate limits it gently, so pulling a full history in one session does not trip anti abuse. It is the same
thing the desktop client's export button does. There is no reason to hammer normal message reads when
this exists.

## The session is the whole game, and the tdata route is a trap

The tempting shortcut is to convert an already logged in desktop session from its tdata folder with a
library like opentele, so you skip the phone code. Do not. That converted session connects and even
reports as authorized, but get_me() returns None. When you do not know your own id, telethon's out flag
comes back False for everything, so every message you ever sent gets labelled not mine. A first export
this way produced hundreds of thousands of rows with zero marked as the owner's, which is useless for
anything that needs your own voice. The converted key also tended to get deregistered by the server.

The fix is a real interactive login (telegram_login.py), and two hard gates that refuse to proceed when
the session is bad: get_me() must not be None, and it must carry an id. Both the login and the export
check this and fail loudly rather than emit a silent all not mine corpus.

## Decide authorship by a union, not by the out flag alone

A message is yours if `msg.out` is set OR its `sender_id` equals your id. Relying on `msg.out` by itself
is what turned into an all not mine corpus on the broken session. The sender id comparison is the
backstop that survives a session that is merely degraded.

## Exclude the folders you never speak in

Telegram folders are dialog filters with titles. If you keep a folder for groups you only lurk in (here
it was literally titled Scrape, holding 170 groups), those groups otherwise dominate the export with
other people's messages and drown the handful you wrote. The exporter reads the dialog filters, collects
the peers of any folder whose title contains the exclusion word, and skips them. On the reference
account this took the owner's own message count from effectively zero visible in the noise to several
thousand clean. The default exclusion word is scrape; change or clear it with `--exclude-folder`.

## Operational gotchas

The session file is a small SQLite database. If a previous export is still running and holds it open, a
new run fails with database is locked. Let the prior run finish or stop it by its exact process id, and
work on a copy of the session if you must run two things at once.

A very large public group can carry hundreds of thousands of other people's messages. If you only want
your own voice and the group's immediate context, cap the pull with `--limit-per-chat`, or exclude the
group by putting it in your excluded folder. Full context is the default because the other party's words
are what make a turn readable later.
