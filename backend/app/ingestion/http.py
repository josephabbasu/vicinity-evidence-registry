from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


def request_bytes(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    attempts: int = 3,
) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "VICINITY-Living-Evidence/3.0", **(headers or {})},
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_headers = {
                    key.casefold(): value for key, value in response.headers.items()
                }
                return response.read(), response_headers
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = min(float(retry_after or (attempt + 1)), 10.0)
            time.sleep(delay)
        except urllib.error.URLError:
            if attempt == attempts - 1:
                raise
            time.sleep(attempt + 1)
    raise RuntimeError("HTTP request failed without an exception.")


def request_json(
    url: str,
    headers: dict[str, str] | None = None,
) -> tuple[Any, dict[str, str]]:
    body, response_headers = request_bytes(url, headers=headers)
    return json.loads(body.decode("utf-8")), response_headers

