#!/usr/bin/env python3
"""Rename Terraform JSON resource files with dot-free resource labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TF_JSON_SUFFIX = ".tf.json"
JSON_SUFFIX = ".json"


def sanitize_directory(
    directory: Path | str, *, dry_run: bool = False
) -> list[tuple[str, str]]:
    """Sanitize Terraform JSON resource file names in *directory*.

    Resource files are JSON files with a top-level Terraform ``resource`` block.
    For those files, dots in the resource-name part of the filename are replaced
    with underscores while preserving the ``.tf.json`` or ``.json`` suffix. All
    JSON Terraform configuration files in the same directory are then updated so
    resource labels, output names, and interpolation strings use the new labels.
    """
    root = Path(directory)
    documents = _load_documents(root)
    rename_targets = _build_rename_targets(documents)
    replacements = [
        (old_path.name[: -len(suffix)], new_path.name[: -len(suffix)])
        for old_path, new_path, suffix in rename_targets
    ]

    if not replacements:
        return []

    sorted_replacements = sorted(replacements, key=lambda item: len(item[0]), reverse=True)
    transformed: dict[Path, Any] = {}
    changed_paths: set[Path] = set()
    for path, document in documents.items():
        new_document, changed = _replace_in_json(document, sorted_replacements)
        transformed[path] = new_document
        if changed:
            changed_paths.add(path)

    if not dry_run:
        target_by_source = {
            source: target for source, target, _suffix in rename_targets
        }
        for path, document in transformed.items():
            target = target_by_source.get(path, path)
            if path in changed_paths or target != path:
                target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            if target != path:
                path.unlink()

    return replacements


def _load_documents(directory: Path) -> dict[Path, Any]:
    if not directory.is_dir():
        raise NotADirectoryError(directory)

    documents = {}
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.name.endswith(JSON_SUFFIX):
            documents[path] = json.loads(path.read_text(encoding="utf-8"))
    return documents


def _build_rename_targets(
    documents: dict[Path, Any]
) -> list[tuple[Path, Path, str]]:
    targets = []
    for path, document in documents.items():
        split_name = _split_terraform_json_name(path.name)
        if split_name is None or not _is_resource_file(document):
            continue

        resource_name, suffix = split_name
        sanitized_name = resource_name.replace(".", "_")
        if sanitized_name == resource_name:
            continue

        targets.append((path, path.with_name(f"{sanitized_name}{suffix}"), suffix))

    _validate_targets(documents, targets)
    return targets


def _split_terraform_json_name(filename: str) -> tuple[str, str] | None:
    if filename.endswith(TF_JSON_SUFFIX):
        return filename[: -len(TF_JSON_SUFFIX)], TF_JSON_SUFFIX
    if filename.endswith(JSON_SUFFIX):
        return filename[: -len(JSON_SUFFIX)], JSON_SUFFIX
    return None


def _is_resource_file(document: Any) -> bool:
    return isinstance(document, dict) and isinstance(document.get("resource"), dict)


def _validate_targets(
    documents: dict[Path, Any], targets: list[tuple[Path, Path, str]]
) -> None:
    seen_targets: dict[Path, Path] = {}
    sources = {source for source, _target, _suffix in targets}
    for source, target, _suffix in targets:
        if target in seen_targets:
            raise ValueError(
                f"multiple resource files would be renamed to {target.name}: "
                f"{seen_targets[target].name}, {source.name}"
            )
        seen_targets[target] = source

        if target.exists() and target not in sources:
            raise FileExistsError(
                f"cannot rename {source.name} to {target.name}: target already exists"
            )

        if target in documents and target not in sources:
            raise FileExistsError(
                f"cannot rename {source.name} to {target.name}: target is already loaded"
            )


def _replace_in_json(
    value: Any, replacements: list[tuple[str, str]]
) -> tuple[Any, bool]:
    if isinstance(value, dict):
        changed = False
        replaced: dict[str, Any] = {}
        for key, child in value.items():
            new_key = _replace_in_string(key, replacements)
            new_child, child_changed = _replace_in_json(child, replacements)

            if new_key in replaced:
                raise ValueError(f"JSON key collision after replacing {key!r}")

            replaced[new_key] = new_child
            changed = changed or new_key != key or child_changed
        return replaced, changed

    if isinstance(value, list):
        changed = False
        replaced_items = []
        for item in value:
            new_item, item_changed = _replace_in_json(item, replacements)
            replaced_items.append(new_item)
            changed = changed or item_changed
        return replaced_items, changed

    if isinstance(value, str):
        new_value = _replace_in_string(value, replacements)
        return new_value, new_value != value

    return value, False


def _replace_in_string(value: str, replacements: list[tuple[str, str]]) -> str:
    for old, new in replacements:
        value = value.replace(old, new)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rename Terraform JSON resource files so resource labels do not "
            "contain dots, and update same-directory JSON config references."
        )
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="directory containing Terraform JSON files (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show planned resource-name rewrites without modifying files",
    )
    args = parser.parse_args()

    renames = sanitize_directory(args.directory, dry_run=args.dry_run)
    if not renames:
        print("No Terraform JSON resource files needed sanitizing.")
        return 0

    prefix = "Would rename" if args.dry_run else "Renamed"
    for old, new in renames:
        print(f"{prefix}: {old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
