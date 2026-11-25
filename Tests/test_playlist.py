import pytest

from scripts.content.playlist import Playlist

pytestmark = pytest.mark.live
URL = "https://www.jiosaavn.com/featured/90s-king---kumar-sanu/QeBmhG7Y1uE_"


def test_get_playlist_id(session, manager):
    assert Playlist(session, manager).get_playlist_id(URL) == "39416670"


def test_get_playlist(session, manager):
    playlist = Playlist(session, manager).get_playlist("39416670")
    assert isinstance(playlist["songs"], list)
