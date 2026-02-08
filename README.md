# qobuz-dl
Search, explore and download Lossless and Hi-Res music from [Qobuz](https://www.qobuz.com/).
**This is a maintained fork of [vitiko98/qobuz-dl](https://github.com/vitiko98/qobuz-dl), optimized for DJs and modern python environments.**

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=VZWSWVGZGJRMU&source=url)  
*(You can donate to vitiko98 the original author of qobuz-dl - I don't take any donations)*

## Why this fork? (DJ Highlights)
This version of `qobuz-dl` is specifically tailored for building a professional music library for performance:

*   **DJ Mode (`-D`)**: A one-stop flag for high-quality MP3s (320kbps), embedded artwork (no messy `cover.jpg` files), and flattened playlist folders.
*   **Sanitization Mode (`sz`)**: A powerful tool to clean up your existing library, renaming files to a consistent `NN - Artist - Title (Year)` format and generating tidy `.m3u` playlists.
*   **Smart Discography**: Automatically avoids duplicates by checking a local database, preferring the latest releases/remasters when available.
*   **Modern & Fast**: Updated for **Python 3.13**, managed by **uv**, and hardened with modern linting for ultimate reliability.

---

## Sanitization Mode (`sz`)
Maintain a perfectly organized library with the `sz` command. It recursively scans a directory, renames all MP3s using their metadata, and creates a master playlist.

**Command:**
```bash
qobuz-dl sz <path_to_directory>
```

**What it does:**
1.  **Strict Renaming**: Renames files to `{NN} - {Artist} - {Title} ({Year}).mp3`.
2.  **Sequential Numbering**: `NN` is a sequential number (01, 02, etc.) based on the alphabetical order of files in the folder.
3.  **Filename Cleaning**: Removes invalid characters and ensures cross-platform compatibility.
4.  **Master Playlist**: Automatically creates an `.m3u` file (named after the folder) containing the new list of files.

---

## DJ Mode Details
Designed for DJs who need consistent formatting and high-quality files for their software (Serato, Rekordbox, Traktor).

**Command:**
```bash
qobuz-dl dl -D <url>
```

**Automated DJ Workflow:**
*   Forces **MP3 320kbps** (best compatibility).
*   **Embeds Artwork** directly into the ID3 tags.
*   **Smart Discography** (skips already owned IDs).
*   **Folder Formatting**:
    *   Albums: `{artist} - {album} ({year})`
    *   Playlists: Flattens all tracks into a single folder (no subfolders).

---

## Getting started

> You'll need an **active subscription** to Qobuz

### Installation with uv (Recommended)
This project is optimized for **[uv](https://github.com/astral/uv)**, a fast Python package installer and resolver.

1.  **Run directly** (no installation required):
    ```bash
    uv run qobuz-dl
    ```

2.  **Or install as a tool**:
    ```bash
    uv tool install .
    ```

3.  **Standalone Executable**:
    Download the pre-compiled binary from the releases page (if available) or build your own with `uv run poe build`.

### Standalone Executable
Download the pre-compiled binary from the releases page (if available) or build your own with `uv run poe build`.

---

## General Features
* Download FLAC and MP3 files from Qobuz
* **Interactive** or **lucky** modes for terminal exploration
* Queue support in interactive mode
* Support for M3U playlists
* Download from text files
* Extended tags and mult-disc album support

## Usage Examples

### Download mode
Download URL in Lossless
```
qobuz-dl dl <url> -q 6
```
Download multiple URLs to custom directory
```
qobuz-dl dl <url1> <url2> -d "My New Music"
```

### Interactive mode
```
qobuz-dl fun -l 10
```

### Lucky mode
```
qobuz-dl lucky "daft punk homework" --type album
```

---

## Usage
```
usage: qobuz-dl [-h] [-r] [-p] [-sc] [--rebuild-db] [--db] {fun,dl,lucky,sz} ...

commands:
  fun       interactive mode
  dl        input mode
  lucky     lucky mode
  sz        sanitize mode
```

## Development
This project uses `poethepoet` for task management.
- `uv run poe check`: Linting and type checking.
- `uv run poe test`: Run unit tests.
- `uv run poe build`: Build standalone executable.

## Disclaimer
This tool is for educational purposes. Please respect the [Qobuz API Terms of Use](https://static.qobuz.com/apps/api/QobuzAPI-TermsofUse.pdf). Not affiliated with Qobuz.
