import os
from urllib.parse import urlparse

from ..download_manager import SHOWS
from ..helper import RECOVERABLE_ERRORS, api_get


class Podcast:
    def __init__(self, session, manager):
        self.session = session
        self.manager = manager

    def get_show(self, show_id):
        home = api_get(self.session, "show.getHomePage", show_id=show_id)
        seasons = {}
        for number, season in enumerate(home["seasons"], start=1):
            seasons[number] = api_get(
                self.session, "show.getAllEpisodes", season_number=number, show_id=show_id,
                n=season["more_info"]["numEpisodes"], sort_order="asc",
            )
        return seasons

    def download_show(self, show_id):
        seasons = self.get_show(show_id)
        episodes = [episode for season in seasons.values() for episode in season]
        if not episodes:
            print(f"No episodes found for show {show_id}")
            return
        show_name = episodes[0]["more_info"]["show_title"]
        print(f"Show: {show_name}")
        show_folder = self.manager.with_id(show_name, show_id)
        for number, season in seasons.items():
            season_name = f"Season {number}"
            print(season_name)
            for episode in season:
                try:
                    dec_url = self.manager.decrypt_url(episode["more_info"]["encrypted_media_url"])
                    # some shows are hosted elsewhere as mp3
                    ext = os.path.splitext(urlparse(dec_url).path)[1] or ".mp4"
                    filename = self.manager.format_filename(episode["title"], episode["id"], ext)
                    location = self.manager.get_download_location(SHOWS, show_folder, season_name, filename=filename)
                    # TODO: add tags for podcast episodes
                    self.manager.download(f"{show_name} - {season_name} - {filename}", location, dec_url)
                except RECOVERABLE_ERRORS as e:
                    self.manager.record_failure(f"Download error: {e}")

    def download_all(self, library_json):
        for show_id in library_json.get("show") or []:
            try:
                self.download_show(show_id)
            except RECOVERABLE_ERRORS as e:
                self.manager.record_failure(f"Error getting show {show_id}: {e}")
