# Simulate getting artist metadata to see if top tracks are included
# Required: qobuz-dl must be installed or in path. Since we are in dev, we can use qobuz-dl directly if installed,
# or emulate the client call if we had the client code.
# Checking qobuz_dl/client.py (which I haven't seen yet but is imported in core.py) would be useful.
# But I can't call the API without credentials.
# I will assume I need to find where `get_artist_meta` is defined.
# logic in core.py lines 116-119 uses `self.client.get_artist_meta`.

from qobuz_dl.core import QobuzDL

print(QobuzDL.search_by_type)
