#!/usr/bin/env python3
"""
Teardown Agent Discovery Links — removes symlinks created by setup_agent_links.py.

TLDR:
    Removes only discovery links that point back into this project: .claude/skills
    links, $CODEX_HOME/skills links, root instruction links, and GitHub Copilot
    link. Delegates MCP teardown to via's own `via uninstall mcp` command and
    removes Codex MCP config with `codex mcp remove via`.
    Real files, directories, unrelated symlinks, and Codex .system skills are
    left untouched. Supports --dry-run for auditing before removal.

"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_project_root() -> Path:
    """Find project root by looking for agents/ directory."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    if not (project_root / "agents").is_dir():
        print(f"Error: Could not find agents/ directory from {project_root}")
        sys.exit(1)

    return project_root


def get_codex_home() -> Path:
    """Return Codex home, honoring CODEX_HOME when set."""
    return Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()


def is_inside(path: Path, parent: Path) -> bool:
    """Return whether path resolves under parent."""
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def unlink_owned_symlink(link_path: Path, project_root: Path, dry_run: bool) -> bool:
    """Remove link_path only if it is a symlink pointing into project_root."""
    if not link_path.is_symlink():
        if link_path.exists():
            print(f"  ⚠️  Skipping {link_path} - exists and is not a symlink")
        return False

    target = link_path.resolve()
    if not is_inside(target, project_root):
        print(f"  ⚠️  Skipping {link_path} - points outside this project: {target}")
        return False

    if dry_run:
        print(f"  DRY-RUN remove {link_path} -> {target}")
        return True

    try:
        link_path.unlink()
    except OSError as exc:
        print(f"  ⚠️  Could not remove {link_path}: {exc}")
        return False

    print(f"  ✅ Removed {link_path}")
    return True


def remove_empty_dir(path: Path, dry_run: bool) -> bool:
    """Remove path when it exists and is empty."""
    if not path.is_dir() or any(path.iterdir()):
        return False

    if dry_run:
        print(f"  DRY-RUN remove empty dir {path}")
        return True

    try:
        path.rmdir()
    except OSError as exc:
        print(f"  ⚠️  Could not remove empty dir {path}: {exc}")
        return False

    print(f"  ✅ Removed empty dir {path}")
    return True


def remove_skill_links(skills_dir: Path, project_root: Path, label: str, dry_run: bool) -> int:
    """Remove symlinked skills in skills_dir that point into this project."""
    print(f"\n📁 Tearing down {label} ({skills_dir})...")

    if not skills_dir.exists():
        print("  Nothing to remove")
        return 0

    count = 0
    for link_path in sorted(skills_dir.iterdir()):
        if link_path.name == ".system":
            continue
        if unlink_owned_symlink(link_path, project_root, dry_run):
            count += 1

    remove_empty_dir(skills_dir, dry_run)
    return count


def remove_root_symlinks(project_root: Path, dry_run: bool) -> int:
    """Remove root instruction symlinks that point into this project."""
    print("\n📁 Tearing down root symlinks...")

    count = 0
    for link_name in ("AGENTS.md", "GEMINI.md", ".cursorrules", "CHATGPT.md"):
        if unlink_owned_symlink(project_root / link_name, project_root, dry_run):
            count += 1

    copilot_link = project_root / ".github" / "copilot-instructions.md"
    if unlink_owned_symlink(copilot_link, project_root, dry_run):
        count += 1

    github_dir = project_root / ".github"
    remove_empty_dir(github_dir, dry_run)
    return count


def uninstall_via_mcp(project_root: Path, dry_run: bool) -> bool:
    """Delegate MCP teardown to via's uninstaller."""
    print("\n📡 Uninstalling via MCP integration...")

    if not shutil.which("via"):
        print("  ⚠️  via not found on PATH — skipping MCP teardown")
        return False

    if dry_run:
        print("  DRY-RUN run via uninstall mcp")
        return True

    result = subprocess.run(
        ["via", "uninstall", "mcp"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ❌ via uninstall mcp failed: {result.stderr.strip()}")
        return False

    print(f"  ✅ via uninstall mcp ({result.stdout.strip() or 'done'})")
    return True


def uninstall_codex_via_mcp(project_root: Path, dry_run: bool) -> bool:
    """Remove the via MCP stdio server from Codex."""
    print("\n📡 Uninstalling Codex via MCP integration...")

    codex_bin = shutil.which("codex")
    if not codex_bin:
        print("  ⚠️  codex not found on PATH — skipping Codex MCP teardown")
        return False

    existing = subprocess.run(
        [codex_bin, "mcp", "get", "via"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if existing.returncode != 0:
        print("  Nothing to remove")
        return False

    if dry_run:
        print("  DRY-RUN run codex mcp remove via")
        return True

    result = subprocess.run(
        [codex_bin, "mcp", "remove", "via"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ❌ codex mcp remove via failed: {result.stderr.strip()}")
        return False

    print(f"  ✅ codex mcp remove via ({result.stdout.strip() or 'done'})")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove symlinks created by setup_agent_links.py")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be removed without deleting anything")
    parser.add_argument("--keep-mcp", action="store_true", help="Skip via MCP uninstall")
    return parser.parse_args()


def main():
    args = parse_args()

    print("🧹 Agent Discovery Links Teardown")
    print("=" * 40)

    project_root = find_project_root()
    print(f"\nProject root: {project_root}")

    total = 0
    total += remove_skill_links(project_root / ".claude" / "skills", project_root, "Claude Skills", args.dry_run)
    total += remove_skill_links(get_codex_home() / "skills", project_root, "Codex Skills", args.dry_run)
    total += remove_root_symlinks(project_root, args.dry_run)

    if not args.keep_mcp:
        if uninstall_via_mcp(project_root, args.dry_run):
            total += 1
        if uninstall_codex_via_mcp(project_root, args.dry_run):
            total += 1

    action = "Would remove" if args.dry_run else "Removed"
    print(f"\n✅ Done. {action} {total} generated link/config item(s).")
    if not args.dry_run:
        print("Restart Codex or other AI tools so they stop using removed discovery links.")


if __name__ == "__main__":
    main()
