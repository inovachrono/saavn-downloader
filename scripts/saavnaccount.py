import getpass

from .content.album import Album
from .content.playlist import Playlist
from .content.podcast import Podcast
from .helper import (
    ANDROID_HEADERS, ANDROID_PARAMS, API_URL, RECOVERABLE_ERRORS,
    SaavnError, api_get, api_post, create_session, require_dict,
)


class Account:
    def __init__(self, session, manager, email, password):
        self.session = session
        self.manager = manager
        self.email = email
        self.password = password

    def _account_call(self, session, call, **fields):
        return api_post(session, {**ANDROID_PARAMS, "__call": call, **fields})

    def login(self, email=None, password=None):
        if email is None:
            email = self.email
        if password is None:
            password = self.password
        session = create_session(ANDROID_HEADERS)
        data = require_dict(self._account_call(session, "user.login", email=email, username=email,
                                               password=password, state="logout"), "login")
        if data.get("error") or not (data.get("data") or {}).get("uid"):
            raise SaavnError(f"Login failed for {email}: {data.get('error') or 'unexpected response'}")
        return session

    def logout(self, session):
        try:
            self._account_call(session, "user.logout", state="logout")
        except RECOVERABLE_ERRORS as e:
            print(f"Logout failed: {e}")

    def get_library(self, session):
        return api_get(session, "library.getAll", cc="", ctx="android", state="login",
                       v=224, app_version="6.8.2", api_version=4)

    def get_own_library(self):
        session = self.login()
        try:
            return self.get_library(session)
        finally:
            self.logout(session)

    def create_account(self, email, password):
        session = create_session(ANDROID_HEADERS)
        data = require_dict(self._account_call(session, "user.createV2", email=email, username=email,
                                               password=password, state="logout"), "account creation")
        if data.get("error"):
            print(f"Account creation failed: {data['error']}")
            return False
        return bool((data.get("data") or {}).get("uid"))

    def create_user(self):
        if not self.create_account(self.email, self.password):
            print("Failed to create account")
            return False
        try:
            # the library has to be read once to activate a new account
            self.get_own_library()
        except RECOVERABLE_ERRORS as e:
            print(f"Account created, but activating its library failed: {e}")
        print(f"\nSUCCESS\nAccount created for {self.email}")
        return True

    def clone(self, target_email, target_password, create_new):
        if create_new:
            if not self.create_account(target_email, target_password):
                print("Account creation failed")
                return False
            print("Account created successfully")

        source = self.login()
        target = None
        failures = 0
        try:
            target = self.login(target_email, target_password)
            library = self.get_library(source)
            self.get_library(target)

            web = create_session()
            web_login = api_post(web, {"username": target_email, "password": target_password},
                                 url=f"{API_URL}?__call=user.login&_marker=0&_format=json")
            if isinstance(web_login, dict) and web_login.get("error"):
                raise SaavnError(f"Web login failed for {target_email}: {web_login['error']}")

            for entity_type in ("song", "album"):
                ids = library.get(entity_type) or []
                print(f"Adding {len(ids)} {entity_type}s to the target account")
                for entity_id in ids:
                    try:
                        result = api_get(web, "library.add", entity_type=entity_type, entity_ids=entity_id)
                        if isinstance(result, dict) and result.get("error"):
                            raise SaavnError(result["error"])
                    except RECOVERABLE_ERRORS as e:
                        failures += 1
                        print(f"Could not add {entity_type} {entity_id}: {e}")

            playlists = library.get("playlist") or []
            print(f"Copying {len(playlists)} playlists to the target account")
            for playlist in playlists:
                try:
                    details = api_get(self.session, "playlist.getDetails", listid=playlist["id"])
                    result = self._account_call(target, "playlist.copyPlaylist", state="login",
                                                destListName=details["listname"], srcListId=playlist["id"])
                    if isinstance(result, dict) and result.get("error"):
                        raise SaavnError(result["error"])
                except RECOVERABLE_ERRORS as e:
                    failures += 1
                    print(f"Could not copy playlist {playlist.get('id')}: {e}")
        finally:
            self.logout(source)
            if target is not None:
                self.logout(target)

        if failures:
            print(f"{failures} items could not be copied")
        return failures == 0

    def clone_interactive(self, create_new):
        label = "new account" if create_new else "account to copy into"
        target_email = input(f"Enter the email of the {label} (TO): ").strip()
        target_password = getpass.getpass(f"Enter the password of the {label} (TO): ")
        if self.clone(target_email, target_password, create_new):
            print(f"Cloned library into {target_email}")
            return True
        print("Error: failed to clone account")
        return False

    def download_playlists(self):
        playlists = self.get_own_library().get("playlist") or []
        print(f"Playlists found: {len(playlists)}")
        downloader = Playlist(self.session, self.manager)
        for playlist in playlists:
            try:
                downloader.download_playlist(playlist["id"])
            except RECOVERABLE_ERRORS as e:
                self.manager.record_failure(f"Error getting playlist {playlist.get('id')}: {e}")

    def download_albums(self):
        album_ids = self.get_own_library().get("album") or []
        print(f"Albums found: {len(album_ids)}")
        downloader = Album(self.session, self.manager)
        for album_id in album_ids:
            try:
                downloader.download_album(album_id)
            except RECOVERABLE_ERRORS as e:
                self.manager.record_failure(f"Error getting album with ID {album_id}: {e}")

    def download_shows(self):
        Podcast(self.session, self.manager).download_all(self.get_own_library())
