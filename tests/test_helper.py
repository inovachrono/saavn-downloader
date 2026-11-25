import pytest

from scripts import helper


@pytest.mark.parametrize("url, result", [
    ("https://www.jiosaavn.com/album/bewafai/y3DlZsa6XD0_", "album"),
    ("https://www.jiosaavn.com/featured/icons---mohd-rafi/HzNAgZVIJT4_", "playlist"),
    ("https://www.jiosaavn.com/artist/udit-narayan-songs/kLtmb7Vh8Rs_", "artist"),
    ("https://www.jiosaavn.com/song/psycho-saiyaan-from-saaho/B1EORCx4blc", "song"),
    ("https://example.com/whatever", None),
])
def test_scan_url(url, result):
    assert helper.scan_url(url) == result


def test_url_token_ignores_trailing_slash():
    assert helper.url_token("https://www.jiosaavn.com/album/bewafai/y3DlZsa6XD0_/") == "y3DlZsa6XD0_"


@pytest.mark.parametrize("name, expected", [
    ('Psycho *Saiyaan ?(From "Saaho")', "Psycho -Saiyaan -(From -Saaho-)"),
    ("AC/DC: Live", "AC-DC- Live"),
    ("trailing dot.", "trailing dot"),
    ("...", "_"),
])
def test_sanitize_name(name, expected):
    assert helper.sanitize_name(name) == expected


def test_parse_json_payload_skips_junk_lines():
    assert helper.parse_json_payload('<!-- junk -->\n  {"a": 1}\n') == {"a": 1}
    assert helper.parse_json_payload("noise\n[1, 2]") == [1, 2]


def test_parse_json_payload_raises_without_json():
    with pytest.raises(helper.SaavnError):
        helper.parse_json_payload("<html>error</html>")


def test_parse_args_does_not_read_sys_argv():
    args = helper.parse_args(["-u", "https://x", "-o", "out", "-song"])
    assert (args.url, args.outFolder, args.song, args.user) == ("https://x", "out", True, False)


def test_url_token_ignores_query_and_fragment():
    assert helper.url_token("https://www.jiosaavn.com/song/x/QVsJYCJYAV0?referrer=share#top") == "QVsJYCJYAV0"
