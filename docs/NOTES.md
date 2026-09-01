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

## Keep the names, not just the ids

An export keyed only by numeric ids is unreadable to the person who owns it. `tg_123456789` said something to `tg_987654321` in `tg_-1001234` tells you nothing about who was talking or which group it was, and every later question, whose voice is this, which conversation do I want, has to be answered by hand. So each record also carries `sender_name` (a user's first and last name joined, or a group or channel's title), `sender_username` (the handle with no leading `@`), and `conv_title` (the conversation's own readable name).

The reason to capture them at export time is asymmetric cost. Telethon has already resolved the peer entity by the time the message reaches us, so reading the name and handle off it costs no extra request and no extra second. Recovering the same names afterwards costs a fresh login, a live session, and a re-query of every peer in the file, and that is exactly the position a first export left us in.

All three are best effort and are null, never empty strings, when Telegram has nothing to give. Deleted accounts have no name and no handle, some channels have a title and nothing else, and an anonymous channel post has no sender entity at all. A downstream reader can always ask for the key; it may get `None`. The numeric fields `sender` and `conv` are unchanged and remain the thing to key on, since a name is not unique and a person can change theirs.

Names are private data, like the message text they sit next to. They live only in the exported jsonl, which is written outside this repository and is declared DATA in `.dataclass.json`. Nothing readable ever enters the repo; the tests run on synthetic peers.

## Operational gotchas

The session file is a small SQLite database. If a previous export is still running and holds it open, a
new run fails with database is locked. Let the prior run finish or stop it by its exact process id, and
work on a copy of the session if you must run two things at once.

A very large public group can carry hundreds of thousands of other people's messages. If you only want
your own voice and the group's immediate context, cap the pull with `--limit-per-chat`, or exclude the
group by putting it in your excluded folder. Full context is the default because the other party's words
are what make a turn readable later.
