"""
analytics/utils.py

Small shared helpers used by the middleware, the tracking endpoint,
and the dashboard.
"""

import hashlib
import re

from django.conf import settings

# Any additional pepper beyond SECRET_KEY. Not required to be secret
# on its own (SECRET_KEY already is), but keeps the hash distinct
# from any other use of SECRET_KEY-based hashing elsewhere.
_IP_HASH_SALT = 'portfolio-analytics-v1'

# Paths that should never be tracked as page visits, even though they
# don't fall under /admin/, /static/ or /media/.
EXCLUDED_PATH_PREFIXES = (
    '/admin/',
    '/static/',
    '/media/',
    '/analytics/',
)
EXCLUDED_EXACT_PATHS = (
    '/robots.txt',
    '/sitemap.xml',
    '/favicon.ico',
)
# Anything with a file-like extension (fonts, images, etc. served outside
# /static/ or /media/ for some reason, XHR/JSON endpoints, etc.)
_FILE_EXTENSION_RE = re.compile(r'\.[a-zA-Z0-9]{1,5}$')

# The contact page's own AJAX/JSON helper endpoint shouldn't count as a
# page view — the /contact/ page load itself is already tracked.
EXCLUDED_EXACT_SUFFIXES = (
    '/contact/form-timestamp/',
)


def hash_ip(ip_address):
    """
    One-way, salted hash of a client IP address. Truncated to 32 hex
    chars (128 bits) — plenty of collision resistance for a personal
    portfolio's traffic volume, while keeping stored rows small.
    Never store the raw IP anywhere.
    """
    if not ip_address:
        return ''
    secret = getattr(settings, 'SECRET_KEY', '')
    digest = hashlib.sha256(f"{_IP_HASH_SALT}:{secret}:{ip_address}".encode('utf-8')).hexdigest()
    return digest[:32]


def get_client_ip(request):
    """
    Best-effort client IP extraction. Trusts X-Forwarded-For only for
    its first entry (the original client), which is the conventional
    reverse-proxy convention (PythonAnywhere included). Used only to
    compute ip_hash — never stored or logged raw.
    """
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def should_track_path(path):
    """True if a request path should generate a PageVisit row."""
    if path in EXCLUDED_EXACT_PATHS:
        return False
    if any(path.endswith(suffix) for suffix in EXCLUDED_EXACT_SUFFIXES):
        return False
    if any(path.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES):
        return False
    if _FILE_EXTENSION_RE.search(path):
        return False
    return True
