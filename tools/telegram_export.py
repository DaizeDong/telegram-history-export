#!/usr/bin/env python3
"""Export your own Telegram messages with context, using the official takeout API.

Why takeout: account.initTakeoutSession is Telegram's own export my data interface. It is ToS clean and
the server rate limits it gently, so a full pull in one session does not trip anti abuse. It is the
same thing the desktop export button does, only scriptable and repeatable.

This requires a healthy session from telegram_login.py. It hard fails if get_me() returns None, because
without our own id every message would be labelled not mine, which is exactly the bug that produced a
worthless all not mine corpus once before. A message is yours if msg.out is set or its sender id equals
your id; the union of the two is the reliable test.

Folders you never speak in (a lurk only folder in the Telegram app) can be excluded whole. By default
any folder whose title contains "scrape" is skipped, which drops the read only groups so they do not
drown the messages you actually wrote. Change or clear this with --exclude-folder.

Output is one JSON object per message, in the shape:
  {"text", "is_me", "ctx": "dm"|"group", "ts", "sender", "conv", "is_forward"}
The other party's words are kept as context; only their numeric id is stored, never their name.

Config directory (session and credentials, outside the repo):
  $TELEGRAM_HISTORY_EXPORT_CONFIG, else ~/.telegram-history-export-config
Output must be written outside this repository, since it is private data.

Usage: python telegram_export.py --out ~/tg-out/telegram.jsonl
"""
import argparse
import asyncio
import json
import os
import sys

BASE = os.environ.get("TELEGRAM_HISTORY_EXPORT_CONFIG") or os.path.expanduser(
    "~/.telegram-history-export-config")
CRED = os.path.join(BASE, "telegram_api.json")
SESSION = os.path.join(BASE, "tg_session")


def load_cred():
    with open(CRED, encoding="utf-8") as f:
        d = json.load(f)
    return int(d["api_id"]), d["api_hash"]


def shape_record(text, is_me, ctx, ts, sender_id, conv_id, is_forward):
    """Build one output record. Pure and testable, no telethon types."""
    return {
        "text": text,
        "is_me": bool(is_me),
        "ctx": ctx,
        "ts": int(ts) if ts is not None else None,
        "sender": "tg_%s" % (sender_id if sender_id is not None else "unknown"),
        "conv": "tg_%s" % conv_id,
        "is_forward": bool(is_forward),
    }


async def excluded_peer_ids(client, GetDialogFiltersRequest, types, needle):
    """Collect the raw peer ids of every folder whose title contains needle (case insensitive)."""
    if not needle:
        return set()
    ids = set()
    res = await client(GetDialogFiltersRequest())
    filters = res.filters if hasattr(res, "filters") else res
    for f in filters:
        if isinstance(f, types.DialogFilterDefault):
            continue
        title = getattr(f, "title", "")
        title = title.text if hasattr(title, "text") else title
        if needle.lower() not in (title or "").lower():
            continue
        for p in (getattr(f, "include_peers", None) or []):
            pid = getattr(p, "channel_id", None) or getattr(p, "chat_id", None) or getattr(p, "user_id", None)
            if pid is not None:
                ids.add(int(pid))
    return ids


async def run(out_path, limit_per_chat, exclude_folder):
    try:
        from telethon import TelegramClient
        from telethon.tl import types
        from telethon.tl.functions.account import InitTakeoutSessionRequest, FinishTakeoutSessionRequest
        from telethon.tl.functions.messages import GetDialogFiltersRequest
    except ImportError:
        sys.stderr.write("ERROR: needs telethon. pip install telethon\n")
        return 2

    if not os.path.exists(SESSION + ".session"):
        sys.stderr.write("ERROR: no session at %s. Run: python telegram_login.py\n" % (SESSION + ".session"))
        return 2
    api_id, api_hash = load_cred()
    client = TelegramClient(SESSION, api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        sys.stderr.write("ERROR: session not authorized. Rerun: python telegram_login.py\n")
        await client.disconnect()
        return 1

    me = await client.get_me()
    if me is None or not getattr(me, "id", None):
        sys.stderr.write("ERROR: get_me() gave no id. The session is broken. Rerun telegram_login.py.\n")
        await client.disconnect()
        return 1
    my_id = me.id
    print("logged in:", (me.username or me.first_name or ""), "id=", my_id)

    excluded = await excluded_peer_ids(client, GetDialogFiltersRequest, types, exclude_folder)
    if exclude_folder:
        print('excluding folder "%s": %d conversations skipped' % (exclude_folder, len(excluded)))

    try:
        await client(InitTakeoutSessionRequest(
            contacts=False, message_users=True, message_chats=True,
            message_megagroups=True, message_channels=False, files=False))
        print("takeout session opened")
    except Exception as e:
        print("takeout open failed, falling back to normal read of your own data:", str(e)[:120])

    out_abs = os.path.abspath(out_path)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if out_abs.startswith(here):
        sys.stderr.write("ERROR: refusing to write exported messages inside the repo. It is DATA.\n")
        await client.disconnect()
        return 2

    os.makedirs(os.path.dirname(out_abs) or ".", exist_ok=True)
    n = n_me = n_skip = 0
    dialogs = await client.get_dialogs()
    print("exporting %d dialogs" % len(dialogs))
    with open(out_abs, "w", encoding="utf-8") as fout:
        for dg in dialogs:
            ent = dg.entity
            if getattr(ent, "id", None) in excluded:
                n_skip += 1
                continue
            if isinstance(ent, types.User):
                if ent.bot:
                    continue
                ctx = "dm"
            elif isinstance(ent, (types.Chat, types.Channel)):
                if isinstance(ent, types.Channel) and ent.broadcast:
                    continue                     # a broadcast channel is not a conversation
                ctx = "group"
            else:
                continue
            try:
                async for msg in client.iter_messages(ent, limit=limit_per_chat):
                    if not isinstance(msg, types.Message) or not msg.message:
                        continue
                    is_me = bool(msg.out) or (msg.sender_id == my_id)
                    rec = shape_record(msg.message, is_me, ctx,
                                       int(msg.date.timestamp()) if msg.date else None,
                                       msg.sender_id, dg.id, msg.fwd_from is not None)
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n += 1
                    n_me += 1 if is_me else 0
            except Exception as e:
                sys.stderr.write("  dialog tg_%s read error (skipped): %s\n" % (dg.id, str(e)[:100]))

    try:
        await client(FinishTakeoutSessionRequest(success=True))
    except Exception:
        pass
    await client.disconnect()
    print("\ndone. wrote %d messages (%d yours, %d others), skipped %d excluded dialogs -> %s"
          % (n, n_me, n - n_me, n_skip, out_abs))
    if n_me == 0:
        sys.stderr.write("WARN: zero of your own messages. Check the session and my_id.\n")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description="export your own Telegram messages with context")
    ap.add_argument("--out", required=True, help="output jsonl path (must be outside this repo)")
    ap.add_argument("--limit-per-chat", type=int, default=0, help="max messages per dialog, 0 = all")
    ap.add_argument("--exclude-folder", default="scrape",
                    help='skip dialogs in any folder whose title contains this (case insensitive); '
                         'empty string disables exclusion')
    a = ap.parse_args()
    limit = a.limit_per_chat if a.limit_per_chat > 0 else None
    sys.exit(asyncio.run(run(a.out, limit, a.exclude_folder)))


if __name__ == "__main__":
    main()
