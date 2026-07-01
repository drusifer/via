import os
import re
from collections import defaultdict

workspace_dir = "/home/drusifer/Projects/via"
sprint_files = defaultdict(list)

# Regex to capture sprint numbers from filenames
pattern = re.compile(r'sprint_?(\d+)', re.IGNORECASE)

for root, dirs, files in os.walk(workspace_dir):
    # Skip virtual environments, git, cache, node_modules etc
    if any(p in root for p in [".venv", ".git", ".pytest_cache", ".ruff_cache", "node_modules", "build"]):
        continue
    for file in files:
        if file.endswith(".md"):
            match = pattern.search(file)
            if match:
                sprint_num = int(match.group(1))
                full_path = os.path.join(root, file)
                sprint_files[sprint_num].append(full_path)

# Let's also print them sorted by sprint number
for sprint in sorted(sprint_files.keys()):
    print(f"\n--- Sprint {sprint} (Count: {len(sprint_files[sprint])}) ---")
    for f in sorted(sprint_files[sprint]):
        print(f"  {os.path.relpath(f, workspace_dir)}")
