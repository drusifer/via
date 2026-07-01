import os
import re
import shutil

workspace_dir = "/home/drusifer/Projects/via"
sprints_dir = os.path.join(workspace_dir, "docs", "sprints")

# Create docs/sprints directory if it doesn't exist
os.makedirs(sprints_dir, exist_ok=True)

# Regex to capture sprint numbers from filenames
pattern = re.compile(r'sprint_?(\d+)', re.IGNORECASE)

# Group files by sprint number
sprint_files = {}

for root, dirs, files in os.walk(workspace_dir):
    # Skip virtual environments, git, cache, node_modules etc
    if any(p in root for p in [".venv", ".git", ".pytest_cache", ".ruff_cache", "node_modules", "build"]):
        continue
    for file in files:
        if file.endswith(".md"):
            # Avoid self-matching already consolidated files under docs/sprints/
            if "docs/sprints" in root or "docs/sprints" in os.path.join(root, file):
                continue
            match = pattern.search(file)
            if match:
                sprint_num = int(match.group(1))
                full_path = os.path.join(root, file)
                if sprint_num not in sprint_files:
                    sprint_files[sprint_num] = []
                sprint_files[sprint_num].append(full_path)

def get_file_priority(file_path):
    lower_path = file_path.lower()
    if "cypher.docs" in lower_path:
        return 1
    elif "morpheus.docs" in lower_path:
        return 2
    elif "smith.docs" in lower_path:
        return 3
    elif "mouse.docs" in lower_path:
        return 4
    elif "neo.docs" in lower_path:
        return 5
    elif "trin.docs" in lower_path:
        return 6
    return 7

# Process each sprint
for sprint_num, files in sorted(sprint_files.items()):
    # Sort files based on role priority, then filename
    sorted_files = sorted(files, key=lambda f: (get_file_priority(f), os.path.basename(f)))
    
    consolidated_content = [
        f"# Sprint {sprint_num} Consolidated Documentation\n",
        f"This document consolidates all documentation for Sprint {sprint_num}.\n",
        "## Table of Contents\n"
    ]
    
    # Generate Table of Contents
    for f in sorted_files:
        rel_path = os.path.relpath(f, workspace_dir)
        filename = os.path.basename(f)
        anchor = filename.lower().replace('.', '').replace('_', '-').replace(' ', '-')
        consolidated_content.append(f"- [{filename}](#{anchor}) (originally `{rel_path}`)\n")
    
    consolidated_content.append("\n---\n")
    
    # Append content of each file
    for f in sorted_files:
        rel_path = os.path.relpath(f, workspace_dir)
        filename = os.path.basename(f)
        
        consolidated_content.append(f"\n## {filename}\n")
        consolidated_content.append(f"**Original Location**: `{rel_path}`\n\n")
        
        try:
            with open(f, 'r', encoding='utf-8') as src_file:
                content = src_file.read()
                # To prevent title collisions, demote headers in the appended content if necessary
                # E.g. convert # Header -> ### Header
                adjusted_lines = []
                for line in content.splitlines():
                    if line.startswith("#"):
                        # Demote # headers to ### to fit nicely under ## filename
                        adjusted_lines.append("#" + line)
                    else:
                        adjusted_lines.append(line)
                consolidated_content.append("\n".join(adjusted_lines) + "\n")
        except Exception as e:
            consolidated_content.append(f"*Error reading file:* {str(e)}\n")
        
        consolidated_content.append("\n---\n")
        
    # Write the consolidated file
    dest_path = os.path.join(sprints_dir, f"sprint_{sprint_num}.md")
    with open(dest_path, 'w', encoding='utf-8') as dest_file:
        dest_file.write("\n".join(consolidated_content))
    print(f"Created: {os.path.relpath(dest_path, workspace_dir)} from {len(files)} files.")
    
    # Remove original files
    for f in sorted_files:
        try:
            os.remove(f)
            # print(f"  Removed: {os.path.relpath(f, workspace_dir)}")
        except Exception as e:
            print(f"  Error removing {os.path.relpath(f, workspace_dir)}: {str(e)}")

print("Consolidation complete.")
