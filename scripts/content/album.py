import html

from ..download_manager import ALBUMS
from ..helper import SaavnError, api_get, webapi_get


class Album:
    def __init__(self, session, manager):
        self.session = session
        self.manager = manager

    def get_album_id(self, url):
        data = webapi_get(self.session, url, "album")
        if "id" not in data:
            raise SaavnError(f"Could not find an album at {url}")
        return str(data["id"])

    def get_album(self, album_id):
        album = api_get(self.session, "content.getAlbumDetails", albumid=album_id)
        if "songs" not in album:
            raise SaavnError(f"No album found with ID {album_id}")
        return album

    def download_album(self, album_id, parent=(ALBUMS,)):
        album = self.get_album(album_id)
        print(f"Album name: {html.unescape(album.get('name', album_id))}")
        folder = self.manager.with_id(album.get("name"), album_id)
        self.manager.download_songs(album["songs"], *parent, folder)

    def start_download(self, url):
        self.download_album(self.get_album_id(url))
