# qobuz-dj 🎧
Search, explore and download Lossless and Hi-Res music from [Qobuz](https://www.qobuz.com/).
**This is a maintained fork of [vitiko98/qobuz-dl](https://github.com/vitiko98/qobuz-dl), specifically optimized for my DJ workflow, but can work for other music collectors as well. Portable and easy to use.**

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=VZWSWVGZGJRMU&source=url)  
*(You can donate to vitiko98 the original author of qobuz-dl - I don't take any donations)*

## Why qobuz-dj?
This version is tailored for building a performance-ready music library:

*   **GUI Mode (`gui`)**: A graphical user interface for the application.
*   **DJ Mode (`dj`)**: A native top-level command for high-quality MP3s (320kbps), better metadata consistency, and embedded artwork.
*   **Sanitization Mode (`sz`)**: Keep your library tidy with automated sequential renumbering and playlist generation.
*   **Top tracks Mode (`top`)**: Download the top <n> tracks of an artist. Don't miss greatest hits!
*   **Smart Discography**: Intelligently filters for the best versions of tracks, avoiding duplicates and prefering remasters.
*   **Modern Reliability**: Fixed for **Python 3.13**, managed by **uv**, and built with automated CI/CD for all major platforms.

---

## The DJ Workflow

### Standard DJ Download
The most common command for building your library. It ensures maximum compatibility with Serato, Rekordbox, and Traktor.
```bash
qobuz-dj dj <url>
```
**This automatically enables:**
- **MP3 320kbps** (For compatibility).
- **Embedded Artwork** (No loose `cover.jpg` files).
- **Smart Filtering** (Skips duplicates and promotional spam).
- **Portable Folder Naming**: Clean artist and album organization.

### Sanitizing your Library
Already have a messy folder? Clean it up instantly:
```bash
qobuz-dj sz <path/to/folder>
```
Matches your files to a strict `NN - Artist - Title (Year)` format and generates a companion `.m3u` playlist.

---

## Getting started

> You'll need an **active subscription** to Qobuz

### 1. Simple Installation (Recommended)
This project is optimized for **[uv](https://github.com/astral/uv)**.

*   **Run directly**: `uv run qobuz-dj`
*   **Install as tool**: `uv tool install .`

### 2. Standalone Binaries
No Python? No problem. Download the pre-compiled `qobuz-dj` executable from the Github Releases page, for:
- 🪟 Windows (`.exe`)
- 🐧 Linux
- 🍎 macOS

---

## All Commands

| Command | Mode | Description |
| :--- | :--- | :--- |
| `dj` | **DJ Mode** | **Recommended.** Shortcut for `dl -D`. Optimized for performance. |
| `dl` | **Input Mode** | Standard downloads with full control over quality and tags. |
| `sz` | **Sanitize** | Rename and renumber existing folders + create playlists. |
| `fun` | **Interactive**| Search and explore music directly in your terminal. |
| `lucky`| **Lucky** | Download the top results for any search query. |

---

## Advanced Usage Examples

### Standard Downloads
Download a specific album in FLAC (Quality 6):
```bash
qobuz-dj dl <url> -q 6
```

### DJ Optimized
Download the Top 10 tracks of an artist, formatted specifically for your DJ software:
```bash
qobuz-dj dj -T 10 <artist_url>
```

### Search & Download
```bash
qobuz-dj lucky "daft punk homework" --type album
```

---

## Development & Build
This project uses `poethepoet` for automation.
- `uv run poe check`: Code quality checks.
- `uv run poe test`: Run the test suite.
- `uv run poe build`: Compile your own standalone executable.

## Disclaimer
This tool is for educational purposes. Please respect the [Qobuz API Terms of Use](https://static.qobuz.com/apps/api/QobuzAPI-TermsofUse.pdf). Not affiliated with Qobuz.
