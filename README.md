# Saavn Downloader

Download songs, albums, playlists and artists from JioSaavn in high quality (320 kbps MP4) with metadata.

## Features

- Download a single song, playlist or album
- Download all albums of an artist (one folder per album)
- Download all songs of an artist
- Download all playlists, albums, and JioSaavn Originals/podcasts from your profile
- Clone your library to a new account (created by the script) or to an existing account
- Create a new account

## Installation

Requires Python 3.10 or newer.

```sh
pip install -r requirements.txt
```

## Usage

If a download fails at any point, run the same command again. Songs that were already downloaded are skipped.

### Download a song, playlist or album

Run the script and paste the URL when asked:

```sh
python main.py
```

Or pass the URL with `-u` / `--url`:

```sh
python main.py -u https://www.jiosaavn.com/album/tum-hi-aana-from-marjaavaan/j9bfphC2728_
```

To download many URLs at once, put them in a text file, one per line, and pass it with `-f` / `--file`:

```sh
python main.py -f urls.txt
```

### Download an artist

By default every album of the artist is downloaded into its own folder:

```sh
python main.py -u https://www.jiosaavn.com/artist/babbal-rai-albums/pRd5ZTGrLv8_
```

Add `-song` to download all of the artist's songs into a single folder instead:

```sh
python main.py -song -u https://www.jiosaavn.com/artist/babbal-rai-albums/pRd5ZTGrLv8_
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

The `[id]` is the JioSaavn ID, so albums and songs that share a name never overwrite each other. With `-song`, an artist's songs go straight into `Artists/<artist> [id]/`.

Use `-o` / `--outFolder` to download somewhere else:

```sh
python main.py -o music
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
| `python main.py -user -p` | Download all playlists from your profile |
| `python main.py -user -a` | Download all albums from your profile |
| `python main.py -user -s` | Download all shows and podcasts from your profile |
| `python main.py -user -create` | Create a new account |
| `python main.py -user -clone -create` | Clone your songs, albums and playlists to a new account created by the script |
| `python main.py -user -clone -copy` | Clone your songs, albums and playlists to an existing account |

When cloning, you are first asked for the account to copy from and then for the account to copy to.

You can also pass your email and password with `-e` / `--email` and `-pw` / `--password`:

```sh
python main.py -user -e YOUR_EMAIL -pw YOUR_PASSWORD -p
```

A password passed with `-pw` is saved in your shell history, so typing it at the prompt is safer.

## Known issues

- Cloning doesn't work with the Saavn-Download-Reloaded package
- Songs that aren't available in 320 kbps don't get their metadata added
- JioSaavn Originals and podcasts are downloaded without metadata

## Development

Run the tests with `pytest`. Tests that call the JioSaavn API only run when `SAAVN_LIVE=1` is set.

`tests/targets.py` lists small songs, albums, playlists and artists that are quick to download when trying out changes by hand.

## License

[MIT](LICENSE)
