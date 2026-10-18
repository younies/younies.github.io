# younies.github.io

The source of my personal site,
**[younies.github.io](https://younies.github.io/)**: blog posts,
the slides and code from my talks, meetups, and projects.

Pages are written in Markdown and built into HTML with
[pandoc](https://pandoc.org/), the same tool that builds my
[reveal.js](https://revealjs.com/) slide decks, plus a small Python script.
GitHub Actions builds and publishes the site on every push to `main`.

## What's here

| Path | What it holds | On the site |
|---|---|---|
| [`index.md`](index.md) | Home page: introduction, latest posts, talks, open source | `/` |
| [`blog/`](blog/) | Blog posts, one file each: `YYYY-MM-DD-short-title.md` | `/blog/` |
| [`talks/`](talks/) | One folder per talk, with its page, slides, and code | `/talks/` |
| [`meetups/`](meetups/) | One folder per meetup | `/meetups/` |
| [`projects/`](projects/) | Open-source work, mentoring, and community | `/projects/` |
| [`404.md`](404.md) | The "Page not found" page | |
| [`assets/`](assets/) | CSS, JavaScript, the icon, and images | `/assets/` |
| [`site.toml`](site.toml) | Settings: title, address, menu, links, and sections | |
| [`templates/layout.html`](templates/layout.html) | The layout around every page: header, menu, footer | |
| [`tools/`](tools/) | The build script and its pandoc helpers | |
| [`.github/workflows/pages.yml`](.github/workflows/pages.yml) | Builds, checks, and publishes the site | |

## Write a blog post

1. Start a draft:

   ```sh
   make post TITLE="Formatting units in ICU4X"
   ```

   This creates `blog/2026-10-18-formatting-units-in-icu4x.md` (with today's
   date):

   ```yaml
   ---
   title: "Formatting units in ICU4X"
   date: 2026-10-18
   description: ""  # one sentence for the post list and the feed
   tags: []
   draft: true  # delete this line to publish the post
   ---
   ```

2. Write the post in [pandoc Markdown](https://pandoc.org/MANUAL.html#pandocs-markdown).
   The title comes from the front matter, so use `##` for section headings.
   Name the language of each code block (```` ```rust ````) to get syntax
   highlighting; every code block also gets a Copy button.
3. Preview it with `make serve`, which also shows drafts.
4. Delete the `draft: true` line, commit, and push. The site updates in about
   a minute.

A post with images can be a folder instead, `blog/YYYY-MM-DD-short-title/index.md`,
with the images next to it.

## Add a talk

Each talk is a folder named `talks/YYYY-MM-<event>-<short-title>/`:

| File | What it is |
|---|---|
| `index.md` | The talk page: front matter (below) and the abstract |
| `slides.md` | The deck in pandoc Markdown. The site builds it into `slides.html` |
| `Makefile`, `slides.css`, `reveal-template.html` | Optional. With a Makefile, the site runs `make slides.html` in the folder, so a deck keeps its own pandoc options, template, and theme. Without one, it runs `pandoc slides.md -t revealjs -s` and uses `slides.css` if there is one |
| `slides.pdf` | Optional. A PDF copy of the slides |
| `demos/` | Optional. The code behind the examples on the slides |
| `README.md` | Optional. Notes for readers on GitHub; not part of the site |

The front matter of `index.md`:

```yaml
---
title: Beyond Meters and Miles
subtitle: Mastering Measurement Unit Internationalization with CLDR and ICU
date: 2026-10-20
event: Unicode Technology Workshop 2026
event_url: https://www.unicode.org/events/utw/2026/
talk_url: https://www.unicode.org/events/utw/2026/talks/measurement-units/
location: Nancy, France
format: Tutorial
description: One sentence about the talk.
tags: [cldr, icu, units]
---
```

The talk page shows the slides inline, with buttons for the slides, the PDF,
the video, and the code. Each button appears when the folder has the matching
file (`slides.md`, `slides.pdf`, or `demos/`); to link somewhere else, set
`slides`, `pdf`, `video`, or `code` to an address. Talks that haven't happened
yet get an "Upcoming" label.

Meetups work the same way, in `meetups/YYYY-MM-<name>/index.md`.

## Build and preview

You need pandoc 3.7 (the version CI uses), Python 3.11 or later, and make.

```sh
make            # build the site into _site/
make serve      # preview at http://localhost:8000/ with drafts; rebuilds on every change
make check      # build, then check every internal link (CI runs this)
make clean      # delete _site/
```

Use `make serve PORT=8765` to preview on another port.

## Publish

[`pages.yml`](.github/workflows/pages.yml) runs `make check` on every push and
pull request, and publishes `_site/` to GitHub Pages from `main`. In the
repository settings, **Pages → Build and deployment → Source** is set to
**GitHub Actions**.

All links on the site are relative, so it works at any address. To move it
(for example, to a custom domain), change `url` in [`site.toml`](site.toml),
which the feed, the sitemap, and the 404 page use.

## Writing tips

- Link to other pages by their Markdown files, such as
  `[talks](../talks/index.md)`. The build points those links at the HTML pages,
  so they work both here on GitHub and on the site.
- Wrap text in `::: note`, `::: tip`, or `::: warning` (closed by `:::`) for a
  call-out box.
- Write math as `$E = mc^2$` or `$$…$$`; it is rendered as MathML.
- A page in another language can set `lang: fr` in its front matter, and
  `dir: rtl` for Arabic or Hebrew.
- Add `toc: true` to the front matter for a table of contents.
- Any page can list a section with `<!-- list:blog -->` or
  `<!-- list:talks limit=3 -->`. Sections are set in `site.toml`.

---

This is a personal site. Opinions are my own.
