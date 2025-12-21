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

    lowered = raw.lower()
    if lowered.startswith(("javascript:", "data:", "vbscript:", "mailto:")):
        return None

    try:
        parsed = urlparse(raw)
        if not parsed.scheme:
            parsed = urlparse("https://" + raw)

        if parsed.scheme not in ("http", "https"):
            return None

        if not parsed.netloc:
            return None

        return urlunparse((parsed.scheme, parsed.netloc, parsed.path or "", "", "", ""))
    except Exception:
        return None
