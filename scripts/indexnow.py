"""Notify IndexNow about deployed public content; dry-run unless explicitly submitted."""

import argparse
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ENDPOINT = "https://api.indexnow.org/indexnow"


def validate_manifest(value, origin):
    if value.get("version") != 1 or value.get("origin") != origin:
        raise ValueError("Discovery manifest version/origin mismatch")
    pages = value.get("pages")
    if not isinstance(pages, dict) or len(pages) > 10000:
        raise ValueError("Invalid discovery pages")
    for url, digest in pages.items():
        parsed = urlsplit(url)
        if (
            f"{parsed.scheme}://{parsed.netloc}" != origin
            or not parsed.path.startswith("/about/")
            or parsed.query
            or parsed.fragment
            or not re.fullmatch(r"[a-f0-9]{64}", str(digest))
        ):
            raise ValueError(
                "Manifest must contain public /about/ URLs and SHA256 digests"
            )
    return value


def changed_urls(previous, current):
    before = previous["pages"] if previous else {}
    after = current["pages"]
    return sorted(
        url for url in before.keys() | after.keys() if before.get(url) != after.get(url)
    )


def fetch(url):
    with urlopen(
        Request(url, headers={"User-Agent": "B4A-Discovery-Check/1.0"}), timeout=15
    ) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError(
                "Discovery resource must return HTTP 200 without redirects"
            )
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError("Discovery resource exceeds size limit")
        return body.decode("utf-8")


def publish(origin, key, state, submit=False):
    parsed = urlsplit(origin)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "IndexNow requires a public HTTPS origin without credentials or path"
        )
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if not re.fullmatch(r"[A-Za-z0-9-]{8,128}", key):
        raise ValueError("Invalid public IndexNow key")
    current = validate_manifest(
        json.loads(fetch(origin + "/discovery-manifest.json")), origin
    )
    previous = (
        validate_manifest(json.loads(state.read_text()), origin)
        if state.exists()
        else None
    )
    urls = changed_urls(previous, current)
    if not urls:
        print("IndexNow: no public content changes; no submission sent.")
        return
    if fetch(f"{origin}/{key}.txt").strip() != key:
        raise ValueError("Deployed IndexNow key file does not match")
    sitemap = ET.fromstring(fetch(origin + "/sitemap.xml"))
    listed = {
        entry.text
        for entry in sitemap.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    }
    if listed != set(current["pages"]):
        raise ValueError(
            "Sitemap and discovery manifest must list the same public pages"
        )
    for url in urls:
        if url in current["pages"]:
            html = fetch(url)
            if (
                f'<link rel="canonical" href="{url}"' not in html
                or "<h1>" not in html
                or 'content="noindex' in html
            ):
                raise ValueError("Public page is not an indexable canonical document")
        else:
            try:
                fetch(url)
            except HTTPError as error:
                if error.code not in (404, 410):
                    raise
            else:
                raise ValueError("Removed public URL must return HTTP 404 or 410")
    print(json.dumps({"submit": submit, "changed_urls": urls}, ensure_ascii=False))
    if not submit:
        return
    payload = {
        "host": parsed.netloc,
        "key": key,
        "keyLocation": f"{origin}/{key}.txt",
        "urlList": urls,
    }
    request = Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        if response.status not in (200, 202):
            raise ValueError("IndexNow did not accept the submission")
        status = response.status
    state.parent.mkdir(parents=True, exist_ok=True)
    temporary = state.with_suffix(".tmp")
    temporary.write_text(json.dumps(current, indent=2) + "\n")
    temporary.replace(state)
    print(
        f"IndexNow accepted URLs (HTTP {status}); crawling and indexing are not guaranteed."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument(
        "--key", required=True, help="Public ownership key, not a secret"
    )
    parser.add_argument(
        "--state", type=Path, default=Path("docker/.indexnow/accepted.json")
    )
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    publish(args.origin, args.key, args.state, args.submit)


if __name__ == "__main__":
    main()
