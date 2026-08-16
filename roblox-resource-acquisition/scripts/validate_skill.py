#!/usr/bin/env python3
"""Structural validator for a generated Roblox resource skill.

This intentionally cannot prove runtime correctness or documentation truth. It
checks that a generated skill exposes the minimum operational/provenance contract
before behavioral tests and rejects obvious unfilled template state.

PyYAML is required (see requirements.txt); the script exits with code 2 and an
install hint when it is missing.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (
    DEVFORUM_TOPIC_PATH_RE,
    SENSITIVE_QUERY_RE,
    SLUG_RE,
    VOLATILE_VERSION_TOKEN_RE,
    has_immutable_version_evidence,
    load_yaml,
    validated_url_host,
)

REQUIRED_HEADINGS = [
    "Use when",
    "Do not use when",
    "Alternatives",
    "Provenance",
    "Prerequisites and installation",
    "Mental model",
    "Client/server placement",
    "Common path",
    "Lifecycle and cleanup",
    "API used by this skill",
    "Failure modes",
    "Limitations",
    "Security notes",
    "Verify after installation",
    "Version drift",
]

# Match template artifacts precisely enough to avoid rejecting ordinary prose
# containing words such as "URL" or "identifier".
TEMPLATE_SENTINELS = [
    "roblox-RESOURCE-SLUG",
    "USE-TRIGGER-IN-ONE-SENTENCE",
    "# RESOURCE NAME",
    "Use **RESOURCE NAME** for CAPABILITY.",
    "Compare against the closest Roblox built-in or credible alternative. If none is meaningful, state why.",
    "VERSION/COMMIT/STATE",
    "Validated against **VERSION/COMMIT/STATE**",
    "Guidance targets **VERSION/COMMIT/STATE** (source reviewed **YYYY-MM-DD**). Resource verification: **VERIFIED/UNVERIFIED/UNAVAILABLE**.",
    "Explain the minimum concepts needed to use the resource correctly.",
    "State where modules and calls belong, what crosses the boundary, and what authority the server must retain.",
    "State where modules and calls belong on both client and server, what crosses the boundary, and what authority the server must retain. If one side must not use the resource, say so explicitly.",
    "Provide the shortest verified setup/use sequence.",
    "-- Verified minimal example.",
    "Document only verified public APIs that the agent needs frequently.",
    "Provide the shortest source-grounded setup/use sequence. Do not call it runtime-verified unless the recorded resource verification status is `verified`.",
    "-- Minimal example grounded in the reviewed source/API.",
    "Document only source-grounded public APIs that the agent needs frequently; distinguish source review from runtime verification.",
    "Likely cause -> diagnosis -> repair.",
    "State the applicable resource-specific trust boundaries and mitigations. If none are special to this resource, say so explicitly. Preserve server authority; never embed secrets in source.",
    "Both lines must be concrete enough for another agent to execute/check; do not use placeholders or generic outcomes such as “check it” or “it works.”",
]

TEMPLATE_LINE_PATTERNS = [
    re.compile(r"^\s*[-*]\s*\.\.\.\s*$", re.M),
    re.compile(r"^\s*[-*]\s*[^:\n]+:\s*\.\.\.\s*$", re.M),
    re.compile(r"^\s*\d+[.)]\s*\.\.\.\s*$", re.M),
    re.compile(r"^\s*[-*]\s*DevForum:\s*(?:HTTPS\s+)?URL\s*$", re.M | re.I),
    re.compile(r"^\s*[-*]\s*Canonical source/docs:\s*(?:HTTPS\s+)?URL(?:\s+\(.*\))?\s*$", re.M | re.I),
    re.compile(r"^\s*[-*]\s*Validated version/release/commit:\s*IDENTIFIER(?:\s+\(.*\))?\s*$", re.M | re.I),
    re.compile(r"^\s*[-*]\s*Validation date:\s*YYYY-MM-DD\s*$", re.M | re.I),
    re.compile(r"^\s*[-*]\s*Source version/release/commit:\s*IDENTIFIER(?:\s+\(.*\))?\s*$", re.M | re.I),
    re.compile(r"^\s*[-*]\s*Source review date:\s*YYYY-MM-DD\s*$", re.M | re.I),
    re.compile(r"^\s*[-*]\s*Resource verification:\s*VERIFIED/UNVERIFIED/UNAVAILABLE\s*$", re.M | re.I),
    re.compile(r"^\s*Run:\s*\.\.\.\s*$", re.M | re.I),
    re.compile(r"^\s*Pass condition:\s*\.\.\.\s*$", re.M | re.I),
]

PROVENANCE_FIELD_ALIASES = {
    "DevForum": ("DevForum",),
    "Canonical source/docs": ("Canonical source/docs",),
    "Source version/release/commit": ("Source version/release/commit", "Validated version/release/commit"),
    "Source review date": ("Source review date", "Validation date"),
    "Resource verification": ("Resource verification",),
}

SENSITIVE_URL_QUERY_KEYS = {
    "access_token",
    "api-key",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "password",
    "passwd",
    "secret",
    "sig",
    "signature",
    "token",
    "x-amz-signature",
}

NO_SEPARATE_CANONICAL_RE = re.compile(
    r"^(?:"
    r"no separate canonical(?: source| docs?)?(?: exists)?"
    r"(?:[;,.]\s*devforum thread is (?:the )?canonical(?: source)?)?"
    r"|devforum thread is (?:the )?canonical(?: source)?"
    r")\.?$",
    re.I,
)

NO_DEVFORUM_RE = re.compile(
    r"^(?:"
    r"no devforum (?:topic|thread)(?: exists| is applicable| is used/applicable| is used or applicable| was used| is used| used)?"
    r"|no devforum provenance(?: is)? available"
    r")\.?$",
    re.I,
)

PLACEHOLDER_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:tbd|todo|tbc|fixme|placeholder|fill me in|to be determined|unknown|n/?a|none|not applicable)[:.!]?\s*$",
    re.M | re.I,
)

VAGUE_SECTION_VALUES = {
    "tbd",
    "todo",
    "tbc",
    "fixme",
    "placeholder",
    "fill me in",
    "to be determined",
    "unknown",
    "n/a",
    "na",
    "none",
    "not applicable",
    "see docs",
    "see documentation",
    "see upstream docs",
    "see upstream documentation",
    "refer to docs",
    "refer to documentation",
    "refer to upstream docs",
    "refer to upstream documentation",
    "check docs",
    "check documentation",
    "see readme",
    "refer to readme",
    "same as upstream",
    "use it normally",
    "use normally",
    "use as needed",
    "standard usage",
    "normal usage",
    "follow the docs",
    "follow the documentation",
}

WEAK_VERIFICATION_VALUES = {
    "check it",
    "test it",
    "verify it",
    "run it",
    "inspect it",
    "make sure it works",
}

WEAK_PASS_CONDITION_VALUES = {
    "it works",
    "it works correctly",
    "works",
    "works correctly",
    "works as expected",
    "success",
    "successful",
    "passes",
    "pass",
    "check that it works",
    "verify that it works",
    "confirm that it works",
    "ensure that it works",
    "make sure that it works",
    "verify successful operation",
    "confirm successful operation",
    "successful operation",
    "the module works",
    "the module works correctly",
    "the module works as expected",
    "the resource works",
    "the resource works correctly",
    "the resource works as expected",
    "no error occurs",
    "no errors occur",
    "no exception occurs",
    "no exceptions occur",
}

GENERIC_VERIFICATION_RE = re.compile(
    r"^(?:"
    r"(?:check|test|verify|confirm|ensure|inspect|run)(?:\s+(?:that|whether))?\s+"
    r"(?:it|this|the\s+(?:module|resource|package|library|code))"
    r"(?:\s+(?:works?|runs?|passes?|succeeds?)(?:\s+(?:correctly|properly|normally|as\s+expected))?)?"
    r"|make\s+sure\s+(?:it|this|the\s+(?:module|resource|package|library|code))\s+"
    r"(?:works?|runs?|passes?|succeeds?)(?:\s+(?:correctly|properly|normally|as\s+expected))?"
    r")$",
    re.I,
)

GENERIC_PASS_RE = re.compile(
    r"(?:"
    r"\b(?:it|this|the\s+(?:module|resource|package|library|code))\s+"
    r"(?:works?|runs?|passes?|succeeds?)(?:\s+(?:correctly|properly|normally|as\s+expected))?\b"
    r"|\b(?:check|verify|confirm|ensure|make\s+sure)\b.*\b(?:works?|successful\s+operation)\b"
    r"|\b(?:verify|confirm)\s+successful\s+operation\b"
    r")",
    re.I,
)

OBSERVABLE_VERB_RE = re.compile(
    r"\b(?:print(?:s|ed)?|log(?:s|ged)?|return(?:s|ed)?|exit(?:s|ed)?|"
    r"run(?:s|ning|ran)?|exist(?:s|ed)?|emit(?:s|ted)?|fire(?:s|d)?|trigger(?:s|ed)?|call(?:s|ed)?|"
    r"receive(?:s|d)?|send(?:s)?|sent|create(?:s|d)?|destroy(?:s|ed)?|"
    r"remove(?:s|d)?|appear(?:s|ed)?|show(?:s|ed)?|contain(?:s|ed)?|"
    r"equal(?:s|ed)?|match(?:es|ed)?|change(?:s|d)?|become(?:s)?|"
    r"increment(?:s|ed)?|decrement(?:s|ed)?|connect(?:s|ed)?|disconnect(?:s|ed)?)\b",
    re.I,
)

OBSERVABLE_TARGET_PATTERN = (
    r"output|message|event|callback|status|state|value|property|attribute|"
    r"instance|object|part|model|folder|gui|player|character|table|count|counter|flag|"
    r"list|array|map|dictionary|field|error|exception|client|server|module|script|signal|"
    r"remote|connection|result|response"
)

OBSERVABLE_TARGET_RE = re.compile(rf"\b(?:{OBSERVABLE_TARGET_PATTERN})\b", re.I)

EXPECTED_VALUE_RE = re.compile(
    r"(?:`[^`]+`|['\"][^'\"]+['\"]|\b\d+(?:\.\d+)?\b|==|!=|<=|>=|"
    r"\b(?:true|false|nil)\b)",
    re.I,
)

VERIFICATION_CONTEXT_RE = re.compile(
    r"(?:`[^`]+`|['\"][^'\"]+['\"]|[/\\][A-Za-z0-9_.-]+|"
    r"\b(?:studio|play solo|test|script|module|package|library|place|client|server|"
    r"service|remoteevent|remotefunction|signal|command|terminal|console|file|path)\b)",
    re.I,
)

NO_CALLABLE_API_RE = re.compile(
    r"\b(?:no callable api|does not expose (?:a )?callable api|no public callable api)\b",
    re.I,
)

NO_MEANINGFUL_ALTERNATIVE_RE = re.compile(
    r"\bno (?:meaningful|credible|applicable|practical) alternative(?:s)?\b",
    re.I,
)

# Decision-language signals for prose Alternatives sections. Broader than a
# bare verb list because legitimate comparison prose often carries its
# decision content in comparatives ("the built-in alone is the better fit")
# rather than in one of a few imperative verbs. Kept to genuinely
# decision-shaped phrases so generic filler ("many alternatives exist") still
# fails the shape check.
ALTERNATIVES_DECISION_RE = re.compile(
    r"\b(?:use|uses|prefer(?:red|s)?|choose|chosen|consider|compare[ds]?|instead|"
    r"rather than|better (?:fit|suited|choice)|sufficient|suffices|is enough|"
    r"covers? the same|equivalent|closest)\b",
    re.I,
)

NO_SPECIAL_SECURITY_RE = re.compile(
    r"\b(?:no|without) "
    r"(?:(?:special|additional)(?:\s+(?:resource-specific|resource specific))?|resource-specific|resource specific) "
    r"(?:security|trust|authority|credential|secret(?:-handling| handling)?|network|persistence|supply-chain|supply chain) "
    r"(?:concern|concerns|boundary|boundaries|risk|risks|requirement|requirements)\b",
    re.I,
)

SECURITY_TOPIC_RE = re.compile(
    r"\b(?:client|server|authority|remoteevent|remotefunction|remote|http|https|"
    r"credential|credentials|secret|secrets|api key|oauth|dynamic require|asset|"
    r"auto-update|auto update|supply-chain|supply chain|datastore|persistence|"
    r"destructive|trust boundary|validation|sanitize|sanitise)\b",
    re.I,
)

SECURITY_ACTION_RE = re.compile(
    r"(?:\b(?:validate|saniti[sz]e|preserve|retain|keep|restrict|reject|never|avoid|"
    r"require|required|must|should|inspect|review|pin|disable|store|protect|"
    r"authorize|authenticate|check|revalidate)\b|\bdo\s+not\b|\bdon't\b)",
    re.I,
)

FAILURE_DIAGNOSIS_RE = re.compile(
    r"\b(?:cause|caused|because|due to|wrong|missing|invalid|unavailable|inspect|"
    r"check|verify|diagnos(?:e|is|tic)|repair|fix|move|install|configure|replace|"
    r"ensure|confirm|retry|reconnect|disconnect|remove|update)\b|->|→",
    re.I,
)

GENERIC_API_TOKENS = {
    "api", "docs", "documentation", "readme", "example", "examples", "resource",
    "library", "package", "method", "methods", "function", "functions", "interface",
}

SECTION_MIN_WORDS = {
    "Use when": 4,
    "Do not use when": 4,
    "Alternatives": 6,
    "Prerequisites and installation": 5,
    "Mental model": 8,
    "Client/server placement": 12,
    "Common path": 4,
    "Lifecycle and cleanup": 6,
    "API used by this skill": 4,
    "Failure modes": 6,
    "Limitations": 4,
    "Security notes": 8,
    "Version drift": 8,
}


COMMAND_TOOL_RE = re.compile(
    r"\b(?:python\d*|pytest|luau|lune|rojo|selene|stylua|npm|pnpm|yarn|bun|cargo|git|wally|aftman)\b",
    re.I,
)

CODELIKE_RUN_RE = re.compile(
    r"(?:"
    r"[A-Za-z_][A-Za-z0-9_.:]*\s*\([^)]*\)"  # function/method call
    r"|(?:^|\s)[./~]?[A-Za-z0-9_.-]+[/\\][A-Za-z0-9_./\\-]+"  # path
    r")",
    re.I,
)

EXPECTED_LITERAL_PATTERN = (
    r"(?:`[^`]+`|['\"][^'\"]+['\"]|\b\d+(?:\.\d+)?\b|\b(?:true|false|nil)\b)"
)

PASS_RELATION_RE = re.compile(
    r"(?:"
    rf"\b(?:{OBSERVABLE_TARGET_PATTERN})\b"
    r"[^.!?\n]{0,80}\b(?:is|are|exists?|equals?|matches?|contains?|becomes?|remains?|changes?\s+to|returns?|prints?|logs?|emits?|fires?|receives?|shows?)\b"
    # Permit a short descriptor such as "one line:" between the relation and
    # the expected literal without spanning into another sentence.
    r"[^.!?\n]{0,40}" + EXPECTED_LITERAL_PATTERN +
    # Also accept common noun-first conditions such as
    # "Part named `Probe` exists in Workspace" where the expected literal
    # appears before the observable relation.
    rf"|\b(?:{OBSERVABLE_TARGET_PATTERN})\b"
    r"[^.!?\n]{0,40}" + EXPECTED_LITERAL_PATTERN +
    r"[^.!?\n]{0,40}\b(?:is|are|exists?|equals?|matches?|contains?|becomes?|remains?|changes?\s+to|returns?|prints?|logs?|emits?|fires?|receives?|shows?)\b"
    # Relation-first conditions are common for container checks, for example
    # "Workspace contains a Part named `Probe`". Keep both the observable
    # target and expected literal close to the relation.
    r"|\b(?:contains?|creates?|returns?|prints?|logs?|emits?|fires?|receives?|shows?)\b"
    rf"[^.!?\n]{{0,40}}\b(?:{OBSERVABLE_TARGET_PATTERN})\b"
    r"[^.!?\n]{0,40}" + EXPECTED_LITERAL_PATTERN +
    r"|\b(?:returns?|prints?|logs?|emits?|fires?|receives?|shows?)\b"
    r"[^.!?\n]{0,40}" + EXPECTED_LITERAL_PATTERN +
    r")",
    re.I,
)


def iter_fenced_blocks(text: str):
    """Yield ``(info, content)`` for Markdown fenced blocks."""
    info = ""
    content: list[str] = []
    fence_char: str | None = None
    fence_len = 0
    close_re: re.Pattern[str] | None = None

    for raw_line in mask_html_comments(text).splitlines():
        if fence_char is None:
            match = FENCE_RE.match(raw_line)
            if not match:
                continue
            marker = match.group(1)
            fence_char = marker[0]
            fence_len = len(marker)
            info = match.group(2).strip()
            content = []
            close_re = re.compile(
                rf"^[ \t]{{0,3}}{re.escape(fence_char)}{{{fence_len},}}[ \t]*$"
            )
            continue

        if close_re is not None and close_re.match(raw_line):
            yield info, "\n".join(content)
            info = ""
            content = []
            fence_char = None
            fence_len = 0
            close_re = None
            continue
        content.append(raw_line)


CODE_EXAMPLE_SIGNAL_RE = re.compile(
    r"(?:"
    r"\b(?:local|function|return|require|if|then|else|elseif|for|while|repeat|until|end|"
    r"class|def|import|from|const|let|var|echo|curl|invoke|new)\b"
    r"|[(){}\[\];=]"
    r"|^[ \t]*[A-Za-z_][A-Za-z0-9_.-]*[ \t]*:[ \t]*\S+"
    r")",
    re.M | re.I,
)


def has_executable_fenced_example(content: str) -> bool:
    for info, fenced in iter_fenced_blocks(content):
        language = info.split(None, 1)[0].lower() if info else ""
        if language in {"text", "plaintext", "markdown", "md"}:
            continue
        if COMMAND_TOOL_RE.search(fenced) or CODELIKE_RUN_RE.search(fenced) or CODE_EXAMPLE_SIGNAL_RE.search(fenced):
            return True
    return False


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("SKILL.md frontmatter is not closed")
    raw = text[4:end]
    body = text[end + 5 :]
    try:
        loaded = load_yaml(raw)
    except ValueError as exc:
        raise ValueError(f"invalid frontmatter: {exc}") from exc
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        raise ValueError("SKILL.md frontmatter must be a YAML mapping")
    data: dict[str, str] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise ValueError(f"frontmatter keys must be strings, got {key!r}")
        if isinstance(value, (dict, list)):
            raise ValueError(f"frontmatter field {key!r} must be a scalar value")
        data[key] = "" if value is None else str(value).strip()
    return data, body


FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")


def mask_html_comments(text: str) -> str:
    """Mask Markdown HTML comments while preserving offsets and line breaks."""
    def repl(match: re.Match[str]) -> str:
        return "".join("\n" if ch == "\n" else "\r" if ch == "\r" else " " for ch in match.group(0))

    return re.sub(r"<!--.*?(?:-->|$)", repl, text, flags=re.S)


def iter_unfenced_lines(text: str):
    """Yield ``(start, end, line)`` triples for Markdown lines outside fences."""
    offset = 0
    fence_char: str | None = None
    fence_len = 0
    close_re: re.Pattern[str] | None = None
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        if fence_char is None:
            match = FENCE_RE.match(line)
            if match:
                marker = match.group(1)
                fence_char = marker[0]
                fence_len = len(marker)
                close_re = re.compile(
                    rf"^[ \t]{{0,3}}{re.escape(fence_char)}{{{fence_len},}}[ \t]*$"
                )
                offset += len(raw_line)
                continue
        else:
            # A Markdown closing fence may only contain the matching marker
            # (at least as long as the opener) plus trailing whitespace. An
            # info-looking line such as ```text inside a longer fence is code,
            # not a close delimiter.
            if close_re is not None and close_re.match(line):
                fence_char = None
                fence_len = 0
                close_re = None
                offset += len(raw_line)
                continue
            offset += len(raw_line)
            continue
        if fence_char is None:
            yield offset, offset + len(raw_line), line
        offset += len(raw_line)

    # splitlines(keepends=True) omits a synthetic final line; no special handling
    # is needed because any real unterminated final line is included above.


def strip_fenced_blocks(text: str) -> str:
    """Return only Markdown lines outside fenced code blocks."""
    return "\n".join(line for _, _, line in iter_unfenced_lines(text))


def structural_headings(body: str, level: int) -> list[tuple[str, int, int]]:
    pattern = re.compile(rf"^{'#' * level}\s+(.+?)\s*$")
    headings: list[tuple[str, int, int]] = []
    for start, end, line in iter_unfenced_lines(mask_html_comments(body)):
        match = pattern.match(line)
        if match:
            headings.append((match.group(1).strip(), start, end))
    return headings


def parse_sections(body: str) -> tuple[dict[str, str], Counter[str]]:
    matches = structural_headings(body, 2)
    counts: Counter[str] = Counter(heading for heading, _, _ in matches)
    sections: dict[str, str] = {}
    for index, (heading, _, heading_end) in enumerate(matches):
        start = heading_end
        end = matches[index + 1][1] if index + 1 < len(matches) else len(body)
        # Preserve the first occurrence; duplicates are reported separately.
        # Remove only surrounding line breaks. Leading spaces on the first
        # content line are semantically relevant because four-space indentation
        # is Markdown code and must not satisfy labeled prose fields.
        sections.setdefault(heading, body[start:end].strip("\r\n"))
    return sections, counts


def has_substantive_content(content: str) -> bool:
    """Return True when a section has actual content rather than markup only."""
    content = mask_html_comments(content)
    if not content.strip():
        return False
    # Ignore fence markers and Markdown/list punctuation, but let code identifiers
    # count as content for sections whose shortest valid form may be code-heavy.
    cleaned = re.sub(r"```[A-Za-z0-9_-]*", " ", content)
    cleaned = cleaned.replace("```", " ")
    tokens = re.findall(r"[A-Za-z0-9_][A-Za-z0-9_./:-]*", cleaned)
    return any(token not in {"...", "…"} for token in tokens)


def extract_labeled_value(section: str, label: str) -> str | None:
    section = strip_fenced_blocks(mask_html_comments(section))
    match = re.search(
        rf"^[ \t]{{0,3}}(?:[-*][ \t]+)?{re.escape(label)}[ \t]*:[ \t]*(.*?)[ \t]*$",
        section,
        re.M | re.I,
    )
    if not match:
        return None
    return match.group(1).strip()


def parse_http_url(value: str) -> tuple[str, str] | None:
    # Labeled provenance fields should contain one HTTPS URL, not prose plus a URL.
    # Curated identities and portable evidence records already require HTTPS;
    # generated skills should not weaken that transport requirement.
    if re.search(r"\s", value):
        return None
    try:
        parsed = urlparse(value)
    except ValueError:
        return None
    if parsed.scheme != "https" or not parsed.netloc:
        return None
    host = validated_url_host(parsed)
    if not host:
        return None
    return value, host


def url_embeds_credentials(value: str) -> bool:
    """Reject provenance URLs that could leak credentials or ephemeral secrets."""
    try:
        parsed = urlparse(value)
    except ValueError:
        # Malformed URLs are rejected by parse_http_url; this helper must not
        # turn an ordinary validation failure into a validator traceback.
        return False
    if parsed.username is not None or parsed.password is not None:
        return True
    for component in (parsed.query, parsed.fragment):
        for key, _ in parse_qsl(component, keep_blank_values=True):
            normalized_key = key.strip().lower()
            if normalized_key in SENSITIVE_URL_QUERY_KEYS or SENSITIVE_QUERY_RE.search(normalized_key):
                return True
    return False


def url_identity(value: str) -> tuple[str, str]:
    """Normalize a source URL for duplicate-source detection.

    Query strings, fragments, and http-vs-https do not make the same source a
    distinct provenance source.
    """
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower().rstrip(".")
    path = re.sub(r"/+", "/", parsed.path or "/").rstrip("/") or "/"
    return host, path


def word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_]+", value))


def normalize_quality_text(value: str) -> str:
    """Normalize prose for conservative placeholder/vagueness checks."""
    cleaned = re.sub(r"```[A-Za-z0-9_-]*", " ", value)
    cleaned = cleaned.replace("```", " ")
    cleaned = re.sub(r"[`*_>#]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned.strip(" .:;!?-")


def is_vague_section(content: str) -> bool:
    # Code-heavy sections such as Common path may be valid with little or no
    # surrounding prose, so fenced code remains meaningful for this generic
    # content check. Fence-aware parsing is applied where structure/labels are
    # normative (headings, provenance, and verification fields).
    normalized = normalize_quality_text(mask_html_comments(content))
    if not normalized or normalized in VAGUE_SECTION_VALUES:
        return True
    return bool(
        re.fullmatch(
            r"(?:"
            r"use (?:it|(?:this|the) (?:module|resource|package|library|api)) (?:normally|as needed)"
            r"|(?:standard|normal) (?:usage|use)"
            r"|(?:follow|check|see|refer to) (?:the )?(?:upstream )?(?:docs|documentation|readme)"
            r")",
            normalized,
            re.I,
        )
    )


def concrete_list_items(content: str, min_words: int = 3) -> list[str]:
    """Return non-placeholder Markdown list/numbered items outside code fences."""
    unfenced = strip_fenced_blocks(mask_html_comments(content))
    items: list[str] = []
    for match in re.finditer(r"^[ \t]{0,3}(?:[-*+]|\d+[.)])[ \t]+(.+?)\s*$", unfenced, re.M):
        value = match.group(1).strip()
        if word_count(value) >= min_words and not is_vague_section(value):
            items.append(value)
    return items


def section_word_count(content: str, *, include_fenced: bool = True) -> int:
    """Count meaningful tokens, optionally excluding fenced code blocks."""
    cleaned = mask_html_comments(content)
    if not include_fenced:
        cleaned = strip_fenced_blocks(cleaned)
    else:
        cleaned = re.sub(r"^[ \t]{0,3}(?:```+|~~~+).*?$", " ", cleaned, flags=re.M)
    return word_count(cleaned)


def validate_section_shapes(sections: dict[str, str], errors: list[str]) -> None:
    """Apply conservative section-specific structural quality checks."""
    prose_required = {
        "Use when",
        "Do not use when",
        "Alternatives",
        "Mental model",
        "Client/server placement",
        "Lifecycle and cleanup",
        "Failure modes",
        "Limitations",
        "Security notes",
        "Version drift",
    }
    for heading, minimum in SECTION_MIN_WORDS.items():
        content = sections.get(heading, "")
        count = section_word_count(content, include_fenced=heading not in prose_required) if content else 0
        if content and count < minimum:
            errors.append(
                f"required section is too thin to carry its contract ({minimum}+ words): {heading}"
            )

    for heading in ("Use when", "Do not use when", "Limitations"):
        content = sections.get(heading, "")
        if content and not concrete_list_items(content, min_words=3):
            errors.append(f"{heading} must contain at least one concrete list item")

    installation = sections.get("Prerequisites and installation", "")
    if installation and not concrete_list_items(installation, min_words=4):
        errors.append("Prerequisites and installation must contain at least one concrete ordered/list step")

    alternatives = sections.get("Alternatives", "")
    if alternatives:
        alternatives_prose = strip_fenced_blocks(mask_html_comments(alternatives))
        alternatives_words = section_word_count(alternatives, include_fenced=False)
        explicit_none = bool(NO_MEANINGFUL_ALTERNATIVE_RE.search(alternatives_prose)) and alternatives_words >= 8
        # The generated-skill contract and shipped template both allow an
        # Alternatives section to be prose. Do not force a Markdown-list
        # presentation when the prose itself contains substantive decision
        # guidance. This is intentionally conservative: short/generic prose
        # still fails, while normal forms such as "Use X when ..." pass.
        substantive_prose = (
            alternatives_words >= 10
            and not is_vague_section(alternatives_prose)
            and bool(ALTERNATIVES_DECISION_RE.search(alternatives_prose))
        )
        if not explicit_none and not concrete_list_items(alternatives, min_words=4) and not substantive_prose:
            errors.append(
                "Alternatives must name at least one concrete alternative/built-in, or explicitly explain why no meaningful alternative exists"
            )

    common_path = sections.get("Common path", "")
    if common_path:
        has_fenced_example = has_executable_fenced_example(common_path)
        if not has_fenced_example and not concrete_list_items(common_path, min_words=3):
            errors.append("Common path must contain an executable/example code fence or concrete ordered/list steps")

    lifecycle = sections.get("Lifecycle and cleanup", "")
    if lifecycle:
        lifecycle_unfenced = strip_fenced_blocks(mask_html_comments(lifecycle))
        for label in ("Initialization", "Reuse", "Cleanup/destruction"):
            field_count = len(
                re.findall(
                    rf"^[ \t]{{0,3}}(?:[-*][ \t]+)?{re.escape(label)}[ \t]*:",
                    lifecycle_unfenced,
                    re.M | re.I,
                )
            )
            if field_count > 1:
                errors.append(f"Lifecycle and cleanup contains duplicate labeled field: {label}")
            value = extract_labeled_value(lifecycle, label)
            if value is None:
                errors.append(f"Lifecycle and cleanup is missing labeled field: {label}")
            elif word_count(value) < 2 or is_vague_section(value):
                errors.append(f"Lifecycle and cleanup field is too thin/vague: {label}")

    api = sections.get("API used by this skill", "")
    if api:
        api_prose = strip_fenced_blocks(mask_html_comments(api))
        api_tokens = [fragment.strip() for fragment in re.findall(r"`([^`\n]+)`", api_prose)]
        api_identifiers = []
        for token in api_tokens:
            if token.lower() in GENERIC_API_TOKENS:
                continue
            if re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]*(?:(?:[.:])[A-Za-z_][A-Za-z0-9_]*)*(?:\([^`\n]*\))?",
                token,
            ):
                api_identifiers.append(token)
        if not api_identifiers and not NO_CALLABLE_API_RE.search(api_prose):
            errors.append(
                "API used by this skill must name verified API identifiers in backticks or explicitly state that no callable API is exposed"
            )

    failure_modes = sections.get("Failure modes", "")
    if failure_modes:
        h3 = structural_headings(failure_modes, 3)
        if not h3:
            errors.append("Failure modes must contain at least one level-3 symptom/failure heading")
        else:
            diagnosed_failure = False
            for index, (_, _, heading_end) in enumerate(h3):
                end = h3[index + 1][1] if index + 1 < len(h3) else len(failure_modes)
                detail = strip_fenced_blocks(mask_html_comments(failure_modes[heading_end:end]))
                if word_count(detail) >= 5 and FAILURE_DIAGNOSIS_RE.search(detail):
                    diagnosed_failure = True
                    break
            if not diagnosed_failure:
                errors.append(
                    "Failure modes must give at least one substantive cause/diagnosis/repair under a level-3 failure heading"
                )

    security_notes = sections.get("Security notes", "")
    if security_notes:
        security_prose = strip_fenced_blocks(mask_html_comments(security_notes))
        explicit_none = bool(NO_SPECIAL_SECURITY_RE.search(security_prose))
        has_boundary = bool(SECURITY_TOPIC_RE.search(security_prose))
        has_action = bool(SECURITY_ACTION_RE.search(security_prose))
        if explicit_none:
            # Even when the resource adds no special trust boundary, the skill
            # contract still requires normal Roblox server-authoritative
            # expectations to remain explicit rather than disappearing behind a
            # blanket "no concerns" statement.
            preserves_server_authority = bool(
                contains_word(security_prose, "server")
                and (
                    re.search(r"\b(?:authority|authoritative)\b", security_prose, re.I)
                    or (
                        re.search(r"\bvalidat(?:e|es|ed|ing|ion)\b", security_prose, re.I)
                        and re.search(r"\b(?:client|remote|input|payload)\b", security_prose, re.I)
                    )
                )
            )
            if not preserves_server_authority:
                errors.append(
                    "Security notes that claim no resource-specific concern must still preserve normal Roblox server-authoritative expectations"
                )
        elif not (has_boundary and has_action):
            errors.append(
                "Security notes must identify a concrete trust/safety boundary with actionable guidance, or explicitly state that no resource-specific security concern applies"
            )

    version_drift = sections.get("Version drift", "")
    if version_drift:
        version_drift_prose = strip_fenced_blocks(mask_html_comments(version_drift))
        if not re.search(r"\b(?:version|release|commit|upstream|source)\b", version_drift_prose, re.I):
            errors.append("Version drift must identify what upstream version/source state can drift")
        if not re.search(r"\b(?:check|review|compare|revalidate|validate|inspect)\b", version_drift_prose, re.I):
            errors.append("Version drift must state a concrete re-check/revalidation action")


def extract_required_labeled_value(section: str, label: str) -> str | None:
    """Extract a required operational field from prose, never from code fences."""
    return extract_labeled_value(section, label)


def looks_like_direct_tool_command(value: str) -> bool:
    """Recognize concise CLI commands without treating tool-name prose as runnable."""
    raw = value.strip().rstrip(".").strip()
    if not raw or re.search(r"\s{2,}", raw):
        # Multiple spaces are not invalid shell syntax, but rejecting them here
        # keeps this heuristic conservative; natural-language steps still use
        # the action/context path below.
        return False

    if re.fullmatch(r"(?:pytest|luau|lune|rojo|selene|stylua)(?:\s+\S+)*", raw, re.I):
        return True

    if re.match(r"^python\d*\b", raw, re.I):
        return bool(
            re.search(r"\s-(?:m|c)\b", raw, re.I)
            or re.search(r"\s\S+\.py(?:\s|$)", raw, re.I)
            or re.search(r"\s[./~\\]\S+", raw)
        )

    return bool(
        re.match(
            r"^(?:npm|pnpm|yarn|bun|cargo|git|wally|aftman)\s+"
            r"(?:test|run|check|build|install|exec|fmt|format|lint|status|clone|"
            r"rev-parse|add|remove|update|publish)(?:\s|$)",
            raw,
            re.I,
        )
    )


def is_concrete_verification_step(value: str) -> bool:
    normalized = normalize_quality_text(value)
    if normalized in WEAK_VERIFICATION_VALUES:
        return False
    if GENERIC_VERIFICATION_RE.fullmatch(normalized):
        return False
    if re.match(r"^(?:do not|don't|never|avoid)\b", normalized, re.I):
        return False

    # Backticks help distinguish an actual command/call from prose that merely
    # mentions a tool. A random multi-word backticked phrase is not executable.
    inline_fragments = [fragment.strip() for fragment in re.findall(r"`([^`]+)`", value)]
    for fragment in inline_fragments:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.:]*\s*\([^)]*\)", fragment):
            return True
        if looks_like_direct_tool_command(fragment):
            return True

    # A concise raw command is also acceptable, but only when it has recognizable
    # CLI structure. This keeps sentences such as "Python docs may help later"
    # from satisfying the verification contract.
    if looks_like_direct_tool_command(value):
        return True

    if word_count(value) < 5:
        return False
    action = re.search(
        r"\b(?:run|execute|start|open|launch|call|invoke|require|create|insert|"
        r"place|set|send|fire|trigger|join|play|publish|load|connect|disconnect)\b",
        value,
        re.I,
    )
    execution_context = bool(
        VERIFICATION_CONTEXT_RE.search(value)
        or CODELIKE_RUN_RE.search(value)
        or COMMAND_TOOL_RE.search(value)
    )
    return bool(action and execution_context)


def is_concrete_pass_condition(value: str) -> bool:
    normalized = normalize_quality_text(value)
    if word_count(value) < 3 or normalized in WEAK_PASS_CONDITION_VALUES:
        return False
    if GENERIC_PASS_RE.search(normalized):
        return False

    has_expected_value = bool(EXPECTED_VALUE_RE.search(value))
    has_target = bool(OBSERVABLE_TARGET_RE.search(value))
    has_observable_verb = bool(OBSERVABLE_VERB_RE.search(value))

    # A number or quoted/backticked literal is not sufficient by itself. The
    # pass condition must connect the expected value to something observable.
    if has_expected_value:
        return bool(PASS_RELATION_RE.search(value))

    # Without an explicit expected literal/comparison, require both an
    # observable transition/action and a concrete thing being observed.
    return bool(word_count(value) >= 4 and has_observable_verb and has_target)


def contains_word(content: str, word: str) -> bool:
    return bool(re.search(rf"\b{re.escape(word)}\b", content, re.I))


def validate_skill(root: Path) -> tuple[list[str], list[str]]:
    skill = root / "SKILL.md"
    errors: list[str] = []
    warnings: list[str] = []

    if not skill.is_file():
        return [f"missing {skill}"], warnings

    # utf-8-sig accepts ordinary UTF-8 and harmlessly strips a Windows/editor BOM.
    try:
        text = skill.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return ["SKILL.md must be valid UTF-8 text"], warnings
    except OSError as exc:
        return [f"could not read {skill}: {exc}"], warnings

    try:
        meta, body = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)], warnings

    for field in ("name", "description"):
        if not meta.get(field):
            errors.append(f"missing frontmatter field: {field}")

    name = meta.get("name", "")
    if name and not SLUG_RE.fullmatch(name):
        errors.append("frontmatter name must be a lowercase kebab-case slug")

    description = meta.get("description", "")
    if description and word_count(description) < 3:
        errors.append("frontmatter description is too thin to state a usable capability/trigger")

    h1 = structural_headings(body, 1)
    if not h1 or not h1[0][0]:
        errors.append("missing resource name as a level-1 heading")
    elif len(h1) > 1:
        errors.append("duplicate level-1 resource heading")

    sections, heading_counts = parse_sections(body)
    for heading in REQUIRED_HEADINGS:
        count = heading_counts.get(heading, 0)
        if count == 0:
            errors.append(f"missing required heading: {heading}")
        elif count > 1:
            errors.append(f"duplicate required heading: {heading}")
        elif not has_substantive_content(sections.get(heading, "")):
            errors.append(f"required section is empty: {heading}")
        elif is_vague_section(sections.get(heading, "")):
            errors.append(f"required section is placeholder/vague: {heading}")

    validate_section_shapes(sections, errors)

    if PLACEHOLDER_LINE_RE.search(body):
        errors.append("unresolved placeholder line found (for example TBD/TODO/unknown)")

    for sentinel in TEMPLATE_SENTINELS:
        if sentinel in text:
            errors.append(f"unresolved template content: {sentinel}")
    for pattern in TEMPLATE_LINE_PATTERNS:
        if pattern.search(text):
            errors.append(f"unresolved template line matching: {pattern.pattern}")

    provenance = sections.get("Provenance", "")
    provenance_unfenced = strip_fenced_blocks(mask_html_comments(provenance))
    provenance_values: dict[str, str | None] = {}
    legacy_provenance_labels: list[str] = []
    for canonical_label, aliases in PROVENANCE_FIELD_ALIASES.items():
        found: list[tuple[str, str | None]] = []
        for label in aliases:
            field_count = len(
                re.findall(
                    rf"^[ \t]{{0,3}}(?:[-*][ \t]+)?{re.escape(label)}[ \t]*:",
                    provenance_unfenced,
                    re.M | re.I,
                )
            )
            if field_count > 1:
                errors.append(f"provenance contains duplicate labeled field: {label}")
            if field_count:
                found.append((label, extract_labeled_value(provenance, label)))

        if len(found) > 1:
            errors.append(
                f"provenance contains conflicting aliases for {canonical_label}: "
                + ", ".join(label for label, _ in found)
            )
            provenance_values[canonical_label] = found[0][1]
            continue
        if not found:
            errors.append(f"provenance is missing labeled field: {canonical_label}")
            provenance_values[canonical_label] = None
            continue

        used_label, value = found[0]
        provenance_values[canonical_label] = value
        if value is not None and not value:
            errors.append(f"provenance field is empty: {used_label}")
        if used_label != canonical_label:
            legacy_provenance_labels.append(used_label)

    if legacy_provenance_labels:
        warnings.append(
            "legacy provenance labels used (" + ", ".join(legacy_provenance_labels)
            + "); prefer Source version/release/commit and Source review date"
        )

    devforum_value = provenance_values.get("DevForum")
    devforum_url: str | None = None
    if devforum_value:
        if url_embeds_credentials(devforum_value):
            errors.append("DevForum provenance URL must not embed credentials or secret-like query parameters")
        parsed = parse_http_url(devforum_value)
        if parsed:
            devforum_url, host = parsed
            if host != "devforum.roblox.com":
                errors.append("DevForum provenance URL must use devforum.roblox.com")
            else:
                topic_path = urlparse(devforum_url).path
                if not DEVFORUM_TOPIC_PATH_RE.fullmatch(topic_path):
                    errors.append("DevForum provenance URL must identify a specific DevForum topic, not a category/home/search page")
        elif NO_DEVFORUM_RE.fullmatch(devforum_value.strip()):
            warnings.append(
                "no DevForum topic recorded; acceptable when the resource has no applicable DevForum provenance"
            )
        else:
            errors.append(
                "DevForum provenance must be a single valid DevForum topic URL or explicitly state that no DevForum topic is used/applicable"
            )

    canonical_value = provenance_values.get("Canonical source/docs")
    canonical_url: str | None = None
    if canonical_value:
        if url_embeds_credentials(canonical_value):
            errors.append("Canonical source/docs URL must not embed credentials or secret-like query parameters")
        parsed = parse_http_url(canonical_value)
        if parsed:
            canonical_url, _ = parsed
        elif NO_SEPARATE_CANONICAL_RE.fullmatch(canonical_value.strip()):
            warnings.append(
                "no separate canonical source/docs URL recorded; acceptable only when the DevForum thread is the canonical source"
            )
        else:
            errors.append(
                "Canonical source/docs must be a single valid https:// URL or explicitly state that no separate canonical source exists"
            )

    if devforum_url and canonical_url and url_identity(devforum_url) == url_identity(canonical_url):
        errors.append("DevForum and canonical source/docs URLs must not identify the same source")
    if not devforum_url and not canonical_url:
        errors.append("provenance must include at least one concrete source URL")

    version_value = provenance_values.get("Source version/release/commit")
    if version_value:
        normalized_state = re.sub(r"[._/-]+", " ", version_value).strip().lower()
        if word_count(version_value) == 0 or normalized_state in {
            "n a",
            "na",
            "none",
            "unknown",
            "tbd",
            "not available",
            "release",
            "version",
            "commit",
            "build",
            "branch",
            "source",
            "snapshot",
            "tag",
            "stable",
        }:
            errors.append(
                "source version/release/commit must name a version/commit or explicit source state, not a generic unknown value"
            )
        elif not has_immutable_version_evidence(version_value):
            if VOLATILE_VERSION_TOKEN_RE.search(version_value):
                errors.append(
                    "source version/release/commit must not use a volatile pointer such as latest/current/main without an immutable identifier or dated source state"
                )
            else:
                errors.append(
                    "source version/release/commit must contain an immutable version/commit, an explicitly labeled tag/release/build, or a dated source state"
                )

    validation_date = provenance_values.get("Source review date")
    if validation_date:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", validation_date):
            errors.append("Source review date must use exact YYYY-MM-DD form")
        else:
            try:
                parsed_validation_date = date.fromisoformat(validation_date)
            except ValueError:
                errors.append("Source review date must be a real ISO date in YYYY-MM-DD form")
            else:
                if parsed_validation_date > date.today():
                    errors.append("Source review date cannot be in the future")

    resource_verification = provenance_values.get("Resource verification")
    if resource_verification:
        normalized_verification = resource_verification.strip().lower()
        if normalized_verification not in {"verified", "unverified", "unavailable"}:
            errors.append("Resource verification must be exactly verified, unverified, or unavailable")

    # Human-facing source/verification summaries near the title must agree with
    # the normative provenance fields. Keep support for the legacy summary so
    # older generated skills can still be checked without conflating it with
    # the new, explicit runtime-verification status.
    body_unfenced = strip_fenced_blocks(mask_html_comments(body))
    summary_match = re.search(
        r"Guidance targets\s+\*\*(.+?)\*\*\s+\(source reviewed\s+\*\*(\d{4}-\d{2}-\d{2})\*\*\)\.\s+Resource verification:\s+\*\*(verified|unverified|unavailable)\*\*",
        body_unfenced,
        re.I,
    )
    if summary_match and version_value and validation_date and resource_verification:
        summary_version = summary_match.group(1).strip()
        summary_date = summary_match.group(2)
        summary_verification = summary_match.group(3).lower()
        if summary_version != version_value.strip():
            errors.append("title source summary version disagrees with Provenance")
        if summary_date != validation_date:
            errors.append("title source summary date disagrees with Provenance")
        if summary_verification != resource_verification.strip().lower():
            errors.append("title resource-verification summary disagrees with Provenance")

    legacy_summary_match = re.search(
        r"Validated against\s+\*\*(.+?)\*\*\s+on\s+\*\*(\d{4}-\d{2}-\d{2})\*\*",
        body_unfenced,
        re.I,
    )
    if legacy_summary_match and version_value and validation_date:
        summary_version = legacy_summary_match.group(1).strip()
        summary_date = legacy_summary_match.group(2)
        if summary_version != version_value.strip():
            errors.append("title validation summary version disagrees with Provenance")
        if summary_date != validation_date:
            errors.append("title validation summary date disagrees with Provenance")
        warnings.append("legacy 'Validated against' title summary is ambiguous; prefer explicit source review + Resource verification status")

    client_server = sections.get("Client/server placement", "")
    client_server_prose = strip_fenced_blocks(mask_html_comments(client_server))
    if client_server and (
        not contains_word(client_server_prose, "client") or not contains_word(client_server_prose, "server")
    ):
        errors.append(
            "Client/server placement must explicitly describe both client and server behavior/placement"
        )

    verify = sections.get("Verify after installation", "")
    run_step = extract_required_labeled_value(verify, "Run")
    pass_condition = extract_required_labeled_value(verify, "Pass condition")

    if run_step is None:
        errors.append("verification recipe is missing an explicit Run: step in its verification section")
    elif not run_step:
        errors.append("verification Run: step is empty")
    elif not is_concrete_verification_step(run_step):
        errors.append("verification Run: step is too thin/vague to be runnable or checkable")

    if pass_condition is None:
        errors.append("verification recipe is missing an explicit Pass condition: in its verification section")
    elif not pass_condition:
        errors.append("verification Pass condition: is empty")
    elif not is_concrete_pass_condition(pass_condition):
        errors.append("Pass condition is too thin/vague to describe a specific observable success condition")

    # Reject duplicate operational labels because the validator otherwise has
    # to guess which recipe is normative.
    verify_unfenced = strip_fenced_blocks(mask_html_comments(verify))
    for label in ("Run", "Pass condition"):
        label_count = len(
            re.findall(
                rf"^[ \t]{{0,3}}(?:[-*][ \t]+)?{re.escape(label)}[ \t]*:",
                verify_unfenced,
                re.M | re.I,
            )
        )
        if label_count > 1:
            errors.append(f"verification recipe contains duplicate {label}: fields")

    # Strong hint, but not a universal hard requirement.
    if "```luau" not in body.lower():
        warnings.append("no Luau example found; acceptable only if the resource is non-code/tooling")

    return errors, warnings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Structurally validate a generated Roblox resource skill. "
            "This does not replace behavioral or runtime validation."
        )
    )
    parser.add_argument(
        "generated_skill_directory",
        type=Path,
        help="directory containing the generated skill's SKILL.md",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.generated_skill_directory.resolve()
    errors, warnings = validate_skill(root)

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
        return 1

    print("PASS: structural generated-skill checks passed")
    for warning in warnings:
        print(f"WARN: {warning}")
    print("NOTE: this is not proof of semantic correctness, documentation truth, or runtime behavior; behavioral/runtime validation are still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
