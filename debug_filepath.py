import os
from pathvalidate import sanitize_filepath

name = "[:SITD:] - Puls:Schlag"
sanitized = sanitize_filepath(name)
print(f"Original: '{name}'")
print(f"Sanitized: '{sanitized}'")

path = os.path.join("Downloads", sanitized)
print(f"Joined: '{path}'")

try:
    os.makedirs(path, exist_ok=True)
    print("Makedirs success")
    os.rmdir(path)
except Exception as e:
    print(f"Makedirs failed: {e}")

# Check what happens if we join with something that looks like an absolute path but isn't
weird_path = "[:/Something"
print(f"Weird path: '{weird_path}'")
try:
    os.makedirs(weird_path)
except Exception as e:
    print(f"Weird makedirs failed: {e}")
