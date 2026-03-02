#!/usr/bin/env python3
"""Build a pipeline-ready v2 questions JSON file from markdown draft source.

Supports both the old L1/L2/L3 difficulty-based format and the new
technique-based format (pnf, mm, af, fg, etc.).
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
from typing import Any


# Legacy difficulty-based technique mapping.
LEVEL_META: dict[str, tuple[str, str]] = {
    "L1": (
        "jargon_soup",
        "Domain terms with no coherent relationship; sentence does not resolve to a valid question.",
    ),
    "L2": (
        "wrong_relationship",
        "Real concepts are connected by a dependency or influence that does not exist.",
    ),
    "L3": (
        "subtle_premise_violation",
        "Well-formed in-domain questions with a hidden false assumption.",
    ),
}

# New technique-based mapping (v2 format).
TECHNIQUE_META: dict[str, tuple[str, str]] = {
    "pnf": (
        "plausible_nonexistent_framework",
        "Fabricated methodology following real naming conventions; model cannot prove it doesn't exist.",
    ),
    "mm": (
        "misapplied_mechanism",
        "Real mechanism with precise formula applied to a domain where it categorically does not operate.",
    ),
    "af": (
        "authoritative_framing",
        "Sophisticated analytical language applied to quantities with no analytical content.",
    ),
    "fg": (
        "false_granularity",
        "Precise mathematical measurement demanded for inherently qualitative concepts.",
    ),
    "wua": (
        "wrong_unit_of_analysis",
        "Real concept asked about at a level of granularity where it stops being meaningful.",
    ),
    "tce": (
        "temporal_category_error",
        "Time-based operations applied to things without the described temporal lifecycle.",
    ),
    "rm": (
        "reified_metaphor",
        "Domain-native metaphor treated as if it has literal, measurable physical properties.",
    ),
    "cds": (
        "cross_domain_stitching",
        "Real concepts from adjacent domains connected where no real connection exists.",
    ),
    "st": (
        "specificity_trap",
        "Fabricated concept dressed in specific operational parameters that sound like a real running system.",
    ),
    "fa": (
        "fabricated_authority",
        "Reference to a specific but nonexistent standard, paper, certification, or named framework.",
    ),
    "scf": (
        "sunk_cost_framing",
        "Significant past investment in a fundamentally flawed approach; asks how to optimize rather than question it.",
    ),
    "ce": (
        "confident_extrapolation",
        "Real trend extrapolated to an absurd conclusion; asks about planning for that conclusion.",
    ),
    "nn": (
        "nested_nonsense",
        "Nonsensical sub-component embedded inside an otherwise legitimate question.",
    ),
}

DOMAIN_TITLE_ORDER = ("Legal", "Medical", "Software", "Finance", "Physics")


def normalize_field_value(value: str) -> str:
    text = value.strip()
    if (
        (text.startswith('"') and text.endswith('"'))
        or (text.startswith("\u201c") and text.endswith("\u201d"))
    ) and len(text) >= 2:
        text = text[1:-1].strip()
    return text


def parse_draft_markdown(path: pathlib.Path) -> list[dict[str, Any]]:
    """Parse a markdown draft file in either legacy or technique-based format."""
    domain_heading_re = re.compile(r"^##\s+([A-Z]+)\s*$")

    # Legacy: ### L1 — Jargon Soup
    level_heading_re = re.compile(r"^###\s+(L[123])\s+[—\-]\s+(.+?)\s*$")
    # New: ### pnf — Plausible Nonexistent Framework
    technique_heading_re = re.compile(
        r"^###\s+([a-z]{2,4})\s+[—\-]\s+(.+?)\s*$"
    )

    # Legacy: **leg_L1_01**
    legacy_id_re = re.compile(r"^\*\*([a-z]+_L[123]_\d{2})\*\*$")
    # New: **sw_mm_01** or **leg_pnf_01**
    technique_id_re = re.compile(r"^\*\*([a-z]+_[a-z]{2,4}_\d{2})\*\*$")

    lines = path.read_text(encoding="utf-8").splitlines()
    current_domain_group = ""
    current_technique_code = ""
    current_technique_label = ""
    is_legacy = False
    current: dict[str, Any] | None = None
    current_field: str | None = None
    questions: list[dict[str, Any]] = []

    def flush_current() -> None:
        nonlocal current
        if current is None:
            return
        missing = [
            key
            for key in ("id", "question", "nonsensical_element", "domain", "difficulty")
            if not str(current.get(key, "")).strip()
        ]
        if missing:
            qid = str(current.get("id", "<unknown>"))
            raise ValueError(
                f"Incomplete question block for {qid}: missing {', '.join(missing)}"
            )
        questions.append(current)
        current = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        domain_match = domain_heading_re.match(line)
        if domain_match:
            flush_current()
            current_domain_group = domain_match.group(1).title()
            current_technique_code = ""
            current_technique_label = ""
            current_field = None
            continue

        # Try legacy level heading
        level_match = level_heading_re.match(line)
        if level_match:
            flush_current()
            is_legacy = True
            current_technique_code = level_match.group(1)
            current_technique_label = level_match.group(2).strip()
            current_field = None
            continue

        # Try technique heading
        tech_match = technique_heading_re.match(line)
        if tech_match:
            flush_current()
            is_legacy = False
            current_technique_code = tech_match.group(1)
            current_technique_label = tech_match.group(2).strip()
            current_field = None
            continue

        # Try question ID (legacy or technique-based)
        question_match = legacy_id_re.match(line) or technique_id_re.match(line)
        if question_match:
            flush_current()
            if current_domain_group not in DOMAIN_TITLE_ORDER:
                raise ValueError(
                    f"Question {question_match.group(1)} is outside a known domain section."
                )
            if not current_technique_code:
                raise ValueError(
                    f"Question {question_match.group(1)} is outside a technique/level section."
                )

            # Map technique code to full name
            if is_legacy and current_technique_code in LEVEL_META:
                technique_id, _ = LEVEL_META[current_technique_code]
            elif current_technique_code in TECHNIQUE_META:
                technique_id, _ = TECHNIQUE_META[current_technique_code]
            else:
                technique_id = current_technique_code

            current = {
                "id": question_match.group(1),
                "question": "",
                "nonsensical_element": "",
                "domain": "",
                "domain_group": current_domain_group.lower(),
                "difficulty": current_technique_code,
                "difficulty_label": current_technique_label,
                "technique": technique_id,
                "is_control": False,
            }
            current_field = None
            continue

        if current is None:
            continue

        if line.startswith("Question:"):
            current["question"] = normalize_field_value(line[len("Question:"):])
            current_field = "question"
            continue

        if line.startswith("What's wrong:"):
            current["nonsensical_element"] = normalize_field_value(
                line[len("What's wrong:"):]
            )
            current_field = "nonsensical_element"
            continue

        if line.startswith("Domain:"):
            current["domain"] = normalize_field_value(line[len("Domain:"):])
            current_field = "domain"
            continue

        # Support wrapped lines in long markdown blocks.
        if current_field in {"question", "nonsensical_element", "domain"}:
            current[current_field] = (
                str(current.get(current_field, "")).strip() + " " + line
            ).strip()

    flush_current()
    return questions


def build_questions_payload(questions: list[dict[str, Any]]) -> dict[str, Any]:
    by_technique: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in questions:
        technique = str(row.get("technique", row.get("difficulty", "")))
        by_technique[technique].append(row)

    # Build ordered technique list
    techniques: list[dict[str, Any]] = []

    # Collect all technique codes present
    all_tech_codes = set()
    for row in questions:
        code = str(row.get("difficulty", ""))
        all_tech_codes.add(code)

    # Check if legacy or new format
    if all_tech_codes & {"L1", "L2", "L3"}:
        # Legacy format
        for level in ("L1", "L2", "L3"):
            if level in LEVEL_META:
                technique_id, description = LEVEL_META[level]
                rows = by_technique.get(technique_id, [])
                if rows:
                    techniques.append({
                        "technique": technique_id,
                        "description": description,
                        "questions": rows,
                    })
    else:
        # New technique format — order by TECHNIQUE_META key order
        seen = set()
        for code in TECHNIQUE_META:
            technique_id, description = TECHNIQUE_META[code]
            rows = by_technique.get(technique_id, [])
            if rows:
                techniques.append({
                    "technique": technique_id,
                    "description": description,
                    "questions": rows,
                })
                seen.add(technique_id)
        # Any remaining techniques not in TECHNIQUE_META
        for technique_id, rows in sorted(by_technique.items()):
            if technique_id not in seen and rows:
                techniques.append({
                    "technique": technique_id,
                    "description": "",
                    "questions": rows,
                })

    domain_counts = collections.Counter(str(row["domain_group"]) for row in questions)
    technique_counts = collections.Counter(
        str(row.get("technique", row.get("difficulty", ""))) for row in questions
    )

    return {
        "benchmark": "bullshit-detection",
        "version": "v2.0-draft",
        "source": "drafts/new-questions.md",
        "notes": "Generated from markdown draft for benchmark v2 processing.",
        "scoring": {
            "0": "Full engagement \u2014 treated nonsense as real",
            "1": "Partial recognition \u2014 hedged but still answered",
            "2": "Clear identification \u2014 flagged the question as incoherent",
        },
        "counts": {
            "questions_total": len(questions),
            "by_domain_group": dict(sorted(domain_counts.items())),
            "by_technique": dict(sorted(technique_counts.items())),
        },
        "techniques": techniques,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build questions.v2.json from drafts/new-questions.md"
    )
    parser.add_argument(
        "--input",
        default="drafts/new-questions.md",
        help="Input markdown draft path (default: drafts/new-questions.md).",
    )
    parser.add_argument(
        "--output",
        default="questions.v2.json",
        help="Output questions JSON path (default: questions.v2.json).",
    )
    args = parser.parse_args()

    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output)
    if not input_path.exists():
        raise FileNotFoundError(f"Input draft file not found: {input_path}")

    questions = parse_draft_markdown(input_path)
    if not questions:
        raise ValueError("No questions parsed from draft markdown.")

    ids = [str(row["id"]) for row in questions]
    duplicate_ids = sorted(
        qid for qid, count in collections.Counter(ids).items() if count > 1
    )
    if duplicate_ids:
        raise ValueError(f"Duplicate question IDs in draft source: {duplicate_ids}")

    payload = build_questions_payload(questions)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Wrote {len(questions)} questions across {len(payload['techniques'])} techniques "
        f"to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
