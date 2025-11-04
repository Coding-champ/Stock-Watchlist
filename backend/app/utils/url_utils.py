from typing import Optional
from urllib.parse import urlparse, urlunparse


def normalize_website_url(url: Optional[str]) -> Optional[str]:
    """Normalize a website/IR URL for safe display.

    - Returns None for empty/invalid/dangerous inputs (javascript:, mailto:, data: etc.)
    - Ensures a scheme (https) if missing
    - Preserves path but strips query and fragment for safety
    """
    if not url:
        return None

    raw = str(url).strip()
    if not raw:
        return None

    # quick reject for dangerous schemes
    lowered = raw.lower()
    for bad in ("javascript:", "data:", "vbscript:", "mailto:"):
        if lowered.startswith(bad):
            return None

    # add scheme if missing
    parsed = urlparse(raw, scheme='')
    if not parsed.scheme:
        # if it looks like domain without scheme, prepend https://
        raw = 'https://' + raw
        parsed = urlparse(raw)

    # only allow http/https
    if parsed.scheme not in ('http', 'https'):
        return None

    # rebuild URL without params/query/fragment for safety
    safe = urlunparse((parsed.scheme, parsed.netloc, parsed.path or '', '', '', ''))
    return safe
from typing import Optional
from urllib.parse import urlparse, urlunparse


def normalize_website_url(url: Optional[str]) -> Optional[str]:
    """Normalize and validate a website URL.

    - Strips whitespace
    - Returns None for empty or clearly invalid values
    - Adds https:// if scheme missing
    - Rejects javascript:, data:, mailto: and other non-http(s) schemes
    """
    if not url:
        return None

    try:
        u = url.strip()
        if not u:
            return None

        # Reject dangerous or non-http schemes
        lowered = u.lower()
        if lowered.startswith(('javascript:', 'data:', 'mailto:')):
            return None

        parsed = urlparse(u)

        # If no scheme provided, assume https
        if not parsed.scheme:
            u = 'https://' + u
            parsed = urlparse(u)

        # Only allow http/https
        if parsed.scheme not in ('http', 'https'):
            return None

        # Ensure there's a network location
        if not parsed.netloc:
            return None

        # Rebuild a cleaned URL without params/fragments.
        # Do not force a trailing slash for bare domains — preserve path if provided.
        path = parsed.path or ''
        cleaned = urlunparse((parsed.scheme, parsed.netloc, path, '', '', ''))
        return cleaned
    except Exception:
        return None
