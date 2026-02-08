import re
import os
import logging

from mutagen.flac import FLAC, Picture
import mutagen.id3 as id3
from mutagen.id3 import ID3NoHeaderError

logger = logging.getLogger(__name__)


# unicode symbols
COPYRIGHT, PHON_COPYRIGHT = "\u2117", "\u00a9"
# if a metadata block exceeds this, mutagen will raise error
# and the file won't be tagged
FLAC_MAX_BLOCKSIZE = 16777215

ID3_LEGEND = {
    "album": id3.TALB,
    "albumartist": id3.TPE2,
    "artist": id3.TPE1,
    "comment": id3.COMM,
    "composer": id3.TCOM,
    "copyright": id3.TCOP,
    "date": id3.TDAT,
    "genre": id3.TCON,
    "isrc": id3.TSRC,
    "label": id3.TPUB,
    "performer": id3.TOPE,
    "title": id3.TIT2,
    "year": id3.TYER,
}


def _get_title(track_dict):
    title = track_dict["title"]
    version = track_dict.get("version")
    if version:
        title = f"{title} ({version})"
    # for classical works
    if track_dict.get("work"):
        title = f"{track_dict['work']}: {title}"

    return title


def log_missing_field(context_id, field, default):
    try:
        with open("errors.log", "a", encoding="utf-8") as f:
            import datetime

            ts = datetime.datetime.now().isoformat()
            f.write(
                f"[{ts}] [{context_id}] Missing field: '{field}', used default: '{default}'\n"
            )
    except Exception:
        pass


def get_safe(data, keys, default=None, context_id=""):
    val = data
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            val = None

        if val is None:
            if context_id and default is not None:
                log_missing_field(context_id, ".".join(keys), default)
            return default
    return val


def _format_copyright(s: str) -> str:
    if s:
        s = s.replace("(P)", PHON_COPYRIGHT)
        s = s.replace("(C)", COPYRIGHT)
    return s


def _format_genres(genres: list) -> str:
    """Fixes the weirdly formatted genre lists returned by the API.
    >>> g = ['Pop/Rock', 'Pop/Rock→Rock', 'Pop/Rock→Rock→Alternatif et Indé']
    >>> _format_genres(g)
    'Pop, Rock, Alternatif et Indé'
    """
    genres = re.findall(r"([^\u2192\/]+)", "/".join(genres))
    no_repeats = []
    for g in genres:
        if g not in no_repeats:
            no_repeats.append(g)
    return ", ".join(no_repeats)


def _embed_flac_img(root_dir, audio: FLAC):
    emb_image = os.path.join(root_dir, "cover.jpg")
    multi_emb_image = os.path.join(
        os.path.abspath(os.path.join(root_dir, os.pardir)), "cover.jpg"
    )
    if os.path.isfile(emb_image):
        cover_image = emb_image
    else:
        cover_image = multi_emb_image

    try:
        # rest of the metadata still gets embedded
        # when the image size is too big
        if os.path.getsize(cover_image) > FLAC_MAX_BLOCKSIZE:
            raise Exception(
                "downloaded cover size too large to embed. "
                "turn off `og_cover` to avoid error"
            )

        image = Picture()
        image.type = 3
        image.mime = "image/jpeg"
        image.desc = "cover"
        with open(cover_image, "rb") as img:
            image.data = img.read()
        audio.add_picture(image)
    except Exception as e:
        logger.error(f"Error embedding image: {e}", exc_info=True)


def _embed_id3_img(root_dir, audio: id3.ID3):
    emb_image = os.path.join(root_dir, "cover.jpg")
    multi_emb_image = os.path.join(
        os.path.abspath(os.path.join(root_dir, os.pardir)), "cover.jpg"
    )
    if os.path.isfile(emb_image):
        cover_image = emb_image
    else:
        cover_image = multi_emb_image

    with open(cover_image, "rb") as cover:
        audio.add(id3.APIC(3, "image/jpeg", 3, "", cover.read()))


# Use KeyError catching instead of dict.get to avoid empty tags
def tag_flac(
    filename, root_dir, final_name, d: dict, album, istrack=True, em_image=False
):
    """
    Tag a FLAC file

    :param str filename: FLAC file path
    :param str root_dir: Root dir used to get the cover art
    :param str final_name: Final name of the FLAC file (complete path)
    :param dict d: Track dictionary from Qobuz_client
    :param dict album: Album dictionary from Qobuz_client
    :param bool istrack
    :param bool em_image: Embed cover art into file
    """
    audio = FLAC(filename)

    try:
        audio["TITLE"] = _get_title(d)
    except KeyError:
        audio["TITLE"] = "Unknown Title"

    audio["TRACKNUMBER"] = str(d.get("track_number", "0"))  # TRACK NUMBER

    if "Disc " in final_name:
        audio["DISCNUMBER"] = str(d.get("media_number", "1"))

    cid = str(d.get("id", "unknown_id"))

    try:
        audio["COMPOSER"] = get_safe(d, ["composer", "name"], None, cid)  # COMPOSER
    except KeyError:  # get_safe handles KeyError/None but returns None. FLAC tag assignment with None might fail or be skipped?
        # FLAC tags are list-like. audio["KEY"] = value. If value is None, it might coerce to string "None" or fail?
        # Mutagen FLAC keys usually expect string or list of strings.
        # We should check if None.
        pass

    comp = get_safe(d, ["composer", "name"], None, cid)
    if comp:
        audio["COMPOSER"] = comp

    artist_ = get_safe(d, ["performer", "name"], None)  # TRACK ARTIST
    if istrack:
        audio["ARTIST"] = artist_ or get_safe(
            d, ["album", "artist", "name"], "Unknown Artist", cid
        )  # TRACK ARTIST
    else:
        audio["ARTIST"] = artist_ or get_safe(
            album, ["artist", "name"], "Unknown Artist", cid
        )

    audio["LABEL"] = get_safe(album, ["label", "name"], "n/a", cid)

    if istrack:
        audio["GENRE"] = _format_genres(get_safe(d, ["album", "genres_list"], [], cid))
        audio["ALBUMARTIST"] = get_safe(
            d, ["album", "artist", "name"], "Unknown Artist", cid
        )
        audio["TRACKTOTAL"] = str(get_safe(d, ["album", "tracks_count"], "0", cid))
        audio["ALBUM"] = get_safe(d, ["album", "title"], "Unknown Album", cid)
        audio["DATE"] = get_safe(
            d, ["album", "release_date_original"], "0000-00-00", cid
        )
        audio["COPYRIGHT"] = _format_copyright(get_safe(d, ["copyright"], "n/a", cid))
    else:
        audio["GENRE"] = _format_genres(get_safe(album, ["genres_list"], [], cid))
        audio["ALBUMARTIST"] = get_safe(
            album, ["artist", "name"], "Unknown Artist", cid
        )
        audio["TRACKTOTAL"] = str(get_safe(album, ["tracks_count"], "0", cid))
        audio["ALBUM"] = get_safe(album, ["title"], "Unknown Album", cid)
        audio["DATE"] = get_safe(album, ["release_date_original"], "0000-00-00", cid)
        audio["COPYRIGHT"] = _format_copyright(
            get_safe(album, ["copyright"], "n/a", cid)
        )

    if em_image:
        _embed_flac_img(root_dir, audio)

    audio.save()
    os.rename(filename, final_name)


def tag_mp3(filename, root_dir, final_name, d, album, istrack=True, em_image=False):
    """
    Tag an mp3 file

    :param str filename: mp3 temporary file path
    :param str root_dir: Root dir used to get the cover art
    :param str final_name: Final name of the mp3 file (complete path)
    :param dict d: Track dictionary from Qobuz_client
    :param bool istrack
    :param bool em_image: Embed cover art into file
    """

    try:
        audio = id3.ID3(filename)
    except ID3NoHeaderError:
        audio = id3.ID3()

    # temporarily holds metadata
    tags = dict()
    # For _get_title we still pass dict, but we should refactor _get_title too?
    # Let's keep _get_title usage but maybe wrap it?
    # Actually _get_title uses d["title"] which might fail.
    # But "title" is core. Let's assume title exists or let it crash?
    # User said "prevent KeyError".
    try:
        tags["title"] = _get_title(d)
    except KeyError:
        tags["title"] = "Unknown Title"

    cid = str(d.get("id", "unknown_id"))

    tags["label"] = get_safe(album, ["label", "name"], "Unknown Label", cid)

    artist_ = get_safe(d, ["performer", "name"], None)  # TRACK ARTIST
    if istrack:
        album_artist = get_safe(d, ["album", "artist", "name"], "Unknown Artist", cid)
        tags["artist"] = artist_ or album_artist
    else:
        album_artist = get_safe(album, ["artist", "name"], "Unknown Artist", cid)
        tags["artist"] = artist_ or album_artist

    if istrack:
        tags["genre"] = _format_genres(get_safe(d, ["album", "genres_list"], [], cid))
        tags["albumartist"] = get_safe(
            d, ["album", "artist", "name"], "Unknown Artist", cid
        )
        tags["album"] = get_safe(d, ["album", "title"], "Unknown Album", cid)
        tags["date"] = get_safe(
            d, ["album", "release_date_original"], "0000-00-00", cid
        )
        tags["copyright"] = _format_copyright(get_safe(d, ["copyright"], "n/a", cid))
        tracktotal = str(get_safe(d, ["album", "tracks_count"], "0", cid))
    else:
        tags["genre"] = _format_genres(get_safe(album, ["genres_list"], [], cid))
        tags["albumartist"] = get_safe(album, ["artist", "name"], "Unknown Artist", cid)
        tags["album"] = get_safe(album, ["title"], "Unknown Album", cid)
        tags["date"] = get_safe(album, ["release_date_original"], "0000-00-00", cid)
        tags["copyright"] = _format_copyright(
            get_safe(album, ["copyright"], "n/a", cid)
        )
        tracktotal = str(get_safe(album, ["tracks_count"], "0", cid))

    tags["year"] = tags["date"][:4]

    audio["TRCK"] = id3.TRCK(
        encoding=3, text=f"{d.get('track_number', '0')}/{tracktotal}"
    )
    audio["TPOS"] = id3.TPOS(encoding=3, text=str(d.get("media_number", "1")))

    # write metadata in `tags` to file
    for k, v in tags.items():
        if v is None:
            continue
        id3tag = ID3_LEGEND[k]
        audio[id3tag.__name__] = id3tag(encoding=3, text=v)

    if em_image:
        _embed_id3_img(root_dir, audio)

    audio.save(filename, "v2_version=3")
    os.rename(filename, final_name)
