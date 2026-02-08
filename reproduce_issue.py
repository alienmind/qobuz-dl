import os
import re
import shutil

from mutagen.id3 import ID3, TDRC, TIT2, TPE1, TRCK
from mutagen.mp3 import MP3

TEST_DIR = "test_downloads"
SOURCE_MP3 = r"c:\Music\qobuz-dl\Qobuz Downloads\Best of VNV Nation\01. God of All.mp3"


def setup_test_files():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)

    if not os.path.exists(SOURCE_MP3):
        print(f"Source MP3 not found: {SOURCE_MP3}")
        return

    # Function to create a dummy mp3 with tags
    def create_mp3(filename, artist, title, year, track):
        path = os.path.join(TEST_DIR, filename)
        shutil.copy(SOURCE_MP3, path)  # Copy real MP3

        try:
            audio = MP3(path, ID3=ID3)
            # Clear existing tags
            audio.delete()
            audio.save()

            # Re-init tags
            audio = MP3(path, ID3=ID3)
            try:
                audio.add_tags()
            except:
                pass

            audio.tags.add(TPE1(encoding=3, text=artist))
            audio.tags.add(TIT2(encoding=3, text=title))
            audio.tags.add(TDRC(encoding=3, text=year))
            audio.tags.add(TRCK(encoding=3, text=str(track)))
            audio.save()
        except Exception as e:
            print(f"Error creating tags for {filename}: {e}")

    # Case 1: Filename has track number
    create_mp3("01. Song One.mp3", "Artist A", "Song One", "2021", 1)

    # Case 2: Filename has no track number
    create_mp3("Song Two.mp3", "Artist B", "Song Two", "2022", 2)

    # Case 3: Filename has track number but different separator
    create_mp3("03 - Song Three.mp3", "Artist C", "Song Three", "2023", 3)

    # Case 4: Track number in filename differs from ID3 (User says keep filename one)
    create_mp3(
        "05. Song Four.mp3", "Artist D", "Song Four", "2024", 4
    )  # Filename says 05, ID3 says 4


def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def processing_logic(directory):
    print(f"\nScanning {directory}...")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if not file.lower().endswith(".mp3"):
                continue

            filepath = os.path.join(root, file)
            print(f"\nProcessing: {file}")

            try:
                audio = MP3(filepath, ID3=ID3)
            except Exception as e:
                print(f"  Error reading ID3: {e}")
                continue

            # Extract info
            artist = str(audio.tags.get("TPE1", ["Unknown Artist"])[0])
            title = str(audio.tags.get("TIT2", ["Unknown Title"])[0])
            year_tag = audio.tags.get("TDRC")
            year = str(year_tag[0]) if year_tag else "0000"
            year = str(year)[:4]

            id3_track = str(audio.tags.get("TRCK", ["0"])[0])
            if "/" in id3_track:
                id3_track = id3_track.split("/")[0]

            # Check filename for track number
            # Regex for starting with digits followed by dot, space, dash
            match = re.match(r"^(\d+)\s*[\.\-]?\s*", file)

            if match:
                track_num = match.group(1)
                print(f"  Found track number in filename: {track_num}")
            else:
                track_num = id3_track
                print(f"  Using ID3 track number: {track_num}")

            # Pad track number
            current_track_num_int = int(track_num) if track_num.isdigit() else 0
            track_num = f"{current_track_num_int:02d}"

            new_filename = f"{track_num} - {artist} - {title} ({year}).mp3"
            new_filename = sanitize_filename(new_filename)

            if file != new_filename:
                print(f"  Renaming to: {new_filename}")
                # os.rename(filepath, os.path.join(root, new_filename))
            else:
                print("  Filename is already correct.")


if __name__ == "__main__":
    setup_test_files()
    processing_logic(TEST_DIR)
