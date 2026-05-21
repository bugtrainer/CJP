import os

git_path = r"c:\Users\raham\Desktop\AntiGravity\CJP\.git"
found = False
for root, dirs, files in os.walk(git_path):
    for f in files:
        full_path = os.path.join(root, f)
        try:
            with open(full_path, 'rb') as file:
                content = file.read()
                # Check for railway, up.railway, onrender, cjphub
                matches = []
                for term in [b'railway', b'onrender', b'cjphub']:
                    if term in content:
                        matches.append(term)
                if matches:
                    print(f"Match in {os.path.relpath(full_path, git_path)}: {matches}")
                    found = True
        except Exception:
            pass

if not found:
    print("No matches in .git directory.")
