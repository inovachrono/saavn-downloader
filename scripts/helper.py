import argparse
import json
import os
import re

import requests
from tqdm import tqdm

API_URL = "https://www.jiosaavn.com/api.php"
REQUEST_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 60

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "cache-control": "private, max-age=0, no-cache",
}

ANDROID_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9.1; Samsung S10 Build/LMY47O)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/x-www-form-urlencoded",
}
ANDROID_PARAMS = {
    "_marker": "0",
    "_format": "json",
    "cc": "",
    "ctx": "android",
    "v": "224",
    "app_version": "6.8.2",
    "readable_version": "6.8.2",
    "build": "Pro",
    "api_version": "4",
    "network_operator": "",
    "network_type": "WIFI",
    "network_subtype": "",
    "manufacturer": "Samsung",
    "model": "Samsung Galaxy S10",
}


class SaavnError(Exception):
    pass


RECOVERABLE_ERRORS = (SaavnError, requests.RequestException, KeyError, IndexError, TypeError, ValueError, OSError)


def create_session(headers=None):
    session = requests.Session()
    session.headers.update(headers or BROWSER_HEADERS)
    return session


# the api sometimes sends junk lines before the json
def parse_json_payload(text):
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("{", "[")):
            return json.loads(stripped)
    raise SaavnError("No JSON found in API response")


def api_get(session, call, **params):
    # __call can't be a keyword argument, python mangles it inside classes
    params = {"__call": call, "_format": "json", "_marker": "0", **params}
    response = session.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return parse_json_payload(response.text)


def webapi_get(session, page_url, entity_type, **params):
    return api_get(
        session, "webapi.get", token=url_token(page_url), type=entity_type,
        includeMetaTags=0, ctx="web6dot0", api_version=4, **params,
    )


def api_post(session, data, url=API_URL):
    response = session.post(url, data=data, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return parse_json_payload(response.text)


def require_dict(data, what):
    if not isinstance(data, dict):
        raise SaavnError(f"Unexpected response for {what}")
    return data


def url_token(url):
    return url.split("?")[0].split("#")[0].rstrip("/").split("/")[-1]


def scan_url(url):
    url_parts = url.split("/")
    if "album" in url_parts:
        return "album"
    if "artist" in url_parts:
        return "artist"
    if "playlist" in url_parts or "featured" in url_parts:
        return "playlist"
    if "song" in url_parts:
        return "song"
    return None


def sanitize_name(name):
    # windows drops trailing dots and spaces from names
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", name).strip().rstrip(".")
    return name or "_"


def download_file(session, url, dest_path, timeout=DOWNLOAD_TIMEOUT, show_progress=False, retries=3):
    # downloads to a .part file and returns its path, the caller renames it when done
    part_path = dest_path + ".part"
    directory = os.path.dirname(part_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    for attempt in range(retries + 1):
        try:
            with session.get(url, stream=True, timeout=timeout) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                with tqdm(
                    total=total_size or None,
                    unit="B",
                    unit_scale=True,
                    desc=os.path.basename(dest_path),
                    bar_format="{percentage:3.0f}%|{bar:40}{r_bar}",
                    disable=not show_progress,
                ) as progress_bar, open(part_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress_bar.update(len(chunk))
            return part_path
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code < 500:
                raise
            error = e
        except requests.RequestException as e:
            error = e
        print(f"Attempt {attempt + 1} failed: {error}")
        if attempt < retries:
            print("Retrying...")
    raise SaavnError(f"Download failed after {retries + 1} attempts: {error}") from error


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Download songs, albums, playlists and artists from JioSaavn")
    parser.add_argument("-song", "--song", action="store_true", help="Download all songs of an artist (instead of albums)")
    parser.add_argument("-album", "--album", action="store_true", help="Download all albums of an artist (default)")

    parser.add_argument("-user", "--user", action="store_true", help="Sign in as a JioSaavn user")
    parser.add_argument("-p", "--playlists", action="store_true", help="Download the playlists in your library")
    parser.add_argument("-a", "--albums", action="store_true", help="Download the albums in your library")
    parser.add_argument("-s", "--shows", action="store_true", help="Download the shows/podcasts in your library")

    parser.add_argument("-clone", "--clone", action="store_true", help="Clone songs, albums, playlists to another account")
    parser.add_argument("-create", "--create", action="store_true", help="Create a new account")
    parser.add_argument("-copy", "--copy", action="store_true", help="Copy to an existing account")

    parser.add_argument("-o", "--outFolder", help="Folder to download into (default: Downloads next to main.py)")
    parser.add_argument("-u", "--url", help="URL of the song, playlist, album or artist")
    parser.add_argument("-e", "--email", help="Email of the JioSaavn user")
    parser.add_argument("-pw", "--password", help="Password of the JioSaavn user")
    parser.add_argument("-f", "--file", help="File with the URLs of songs, albums, playlists, artists")
    return parser.parse_args(argv)
