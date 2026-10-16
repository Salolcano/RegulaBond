"""Pre-deployment public-source probe for RegulaBond.

Usage: python scripts/source_probe.py https://www.federalregister.gov/documents/YYYY/MM/DD/example
This checks basic public reachability only; Studio validators must still be tested.
"""
import sys
from urllib.request import Request, urlopen

PREFIX = "https://www.federalregister.gov/documents/"

if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/source_probe.py <official-Federal-Register-URL>")
url = sys.argv[1]
if not url.startswith(PREFIX) or len(url) > 240 or "#" in url or " " in url:
    raise SystemExit("Rejected: URL must use the allowed official Federal Register prefix")
request = Request(url, headers={"User-Agent": "RegulaBond-source-probe/0.1 (pre-deployment check)"})
try:
    with urlopen(request, timeout=20) as response:
        body = response.read(50001)
        print({"status": response.status, "content_type": response.headers.get("Content-Type"), "bytes_read": len(body), "within_contract_limit": len(body) <= 50000})
        if response.status != 200:
            raise SystemExit("Source probe failed: expected HTTP 200")
except Exception as exc:
    raise SystemExit(f"Source probe failed: {exc}")
