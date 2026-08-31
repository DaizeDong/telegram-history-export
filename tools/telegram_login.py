#!/usr/bin/env python3
"""Interactive Telegram login that produces one clean, working telethon session.

Only the account owner can run this. Telegram sends a code to the owner's Telegram app, and the script
stops to read it from the terminal (and a two step password if that is set). An agent's shell is not an
interactive terminal, so it hangs at that prompt. Run this yourself in a real cmd, PowerShell, or Git
Bash window.

Why a proper login matters: a session converted from the desktop tdata folder connects and even reports
as authorized, but get_me() returns None, so every message's out flag is False and a whole export gets
labelled not mine. That key also tends to get deregistered by the server. This script hard fails if
get_me() returns None, so a broken session never reaches the exporter.

Run it once. The session file is full account credentials. It lives in the private config directory,
never in any git repository. After this, telegram_export.py runs unattended.

Config directory (session and api credentials live here, outside the repo):
  $TELEGRAM_HISTORY_EXPORT_CONFIG, else ~/.telegram-history-export-config
The credentials file telegram_api.json in that directory must contain:
  {"api_id": 123456, "api_hash": "..."}
Get api_id and api_hash from https://my.telegram.org.

Usage: python telegram_login.py
"""
import asyncio
import json
import os
import sys

BASE = os.environ.get("TELEGRAM_HISTORY_EXPORT_CONFIG") or os.path.expanduser(
    "~/.telegram-history-export-config")
CRED = os.path.join(BASE, "telegram_api.json")
SESSION = os.path.join(BASE, "tg_session")     # telethon appends the .session suffix


def load_cred():
    if not os.path.exists(CRED):
        sys.stderr.write("ERROR: credentials file not found: %s\n" % CRED)
        sys.stderr.write('       It must contain {"api_id": 123456, "api_hash": "..."}\n')
        sys.stderr.write("       Get these from https://my.telegram.org\n")
        sys.exit(2)
    with open(CRED, encoding="utf-8") as f:
        d = json.load(f)
    return int(d["api_id"]), d["api_hash"]


async def _cleanup_partial(client, path, preexisting):
    """A login that did not finish must not leave an unauthorized session behind, or the next run
    thinks it is already logged in."""
    try:
        await client.disconnect()
    except Exception:
        pass
    if preexisting:
        return
    for f in (path, path + "-journal"):
        try:
            if os.path.exists(f):
                os.remove(f)
                print("cleaned up the unfinished session:", f)
        except OSError:
            pass


async def main():
    try:
        from telethon import TelegramClient
    except ImportError:
        sys.stderr.write("ERROR: needs telethon. pip install telethon\n")
        return 2

    api_id, api_hash = load_cred()
    os.makedirs(BASE, exist_ok=True)
    path = SESSION + ".session"
    if os.path.exists(path):
        print("A session already exists at %s" % path)
        print("If it is healthy this login reuses it and asks for no code. To start over, rename it.")

    if not sys.stdin.isatty():
        sys.stderr.write(
            "ERROR: this is not an interactive terminal, so the login would hang at the code prompt.\n"
            "       Run this script yourself in a real cmd, PowerShell, or Git Bash window.\n")
        return 2

    print("Connecting to Telegram. You will be asked for your phone number with country code, then")
    print("the code sent to your Telegram app, and a password if two step verification is on.\n")

    preexisting = os.path.exists(path)
    client = TelegramClient(SESSION, api_id, api_hash)
    try:
        await client.start()                 # interactive: phone, then code, then optional 2FA
    except EOFError:
        sys.stderr.write("\nERROR: cannot read input; this is not an interactive terminal.\n"
                         "       Run it yourself in a real terminal window.\n")
        await _cleanup_partial(client, path, preexisting)
        return 2
    except KeyboardInterrupt:
        sys.stderr.write("\ncancelled.\n")
        await _cleanup_partial(client, path, preexisting)
        return 130

    if not await client.is_user_authorized():
        sys.stderr.write("ERROR: the login finished but the session is still not authorized.\n")
        await client.disconnect()
        return 1

    me = await client.get_me()
    if me is None:
        sys.stderr.write(
            "ERROR: get_me() returned None. This session is broken the same way the tdata route is.\n"
            "       Do not export with it; it would produce an all not mine corpus.\n")
        await client.disconnect()
        return 1

    await client.disconnect()
    print("\nLogged in, session healthy.")
    print("  account id: %s" % me.id)
    print("  username  : %s" % (me.username or "(none)"))
    print("  session   : %s" % path)
    print("\nYou are done. The export can now run unattended: python telegram_export.py")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
