import pytest

from scripts.content.song import Song

pytestmark = pytest.mark.live
URL = "https://www.jiosaavn.com/song/dekha-ek-khwab/QVsJYCJYAV0"


def test_get_song_id(session, manager):
    assert Song(session, manager).get_song_id(URL) == "13bQVh6n"


def test_get_song(session, manager):
    song = Song(session, manager).get_song("13bQVh6n")
    assert song["more_info"]["encrypted_media_url"]
