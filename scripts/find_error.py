import os

target = "del processor"
target2 = "image"

print("Searching for files containing both 'del processor' and 'image'...")
for root, dirs, files in os.walk("."):
    if "venv" in root: continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if target in content and target2 in content:
                        print(f"FOUND MATCH: {path}")
            except Exception as e:
                print(f"Error reading {path}: {e}")
