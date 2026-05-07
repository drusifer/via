#!/usr/bin/env python3
"""
Setup Agent Discovery Links — creates symlinks so AI tools can find agent personas.

TLDR:
    Scans agents/*.docs/ directories for persona folders (identified by the
    presence of SKILL.md) and creates the platform-specific symlinks each AI
    tool expects: .claude/skills/<name>/ for Claude Code, $CODEX_HOME/skills/<name>/
    for Codex, AGENTS.md / GEMINI.md / .cursorrules / CHATGPT.md /
    .github/copilot-instructions.md at the project root for other tools.
    Key functions: find_project_root() locates the repo root; find_persona_folders()
    discovers persona dirs; find_shared_skills() finds agents/skills/*/;
    setup_claude_skills() builds the .claude/skills/ tree; setup_codex_skills()
    builds the Codex skill links; setup_root_symlinks() creates root-level links;
    install_via_mcp() writes generic via MCP config; install_codex_via_mcp()
    registers the same server with Codex using `codex mcp add`;
    check_yaml_frontmatter() warns about missing
    SKILL.md frontmatter; create_symlink() safely creates/replaces a symlink.
    Role in the system: a one-time setup script run from the project root; depends
    on agents/*.docs/SKILL.md files existing and produces the discovery artifacts
    consumed by Claude Code, OpenAI Codex, Cursor, Gemini CLI, and GitHub Copilot.

"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_project_root() -> Path:
    """Find project root by looking for agents/ directory."""
    script_dir = Path(__file__).resolve().parent
    # Script is in agents/tools/, so go up two levels
    project_root = script_dir.parent.parent

    if not (project_root / "agents").is_dir():
        print(f"Error: Could not find agents/ directory from {project_root}")
        sys.exit(1)

    return project_root


def find_persona_folders(agents_dir: Path) -> list[tuple[str, Path]]:
    """Find all persona folders (*.docs directories with SKILL.md files)."""
    personas = []

    for item in agents_dir.iterdir():
        if item.is_dir() and item.name.endswith(".docs"):
            # Look for SKILL.md file
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                persona_name = item.name.replace(".docs", "")
                personas.append((persona_name, item))

    return personas


def find_shared_skills(agents_dir: Path) -> list[tuple[str, Path]]:
    """Find shared skills in agents/skills/ directory."""
    skills = []
    skills_dir = agents_dir / "skills"

    if not skills_dir.is_dir():
        return skills

    for item in skills_dir.iterdir():
        if item.is_dir():
            skill_file = item / "SKILL.md"
            if skill_file.exists():
                skills.append((item.name, item))

    return skills


def create_symlink(link_path: Path, target_path: Path, relative: bool = True) -> bool:
    """Create a symlink, removing existing one if present."""
    if link_path.exists() or link_path.is_symlink():
        if link_path.is_symlink():
            existing_target = link_path.resolve()
            if existing_target == target_path.resolve():
                return False
            try:
                link_path.unlink()
            except OSError as exc:
                print(f"  ⚠️  Skipping {link_path} - could not remove symlink: {exc}")
                return False
        else:
            print(f"  ⚠️  Skipping {link_path} - exists and is not a symlink")
            return False

    if relative:
        # Calculate relative path from link location to target
        target = os.path.relpath(target_path, link_path.parent)
    else:
        target = target_path

    try:
        link_path.symlink_to(target)
    except OSError as exc:
        print(f"  ⚠️  Skipping {link_path} - could not create symlink: {exc}")
        return False

    return True


def get_codex_home() -> Path:
    """Return Codex home, honoring CODEX_HOME when set."""
    return Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()


def setup_claude_skills(project_root: Path, personas: list, shared_skills: list) -> int:
    """Create .claude/skills/ structure with symlinks to persona and shared skill folders."""
    print("\n📁 Setting up Claude Skills (.claude/skills/)...")

    skills_dir = project_root / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    count = 0

    # Persona skills (agents/*.docs/)
    for persona_name, persona_dir in personas:
        # Create symlink: .claude/skills/<name>/ -> agents/<name>.docs/
        skill_link = skills_dir / persona_name
        if create_symlink(skill_link, persona_dir):
            print(f"  ✅ {skill_link.relative_to(project_root)} -> {persona_dir.relative_to(project_root)}")
            count += 1
        else:
            # Already linked
            pass

    # Shared skills (agents/skills/*/)
    for skill_name, skill_dir in shared_skills:
        skill_link = skills_dir / skill_name
        if create_symlink(skill_link, skill_dir):
            print(f"  ✅ {skill_link.relative_to(project_root)} -> {skill_dir.relative_to(project_root)}")
            count += 1

    return count


def setup_codex_skills(project_root: Path, personas: list, shared_skills: list) -> int:
    """Create $CODEX_HOME/skills/ links so Codex loads project skills on startup."""
    codex_home = get_codex_home()
    skills_dir = codex_home / "skills"

    print(f"\n📁 Setting up Codex Skills ({skills_dir})...")

    try:
        skills_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"  ⚠️  Could not create {skills_dir}: {exc}")
        print("     Set CODEX_HOME to a writable Codex home and re-run this script.")
        return 0

    count = 0

    for persona_name, persona_dir in personas:
        skill_link = skills_dir / persona_name
        if create_symlink(skill_link, persona_dir):
            print(f"  ✅ {skill_link} -> {persona_dir.relative_to(project_root)}")
            count += 1

    for skill_name, skill_dir in shared_skills:
        skill_link = skills_dir / skill_name
        if create_symlink(skill_link, skill_dir):
            print(f"  ✅ {skill_link} -> {skill_dir.relative_to(project_root)}")
            count += 1

    print("  ℹ️  Existing Codex system skills in .system/ were left untouched")
    return count


def setup_root_symlinks(project_root: Path, agents_dir: Path) -> int:
    """Create discovery symlinks at project root for various AI tools."""
    print("\n📁 Setting up root symlinks...")

    agents_md = agents_dir / "AGENTS.md"
    if not agents_md.exists():
        print(f"  ⚠️  {agents_md} not found - skipping root symlinks")
        print(f"      Create agents/AGENTS.md first with project instructions")
        return 0

    count = 0
    links = [
        ("AGENTS.md", "OpenAI/Codex/Standard"),
        ("GEMINI.md", "Gemini CLI"),
        (".cursorrules", "Cursor AI"),
        ("CHATGPT.md", "ChatGPT Projects (Copy-Paste)"),
    ]

    for link_name, tool_name in links:
        link = project_root / link_name
        if create_symlink(link, agents_md):
            print(f"  ✅ {link_name} -> agents/AGENTS.md ({tool_name})")
            count += 1

    # GitHub Copilot (specific directory)
    github_dir = project_root / ".github"
    github_dir.mkdir(exist_ok=True)
    copilot_link = github_dir / "copilot-instructions.md"
    if create_symlink(copilot_link, agents_md):
        print(f"  ✅ .github/copilot-instructions.md -> agents/AGENTS.md (GitHub Copilot)")
        count += 1

    return count


def install_via_mcp(project_root: Path) -> bool:
    """Delegate MCP setup to via's installer."""
    print("\n📡 Installing via MCP integration...")

    if not shutil.which("via"):
        print("  ⚠️  via not found on PATH — skipping MCP setup")
        print("     Install via and re-run: pip install via")
        return False

    import subprocess
    result = subprocess.run(
        ["via", "install", "mcp"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ❌ via install mcp failed: {result.stderr.strip()}")
        return False

    print(f"  ✅ via install mcp ({result.stdout.strip() or 'done'})")
    return configure_project_via_mcp(project_root)


def configure_project_via_mcp(project_root: Path) -> bool:
    """Harden project .mcp.json so via MCP works in sandboxed clients."""
    mcp_json = project_root / ".mcp.json"
    try:
        data = json.loads(mcp_json.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  ⚠️  Could not read {mcp_json}: {exc}")
        return False

    via_entry = data.setdefault("mcpServers", {}).setdefault("via", {})
    args = list(via_entry.get("args", []))
    if "serve" in args and "--no-web" not in args:
        serve_index = args.index("serve")
        args.insert(serve_index + 1, "--no-web")
    via_entry["args"] = args

    env = dict(via_entry.get("env", {}))
    env["HOME"] = str(project_root)
    via_entry["env"] = env

    try:
        mcp_json.write_text(json.dumps(data, indent=2) + "\n")
    except OSError as exc:
        print(f"  ⚠️  Could not update {mcp_json}: {exc}")
        return False

    print("  ✅ Hardened .mcp.json for sandboxed via MCP startup")
    return True


def ensure_via_index(project_root: Path) -> bool:
    """Create the via index required by the MCP server when it is missing."""
    print("\n📇 Checking via index...")

    index_db = project_root / ".via" / "index.db"
    if index_db.exists():
        print("  ℹ️  via index already exists")
        return True

    via_bin = shutil.which("via")
    if not via_bin:
        print("  ⚠️  via not found on PATH — cannot create via index")
        return False

    result = subprocess.run(
        [via_bin, "index", str(project_root)],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ❌ via index failed: {result.stderr.strip()}")
        return False

    print(f"  ✅ via index ({result.stdout.strip() or 'done'})")
    return True


def install_codex_via_mcp(project_root: Path) -> bool:
    """Register the via MCP stdio server with Codex."""
    print("\n📡 Installing Codex via MCP integration...")

    codex_bin = shutil.which("codex")
    if not codex_bin:
        print("  ⚠️  codex not found on PATH — skipping Codex MCP setup")
        return False

    via_bin = shutil.which("via")
    if not via_bin:
        print("  ⚠️  via not found on PATH — skipping Codex MCP setup")
        print("     Install via and re-run: pip install via")
        return False

    expected_args = ["mcp", "serve", "--no-web", str(project_root)]
    expected_env = f"HOME={project_root}"

    def add_server() -> bool:
        result = subprocess.run(
            [
                codex_bin,
                "mcp",
                "add",
                "via",
                "--env",
                expected_env,
                "--",
                via_bin,
                *expected_args,
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  ❌ codex mcp add via failed: {result.stderr.strip()}")
            print("     Manual fallback:")
            print(f"     codex mcp add via --env {expected_env} -- {via_bin} {' '.join(expected_args)}")
            return False

        print(f"  ✅ codex mcp add via ({result.stdout.strip() or 'done'})")
        return True

    existing = subprocess.run(
        [codex_bin, "mcp", "get", "via"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if existing.returncode != 0:
        return add_server()

    existing_config = existing.stdout
    if (
        f"command: {via_bin}" in existing_config
        and f"args: {' '.join(expected_args)}" in existing_config
        and expected_env in existing_config
    ):
        print("  ℹ️  Codex MCP server 'via' already points at this project")
        return True

    print("  ℹ️  Replacing existing Codex MCP server 'via' with this project")
    remove = subprocess.run(
        [
            codex_bin,
            "mcp",
            "remove",
            "via",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if remove.returncode != 0:
        print(f"  ❌ codex mcp remove via failed: {remove.stderr.strip()}")
        return False

    return add_server()


def setup_project_capabilities(project_root: Path, via_enabled: bool) -> bool:
    """Create agents/PROJECT.md if missing so personas know available tools."""
    project_file = project_root / "agents" / "PROJECT.md"
    print("\n📁 Setting up project capability declarations...")

    if project_file.exists():
        print("  ℹ️  agents/PROJECT.md already exists; leaving it unchanged")
        return False

    via_state = "enabled" if via_enabled else "disabled"
    content = f"""---
# PROJECT.md — Project Capability Declarations
#
# Generated by agents/tools/setup_agent_links.py.
# All personas read this file on cold start to adapt their workflow to available tools.
---

# Project: {project_root.name}

## Description
BobProtocol-enabled project.

## Capabilities

### via
```
via: {via_state}
```
- When `enabled`: all personas use `via` for code navigation before falling back to Grep/Glob/Read.
- When `disabled`: personas use standard file and shell tools.

## Project Standards
Follow the repository instructions in `AGENTS.md` and persona state files.

## Key Artifacts
- `agents/CHAT.md` — Team communication log
- `agents/AGENTS.md` — Shared agent instructions
- `agents/*.docs/` — Persona state and instructions

## Notes
Update this file when project capabilities change.
"""

    try:
        project_file.write_text(content)
    except OSError as exc:
        print(f"  ⚠️  Could not create {project_file}: {exc}")
        return False

    print(f"  ✅ Created agents/PROJECT.md with via: {via_state}")
    return True


def check_yaml_frontmatter(personas: list) -> list[str]:
    """Check which persona files are missing YAML frontmatter."""
    missing = []

    for persona_name, persona_dir in personas:
        skill_md = persona_dir / "SKILL.md"
        content = skill_md.read_text()
        if not content.startswith("---"):
            missing.append(str(skill_md))

    return missing


def main():
    print("🔧 Agent Discovery Links Setup")
    print("=" * 40)

    # Find project root
    project_root = find_project_root()
    agents_dir = project_root / "agents"
    print(f"\nProject root: {project_root}")
    print(f"Agents dir: {agents_dir}")

    # Find persona folders
    personas = find_persona_folders(agents_dir)
    if not personas:
        print("\n❌ No persona folders found!")
        print("   Expected: agents/<name>.docs/SKILL.md")
        sys.exit(1)

    print(f"\nFound {len(personas)} personas:")
    for name, _ in personas:
        print(f"  • {name}")

    # Find shared skills
    shared_skills = find_shared_skills(agents_dir)
    if shared_skills:
        print(f"\nFound {len(shared_skills)} shared skills:")
        for name, skill_dir in shared_skills:
            print(f"  • {name}: {skill_dir.relative_to(agents_dir)}/SKILL.md")

    # Check for YAML frontmatter
    missing_frontmatter = check_yaml_frontmatter(personas)
    if missing_frontmatter:
        print("\n⚠️  Missing YAML frontmatter (recommended for Skills):")
        for f in missing_frontmatter:
            print(f"   • {f}")
        print("\n   Add frontmatter like:")
        print("   ---")
        print("   name: persona-name")
        print("   description: When to use this agent...")
        print("   ---")

    # Create symlinks
    total = 0
    total += setup_claude_skills(project_root, personas, shared_skills)
    total += setup_codex_skills(project_root, personas, shared_skills)
    total += setup_root_symlinks(project_root, agents_dir)

    # Delegate generic MCP setup to via, then register the server with Codex.
    via_index_ok = ensure_via_index(project_root)
    via_ok = install_via_mcp(project_root)
    codex_via_ok = install_codex_via_mcp(project_root)
    project_md_ok = setup_project_capabilities(project_root, via_index_ok and (via_ok or codex_via_ok))

    print(f"\n✅ Done! Created {total} symlinks.")
    print("\nAgent discovery is now enabled for:")
    print("  • Claude Code (.claude/skills/)")
    print(f"  • OpenAI Codex ({get_codex_home() / 'skills'}/ and AGENTS.md)")
    print("  • Cursor, Copilot (AGENTS.md)")
    print("  • Gemini CLI (GEMINI.md)")
    if via_index_ok:
        print("  • via index (.via/index.db)")
    if via_ok:
        print("  • via MCP server (via install mcp)")
    if codex_via_ok:
        print(f"  • Codex via MCP server ({get_codex_home() / 'config.toml'})")
    if project_md_ok:
        print("  • Project capabilities (agents/PROJECT.md)")


if __name__ == "__main__":
    main()
