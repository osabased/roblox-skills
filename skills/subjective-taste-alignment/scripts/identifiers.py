"""Shared identifier validation used by every subsystem seam."""

from __future__ import annotations


def require_identifier(value: str, field_name: str) -> None:
    """Reject missing, non-string, or blank stable identifiers."""
    if not isinstance(value, str) or not value or value.isspace():
        raise ValueError(f"{field_name} must be a non-empty stable identifier")


__all__ = ["require_identifier"]
