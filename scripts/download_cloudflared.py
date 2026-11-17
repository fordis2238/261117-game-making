"""Download Cloudflare's official Windows x64 public-sharing executable."""
import platform
import urllib.request
from pathlib import Path

if platform.system() != 'Windows' or platform.machine().lower() not in ('amd64', 'x86_64'):
    raise SystemExit('This helper targets Windows x64. Download your platform from https://developers.cloudflare.com/tunnel/downloads/')

destination = Path(__file__).resolve().parents[1] / 'jump-game/tools/cloudflared.exe'
destination.parent.mkdir(parents=True, exist_ok=True)
url = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'
temporary = destination.with_suffix('.download')
try:
    urllib.request.urlretrieve(url, temporary)
    if temporary.stat().st_size < 1000000:
        raise RuntimeError('The download was unexpectedly small.')
    temporary.replace(destination)
finally:
    temporary.unlink(missing_ok=True)
print(destination)
