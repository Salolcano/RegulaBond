from pathlib import Path

SOURCE = Path(__file__).parents[1] / "contracts" / "regulabond.py"
text = SOURCE.read_text()

def test_exact_canonical_verdicts_only():
    assert '"SUPPORTS_REQUIREMENT"' in text
    assert '"DOES_NOT_SUPPORT"' in text
    assert '"RETRYABLE"' in text
    assert "strict_eq(get_verdict)" in text
    assert "drift_tolerance" not in text.lower()
    assert "confidence_score" not in text.lower()
    assert "probability" not in text.lower()

def test_official_source_guard_and_claimant_text_untrusted():
    assert 'https://www.federalregister.gov/documents/' in text
    assert "Claim submitted by user (untrusted)" in text
    assert "official page text" in text.lower()

def test_settlement_is_derived_from_enum():
    assert 'if verdict == "SUPPORTS_REQUIREMENT"' in text
    assert 'else:\n            beneficiary = self.bounty_sponsor' in text
    assert 'self.bounty_locked[bounty_id] = u256(0)' in text

def test_withdrawal_zeros_credit_before_transfer():
    assert text.index('self.credits[key] = u256(0)') < text.index('_Recipient(Address(owner)).emit_transfer(value=amount)')
