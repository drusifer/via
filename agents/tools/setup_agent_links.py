#!/usr/bin/env python3
"""
Setup Agent Discovery Links

Creates symlinks for agent discovery across different AI platforms:
- Claude: .claude/skills/<name>/ -> agents/<name>.docs/
- OpenAI/Codex/Cursor: AGENTS.md -> agents/AGENTS.md
- Gemini: GEMINI.md -> agents/AGENTS.md

Run from project root:
    python agents/tools/setup_agent_links.py

Or make executable:
    chmod +x agents/tools/setup_agent_links.py
    ./agents/tools/setup_agent_links.py
"""

import os
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
            link_path.unlink()
        else:
            print(f"  ⚠️  Skipping {link_path} - exists and is not a symlink")
            return False

    if relative:
        # Calculate relative path from link location to target
        target = os.path.relpath(target_path, link_path.parent)
    else:
        target = target_path

    link_path.symlink_to(target)
    return True


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
    total += setup_root_symlinks(project_root, agents_dir)

    print(f"\n✅ Done! Created {total} symlinks.")
    print("\nAgent discovery is now enabled for:")
    print("  • Claude Code (.claude/skills/)")
    print("  • OpenAI Codex, Cursor, Copilot (AGENTS.md)")
    print("  • Gemini CLI (GEMINI.md)")


if __name__ == "__main__":
    main()
