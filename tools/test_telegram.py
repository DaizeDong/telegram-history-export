#!/usr/bin/env python3
"""Unit tests for the export record shaping and the is-me rule, on synthetic data with no real values.

telegram_export.py keeps its telethon calls behind pure functions so the important logic can be tested
without a live account. shape_record builds one output record; the is-me rule is the union of msg.out
and sender-id equals my-id; display_name, clean_username and entity_identity turn whatever Telegram
gave us about a peer into the readable fields, including the cases where it gave us nothing.

Every value here is synthetic. No real account id, handle or name appears in this file.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from telegram_export import (clean_username, display_name, entity_identity,
                             shape_record)


MY_ID = 5000001            # synthetic owner id
PEER_ID = 5000002          # synthetic peer id


class Stub(object):
    """Stand in for a telethon entity: attributes only, missing ones simply absent."""

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


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


def test_stable_fields_unchanged_by_the_new_ones():
    # the seven original fields must read identically whether or not identity is supplied
    base = shape_record("hi", False, "group", 1700000002, PEER_ID, -1002222, True)
    named = shape_record("hi", False, "group", 1700000002, PEER_ID, -1002222, True,
                         sender_name="AcmeUser", sender_username="acme_user",
                         conv_title="Acme Test Group")
    for k in ("text", "is_me", "ctx", "ts", "sender", "conv", "is_forward"):
        assert base[k] == named[k], k
    print("[test] stable_fields_unchanged_by_the_new_ones OK")


def test_identity_fields_carried():
    r = shape_record("their words", False, "group", 1700000003, PEER_ID, -1003333, False,
                     sender_name="AcmeUser", sender_username="@acme_user",
                     conv_title="Acme Test Group")
    assert r["sender_name"] == "AcmeUser"
    assert r["sender_username"] == "acme_user"      # the leading @ is stripped
    assert r["conv_title"] == "Acme Test Group"
    print("[test] identity_fields_carried OK")


def test_identity_fields_absent_are_null_not_missing():
    # a downstream reader must be able to ask for the key and get None, not a KeyError
    r = shape_record("no idea who", False, "dm", 1700000004, PEER_ID, -1004444, False)
    for k in ("sender_name", "sender_username", "conv_title"):
        assert k in r, k
        assert r[k] is None, k
    # empty strings from Telegram normalise to None, never to ""
    blank = shape_record("blank", False, "dm", 1700000005, PEER_ID, -1004444, False,
                         sender_name="  ", sender_username="@", conv_title="")
    assert blank["sender_name"] is None
    assert blank["sender_username"] is None
    assert blank["conv_title"] is None
    print("[test] identity_fields_absent_are_null_not_missing OK")


def test_display_name_assembly():
    assert display_name("Acme", "User") == "Acme User"
    assert display_name("Acme", None) == "Acme"          # last name is optional
    assert display_name(None, "User") == "User"          # so is the first
    assert display_name(None, None) is None              # a deleted account has neither
    assert display_name("Acme", "User", "Acme Test Group") == "Acme Test Group"
    print("[test] display_name_assembly OK")


def test_clean_username():
    assert clean_username("@acme_user") == "acme_user"
    assert clean_username("acme_user") == "acme_user"
    assert clean_username(None) is None
    assert clean_username("") is None
    print("[test] clean_username OK")


def test_entity_identity_cases():
    # a user with both names and a handle
    assert entity_identity(Stub(first_name="Acme", last_name="User",
                                username="acme_user")) == ("Acme User", "acme_user")
    # a user with no handle at all: name only
    assert entity_identity(Stub(first_name="Acme", last_name=None)) == ("Acme", None)
    # a channel or group: a title and no personal name
    assert entity_identity(Stub(title="Acme Test Group")) == ("Acme Test Group", None)
    # a channel with a title and nothing else, plus the newer usernames list
    assert entity_identity(Stub(title="Acme Test Group",
                                usernames=[Stub(username="acmegroup")])) == ("Acme Test Group",
                                                                             "acmegroup")
    # a deleted account: telethon hands back an entity with nothing readable
    assert entity_identity(Stub(first_name=None, last_name=None, username=None)) == (None, None)
    # no entity at all, for an anonymous post
    assert entity_identity(None) == (None, None)
    print("[test] entity_identity_cases OK")


def test_is_me_union():
    # out flag set, sender unknown: still mine
    assert is_me(True, None, MY_ID) is True
    # out flag not set but sender is me: mine (the backstop the tdata bug needed)
    assert is_me(False, MY_ID, MY_ID) is True
    # peer message: not mine
    assert is_me(False, PEER_ID, MY_ID) is False
    print("[test] is_me_union OK")


def test_sender_id_field_is_still_the_numeric_id():
    # the readable name goes in sender_name; "sender" stays the numeric id downstream keys on
    r = shape_record("their words", False, "group", 1700000001, PEER_ID, -1009999, False,
                     sender_name="AcmeUser")
    assert r["sender"] == "tg_%d" % PEER_ID
    assert r["sender_name"] == "AcmeUser"
    assert r["is_me"] is False
    print("[test] sender_id_field_is_still_the_numeric_id OK")


def main():
    fails = 0
    for fn in (test_record_shape, test_stable_fields_unchanged_by_the_new_ones,
               test_identity_fields_carried, test_identity_fields_absent_are_null_not_missing,
               test_display_name_assembly, test_clean_username, test_entity_identity_cases,
               test_is_me_union, test_sender_id_field_is_still_the_numeric_id):
        try:
            fn()
        except AssertionError as e:
            print("[FAIL]", fn.__name__, e)
            fails += 1
    print("=== %s ===" % ("all passed" if fails == 0 else "%d failed" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
