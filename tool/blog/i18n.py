"""Per-language chrome strings.

`curriculum.json` owns the *content* of the blog -- titles, summaries, blurbs
-- and each language carries its own, under ``blog/<lang>/``. This module owns
the *chrome*: the labels the templates themselves contribute, which no
curriculum file should have to repeat (and which must never drift between two
copies of a template).

Adding a language is therefore two things: an entry in :data:`CATALOGUE`, and a
``blog/<lang>/curriculum.json`` mirroring the English structure. Nothing in
``theme.py`` or ``site.py`` needs to learn about it.

Placeholders are ``str.format`` fields, so a string that takes an argument says
so in its own value rather than in a call site.
"""

from __future__ import annotations

from dataclasses import dataclass

# The default language lives at the root of docs/blog/ so its URLs never moved
# when a second language was added. Every other language is a subdirectory.
DEFAULT_LANG = "en"
LANGS = ("en", "vi")


@dataclass(frozen=True)
class Strings:
    """Chrome strings for one language.

    Plain labels are used verbatim; the few that take a value document it in a
    comment and are formatted at the call site.
    """

    code: str                  # BCP-47 tag for <html lang> and hreflang
    label: str                 # short form in the language selector: EN / VI
    name: str                  # the language's own name, for the selector title

    skip_to_content: str
    brand_sub: str
    nav_curriculum: str
    nav_cv: str
    nav_github: str
    theme_toggle_title: str
    theme_switch_dark: str
    theme_switch_light: str
    aria_primary: str
    aria_language: str
    aria_toc: str
    aria_breadcrumb: str
    aria_pager: str
    aria_curriculum: str

    on_this_page: str
    min_read: str              # {n}
    minutes: str               # {n}
    updated: str               # {date}
    previous: str
    next: str
    planned: str
    english_only: str
    start_here: str
    part: str                  # {n}
    stat_parts: str
    stat_chapters: str
    stat_published: str
    stat_diagrams: str
    figure_label: str

    # Read by blog.js out of data- attributes, so the script carries no English.
    copy: str
    copied: str
    copy_failed: str

    @property
    def has_translations(self) -> bool:
        """True when this language is not the default one."""
        return self.code != DEFAULT_LANG


EN = Strings(
    code="en",
    label="EN",
    name="English",
    skip_to_content="Skip to content",
    brand_sub="signal processing notes",
    nav_curriculum="Curriculum",
    nav_cv="CV",
    nav_github="GitHub",
    theme_toggle_title="Switch colour theme",
    theme_switch_dark="Switch to dark theme",
    theme_switch_light="Switch to light theme",
    aria_primary="Primary",
    aria_language="Language",
    aria_toc="On this page",
    aria_breadcrumb="Breadcrumb",
    aria_pager="Chapter navigation",
    aria_curriculum="Full curriculum",
    on_this_page="On this page",
    min_read="{n} min read",
    minutes="{n} min",
    updated="Updated {date}",
    previous="Previous",
    next="Next",
    planned="Planned",
    english_only="English only",
    start_here="Start here",
    part="Part {n}",
    stat_parts="parts",
    stat_chapters="chapters planned",
    stat_published="published",
    stat_diagrams="diagrams",
    figure_label="Figure",
    copy="Copy",
    copied="Copied",
    copy_failed="Failed",
)

VI = Strings(
    code="vi",
    label="VI",
    name="Tiếng Việt",
    skip_to_content="Bỏ qua nội dung",
    brand_sub="ghi chú xử lý tín hiệu",
    nav_curriculum="Chương trình",
    nav_cv="CV",
    nav_github="GitHub",
    theme_toggle_title="Đổi giao diện",
    theme_switch_dark="Chuyển sang nền tối",
    theme_switch_light="Chuyển sang nền sáng",
    aria_primary="Chính",
    aria_language="Ngôn ngữ",
    aria_toc="Trong bài này",
    aria_breadcrumb="Đường dẫn",
    aria_pager="Điều hướng chương",
    aria_curriculum="Toàn bộ chương trình",
    on_this_page="Trong bài này",
    min_read="{n} phút đọc",
    minutes="{n} phút",
    updated="Cập nhật {date}",
    previous="Trước",
    next="Sau",
    planned="Dự kiến",
    english_only="Bản tiếng Anh",
    start_here="Bắt đầu từ đây",
    part="Phần {n}",
    stat_parts="phần",
    stat_chapters="chương dự kiến",
    stat_published="đã đăng",
    stat_diagrams="hình vẽ",
    figure_label="Hình",
    copy="Sao chép",
    copied="Đã chép",
    copy_failed="Lỗi",
)

CATALOGUE: dict[str, Strings] = {EN.code: EN, VI.code: VI}


def strings(lang: str) -> Strings:
    """Chrome strings for ``lang``.

    An unknown language is a programming error rather than a fallback: a
    silently English page under ``docs/blog/xx/`` is worse than a failed build.
    """
    try:
        return CATALOGUE[lang]
    except KeyError:
        raise KeyError(
            f"no string catalogue for language '{lang}'; add one to "
            f"tool/blog/i18n.py (known: {', '.join(CATALOGUE)})"
        ) from None


def other_lang(lang: str) -> str:
    """The language the selector switches to.

    With exactly two languages this is a swap. When a third arrives, this
    becomes a list and the header renders one link per language -- the call
    sites already treat the value as "the other language", not "the second".
    """
    others = [code for code in LANGS if code != lang]
    if not others:
        raise KeyError(f"language '{lang}' has no counterpart to switch to")
    return others[0]
