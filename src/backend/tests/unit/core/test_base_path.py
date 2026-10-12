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
