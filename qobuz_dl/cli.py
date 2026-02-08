import configparser
import glob
import hashlib
import logging
import os
import sys

from qobuz_dl.bundle import Bundle
from qobuz_dl.color import GREEN, RED, YELLOW
from qobuz_dl.commands import qobuz_dl_args
from qobuz_dl.core import QobuzDL
from qobuz_dl.downloader import DEFAULT_FOLDER, DEFAULT_TRACK

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

if os.name == "nt":
    OS_CONFIG = os.environ.get("APPDATA", "")
else:
    OS_CONFIG = os.path.join(os.environ["HOME"], ".config")

CONFIG_PATH = os.path.join(OS_CONFIG, "qobuz-dl")
CONFIG_FILE = os.path.join(CONFIG_PATH, "config.ini")
QOBUZ_DB = os.path.join(os.getcwd(), "downloads.db")


def _reset_config(config_file):
    logging.info(f"{YELLOW}Creating config file: {config_file}")
    config = configparser.ConfigParser()
    config["DEFAULT"]["email"] = input("Enter your email:\n- ")
    password = input("Enter your password\n- ")
    config["DEFAULT"]["password"] = hashlib.md5(password.encode("utf-8")).hexdigest()
    config["DEFAULT"]["default_folder"] = (
        input("Folder for downloads (leave empty for default 'MP3')\n- ") or "MP3"
    )
    config["DEFAULT"]["default_quality"] = (
        input(
            "Download quality (5, 6, 7, 27) "
            "[320, LOSSLESS, 24B <96KHZ, 24B >96KHZ]"
            "\n(leave empty for default '6')\n- "
        )
        or "6"
    )
    config["DEFAULT"]["default_limit"] = "20"
    config["DEFAULT"]["no_m3u"] = "false"
    config["DEFAULT"]["albums_only"] = "false"
    config["DEFAULT"]["no_fallback"] = "false"
    config["DEFAULT"]["og_cover"] = "false"
    config["DEFAULT"]["embed_art"] = "false"
    config["DEFAULT"]["no_cover"] = "false"
    config["DEFAULT"]["no_database"] = "false"
    logging.info(f"{YELLOW}Getting tokens. Please wait...")
    bundle = Bundle()
    config["DEFAULT"]["app_id"] = str(bundle.get_app_id())
    config["DEFAULT"]["secrets"] = ",".join(bundle.get_secrets().values())
    config["DEFAULT"]["folder_format"] = DEFAULT_FOLDER
    config["DEFAULT"]["track_format"] = DEFAULT_TRACK
    config["DEFAULT"]["smart_discography"] = "false"
    with open(config_file, "w") as configfile:
        config.write(configfile)
    logging.info(
        f"{GREEN}Config file updated. Edit more options in {config_file}"
        "\nso you don't have to call custom flags every time you run "
        "a qobuz-dl command."
    )


def _remove_leftovers(directory):
    directory = os.path.join(directory, "**", ".*.tmp")
    for i in glob.glob(directory, recursive=True):
        try:
            os.remove(i)
        except:  # noqa
            pass


def _handle_commands(qobuz, arguments):
    if arguments.rebuild_db:
        qobuz.rebuild_db()
        return

    try:
        if arguments.command == "dl":
            qobuz.download_list_of_urls(arguments.SOURCE)
        elif arguments.command == "lucky":
            query = " ".join(arguments.QUERY)
            qobuz.lucky_type = arguments.type
            qobuz.lucky_limit = arguments.number
            qobuz.lucky_mode(query)
        else:
            qobuz.interactive_limit = arguments.limit
            qobuz.interactive()

    except KeyboardInterrupt:
        logging.info(
            f"{RED}Interrupted by user\n{YELLOW}Already downloaded items will "
            "be skipped if you try to download the same releases again."
        )

    finally:
        _remove_leftovers(qobuz.directory)


def _initial_checks():
    if not os.path.isdir(CONFIG_PATH) or not os.path.isfile(CONFIG_FILE):
        os.makedirs(CONFIG_PATH, exist_ok=True)
        _reset_config(CONFIG_FILE)

    if len(sys.argv) < 2:
        sys.exit(qobuz_dl_args().print_help())


def main():
    _initial_checks()

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    try:
        email = config["DEFAULT"]["email"]
        password = config["DEFAULT"]["password"]
        default_folder = config["DEFAULT"]["default_folder"]
        default_limit = config["DEFAULT"]["default_limit"]
        default_quality = config["DEFAULT"]["default_quality"]
        no_m3u = config.getboolean("DEFAULT", "no_m3u")
        albums_only = config.getboolean("DEFAULT", "albums_only")
        no_fallback = config.getboolean("DEFAULT", "no_fallback")
        og_cover = config.getboolean("DEFAULT", "og_cover")
        embed_art = config.getboolean("DEFAULT", "embed_art")
        no_cover = config.getboolean("DEFAULT", "no_cover")
        no_database = config.getboolean("DEFAULT", "no_database")
        app_id = config["DEFAULT"]["app_id"]
        smart_discography = config.getboolean("DEFAULT", "smart_discography")
        folder_format = config["DEFAULT"]["folder_format"]
        track_format = config["DEFAULT"]["track_format"]

        secrets = [
            secret for secret in config["DEFAULT"]["secrets"].split(",") if secret
        ]
        arguments = qobuz_dl_args(
            int(default_quality), int(default_limit), default_folder
        ).parse_args()
    except (KeyError, UnicodeDecodeError, configparser.Error) as error:
        arguments = qobuz_dl_args().parse_args()
        if not arguments.reset:
            sys.exit(
                f"{RED}Your config file is corrupted: {error}! "
                "Run 'qobuz-dl -r' to fix this."
            )

    if arguments.reset:
        sys.exit(_reset_config(CONFIG_FILE))

    if arguments.show_config:
        print(f"Configuation: {CONFIG_FILE}\nDatabase: {QOBUZ_DB}\n---")
        with open(CONFIG_FILE, "r") as f:
            print(f.read())
        sys.exit()

    if arguments.purge:
        try:
            os.remove(QOBUZ_DB)
        except FileNotFoundError:
            pass
        sys.exit(f"{GREEN}The database was deleted.")

    # Determine DB path
    # If explicit --db: use QOBUZ_DB
    # Else if explicit --no-db or config "no_database": None
    # Else: QOBUZ_DB
    if arguments.db:
        db_path = QOBUZ_DB
    elif arguments.no_db or no_database:
        db_path = None
    else:
        db_path = QOBUZ_DB

    qobuz = QobuzDL(
        arguments.directory,
        arguments.quality,
        arguments.embed_art or embed_art,  # type: ignore
        ignore_singles_eps=arguments.albums_only or albums_only,  # type: ignore
        no_m3u_for_playlists=arguments.no_m3u or no_m3u,  # type: ignore
        quality_fallback=not arguments.no_fallback or not no_fallback,  # type: ignore
        cover_og_quality=arguments.og_cover or og_cover,  # type: ignore
        no_cover=arguments.no_cover or no_cover,  # type: ignore
        downloads_db=db_path,  # type: ignore
        folder_format=arguments.folder_format or folder_format,  # type: ignore
        track_format=arguments.track_format or track_format,  # type: ignore
        smart_discography=arguments.smart_discography or smart_discography,  # type: ignore
        dj_mode=arguments.dj,
    )
    if arguments.dj:
        qobuz.quality = 5
        qobuz.quality_fallback = False
        # Only disable DB if not forced by --db
        if not arguments.db:
            qobuz.downloads_db = None
        qobuz.smart_discography = True
        qobuz.embed_art = True
        qobuz.no_cover = True
        logging.info(
            f"{YELLOW}DJ Mode enabled: MP3 320, No Fallback, Smart Discography, "
            f"{'DB Enabled' if arguments.db else 'No DB'}, Embedded Art"
        )
    qobuz.top_tracks = arguments.top
    qobuz.initialize_client(email, password, app_id, secrets)  # type: ignore

    _handle_commands(qobuz, arguments)


if __name__ == "__main__":
    sys.exit(main())
