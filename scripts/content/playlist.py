import html

from ..download_manager import PLAYLISTS
from ..helper import SaavnError, api_get, webapi_get


class Playlist:
    def __init__(self, session, manager):
        self.session = session
        self.manager = manager

    def get_playlist_id(self, url):
        data = webapi_get(self.session, url, "playlist", p=1, n=20)
        if not data.get("id"):
            raise SaavnError(f"Could not find a playlist at {url}")
        return str(data["id"])

    def get_playlist(self, playlist_id):
        playlist = api_get(self.session, "playlist.getDetails", listid=playlist_id)
        if "songs" not in playlist:
            raise SaavnError(f"No playlist found with ID {playlist_id}")
        return playlist

    def download_playlist(self, playlist_id):
        playlist = self.get_playlist(playlist_id)
        print(f"Playlist: {html.unescape(playlist.get('listname', playlist_id))}")
        folder = self.manager.with_id(playlist.get("listname"), playlist_id)
        self.manager.download_songs(playlist["songs"], PLAYLISTS, folder)

    def start_download(self, url):
        self.download_playlist(self.get_playlist_id(url))
