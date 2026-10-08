from collections.abc import Callable
from html.parser import HTMLParser

import pytest

from app.core.mail.templates import (
    EmailContent,
    build_password_reset_email,
    build_verification_email,
    build_welcome_email,
)


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href is not None:
                self.hrefs.append(href)
        if tag == "script":
            self.scripts.append(tag)


@pytest.mark.parametrize(
    "builder", [build_verification_email, build_password_reset_email, build_welcome_email]
)
@pytest.mark.parametrize("language", ["en", "ko-KR"])
def test_mail_preserves_links_plaintext_and_escapes_dynamic_html(
    builder: Callable[..., EmailContent], language: str
) -> None:
    # Given: HTML-sensitive display text and a URL containing multiple parameters.
    link = 'https://example.com/action?token=sample&context="account"'
    name = "<script>alert(1)</script> & User"
    content = builder(name=name, link=link, app_name="B4A <workspace>", language=language)
    # When: the email HTML is parsed as a client would parse it.
    parsed = Links()
    parsed.feed(content.html)
    # Then: both CTA and fallback preserve the URL while dynamic text stays text.
    assert parsed.hrefs == [link, link]
    assert not parsed.scripts
    assert "&lt;workspace&gt;" in content.html
    assert "&lt;script&gt;" in content.html
    assert link in content.text
    assert name in content.text
    assert f'lang="{language.split("-")[0]}"' in content.html
    assert content.subject


@pytest.mark.parametrize("language", ["en", "ko"])
def test_deletion_email_explains_consequences_without_action_links(language):
    """Scenario: reading a deletion email cannot trigger deletion or expose an action URL."""
    from app.core.mail.templates import build_account_deletion_email

    # Given: an email with a six-digit code and untrusted display name.
    content = build_account_deletion_email(
        name="<script>name</script>", code="123456", language=language
    )
    # When: an email client parses its content.
    parsed = Links()
    parsed.feed(content.html)
    # Then: code and expiry remain visible, with no actionable links or scripts.
    assert "123456" in content.text and "123456" in content.html
    assert "10" in content.text
    assert not parsed.hrefs and not parsed.scripts
    assert 'role="presentation"' in content.html
    assert "max-width:480px" in content.html
    assert 'lang="' + language + '"' in content.html
    assert "&lt;script&gt;" in content.html
    assert "href=" not in content.html
    assert "B4A" in content.html
    assert "Blueprint4FastAPI" not in content.html


@pytest.mark.parametrize("language", ["en", "ko"])
@pytest.mark.parametrize("kind", ["subscription_started", "plan_changed", "account_deleted"])
def test_lifecycle_templates_are_localized_escaped_and_linked(language, kind):
    """Scenario: lifecycle completion mail has localized copy, safe HTML and working text/HTML links."""
    from app.core.mail.templates import build_lifecycle_email

    # Given: untrusted display data and a server-owned destination.
    link = (
        "https://example.com/home"
        if kind == "account_deleted"
        else "https://example.com/settings?section=billing"
    )
    content = build_lifecycle_email(
        kind=kind,
        name="<script>User</script>",
        plan="Plus & Pro",
        link=link,
        app_name="B4A",
        language=language,
    )
    # When: the message is parsed as HTML.
    parsed = Links()
    parsed.feed(content.html)
    # Then: both action/fallback links and plaintext preserve the destination.
    assert parsed.hrefs == [link, link] and not parsed.scripts
    assert "&lt;script&gt;" in content.html
    assert link in content.text and f'lang="{language}"' in content.html
    assert ("했습니다" in content.subject) == (language == "ko")
    if kind == "account_deleted":
        assert "123456" not in content.text
        assert (
            "deletion is complete" in content.text
            if language == "en"
            else "삭제가 완료" in content.text
        )
