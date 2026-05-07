# ruff: noqa: E501
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class EmailContent:
    subject: str
    text: str
    html: str


@dataclass(frozen=True)
class TemplateCopy:
    subject: str
    preheader: str
    heading: str
    intro: str
    cta_label: str
    outro: str
    footer: str


@dataclass(frozen=True)
class TemplateTheme:
    page_bg: str
    panel_bg: str
    panel_border: str
    heading_bg_start: str
    heading_bg_end: str
    text_primary: str
    text_secondary: str
    cta_bg: str
    cta_bg_hover: str
    cta_fg: str
    muted_bg: str
    muted_fg: str


class EmailLocale(StrEnum):
    EN = "en"
    KO = "ko"


DEFAULT_LOCALE = EmailLocale.EN.value
SUPPORTED_LOCALES = {locale.value for locale in EmailLocale}

FRONTEND_LIGHT_THEME = TemplateTheme(
    page_bg="#f7f4ea",
    panel_bg="#ffffff",
    panel_border="rgba(19, 32, 51, 0.12)",
    heading_bg_start="#101010",
    heading_bg_end="#2a2a2a",
    text_primary="#132033",
    text_secondary="#4a5a6b",
    cta_bg="#101010",
    cta_bg_hover="#2a2a2a",
    cta_fg="#f7f7f7",
    muted_bg="#f2eee3",
    muted_fg="#4a5a6b",
)

TEMPLATE_COPY_BY_LOCALE: dict[str, dict[str, TemplateCopy]] = {
    "en": {
        "verification": TemplateCopy(
            subject="Verify your email",
            preheader="Confirm your email to finish setting up your account.",
            heading="Confirm your email",
            intro="Hi {name}, welcome aboard. Please verify your email to continue.",
            cta_label="Verify email",
            outro=(
                "This link is valid for a limited time. If you did not request this email, "
                "you can ignore it."
            ),
            footer="",
        ),
        "password_reset": TemplateCopy(
            subject="Reset your password",
            preheader="Reset your password with a secure one-time link.",
            heading="Reset your password",
            intro="Hi {name}, we received a request to reset your password.",
            cta_label="Reset password",
            outro=("If you did not request a password reset, you can safely ignore this email."),
            footer="For account security, never share this link with anyone.",
        ),
    },
    "ko": {
        "verification": TemplateCopy(
            subject="이메일을 인증해 주세요",
            preheader="계정 설정을 완료하려면 이메일 인증이 필요합니다.",
            heading="이메일 인증",
            intro="{name}님, 가입을 환영합니다. 계속하려면 이메일을 인증해 주세요.",
            cta_label="이메일 인증하기",
            outro=(
                "이 링크는 일정 시간 동안만 유효합니다. 요청하지 않은 메일이라면 무시해도 됩니다."
            ),
            footer="",
        ),
        "password_reset": TemplateCopy(
            subject="비밀번호를 재설정해 주세요",
            preheader="보안 일회성 링크로 비밀번호를 재설정할 수 있습니다.",
            heading="비밀번호 재설정",
            intro="{name}님, 비밀번호 재설정 요청을 확인했습니다.",
            cta_label="비밀번호 재설정",
            outro="요청하지 않은 재설정 메일이라면 무시해도 됩니다.",
            footer="계정 보안을 위해 이 링크를 다른 사람과 공유하지 마세요.",
        ),
    },
}


def _display_name(name: str | None) -> str:
    value = (name or "").strip()
    return value if value else "there"


def resolve_locale(language: str | None) -> str:
    if not language:
        return DEFAULT_LOCALE

    # Accept-Language can contain priority list like "ko-KR,ko;q=0.9,en;q=0.8".
    primary = language.split(",")[0].strip().lower()
    normalized = primary.split("-")[0]
    if normalized in SUPPORTED_LOCALES:
        return normalized
    return DEFAULT_LOCALE


def _copy(template_name: str, *, locale: str) -> TemplateCopy:
    return TEMPLATE_COPY_BY_LOCALE[locale][template_name]


def _verification_text_en(display_name: str, link: str) -> tuple[str, str]:
    text = (
        f"Hi {display_name},\n\n"
        "Please verify your email by clicking the link below:\n"
        f"{link}\n\n"
        "If you did not request this email, you can ignore it.\n"
    )
    manual_link_label = "If the button does not work, use this link:"
    return text, manual_link_label


def _verification_text_ko(display_name: str, link: str) -> tuple[str, str]:
    text = (
        f"{display_name}님, 안녕하세요.\n\n"
        "아래 링크를 눌러 이메일 인증을 완료해 주세요.\n"
        f"{link}\n\n"
        "요청하지 않은 메일이라면 무시하셔도 됩니다.\n"
    )
    manual_link_label = "버튼이 동작하지 않으면 아래 링크를 사용해 주세요:"
    return text, manual_link_label


def _password_reset_text_en(display_name: str, link: str) -> tuple[str, str]:
    text = (
        f"Hi {display_name},\n\n"
        "We received a request to reset your password. Use the link below:\n"
        f"{link}\n\n"
        "If you did not request a password reset, you can ignore this email.\n"
    )
    manual_link_label = "If the button does not work, use this link:"
    return text, manual_link_label


def _password_reset_text_ko(display_name: str, link: str) -> tuple[str, str]:
    text = (
        f"{display_name}님, 안녕하세요.\n\n"
        "비밀번호 재설정 요청을 확인했습니다. 아래 링크를 사용해 주세요.\n"
        f"{link}\n\n"
        "요청하지 않은 메일이라면 무시하셔도 됩니다.\n"
    )
    manual_link_label = "버튼이 동작하지 않으면 아래 링크를 사용해 주세요:"
    return text, manual_link_label


TextBuilder = Callable[[str, str], tuple[str, str]]
VERIFICATION_TEXT_BUILDERS: dict[str, TextBuilder] = {
    EmailLocale.EN.value: _verification_text_en,
    EmailLocale.KO.value: _verification_text_ko,
}
PASSWORD_RESET_TEXT_BUILDERS: dict[str, TextBuilder] = {
    EmailLocale.EN.value: _password_reset_text_en,
    EmailLocale.KO.value: _password_reset_text_ko,
}


def _build_email_html(
    *,
    app_name: str,
    preheader: str,
    heading: str,
    intro: str,
    cta_label: str,
    link: str,
    outro: str,
    footer: str,
    manual_link_label: str,
    theme: TemplateTheme,
) -> str:
    footer_html = ""
    if footer.strip():
        footer_html = f"""
            <tr>
              <td
                style="padding:16px 28px;background:{theme.muted_bg};font-family:'IBM Plex Mono','Courier New',monospace;font-size:12px;color:{theme.muted_fg};"
              >
                {footer}
              </td>
            </tr>
"""

    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <title>{heading}</title>
  </head>
  <body style="margin:0;padding:0;background-color:{theme.page_bg};color:{theme.text_primary};">
    <span style="display:none;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden;">
      {preheader}
    </span>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{theme.page_bg};">
      <tr>
        <td align="center" style="padding:32px 16px;">
          <table
            role="presentation"
            width="100%"
            cellpadding="0"
            cellspacing="0"
            style="max-width:560px;background:{theme.panel_bg};border-radius:20px;overflow:hidden;border:1px solid {theme.panel_border};box-shadow:0 20px 45px rgba(22,33,48,0.14);"
          >
            <tr>
              <td style="padding:24px 28px;background:linear-gradient(135deg,{theme.heading_bg_start} 0%,{theme.heading_bg_end} 100%);">
                <div
                  style="font-family:'Space Grotesk','Segoe UI',sans-serif;font-size:22px;font-weight:700;color:{theme.cta_fg};"
                >
                  {app_name}
                </div>
                <div
                  style="margin-top:6px;font-family:'IBM Plex Mono','Courier New',monospace;font-size:12px;letter-spacing:0.04em;color:rgba(247,247,247,0.86);"
                >
                  Account & Security
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:30px 28px;">
                <h1
                  style="margin:0 0 12px;font-family:'Space Grotesk','Segoe UI',sans-serif;font-size:24px;line-height:1.2;color:{theme.text_primary};"
                >
                  {heading}
                </h1>
                <p
                  style="margin:0 0 20px;font-family:'Space Grotesk','Segoe UI',sans-serif;font-size:15px;line-height:1.6;color:{theme.text_secondary};"
                >
                  {intro}
                </p>
                <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 22px;">
                  <tr>
                    <td align="left">
                      <a
                        href="{link}"
                        style="display:inline-block;padding:12px 22px;border-radius:999px;background:{theme.cta_bg};color:{theme.cta_fg};font-family:'Space Grotesk','Segoe UI',sans-serif;font-size:14px;font-weight:600;text-decoration:none;border:1px solid {theme.cta_bg_hover};"
                      >
                        {cta_label}
                      </a>
                    </td>
                  </tr>
                </table>
                <p
                  style="margin:0 0 14px;font-family:'Space Grotesk','Segoe UI',sans-serif;font-size:14px;line-height:1.6;color:{theme.text_secondary};"
                >
                  {outro}
                </p>
                <p
                  style="margin:0 0 8px;font-family:'IBM Plex Mono','Courier New',monospace;font-size:12px;color:{theme.text_secondary};"
                >
                  {manual_link_label}
                </p>
                <p
                  style="margin:0;font-family:'IBM Plex Mono','Courier New',monospace;font-size:12px;line-height:1.6;"
                >
                  <a href="{link}" style="color:{theme.text_primary};text-decoration:none;word-break:break-all;">{link}</a>
                </p>
              </td>
            </tr>
{footer_html}
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def build_verification_email(
    *,
    name: str | None,
    link: str,
    app_name: str = "Blueprint4FastAPI",
    language: str | None = None,
) -> EmailContent:
    locale = resolve_locale(language)
    copy = _copy("verification", locale=locale)
    display_name = _display_name(name)
    text, manual_link_label = VERIFICATION_TEXT_BUILDERS[locale](display_name, link)
    html = _build_email_html(
        app_name=app_name,
        preheader=copy.preheader,
        heading=copy.heading,
        intro=copy.intro.format(name=display_name),
        cta_label=copy.cta_label,
        link=link,
        outro=copy.outro,
        footer=copy.footer,
        manual_link_label=manual_link_label,
        theme=FRONTEND_LIGHT_THEME,
    )
    return EmailContent(subject=copy.subject, text=text, html=html)


def build_password_reset_email(
    *,
    name: str | None,
    link: str,
    app_name: str = "Blueprint4FastAPI",
    language: str | None = None,
) -> EmailContent:
    locale = resolve_locale(language)
    copy = _copy("password_reset", locale=locale)
    display_name = _display_name(name)
    text, manual_link_label = PASSWORD_RESET_TEXT_BUILDERS[locale](display_name, link)
    html = _build_email_html(
        app_name=app_name,
        preheader=copy.preheader,
        heading=copy.heading,
        intro=copy.intro.format(name=display_name),
        cta_label=copy.cta_label,
        link=link,
        outro=copy.outro,
        footer=copy.footer,
        manual_link_label=manual_link_label,
        theme=FRONTEND_LIGHT_THEME,
    )
    return EmailContent(subject=copy.subject, text=text, html=html)
