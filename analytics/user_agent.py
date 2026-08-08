"""
analytics/user_agent.py

A small, dependency-free user-agent parser.

Deliberately NOT using a third-party library (e.g. user-agents,
httpagentparser): the portfolio site needs to stay lightweight, and a
handful of regexes covers the browsers/OSes/devices that matter for a
personal-portfolio audience. Good enough for reporting purposes; not
intended to be a byte-perfect UA parser.
"""

import re

MAX_UA_LENGTH = 500  # defensive cap — user-agent strings are attacker-controlled input

_BROWSER_PATTERNS = [
    ('Edge',            re.compile(r'Edg(?:A|iOS)?/', re.I)),
    ('Opera',           re.compile(r'OPR/|Opera/', re.I)),
    ('Samsung Internet', re.compile(r'SamsungBrowser/', re.I)),
    ('Chrome',          re.compile(r'Chrome/|CriOS/', re.I)),
    ('Firefox',         re.compile(r'Firefox/|FxiOS/', re.I)),
    ('Safari',          re.compile(r'Safari/', re.I)),
    ('Internet Explorer', re.compile(r'MSIE |Trident/', re.I)),
]

_OS_PATTERNS = [
    ('iOS',       re.compile(r'iPhone|iPad|iPod', re.I)),
    ('Android',   re.compile(r'Android', re.I)),
    ('Windows',   re.compile(r'Windows NT', re.I)),
    ('macOS',     re.compile(r'Mac OS X', re.I)),
    ('Linux',     re.compile(r'Linux', re.I)),
    ('Chrome OS', re.compile(r'CrOS', re.I)),
]

_TABLET_HINTS = re.compile(r'iPad|Tablet|Nexus 7|Nexus 9|Nexus 10|KFAPWI', re.I)
_MOBILE_HINTS = re.compile(r'Mobi|iPhone|iPod|Android(?!.*Tablet)|BlackBerry|Windows Phone', re.I)


def parse_user_agent(ua_string):
    """
    Returns a dict: {'browser': str, 'os': str, 'device_type': str}
    device_type is one of: 'desktop', 'mobile', 'tablet', 'other'.
    Never raises — malformed/empty input degrades to 'Unknown'/'other'.
    """
    ua = (ua_string or '')[:MAX_UA_LENGTH]

    if not ua.strip():
        return {'browser': 'Unknown', 'os': 'Unknown', 'device_type': 'other'}

    browser = next((name for name, pattern in _BROWSER_PATTERNS if pattern.search(ua)), 'Other')
    os_name = next((name for name, pattern in _OS_PATTERNS if pattern.search(ua)), 'Other')

    if _TABLET_HINTS.search(ua):
        device_type = 'tablet'
    elif _MOBILE_HINTS.search(ua):
        device_type = 'mobile'
    elif ua.strip():
        device_type = 'desktop'
    else:
        device_type = 'other'

    return {'browser': browser, 'os': os_name, 'device_type': device_type}
