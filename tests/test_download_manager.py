import os

import pytest
import requests

from scripts import helper
from scripts.download_manager import LimitReached, has_320, tags_from_list_song, tags_from_song_details


class FakeResponse:
    def __init__(self, chunks, fail_after=None):
        self.chunks = chunks
        self.fail_after = fail_after
        self.headers = {"content-length": str(sum(len(c) for c in chunks))}

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        for i, chunk in enumerate(self.chunks):
            if self.fail_after is not None and i >= self.fail_after:
                raise requests.ConnectionError("connection dropped")
            yield chunk

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def get(self, url, stream=False, timeout=None):
        self.calls += 1
        return self.response


def test_decrypt_url(manager):
    enc_url = "ID2ieOjCrwfgWvL5sXl4B1ImC5QfbsDy9OyCHwmG0FcgA1ieF26kd4Vm/WhQL0FHWbLZmxKh9EBgAPgqc99pQBw7tS9a8Gtq"
    assert manager.decrypt_url(enc_url) == "https://aac.saavncdn.com/274/5ec5d630172f4cf8e143fe7ec8fc816d_320.mp4"


def test_format_filename(manager):
    filename = manager.format_filename("Psycho *Saiyaan ?(From &quot;Saaho&quot;)", "B1EORCx4blc")
    assert filename == "Psycho -Saiyaan -(From -Saaho-) [B1EORCx4blc].mp4"


def test_with_id(manager):
    assert manager.with_id("Album: Part 1/2", "123") == "Album- Part 1-2 [123]"
    assert manager.with_id(None, "123") == "Unknown [123]"


def test_get_download_location(manager, tmp_path):
    location = manager.get_download_location("Albums", "Aashiqui 2 [1139549]", filename="Tum Hi Ho [x].mp4")
    assert location == os.path.join(str(tmp_path), "Albums", "Aashiqui 2 [1139549]", "Tum Hi Ho [x].mp4")


def test_songs_with_the_same_name_get_separate_files(manager, tmp_path):
    manager.session = FakeSession(FakeResponse([b"audio"]))
    enc_url = "ID2ieOjCrwfgWvL5sXl4B1ImC5QfbsDy9OyCHwmG0FcgA1ieF26kd4Vm/WhQL0FHWbLZmxKh9EBgAPgqc99pQBw7tS9a8Gtq"
    songs = [
        {"id": "aaa", "song": "Intro", "encrypted_media_url": enc_url},
        {"id": "bbb", "song": "Intro", "encrypted_media_url": enc_url},
    ]
    manager.download_songs(songs, "Albums", "Greatest Hits [1]")
    folder = tmp_path / "Albums" / "Greatest Hits [1]"
    assert sorted(os.listdir(folder)) == ["Intro [aaa].mp4", "Intro [bbb].mp4"]


def test_download_completes_via_part_file(manager, tmp_path):
    manager.session = FakeSession(FakeResponse([b"abc", b"def"]))
    location = os.path.join(str(tmp_path), "a", "song.mp4")
    assert manager.download("song", location, "https://cdn/x.mp4") is True
    with open(location, "rb") as f:
        assert f.read() == b"abcdef"
    assert not os.path.exists(location + ".part")
    assert manager.download("song", location, "https://cdn/x.mp4") is False


def test_interrupted_download_is_not_treated_as_finished(manager, tmp_path):
    session = FakeSession(FakeResponse([b"abc", b"def"], fail_after=1))
    manager.session = session
    location = os.path.join(str(tmp_path), "song.mp4")
    with pytest.raises(helper.SaavnError):
        manager.download("song", location, "https://cdn/x.mp4")
    assert not os.path.exists(location)
    assert session.calls == 4


def test_tags_from_list_song_splits_names():
    tags = tags_from_list_song({
        "song": "Tum Hi Ho", "primary_artists": "Arijit Singh, Mithoon", "music": "Mithoon",
        "starring": "", "album": "Aashiqui 2", "label": "T-Series", "year": "2013",
    })
    assert tags["artists"] == ["Arijit Singh", "Mithoon"]
    assert tags["composers"] == ["Mithoon"]
    assert tags["starring"] == []
    assert tags["copyright"] == "T-Series"


def test_tags_from_song_details_music_fallback_is_not_split_into_letters():
    song = {
        "title": "Dekha Ek Khwab",
        "more_info": {
            "album": "Silsila",
            "music": "Shiv-Hari",
            "copyright_text": "(C) 1981",
            "label": "Saregama",
            "artistMap": {
                "primary_artists": [{"name": "Kishore Kumar"}],
                "artists": [{"name": "Amitabh Bachchan", "role": "starring"}],
            },
        },
    }
    tags = tags_from_song_details(song)
    assert tags["composers"] == ["Shiv-Hari"]
    assert tags["artists"] == ["Kishore Kumar"]
    assert tags["starring"] == ["Amitabh Bachchan"]
    assert tags["copyright"] == "(C) 1981"


def test_failures_are_counted(manager):
    manager.download_songs([{"song": "broken"}])
    assert manager.failures == 1


SONGS = [
    {"id": f"id{n}", "song": f"Song {n}",
     "encrypted_media_url": "ID2ieOjCrwfgWvL5sXl4B1ImC5QfbsDy9OyCHwmG0FcgA1ieF26kd4Vm/WhQL0FHWbLZmxKh9EBgAPgqc99pQBw7tS9a8Gtq"}
    for n in range(3)
]


def test_dry_run_downloads_nothing(manager, tmp_path):
    session = FakeSession(FakeResponse([b"audio"]))
    manager.session = session
    manager.dry_run = True
    manager.download_songs(SONGS, "Albums", "Test [1]")
    assert session.calls == 0
    assert not os.listdir(tmp_path)
    assert manager.count == 3


def test_limit_stops_after_n_songs(manager, tmp_path):
    manager.session = FakeSession(FakeResponse([b"audio"]))
    manager.limit = 2
    with pytest.raises(LimitReached):
        manager.download_songs(SONGS, "Albums", "Test [1]")
    assert len(os.listdir(tmp_path / "Albums" / "Test [1]")) == 2


class NotFoundResponse(FakeResponse):
    def __init__(self):
        super().__init__([])
        self.status_code = 404

    def raise_for_status(self):
        raise requests.HTTPError("404", response=self)


class No320Session:
    def __init__(self):
        self.urls = []

    def get(self, url, stream=False, timeout=None):
        self.urls.append(url)
        return NotFoundResponse() if "_320.mp4" in url else FakeResponse([b"audio"])


def test_has_320():
    assert has_320({"320kbps": "true"})
    assert not has_320({"320kbps": "false"})
    assert has_320({})


def test_decrypt_url_uses_160_without_320(manager):
    enc_url = SONGS[0]["encrypted_media_url"]
    assert manager.decrypt_url(enc_url, high_quality=False).endswith("_160.mp4")


def test_download_falls_back_to_160_when_320_is_missing(manager, tmp_path):
    session = No320Session()
    manager.session = session
    location = os.path.join(str(tmp_path), "song.mp4")
    assert manager.download("song", location, "https://cdn/x_320.mp4") is True
    assert session.urls == ["https://cdn/x_320.mp4", "https://cdn/x_160.mp4"]
    assert os.path.isfile(location)


class FakeMP4(dict):
    def __init__(self, path):
        super().__init__()

    def save(self):
        FakeMP4.saved = dict(self)


def test_album_artist_is_the_same_on_every_track(manager):
    seen = []
    manager.download = lambda label, location, url, tags: seen.append(tags)
    songs = [dict(SONGS[0], primary_artists="Singer A"), dict(SONGS[1], primary_artists="Singer B")]
    manager.download_songs(songs, "Albums", "Test [1]", album_artist="Laxmikant - Pyarelal")
    assert [t["album_artist"] for t in seen] == ["Laxmikant - Pyarelal"] * 2
    assert [t["artists"] for t in seen] == [["Singer A"], ["Singer B"]]


def test_add_tags_album_artist(manager, monkeypatch):
    monkeypatch.setattr("scripts.download_manager.MP4", FakeMP4)
    manager.add_tags("x.mp4", {"artists": ["Singer A"], "album_artist": "Laxmikant - Pyarelal"})
    assert FakeMP4.saved["aART"] == ["Laxmikant - Pyarelal"]
    assert FakeMP4.saved["\xa9ART"] == ["Singer A"]
    manager.add_tags("x.mp4", {"artists": ["Singer A"]})
    assert FakeMP4.saved["aART"] == ["Singer A"]


def test_album_tracks_are_numbered_in_order(manager):
    seen = []
    manager.download = lambda label, location, url, tags: seen.append(tags)
    manager.download_songs(SONGS, "Albums", "Test [1]", numbered=True)
    assert [t["track"] for t in seen] == [(1, 3), (2, 3), (3, 3)]
    seen.clear()
    manager.download_songs(SONGS, "Playlists", "Test [2]")
    assert all("track" not in t for t in seen)


def test_add_tags_track_number(manager, monkeypatch):
    monkeypatch.setattr("scripts.download_manager.MP4", FakeMP4)
    manager.add_tags("x.mp4", {"title": "Song", "track": (2, 7)})
    assert FakeMP4.saved["trkn"] == [(2, 7)]
