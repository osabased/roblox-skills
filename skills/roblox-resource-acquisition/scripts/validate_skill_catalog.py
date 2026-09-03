#!/usr/bin/env python3
"""Validate generated Roblox resource skills and their host routing competitors.

Generated children receive full structural validation. Explicit non-generated
routing competitors contribute activation metadata and fingerprint state only.
Static overlap detection identifies routing risk; it does not prove host selection.
PyYAML is required through validate_skill.py (see requirements.txt).
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_skill import (
    extract_labeled_value,
    parse_frontmatter,
    parse_sections,
    validate_skill,
)


CODEX_METADATA_BUDGET = 8_000
CODEX_RISK_THRESHOLD = 7_200
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for",
    "from", "in", "is", "it", "not", "of", "on", "or", "resource", "roblox",
    "skill", "that", "the", "this", "to", "use", "uses", "using", "when", "with",
}


@dataclass(frozen=True)
class CatalogSkill:
    path: Path
    name: str
    description: str
    use_when: str
    do_not_use_when: str
    source_state: str
    kind: str = "generated"

    @property
    def positive_tokens(self) -> set[str]:
        return tokenize(f"{self.description} {self.use_when}")

    @property
    def boundary_tokens(self) -> set[str]:
        return tokenize(f"{self.use_when} {self.do_not_use_when}")


def normalize_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9-]*", value.lower())
        if len(token) >= 3 and token not in STOPWORDS
    }


def collect_skill_directories(paths: list[Path]) -> list[Path]:
    found: dict[str, Path] = {}
    for supplied in paths:
        path = supplied.resolve()
        if path.is_file() and path.name == "SKILL.md":
            roots = [path.parent]
        elif path.is_dir() and (path / "SKILL.md").is_file():
            roots = [path]
        elif path.is_dir():
            roots = [item.parent for item in path.rglob("SKILL.md")]
        else:
            roots = []
        for root in roots:
            found[str(root).lower()] = root
    return sorted(found.values(), key=lambda item: str(item).lower())


def load_catalog_skill(root: Path, *, kind: str = "generated") -> CatalogSkill:
    text = (root / "SKILL.md").read_text(encoding="utf-8-sig")
    metadata, body = parse_frontmatter(text)
    sections, _ = parse_sections(body)
    provenance = sections.get("Provenance", "")
    name_value = metadata.get("name")
    description_value = metadata.get("description")
    return CatalogSkill(
        path=root,
        name=name_value.strip() if isinstance(name_value, str) else "",
        description=description_value.strip() if isinstance(description_value, str) else "",
        use_when=sections.get("Use when", "").strip(),
        do_not_use_when=sections.get("Do not use when", "").strip(),
        source_state=(extract_labeled_value(provenance, "Source version/release/commit") or "").strip(),
        kind=kind,
    )


def validate_routing_competitor(root: Path) -> tuple[list[str], CatalogSkill | None]:
    """Load only activation metadata for a host-visible non-generated skill.

    Routing competitors are deliberately not forced through the generated
    resource-skill contract. They need only enough valid Agent Skills metadata
    to participate in overlap detection and the routing fingerprint.
    """
    errors: list[str] = []
    try:
        skill = load_catalog_skill(root, kind="competitor")
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"{root}: could not load routing competitor metadata: {exc}"], None
    if not skill.name:
        errors.append(f"{root}: routing competitor frontmatter requires non-empty name")
    if not skill.description:
        errors.append(f"{root}: routing competitor frontmatter requires non-empty description")
    if len(skill.name) > 64:
        errors.append(f"{root}: routing competitor name must be at most 64 characters")
    if len(skill.description) > 1024:
        errors.append(f"{root}: routing competitor description must be at most 1024 characters")
    return errors, skill


def catalog_fingerprint(skills: list[CatalogSkill]) -> str:
    rows = []
    for skill in skills:
        rows.append(
            "\0".join(
                (
                    skill.name,
                    normalize_text(skill.description),
                    normalize_text(skill.use_when),
                    normalize_text(skill.do_not_use_when),
                    skill.source_state,
                )
            )
        )
    payload = "\n".join(sorted(rows)).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def overlap_score(left: CatalogSkill, right: CatalogSkill) -> tuple[float, float, set[str]]:
    left_tokens = left.positive_tokens
    right_tokens = right.positive_tokens
    shared = left_tokens & right_tokens
    union = left_tokens | right_tokens
    jaccard = len(shared) / len(union) if union else 0.0
    smaller = min(len(left_tokens), len(right_tokens))
    containment = len(shared) / smaller if smaller else 0.0
    return jaccard, containment, shared


def validate_catalog(
    roots: list[Path], *, host: str, competitor_roots: list[Path] | None = None
) -> tuple[list[str], list[str], list[str], str]:
    errors: list[str] = []
    warnings: list[str] = []
    overlaps: list[str] = []
    skills: list[CatalogSkill] = []
    competitor_roots = competitor_roots or []

    if not roots:
        return ["no generated skills found in supplied paths"], warnings, overlaps, catalog_fingerprint([])

    for root in roots:
        child_errors, child_warnings = validate_skill(root)
        errors.extend(f"{root}: {message}" for message in child_errors)
        warnings.extend(f"{root}: {message}" for message in child_warnings)
        try:
            skills.append(load_catalog_skill(root, kind="generated"))
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{root}: could not load catalog metadata: {exc}")

    generated_paths = {root.resolve() for root in roots}
    for root in competitor_roots:
        if root.resolve() in generated_paths:
            continue
        competitor_errors, competitor = validate_routing_competitor(root)
        errors.extend(competitor_errors)
        if competitor is not None:
            skills.append(competitor)

    by_name: dict[str, list[CatalogSkill]] = {}
    by_description: dict[str, list[CatalogSkill]] = {}
    for skill in skills:
        by_name.setdefault(skill.name.lower(), []).append(skill)
        by_description.setdefault(normalize_text(skill.description), []).append(skill)
    for name, matches in by_name.items():
        if name and len(matches) > 1 and any(item.kind == "generated" for item in matches):
            errors.append(
                f"duplicate skill name {name!r}: " + ", ".join(str(item.path) for item in matches)
            )
    for description, matches in by_description.items():
        if description and len(matches) > 1 and any(item.kind == "generated" for item in matches):
            errors.append(
                "duplicate normalized description: " + ", ".join(str(item.path) for item in matches)
            )

    for index, left in enumerate(skills):
        for right in skills[index + 1 :]:
            if left.kind != "generated" and right.kind != "generated":
                continue
            jaccard, containment, shared = overlap_score(left, right)
            shared_boundaries = left.boundary_tokens & right.boundary_tokens
            if len(shared) >= 4 and (jaccard >= 0.50 or containment >= 0.75):
                overlaps.append(
                    f"{left.name} <-> {right.name}: jaccard={jaccard:.2f}, "
                    f"containment={containment:.2f}, shared={','.join(sorted(shared))}, "
                    f"boundary_shared={','.join(sorted(shared_boundaries)) or '-'}"
                )

    if host == "codex":
        metadata_chars = sum(
            len(skill.name) + len(skill.description) + len(str(skill.path)) + 3 for skill in skills
        )
        if metadata_chars >= CODEX_RISK_THRESHOLD:
            warnings.append(
                f"Codex initial skill metadata is {metadata_chars} characters; this approaches/exceeds "
                f"the {CODEX_METADATA_BUDGET}-character fallback budget and may cause shortening or omission"
            )

    return errors, warnings, overlaps, catalog_fingerprint(skills)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate generated-skill catalog structure and report routing-overlap risk."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="generated skill directories or roots")
    parser.add_argument(
        "--routing-competitor",
        action="append",
        type=Path,
        default=[],
        help="host-visible non-generated skill/root to include in routing overlap checks and fingerprint",
    )
    parser.add_argument("--host", choices=("portable", "codex"), default="codex")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    roots = collect_skill_directories(args.paths)
    competitor_roots = collect_skill_directories(args.routing_competitor)
    errors, warnings, overlaps, fingerprint = validate_catalog(
        roots, host=args.host, competitor_roots=competitor_roots
    )
    print(f"CATALOG_FINGERPRINT: {fingerprint}")
    print(f"SKILLS: {len(roots)}")
    generated_paths = {item.resolve() for item in roots}
    routing_competitor_count = sum(
        1 for root in competitor_roots if root.resolve() not in generated_paths
    )
    print(f"ROUTING_COMPETITORS: {routing_competitor_count}")
    for overlap in overlaps:
        print(f"OVERLAP: {overlap}")
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
        return 1
    print("PASS: catalog structural checks passed")
    for warning in warnings:
        print(f"WARN: {warning}")
    if overlaps:
        print("NOTE: overlap clusters require independent catalog-routing tests; static PASS does not prove host selection")
    else:
        print("NOTE: no static overlap cluster found; static PASS does not prove host selection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

