from backend.app.utils.url_utils import normalize_website_url


def test_normalize_with_scheme():
    assert normalize_website_url('https://example.com') == 'https://example.com'
    assert normalize_website_url('http://example.com/path') == 'http://example.com/path'


def test_normalize_without_scheme():
    assert normalize_website_url('example.com') == 'https://example.com'
    assert normalize_website_url('www.example.com/page') == 'https://www.example.com/page'


def test_normalize_invalid_or_dangerous():
    assert normalize_website_url('') is None
    assert normalize_website_url(None) is None
    assert normalize_website_url('javascript:alert(1)') is None
    assert normalize_website_url('mailto:foo@example.com') is None
