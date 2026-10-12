"""Prefix-stripping proxies must preserve monolithic routing and session ownership."""

import json

import pytest
from fastapi import Request, Response
from fastapi.testclient import TestClient

import app.main as main_module
from app.core.config.base_path import normalize_base_path, validate_frontend_path
from app.core.config.settings import SETTINGS
from app.utils.cookies import clear_refresh_cookies, get_refresh_cookie_value, set_refresh_cookies


@pytest.mark.parametrize("path", ["alpha", "//alpha", "/a//b", "/a/../b", "/a%2fb", "/a?b", "/a#b"])
def test_reject_ambiguous_paths(path):
    with pytest.raises(ValueError):
        normalize_base_path(path)


def test_packaged_path_mismatch_is_rejected(tmp_path):
    (tmp_path / "deployment-path.json").write_text(json.dumps({"basePath": "/alpha"}))
    validate_frontend_path(tmp_path, "/alpha")
    with pytest.raises(ValueError, match="rebuild"):
        validate_frontend_path(tmp_path, "/beta")


def test_monolithic_prefix_routes_and_redirects(tmp_path, monkeypatch):
    fake_main = tmp_path / "app" / "main.py"
    dist = fake_main.parent / "static" / "dist"
    dist.mkdir(parents=True)
    (dist / "deployment-path.json").write_text(json.dumps({"basePath": "/demos/alpha"}))
    (dist / "index.html").write_text('<html><div id="root"></div></html>')
    (dist / "assets").mkdir()
    (dist / "assets" / "app.js").write_text("window.loaded = true;")
    (dist / "about").mkdir()
    (dist / "about" / "index.html").write_text("public document")
    monkeypatch.setattr(main_module, "__file__", str(fake_main))
    monkeypatch.setattr(SETTINGS, "APP_BASE_PATH", "/demos/alpha")
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", True)
    app = main_module.create_app()
    client = TestClient(app)
    # The reverse proxy removes the public prefix before forwarding.
    for prefix in ("",):
        assert client.get(prefix + "/home", headers={"Accept": "text/html"}).status_code == 200
        assert client.get(prefix + "/config").json()["frontend_base_path"] == "/demos/alpha"
        assert client.get(prefix + "/assets/app.js").text == "window.loaded = true;"
        for missing in ("/api/v1/missing", "/assets/missing.js", "/about/missing/"):
            assert client.get(prefix + missing, headers={"Accept": "text/html"}).status_code == 404
    redirect = client.get("/about", follow_redirects=False)
    assert redirect.headers["location"].endswith("/demos/alpha/about/")

    # The static catch-all is last in production; inspect URL construction with a request scope.
    request = Request(
        {
            "type": "http",
            "scheme": "https",
            "server": ("example.test", 443),
            "path": "/config",
            "root_path": "/demos/alpha",
            "headers": [],
            "router": app.router,
        }
    )
    assert (
        str(request.url_for("oauth_callback", provider="google"))
        == "https://example.test/demos/alpha/api/v1/auth/oauth/google/callback"
    )


def test_cookie_isolation_and_matching_deletion(monkeypatch):
    issued = {}
    request = Request({"type": "http", "scheme": "https", "path": "/", "headers": []})
    for path in ("", "/demos/alpha", "/demos/beta"):
        monkeypatch.setattr(SETTINGS, "APP_BASE_PATH", path)
        response = Response()
        set_refresh_cookies(response, request, "token", "session")
        cookies = response.headers.getlist("set-cookie")
        names = [value.split("=", 1)[0] for value in cookies]
        issued[path] = names
        assert all(f"Path={path}/;" in value for value in cookies)
        read_request = Request(
            {
                "type": "http",
                "headers": [(b"cookie", f"{names[0]}=token; {names[1]}=session".encode())],
            }
        )
        assert get_refresh_cookie_value(read_request) == ("token", "session")
        cleared = Response()
        clear_refresh_cookies(cleared)
        assert [value.split("=", 1)[0] for value in cleared.headers.getlist("set-cookie")] == names
        assert all(f"Path={path}/;" in value for value in cleared.headers.getlist("set-cookie"))
    assert len({name for names in issued.values() for name in names}) == 6


@pytest.mark.parametrize("prefix", ["", "/community", "/demos/tracker"])
def test_same_artifact_runtime_documents(tmp_path, monkeypatch, prefix):
    fake_main = tmp_path / "app" / "main.py"
    dist = fake_main.parent / "static" / "dist"
    dist.mkdir(parents=True)
    metadata = {"version": 2, "mode": "runtime", "publicOrigin": "https://build.test"}
    (dist / "deployment-path.json").write_text(json.dumps(metadata))
    source = (
        '<html><head><base data-b4-app-base href="/">'
        '<meta name="b4-base-path" content="">'
        '<link rel="canonical" href="https://build.test/about/">'
        '</head><body><img src="/logo.svg"><script src="./assets/app.js"></script></body></html>'
    )
    (dist / "index.html").write_text(source)
    (dist / "about").mkdir()
    (dist / "about" / "index.html").write_text(source)
    (dist / "assets").mkdir()
    (dist / "assets" / "app.js").write_text("const build = 'identical';")
    (dist / "sitemap.xml").write_text("<loc>https://build.test/about/</loc>")
    (dist / "robots.txt").write_text("Sitemap: https://build.test/sitemap.xml")
    (dist / "discovery-manifest.json").write_text(
        json.dumps({"origin": "https://build.test", "pages": {"https://build.test/about/": "hash"}})
    )
    monkeypatch.setattr(main_module, "__file__", str(fake_main))
    monkeypatch.setattr(SETTINGS, "APP_BASE_PATH", prefix)
    monkeypatch.setattr(SETTINGS, "APP_BASE_URL", "https://runtime.test" + prefix)
    validate_frontend_path(dist, prefix)
    client = TestClient(main_module.create_app())
    for path in ("/", "/home/nested", "/about/"):
        response = client.get(path, headers={"accept": "text/html", "if-none-match": "old"})
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.text.count("<base ") == 1
        assert f'<base data-b4-app-base href="{prefix}/">' in response.text
        assert f'<meta name="b4-base-path" content="{prefix}">' in response.text
        assert f'href="https://runtime.test{prefix}/about/"' in response.text
        assert f'src="{prefix}/logo.svg"' in response.text
        assert 'src="./assets/app.js"' in response.text
        head = client.head(path, headers={"accept": "text/html"})
        assert head.content == b""
        assert head.headers["content-length"] == response.headers["content-length"]
    assert client.get("/sitemap.xml").text == f"<loc>https://runtime.test{prefix}/about/</loc>"
    assert client.get("/robots.txt").text == f"Sitemap: https://runtime.test{prefix}/sitemap.xml"
    manifest = client.get("/discovery-manifest.json").json()
    assert manifest["origin"] == "https://runtime.test"
    assert list(manifest["pages"]) == [f"https://runtime.test{prefix}/about/"]
    asset = client.get("/assets/app.js")
    assert (
        client.get("/assets/app.js", headers={"if-none-match": asset.headers["etag"]}).status_code
        == 304
    )
    assert (dist / "index.html").read_text() == source


def test_static_discovery_keeps_fragment_links_document_local(tmp_path):
    from app.core.config.frontend import RuntimeStaticFiles

    (tmp_path / "deployment-path.json").write_text(json.dumps({"version": 2, "mode": "runtime"}))
    document = tmp_path / "index.html"
    document.write_text(
        '<html><head></head><body><a href="#features">Features</a>'
        '<img src="/logo.svg"></body></html>'
    )
    files = RuntimeStaticFiles(tmp_path, "/demo", "https://example.test/demo")
    result = files.render(document)
    assert "<base" not in result
    assert 'href="#features"' in result
    assert 'src="/demo/logo.svg"' in result
