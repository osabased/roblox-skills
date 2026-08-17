"""Regression tests for small validator heuristics fixed during maintenance."""
from pathlib import Path

import fixtures


def test_pass_condition_recognizes_past_tense_sent(skill_mod):
    # OBSERVABLE_VERB_RE previously spelled the alternation as send(?:s|sent)?,
    # which matched "send"/"sends" but never the past tense "sent". Here
    # "sent" is the only observable verb, so the fix is what makes this pass.
    assert skill_mod.is_concrete_pass_condition("Payload sent to the client table") is True


def test_pass_condition_still_rejects_generic_claims(skill_mod):
    assert skill_mod.is_concrete_pass_condition("it works") is False
    assert skill_mod.is_concrete_pass_condition("verify successful operation") is False


def test_verified_acquisition_missing_canonical_url_reported_once(record_mod):
    # An empty canonical_url used to be reported twice for verified-acquisition
    # records (required_nonempty loop plus a redundant trailing check).
    record = fixtures.invalid_record()
    record["canonical_url"] = ""
    errors, _notes = record_mod.validate_record(Path("record.yaml"), record)
    canonical_errors = [e for e in errors if "canonical" in e]
    assert canonical_errors == ["verified-acquisition requires canonical_url"]
