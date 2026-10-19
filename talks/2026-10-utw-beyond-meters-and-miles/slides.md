---
pagetitle: "Beyond Meters and Miles: Mastering Measurement Unit Internationalization with CLDR and ICU"
author: Younies Mahmoud
lang: en
theme: white
transition: fade
slideNumber: true
hash: true
---

# Beyond Meters and Miles {.cover data-background-gradient="linear-gradient(135deg, #312e81 0%, #6d28d9 55%, #db2777 100%)"}

## Mastering Measurement Unit Internationalization with CLDR and ICU

**Younies Mahmoud** · Software Engineer, Google

Unicode Technology Workshop 2026 · Nancy · October 20, 2026

::: notes
[0:00–0:20] Good morning, everyone. I'm Younies, a software engineer on the
Internationalization team at Google in Zürich. I work on ICU, ICU4X, and CLDR,
mostly on measurement units, grammatical inflection, and number formatting.
In the next half hour, we'll see why formatting a measurement is much more than
translating a label, and how CLDR and ICU do the hard work for you.

Time plan (45-minute slot): about 30 minutes of content, then 10 minutes of
questions and 5 minutes of buffer.
Checkpoints: slide 7 at 5:00 · slide 15 at 9:05 · slide 21 at 12:30 ·
slide 28 at 19:00 · slide 35 at 28:00 · slide 39 at 30:30.
Skip if behind: the ICU4C walkthrough (slide 24), the weather bonus (slide 27),
the runtime-gender slide (slide 31), and the cases table (slide 33).
:::

# Is 30 degrees hot or cold?

> “It’s 30 degrees today!”

🙋 **Quick poll:** a beach day, or freezing?

::: incremental
- **30°C:** a summer beach day, about 86°F 🏖️
- **30°F:** below freezing, about -1°C 🥶
:::

. . .

**Both answers are right: a number without its unit is ambiguous.**

::: notes
[0:20–1:20] We're in France, so read the quote and ask for hands: who is packing for the beach?
Then: who would grab a winter coat? (Anyone from the US?)
Click to reveal Celsius, then Fahrenheit, then the punchline.
Bridge: even when we know the unit, choosing the right one for each person is the hard part.
Let me show you with a simple question.
:::

# How tall are you?

🇺🇸 **Alex** (US) asks. 🇨🇭 **Sam** (Switzerland, 1.8 m tall) answers.

::::: chat
::: chat-names
[🇺🇸 Alex]{.who} [Sam 🇨🇭]{.who}
:::

::: {.msg .alex}
How tall are you?
:::

:::: round
::: {.msg .sam .fragment}
[1.8 meters]{.wrong}
:::

::: {.msg .alex .fragment}
🤨 Meters?
:::

::: {.thought .fragment}
💭 Aha, they don't use metric. They use imperial units!
:::
::::

:::: round
::: {.msg .sam .fragment}
[0.00111847 miles]{.wrong}
:::

::: {.msg .alex .fragment}
😱 Miles?!
:::

::: {.thought .fragment}
💭 Right: miles are for roads. For a person's height, it's feet and inches.
:::
::::

:::: round
::: {.msg .sam .fragment}
[5 feet, 10.8661 inches]{.wrong}
:::

::: {.msg .alex .fragment}
😅 Way too precise!
:::

::: {.thought .fragment}
💭 Nobody says 10.8661 inches: round to the nearest inch.
:::
::::

:::: round
::: {.msg .sam .correct .fragment}
5 feet, 11 inches ✅
:::

::: {.msg .alex .fragment}
😊 Got it!
:::
::::
:::::

::: notes
[1:20–2:40] Act it out: you are Sam (from Switzerland, like me), the audience is Alex (from the US).
Alex asks on the left; Sam answers on the right. Click once per bubble.
Each surprise is one idea of this talk:
meters → the wrong measurement system for the US (region). Strictly, the US uses
US customary units, which CLDR calls "ussystem".
miles → right system, wrong unit for this usage: height is in feet and inches (usage, mixed units).
10.8661 inches → too precise (rounding).
5 feet, 11 inches → what ICU gives us in Tutorial 1.
:::

# How tall is your child?

🇺🇸 **Alex** asks again. 🇨🇭 **Sam**'s child is 0.7 m tall.

:::: chat
::: chat-names
[🇺🇸 Alex]{.who} [Sam 🇨🇭]{.who}
:::

::: {.msg .alex}
And how tall is your child?
:::

::: {.msg .sam .fragment}
[2 feet, 4 inches]{.wrong}
:::

::: {.msg .alex .fragment}
🤔 Feet? For a little kid?
:::

::: {.thought .fragment}
💭 Aha: small children are measured in inches only.
:::

::: {.msg .sam .correct .fragment}
28 inches ✅
:::

::: {.msg .alex .fragment}
😊 Perfect!
:::
::::

::: notes
[2:40–3:20] One more question from Alex. You (Sam) apply what you just learned:
feet and inches, rounded to the nearest inch (0.7 m = 27.56 in = 2 ft, 3.56 in).
Right system, right rounding, wrong unit for this value.
Same locale, same usage, a different value → a different unit.
The real rule: in the US, a height under 3 feet (91 cm) is in inches only.
We will see it in the CLDR data in a few minutes (geq="3.0").
"28 inches" is real ICU output: 0.7 m, en-US, usage person-height.
:::

# Today

1. **What do we need to format a unit?**
2. **CLDR:** unit preferences and conversion data
3. **ICU:** convert, cascade, round, and route
4. **Tutorial 1:** person height and road distance (ICU4J and ICU4C)
5. **Grammar:** gender (Tutorial 2) and case (Tutorial 3) in `MessageFormat`
6. **ICU4X & ECMAScript:** `Amount`, Smart Unit Preferences, and what’s coming
7. **Questions**

::: notes
[3:20–3:40] Keep this quick: it is the map for the talk.
:::

# What do we need to format a unit?

🙋 **What can Sam know about the user (and the measurement)?**

::: incremental
- 🌍 **Region:** Alex lives in the US → not meters
- 🎯 **Usage:** a person's height → feet and inches, not miles (`person-height`)
- 📏 **Value:** a small child → inches only (`0.7` vs `1.8`)
- 📐 **Input unit (category):** what we measured (`meter` → `length`)
:::

. . .

🙋 **Given that information, what does Sam want to know?**

. . .

**➜ Output unit and rounding (or precision):** `foot-and-inch` (5 feet, 11 inches) or `inch` (28 inches)

::: notes
[3:40–5:00] Ask the audience, then click once per answer; each one comes from the two chats.
Region (from the locale): "1.8 meters? 🤨" Usage: "Miles?! 😱" Value: "Feet? For a little kid? 🤔"
Plus the input unit, which tells us the category (meter → length).
Then ask: given that information, what does Sam want to know?
The output unit and the rounding (or precision).
Usage is the input most developers forget: the same length is formatted
differently on a road sign and for a person's height.
If asked: users can override the measurement system (en-US-u-ms-metric);
the width (long/short) and grammar (later today) are also inputs.
Bridge: who maps region, usage, value, and category to the output unit and precision? CLDR.
:::

# CLDR {.divider data-background-gradient="linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)"}

## Unit preferences and conversion data

::: notes
[5:00] Checkpoint.
:::

# Person height in CLDR

```{.xml data-line-numbers="1-6|1|2-5|3" data-fragment-index="0"}
<unitPreferences category="length" usage="person-height">
  <unitPreference regions="001">centimeter</unitPreference>
  <unitPreference regions="CA GB IN US" geq="3.0">foot-and-inch</unitPreference>
  <unitPreference regions="CA GB IN US">inch</unitPreference>
  <unitPreference regions="EG ES FR …">meter-and-centimeter</unitPreference>
</unitPreferences>
```

:::: steps
::: {.fragment data-fragment-index="0"}
- **category + usage**: what we measure, and why
:::

::: {.fragment data-fragment-index="1"}
- **regions**: who uses this preference (`001` is the world default)
:::

::: {.fragment data-fragment-index="2"}
- **geq**: use this unit when the value is at least this big (in that unit)
:::
::::

::: notes
[5:00–5:50] Click once per bullet; each one highlights its part of the XML.
Callback to Sam's child (slide 4). The US rule: 3 feet and taller → feet and inches;
shorter → inches only. 0.7 m in en-US → "28 inches".
Source: CLDR common/supplemental/units.xml (regions list shortened on the slide).
:::

# Road distance in CLDR: thresholds and rounding

```{.xml data-line-numbers="1-13|3-4,10-11|2-8" data-fragment-index="0"}
<unitPreferences category="length" usage="road">
  <unitPreference regions="001" geq="0.9">kilometer</unitPreference>
  <unitPreference regions="001" geq="300.0"
                  skeleton="precision-increment/50">meter</unitPreference>
  <unitPreference regions="001" geq="10"
                  skeleton="precision-increment/10">meter</unitPreference>
  <unitPreference regions="001"
                  skeleton="precision-increment/1">meter</unitPreference>
  <unitPreference regions="US" geq="0.5">mile</unitPreference>
  <unitPreference regions="US" geq="100.0"
                  skeleton="precision-increment/50">foot</unitPreference>
  …
</unitPreferences>
```

:::: steps
::: {.fragment data-fragment-index="0"}
- **skeleton**: how to round (here, to the nearest 50)
:::

::: {.fragment data-fragment-index="1"}
- The first row that matches wins
:::
::::

::: notes
[5:50–6:25] Click 1: the rows with precision-increment/50 round to the nearest 50.
Click 2: ICU checks the rows from the top; the first match wins
(320 m: less than 0.9 km, but at least 300 m → rounded to 50 → "300 Meter").
The UK uses yards for short road distances: see the next slide.
Source: CLDR units.xml (long rows wrapped, and only some rows shown).
:::

# What the CLDR data says

```{=html}
<svg class="unit-tree" viewBox="0 0 1060 420" role="img" aria-label="Decision graph from category length to usage person-height and road, then region, then value thresholds and output unit with precision">
  <defs>
    <linearGradient id="pref-cat" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#312e81"/><stop offset="1" stop-color="#4f46e5"/></linearGradient>
    <linearGradient id="pref-height" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4f46e5"/><stop offset="1" stop-color="#7c3aed"/></linearGradient>
    <linearGradient id="pref-road" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#059669"/><stop offset="1" stop-color="#0d9488"/></linearGradient>
  </defs>
  <text class="tree-label" x="14" y="20">CATEGORY</text>
  <text class="tree-label" x="180" y="20">USAGE</text>
  <text class="tree-label" x="392" y="20">REGION</text>
  <text class="tree-label" x="580" y="20">VALUE (geq)  ➜  OUTPUT UNIT &amp; PRECISION</text>

  <!-- Connector lines -->
  <g stroke="#cbd5e1" stroke-width="2.5" fill="none">
    <!-- length -> usages -->
    <path d="M126 216 L165 112"/><path d="M126 216 L165 308"/>
    <!-- person-height -> regions -->
    <path d="M335 112 L375 58"/><path d="M335 112 L375 112"/><path d="M335 112 L375 162"/>
    <!-- road -> regions -->
    <path d="M335 308 L375 236"/><path d="M335 308 L375 308"/><path d="M335 308 L375 380"/>
    <!-- regions -> thresholds -->
    <line x1="545" y1="58" x2="815" y2="58"/>
    <line x1="545" y1="112" x2="575" y2="112"/>
    <line x1="545" y1="162" x2="575" y2="162"/>
    <line x1="545" y1="236" x2="895" y2="236"/>
    <line x1="545" y1="308" x2="895" y2="308"/>
    <line x1="545" y1="380" x2="895" y2="380"/>
  </g>

  <!-- Category & Usage pills -->
  <g class="tree-compound">
    <rect x="10" y="190" width="116" height="52" rx="26" fill="url(#pref-cat)"/><text x="68" y="223">length</text>
    <rect x="165" y="88" width="170" height="48" rx="24" fill="url(#pref-height)"/><text x="250" y="119">person-height</text>
    <rect x="165" y="284" width="170" height="48" rx="24" fill="url(#pref-road)"/><text x="250" y="315">road</text>
  </g>

  <!-- Region boxes -->
  <g class="tree-leaf">
    <rect x="375" y="36" width="170" height="44" rx="10"/><text class="name" x="460" y="64" style="font-size:17px">CA · GB · IN · US</text>
    <rect x="375" y="90" width="170" height="44" rx="10"/><text class="name" x="460" y="118" style="font-size:17px">FR · EG · ES · …</text>
    <rect x="375" y="140" width="170" height="44" rx="10"/><text class="name" x="460" y="168" style="font-size:17px">001 (world)</text>

    <rect x="375" y="210" width="170" height="52" rx="10"/><text class="name" x="460" y="243" style="font-size:19px">US</text>
    <rect x="375" y="282" width="170" height="52" rx="10"/><text class="name" x="460" y="315" style="font-size:19px">GB</text>
    <rect x="375" y="354" width="170" height="52" rx="10"/><text class="name" x="460" y="387" style="font-size:18px">001 (world)</text>
  </g>

  <!-- Output unit + precision cards -->
  <g class="tree-leaf">
    <!-- person-height: CA GB IN US -->
    <rect x="575" y="34" width="232" height="48" rx="10"/>
    <text class="rate meter" x="691" y="53">≥ 3 ft · nearest 1 in</text>
    <text class="name" x="691" y="74" style="font-size:18px">foot-and-inch</text>

    <rect x="815" y="34" width="235" height="48" rx="10"/>
    <text class="rate meter" x="932" y="53">&lt; 3 ft · nearest 1 in</text>
    <text class="name" x="932" y="74" style="font-size:18px">inch</text>

    <!-- person-height: FR EG ... -->
    <rect x="575" y="90" width="475" height="44" rx="10"/>
    <text class="name" x="691" y="118" style="font-size:18px">meter-and-centimeter</text>
    <text class="rate meter" x="932" y="117">nearest 1 cm</text>

    <!-- person-height: 001 -->
    <rect x="575" y="140" width="475" height="44" rx="10"/>
    <text class="name" x="691" y="168" style="font-size:18px">centimeter</text>
    <text class="rate meter" x="932" y="167">integer / 2 sig. digits</text>

    <!-- road: US -->
    <rect x="575" y="206" width="152" height="60" rx="10"/>
    <text class="rate kilogram" x="651" y="226">≥ 0.5 mi</text>
    <text class="name" x="651" y="246" style="font-size:18px">mile</text>
    <text class="rate" x="651" y="261" style="fill:#64748b;font-size:12px">integer / 2 sig.</text>

    <rect x="735" y="206" width="152" height="60" rx="10"/>
    <text class="rate kilogram" x="811" y="226">≥ 100 ft</text>
    <text class="name" x="811" y="246" style="font-size:18px">foot</text>
    <text class="rate" x="811" y="261" style="fill:#64748b;font-size:12px">round to 50</text>

    <rect x="895" y="206" width="155" height="60" rx="10"/>
    <text class="rate kilogram" x="972" y="226">≥ 10 ft · &lt; 10 ft</text>
    <text class="name" x="972" y="246" style="font-size:18px">foot</text>
    <text class="rate" x="972" y="261" style="fill:#64748b;font-size:12px">round to 10 · 1</text>

    <!-- road: GB -->
    <rect x="575" y="278" width="152" height="60" rx="10"/>
    <text class="rate kilogram" x="651" y="298">≥ 0.5 mi</text>
    <text class="name" x="651" y="318" style="font-size:18px">mile</text>
    <text class="rate" x="651" y="333" style="fill:#64748b;font-size:12px">integer / 2 sig.</text>

    <rect x="735" y="278" width="152" height="60" rx="10"/>
    <text class="rate kilogram" x="811" y="298">≥ 100 yd</text>
    <text class="name" x="811" y="318" style="font-size:18px">yard</text>
    <text class="rate" x="811" y="333" style="fill:#64748b;font-size:12px">round to 50</text>

    <rect x="895" y="278" width="155" height="60" rx="10"/>
    <text class="rate kilogram" x="972" y="298">≥ 10 yd · &lt; 10 yd</text>
    <text class="name" x="972" y="318" style="font-size:18px">yard</text>
    <text class="rate" x="972" y="333" style="fill:#64748b;font-size:12px">round to 10 · 1</text>

    <!-- road: 001 -->
    <rect x="575" y="350" width="152" height="60" rx="10"/>
    <text class="rate kilogram" x="651" y="370">≥ 0.9 km</text>
    <text class="name" x="651" y="390" style="font-size:18px">kilometer</text>
    <text class="rate" x="651" y="405" style="fill:#64748b;font-size:12px">integer / 2 sig.</text>

    <rect x="735" y="350" width="152" height="60" rx="10"/>
    <text class="rate kilogram" x="811" y="370">≥ 300 m</text>
    <text class="name" x="811" y="390" style="font-size:18px">meter</text>
    <text class="rate" x="811" y="405" style="fill:#64748b;font-size:12px">round to 50</text>

    <rect x="895" y="350" width="155" height="60" rx="10"/>
    <text class="rate kilogram" x="972" y="370">≥ 10 m · &lt; 10 m</text>
    <text class="name" x="972" y="390" style="font-size:18px">meter</text>
    <text class="rate" x="972" y="405" style="fill:#64748b;font-size:12px">round to 10 · 1</text>
  </g>
</svg>
```

::: notes
[6:25–7:00] "Just trust me: if you don't want to read raw XML, here is what the UTS #35 spec
and the CLDR data actually say."
From left to right, the four inputs from slide 6:
1. Category (length, from meter)
2. Usage (person-height vs road)
3. Region (US, GB, FR/EG, or 001 world default)
4. Value threshold (geq) → gives the output unit and how to round it (precision).
In the US, road distances under 100 ft round to the nearest 10 ft (50 feet), and under 10 ft to 1 ft (7 feet).
In the UK, it's the same thresholds in yards (30 yards, 2 yards), and in 001 in meters (300 Meter, 20 Meter, 7 Meter).
:::

# CLDR picked the unit. Now convert!

We have **1.8 meters**. CLDR says: **foot-and-inch**.

::: {.fragment data-fragment-index="0"}
1.8 m = **? ft** + **? in**
:::

```{=html}
<svg class="unit-tree pairs" viewBox="0 0 960 350" role="img" aria-label="Eight length units in a ring. Arrows show conversions we may need: meter to foot, foot to inch, mile to kilometer, inch to centimeter. Then every pair of units is connected: 8 units make 28 pairs.">
  <defs>
    <marker id="pairs-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#4f46e5"/></marker>
  </defs>
  <!-- Every pair of units (shown last, drawn under the units) -->
  <g class="fragment" data-fragment-index="6">
    <path class="pairs-mesh" d="M225 50L342 85M225 50L390 170M225 50L342 255M225 50L225 290M225 50L108 255M225 50L60 170M225 50L108 85M342 85L390 170M342 85L342 255M342 85L225 290M342 85L108 255M342 85L60 170M342 85L108 85M390 170L342 255M390 170L225 290M390 170L108 255M390 170L60 170M390 170L108 85M342 255L225 290M342 255L108 255M342 255L60 170M342 255L108 85M225 290L108 255M225 290L60 170M225 290L108 85M108 255L60 170M108 255L108 85M60 170L108 85"/>
  </g>
  <!-- The units -->
  <g class="fragment tree-leaf" data-fragment-index="1">
    <text class="tree-label" x="470" y="40">WE MAY NEED TO CONVERT</text>
    <rect x="169" y="32" width="112" height="36" rx="18"/><text class="name" x="225" y="56">meter</text>
    <rect x="286" y="67" width="112" height="36" rx="18"/><text class="name" x="342" y="91">kilometer</text>
    <rect x="334" y="152" width="112" height="36" rx="18"/><text class="name" x="390" y="176">millimeter</text>
    <rect x="286" y="237" width="112" height="36" rx="18"/><text class="name" x="342" y="261">foot</text>
    <rect x="169" y="272" width="112" height="36" rx="18"/><text class="name" x="225" y="296">yard</text>
    <rect x="52" y="237" width="112" height="36" rx="18"/><text class="name" x="108" y="261">centimeter</text>
    <rect x="4" y="152" width="112" height="36" rx="18"/><text class="name" x="60" y="176">mile</text>
    <rect x="52" y="67" width="112" height="36" rx="18"/><text class="name" x="108" y="91">inch</text>
  </g>
  <!-- Conversions we may need, one at a time -->
  <g class="fragment" data-fragment-index="1">
    <line class="pairs-example" x1="238" y1="74" x2="327" y2="229"/>
    <text class="pairs-row" x="470" y="84">📏 meter → foot</text>
  </g>
  <g class="fragment" data-fragment-index="2">
    <line class="pairs-example" x1="300" y1="234" x2="158" y2="108"/>
    <text class="pairs-row" x="470" y="122">📏 foot → inch</text>
  </g>
  <g class="fragment" data-fragment-index="3">
    <line class="pairs-example" x1="121" y1="152" x2="281" y2="104"/>
    <text class="pairs-row" x="470" y="160">📏 mile → kilometer</text>
  </g>
  <g class="fragment" data-fragment-index="4">
    <line class="pairs-example" x1="108" y1="109" x2="108" y2="228"/>
    <text class="pairs-row" x="470" y="198">📏 inch → centimeter</text>
  </g>
  <g class="fragment" data-fragment-index="5">
    <text class="pairs-row" x="470" y="236">⛽ liter → gallon · 🌡️ °C → °F · …</text>
  </g>
  <g class="fragment" data-fragment-index="6">
    <text class="pairs-count" x="470" y="284">8 length units → 28 pairs</text>
  </g>
  <g class="fragment" data-fragment-index="7">
    <text class="pairs-total" x="470" y="324">Hundreds of units → thousands of pairs</text>
  </g>
</svg>
```

::: {.fragment data-fragment-index="8"}
🆘 **Help! We need CLDR to give us conversion data too**
:::

::: notes
[7:00–7:30] Ask: how many feet is 1.8 meters? Most people need a calculator, and a table.
Click through quickly: each arrow is one conversion someone needs (meter → foot, then foot → inch
for Sam's height; then other pairs and other quantities).
Then every pair: 8 length units already make 28 pairs, each with its own rate.
A table with every pair of units does not scale. Help! Bridge: CLDR has a trick.
:::

# Conversion data in CLDR

One row per unit: every unit converts to **one base unit**

```{.xml data-line-numbers="1-6|3-6|1,3-5|6" data-fragment-index="0"}
<unitConstant constant="ft_to_m" value="0.3048"/>

<convertUnit source='foot' baseUnit='meter' factor='ft_to_m'/>
<convertUnit source='inch' baseUnit='meter' factor='ft_to_m/12'/>
<convertUnit source='mile' baseUnit='meter' factor='ft_to_m*5280'/>
<convertUnit source='fahrenheit' baseUnit='kelvin' factor='5/9' offset='2298.35/9'/>
```

:::: steps
::: {.fragment data-fragment-index="0"}
- **baseUnit**: lengths → `meter`, temperatures → `kelvin`
:::

::: {.fragment data-fragment-index="1"}
- **factor**: multiply by it (exact: `ft_to_m` = 0.3048)
:::

::: {.fragment data-fragment-index="2"}
- **offset**: add it too (temperature)
:::
::::

::: notes
[7:30–8:00] One row per unit instead of one per pair. Click once per bullet:
1. baseUnit: foot, inch, and mile all point to meter; fahrenheit points to kelvin.
2. factor: constants like ft_to_m are exact, so the factors are exact fractions.
3. offset: fahrenheit needs an offset as well as a factor.
Source: CLDR common/supplemental/units.xml (the systems attribute is omitted on the slide).
:::

# Every unit hangs from a base unit

```{=html}
<svg class="unit-tree" viewBox="0 0 1060 375" role="img" aria-label="Three separate base-unit trees. Arrows point from foot, inch, and mile to meter; from gram and pound to kilogram; and from celsius, fahrenheit, and rankine to kelvin. Each arrow shows its conversion rate.">
  <defs>
    <linearGradient id="tree-meter" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4f46e5"/><stop offset="1" stop-color="#7c3aed"/></linearGradient>
    <linearGradient id="tree-kilogram" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#059669"/><stop offset="1" stop-color="#0d9488"/></linearGradient>
    <linearGradient id="tree-kelvin" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ea580c"/><stop offset="1" stop-color="#e11d48"/></linearGradient>
    <marker id="to-base" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#94a3b8"/></marker>
  </defs>
  <text class="tree-label" x="12" y="22">BASE UNITS</text>
  <text class="tree-quantity" x="190" y="22">length</text><text class="tree-quantity" x="520" y="22">mass</text><text class="tree-quantity" x="870" y="22">temperature</text>
  <!-- Every unit points to its base unit -->
  <g stroke="#94a3b8" stroke-width="3" marker-end="url(#to-base)">
    <line x1="60" y1="256" x2="148" y2="95"/><line x1="190" y1="256" x2="190" y2="95"/><line x1="320" y1="256" x2="232" y2="95"/>
    <line x1="455" y1="256" x2="500" y2="95"/><line x1="600" y1="256" x2="542" y2="95"/>
    <line x1="740" y1="256" x2="822" y2="95"/><line x1="870" y1="256" x2="870" y2="95"/><line x1="1000" y1="256" x2="918" y2="95"/>
  </g>
  <g class="tree-base">
    <rect x="100" y="32" width="180" height="56" rx="28" fill="url(#tree-meter)"/><text x="190" y="68">meter</text>
    <rect x="430" y="32" width="180" height="56" rx="28" fill="url(#tree-kilogram)"/><text x="520" y="68">kilogram</text>
    <rect x="780" y="32" width="180" height="56" rx="28" fill="url(#tree-kelvin)"/><text x="870" y="68">kelvin</text>
  </g>
  <g class="tree-leaf">
    <rect x="8" y="258" width="104" height="48" rx="14"/><text class="name" x="60" y="289">foot</text>
    <rect x="138" y="258" width="104" height="48" rx="14"/><text class="name" x="190" y="289">inch</text>
    <rect x="268" y="258" width="104" height="48" rx="14"/><text class="name" x="320" y="289">mile</text>
    <rect x="403" y="258" width="104" height="48" rx="14"/><text class="name" x="455" y="289">gram</text>
    <rect x="548" y="258" width="104" height="48" rx="14"/><text class="name" x="600" y="289">pound</text>
    <rect x="685" y="258" width="110" height="48" rx="14"/><text class="name" x="740" y="289">celsius</text>
    <rect x="805" y="258" width="130" height="48" rx="14"/><text class="name" x="870" y="289">fahrenheit</text>
    <rect x="945" y="258" width="110" height="48" rx="14"/><text class="name" x="1000" y="289">rankine</text>
  </g>
  <!-- Highlighted arrows (under the rate tags, so the rates stay readable) -->
  <g class="fragment" data-fragment-index="1" stroke="#db2777" stroke-width="5" stroke-linecap="round">
    <line x1="60" y1="256" x2="148" y2="92"/>
  </g>
  <g class="fragment" data-fragment-index="2" stroke="#f59e0b" stroke-width="5" stroke-linecap="round">
    <line x1="740" y1="256" x2="822" y2="92"/><line x1="870" y1="256" x2="870" y2="92"/>
  </g>
  <!-- The conversion rate on each arrow -->
  <g class="rate-tag">
    <rect x="55" y="178" width="80" height="26" rx="8"/><text class="rate meter" x="95" y="196">× 0.3048</text>
    <rect x="150" y="143" width="80" height="26" rx="8"/><text class="rate meter" x="190" y="161">× 0.0254</text>
    <rect x="236" y="178" width="98" height="26" rx="8"/><text class="rate meter" x="285" y="196">× 1609.344</text>
    <rect x="438" y="178" width="72" height="26" rx="8"/><text class="rate kilogram" x="474" y="196">× 0.001</text>
    <rect x="519" y="178" width="116" height="26" rx="8"/><text class="rate kilogram" x="577" y="196">× 0.45359237</text>
    <rect x="733" y="178" width="80" height="26" rx="8"/><text class="rate kelvin" x="773" y="196">+ 273.15</text>
    <rect x="817" y="124" width="106" height="48" rx="8"/><text class="rate kelvin" x="870" y="144">× 5/9</text><text class="rate kelvin" x="870" y="164">+ 2298.35/9</text>
    <rect x="940" y="178" width="54" height="26" rx="8"/><text class="rate kelvin" x="967" y="196">× 5/9</text>
  </g>
  <g class="fragment" data-fragment-index="1" fill="none" stroke="#db2777" stroke-width="5">
    <rect x="96" y="28" width="188" height="64" rx="32"/><rect x="4" y="254" width="112" height="56" rx="17"/>
  </g>
  <g class="fragment" data-fragment-index="2" fill="none" stroke="#f59e0b" stroke-width="5">
    <rect x="776" y="28" width="188" height="64" rx="32"/><rect x="681" y="254" width="118" height="56" rx="17"/><rect x="801" y="254" width="138" height="56" rx="17"/>
  </g>
  <g class="fragment" data-fragment-index="3">
    <path d="M60 306 V345 H600 V306" fill="none" stroke="#ef4444" stroke-width="4" stroke-dasharray="10 8"/>
    <circle cx="330" cy="345" r="20" fill="#ef4444"/><text class="tree-cross" x="330" y="353">✗</text>
  </g>
</svg>
```

:::: tree-steps
::: {.fragment data-fragment-index="1"}
📏 **meter → foot:** 1.8 m is already in meters → ÷ 0.3048 → **5.9055 ft**
:::

::: {.fragment data-fragment-index="2"}
🌡️ **celsius → fahrenheit:** up to kelvin, then down, with factors *and* offsets: 30°C = **86°F**
:::

::: {.fragment data-fragment-index="3"}
🚫 **foot → pound:** different trees, so no conversion
:::
::::

::: notes
[8:00–8:35] Each quantity has its own separate tree rooted at a base unit; every other unit hangs from its base unit.
Each arrow points to the base unit and carries its rate: follow the arrow up (× the rate),
or go against it, down to another unit (÷ the rate). To convert, go up to the base unit, then down to the target unit.
Click 1: meter → foot (our 1.8 m). Click 2: celsius → kelvin → fahrenheit, the opening poll again.
Click 3: foot and pound hang from different base units, so ICU rejects the conversion.
Each quantity names its base unit in CLDR, for example <unitQuantity baseUnit='kelvin' quantity='temperature'/>:
the root for temperature is kelvin, not celsius. Celsius is only an offset (+273.15); rankine is only a factor (5/9);
fahrenheit needs both.
The values are from CLDR units.xml (inch = ft_to_m/12, mile = ft_to_m×5280, pound = lb_to_kg).
Prefixed units such as centimeter and kilometer come from SI prefixes, not their own rows.
:::

# Compound units: each part climbs its own tree

```{=html}
<svg class="unit-tree" viewBox="0 0 1060 330" role="img" aria-label="foot-pound splits into foot and pound. Arrows point from foot to meter (times 0.3048) and from pound to kilogram (times 0.45359237); meter and kilogram join into meter-kilogram. Multiplying the two rates gives the rate of the compound unit.">
  <defs>
    <linearGradient id="tree2-meter" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4f46e5"/><stop offset="1" stop-color="#7c3aed"/></linearGradient>
    <linearGradient id="tree2-kilogram" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#059669"/><stop offset="1" stop-color="#0d9488"/></linearGradient>
    <linearGradient id="tree2-compound" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4f46e5"/><stop offset="1" stop-color="#059669"/></linearGradient>
    <marker id="tree2-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#94a3b8"/></marker>
  </defs>
  <text class="tree-label" x="20" y="22">COMPOUND UNIT</text>
  <text class="tree-label" x="616" y="22">BASE UNITS</text>
  <!-- foot-pound splits into its parts; the base units join again -->
  <g stroke="#cbd5e1" stroke-width="2.5" fill="none">
    <path d="M230 150 L290 72"/><path d="M230 150 L290 228"/>
    <path d="M780 72 L840 150"/><path d="M780 228 L840 150"/>
  </g>
  <!-- Each part points to its base unit -->
  <g stroke="#94a3b8" stroke-width="3" marker-end="url(#tree2-arrow)">
    <line x1="412" y1="72" x2="612" y2="72"/><line x1="412" y1="228" x2="612" y2="228"/>
  </g>
  <g class="rate-tag">
    <rect x="471" y="59" width="80" height="26" rx="8"/><text class="rate meter" x="511" y="77">× 0.3048</text>
    <rect x="453" y="215" width="116" height="26" rx="8"/><text class="rate kilogram" x="511" y="233">× 0.45359237</text>
  </g>
  <g class="tree-compound">
    <rect x="20" y="122" width="210" height="56" rx="28" fill="#7c3aed"/><text x="125" y="157">foot-pound</text>
    <rect x="840" y="122" width="210" height="56" rx="28" fill="url(#tree2-compound)"/><text x="945" y="157">meter-kilogram</text>
  </g>
  <g class="tree-leaf">
    <rect x="290" y="48" width="120" height="48" rx="14"/><text class="name" x="350" y="79">foot</text>
    <rect x="290" y="204" width="120" height="48" rx="14"/><text class="name" x="350" y="235">pound</text>
  </g>
  <g class="tree-base">
    <rect x="620" y="44" width="160" height="56" rx="28" fill="url(#tree2-meter)"/><text x="700" y="80">meter</text>
    <rect x="620" y="200" width="160" height="56" rx="28" fill="url(#tree2-kilogram)"/><text x="700" y="236">kilogram</text>
  </g>
  <!-- The rate of the compound unit: just multiply the rates on the arrows -->
  <g class="fragment">
    <text class="tree-sum" x="530" y="292">⚡ 1 foot-pound = 0.3048 × 0.45359237 = <tspan class="result">0.138255 meter-kilogram</tspan></text>
    <text class="tree-sum" x="530" y="322">and back: 1 meter-kilogram = 1 ÷ 0.138255 = <tspan class="result">7.233 foot-pound</tspan></text>
  </g>
</svg>
```

:::: tree-steps
::: fragment
🚗 **kilometer-per-hour → mile-per-hour:** “per” divides, so the hours cancel: 100 km/h = **62.137 mph**
:::

::: fragment
🚫 **meter-per-second → foot-pound:** the parts hang from different base units, so no conversion
:::
::::

::: notes
[8:35–9:05] ICU parses the unit identifier into parts, and each part follows its arrow to its base unit.
The rate of the compound unit is just the product of the rates on the arrows (divided for "per" parts):
foot-pound → meter-kilogram: 0.3048 × 0.45359237 = 0.138255; and back, 1 ÷ 0.138255 = 7.233.
ICU normalizes the identifiers (kilogram-meter → pound-foot), so formatting gives "7.233 pound-feet".
kilometer-per-hour → mile-per-hour: (1000 ÷ 3600) ÷ (1609.344 ÷ 3600) → 100 km/h = 62.137 mph.
meter-per-second → foot-pound: ICU throws "input units must be convertible or reciprocal".
Every value is a test case in demos/java/UnitsTest.java (internal UnitsConverter); make test runs it.
:::

# ICU {.divider data-background-gradient="linear-gradient(135deg, #0369a1 0%, #4f46e5 100%)"}

## Convert, cascade, round, and route

::: notes
[9:05] Checkpoint. It looks easy… until you implement it.
:::

# What ICU does for 1.8 meters in en-US

1. **Single convert:** meter → foot
2. **Cascading convert:** meter → foot → inch (mixed units)
3. **Round through the cascade:** round, then carry back up
4. **Route:** pick the best unit combination for *this* value

::: notes
[9:05–9:15] Each step looks trivial. Each one hides an edge case.
In ICU: UnitsConverter does one conversion; ComplexUnitsConverter chains them for mixed units
(and rounds the last unit, then carries back up the chain); UnitsRouter picks the unit per value.
:::

# Step 1: Single convert

ICU turns the CLDR data into a converter for each pair of units, with exact rational arithmetic:

::: incremental
- 📏 **A factor:** 1.8 m ÷ 0.3048 = **5.9055 ft**
- 🌡️ **A factor *and* an offset:** 30°C × 9/5 + 32 = **86°F**
- ⛽ **A reciprocal:** less fuel per distance = more distance per fuel:
  6.5 L/100 km → **36 miles per gallon** (US) · **43 miles per gallon** (UK)
:::

::: notes
[9:15–9:50] Three kinds of conversion, one per click.
1. Most units: just a factor (meter → foot).
2. Temperature: a factor and an offset (the opening poll: 30°C = 86°F).
3. Fuel consumption: liters per 100 km goes down when the car is better; miles per gallon goes up.
That is a reciprocal, not just a factor. The UK number is higher because the imperial gallon is bigger.
All values are real ICU output (the fuel example uses usage "vehicle-fuel").
:::

# Step 2: Cascading convert

1.8 m = 5.9055 ft → **5 ft** + 0.9055 ft = **10.8661 in**

Mixed units depend on the region:

| Locale | Output | Unit |
|---|---|---|
| en-US | 5 feet, 11 inches | foot-and-inch |
| fr-FR | 1 mètre et 80 centimètres | meter-and-centimeter |
| ar-EG | متر و٨٠ سنتيمتر | meter-and-centimeter |

::: notes
[9:50–10:20] 10.8661 inches rounds to 11 inches (Step 3 shows what happens when rounding overflows).
French puts a no-break space (U+00A0) between the number and the unit.
Arabic drops the numeral for "one": متر alone means "one meter".
It also uses Arabic-Indic digits (٨٠).
:::

# Step 3: Round through the cascade

1.826 m = **5 ft, 11.89 in**

Round the inches → **12 in**… but 12 inches is **1 foot**!

| | |
|---|---|
| ❌ | 5 feet, 12 inches |
| ✅ | 6 feet, 0 inches |

ICU rounds the smallest unit, then carries the overflow back up the cascade (inches → feet).

::: notes
[10:20–11:30] ICU rounds the smallest unit, then carries the overflow back up the cascade.
Without a CLDR skeleton, the default rounding of the smallest unit is about to change (ICU-23558):
we will see it in Tutorial 1 with 1.7 m. Callers can always set their own `.precision(...)`.
:::

# Step 4: Route each value to the best unit

`en-US`, usage `road`:

```{=html}
<table class="route-table">
  <thead><tr><th>Value</th><th>Output</th><th>Why</th></tr></thead>
  <tbody>
    <tr class="fragment"><td>150 m</td><td><strong>500 feet</strong></td><td>at least 100 ft → feet, round to 50</td></tr>
    <tr class="fragment"><td>900 m</td><td><strong>0.56 miles</strong></td><td>at least 0.5 mi → miles</td></tr>
    <tr class="fragment"><td>120 km</td><td><strong>75 miles</strong></td><td>at least 0.5 mi → miles</td></tr>
  </tbody>
</table>
```

::: fragment
Same values in `en-GB`: 150 yards · 0.56 miles · 75 miles
:::

::: notes
[11:30–12:30] One row per click. Real ICU output. The router uses the converter to check each CLDR preference
row in order and picks the first one whose threshold the value meets.
Last click: the UK uses yards for short road distances.
:::

# Tutorial 1 {.divider data-background-gradient="linear-gradient(135deg, #ea580c 0%, #e11d48 100%)"}

## Person height and road distance (ICU4J and ICU4C)

::: notes
[12:30] Checkpoint.
:::

# ICU4J

::: {.code-window data-label="UnitsTest.java · ICU4J"}
```{.java data-line-numbers="1-5|2|3|4|5|7-8|9" data-fragment-index="0"}
LocalizedNumberFormatter formatter = NumberFormatter.with()
        .unit(MeasureUnit.forIdentifier("meter"))
        .unitWidth(UnitWidth.FULL_NAME)
        .locale(ULocale.forLanguageTag("en-US"))
        .usage("person-height");

FormattedNumber result = formatter.format(1.8);
String text = result.toString();
MeasureUnit unit = result.getOutputUnit();
```
:::

::: {.key-callout .fragment data-fragment-index="3"}
🔑 **`.usage()` is the key:** it lets ICU pick the unit for the locale's region
:::

:::: code-output
::: {.fragment data-fragment-index="4"}
[text]{.out-label} [5 feet, 11 inches ✅]{.out-value}
:::

::: {.fragment data-fragment-index="5"}
[unit]{.out-label} [foot-and-inch]{.out-value}
:::
::::

::: notes
[12:30–13:45] Click through the highlighted lines:
1–5: one formatter, built once and reused.
2: the input unit, what we measured.
3: the width (full unit names here).
4: the locale; its region decides the units.
5: the usage, the key. Without it, nothing is converted (next slide).
7–8: format 1.8 m → "5 feet, 11 inches", Sam's answer from slide 3.
9: the unit ICU chose for this value: foot-and-inch.
Test: demos/java/UnitsTest.java
:::

# Without `.usage()`

::: {.code-window data-label="UnitsTest.java · ICU4J"}
```{.java data-line-numbers="1-8|5|7-8" data-fragment-index="0"}
LocalizedNumberFormatter formatter = NumberFormatter.with()
        .unit(MeasureUnit.forIdentifier("meter"))
        .unitWidth(UnitWidth.FULL_NAME)
        .locale(ULocale.forLanguageTag("en-US"));
        // no .usage()

FormattedNumber result = formatter.format(1.8);
String text = result.toString();
```
:::

:::: code-output
::: {.fragment data-fragment-index="1"}
[text]{.out-label} [1.8 meters 🤨]{.out-value .out-bad}
:::

::: {.fragment data-fragment-index="2"}
[with .usage()]{.out-label} [5 feet, 11 inches ✅]{.out-value}
:::
::::

::: {.fragment data-fragment-index="2"}
Same locale, same value: without the usage, ICU formats the unit you gave it, with no conversion.
:::

::: notes
[13:45–14:15] Click 1: the usage line is gone. Click 2: "1.8 meters", even for en-US.
Click 3: compare with the previous slide. The locale alone never converts units:
you have to tell ICU what the value is for.
If asked: in ICU4J, getOutputUnit() returns null when no usage is set.
:::

# ICU4C

::: {.code-window data-label="units_test.cpp · ICU4C"}
```{.cpp data-line-numbers="1-6|8-9|10-11" data-fragment-index="0"}
UErrorCode status = U_ZERO_ERROR;
LocalizedNumberFormatter formatter = NumberFormatter::with()
        .unit(MeasureUnit::forIdentifier("meter", status))
        .unitWidth(UNUM_UNIT_WIDTH_FULL_NAME)
        .locale(Locale::forLanguageTag("en-US", status))
        .usage("person-height");

FormattedNumber result = formatter.formatDouble(1.8, status);
UnicodeString text = result.toString(status);
MeasureUnit unit = result.getOutputUnit(status);
const char* id = unit.getIdentifier();
```
:::

:::: code-output
::: {.fragment data-fragment-index="0"}
[text]{.out-label} [5 feet, 11 inches ✅]{.out-value}
:::

::: {.fragment data-fragment-index="1"}
[id]{.out-label} [foot-and-inch]{.out-value}
:::
::::

::: notes
[14:15–15:00] Click: the formatter (same inputs as Java, plus UErrorCode), then format, then the output unit.
Test: demos/cpp/units_test.cpp
Skip if behind: say the C++ API mirrors the Java one and move on.
Keep the MeasureUnit in a variable: getIdentifier() points into the object.
:::

# 1.7 meters: set your own precision

::: {.code-window data-label="UnitsTest.java · ICU4J"}
```{.java data-line-numbers="1-10|2|4-6|8-10" data-fragment-index="0"}
// formatter: the same as before, with .usage("person-height")
String byDefault = formatter.format(1.7).toString();

String integer = formatter
        .precision(Precision.integer())
        .format(1.7).toString();

String twoDecimals = formatter
        .precision(Precision.maxFraction(2))
        .format(1.7).toString();
```
:::

:::: code-output
::: {.fragment data-fragment-index="0"}
[byDefault]{.out-label} [5 feet, 6.9 inches 😕]{.out-value .out-bad}
:::

::: {.fragment data-fragment-index="1"}
[integer]{.out-label} [5 feet, 7 inches ✅]{.out-value}
:::

::: {.fragment data-fragment-index="2"}
[twoDecimals]{.out-label} [5 feet, 6.93 inches]{.out-value}
:::
::::

::: {.key-callout .fragment data-fragment-index="3"}
🔧 **A small fix is coming soon:** by default, the last unit will be rounded to an integer (ICU-23558)
:::

::: notes
[15:00–16:00] Why did we use 1.8 m? Because with 1.7 m, today's default gives "5 feet, 6.9 inches".
Click 1: the default today. Click 2: your own precision, Precision.integer() → "5 feet, 7 inches".
Click 3: or any other precision you want (two decimals).
Click 4: the fix is coming (ICU-23558; UTS #35 says to round the smallest unit of mixed units).
Until then, set the precision yourself. It always wins over the default.
:::

# Person height: 1.8 meters

| Locale | Output |
|---|---|
| en-US | 5 feet, 11 inches |
| en-GB | 5 feet, 11 inches |
| de-DE | 180 Zentimeter |
| fr-FR | 1 mètre et 80 centimètres |
| ja-JP | 180 センチメートル |
| ar-EG | متر و٨٠ سنتيمتر |
| en-US-u-ms-metric | 180 centimeters |

::: notes
[15:00–16:45] All outputs are real ICU 79 (main) results, identical in ICU4J and ICU4C.
:::

# Road distance: same code, different values

| | 150 m | 900 m | 5 km | 120 km |
|---|---|---|---|---|
| en-US | 500 feet | 0.56 miles | 3.1 miles | 75 miles |
| en-GB | 150 yards | 0.56 miles | 3.1 miles | 75 miles |
| de-DE | 150 Meter | 0,9 Kilometer | 5 Kilometer | 120 Kilometer |

Bonus, 30°C with usage `weather`:
`en-US` → 86 degrees Fahrenheit · `en-US-u-mu-celsius` → 30 degrees Celsius

::: notes
[16:45–18:30] Callback to the opening: 30°C, the beach day, is "86 degrees Fahrenheit" for a US user.
The -u-mu- keyword lets a user override the temperature unit.
Skip if behind: the weather bonus.
:::

# Grammar {.divider data-background-gradient="linear-gradient(135deg, #047857 0%, #0d9488 100%)"}

## Grammatical gender and case in `MessageFormat` sentences

::: notes
[18:30] Checkpoint. In real apps, units don't appear in isolation: they sit inside sentences
formatted with MessageFormat, where the sentence needs the unit's gender and case.
:::

# Grammatical gender changes the message

A French app offers a free trial: `{duration} offert` ("… free")

::: incremental
- 📅 `month` → **1 mois offert** ✅ · *mois* is masculine
- 📅 `week` → ~~1 semaine offert~~ ❌ → **1 semaine offerte** ✅ · *semaine* is feminine
:::

. . .

**➜ The adjective agrees with the unit, so we need the unit's grammatical gender:** `getNounClass()`

::: notes
[18:30–19:30] A free-trial banner: "1 mois offert" (1 month free) is fine, but the same message
with a week gives "1 semaine offert", which is wrong: semaine is feminine, so the adjective
becomes "offerte". The message has to know the gender of the unit, and only ICU knows it
(the unit can come from data or from the router).
:::

# Tutorial 2: grammatical gender

::: {.code-window data-label="UnitsTest.java · ICU4J"}
```{.java data-line-numbers="1-12|6|7|9-11|12" data-fragment-index="0"}
LocalizedNumberFormatter formatter = NumberFormatter.with()
        .unit(MeasureUnit.forIdentifier("week"))
        .unitWidth(UnitWidth.FULL_NAME)
        .locale(ULocale.FRENCH);

FormattedNumber duration = formatter.format(1);
String gender = duration.getNounClass().getIdentifier();

MessageFormat trial = new MessageFormat(
        "{gender, select, feminine {{duration} offerte} other {{duration} offert}}",
        ULocale.FRENCH);
String text = trial.format(Map.of("gender", gender, "duration", duration.toString()));
```
:::

:::: code-output
::: {.fragment data-fragment-index="0"}
[duration]{.out-label} [1 semaine]{.out-value}
:::

::: {.fragment data-fragment-index="1"}
[gender]{.out-label} [feminine]{.out-value}
:::

::: {.fragment data-fragment-index="3"}
[text]{.out-label} [1 semaine offerte ✅]{.out-value}
:::

::: {.fragment data-fragment-index="4"}
[with month]{.out-label} [1 mois offert ✅]{.out-value}
:::
::::

::: notes
[19:30–21:30] Click through:
6: format the duration with ICU ("1 semaine").
7: ask the formatted number for its noun class: feminine.
9–11: the message selects on the gender (select, not plural).
12: "1 semaine offerte". Last click: the same code with a month gives "1 mois offert".
ICU4C: FormattedNumber::getNounClass(status) returns UDisplayOptionsNounClass.
Real messages also need plural selection; kept to 1 here.
:::

# The gender is only known at runtime

`ru-US`, usage `road`:

| Value | Output | Unit | Noun class |
|---|---|---|---|
| 100 m | 350 футов | foot | masculine |
| 10 km | 6,2 мили | mile | feminine |

The router picks the unit, so the `MessageFormat` sentence has to follow it.

::: notes
[21:30–22:00] Skip if behind. Real ICU4C output.
With usage, the router picks the unit per value, so the gender can change with the value.
Note: ICU4J currently returns UNDEFINED from getNounClass() whenever usage() is set
(found while preparing this talk). Decide before the talk: fix, or mention it.
:::

# Grammatical case changes the unit

In German, the sentence decides the **case**, and the unit changes with it:

::: incremental
- 🚗 Erlaubt sind **100 Kilometer pro Stunde**. · nominative
- 🚗 Er fährt mit **100 Kilometern pro Stunde**. · *mit* needs the **dative**
:::

. . .

**➜ The message knows the case; ICU inflects the unit:** `DisplayOptions` + `GrammaticalCase`

::: notes
[22:00–23:00] "100 km/h are allowed" vs "he drives at 100 km/h".
The preposition "mit" requires the dative, so "Kilometer" becomes "Kilometern".
Only the first part of the compound unit changes ("pro Stunde" stays).
Unlike gender, the case comes from the sentence, so the message passes it to ICU.
:::

# The same unit in different cases

| Case | German | Polish | Russian |
|---|---|---|---|
| nominative | 3 Meter | 3 metry | 3 метра |
| genitive | 3 Meter | 3 metrów | 3 метров |
| dative | 3 Metern | 3 metrom | 3 метрам |
| instrumental | — | 3 metrami | 3 метрами |
| locative / prepositional | — | 3 metrach | 3 метрах |

::: notes
[23:00–23:45] Skip if behind. Real ICU output. German has four cases, so instrumental and locative do not apply.
Polish and Russian have more cases, so the unit has more forms.
:::

# Tutorial 3: grammatical case

::: {.code-window data-label="UnitsTest.java · ICU4J"}
```{.java data-line-numbers="1-12|4-6|9|11-12" data-fragment-index="0"}
LocalizedNumberFormatter formatter = NumberFormatter.with()
        .unit(MeasureUnit.forIdentifier("kilometer-per-hour"))
        .unitWidth(UnitWidth.FULL_NAME)
        .displayOptions(DisplayOptions.builder()
                .setGrammaticalCase(GrammaticalCase.DATIVE)
                .build())
        .locale(ULocale.GERMAN);

String speed = formatter.format(100).toString();

MessageFormat drives = new MessageFormat("Er fährt mit {speed}.", ULocale.GERMAN);
String text = drives.format(Map.of("speed", speed));
```
:::

:::: code-output
::: {.fragment data-fragment-index="1"}
[speed]{.out-label} [100 Kilometern pro Stunde]{.out-value}
:::

::: {.fragment data-fragment-index="2"}
[text]{.out-label} [Er fährt mit 100 Kilometern pro Stunde. ✅]{.out-value}
:::

::: {.fragment data-fragment-index="3"}
[without the case]{.out-label} [Er fährt mit 100 Kilometer pro Stunde. ❌]{.out-value .out-bad}
:::
::::

::: notes
[23:45–26:30] Checkpoint. Click through:
4–6: ask for the dative, because the message says "mit {speed}".
9: "100 Kilometern pro Stunde".
11–12: the sentence: "Er fährt mit 100 Kilometern pro Stunde."
Last click: without displayOptions, ICU gives the nominative, and the sentence is wrong.
ICU4C: DisplayOptions::builder().setGrammaticalCase(UDISPOPT_GRAMMATICAL_CASE_DATIVE).build()
:::

# ICU4X {.divider data-background-gradient="linear-gradient(135deg, #e11d48 0%, #a21caf 100%)"}

## Progress and what’s coming

::: notes
[26:30] Checkpoint.
:::

# ICU4X today (experimental)

- `measure`: `MeasureUnit` and the unit identifier parser
- `units`: exact unit converter (`ConverterFactory`, rational arithmetic)
- `dimension`: unit, currency (including compact), and percent formatters
- `duration`: duration formatter

::: notes
[26:30–27:30] Confirm the current status of each item before the talk.
:::

# What’s coming

- **ECMAScript proposals (TC39 / ECMA-402):**
  - **`Amount`** (`proposal-amount`): bundles a numeric value with its `unit` and precision (so `30` never travels without `celsius`)
  - **Smart Unit Preferences** (`proposal-smart-unit-preferences`): brings CLDR `usage` (`person-height`, `road`) and mixed units to `Intl.NumberFormat`
- **ICU4X:**
  - Graduating currency formatting out of experimental
  - Unit and duration formatting for ECMA-402
  - Usage-based unit preferences, mixed units, and grammatical case & gender

::: notes
[27:30–29:30] Callback to slide 2: ECMAScript's Amount proposal keeps the number and unit together,
and Smart Unit Preferences brings CLDR usage-based routing and mixed units to JavaScript,
backed by ICU4X.
:::

# Takeaways

- Keep the unit with the value (like ECMAScript’s upcoming `Amount`)
- Pass the usage, and let CLDR choose the unit and the rounding (Smart Unit Preferences)
- Never glue a number and a unit string together: use `MessageFormat`
- Ask ICU for the grammatical case your sentence needs
- Check the noun class so the rest of the sentence agrees

::: notes
[29:30–30:30] Quick recap, one sentence per point.
:::

# Questions! {.cover data-background-gradient="linear-gradient(135deg, #312e81 0%, #6d28d9 55%, #db2777 100%)"}

- UTS #35, Part 6 (Supplemental): <https://www.unicode.org/reports/tr35/tr35-info.html>
- ICU number formatting: <https://unicode-org.github.io/icu/userguide/format_parse/numbers/>
- ICU4X: <https://github.com/unicode-org/icu4x>
- Demo code: (QR code)

::: notes
[30:30–40:00] Checkpoint. Questions; 40:00–45:00 is buffer.
:::
