import os

workspace_dir = "/home/drusifer/Projects/via"
via_dir = os.path.join(workspace_dir, "via")

missing_py = []
for root, dirs, files in os.walk(via_dir):
    for file in files:
        if file.endswith(".py"):
            full_path = os.path.join(root, file)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if "TLDR:" not in content:
                missing_py.append(os.path.relpath(full_path, workspace_dir))

print("Missing Py Files:")
for f in sorted(missing_py):
    print(f"  {f}")
