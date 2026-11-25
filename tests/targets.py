# JioSaavn pages to test against, picked to be small so a full download is quick.
# Used by the live tests, and handy for manual runs:
#   python main.py -o <scratch folder> -u <url>
# Sizes were checked on 2026-11-25.

# 1 song, about 13 MB
SONG_URL = "https://www.jiosaavn.com/song/dekha-ek-khwab/QVsJYCJYAV0"
SONG_ID = "13bQVh6n"

# 1 song
ALBUM_URL = "https://www.jiosaavn.com/album/kuch-bhi-ho-jaye/2EvVc5JXg3I_"
ALBUM_ID = "19805392"

# 3 songs
PLAYLIST_URL = "https://www.jiosaavn.com/featured/artist-hits-lyrical-folk/C1hi-Wx5hCy5MW-661Z5Dg__"
PLAYLIST_ID = "1268982627"

# 2 albums with 40 songs in total, 2 songs with -song.
# Both albums have songs with the same title, and -song gives two songs with the
# same title, which is a good check that nothing gets overwritten.
ARTIST_URL = "https://www.jiosaavn.com/artist/piano-tecontrol-breath-controller-alto-sax-ajay-singha-songs/OFn9qtzZpXE_"
ARTIST_ID = "7867165"

# Big ones, fine for metadata tests but too large to download.
BIG_PLAYLIST_URL = "https://www.jiosaavn.com/featured/90s-king---kumar-sanu/QeBmhG7Y1uE_"  # 50 songs
BIG_PLAYLIST_ID = "39416670"
BIG_ARTIST_URL = "https://www.jiosaavn.com/artist/udit-narayan-songs/kLtmb7Vh8Rs_"  # hundreds of albums
BIG_ARTIST_ID = "455127"

# A public podcast, so show code can be checked without logging in.
SHOW_ID = "333060"

# Pages that don't exist.
MISSING_URLS = {
    "album": "https://www.jiosaavn.com/album/x/zzzzzzzzzzzz",
    "playlist": "https://www.jiosaavn.com/featured/x/zzzzzzzzzzzz",
    "artist": "https://www.jiosaavn.com/artist/x/zzzzzzzzzzzz",
    "song": "https://www.jiosaavn.com/song/x/zzzzzzzzzzzz",
}
