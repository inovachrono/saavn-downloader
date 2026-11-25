# Saavn Downloader

Download songs, albums, playlists and artists from JioSaavn in high quality (320 kbps MP4, or 160 kbps if 320 isn't available) with metadata.

## Features

- Download a single song, playlist or album
- Download all albums of an artist (one folder per album)
- Download all songs of an artist
- Download all playlists, albums, and JioSaavn Originals/podcasts from your profile
- Clone your library to a new account (created by the script) or to an existing account
- Create a new account

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run this in the project folder:

```sh
uv sync
```

This installs Python 3.11 or newer and the dependencies into `.venv`.

## Usage

If a download fails at any point, run the same command again. Songs that were already downloaded are skipped.

### Download a song, playlist or album

Run the script and paste the URL when asked:

```sh
uv run main.py
```

Or pass the URL with `-u` / `--url`:

```sh
uv run main.py -u https://www.jiosaavn.com/album/tum-hi-aana-from-marjaavaan/j9bfphC2728_
```

To download many URLs at once, put them in a text file, one per line, and pass it with `-f` / `--file`:

```sh
uv run main.py -f urls.txt
```

### Download an artist

By default every album of the artist is downloaded into its own folder:

```sh
uv run main.py -u https://www.jiosaavn.com/artist/babbal-rai-albums/pRd5ZTGrLv8_
```

Add `-song` to download all of the artist's songs into a single folder instead:

```sh
uv run main.py -song -u https://www.jiosaavn.com/artist/babbal-rai-albums/pRd5ZTGrLv8_
```

### Output folder

Everything is downloaded into a `Downloads` folder next to `main.py`:

```
Downloads/
  Albums/<album> [id]/<song> [id].mp4
  Artists/<artist> [id]/<album> [id]/<song> [id].mp4
  Playlists/<playlist> [id]/<song> [id].mp4
  Shows/<show> [id]/Season 1/<episode> [id].mp4
  Songs/<song> [id].mp4
```

`[id]` is the JioSaavn ID, so songs and albums with the same name don't overwrite each other. With `-song`, an artist's songs go into `Artists/<artist> [id]/`.

Use `-o` / `--outFolder` to download somewhere else:

```sh
uv run main.py -o music
```

### Proxy

Set the `http_proxy` and `https_proxy` environment variables:

```sh
export https_proxy=http://127.0.0.1:8080
```

## Using your JioSaavn account

Sign in to the JioSaavn Android or iOS app at least once before using these commands. You will be asked for your email and password.

| Command | What it does |
| --- | --- |
| `uv run main.py -user -p` | Download all playlists from your profile |
| `uv run main.py -user -a` | Download all albums from your profile |
| `uv run main.py -user -s` | Download all shows and podcasts from your profile |
| `uv run main.py -user -create` | Create a new account |
| `uv run main.py -user -clone -create` | Clone your songs, albums and playlists to a new account created by the script |
| `uv run main.py -user -clone -copy` | Clone your songs, albums and playlists to an existing account |

When cloning, you are first asked for the account to copy from and then for the account to copy to.

You can also pass your email and password with `-e` / `--email` and `-pw` / `--password`:

```sh
uv run main.py -user -e YOUR_EMAIL -pw YOUR_PASSWORD -p
```

A password passed with `-pw` is saved in your shell history, so typing it at the prompt is safer.

### Dry run and limit

`--dry-run` shows what would be downloaded without downloading it. `--limit N` stops after N songs. Both work with any download command:

```sh
uv run main.py -user -p --dry-run
uv run main.py -user -p --limit 2
```

## Known issues

- Cloning doesn't work with the Saavn-Download-Reloaded package
- JioSaavn Originals and podcasts are downloaded without metadata

## Development

`uv sync` also installs pytest. Run the tests with `uv run pytest`. Tests that call the JioSaavn API only run when `SAAVN_LIVE=1` is set.

`tests/targets.py` has a few small songs, albums, playlists and artists to try changes on.

## License

[MIT](LICENSE)
