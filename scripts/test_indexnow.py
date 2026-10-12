import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError

from indexnow import changed_urls, publish, validate_manifest

ORIGIN = "https://example.test"
URL = ORIGIN + "/about/"
KEY = "public-key-123"
CURRENT = {"version": 1, "origin": ORIGIN, "pages": {URL: "a" * 64}}


class IndexNowTests(unittest.TestCase):
    def test_diff_handles_added_changed_deleted_and_unchanged(self):
        before = {"pages": {"a": "1", "b": "2", "c": "3"}}
        after = {"pages": {"a": "1", "b": "4", "d": "5"}}
        self.assertEqual(changed_urls(before, after), ["b", "c", "d"])
        self.assertEqual(changed_urls(after, after), [])

    def test_rejects_foreign_private_and_query_urls(self):
        for url in [
            "https://other.test/about/",
            ORIGIN + "/settings",
            URL + "?token=x",
        ]:
            with self.assertRaises(ValueError):
                validate_manifest({**CURRENT, "pages": {url: "a" * 64}}, ORIGIN)

    def resources(self, url):
        return {
            ORIGIN + "/discovery-manifest.json": json.dumps(CURRENT),
            ORIGIN
            + "/sitemap.xml": f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{URL}</loc></url></urlset>',
            ORIGIN + f"/{KEY}.txt": KEY,
            URL: f'<link rel="canonical" href="{URL}" /><h1>Project</h1>',
        }[url]

    def test_dry_run_never_submits_or_writes_state(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("indexnow.fetch", side_effect=self.resources),
            patch("indexnow.urlopen") as send,
        ):
            state = Path(directory) / "state.json"
            publish(ORIGIN, KEY, state)
            send.assert_not_called()
            self.assertFalse(state.exists())

    def test_failure_retains_state_then_acceptance_advances_it(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("indexnow.fetch", side_effect=self.resources),
            patch("indexnow.urlopen") as send,
        ):
            state = Path(directory) / "state.json"
            previous = {**CURRENT, "pages": {URL: "b" * 64}}
            state.write_text(json.dumps(previous))
            send.side_effect = HTTPError(
                "https://api.indexnow.org/indexnow", 429, "Retry", {}, None
            )
            with self.assertRaises(HTTPError):
                publish(ORIGIN, KEY, state, True)
            self.assertEqual(json.loads(state.read_text()), previous)
            send.side_effect = None
            response = MagicMock()
            response.__enter__.return_value.status = 202
            send.return_value = response
            publish(ORIGIN, KEY, state, True)
            self.assertEqual(json.loads(state.read_text()), CURRENT)
            payload = json.loads(send.call_args.args[0].data)
            self.assertEqual(payload["urlList"], [URL])

    def test_deleted_page_must_return_404_not_spa_html(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("indexnow.fetch", side_effect=self.resources),
            patch("indexnow.urlopen") as send,
        ):
            state = Path(directory) / "state.json"
            deleted = ORIGIN + "/about/removed/"
            state.write_text(
                json.dumps(
                    {**CURRENT, "pages": {**CURRENT["pages"], deleted: "c" * 64}}
                )
            )
            original = self.resources
            with patch(
                "indexnow.fetch",
                side_effect=lambda url: (
                    "<div id='root'></div>" if url == deleted else original(url)
                ),
            ):
                with self.assertRaisesRegex(ValueError, "404 or 410"):
                    publish(ORIGIN, KEY, state, True)
            send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
