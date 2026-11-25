from ..download_manager import SONGS, has_320, tags_from_song_details
from ..helper import ANDROID_PARAMS, SaavnError, api_post, webapi_get


class Song:
    def __init__(self, session, manager):
        self.session = session
        self.manager = manager

    def get_song_id(self, url):
        data = webapi_get(self.session, url, "song")
        songs = data.get("songs") if isinstance(data, dict) else None
        if not songs:
            raise SaavnError(f"Could not find a song at {url}")
        return songs[0]["id"]

    def get_song(self, song_id):
        data = api_post(self.session, {**ANDROID_PARAMS, "__call": "song.getDetails", "pids": song_id})
        if song_id not in data:
            raise SaavnError(f"No song found with ID {song_id}")
        return data[song_id]

    def download_song(self, song_id):
        song = self.get_song(song_id)
        dec_url = self.manager.decrypt_url(song["more_info"]["encrypted_media_url"], has_320(song["more_info"]))
        filename = self.manager.format_filename(song["title"], song_id)
        location = self.manager.get_download_location(SONGS, filename=filename)
        self.manager.download(filename, location, dec_url, tags_from_song_details(song))

    def start_download(self, url):
        self.download_song(self.get_song_id(url))
