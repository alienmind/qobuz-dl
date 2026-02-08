import os
import shutil

# Directory to scan
ROOT_DIR = "Qobuz Downloads"


def flatten_downloads(root_dir):
    if not os.path.isdir(root_dir):
        print(f"Directory '{root_dir}' does not exist.")
        return

    # Iterate over items in the root directory (playlists or artists)
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path):
            print(f"Processing directory: {item}")

            # Iterate over sub-items (potential album folders)
            sub_items = os.listdir(item_path)
            for sub_item in sub_items:
                sub_item_path = os.path.join(item_path, sub_item)

                # If it's a directory, move its contents up
                if os.path.isdir(sub_item_path):
                    print(f"  Flattening sub-directory: {sub_item}")
                    for file in os.listdir(sub_item_path):
                        src = os.path.join(sub_item_path, file)
                        dst = os.path.join(item_path, file)

                        # Handle collisions
                        if os.path.exists(dst):
                            base, ext = os.path.splitext(file)
                            counter = 1
                            while os.path.exists(dst):
                                dst = os.path.join(item_path, f"{base}_{counter}{ext}")
                                counter += 1

                        try:
                            shutil.move(src, dst)
                            print(f"    Moved: {file} -> {os.path.basename(dst)}")
                        except Exception as e:
                            print(f"    Error moving {file}: {e}")

                    # Remove empty directory
                    if not os.listdir(sub_item_path):
                        os.rmdir(sub_item_path)
                        print(f"  Removed empty directory: {sub_item}")
                    else:
                        print(f"  Directory not empty, skipping removal: {sub_item}")


if __name__ == "__main__":
    flatten_downloads(ROOT_DIR)
