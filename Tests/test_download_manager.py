import os

import pytest
import requests

from scripts import helper
from scripts.download_manager import tags_from_list_song, tags_from_song_details


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
