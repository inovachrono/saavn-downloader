import pytest

from scripts.content.artist import Artist

pytestmark = pytest.mark.live
URL = "https://www.jiosaavn.com/artist/udit-narayan-songs/kLtmb7Vh8Rs_"


def test_get_artist_id(session, manager):
    assert Artist(session, manager).get_artist_id(URL) == "455127"


def test_get_album_ids(session, manager):
    album_ids = Artist(session, manager).get_album_ids("455127", total_albums=20)
    assert len(album_ids) == 20
