"""Behavioral tests for the single-live-case lifecycle.

Run with `python -m pytest -q`, or without pytest via `python tests/test_case_lifecycle.py`.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fake_genlayer import ENV, UserError, new_contract  # noqa: E402

URL = "https://www.federalregister.gov/documents/2024/01/02/2023-00001/example"
SPONSOR, ALICE, BOB = "0xsponsor", "0xalice", "0xbob"
BID = "b1"


def call(sender, fn, *args, value=0):
    ENV.sender = sender
    ENV.value = value
    try:
        return fn(*args)
    finally:
        ENV.value = 0


def expect_error(fn, *args, sender=SPONSOR, contains=""):
    try:
        call(sender, fn, *args)
    except UserError as exc:
        assert contains in str(exc), str(exc)
        return
    raise AssertionError(f"expected UserError containing {contains!r}")


def funded(amount=1000):
    c = new_contract()
    call(SPONSOR, c.create_bounty, BID, "t", URL, "REQ-1", "definition")
    call(SPONSOR, c.fund_bounty, BID, value=amount)
    return c


def bounty(c):
    return json.loads(c.get_bounty(BID))


def case(c, case_id):
    return json.loads(c.get_case(case_id))


def assert_synced(c, case_id):
    """While a case is live, bounty status mirrors case status."""
    b, k = bounty(c), case(c, case_id)
    assert b["case_id"] == case_id
    if k["status"] in ("CASE_OPEN", "RETRYABLE"):
        assert b["status"] == k["status"]
        assert b["locked"] != "0"
    else:
        assert b["status"] == "SETTLED"
        assert b["locked"] == "0"


def test_second_claimant_blocked_while_case_open():
    c = funded()
    cid = call(ALICE, c.submit_claim, BID, "claim")
    assert_synced(c, cid)
    expect_error(c.submit_claim, BID, "claim", sender=BOB, contains="not active")


def test_second_claimant_blocked_after_retryable_result():
    c = funded()
    cid = call(ALICE, c.submit_claim, BID, "claim")
    ENV.model_output = "maybe?"
    assert call(SPONSOR, c.adjudicate_case, cid) == "RETRYABLE"
    assert_synced(c, cid)
    assert bounty(c)["status"] == "RETRYABLE"
    assert bounty(c)["locked"] == "1000"
    expect_error(c.submit_claim, BID, "other", sender=BOB, contains="not active")
    expect_error(c.submit_claim, BID, "again", sender=ALICE, contains="not active")


def test_retry_cycle_keeps_statuses_synced_and_claimants_locked_out():
    c = funded()
    cid = call(ALICE, c.submit_claim, BID, "claim")
    ENV.page = ""  # unusable source -> RETRYABLE
    assert call(BOB, c.adjudicate_case, cid) == "RETRYABLE"
    expect_error(c.retry_case, cid, sender=BOB, contains="Only claimant or sponsor")
    call(ALICE, c.retry_case, cid)
    assert_synced(c, cid)
    assert bounty(c)["status"] == "CASE_OPEN"
    expect_error(c.submit_claim, BID, "other", sender=BOB, contains="not active")
    ENV.page = "Official page text"
    assert call(BOB, c.adjudicate_case, cid) == "SUPPORTS_REQUIREMENT"
    assert_synced(c, cid)


def test_retryable_case_can_be_adjudicated_directly_by_anyone():
    c = funded()
    cid = call(ALICE, c.submit_claim, BID, "claim")
    ENV.model_output = "unclear"
    call(SPONSOR, c.adjudicate_case, cid)
    ENV.model_output = "DOES_NOT_SUPPORT"
    assert call(BOB, c.adjudicate_case, cid) == "DOES_NOT_SUPPORT"
    assert_synced(c, cid)


def test_settled_bounty_accepts_no_new_case_and_no_repeat_settlement():
    c = funded()
    cid = call(ALICE, c.submit_claim, BID, "claim")
    call(BOB, c.adjudicate_case, cid)
    expect_error(c.submit_claim, BID, "late", sender=BOB, contains="not active")
    expect_error(c.adjudicate_case, cid, sender=BOB, contains="not awaiting")
    expect_error(c.retry_case, cid, sender=ALICE, contains="Only retryable")


def test_settlement_and_withdrawal_accounting():
    c = funded(1000)
    cid = call(ALICE, c.submit_claim, BID, "claim")
    call(BOB, c.adjudicate_case, cid)  # SUPPORTS_REQUIREMENT by default
    assert c.get_credit(BID, ALICE) == "1000"
    assert c.get_credit(BID, SPONSOR) == "0"
    call(ALICE, c.withdraw_credit, BID)
    assert ENV.transfers == [(ALICE, 1000)]
    acct = json.loads(c.get_accounting(BID))
    assert acct["invariant_received_equals_locked_plus_credited"]
    assert acct["invariant_withdrawn_not_above_credited"]
    expect_error(c.withdraw_credit, BID, sender=ALICE, contains="No withdrawable")


def test_not_supported_refunds_sponsor():
    c = funded(500)
    cid = call(ALICE, c.submit_claim, BID, "claim")
    ENV.model_output = "DOES_NOT_SUPPORT"
    call(BOB, c.adjudicate_case, cid)
    assert c.get_credit(BID, SPONSOR) == "500"
    assert c.get_credit(BID, ALICE) == "0"


def test_desynced_state_is_rejected_not_repaired():
    # The pre-fix flow left a RETRYABLE case under an ACTIVE bounty. If state
    # like that ever exists, no write may act on it.
    c = funded()
    cid = call(ALICE, c.submit_claim, BID, "claim")
    ENV.model_output = "unclear"
    call(SPONSOR, c.adjudicate_case, cid)
    c.bounty_status[BID] = "ACTIVE"
    expect_error(c.adjudicate_case, cid, sender=BOB, contains="out of sync")
    expect_error(c.retry_case, cid, sender=ALICE, contains="out of sync")


def test_case_not_attached_to_bounty_is_rejected():
    c = funded()
    cid = call(ALICE, c.submit_claim, BID, "claim")
    # Forge a second CASE_OPEN case for the same bounty (cannot happen via the
    # public API). It is not the bounty's attached case, so it cannot settle.
    rogue = BID + ":" + BOB
    c.case_bounty_id[rogue] = BID
    c.case_claimant[rogue] = BOB
    c.case_claim_text[rogue] = "rogue"
    c.case_status[rogue] = "CASE_OPEN"
    c.case_verdict[rogue] = "UNRESOLVED"
    expect_error(c.adjudicate_case, rogue, sender=BOB, contains="not the live case")
    assert call(ALICE, c.adjudicate_case, cid) == "SUPPORTS_REQUIREMENT"


def test_bounty_exposes_its_single_case_id():
    c = funded()
    assert bounty(c)["case_id"] == ""
    cid = call(ALICE, c.submit_claim, BID, "claim")
    assert bounty(c)["case_id"] == cid


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print("FAIL", name, "-", repr(exc))
    raise SystemExit(1 if failures else 0)
