#!/usr/bin/env python3
"""Builds the site into _site/ with pandoc.

  python3 tools/build.py                   build the site
  python3 tools/build.py --drafts          also build pages marked `draft: true`
  python3 tools/build.py --check           build, then check every internal link
  python3 tools/build.py --serve           build with drafts, serve it on port 8000,
                                           and rebuild when a file changes
  python3 tools/build.py --new-post TITLE  start a draft blog post

The site mirrors the source tree. A Markdown page becomes an HTML page in the
same place (blog/x.md -> blog/x.html; talks/y/index.md -> talks/y/index.html,
served as talks/y/), and other files (images, CSS, code) are copied as they
are. A folder with a slides.md also gets slides.html, a reveal.js deck.
README.md files are for GitHub and are not part of the site.

Needs pandoc 3 and Python 3.11 or later. README.md explains how to write pages.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import datetime as dt
import fnmatch
import functools
import html
import http.server
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import threading
import time
import tomllib
import unicodedata
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
TOOLS = ROOT / "tools"

# Left out of the site wherever they are, on top of `exclude` in site.toml.
EXCLUDE = [".*", "_*", "__pycache__", "*.pyc", "README.md", "Makefile", "reveal-template.html"]
# Left out of the site when they are at the top of the repository.
EXCLUDE_AT_ROOT = ["LICENSE*", "site.toml", "templates", "tools"]

TOC_MARK = "<!--@@toc@@-->"
BODY_MARK = "<!--@@body@@-->"
LIST_RE = re.compile(r"<!--\s*list:([\w-]+)((?:\s+\w+=\w+)*)\s*-->")
# site.js shows the "Upcoming" badge on talks and meetups that are still ahead.
UPCOMING = '<span class="badge upcoming" hidden>Upcoming</span>'
DRAFT = '<span class="badge draft">Draft</span>'

# Icons for the links on the home page (GitHub Octicons, MIT; Simple Icons, CC0).
ICONS = {
    "github": '<svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>',
    "linkedin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>',
    "rss": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M19.199 24C19.199 13.467 10.533 4.8 0 4.8V0c13.165 0 24 10.835 24 24h-4.801zM3.291 17.415a3.3 3.3 0 0 1 3.293 3.295A3.303 3.303 0 0 1 3.283 24C1.47 24 0 22.526 0 20.71s1.475-3.294 3.291-3.295zM15.909 24h-4.665c0-6.169-5.075-11.245-11.244-11.245V8.09c8.727 0 15.909 7.184 15.909 15.91z"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm18 2-10 7L2 6"/></svg>',
    "link": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
}


class BuildError(Exception):
    """A problem in the sources, reported without a traceback."""


@dataclasses.dataclass
class Page:
    src: str  # path in the repository, such as "blog/x.md"
    meta: dict  # front matter; text values are HTML
    toc: str  # table of contents, as HTML
    body: str  # content, as HTML
    section: str | None = None  # "blog" for a blog post, and so on
    date: dt.date | None = None

    @property
    def out(self) -> str:
        """Path of the HTML file in the site, such as "blog/x.html"."""
        return self.src.removesuffix(".md") + ".html"

    @property
    def url(self) -> str:
        """Address relative to the site root: "blog/x.html", "talks/y/", or ""."""
        if self.is_index:
            return self.out.removesuffix("index.html")
        return self.out

    @property
    def folder(self) -> str:
        return posixpath.dirname(self.src)

    @property
    def is_index(self) -> bool:
        return posixpath.basename(self.src) == "index.md"

    @property
    def is_draft(self) -> bool:
        return self.meta.get("draft") in (True, "true", "yes")

    def text(self, key: str) -> str:
        """A front matter value as inline HTML, or "" if it is not text."""
        value = self.meta.get(key)
        if not isinstance(value, str):
            return ""
        value = value.strip()
        # Multi-line values come back as one paragraph; keep only its content.
        match = re.fullmatch(r"<p>(.*)</p>", value, re.DOTALL)
        return match.group(1) if match else value

    def url_field(self, key: str) -> str:
        """A front matter value that holds an address."""
        return plain(self.text(key))


@dataclasses.dataclass
class Site:
    config: dict
    layout: str
    pages: list[Page]
    sections: dict[str, list[Page]]  # pages of each section, newest first
    decks: set[str]  # folders with a slide deck


def plain(markup: str) -> str:
    """The text of an HTML snippet, without tags or character references."""
    return html.unescape(re.sub(r"<[^>]*>", "", markup)).strip()


def attr(value: str) -> str:
    """Escapes text for an HTML attribute or for XML."""
    return html.escape(value, quote=True)


def is_absolute(url: str) -> bool:
    return bool(re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:|/", url))


def load_config() -> dict:
    with open(ROOT / "site.toml", "rb") as f:
        config = tomllib.load(f)
    config["url"] = config["url"].rstrip("/") + "/"
    config.setdefault("branch", "main")
    config.setdefault("sections", {})
    return config


def excluded(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


def find_sources(config: dict) -> tuple[list[str], list[str], list[str]]:
    """Lists the pages, the slide decks, and the other files of the site."""
    pages, decks, files = [], [], []
    for folder, dirs, names in os.walk(ROOT):
        rel = Path(folder).relative_to(ROOT).as_posix()
        rel = "" if rel == "." else rel
        patterns = EXCLUDE + config.get("exclude", []) + ([] if rel else EXCLUDE_AT_ROOT)
        dirs[:] = sorted(d for d in dirs if not excluded(d, patterns))
        for name in sorted(names):
            if excluded(name, patterns):
                continue
            path = f"{rel}/{name}" if rel else name
            if name == "slides.md":
                decks.append(path)
            elif name.endswith(".md"):
                pages.append(path)
            else:
                files.append(path)
    return pages, decks, files


def run(command: list[str], cwd: Path, what: str, env: dict | None = None) -> str:
    """Runs a command and returns its output; raises BuildError if it fails."""
    result = subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode:
        raise BuildError(f"{what} failed:\n{(result.stdout + result.stderr).strip()}")
    if result.stderr.strip():
        print(f"{what}: {result.stderr.strip()}", file=sys.stderr)
    return result.stdout


def convert(src: str, config: dict) -> tuple[dict, str, str]:
    """Converts a page with pandoc. Returns its front matter, contents, and body."""
    command = [
        "pandoc", src, "--from=markdown", "--to=html5", "--wrap=none", "--mathml",
        "--toc", "--toc-depth=3",
        f"--template={TOOLS / 'fragment.html'}",
        f"--lua-filter={TOOLS / 'links.lua'}",
    ]
    env = dict(os.environ, SITE_REPO=config["repo"], SITE_BRANCH=config["branch"])
    output = run(command, ROOT, f"pandoc on {src}", env)
    meta, rest = output.split(TOC_MARK, 1)
    toc, body = rest.split(BODY_MARK, 1)
    return json.loads(meta), toc.strip(), body.strip()


def build_deck(path: str, staging: Path) -> None:
    """Builds a slides.md into slides.html, a reveal.js deck."""
    folder = ROOT / posixpath.dirname(path)
    target = staging / posixpath.dirname(path) / "slides.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    if (folder / "Makefile").exists():
        # The deck has its own build (template, CSS, options): use it.
        run(["make", "--silent", "--no-print-directory", "slides.html"], folder, f"make in {folder.name}")
        shutil.copy2(folder / "slides.html", target)
        return
    command = ["pandoc", "slides.md", "--to=revealjs", "--standalone", f"--output={target}"]
    if (folder / "slides.css").exists():
        command.append("--css=slides.css")
    run(command, folder, f"pandoc on {path}")


def page_date(page: Page) -> dt.date:
    value = plain(str(page.meta.get("date", "")))
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise BuildError(f"{page.src}: add a date like 2026-10-18 to the front matter") from None


def sort_sections(pages: list[Page], config: dict) -> dict[str, list[Page]]:
    """Finds the pages of each section (blog/x.md or talks/y/index.md), newest first."""
    sections = {name: [] for name in config["sections"]}
    for page in pages:
        parts = page.src.split("/")
        if parts[0] not in sections:
            continue
        if (len(parts) == 2 and parts[1] != "index.md") or (len(parts) == 3 and parts[2] == "index.md"):
            page.section = parts[0]
            page.date = page_date(page)
            sections[parts[0]].append(page)
    for items in sections.values():
        items.sort(key=lambda page: (page.date, page.src), reverse=True)
    return sections


def build(drafts: bool = False) -> Site:
    started = time.monotonic()
    config = load_config()
    page_paths, deck_paths, file_paths = find_sources(config)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        converted = list(pool.map(lambda path: convert(path, config), page_paths))
    pages = [Page(path, *result) for path, result in zip(page_paths, converted)]

    if not drafts:
        # A draft index.md hides its whole folder: the talk page, slides, and code.
        hidden = [p.folder + "/" for p in pages if p.is_draft and p.is_index and p.folder]

        def shown(path: str) -> bool:
            return not any(path.startswith(folder) for folder in hidden)

        pages = [p for p in pages if not p.is_draft and shown(p.src)]
        deck_paths = [path for path in deck_paths if shown(path)]
        file_paths = [path for path in file_paths if shown(path)]

    for page in pages:
        if not page.text("title"):
            raise BuildError(f"{page.src}: add a title to the front matter")
    site = Site(
        config=config,
        layout=(ROOT / "templates" / "layout.html").read_text(encoding="utf-8"),
        pages=pages,
        sections=sort_sections(pages, config),
        decks={posixpath.dirname(path) for path in deck_paths},
    )

    # Build into a fresh folder, then swap it in, so a failed build (or a
    # preview server) never sees a half-written site.
    staging = OUT.with_name(OUT.name + ".new")
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir()
    for path in file_paths:
        target = staging / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
    # Decks come after the files, so a fresh slides.html replaces a stale copy.
    for path in deck_paths:
        build_deck(path, staging)
    for page in pages:
        target = staging / page.out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(page, site), encoding="utf-8")
    for name, section in config["sections"].items():
        if section.get("feed"):
            write_feed(name, site, staging)
    write_sitemap(site, staging)
    shutil.rmtree(OUT, ignore_errors=True)
    staging.rename(OUT)

    seconds = time.monotonic() - started
    print(
        f"Built {plural(len(pages), 'page')}, {plural(len(deck_paths), 'slide deck')}, and "
        f"{plural(len(file_paths), 'other file')} into {OUT.name}/ in {seconds:.1f} s."
    )
    return site


def plural(count: int, noun: str) -> str:
    return f"{count} {noun}{'' if count == 1 else 's'}"


# Rendering ------------------------------------------------------------------


def render_page(page: Page, site: Site) -> str:
    config = site.config
    if page.src == "404.md":
        # GitHub serves the 404 page at any address, so its relative links
        # need a <base> that points at the site root.
        root = ""
        base = f'<base href="{attr(urllib.parse.urlsplit(config["url"]).path)}">'
    else:
        root = "../" * page.out.count("/")
        base = ""
    body = LIST_RE.sub(lambda match: render_list(match, page, root, site), page.body)

    parts = [render_hero(root, site) if page.meta.get("layout") == "home" else render_header(page, root, site)]
    if page.is_index and page.folder in site.decks:
        title = attr(plain(page.text("title")))
        parts.append(
            f'<div class="deck"><iframe src="slides.html" title="Slides: {title}" '
            'loading="lazy" allowfullscreen></iframe></div>'
        )
    if page.meta.get("toc") is True and page.toc:
        parts.append(f'<nav class="toc" aria-labelledby="toc-title"><h2 id="toc-title">Contents</h2>{page.toc}</nav>')
    parts.append(f'<div class="prose">\n{body}\n</div>')

    lang, direction = page.text("lang"), page.text("dir")
    article = ' class="page"' + (f' lang="{attr(lang)}"' if lang else "") + (f' dir="{attr(direction)}"' if direction else "")
    title = plain(page.text("title"))
    values = {
        "base": base,
        "lang": attr(config.get("lang", "en")),
        "title": attr(title if title == config["title"] else f"{title} · {config['title']}"),
        "og_title": attr(title),
        "og_type": "article" if page.section else "website",
        "description": attr(plain(page.text("description")) or config["description"]),
        "canonical": attr(config["url"] + page.url),
        "site_title": attr(config["title"]),
        "author": attr(config["author"]["name"]),
        "initials": attr(config["author"].get("initials", "")),
        "root": attr(root),
        "home": attr(root or "./"),
        "feeds": render_feed_links(root, site),
        "nav": render_nav(page, root, site),
        "content": f"<article{article}>\n" + "\n".join(parts) + "\n</article>",
        "footer": render_footer(root, site),
        "year": str(dt.date.today().year),
    }
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda match: values[match.group(1)], site.layout)


def render_hero(root: str, site: Site) -> str:
    author = site.config["author"]
    if author.get("avatar"):
        picture = f'<img class="avatar" src="{attr(root + author["avatar"])}" alt="" width="112" height="112">'
    else:
        picture = f'<span class="avatar" aria-hidden="true">{html.escape(author.get("initials", ""))}</span>'
    tagline = f'<p class="hero-tagline">{html.escape(author["tagline"])}</p>\n' if author.get("tagline") else ""
    return (
        f'<section class="hero">\n{picture}\n<div class="hero-text">\n'
        f'<h1 class="hero-name">{html.escape(author["name"])}</h1>\n{tagline}'
        f"{render_social(root, site)}\n</div>\n</section>"
    )


def render_header(page: Page, root: str, site: Site) -> str:
    is_event = bool(page.text("event"))
    date_attr = f' data-event-date="{page.date.isoformat()}"' if is_event and page.date else ""
    lines = [f'<header class="page-header"{date_attr}>']
    if page.section:
        section_title = site.config["sections"][page.section].get("title", page.section.title())
        badges = (UPCOMING if is_event else "") + (DRAFT if page.is_draft else "")
        lines.append(f'<p class="kicker"><a href="{attr(root + page.section)}/">{html.escape(section_title)}</a>{badges}</p>')
    elif page.is_draft:
        lines.append(f'<p class="kicker">{DRAFT}</p>')
    lines.append(f'<h1 class="title">{page.text("title")}</h1>')
    if subtitle := page.text("subtitle"):
        lines.append(f'<p class="subtitle">{subtitle}</p>')

    facts = []
    if page.date:
        facts.append(f'<time datetime="{page.date.isoformat()}">{page.date.isoformat()}</time>')
    if is_event:
        facts += event_facts(page, linked=True, with_format=True)
    elif page.section:
        facts.append(f"{reading_minutes(page.body)} min read")
    if facts:
        lines.append(f'<p class="meta">{" · ".join(facts)}</p>')

    tags = page.meta.get("tags")
    if isinstance(tags, list) and tags:
        lines.append('<ul class="tags">' + "".join(f"<li>{tag}</li>" for tag in tags if isinstance(tag, str)) + "</ul>")

    links = event_links(page, "", site)
    if talk_url := page.url_field("talk_url"):
        links.append(("Talk page", talk_url))
    if links:
        buttons = [
            f'<a class="button{" primary" if i == 0 else ""}" href="{attr(url)}">{label}</a>'
            for i, (label, url) in enumerate(links)
        ]
        lines.append(f'<p class="actions">{"".join(buttons)}</p>')
    lines.append("</header>")
    return "\n".join(lines)


def event_facts(page: Page, linked: bool, with_format: bool = False) -> list[str]:
    """Event, location, and format of a talk or meetup, as HTML."""
    facts = []
    if event := page.text("event"):
        url = page.url_field("event_url")
        facts.append(f'<a href="{attr(url)}">{event}</a>' if linked and url else event)
    if location := page.text("location"):
        facts.append(location)
    if with_format and (talk_format := page.text("format")):
        facts.append(talk_format)
    return facts


def event_links(page: Page, base: str, site: Site) -> list[tuple[str, str]]:
    """Slides, PDF, video, and code links of a talk or meetup page.

    Relative addresses are relative to the page's folder; `base` is the way
    from the current page to that folder.
    """
    folder = ROOT / page.folder
    links = []
    slides = page.url_field("slides")
    if not slides and page.is_index and page.folder in site.decks:
        slides = "slides.html"
    pdf = page.url_field("pdf")
    if not pdf and page.is_index and (folder / "slides.pdf").exists():
        pdf = "slides.pdf"
    code = page.url_field("code")
    if not code and page.is_index and (folder / "demos").is_dir():
        code = f"{site.config['repo']}/tree/{site.config['branch']}/{page.folder}"
    for label, url in (("Slides", slides), ("PDF", pdf), ("Video", page.url_field("video")), ("Code", code)):
        if url:
            links.append((label, url if is_absolute(url) else base + url))
    return links


def reading_minutes(body: str) -> int:
    return max(1, round(len(re.findall(r"\w+", plain(body))) / 220))


def render_list(match: re.Match, page: Page, root: str, site: Site) -> str:
    """Replaces <!-- list:NAME limit=N --> with the pages of a section."""
    name = match.group(1)
    if name not in site.sections:
        raise BuildError(f"{page.src}: <!-- list:{name} --> needs a [sections.{name}] in site.toml")
    options = dict(option.split("=", 1) for option in match.group(2).split())
    items = site.sections[name]
    if "limit" in options:
        if not options["limit"].isdigit():
            raise BuildError(f"{page.src}: limit in <!-- list:{name} --> must be a number")
        items = items[: int(options["limit"])]
    if not items:
        return '<p class="empty">Nothing here yet.</p>'

    level = 2 if page.src == f"{name}/index.md" else 3
    entries = []
    for item in items:
        is_event = bool(item.text("event"))
        day = item.date.isoformat()
        date_attr = f' data-event-date="{day}"' if is_event else ""
        badges = (UPCOMING if is_event else "") + (DRAFT if item.is_draft else "")
        lines = [
            f'<li class="entry"{date_attr}>',
            f'<div class="entry-date"><time datetime="{day}">{day}</time>{badges}</div>',
            '<div class="entry-body">',
            f'<h{level} class="entry-title"><a href="{attr(root + item.url)}">{item.text("title")}</a></h{level}>',
        ]
        if is_event:
            if subtitle := item.text("subtitle"):
                lines.append(f'<p class="entry-subtitle">{subtitle}</p>')
            if facts := event_facts(item, linked=False):
                lines.append(f'<p class="entry-meta">{" · ".join(facts)}</p>')
            if links := event_links(item, f"{root}{item.folder}/", site):
                chips = "".join(f'<a class="chip" href="{attr(url)}">{label}</a>' for label, url in links)
                lines.append(f'<p class="entry-links">{chips}</p>')
        elif description := item.text("description"):
            lines.append(f'<p class="entry-desc">{description}</p>')
        lines.append("</div>\n</li>")
        entries.append("\n".join(lines))
    return '<ul class="entries">\n' + "\n".join(entries) + "\n</ul>"


def render_nav(page: Page, root: str, site: Site) -> str:
    links = []
    for item in site.config.get("nav", []):
        path = item["path"]
        current = page.url == path or (path.endswith("/") and page.url.startswith(path))
        aria = ' aria-current="page"' if current else ""
        links.append(f'<a href="{attr(root + path)}"{aria}>{html.escape(item["title"])}</a>')
    return "\n".join(links)


def feeds(site: Site) -> list[tuple[str, str]]:
    """(section name, title) of each section with a feed."""
    return [(name, s.get("title", name)) for name, s in site.config["sections"].items() if s.get("feed")]


def render_social(root: str, site: Site) -> str:
    items = []
    for link in site.config.get("social", []):
        icon = ICONS.get(link.get("icon", "link"), ICONS["link"])
        items.append(f'<li><a href="{attr(link["url"])}" rel="me">{icon}<span>{html.escape(link["title"])}</span></a></li>')
    for name, _ in feeds(site):
        items.append(f'<li><a href="{attr(root + name)}/feed.xml">{ICONS["rss"]}<span>RSS</span></a></li>')
    return '<ul class="social">\n' + "\n".join(items) + "\n</ul>"


def render_feed_links(root: str, site: Site) -> str:
    return "\n".join(
        f'<link rel="alternate" type="application/atom+xml" '
        f'title="{attr(title + " · " + site.config["title"])}" href="{attr(root + name)}/feed.xml">'
        for name, title in feeds(site)
    )


def render_footer(root: str, site: Site) -> str:
    links = [f'<a href="{attr(site.config["repo"])}">Source</a>']
    links += [f'<a href="{attr(root + name)}/feed.xml">RSS</a>' for name, _ in feeds(site)]
    return " · ".join(links)


def write_feed(name: str, site: Site, staging: Path) -> None:
    """Writes NAME/feed.xml, an Atom feed of the latest pages of a section."""
    config = site.config
    items = site.sections.get(name, [])[:20]
    feed_url = f"{config['url']}{name}/feed.xml"
    updated = max((page.date for page in items), default=dt.date.today()).isoformat()
    title = f"{config['sections'][name].get('title', name)} · {config['title']}"
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"<title>{attr(title)}</title>",
        f'<link rel="alternate" href="{attr(config["url"] + name)}/"/>',
        f'<link rel="self" href="{attr(feed_url)}"/>',
        f"<id>{attr(feed_url)}</id>",
        f"<updated>{updated}T00:00:00Z</updated>",
        f"<author><name>{attr(config['author']['name'])}</name></author>",
    ]
    for page in items:
        url = config["url"] + page.url
        day = page.date.isoformat()
        lines += [
            "<entry>",
            f'<title type="html">{attr(page.text("title"))}</title>',
            f'<link rel="alternate" href="{attr(url)}"/>',
            f"<id>{attr(url)}</id>",
            f"<published>{day}T00:00:00Z</published>",
            f"<updated>{day}T00:00:00Z</updated>",
        ]
        if description := page.text("description"):
            lines.append(f'<summary type="html">{attr(description)}</summary>')
        lines += [f'<content type="html" xml:base="{attr(url)}">{attr(page.body)}</content>', "</entry>"]
    lines.append("</feed>")
    (staging / name).mkdir(parents=True, exist_ok=True)
    (staging / name / "feed.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_sitemap(site: Site, staging: Path) -> None:
    urls = sorted(site.config["url"] + page.url for page in site.pages if page.src != "404.md")
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines += [f"<url><loc>{attr(url)}</loc></url>" for url in urls]
    lines.append("</urlset>")
    (staging / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


# Checking, serving, and new posts -------------------------------------------


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.links += [value for name, value in attrs if name in ("href", "src") and value]


def check_links(site: Site) -> list[str]:
    """Returns the internal links in _site/ that point to a missing file."""
    base = urllib.parse.urlsplit(site.config["url"]).path
    problems = []
    for page in sorted(OUT.rglob("*.html")):
        collector = LinkCollector()
        collector.feed(page.read_text(encoding="utf-8"))
        for link in collector.links:
            parts = urllib.parse.urlsplit(link)
            if parts.scheme or parts.netloc or not parts.path:
                continue  # another site, mailto:, or an anchor on the same page
            path = urllib.parse.unquote(parts.path)
            if path.startswith("/"):
                target = OUT / path.removeprefix(base) if path.startswith(base) else None
            else:
                target = page.parent / path
            if target is not None:
                target = Path(os.path.normpath(target))
                if target.is_dir():
                    target /= "index.html"
            if target is None or not target.is_relative_to(OUT) or not target.is_file():
                problems.append(f"{page.relative_to(OUT)}: broken link {link}")
    return problems


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass  # keep the terminal for build messages


def source_stamp() -> dict[str, int]:
    stamp = {}
    for folder, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != ".git" and not d.startswith("_site")]
        for name in names:
            path = os.path.join(folder, name)
            try:
                stamp[path] = os.stat(path).st_mtime_ns
            except FileNotFoundError:
                pass
    return stamp


def serve(port: int) -> None:
    handler = functools.partial(QuietHandler, directory=str(OUT))
    server = http.server.ThreadingHTTPServer(("", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Serving the site at http://localhost:{port}/ and rebuilding on changes. Press Ctrl+C to stop.")
    stamp = source_stamp()
    try:
        while True:
            time.sleep(1)
            if source_stamp() == stamp:
                continue
            try:
                build(drafts=True)
            except BuildError as error:
                print(f"error: {error}", file=sys.stderr)
            stamp = source_stamp()  # includes decks that the build itself made
    except KeyboardInterrupt:
        print()
    finally:
        server.shutdown()


def slugify(text: str) -> str:
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def new_post(title: str) -> Path:
    today = dt.date.today().isoformat()
    path = ROOT / "blog" / f"{today}-{slugify(title) or 'post'}.md"
    if path.exists():
        raise BuildError(f"{path.relative_to(ROOT)} already exists")
    path.write_text(
        "---\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f"date: {today}\n"
        'description: ""  # one sentence for the post list and the feed\n'
        "tags: []\n"
        "draft: true  # delete this line to publish the post\n"
        "---\n\n"
        "Write the post here. Use `##` for section headings.\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Builds the site into _site/ with pandoc.")
    parser.add_argument("--drafts", action="store_true", help="also build pages marked draft: true")
    parser.add_argument("--check", action="store_true", help="check every internal link after building")
    parser.add_argument("--serve", action="store_true", help="build with drafts, serve the site, and rebuild on changes")
    parser.add_argument("--port", type=int, default=8000, help="port for --serve (default: 8000)")
    parser.add_argument("--new-post", metavar="TITLE", help="start a draft blog post with this title")
    args = parser.parse_args()
    try:
        if args.new_post:
            print(f"Created {new_post(args.new_post).relative_to(ROOT)}")
            return 0
        site = build(drafts=args.drafts or args.serve)
        if args.check:
            problems = check_links(site)
            for problem in problems:
                print(problem, file=sys.stderr)
            if problems:
                return 1
            print("All internal links work.")
        if args.serve:
            serve(args.port)
    except BuildError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        if error.filename in ("pandoc", "make"):
            print(f"error: {error.filename} is not installed", file=sys.stderr)
            return 1
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
