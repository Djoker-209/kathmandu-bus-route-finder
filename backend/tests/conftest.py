"""
pytest loads conftest.py before collecting any test module in this
directory -- this is the one place we can guarantee ADMIN_API_KEY is set
before app.core.config.Settings() is constructed (it has no default, by
design -- see app/core/config.py). Real environments (CI, docker-compose)
should set a real ADMIN_API_KEY themselves; this is a test-only fallback
so `pytest` works out of the box for anyone who hasn't set one up yet.
"""

import os

os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")