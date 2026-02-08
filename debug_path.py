import os
from pathvalidate import sanitize_filename

name = "[:SITD:]"
sanitized = sanitize_filename(name)
print(f"Original: '{name}'")
print(f"Sanitized: '{sanitized}'")

try:
    os.makedirs(sanitized, exist_ok=True)
    print("Makedirs success")
    os.rmdir(sanitized)
except Exception as e:
    print(f"Makedirs failed: {e}")

path_with_folder = os.path.join("Downloads", sanitized)
print(f"Joined path: '{path_with_folder}'")
