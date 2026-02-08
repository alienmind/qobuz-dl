import logging
import os
import re
import string
import time

from mutagen.flac import FLAC
from mutagen.mp3 import EasyMP3

from qobuz_dj.color import GREEN, RED, RESET, YELLOW

logger = logging.getLogger(__name__)

EXTENSIONS = (".mp3", ".flac")


class PartialFormatter(string.Formatter):
    def __init__(self, missing="n/a", bad_fmt="n/a"):
        self.missing, self.bad_fmt = missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        try:
            val = super(PartialFormatter, self).get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            val = None, field_name
        return val

    def format_field(self, value, format_spec):
        if not value:
            return self.missing
        try:
            return super(PartialFormatter, self).format_field(value, format_spec)
        except ValueError:
            if self.bad_fmt:
                return self.bad_fmt
            raise


def clean_unicode(text):
    """Replaces specific unicode characters as requested by the user."""
    if not text:
        return text
    return text.replace("æ", "ae").replace("Æ", "AE")


def make_m3u(pl_directory):
    track_list = ["#EXTM3U"]
    rel_folder = os.path.basename(os.path.normpath(pl_directory))
    pl_name = rel_folder + ".m3u"
    for local, dirs, files in os.walk(pl_directory):
        dirs.sort()
        audio_rel_files = [
            os.path.join(os.path.basename(os.path.normpath(local)), file_)
            for file_ in files
            if os.path.splitext(file_)[-1] in EXTENSIONS
        ]
        audio_files = [
            os.path.abspath(os.path.join(local, file_))
            for file_ in files
            if os.path.splitext(file_)[-1] in EXTENSIONS
        ]
        if not audio_files or len(audio_files) != len(audio_rel_files):
            continue

        for audio_rel_file, audio_file in zip(
            audio_rel_files, audio_files, strict=True
        ):
            try:
                pl_item = (
                    EasyMP3(audio_file) if ".mp3" in audio_file else FLAC(audio_file)
                )

                title = pl_item["TITLE"][0]
                artist = pl_item["ARTIST"][0]
                length = int(pl_item.info.length)
                index = "#EXTINF:{}, {} - {}\n{}".format(
                    length, artist, title, audio_rel_file
                )
            except:  # noqa
                continue
            track_list.append(index)

    if len(track_list) > 1:
        with open(os.path.join(pl_directory, pl_name), "w", encoding="utf-8") as pl:
            pl.write("\n\n".join(track_list))


def smart_discography_filter(
    contents: list, save_space: bool = False, skip_extras: bool = False
) -> list:
    """When downloading some artists' discography, many random and spam-like
    albums can get downloaded. This helps filter those out to just get the good stuff.

    This function removes:
        * albums by other artists, which may contain a feature from the requested artist
        * duplicate albums in different qualities
        * (optionally) removes collector's, deluxe, live albums

    :param list contents: contents returned by qobuz API
    :param bool save_space: choose highest bit depth, lowest sampling rate
    :param bool remove_extras: remove albums with extra material (i.e. live, deluxe,...)
    :returns: filtered items list
    """

    TYPE_REGEXES = {
        "remaster": r"(?i)(re)?master(ed)?",
        "extra": r"(?i)(anniversary|deluxe|live|collector|demo|expanded)",
    }

    def is_type(album_t: str, album: dict) -> bool:
        """Check if album is of type `album_t`"""
        version = album.get("version", "")
        title = album.get("title", "")
        regex = TYPE_REGEXES[album_t]
        return re.search(regex, f"{title} {version}") is not None

    def essence(title: str) -> str:
        """Ignore text in parens/brackets, return all lowercase.
        Used to group two albums that may be named similarly, but not exactly
        the same.
        """
        r = re.match(r"([^\(]+)(?:\s*[\(\[][^\)][\)\]])*", title)
        if r:
            return r.group(1).strip().lower()
        return title.strip().lower()

    requested_artist = contents[0]["name"]
    items = [item["albums"]["items"] for item in contents][0]

    # use dicts to group duplicate albums together by title
    title_grouped: dict[str, list[dict]] = {}
    for item in items:
        title_ = essence(item["title"])
        if title_ not in title_grouped:  # ?
            #            if (t := essence(item["title"])) not in title_grouped:
            title_grouped[title_] = []
        title_grouped[title_].append(item)

    items = []
    for albums in title_grouped.values():
        best_bit_depth = max(a["maximum_bit_depth"] for a in albums)
        get_best = min if save_space else max
        best_sampling_rate = get_best(
            a["maximum_sampling_rate"]
            for a in albums
            if a["maximum_bit_depth"] == best_bit_depth
        )
        remaster_exists = any(is_type("remaster", a) for a in albums)

        def is_valid(
            album: dict,
            best_bit_depth=best_bit_depth,
            best_sampling_rate=best_sampling_rate,
            remaster_exists=remaster_exists,
        ) -> bool:
            """Check if album is of type `album_t`"""
            return (
                album["maximum_bit_depth"] == best_bit_depth
                and album["maximum_sampling_rate"] == best_sampling_rate
                and album["artist"]["name"] == requested_artist
                and not (  # states that are not allowed
                    (remaster_exists and not is_type("remaster", album))
                    or (skip_extras and is_type("extra", album))
                )
            )

        sorted_albums = sorted(
            filter(is_valid, albums),
            key=lambda x: x.get("release_date_original", "0000-00-00"),
            reverse=True,
        )

        filtered = sorted_albums
        # most of the time, len is 0 or 1.
        # if greater, it is a complete duplicate,
        # so it doesn't matter which is chosen
        if len(filtered) >= 1:
            selected = filtered[0]
            items.append(selected)

    return items


def format_duration(duration):
    return time.strftime("%H:%M:%S", time.gmtime(duration))


def create_and_return_dir(directory):
    fix = os.path.normpath(directory)
    os.makedirs(fix, exist_ok=True)
    return fix


def sanitize_directory(directory):
    """
    Recursively sanitizes MP3 filenames in a directory.
    Renames to: {NN} - {Artist} - {Title} ({Year}).mp3
    Renumbers sequentially across all files found.
    """
    from mutagen.id3 import ID3
    from mutagen.mp3 import MP3
    from pathvalidate import sanitize_filename

    # Strip potential quotes and normalization
    directory = directory.strip("\"'")
    directory = os.path.normpath(directory)

    logger.info(f"{YELLOW}Sanitizing directory: {directory}{RESET}")

    if not os.path.isdir(directory):
        logger.error(f"{RED}Error: {directory} is not a valid directory.{RESET}")
        return

    mp3_files = []
    # Collect all mp3 files first to sort them
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".mp3"):
                mp3_files.append(os.path.join(root, file))

    # Sort files to ensure deterministic order (by path)
    mp3_files.sort()

    count = 0
    errors = 0

    final_files = []
    for i, filepath in enumerate(mp3_files, 1):
        try:
            # Load ID3
            try:
                audio = MP3(filepath, ID3=ID3)
            except Exception:
                audio = None

            # Extract Metadata (ID3 Priority)
            artist = "Unknown Artist"
            title = "Unknown Title"
            year = "0000"

            if audio and audio.tags:
                artist = clean_unicode(str(audio.tags.get("TPE1", [artist])[0]))
                title = clean_unicode(str(audio.tags.get("TIT2", [title])[0]))

                # Year
                dr_tag = audio.tags.get("TDRC")
                if dr_tag:
                    year = str(dr_tag[0])
                else:
                    year_tag = audio.tags.get("TDER") or audio.tags.get("TYER")
                    if year_tag:
                        year = str(year_tag[0])
                year = str(year)[:4]

            # Construct new name
            # NN - Artist - Title (Year).mp3
            track_num = f"{i:02d}"
            new_filename = f"{track_num} - {artist} - {title} ({year}).mp3"
            new_filename = sanitize_filename(new_filename)

            # Directory needed
            root = os.path.dirname(filepath)
            new_filepath = os.path.join(root, new_filename)

            if filepath != new_filepath:
                try:
                    os.rename(filepath, new_filepath)
                    logger.info(
                        f"Renamed: {os.path.basename(filepath)} -> {new_filename}"
                    )
                    count += 1
                    final_files.append(new_filepath)
                except OSError as e:
                    logger.error(f"{RED}Failed to rename {filepath}: {e}{RESET}")
                    errors += 1
                    final_files.append(filepath)
            else:
                final_files.append(filepath)
        except Exception as e:
            logger.error(f"{RED}Error processing {filepath}: {e}{RESET}")
            errors += 1
            final_files.append(filepath)

    logger.info(f"{YELLOW}Sanitized {count} files. Errors: {errors}.{RESET}")

    # Create M3U playlist
    if final_files:
        # Use directory name for playlist, stripping any trailing separators
        dir_name = os.path.basename(directory.rstrip(os.sep + (os.altsep or "")))
        playlist_name = dir_name + ".m3u"
        playlist_path = os.path.join(directory, playlist_name)
        try:
            with open(playlist_path, "w", encoding="utf-8") as f:
                for fpath in final_files:
                    # Write relative path for portability
                    rel_path = os.path.relpath(fpath, directory)
                    f.write(rel_path + "\n")
            logger.info(f"{GREEN}Created playlist: {playlist_name}{RESET}")
        except Exception as e:
            logger.error(f"{RED}Failed to create playlist: {e}{RESET}")


def get_url_info(url):
    """Returns the type of the url and the id.

    Compatible with urls of the form:
        https://www.qobuz.com/us-en/{type}/{name}/{id}
        https://open.qobuz.com/{type}/{id}
        https://play.qobuz.com/{type}/{id}
        /us-en/{type}/-/{id}
    """

    r = re.search(
        r"(?:https:\/\/(?:w{3}|open|play)\.qobuz\.com)?(?:\/[a-z]{2}-[a-z]{2})"
        r"?\/(album|artist|track|playlist|label)(?:\/[-\w\d]+)?\/([\w\d]+)",
        url,
    )
    if not r:
        raise IndexError("Invalid URL")
    return r.groups()
