"""Unit tests for the shared mechanics in scripts/_common.py."""
from datetime import date, timedelta
from urllib.parse import urlparse

import pytest


# --- YAML loading / duplicate keys -----------------------------------------

def test_duplicate_key_rejected(common):
    with pytest.raises(ValueError, match="duplicate key"):
        common.load_yaml("a: 1\na: 2\n")


def test_resolved_alias_keys_collide(common):
    # `yes` and `true` both resolve to boolean True; the raw-string comparison
    # in the old fallback parser missed this collision.
    with pytest.raises(ValueError, match="duplicate key"):
        common.load_yaml("yes: 1\ntrue: 2\n")


def test_block_scalars_parse(common):
    loaded = common.load_yaml("notes: |\n  line one\n  line two\n")
    assert loaded == {"notes": "line one\nline two\n"}


def test_normalize_empty_values_scalars_and_lists(common):
    data = {"a": None, "nested": {"b": None, "keep": "x"}, "items": None}
    common.normalize_empty_values(data, {"items", "nested.b"})
    assert data == {"a": "", "nested": {"b": [], "keep": "x"}, "items": []}


# --- URL host validation -----------------------------------------------------

@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://devforum.roblox.com/t/x/1", "devforum.roblox.com"),
        ("https://devforum.roblox.com./t/x/1", "devforum.roblox.com"),  # trailing dot
        ("https://EXAMPLE.test/page", "example.test"),
        ("https://[::1]/x", "::1"),
        ("https://münchen.example/x", "xn--mnchen-3ya.example"),
    ],
)
def test_validated_url_host_accepts(common, url, expected):
    assert common.validated_url_host(urlparse(url)) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://exa%6Dple.test/x",  # percent-encoded host
        "https://-bad.example/x",  # leading hyphen label
        "https://host:99999/x",  # out-of-range port
        "https://" + "a" * 300 + ".test/",  # host too long
    ],
)
def test_validated_url_host_rejects(common, url):
    assert common.validated_url_host(urlparse(url)) is None


def test_https_url_policy(common):
    assert common.validate_https_url("http://example.test/x", field="f") == [
        "f must be an absolute https:// URL"
    ]
    assert "f must not contain embedded credentials" in common.validate_https_url(
        "https://user:pw@example.test/x", field="f"
    )
    assert any(
        "credential-like query parameter" in e
        for e in common.validate_https_url("https://example.test/x?api_key=1", field="f")
    )
    # Sensitive keys hide in fragments too.
    assert any(
        "credential-like fragment parameter" in e
        for e in common.validate_https_url("https://example.test/x#token=abc", field="f")
    )
    assert common.validate_https_url(
        "https://example.test/x", field="f", expected_host="devforum.roblox.com"
    ) == ["f must use host devforum.roblox.com"]
    assert common.validate_https_url("https://example.test/page#section", field="f") == []


# --- Date validation ---------------------------------------------------------

def test_validate_date_happy_path(common):
    assert common.validate_date("2026-01-02", field="observed") == []


def test_validate_date_placeholder(common):
    assert common.validate_date("YYYY-MM-DD", field="observed") == [
        "observed still contains the template placeholder YYYY-MM-DD"
    ]


def test_validate_date_future(common):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert common.validate_date(tomorrow, field="observed") == [
        "observed cannot be in the future"
    ]


def test_validate_date_compact_form_rejected_on_all_pythons(common):
    # date.fromisoformat accepts "20260102" on Python 3.11+ but not on 3.8-3.10.
    # The strict-form guard keeps the verdict identical across versions.
    assert common.validate_date("20260102", field="observed") == [
        "observed must be a real ISO date in YYYY-MM-DD form"
    ]


def test_validate_date_custom_messages(common):
    assert common.validate_date(
        "nope", field="last_reviewed", format_msg="last_reviewed must be YYYY-MM-DD or empty"
    ) == ["last_reviewed must be YYYY-MM-DD or empty"]


# --- Version evidence ----------------------------------------------------------

@pytest.mark.parametrize(
    "value",
    [
        "v1.2.3",
        "4.0.0",
        "a3f9c21bd44",  # abbreviated commit hash
        "source state 2024-06-01",  # dated source state
        "tag rc-4-final",
    ],
)
def test_immutable_version_evidence_accepts(common, value):
    assert common.has_immutable_version_evidence(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "latest",
        "main",
        "tag latest",  # explicit ref to a volatile name
        "2099-13-45",  # date-shaped but invalid; masked before the ID check
        "banana-state",  # bare prose, no explicit ref kind
    ],
)
def test_immutable_version_evidence_rejects(common, value):
    assert common.has_immutable_version_evidence(value) is False


# --- File collection -----------------------------------------------------------

def test_collect_files(common, tmp_path):
    (tmp_path / "a.yaml").write_text("x: 1\n", encoding="utf-8")
    (tmp_path / "b.yml").write_text("x: 1\n", encoding="utf-8")
    (tmp_path / ".hidden.yaml").write_text("x: 1\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")
    files = common.collect_files(tmp_path)
    assert [p.name for p in files] == ["a.yaml", "b.yml"]
    with pytest.raises(ValueError, match="expected .yaml or .yml"):
        common.collect_files(tmp_path / "notes.txt")
    with pytest.raises(ValueError, match="does not exist"):
        common.collect_files(tmp_path / "missing")
