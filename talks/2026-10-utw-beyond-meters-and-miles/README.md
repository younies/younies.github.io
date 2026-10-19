# Beyond Meters and Miles

**Mastering Measurement Unit Internationalization with CLDR and ICU**

| | |
|---|---|
| Event | [Unicode Technology Workshop 2026](https://www.unicode.org/events/utw/2026/) (UTW 2026), Nancy, France |
| Session | Tutorial · Tuesday, October 20, 2026 · 10:00–10:45 · Creativity Station (Room 109), Campus Artem |
| Talk page | [unicode.org/events/utw/2026/talks/measurement-units](https://www.unicode.org/events/utw/2026/talks/measurement-units/) |
| Slides | [younies.github.io/talks/2026-10-utw-beyond-meters-and-miles](https://younies.github.io/talks/2026-10-utw-beyond-meters-and-miles/) |

## Abstract

Internationalizing measurement units is deceptively challenging. At first
glance, it seems as simple as multiplying a value and translating a label—until
you realize that length alone is expressed in miles on a highway sign, in feet
and inches for a person’s height, and in meters in a scientific article, often
within the same country.

In this tutorial, we explore how Unicode CLDR and ICU make measurements read
naturally for every user. You will learn how to:

- Show measurements in the units people expect for their region and context,
  such as road distances, weather, or a person’s height
- Convert between units, including splitting one value into combined units like
  feet and inches, with natural rounding
- Format units in the right grammatical case, such as nominative or dative,
  since many languages change how a unit is written depending on its role in a
  sentence
- Retrieve a unit’s grammatical gender, so you can make surrounding words, such
  as articles and adjectives, agree with it

## Files

| File | What it is |
|---|---|
| [slides.md](slides.md) | The deck source, in pandoc Markdown for reveal.js. Speaker notes are the `::: notes` blocks. |
| [slides.css](slides.css) | Deck styles |
| [reveal-template.html](reveal-template.html) | pandoc's reveal.js template plus the reveal.js highlight plugin, for line-by-line code steps |
| [Makefile](Makefile) | Builds the deck with pandoc, and runs the slide test cases (`make test`) |
| [demos/java/UnitsTest.java](demos/java/UnitsTest.java) | ICU4J test cases, one per slide, for every output on the slides |
| [demos/cpp/units_test.cpp](demos/cpp/units_test.cpp) | The same test cases in ICU4C, where the C++ API has the output |
| [index.md](index.md) | The talk page on the site, which shows the slides |
| [qr-page.svg](qr-page.svg), [qr-slides.svg](qr-slides.svg), [qr-code.svg](qr-code.svg) | QR codes on the Questions slide: my page, the slides (younies.github.io/utw2026/slides), and the code demo (younies.github.io/utw2026/code), made with [segno](https://github.com/heuer/segno) |

## Build, present, and export

`slides.md` is the single source. [pandoc](https://pandoc.org/) 3 turns it into a
[reveal.js](https://revealjs.com/) deck, and the PDF backup is printed from that
deck. The site builds the deck on every push; to build it yourself:

- **Build:** run `make` to write `slides.html`. It loads reveal.js from a CDN, so
  it needs internet. Run `make offline` for `slides-offline.html`, a single file
  that works without internet (building it needs internet once).
- **Present:** open the HTML file in a browser. Press `S` for the speaker view
  (notes, timer, next slide), `F` for full screen, and `Esc` for the overview.
- **PDF backup:** open `slides.html?print-pdf` in Chrome, print, and choose "Save
  as PDF" with margins set to "None" and background graphics on. Each
  step-by-step reveal gets its own page, so you can click through the PDF like
  the live deck. For one page per slide, open
  `slides.html?print-pdf&pdfSeparateFragments=false` instead.

## Test the slides

Every output on the slides (tables, chat bubbles, code comments, and numbers
in the diagrams) is a test case. The expected values come from ICU 79
(development) built from source; other ICU versions can differ slightly because
they ship different CLDR data.

```sh
make test                      # an ICU checkout next to this repository (../../../icu), with ICU4J and ICU4C built
make test ICU=/path/to/icu     # or anywhere else
make test-java                 # only ICU4J (Java 11 or later)
make test-cpp                  # only ICU4C
```

Each test is named after a slide and checks every output on it:

```java
// Slide "Person height: 1.8 meters".
static void personHeightTable() {
    assertPersonHeight("de-DE", "180 Zentimeter", "centimeter");
    assertPersonHeight("ar-EG", "متر و٨٠ سنتيمتر", "meter-and-centimeter");
    ...
}
```

A check fails if ICU returns something else, if the expected value is not in
`slides.md`, or if the slide title is missing. So a test fails when ICU changes,
and also when a slide is edited without updating its test:

```text
PASS  Person height: 1.8 meters                          14 checks
FAIL  Road distance: same code, different values         14 checks
      "150 yards" is not in slides.md
```

Notes:

- The conversion slides use ICU4J's internal `UnitsConverter`, which is not
  public API.
- ICU4J's `getNounClass()` returns `undefined` when `usage()` is set (ICU4C is
  correct). `UnitsTest.java` asserts the current behavior, so it fails once the
  bug is fixed; then update the test and the slide notes.
