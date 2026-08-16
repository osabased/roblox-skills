#!/usr/bin/env python3
"""Shared mechanics for the roblox-resource-acquisition validator scripts.

This module centralizes the parsing and syntax-checking machinery that was
previously duplicated across the four validators: YAML loading with
duplicate-key rejection, URL/host validation, date validation, version-evidence
detection, and file collection. Policy decisions and error wording stay in the
individual scripts.

PyYAML is a hard requirement. A single parser everywhere guarantees that the
same registry entry, learning, or record receives the same trust verdict in
every environment; the previous optional-PyYAML fallback parser could disagree
with PyYAML on inputs such as empty scalars, octal-like integers, and duplicate
keys, letting a file pass validation in one environment and fail in another.
"""
from __future__ import annotations

import ipaddress
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

try:
    import yaml
except ImportError:  # pragma: no cover - exercised via subprocess in tests
    print(
        "ERROR: PyYAML is required to run this validator. "
        "Install it with: pip install -r requirements.txt (or: pip install pyyaml)",
        file=sys.stderr,
    )
    sys.exit(2)


class UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys instead of silently
    keeping the last one. Keys are compared after resolution, so aliases of
    the same value (e.g. ``yes`` and ``true``) collide as duplicates."""


def _construct_unique_mapping(loader: Any, node: Any, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_yaml(text: str) -> Any:
    """Parse YAML with duplicate-key rejection; raise ValueError on failure."""
    try:
        return yaml.load(text, Loader=UniqueKeyLoader)
    except Exception as exc:
        raise ValueError(f"invalid YAML: {exc}") from exc


def normalize_empty_values(
    mapping: dict[Any, Any],
    list_fields: frozenset[str] | set[str] = frozenset(),
    _prefix: str = "",
) -> dict[Any, Any]:
    """Rewrite None values in a mapping (and nested mappings) to their empty form.

    YAML parses a bare ``key:`` as None while the shipped templates spell the
    same intent as ``key: ""`` or ``key: []``. Both spellings must validate
    identically, so empty values are normalized before schema checks: fields
    named in ``list_fields`` (dotted paths for nested fields) become ``[]``,
    everything else becomes ``""``. Required-field checks still reject empty
    strings and empty lists, so nothing malformed or absent gains trust
    through this normalization.
    """
    for key, value in mapping.items():
        dotted = f"{_prefix}{key}"
        if value is None:
            mapping[key] = [] if dotted in list_fields else ""
        elif isinstance(value, dict):
            normalize_empty_values(value, list_fields, _prefix=f"{dotted}.")
    return mapping


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

DEVFORUM_TOPIC_PATH_RE = re.compile(r"/t/(?:[^/]+/)?\d+(?:/\d+)?/?")

SENSITIVE_QUERY_RE = re.compile(
    r"(?:"
    r"(?:^|[_-])(?:access[_-]?key|api[_-]?key|auth(?:orization)?|credential|password|passwd|secret|signature|sig|token)(?:$|[_-])"
    r"|(?:api|access|auth|client|private|refresh|session|bearer)[_-]?(?:token|key|secret|credential)(?:$|[_-])"
    r"|secret[_-]?key(?:$|[_-])"
    r")",
    re.I,
)

VOLATILE_VERSION_TOKEN_RE = re.compile(
    r"\b(?:latest|current|stable|head|main|master|trunk|nightly|rolling|dev|development)\b",
    re.I,
)

IMMUTABLE_VERSION_ID_RE = re.compile(
    r"(?:"
    r"\bv\d+(?:(?:[._-]\d+)+(?:[-+][0-9A-Za-z.-]+)?)?\b"
    r"|\b\d+(?:[._-]\d+)+(?:[-+][0-9A-Za-z.-]+)?\b"
    r"|\b[0-9a-f]{7,64}\b"
    r")",
    re.I,
)

EXPLICIT_IMMUTABLE_REF_RE = re.compile(
    r"\b(?:tag|release|version|commit|revision|rev|build|asset version)\b"
    r"\s*(?:[:=#@]|is\b)?\s*([A-Za-z0-9][A-Za-z0-9._/-]{0,127})\b",
    re.I,
)

SOURCE_STATE_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def validated_url_host(parsed: Any) -> str | None:
    """Return a normalized hostname when URL authority syntax is valid."""
    try:
        host = parsed.hostname
        # Accessing .port validates its numeric/range syntax.
        _ = parsed.port
    except ValueError:
        return None
    if not host or re.search(r"[\s\x00-\x1f\x7f]", host) or "%" in host:
        return None
    host = host.rstrip(".")
    if not host:
        return None
    if ":" in host:
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return None
        return host.lower()
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    if len(ascii_host) > 253:
        return None
    labels = ascii_host.split(".")
    if any(
        not label
        or len(label) > 63
        or label.startswith("-")
        or label.endswith("-")
        or not re.fullmatch(r"[A-Za-z0-9-]+", label)
        for label in labels
    ):
        return None
    return ascii_host.lower()


def validate_https_url(value: str, *, field: str, expected_host: str | None = None) -> list[str]:
    errors: list[str] = []
    try:
        parsed = urlparse(value)
    except Exception:
        return [f"{field} is not a valid URL"]
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        errors.append(f"{field} must be an absolute https:// URL")
    host = validated_url_host(parsed)
    if parsed.netloc and host is None:
        errors.append(f"{field} has an invalid URL host or port")
    if parsed.username or parsed.password:
        errors.append(f"{field} must not contain embedded credentials")
    if expected_host and host and host != expected_host:
        errors.append(f"{field} must use host {expected_host}")
    for component_name, component in (("query", parsed.query), ("fragment", parsed.fragment)):
        for key, _ in parse_qsl(component, keep_blank_values=True):
            if SENSITIVE_QUERY_RE.search(key):
                errors.append(
                    f"{field} must not contain credential-like {component_name} parameter {key!r}"
                )
    return errors


def validate_date(
    value: str,
    *,
    field: str,
    placeholder_msg: str | None = None,
    format_msg: str | None = None,
    future_msg: str | None = None,
) -> list[str]:
    """Validate a YYYY-MM-DD date string; message wording is script policy."""
    if value == "YYYY-MM-DD":
        return [placeholder_msg or f"{field} still contains the template placeholder YYYY-MM-DD"]
    # date.fromisoformat accepts compact ("20260102") and timestamp forms on
    # Python 3.11+, but not on 3.8-3.10. Require the exact dashed form so the
    # verdict does not depend on the interpreter version.
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return [format_msg or f"{field} must be a real ISO date in YYYY-MM-DD form"]
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return [format_msg or f"{field} must be a real ISO date in YYYY-MM-DD form"]
    if parsed > date.today():
        return [future_msg or f"{field} cannot be in the future"]
    return []


def has_immutable_version_evidence(value: str) -> bool:
    """Accept an immutable-looking ID, named reference, or valid dated source state."""
    for raw_date in SOURCE_STATE_DATE_RE.findall(value):
        try:
            source_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if source_date <= date.today():
            return True

    # Date-shaped tokens can resemble numeric release IDs. Mask them before
    # checking version identifiers so malformed/future dates cannot satisfy a
    # release-number branch by accident.
    without_dates = SOURCE_STATE_DATE_RE.sub(" ", value)
    if IMMUTABLE_VERSION_ID_RE.search(without_dates):
        return True

    explicit = EXPLICIT_IMMUTABLE_REF_RE.search(without_dates)
    if not explicit:
        return False
    identifier = explicit.group(1).strip().lower()
    return identifier not in {
        "latest", "current", "stable", "head", "main", "master", "trunk",
        "nightly", "rolling", "dev", "development", "unknown", "tbd", "none",
        "not", "unavailable", "unspecified", "n/a", "na", "not-available",
        "not_available", "not-applicable", "not_applicable",
    }


def collect_files(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() not in {".yaml", ".yml"}:
            raise ValueError(f"{path}: expected .yaml or .yml file")
        return [path]
    if path.is_dir():
        return sorted(
            p for p in path.iterdir()
            if p.is_file() and p.suffix.lower() in {".yaml", ".yml"} and not p.name.startswith(".")
        )
    raise ValueError(f"{path}: path does not exist")
