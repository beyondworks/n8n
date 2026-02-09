"""SSL context helper.

Some Python distributions on macOS don't ship a working default CA bundle
out of the box, which breaks HTTPS requests made via urllib.

We prefer certifi's CA bundle when available, and fall back to the default
SSL context otherwise.
"""

from __future__ import annotations

import ssl


def get_ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore

        cafile = certifi.where()
        return ssl.create_default_context(cafile=cafile)
    except Exception:
        return ssl.create_default_context()

