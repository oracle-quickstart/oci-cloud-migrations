#!/usr/bin/env python3
"""Render the public Agent Skills projection from the authored OCM pack."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "ocm-ai-tools"
OUTPUT = ROOT / ".agents" / "skills"

WORKFLOWS = {
    "migration-prereqs-validate": {
        "filename": "migration-prereqs-validate.md",
    },
    "migration-prereqs-onboard": {
        "filename": "migration-prereqs-onboard.md",
    },
}

WORKFLOW_REFERENCES = {
    "migration-prereqs-validate": (
        "oci-api-reference.md",
        "stack-resources.md",
        "stack-variables.md",
        "version-compatibility.md",
    ),
    "migration-prereqs-onboard": (
        "oci-api-reference.md",
        "rms-guide.md",
        "stack-resources.md",
        "stack-variables.md",
        "version-compatibility.md",
    ),
}


def _frontmatter_value(frontmatter: str, key: str) -> str:
    prefix = f"{key}:"
    for line in frontmatter.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    raise ValueError(f"missing {key!r} in workflow frontmatter")


def _render_workflow(name: str, source_path: Path) -> str:
    source = source_path.read_text(encoding="utf-8")
    if not source.startswith("---\n") or "\n---\n" not in source[4:]:
        raise ValueError(f"workflow has invalid frontmatter: {source_path}")

    frontmatter, body = source[4:].split("\n---\n", 1)
    owner = _frontmatter_value(frontmatter, "  owner")
    last_updated = _frontmatter_value(frontmatter, "  last_updated")
    metadata = (
        "metadata:\n"
        f"  owner: {owner}\n"
        f"  last_updated: {last_updated}\n"
        "  source_type: workflow\n"
        f"  source_path: ocm-ai-tools/workflows/{source_path.name}\n"
    )

    description = _frontmatter_value(frontmatter, "description")
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f"{metadata}"
        "---\n"
        + body
    )


def _build(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        SOURCE / "skills" / "migration-prereqs",
        destination / "migration-prereqs",
    )
    for name, details in WORKFLOWS.items():
        rendered = _render_workflow(
            name,
            SOURCE / "workflows" / details["filename"],
        )
        skill_dir = destination / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(rendered, encoding="utf-8")
        references = skill_dir / "references"
        references.mkdir()
        for reference_name in WORKFLOW_REFERENCES[name]:
            shutil.copy2(
                SOURCE / "skills" / "migration-prereqs" / "references" / reference_name,
                references / reference_name,
            )


def _files(root: Path) -> list[Path]:
    return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())


def _same_tree(left: Path, right: Path) -> bool:
    left_files = _files(left)
    right_files = _files(right)
    if left_files != right_files:
        return False
    return all(
        (left / path).read_bytes() == (right / path).read_bytes()
        for path in left_files
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that the checked-in projection matches the authored source",
    )
    args = parser.parse_args()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=OUTPUT.parent) as temporary:
        expected = Path(temporary) / "skills"
        _build(expected)
        if args.check:
            if not OUTPUT.exists() or not _same_tree(expected, OUTPUT):
                print(".agents/skills is out of date; run render_agent_skills.py", file=sys.stderr)
                return 1
            print(".agents/skills is current")
            return 0

        for name in ["migration-prereqs", *WORKFLOWS]:
            target = OUTPUT / name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(expected / name, target)
        print("Rendered .agents/skills from ocm-ai-tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
