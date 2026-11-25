import base64
import html
import os
import re

import requests
from mutagen.mp4 import MP4, MP4Cover

from .helper import RECOVERABLE_ERRORS, REQUEST_TIMEOUT, download_file, sanitize_name
from .pyDes import ECB, PAD_PKCS5, des

DES_KEY = b"38346591"
ALBUMS = "Albums"
ARTISTS = "Artists"
PLAYLISTS = "Playlists"
SHOWS = "Shows"
SONGS = "Songs"


def _split_names(value):
    if not value:
        return []
    if isinstance(value, str):
        value = value.split(",")
    return [html.unescape(str(name)).strip() for name in value if str(name).strip()]


def _text(value):
    return html.unescape(str(value)) if value else ""


def tags_from_list_song(song):
    return {
        "title": _text(song.get("song")),
        "artists": _split_names(song.get("primary_artists")),
        "album": _text(song.get("album")),
        "composers": _split_names(song.get("music")),
        "starring": _split_names(song.get("starring")),
        "year": _text(song.get("year")),
        "copyright": _text(song.get("copyright_text") or song.get("label")),
        "image": song.get("image", ""),
    }


def tags_from_song_details(song):
    more_info = song.get("more_info", {})
    artist_map = more_info.get("artistMap", {})
    artists = artist_map.get("artists", [])

    def by_role(role):
        return [a["name"] for a in artists if a.get("role") == role]

    return {
        "title": _text(song.get("title")),
        "artists": _split_names([a["name"] for a in artist_map.get("primary_artists", [])]),
        "album": _text(more_info.get("album")),
        "composers": _split_names(by_role("music") or more_info.get("music")),
        "starring": _split_names(by_role("starring")),
        "year": _text(song.get("year")),
        "copyright": _text(more_info.get("copyright_text") or more_info.get("label")),
        "image": song.get("image", ""),
    }


class Manager:
    def __init__(self, session, out_folder):
        self.session = session
        self.out_folder = os.path.abspath(out_folder)
        self.des_cipher = des(DES_KEY, ECB, b"\0" * 8, pad=None, padmode=PAD_PKCS5)
        self.failures = 0

    def record_failure(self, message):
        self.failures += 1
        print(message)

    def decrypt_url(self, enc_url):
        enc_url = base64.b64decode(enc_url.strip())
        dec_url = self.des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode("utf-8")
        return dec_url.replace("_96.mp4", "_320.mp4")

    def with_id(self, name, item_id):
        # the id keeps albums, songs etc. with the same name apart
        return sanitize_name(f"{html.unescape(name or 'Unknown')} [{item_id}]")

    def format_filename(self, title, song_id):
        return self.with_id(title, song_id) + ".mp4"

    def get_download_location(self, *folders, filename):
        return os.path.join(self.out_folder, *folders, filename)

    def download(self, label, location, url, tags=None):
        if os.path.isfile(location):
            print(f"Already downloaded: {label}")
            return False
        print(f"Downloading {label}")
        part_path = download_file(self.session, url, location, show_progress=True)
        if tags:
            try:
                self.add_tags(part_path, tags)
            except Exception as e:
                print(f"Error adding metadata: {e}")
        os.replace(part_path, location)
        return True

    def download_songs(self, songs, *folders):
        for song in songs:
            try:
                dec_url = self.decrypt_url(song["encrypted_media_url"])
                filename = self.format_filename(song["song"], song["id"])
                location = self.get_download_location(*folders, filename=filename)
                self.download(filename, location, dec_url, tags_from_list_song(song))
            except RECOVERABLE_ERRORS as e:
                self.record_failure(f"Download error for {song.get('song', 'unknown song')}: {e}")

    def fetch_cover(self, image_url):
        if not image_url:
            return None
        cover_url = re.sub(r"-\d+x\d+\.(webp|jpg|png)$", r"-500x500.jpg", image_url)
        try:
            response = self.session.get(cover_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Could not fetch cover art: {e}")
            return None
        image_format = MP4Cover.FORMAT_PNG if cover_url.endswith(".png") else MP4Cover.FORMAT_JPEG
        return MP4Cover(response.content, image_format)

    def add_tags(self, path, tags):
        # https://mutagen.readthedocs.io/en/latest/api/mp4.html
        audio = MP4(path)
        if tags.get("title"):
            audio["\xa9nam"] = tags["title"]
        if tags.get("artists"):
            audio["\xa9ART"] = tags["artists"]
            audio["aART"] = tags["artists"]
        if tags.get("album"):
            audio["\xa9alb"] = tags["album"]
        if tags.get("composers"):
            audio["\xa9wrt"] = tags["composers"]
        if tags.get("starring"):
            audio["desc"] = "Starring: " + ", ".join(tags["starring"])
        if tags.get("year"):
            audio["\xa9day"] = tags["year"]
        if tags.get("copyright"):
            audio["cprt"] = tags["copyright"]
        cover = self.fetch_cover(tags.get("image"))
        if cover is not None:
            audio["covr"] = [cover]
        audio.save()
