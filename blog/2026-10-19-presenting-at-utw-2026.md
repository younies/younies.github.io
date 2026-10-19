---
title: "Presenting at UTW 2026: Beyond Meters and Miles"
date: 2026-10-19
description: "Tomorrow I'm giving a tutorial on measurement unit internationalization with Unicode CLDR and ICU at the Unicode Technology Workshop in Nancy. The slides and code are online."
image: /talks/2026-10-utw-beyond-meters-and-miles/card.png
image_alt: "Beyond Meters and Miles: a tutorial by Younies Mahmoud at the Unicode Technology Workshop 2026, Nancy, October 20, 2026"
tags: [utw, cldr, icu, units]
---

Tomorrow morning I'm giving a tutorial at the
[Unicode Technology Workshop 2026](https://www.unicode.org/events/utw/2026/)
in Nancy, France.

::: note
**Beyond Meters and Miles: Mastering Measurement Unit Internationalization with
CLDR and ICU**\
Tuesday, October 20, 2026 · 10:00–10:45 · Creativity Station (Room 109), Campus
Artem, Nancy
:::

## Why units are harder than they look

"It's 30 degrees today." Is that a beach day or a freezing one? A number without
its unit is ambiguous. And even when the unit is known, the right one depends on
who is reading and what is being measured. Someone who is 1.8 meters tall is
"5 feet, 11 inches" to a reader in the US: not "1.8 meters", not "0.00111847
miles", and not "5 feet, 10.8661 inches". Road distances, the weather, and a
person's height each follow their own conventions, often within the same
country.

Language adds another layer. In French, the words around a unit agree with its
grammatical gender ("1 mois offert" but "1 semaine offerte"). In German, the unit
itself changes with its grammatical case ("100 Kilometer", but "mit 100
Kilometern").

## What the tutorial covers

- How the Unicode CLDR unit preference data picks the output unit from the
  region, the usage (such as `person-height` or `road`), and the value
- How ICU converts between units, splits a value into mixed units such as feet
  and inches, rounds it, and carries the rounding back up
- Hands-on code in ICU4J (Java) and ICU4C (C++)
- Grammatical gender and case in `MessageFormat`, with French and German
  examples
- What's coming in ICU4X and ECMAScript

## Slides and code

The slides are online, and every output on them, from the chat bubbles to the
tables, comes from ICU4J and ICU4C test programs that you can run yourself.

- **Slides:** [younies.github.io/utw2026/slides](https://younies.github.io/utw2026/slides/)
- **Code:** [younies.github.io/utw2026/code](https://younies.github.io/utw2026/code/)
- **Talk page:** [younies.github.io/utw2026](https://younies.github.io/utw2026/),
  with the abstract and the slides

If you're attending UTW, find me after the session. I'm happy to talk about
units, CLDR, ICU, or ICU4X.
