#!/usr/bin/env python3
"""Sync local skills into project/global .agents directories for development.

Default behavior uses links (Windows junctions on Windows, symlink on others)
so edits in ./skills are reflected immediately.
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

DEFAULT_SKILL_DIR_NAMES = [".agents", ".agent", ".trae"]


def is_reparse_point(path: Path) -> bool:
    """Return True if the path is a Windows reparse point (junction/symlink)."""
    if os.name != "nt" or not path.exists():
        return False
    try:
        attrs = os.lstat(path).st_file_attributes
        return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, OSError):
        return False


def remove_path(path: Path) -> None:
    """Remove file/dir/symlink/junction without touching unrelated paths."""
    if not path.exists() and not path.is_symlink():
        return

    if path.is_symlink():
        path.unlink()
        return

    if is_reparse_point(path):
        # Junction: remove link itself, not target contents.
        os.rmdir(path)
        return

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def ensure_link(source: Path, target: Path, force: bool) -> None:
    """Create a directory link from target -> source."""
    if target.exists() or target.is_symlink():
        same_target = False
        if target.is_symlink():
            try:
                same_target = target.resolve() == source.resolve()
            except OSError:
                same_target = False
        if same_target:
            print(f"[skip] already linked: {target}")
            return
        if not force:
            print(f"[warn] target exists, skip (use --force to replace): {target}")
            return
        remove_path(target)

    target.parent.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        # Use junction to avoid admin/dev-mode requirements for symlink.
        cmd = ["cmd", "/c", "mklink", "/J", str(target), str(source)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            msg = stderr or stdout or "mklink failed"
            raise RuntimeError(msg)
    else:
        os.symlink(source, target, target_is_directory=True)

    print(f"[ok] linked: {target} -> {source}")


def ensure_copy(source: Path, target: Path, force: bool) -> None:
    """Copy source directory to target directory."""
    if target.exists() or target.is_symlink():
        if not force:
            print(f"[warn] target exists, skip (use --force to replace): {target}")
            return
        remove_path(target)

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    print(f"[ok] copied: {source} -> {target}")


def iter_skill_dirs(skills_root: Path) -> list[Path]:
    if not skills_root.exists() or not skills_root.is_dir():
        raise FileNotFoundError(f"skills directory not found: {skills_root}")
    skill_dirs = [p for p in skills_root.iterdir() if p.is_dir()]
    if not skill_dirs:
        raise RuntimeError(f"no skill directories found under: {skills_root}")
    return sorted(skill_dirs)


def sync_target(skills_root: Path, target_root: Path, mode: str, force: bool) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    for skill_dir in iter_skill_dirs(skills_root):
        target = target_root / skill_dir.name
        if mode == "link":
            ensure_link(skill_dir.resolve(), target, force)
        else:
            ensure_copy(skill_dir.resolve(), target, force)


def parse_dir_names(raw: str) -> list[str]:
    names = [part.strip() for part in raw.split(",") if part.strip()]
    if not names:
        return DEFAULT_SKILL_DIR_NAMES.copy()
    return names


def expand_target_roots(seed_target: Path, dir_names: list[str]) -> list[Path]:
    # Expected seed: <scope_root>/.agents/skills
    scope_root = seed_target.parent.parent if seed_target.name == "skills" else seed_target.parent
    expanded = [scope_root / dir_name / "skills" for dir_name in dir_names]

    deduped = []
    seen = set()
    for path in expanded:
        normalized = str(path.resolve(strict=False)).lower() if os.name == "nt" else str(path.resolve(strict=False))
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(path)
    return deduped


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent.parent
    default_source = repo_root / "skills"
    default_project_agents = repo_root / ".agents" / "skills"
    default_global_agents = Path.home() / ".agents" / "skills"

    parser = argparse.ArgumentParser(
        description=(
            "Sync local skills to project/global skill dirs for development "
            "(default dirs: .agents,.agent,.trae)."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=default_source,
        help=f"Source skills directory (default: {default_source})",
    )
    parser.add_argument(
        "--project-target",
        type=Path,
        default=default_project_agents,
        help=f"Project .agents skills dir (default: {default_project_agents})",
    )
    parser.add_argument(
        "--global-target",
        type=Path,
        default=default_global_agents,
        help=f"Global .agents skills dir (default: {default_global_agents})",
    )
    parser.add_argument(
        "--target-dirs",
        default=",".join(DEFAULT_SKILL_DIR_NAMES),
        help=(
            "Comma-separated directory names under scope root to sync skills into "
            "(default: .agents,.agent,.trae)."
        ),
    )
    parser.add_argument(
        "--scope",
        choices=["project", "global", "all"],
        default="all",
        help="Sync target scope.",
    )
    parser.add_argument(
        "--mode",
        choices=["link", "copy"],
        default="link",
        help="Use links (recommended) or copy files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing target directories with managed links/copies.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    dir_names = parse_dir_names(args.target_dirs)

    targets = []
    if args.scope in ("project", "all"):
        for target in expand_target_roots(args.project_target.resolve(), dir_names):
            targets.append(("project", target))
    if args.scope in ("global", "all"):
        for target in expand_target_roots(args.global_target.resolve(), dir_names):
            targets.append(("global", target))

    print(f"Source: {source}")
    print(f"Mode: {args.mode}")
    print(f"Force: {args.force}")
    print(f"Target dirs: {','.join(dir_names)}")

    try:
        for name, target_root in targets:
            print(f"\n==> Sync to {name}: {target_root}")
            sync_target(source, target_root, args.mode, args.force)
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
