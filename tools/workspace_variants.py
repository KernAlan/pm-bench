#!/usr/bin/env python3
"""Procedural workspace-variant generator for PM-Bench.

The public benchmark ships with one fixed cast (Alan, Josh, Sarah, ...), one
fixed company (Acme), and a handful of fixed project names. A model that
trained on this repo can memorize those tokens. Variants defeat that by
producing *semantically equivalent* scenarios where every person / company /
project name has been lexically substituted.

The substitution preserves all structural properties that the benchmark
actually scores on:

  * scenario ``id`` and ``correct_answer`` letter are untouched
  * scoring type (``mcq`` / ``keyword`` / ``tool_use``) is untouched
  * open-ended rubric shape is preserved; keyword lists are substituted when
    they reference substituted tokens

Inline ``workspace_files`` content is substituted in place. Fixture references
(``@fixtures/foo.md``) are rewritten to point at a parallel tree under
``fixtures/variants/<variant>/foo.md`` so the two casts can coexist.

Usage::

    python tools/workspace_variants.py --variant v2-neon
    python tools/workspace_variants.py --variant all
    python tools/workspace_variants.py --variant v3-helix --verify

The ``--verify`` flag runs the generated file through ``validate_schema.py``.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Variant packs
# -----------------------------------------------------------------------------
# Each pack is an ordered list of (old, new) pairs. Order matters because some
# tokens are substrings of others ("Alan" vs "Alan Kern"). We still use a
# two-pass placeholder strategy at substitution time so overlap between new
# tokens and old tokens (e.g. a new cast member named "Nina" while the original
# cast already contains a Nina Kowalski) is safe, but we also sort longest-key
# first as a second layer of defense.
#
# Keep these *value-for-value* swaps: a first name maps to a first name, a
# full name maps to a full name, a company maps to a company. Do NOT map a
# person to a company or vice versa — the scoring rubrics can key off either.

VariantPack = List[Tuple[str, str]]


VARIANT_PACKS: Dict[str, VariantPack] = {
    # ------------------------------------------------------------------
    # v2-neon: payments / fintech vibe
    # ------------------------------------------------------------------
    "v2-neon": [
        # Full names first (longer keys win)
        ("Alan Kern", "Maya Okonkwo"),
        ("Josh Reed", "Devon Park"),
        ("Sarah Chen", "Nina Reyes"),
        ("Marcus Washington", "Raj Shankar"),
        ("Priya Patel", "Elena Voss"),
        ("Alex Kim", "Theo Matsuda"),
        ("Rachel Torres", "Kai Mendoza"),
        ("Dev Okonkwo", "Lev Reinhardt"),
        ("Lisa Park", "Zara Nabil"),
        ("Jordan Rivera", "Sam Kaelani"),
        ("Nina Kowalski", "Paula Wexler"),
        # First names (apply after full-name substitutions via placeholders)
        ("Alan", "Maya"),
        ("Josh", "Devon"),
        ("Sarah", "Nina"),
        ("Marcus", "Raj"),
        ("Priya", "Elena"),
        ("Alex", "Theo"),
        ("Rachel", "Kai"),
        ("Dev", "Lev"),
        ("Lisa", "Zara"),
        ("Jordan", "Sam"),
        ("Nina", "Paula"),
        ("Maria", "Iris"),
        # Surnames that appear alone
        ("Kern", "Okonkwo"),
        # Companies
        ("Acme Corp", "NeonPay"),
        ("Acme", "NeonPay"),
        ("CloudFirst", "PulseNet"),
        ("Pinnacle Inc", "Terabyte Labs"),
        ("Pinnacle", "Terabyte"),
        ("Waverly Labs", "Catalyst Systems"),
        ("Waverly", "Catalyst"),
        ("Redstone Analytics", "Axiom Research"),
        ("Redstone", "Axiom"),
        # Products / projects (only substitute the *project label*, NOT generic
        # technical nouns like "events table" which scoring rubrics key on).
        ("TransactionEngine", "TransactionEngine"),  # self-map as documentation
    ],
    # ------------------------------------------------------------------
    # v3-helix: developer-tools / platform vibe
    # ------------------------------------------------------------------
    "v3-helix": [
        ("Alan Kern", "Priya Anand"),
        ("Josh Reed", "Anh Nguyen"),
        ("Sarah Chen", "Ola Bergstrom"),
        ("Marcus Washington", "Kian Farahani"),
        ("Priya Patel", "Sofia Marek"),
        ("Alex Kim", "Milos Horvat"),
        ("Rachel Torres", "Zane Abara"),
        ("Dev Okonkwo", "Tomas Ilves"),
        ("Lisa Park", "Yara Haddad"),
        ("Jordan Rivera", "Noor Siddiqui"),
        ("Nina Kowalski", "Hana Petrovic"),
        ("Alan", "Priya"),
        ("Josh", "Anh"),
        ("Sarah", "Ola"),
        ("Marcus", "Kian"),
        ("Priya", "Sofia"),  # original Priya -> Sofia (post-placeholder)
        ("Alex", "Milos"),
        ("Rachel", "Zane"),
        ("Dev", "Tomas"),
        ("Lisa", "Yara"),
        ("Jordan", "Noor"),
        ("Nina", "Hana"),
        ("Maria", "Leyla"),
        ("Kern", "Anand"),
        ("Acme Corp", "HelixOS"),
        ("Acme", "HelixOS"),
        ("CloudFirst", "MeshCore"),
        ("Pinnacle Inc", "Beacon Systems"),
        ("Pinnacle", "Beacon"),
        ("Waverly Labs", "Ironvine Research"),
        ("Waverly", "Ironvine"),
        ("Redstone Analytics", "Stratum Analytics"),
        ("Redstone", "Stratum"),
    ],
    # ------------------------------------------------------------------
    # v4-orbit: consumer SaaS / growth vibe
    # ------------------------------------------------------------------
    "v4-orbit": [
        ("Alan Kern", "Aisha Boateng"),
        ("Josh Reed", "Linh Tran"),
        ("Sarah Chen", "Tomasz Lewandowski"),
        ("Marcus Washington", "Marcus Delacroix"),
        ("Priya Patel", "Jade Okafor"),
        ("Alex Kim", "Ollie Hartley"),
        ("Rachel Torres", "Rin Tanaka"),
        ("Dev Okonkwo", "Bram Veldhuis"),
        ("Lisa Park", "Esi Asante"),
        ("Jordan Rivera", "Mateo Ibarra"),
        ("Nina Kowalski", "Selin Kaya"),
        ("Alan", "Aisha"),
        ("Josh", "Linh"),
        ("Sarah", "Tomasz"),
        ("Marcus", "Marcus"),  # coincident name, keep
        ("Priya", "Jade"),
        ("Alex", "Ollie"),
        ("Rachel", "Rin"),
        ("Dev", "Bram"),
        ("Lisa", "Esi"),
        ("Jordan", "Mateo"),
        ("Nina", "Selin"),
        ("Maria", "Fern"),
        ("Kern", "Boateng"),
        ("Acme Corp", "OrbitPulse"),
        ("Acme", "OrbitPulse"),
        ("CloudFirst", "Skyrail"),
        ("Pinnacle Inc", "Lumen Studios"),
        ("Pinnacle", "Lumen"),
        ("Waverly Labs", "Meridian Works"),
        ("Waverly", "Meridian"),
        ("Redstone Analytics", "Northstar Insights"),
        ("Redstone", "Northstar"),
    ],
}


# -----------------------------------------------------------------------------
# Substitution engine
# -----------------------------------------------------------------------------

# Sentinel that is guaranteed not to appear in any human-authored fixture text.
_PLACEHOLDER_FMT = "\x00PMBV{idx}\x00"


def _sorted_pack(pack: VariantPack) -> VariantPack:
    """Longest-key-first. Stable tie-break on original order."""
    return sorted(pack, key=lambda kv: (-len(kv[0]), pack.index(kv)))


def _build_regex(old: str) -> re.Pattern[str]:
    """Build a word-boundary-aware regex for a token.

    We use ``\b`` on both sides for single-word tokens (so 'Alan' doesn't
    match 'Alana') but drop the boundary at spaces for multi-word tokens
    (Python's ``\b`` is between word and non-word chars, so 'Alan Kern' with
    ``\b...\b`` still works at the edges).
    """
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(old) + r"(?![A-Za-z0-9])")


def substitute_text(text: str, pack: VariantPack) -> str:
    """Two-pass substitution.

    Pass 1: replace each old token with a unique placeholder.
    Pass 2: replace each placeholder with the new token.

    This prevents the classic cascade bug where a new value introduced in an
    earlier substitution gets re-substituted by a later rule.
    """
    pack = _sorted_pack(pack)

    # Pass 1: old -> placeholder
    for idx, (old, _new) in enumerate(pack):
        text = _build_regex(old).sub(_PLACEHOLDER_FMT.format(idx=idx), text)

    # Pass 2: placeholder -> new
    for idx, (_old, new) in enumerate(pack):
        text = text.replace(_PLACEHOLDER_FMT.format(idx=idx), new)

    return text


# -----------------------------------------------------------------------------
# Fixture-tree rewriting
# -----------------------------------------------------------------------------

def _rewrite_fixture_ref(ref: str, variant: str) -> str:
    """Rewrite an ``@fixtures/foo.md`` ref to ``@fixtures/variants/<v>/foo.md``."""
    prefix = "@fixtures/"
    if not ref.startswith(prefix):
        return ref
    rest = ref[len(prefix):]
    # If the ref is already pointing into the variants tree, leave it alone.
    if rest.startswith("variants/"):
        return ref
    return f"{prefix}variants/{variant}/{rest}"


def generate_variant_fixtures(
    variant: str, pack: VariantPack, dry_run: bool = False
) -> List[Path]:
    """Copy fixtures/ to fixtures/variants/<variant>/ with token substitution.

    Returns the list of generated file paths. If ``dry_run`` is true, only the
    planned output paths are returned and no files are written.
    """
    src_root = REPO_ROOT / "fixtures"
    dst_root = src_root / "variants" / variant

    written: List[Path] = []
    for src in src_root.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(src_root)
        # Skip the variants tree itself (don't recursively regenerate).
        if rel.parts and rel.parts[0] == "variants":
            continue
        dst = dst_root / rel
        written.append(dst)
        if dry_run:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() == ".md":
            text = src.read_text(encoding="utf-8")
            dst.write_text(substitute_text(text, pack), encoding="utf-8")
        else:
            shutil.copy2(src, dst)
    return written


# -----------------------------------------------------------------------------
# Scenario rewriting
# -----------------------------------------------------------------------------

def _transform_workspace_files(
    wf: Dict[str, str], pack: VariantPack, variant: str
) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for fn, ref in wf.items():
        if isinstance(ref, str) and ref.startswith("@fixtures/"):
            out[fn] = _rewrite_fixture_ref(ref, variant)
        elif isinstance(ref, str):
            # Inline markdown content — substitute in place.
            out[fn] = substitute_text(ref, pack)
        else:
            out[fn] = ref
    return out


def _transform_rubric(rubric: dict, pack: VariantPack) -> dict:
    """Rewrite rubric keyword lists so name-tokens follow the substitution.

    We substitute each keyword string end-to-end. Keywords that don't mention
    a substituted token (like 'events', 'collision', 'merge conflict') are
    untouched.
    """
    out = dict(rubric)
    for key in ("must_mention", "should_mention", "red_flags"):
        vals = rubric.get(key)
        if isinstance(vals, list):
            out[key] = [substitute_text(v, pack) if isinstance(v, str) else v
                        for v in vals]
    return out


def transform_scenario(s: dict, pack: VariantPack, variant: str) -> dict:
    out = dict(s)
    # id, correct_answer, scoring, expected_tools — untouched on purpose.
    if isinstance(s.get("trigger"), str):
        out["trigger"] = substitute_text(s["trigger"], pack)
    if isinstance(s.get("name"), str):
        # Keep the snake_case name stable for cross-variant comparisons.
        out["name"] = s["name"]
    if isinstance(s.get("description"), str):
        out["description"] = substitute_text(s["description"], pack)
    if isinstance(s.get("workspace_files"), dict):
        out["workspace_files"] = _transform_workspace_files(
            s["workspace_files"], pack, variant
        )
    # Open-ended scenarios
    if isinstance(s.get("rubric"), dict):
        out["rubric"] = _transform_rubric(s["rubric"], pack)
    if isinstance(s.get("judge_prompt"), str):
        out["judge_prompt"] = substitute_text(s["judge_prompt"], pack)
    # Keyword-scored MCQ: correct_answer IS a keyword, so it must follow
    # substitution too (e.g. "alan" -> "maya" lowercased).
    if s.get("scoring") == "keyword" and isinstance(s.get("correct_answer"), str):
        out["correct_answer"] = substitute_text(s["correct_answer"], pack)
        # Also substitute lowercase tokens, which rubric/keyword matching uses.
        lowered_pack: VariantPack = [(o.lower(), n.lower()) for o, n in pack]
        out["correct_answer"] = substitute_text(
            out["correct_answer"], lowered_pack
        )
    return out


def transform_dataset(data: dict | list, pack: VariantPack, variant: str):
    """Transform a scenarios.json / open-ended.json payload."""
    if isinstance(data, dict) and "scenarios" in data:
        out = dict(data)
        out["scenarios"] = [
            transform_scenario(s, pack, variant) for s in data["scenarios"]
        ]
        if isinstance(out.get("description"), str):
            out["description"] = substitute_text(out["description"], pack)
        out["variant"] = variant
        return out
    if isinstance(data, list):
        return [transform_scenario(s, pack, variant) for s in data]
    raise ValueError("Unrecognized scenarios payload shape")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def _default_output(variant: str, source: Path) -> Path:
    """Default output path next to the source file with a .<variant>.json suffix."""
    stem = source.stem  # e.g. 'scenarios' or 'open-ended'
    return source.with_name(f"{stem}.{variant}.json")


def generate_variant(
    variant: str,
    pack: VariantPack,
    sources: Iterable[Path],
    output: Path | None,
    verify: bool,
) -> List[Path]:
    produced: List[Path] = []
    # Always regenerate the fixture tree for this variant.
    generate_variant_fixtures(variant, pack)

    for src in sources:
        if not src.exists():
            print(f"warn: source missing, skipping: {src}", file=sys.stderr)
            continue
        data = json.loads(src.read_text(encoding="utf-8"))
        transformed = transform_dataset(data, pack, variant)

        if output is not None and len(list(sources)) == 1:
            dst = output
        else:
            dst = _default_output(variant, src)
        dst.write_text(
            json.dumps(transformed, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        produced.append(dst)
        print(f"wrote {dst.relative_to(REPO_ROOT)}")

    if verify:
        rc = subprocess.call([
            sys.executable,
            str(REPO_ROOT / "tools" / "validate_schema.py"),
            "--repo-root",
            str(REPO_ROOT),
        ])
        if rc != 0:
            print(
                "warn: validate_schema.py reported issues (variants may "
                "reference the main scenarios.json which is still the "
                "baseline; re-run validation against a checkout where the "
                "variant file has replaced scenarios.json if needed).",
                file=sys.stderr,
            )
    return produced


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variant",
        required=True,
        help="Variant key (v2-neon, v3-helix, v4-orbit) or 'all'",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=REPO_ROOT / "scenarios" / "scenarios.json",
        help="Scenarios JSON to transform (default: scenarios/scenarios.json)",
    )
    parser.add_argument(
        "--also-open-ended",
        action="store_true",
        default=True,
        help="Also transform scenarios/open-ended.json (default: on)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (only respected when exactly one source is "
        "processed). Default: <source>.<variant>.json next to the source.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run tools/validate_schema.py after generation.",
    )
    args = parser.parse_args(argv)

    if args.variant == "all":
        variants = list(VARIANT_PACKS.keys())
    elif args.variant in VARIANT_PACKS:
        variants = [args.variant]
    else:
        print(
            f"unknown variant: {args.variant!r}. known: "
            f"{sorted(VARIANT_PACKS)} or 'all'",
            file=sys.stderr,
        )
        return 2

    sources: List[Path] = [args.source]
    if args.also_open_ended:
        oe = REPO_ROOT / "scenarios" / "open-ended.json"
        if oe.exists() and oe != args.source:
            sources.append(oe)

    for v in variants:
        generate_variant(
            variant=v,
            pack=VARIANT_PACKS[v],
            sources=sources,
            output=args.output if len(sources) == 1 else None,
            verify=args.verify,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
