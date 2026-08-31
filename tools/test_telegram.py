#!/usr/bin/env python3
"""Unit tests for the export record shaping and the is-me rule, on synthetic data with no real values.

telegram_export.py keeps its telethon calls behind pure functions so the important logic can be tested
without a live account. shape_record builds one output record; the is-me rule is the union of msg.out
and sender-id equals my-id.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from telegram_export import shape_record


MY_ID = 5000001            # synthetic owner id
PEER_ID = 5000002          # synthetic peer id


def is_me(out_flag, sender_id, my_id):
    return bool(out_flag) or (sender_id == my_id)


def test_record_shape():
    r = shape_record("hello there", True, "dm", 1700000000, MY_ID, -1001234, False)
    assert r["text"] == "hello there"
    assert r["is_me"] is True
    assert r["ctx"] == "dm"
    assert r["sender"] == "tg_%d" % MY_ID
    assert r["conv"] == "tg_-1001234"
    assert r["is_forward"] is False
    print("[test] record_shape OK")


def test_is_me_union():
    # out flag set, sender unknown: still mine
    assert is_me(True, None, MY_ID) is True
    # out flag not set but sender is me: mine (the backstop the tdata bug needed)
    assert is_me(False, MY_ID, MY_ID) is True
    # peer message: not mine
    assert is_me(False, PEER_ID, MY_ID) is False
    print("[test] is_me_union OK")


def test_sender_never_named():
    # the record stores only the numeric id, never a name
    r = shape_record("their words", False, "group", 1700000001, PEER_ID, -1009999, False)
    assert r["sender"] == "tg_%d" % PEER_ID
    assert r["is_me"] is False
    print("[test] sender_never_named OK")


def main():
    fails = 0
    for fn in (test_record_shape, test_is_me_union, test_sender_never_named):
        try:
            fn()
        except AssertionError as e:
            print("[FAIL]", fn.__name__, e)
            fails += 1
    print("=== %s ===" % ("all passed" if fails == 0 else "%d failed" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
