import pytest

import targets
from scripts.content.album import Album
from scripts.content.artist import Artist
from scripts.content.playlist import Playlist
from scripts.content.podcast import Podcast
from scripts.content.song import Song
from scripts.helper import SaavnError

pytestmark = pytest.mark.live


def test_song(session, manager):
    song = Song(session, manager)
    assert song.get_song_id(targets.SONG_URL) == targets.SONG_ID
    assert song.get_song(targets.SONG_ID)["more_info"]["encrypted_media_url"]


def test_album(session, manager):
    album = Album(session, manager)
    assert album.get_album_id(targets.ALBUM_URL) == targets.ALBUM_ID
    songs = album.get_album(targets.ALBUM_ID)["songs"]
    assert songs and all(s["id"] for s in songs)


def test_playlist(session, manager):
    playlist = Playlist(session, manager)
    assert playlist.get_playlist_id(targets.PLAYLIST_URL) == targets.PLAYLIST_ID
    assert playlist.get_playlist(targets.PLAYLIST_ID)["songs"]
    assert playlist.get_playlist_id(targets.BIG_PLAYLIST_URL) == targets.BIG_PLAYLIST_ID


def test_artist(session, manager):
    artist = Artist(session, manager)
    assert artist.get_artist_id(targets.ARTIST_URL) == targets.ARTIST_ID
    assert artist.get_artist_id(targets.BIG_ARTIST_URL) == targets.BIG_ARTIST_ID
    assert len(artist.get_album_ids(targets.BIG_ARTIST_ID, total_albums=20)) == 20


def test_show(session, manager):
    seasons = Podcast(session, manager).get_show(targets.SHOW_ID)
    episodes = [episode for season in seasons.values() for episode in season]
    assert episodes and all(e["id"] and e["more_info"]["encrypted_media_url"] for e in episodes)


@pytest.mark.parametrize("kind, cls, method", [
    ("album", Album, "get_album_id"),
    ("playlist", Playlist, "get_playlist_id"),
    ("artist", Artist, "get_artist_id"),
    ("song", Song, "get_song_id"),
])
def test_missing_pages(session, manager, kind, cls, method):
    with pytest.raises(SaavnError, match="Could not find"):
        getattr(cls(session, manager), method)(targets.MISSING_URLS[kind])
