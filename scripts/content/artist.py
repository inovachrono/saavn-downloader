import math

from .album import Album
from ..download_manager import ARTISTS
from ..helper import RECOVERABLE_ERRORS, SaavnError, api_get, webapi_get

PAGE_SIZE = 10


class Artist:
    def __init__(self, session, manager, songs_only=False):
        self.session = session
        self.manager = manager
        self.songs_only = songs_only

    def get_artist_id(self, url):
        data = webapi_get(self.session, url, "artist", p="", n_song=10, n_album=14,
                          sub_type="", category="", sort_order="")
        if not data.get("artistId"):
            raise SaavnError(f"Could not find an artist at {url}")
        return str(data["artistId"])

    def get_artist_page(self, artist_id, **params):
        return api_get(self.session, "artist.getArtistPageDetails", artistId=artist_id, **params)

    def get_album_ids(self, artist_id, total_albums):
        album_ids = []
        for page in range(math.ceil(total_albums / PAGE_SIZE)):
            print(f"Getting album page {page + 1}")
            data = self.get_artist_page(artist_id, n_album=PAGE_SIZE, page=page)
            album_ids.extend(album["albumid"] for album in data["topAlbums"]["albums"])
        return album_ids

    def download_all_albums(self, artist_id, artist):
        total = int(artist["topAlbums"]["total"])
        print(f"Total albums of the artist: {total}")
        album_ids = self.get_album_ids(artist_id, total)
        print(f"Albums found: {len(album_ids)}")
        artist_folder = self.manager.with_id(artist.get("name"), artist_id)
        album = Album(self.session, self.manager)
        for album_id in album_ids:
            try:
                album.download_album(album_id, parent=(ARTISTS, artist_folder))
            except RECOVERABLE_ERRORS as e:
                self.manager.record_failure(f"Error getting album with ID {album_id}: {e}")

    def download_all_songs(self, artist_id, artist):
        total = int(artist["topSongs"]["total"])
        print(f"Total songs of the artist: {total}")
        artist_folder = self.manager.with_id(artist.get("name"), artist_id)
        for page in range(math.ceil(total / PAGE_SIZE)):
            print(f"Getting song page {page + 1}")
            try:
                data = self.get_artist_page(artist_id, n_song=PAGE_SIZE, page=page)
                songs = data["topSongs"]["songs"]
            except RECOVERABLE_ERRORS as e:
                self.manager.record_failure(f"Error getting song page {page + 1}: {e}")
                continue
            self.manager.download_songs(songs, ARTISTS, artist_folder)

    def start_download(self, url):
        artist_id = self.get_artist_id(url)
        artist = self.get_artist_page(artist_id)
        if self.songs_only:
            print("Downloading all songs of the artist")
            self.download_all_songs(artist_id, artist)
        else:
            print("Downloading all albums of the artist")
            self.download_all_albums(artist_id, artist)
