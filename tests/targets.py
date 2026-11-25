# small pages for the live tests and manual runs:
#   python main.py -o <folder> -u <url>

# 1 song, about 13 MB
SONG_URL = "https://www.jiosaavn.com/song/dekha-ek-khwab/QVsJYCJYAV0"
SONG_ID = "13bQVh6n"

# 1 song
ALBUM_URL = "https://www.jiosaavn.com/album/kuch-bhi-ho-jaye/2EvVc5JXg3I_"
ALBUM_ID = "19805392"

# 3 songs
PLAYLIST_URL = "https://www.jiosaavn.com/featured/artist-hits-lyrical-folk/C1hi-Wx5hCy5MW-661Z5Dg__"
PLAYLIST_ID = "1268982627"

# 2 albums, 40 songs (2 with -song); has songs with the same title
ARTIST_URL = "https://www.jiosaavn.com/artist/piano-tecontrol-breath-controller-alto-sax-ajay-singha-songs/OFn9qtzZpXE_"
ARTIST_ID = "7867165"

# too big to download
BIG_PLAYLIST_URL = "https://www.jiosaavn.com/featured/90s-king---kumar-sanu/QeBmhG7Y1uE_"  # 50 songs
BIG_PLAYLIST_ID = "39416670"
BIG_ARTIST_URL = "https://www.jiosaavn.com/artist/udit-narayan-songs/kLtmb7Vh8Rs_"  # hundreds of albums
BIG_ARTIST_ID = "455127"

# public podcast, no login needed
SHOW_ID = "333060"

MISSING_URLS = {
    "album": "https://www.jiosaavn.com/album/x/zzzzzzzzzzzz",
    "playlist": "https://www.jiosaavn.com/featured/x/zzzzzzzzzzzz",
    "artist": "https://www.jiosaavn.com/artist/x/zzzzzzzzzzzz",
    "song": "https://www.jiosaavn.com/song/x/zzzzzzzzzzzz",
}
