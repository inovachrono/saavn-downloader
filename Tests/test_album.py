import pytest

from scripts.content.album import Album

pytestmark = pytest.mark.live
URL = "https://www.jiosaavn.com/album/kuch-bhi-ho-jaye/2EvVc5JXg3I_"


def test_get_album_id(session, manager):
    assert Album(session, manager).get_album_id(URL) == "19805392"


def test_get_album(session, manager):
    album = Album(session, manager).get_album("19805392")
    assert isinstance(album["songs"], list)
    assert isinstance(album["name"], str)
