"""Public files must be documents, never successful SPA fallbacks."""

import pytest
from fastapi.testclient import TestClient

import app.main as main_module


@pytest.fixture
def public_client(tmp_path, monkeypatch):
    # Given: an isolated packaged frontend, without starting database/mail workers.
    fake_main = tmp_path / "app" / "main.py"
    dist = fake_main.parent / "static" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text('<html><div id="root"></div></html>')
    (dist / "about").mkdir()
    (dist / "about" / "index.html").write_text("<html><h1>Blueprint4Agent</h1></html>")
    (dist / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    monkeypatch.setattr(main_module, "__file__", str(fake_main))
    return TestClient(main_module.create_app())


def test_public_documents_and_app_fallback(public_client):
    # When: requesting a public document or an existing client-side route.
    document = public_client.get("/about/", headers={"Accept": "text/html"})
    app = public_client.get("/home", headers={"Accept": "text/html"})
    # Then: static content and application fallback retain separate ownership.
    assert document.status_code == 200
    assert "<h1>Blueprint4Agent</h1>" in document.text
    assert app.status_code == 200
    assert 'id="root"' in app.text
    assert "text/plain" in public_client.get("/robots.txt").headers["content-type"]


@pytest.mark.parametrize(
    "path",
    [
        "/about/missing/",
        "/sitemap.xml",
        "/missing-key.txt",
        "/assets/missing.js",
        "/api/v1/missing",
    ],
)
def test_missing_documents_remain_404_with_browser_accept(public_client, path):
    # When: a bot/browser requests a deleted document or missing resource.
    response = public_client.get(path, headers={"Accept": "text/html"})
    # Then: search engines and IndexNow never receive the SPA with HTTP 200.
    assert response.status_code == 404
    assert 'id="root"' not in response.text
