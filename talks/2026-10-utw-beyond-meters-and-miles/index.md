---
title: Beyond Meters and Miles
subtitle: Mastering Measurement Unit Internationalization with CLDR and ICU
date: 2026-10-20
event: Unicode Technology Workshop 2026
event_url: https://www.unicode.org/events/utw/2026/
talk_url: https://www.unicode.org/events/utw/2026/talks/measurement-units/
location: Nancy, France
format: Tutorial
description: How Unicode CLDR and ICU choose, convert, round, and inflect measurement units so they read naturally for every user.
tags: [cldr, icu, units]
image: card.png
---

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

## Outline

1. What do we need for locale-aware unit formatting?
2. CLDR: unit preferences and conversion data
3. ICU: convert, cascade, round, and route
4. Tutorial 1: person height and road distance (ICU4J and ICU4C)
5. Grammar: gender (Tutorial 2) and case (Tutorial 3) in `MessageFormat`
6. ICU4X & ECMAScript: `Amount`, Smart Unit Preferences, and what’s coming

## Slides and code

The slides are at the top of this page. Click them, then use the arrow keys to
step through; press `F` for full screen and `S` for the speaker notes. You can
also [open the slides on their own](slides.html).

Every output on the slides, from the chat bubbles to the tables, comes from the
ICU4J and ICU4C test programs in
[`demos/`](https://github.com/younies/younies.github.io/tree/HEAD/talks/2026-10-utw-beyond-meters-and-miles/demos).
The [README](README.md) explains how to build the slides and run the tests.
