import getpass
import os
import sys

from scripts.content.album import Album
from scripts.content.artist import Artist
from scripts.content.playlist import Playlist
from scripts.content.song import Song
from scripts.download_manager import LimitReached, Manager
from scripts.helper import RECOVERABLE_ERRORS, create_session, parse_args, scan_url
from scripts.saavnaccount import Account

CONTENT_TYPES = {"album": Album, "playlist": Playlist, "song": Song}
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads")


def read_urls(filepath):
    with open(filepath, encoding="utf-8-sig") as f:
        return [line.strip() for line in f if line.strip()]


def run_account(args, session, manager):
    if args.clone and args.create == args.copy:
        print("Use -clone with exactly one of -create or -copy")
        return False
    if not (args.playlists or args.albums or args.shows or args.clone or args.create):
        print("With -user, choose one of -p, -a, -s, -clone or -create")
        return False
    if args.dry_run and (args.clone or args.create):
        print("--dry-run can't be used with -clone or -create")
        return False

    email = args.email or input("Enter your email for JioSaavn: ").strip()
    password = args.password or getpass.getpass("Enter your password for JioSaavn: ")
    account = Account(session, manager, email, password)

    if args.playlists:
        account.download_playlists()
    elif args.albums:
        account.download_albums()
    elif args.shows:
        account.download_shows()
    elif args.clone:
        return account.clone_interactive(create_new=args.create)
    else:
        return account.create_user()
    return True


def run_downloads(args, session, manager):
    urls = []
    if args.url:
        urls.append(args.url)
    if args.file:
        urls.extend(read_urls(args.file))
    if not urls:
        urls = [input("Enter the URL: ").strip()]

    failed = 0
    for url in urls:
        kind = scan_url(url)
        try:
            if kind == "artist":
                Artist(session, manager, songs_only=args.song).start_download(url)
            elif kind in CONTENT_TYPES:
                CONTENT_TYPES[kind](session, manager).start_download(url)
            else:
                print(f"Invalid URL: {url}")
                failed += 1
        except RECOVERABLE_ERRORS as e:
            print(f"Failed to download {url}: {e}")
            failed += 1
    return failed == 0


def main(argv=None):
    args = parse_args(argv)
    if args.limit is not None and args.limit < 1:
        print("--limit must be 1 or more")
        return 2
    session = create_session()
    manager = Manager(session, args.outFolder or DOWNLOAD_DIR, dry_run=args.dry_run, limit=args.limit)
    try:
        ok = run_account(args, session, manager) if args.user else run_downloads(args, session, manager)
    except RECOVERABLE_ERRORS as e:
        print(f"Error: {e}")
        ok = False
    except LimitReached:
        print(f"Stopped at --limit {args.limit}")
        ok = True
    except KeyboardInterrupt:
        print("\nCancelled")
        return 130
    ok = ok and manager.failures == 0
    print("DONE" if ok else "Finished with errors")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
