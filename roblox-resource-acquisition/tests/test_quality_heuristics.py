"""Regression tests for small validator heuristics fixed during maintenance."""
import fixtures


def test_pass_condition_recognizes_past_tense_sent(skill_mod):
    # OBSERVABLE_VERB_RE previously spelled the alternation as send(?:s|sent)?,
    # which matched "send"/"sends" but never the past tense "sent". Here
    # "sent" is the only observable verb, so the fix is what makes this pass.
    assert skill_mod.is_concrete_pass_condition("Payload sent to the client table") is True


def test_pass_condition_still_rejects_generic_claims(skill_mod):
    assert skill_mod.is_concrete_pass_condition("it works") is False
    assert skill_mod.is_concrete_pass_condition("verify successful operation") is False


def test_verified_acquisition_missing_canonical_url_reported_once(record_mod, tmp_path):
    # An empty canonical_url used to be reported twice for verified-acquisition
    # records (required_nonempty loop plus a redundant trailing check).
    text = fixtures.INVALID_RECORD.replace(
        'canonical_url: "https://github.com/evaera/roblox-lua-promise"',
        'canonical_url: ""',
    )
    path = tmp_path / "record.yaml"
    path.write_text(text)
    errors, _notes = record_mod.validate_record(path, record_mod.load_record(path))
    canonical_errors = [e for e in errors if "canonical" in e]
    assert canonical_errors == ["verified-acquisition requires canonical_url"]
