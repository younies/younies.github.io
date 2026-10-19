// UTW 2026 tutorial: "Beyond Meters and Miles". ICU4J test cases.
//
// Each test is named after a slide and checks every output that slide shows:
//   assertOnSlide(expected, actual)  checks that ICU returns `expected` and that
//                                    `expected` is in slides.md;
//   assertEquals(expected, actual)   checks ICU only (for values not on a slide).
// The test also checks that each slide title is in slides.md.
//
// Run from the talk folder with a built ICU4J checkout (Java 11+):
//   java -cp <icu>/icu4j/main/core/target/classes demos/java/UnitsTest.java slides.md
// or simply: make test

import com.ibm.icu.impl.units.UnitsConverter;
import com.ibm.icu.number.FormattedNumber;
import com.ibm.icu.number.LocalizedNumberFormatter;
import com.ibm.icu.number.NumberFormatter;
import com.ibm.icu.number.NumberFormatter.UnitWidth;
import com.ibm.icu.number.Precision;
import com.ibm.icu.text.DisplayOptions;
import com.ibm.icu.text.DisplayOptions.GrammaticalCase;
import com.ibm.icu.text.MeasureFormat;
import com.ibm.icu.text.MeasureFormat.FormatWidth;
import com.ibm.icu.text.MessageFormat;
import com.ibm.icu.util.Measure;
import com.ibm.icu.util.MeasureUnit;
import com.ibm.icu.util.ULocale;
import java.math.BigDecimal;
import java.math.MathContext;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class UnitsTest {

    // Slide "Is 30 degrees hot or cold?"
    static void isThirtyDegreesHotOrCold() {
        assertOnSlide("30°C", format("celsius", 30, SHORT, Precision.integer()));
        assertOnSlide("86°F", format("fahrenheit", convert("celsius", "fahrenheit", 30),
                SHORT, Precision.integer()));
        assertOnSlide("30°F", format("fahrenheit", 30, SHORT, Precision.integer()));
        assertOnSlide("-1°C", format("celsius", convert("fahrenheit", "celsius", 30),
                SHORT, Precision.integer()));
    }

    // Slide "How tall are you?": Sam's answers to Alex.
    static void howTallAreYou() {
        assertOnSlide("1.8 meters", format("meter", 1.8, FULL, Precision.unlimited()));
        assertOnSlide("0.00111847 miles", format("mile", convert("meter", "mile", 1.8),
                FULL, Precision.maxSignificantDigits(6)));
        assertOnSlide("5 feet, 10.8661 inches", format("foot-and-inch",
                convert("meter", "foot", 1.8), FULL, Precision.maxFraction(4)));
        assertOnSlide("5 feet, 11 inches", personHeight("en-US").format(1.8));
    }

    // Slide "How tall is your child?" (0.7 m).
    static void howTallIsYourChild() {
        double feet = convert("meter", "foot", 0.7);
        assertOnSlide("2 feet, 4 inches", format("foot-and-inch", feet, FULL, Precision.integer()));
        assertOnSlide("28 inches", personHeight("en-US").format(0.7));
        // Speaker notes.
        assertOnSlide("27.56 in", format("inch", convert("meter", "inch", 0.7),
                SHORT, Precision.maxFraction(2)));
        assertOnSlide("2 ft, 3.56 in", format("foot-and-inch", feet, SHORT, Precision.maxFraction(2)));
        assertOnSlide("91 cm", format("centimeter", convert("foot", "centimeter", 3),
                SHORT, Precision.integer()));
    }

    // Slide "What the CLDR data says".
    static void whatTheCldrDataSays() {
        assertOnSlide("foot-and-inch", personHeight("en-US").format(1.8).getOutputUnit().getIdentifier());
        assertOnSlide("inch", personHeight("en-US").format(0.7).getOutputUnit().getIdentifier());
        assertOnSlide("meter-and-centimeter", personHeight("fr-FR").format(1.8).getOutputUnit().getIdentifier());
        assertOnSlide("centimeter", personHeight("de-DE").format(1.8).getOutputUnit().getIdentifier());
        // Road thresholds and precision increments in speaker notes.
        assertOnSlide("50 feet", formatWithUsage("en-US", "meter", "road", 15));
        assertOnSlide("7 feet", formatWithUsage("en-US", "meter", "road", 2));
        assertOnSlide("30 yards", formatWithUsage("en-GB", "meter", "road", 25));
        assertOnSlide("2 yards", formatWithUsage("en-GB", "meter", "road", 2));
        assertOnSlide("300 Meter", formatWithUsage("de-DE", "meter", "road", 320));
        assertOnSlide("20 Meter", formatWithUsage("de-DE", "meter", "road", 24));
        assertOnSlide("7 Meter", formatWithUsage("de-DE", "meter", "road", 7.4));
    }

    // Slide "Conversion data in CLDR": the exact constant ft_to_m.
    static void conversionDataInCldr() {
        assertOnSlide("0.3048", plain(convert("foot", "meter", 1)));
    }

    // Slide "Every unit hangs from a base unit": the rate on each arrow.
    static void everyUnitHangsFromABaseUnit() {
        assertOnSlide("0.3048", plain(convert("foot", "meter", 1)));
        assertOnSlide("0.0254", plain(convert("inch", "meter", 1)));
        assertOnSlide("1609.344", plain(convert("mile", "meter", 1)));
        assertOnSlide("0.001", plain(convert("gram", "kilogram", 1)));
        assertOnSlide("0.45359237", plain(convert("pound", "kilogram", 1)));
        assertOnSlide("273.15", plain(convert("celsius", "kelvin", 0)));
        assertOnSlide("5.9055 ft", format("foot", convert("meter", "foot", 1.8),
                SHORT, Precision.maxFraction(4)));
        assertOnSlide("86°F", format("fahrenheit", convert("celsius", "fahrenheit", 30),
                SHORT, Precision.integer()));
    }

    // Slide "Compound units: each part climbs its own tree".
    static void compoundUnits() {
        // The rate of the compound unit: the product of the rates on the arrows.
        assertOnSlide("0.138255", NumberFormatter.withLocale(ULocale.US)
                .precision(Precision.maxSignificantDigits(6))
                .format(convert("foot-pound", "meter-kilogram", 1)).toString());
        double footPounds = convert("meter-kilogram", "foot-pound", 1);
        assertOnSlide("7.233", NumberFormatter.withLocale(ULocale.US)
                .precision(Precision.maxFraction(3)).format(footPounds));
        assertOnSlide("62.137 mph", format("mile-per-hour",
                convert("kilometer-per-hour", "mile-per-hour", 100), SHORT, Precision.maxFraction(3)));
        // Speaker notes.
        assertOnSlide("kilogram-meter → pound-foot",
                MeasureUnit.forIdentifier("meter-kilogram").getIdentifier() + " → "
                        + MeasureUnit.forIdentifier("foot-pound").getIdentifier());
        assertOnSlide("7.233 pound-feet", format("foot-pound", footPounds, FULL,
                Precision.maxFraction(3)));
        String error = "converted";
        try {
            convert("meter-per-second", "foot-pound", 1);
        } catch (IllegalArgumentException e) {
            error = e.getMessage();
        }
        assertOnSlide("input units must be convertible or reciprocal", error);
    }

    // Slide "Follow 1.8 m through the CLDR data": the chips at the bottom.
    static void followPersonHeight() {
        assertOnSlide("1.8 m = 5.91 ft", "1.8 m = " + format("foot", convert("meter", "foot", 1.8),
                SHORT, Precision.maxFraction(2)));
        FormattedNumber result = personHeight("en-US").format(1.8);
        assertOnSlide("foot-and-inch, nearest 1 in: 5 feet, 11 inches",
                result.getOutputUnit().getIdentifier() + ", nearest 1 in: " + result);
    }

    // Slide "Follow 150 m through the CLDR data": the first row fails, the next one matches.
    static void followRoad() {
        assertOnSlide("150 m = 0.09 mi", "150 m = " + format("mile", convert("meter", "mile", 150),
                SHORT, Precision.maxFraction(2)));
        assertOnSlide("150 m = 492 ft", "150 m = " + format("foot", convert("meter", "foot", 150),
                SHORT, Precision.integer()));
        FormattedNumber result = formatWithUsage("en-US", "meter", "road", 150);
        assertOnSlide("foot, round to 50: 500 feet",
                result.getOutputUnit().getIdentifier() + ", round to 50: " + result);
    }

    // Slide "Step 1: Single convert": a factor, a factor and an offset, a reciprocal.
    static void stepOneConvert() {
        assertOnSlide("5.9055 ft", format("foot", convert("meter", "foot", 1.8),
                SHORT, Precision.maxFraction(4)));
        assertOnSlide("86°F", format("fahrenheit", convert("celsius", "fahrenheit", 30),
                SHORT, Precision.integer()));
        assertOnSlide("36 miles per gallon",
                formatWithUsage("en-US", "liter-per-100-kilometer", "vehicle-fuel", 6.5));
        assertOnSlide("43 miles per gallon",
                formatWithUsage("en-GB", "liter-per-100-kilometer", "vehicle-fuel", 6.5));
    }

    // Slide "Step 2: Cascading convert": two cascades, each with its formatted result.
    static void stepTwoMixedUnits() {
        double feet = convert("meter", "foot", 1.8);
        assertOnSlide("5.9055 ft", format("foot", feet, SHORT, Precision.maxFraction(4)));
        assertOnSlide("0.9055 ft", format("foot", feet - 5, SHORT, Precision.maxFraction(4)));
        assertOnSlide("10.8661 in", format("inch", convert("foot", "inch", feet - 5),
                SHORT, Precision.maxFraction(4)));
        assertOnSlide("× 12", "× " + plain(convert("foot", "inch", 1)));
        assertOnSlide("5 feet, 11 inches", personHeight("en-US").format(1.8));
        double meters = convert("foot", "meter", 6);
        assertOnSlide("1.8288 m", format("meter", meters, SHORT, Precision.maxFraction(4)));
        assertOnSlide("0.8288 m", format("meter", meters - 1, SHORT, Precision.maxFraction(4)));
        assertOnSlide("82.88 cm", format("centimeter", convert("meter", "centimeter", meters - 1),
                SHORT, Precision.maxFraction(2)));
        assertOnSlide("× 100", "× " + plain(convert("meter", "centimeter", 1)));
        assertOnSlide("1 mètre et 83 centimètres",
                formatWithUsage("fr-FR", "foot", "person-height", 6));
    }

    // Slide "Step 3: Round through the cascade" (1.826 m).
    static void stepThreeRounding() {
        double feet = convert("meter", "foot", 1.826);
        double inches = convert("foot", "inch", feet - 5);
        assertOnSlide("5 ft, 11.89 in", format("foot-and-inch", feet, SHORT, Precision.maxFraction(2)));
        assertOnSlide("12 in", format("inch", inches, SHORT, Precision.integer()));
        // The naive way: round the inches on their own, with no carry.
        assertOnSlide("5 feet, 12 inches", MeasureFormat.getInstance(ULocale.US, FormatWidth.WIDE)
                .formatMeasures(new Measure(5, MeasureUnit.FOOT),
                        new Measure(Math.round(inches), MeasureUnit.INCH)));
        assertOnSlide("6 feet, 0 inches", personHeight("en-US").format(1.826));
    }

    // Slide "Step 4: Route each value to the best unit".
    static void stepFourRoute() {
        assertOnSlide("500 feet", formatWithUsage("en-US", "meter", "road", 150));
        assertOnSlide("0.56 miles", formatWithUsage("en-US", "meter", "road", 900));
        assertOnSlide("75 miles", formatWithUsage("en-US", "meter", "road", 120000));
        assertOnSlide("150 yards", formatWithUsage("en-GB", "meter", "road", 150));
        assertOnSlide("0.56 miles", formatWithUsage("en-GB", "meter", "road", 900));
        assertOnSlide("75 miles", formatWithUsage("en-GB", "meter", "road", 120000));
    }

    // Slide "Step 4: the first match wins": each check and each result.
    static void routerStepByStep() {
        assertOnSlide("0.09 mi ✗", format("mile", convert("meter", "mile", 150),
                SHORT, Precision.maxFraction(2)) + " ✗");
        assertOnSlide("492 ft ✓", format("foot", convert("meter", "foot", 150),
                SHORT, Precision.integer()) + " ✓");
        assertOnSlide("0.56 mi ✓", format("mile", convert("meter", "mile", 900),
                SHORT, Precision.maxFraction(2)) + " ✓");
        assertOnSlide("74.56 mi ✓", format("mile", convert("meter", "mile", 120000),
                SHORT, Precision.maxFraction(2)) + " ✓");
        assertOnSlide("500 feet ✅", formatWithUsage("en-US", "meter", "road", 150) + " ✅");
        assertOnSlide("0.56 miles ✅", formatWithUsage("en-US", "meter", "road", 900) + " ✅");
        assertOnSlide("75 miles ✅", formatWithUsage("en-US", "meter", "road", 120000) + " ✅");
    }

    // Slide "ICU4J": the code on the slide (.usage() last).
    static void icu4j() {
        LocalizedNumberFormatter formatter = NumberFormatter.with()
                .unit(MeasureUnit.forIdentifier("meter"))
                .unitWidth(UnitWidth.FULL_NAME)
                .locale(ULocale.forLanguageTag("en-US"))
                .usage("person-height");

        FormattedNumber result = formatter.format(1.8);
        String text = result.toString();
        MeasureUnit unit = result.getOutputUnit();

        assertOnSlide("5 feet, 11 inches", text);
        assertOnSlide("foot-and-inch", unit.getIdentifier());
    }

    // Slide "Without `.usage()`": the same formatter without the usage.
    static void withoutUsage() {
        LocalizedNumberFormatter formatter = NumberFormatter.with()
                .unit(MeasureUnit.forIdentifier("meter"))
                .unitWidth(UnitWidth.FULL_NAME)
                .locale(ULocale.forLanguageTag("en-US"));

        FormattedNumber result = formatter.format(1.8);
        String text = result.toString();

        assertOnSlide("1.8 meters", text);
        assertOnSlide("5 feet, 11 inches", personHeight("en-US").format(1.8));
        // Speaker notes: ICU4J has no output unit without a usage.
        assertEquals("null", result.getOutputUnit());
    }

    // Slide "1.7 meters: set your own precision".
    static void ownPrecision() {
        LocalizedNumberFormatter formatter = personHeight("en-US");
        String byDefault = formatter.format(1.7).toString();
        String integer = formatter
                .precision(Precision.integer())
                .format(1.7).toString();
        String twoDecimals = formatter
                .precision(Precision.maxFraction(2))
                .format(1.7).toString();

        // Without the ICU-23558 fix (reverted for ICU 79). With it, the default is "5 feet, 7 inches".
        assertOnSlide("5 feet, 6.9 inches", byDefault);
        assertOnSlide("5 feet, 7 inches", integer);
        assertOnSlide("5 feet, 6.93 inches", twoDecimals);
    }

    // Slide "Person height: 1.8 meters".
    static void personHeightTable() {
        assertPersonHeight("en-US", "5 feet, 11 inches", "foot-and-inch");
        assertPersonHeight("en-GB", "5 feet, 11 inches", "foot-and-inch");
        assertPersonHeight("de-DE", "180 Zentimeter", "centimeter");
        assertPersonHeight("fr-FR", "1 mètre et 80 centimètres", "meter-and-centimeter");
        assertPersonHeight("ja-JP", "180 センチメートル", "centimeter");
        assertPersonHeight("ar-EG", "متر و٨٠ سنتيمتر", "meter-and-centimeter");
        assertPersonHeight("en-US-u-ms-metric", "180 centimeters", "centimeter");
    }

    // Slide "Road distance: same code, different values".
    static void roadDistance() {
        String[][] table = {
            {"en-US", "500 feet", "0.56 miles", "3.1 miles", "75 miles"},
            {"en-GB", "150 yards", "0.56 miles", "3.1 miles", "75 miles"},
            {"de-DE", "150 Meter", "0,9 Kilometer", "5 Kilometer", "120 Kilometer"}};
        double[] meters = {150, 900, 5000, 120000};
        for (String[] row : table) {
            for (int i = 0; i < meters.length; i++) {
                assertOnSlide(row[i + 1], formatWithUsage(row[0], "meter", "road", meters[i]));
            }
        }
        assertOnSlide("86 degrees Fahrenheit", formatWithUsage("en-US", "celsius", "weather", 30));
    }

    static FormattedNumber frenchDuration(String unit) {
        return NumberFormatter.with()
                .unit(MeasureUnit.forIdentifier(unit))
                .unitWidth(UnitWidth.FULL_NAME)
                .locale(ULocale.FRENCH)
                .format(1);
    }

    // Slide "Gender vs. case": one example on each card.
    static void genderVsCase() {
        FormattedNumber month = frenchDuration("month");
        FormattedNumber week = frenchDuration("week");
        assertOnSlide("1 mois offert · 1 semaine offert**e**",
                month + " offert · " + week + " offert**e**");
        String nominative = formatWithCase("de", "kilometer", 100, GrammaticalCase.NOMINATIVE);
        String dative = formatWithCase("de", "kilometer", 100, GrammaticalCase.DATIVE);
        assertEquals(nominative + "n", dative);
        assertOnSlide("100 Kilometer · mit 100 Kilometer**n**",
                nominative + " · mit " + nominative + "**n**");
    }

    // Slide "Grammatical gender changes the message" (French free trial).
    static void genderChangesTheMessage() {
        FormattedNumber month = frenchDuration("month");
        FormattedNumber week = frenchDuration("week");
        assertEquals("masculine", month.getNounClass().getIdentifier());
        assertEquals("feminine", week.getNounClass().getIdentifier());
        assertOnSlide("**1 mois offert**", "**" + month + " offert**");
        // The naive message, with no gender: wrong for a feminine unit.
        assertOnSlide("~~1 semaine offert~~", "~~" + week + " offert~~");
        assertOnSlide("**1 semaine offerte**", "**" + week + " offerte**");
    }

    // Slide "Tutorial 2: grammatical gender": the code on the slide.
    static void tutorialTwo() {
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

        assertOnSlide("[1 semaine]", "[" + duration + "]");
        assertOnSlide("[feminine]", "[" + gender + "]");
        assertOnSlide("[1 semaine offerte ✅]", "[" + text + " ✅]");
        FormattedNumber month = frenchDuration("month");
        assertOnSlide("[1 mois offert ✅]", "[" + trial.format(Map.of(
                "gender", month.getNounClass().getIdentifier(), "duration", month.toString())) + " ✅]");
    }

    // Slide "The gender is only known at runtime" (ru-US, usage road).
    static void genderAtRuntime() {
        FormattedNumber feet = formatWithUsage("ru-US", "meter", "road", 100);
        assertOnSlide("350 футов", feet);
        assertOnSlide("foot", feet.getOutputUnit().getIdentifier());
        FormattedNumber miles = formatWithUsage("ru-US", "meter", "road", 10000);
        assertOnSlide("6,2 мили", miles);
        assertOnSlide("mile", miles.getOutputUnit().getIdentifier());
        // Known ICU4J bug: getNounClass() returns UNDEFINED whenever usage() is set.
        // ICU4C returns masculine and feminine (see units_test.cpp). When the bug is
        // fixed, these two checks fail: update them and the slide notes.
        assertEquals("undefined", feet.getNounClass().getIdentifier());
        assertEquals("undefined", miles.getNounClass().getIdentifier());
    }

    // Slide "Grammatical case changes the unit" (German).
    static void caseChangesTheUnit() {
        String nominative = formatWithCase("de", "kilometer-per-hour", 100, GrammaticalCase.NOMINATIVE);
        String dative = formatWithCase("de", "kilometer-per-hour", 100, GrammaticalCase.DATIVE);
        assertOnSlide("Erlaubt sind **100 Kilometer pro Stunde**.", "Erlaubt sind **" + nominative + "**.");
        assertOnSlide("Er fährt mit **100 Kilometern pro Stunde**.", "Er fährt mit **" + dative + "**.");
    }

    // Slide "The same unit in different cases".
    static void sameUnitInDifferentCases() {
        assertOnSlide("3 Meter", formatWithCase("de", "meter", 3, GrammaticalCase.NOMINATIVE));
        assertOnSlide("3 Meter", formatWithCase("de", "meter", 3, GrammaticalCase.GENITIVE));
        assertOnSlide("3 Metern", formatWithCase("de", "meter", 3, GrammaticalCase.DATIVE));
        assertOnSlide("3 metry", formatWithCase("pl", "meter", 3, GrammaticalCase.NOMINATIVE));
        assertOnSlide("3 metrów", formatWithCase("pl", "meter", 3, GrammaticalCase.GENITIVE));
        assertOnSlide("3 metrom", formatWithCase("pl", "meter", 3, GrammaticalCase.DATIVE));
        assertOnSlide("3 metrami", formatWithCase("pl", "meter", 3, GrammaticalCase.INSTRUMENTAL));
        assertOnSlide("3 metrach", formatWithCase("pl", "meter", 3, GrammaticalCase.LOCATIVE));
        assertOnSlide("3 метра", formatWithCase("ru", "meter", 3, GrammaticalCase.NOMINATIVE));
        assertOnSlide("3 метров", formatWithCase("ru", "meter", 3, GrammaticalCase.GENITIVE));
        assertOnSlide("3 метрам", formatWithCase("ru", "meter", 3, GrammaticalCase.DATIVE));
        assertOnSlide("3 метрами", formatWithCase("ru", "meter", 3, GrammaticalCase.INSTRUMENTAL));
        assertOnSlide("3 метрах", formatWithCase("ru", "meter", 3, GrammaticalCase.PREPOSITIONAL));
    }

    // Slide "Tutorial 3: grammatical case": the code on the slide.
    static void tutorialThree() {
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

        assertOnSlide("[100 Kilometern pro Stunde]", "[" + speed + "]");
        assertOnSlide("[Er fährt mit 100 Kilometern pro Stunde. ✅]", "[" + text + " ✅]");
        // Without displayOptions: the nominative, which is wrong after "mit".
        String withoutCase = NumberFormatter.with()
                .unit(MeasureUnit.forIdentifier("kilometer-per-hour"))
                .unitWidth(UnitWidth.FULL_NAME)
                .locale(ULocale.GERMAN)
                .format(100).toString();
        assertOnSlide("[Er fährt mit 100 Kilometer pro Stunde. ❌]",
                "[" + drives.format(Map.of("speed", withoutCase)) + " ❌]");
    }

    // --- Helpers -----------------------------------------------------------------

    static final UnitWidth SHORT = UnitWidth.SHORT;
    static final UnitWidth FULL = UnitWidth.FULL_NAME;

    static LocalizedNumberFormatter personHeight(String localeTag) {
        return NumberFormatter.with()
                .unit(MeasureUnit.forIdentifier("meter"))
                .usage("person-height")
                .unitWidth(UnitWidth.FULL_NAME)
                .locale(ULocale.forLanguageTag(localeTag));
    }

    static void assertPersonHeight(String localeTag, String expected, String expectedUnit) {
        FormattedNumber result = personHeight(localeTag).format(1.8);
        assertOnSlide(expected, result);
        assertOnSlide(expectedUnit, result.getOutputUnit().getIdentifier());
    }

    /** Formats a value with locale- and usage-aware unit selection. */
    static FormattedNumber formatWithUsage(String localeTag, String unit, String usage,
                                           double value) {
        return NumberFormatter.with()
                .unit(MeasureUnit.forIdentifier(unit))
                .usage(usage)
                .unitWidth(UnitWidth.FULL_NAME)
                .locale(ULocale.forLanguageTag(localeTag))
                .format(value);
    }

    static String formatWithCase(String localeTag, String unit, double value,
                                 GrammaticalCase grammaticalCase) {
        return NumberFormatter.with()
                .unit(MeasureUnit.forIdentifier(unit))
                .unitWidth(UnitWidth.FULL_NAME)
                .displayOptions(DisplayOptions.builder().setGrammaticalCase(grammaticalCase).build())
                .locale(ULocale.forLanguageTag(localeTag))
                .format(value)
                .toString();
    }

    /** Formats a value in exactly this unit (en-US), without any unit selection. */
    static String format(String unit, double value, UnitWidth width, Precision precision) {
        return NumberFormatter.with()
                .unit(MeasureUnit.forIdentifier(unit))
                .unitWidth(width)
                .precision(precision)
                .locale(ULocale.forLanguageTag("en-US"))
                .format(value)
                .toString();
    }

    /**
     * Converts with ICU's internal converter. It is not public API; the conversion
     * slides use it to show the intermediate numbers.
     */
    static double convert(String source, String target, double value) {
        return new UnitsConverter(source, target).convert(new BigDecimal(value)).doubleValue();
    }

    static String plain(double value) {
        return new BigDecimal(value).round(new MathContext(12)).stripTrailingZeros().toPlainString();
    }

    // --- A tiny test runner (no JUnit needed) -------------------------------------

    static String slides;
    static int assertions;
    static final List<String> failures = new ArrayList<>();

    static void assertEquals(String expected, Object actual) {
        assertions++;
        if (!expected.equals(String.valueOf(actual))) {
            failures.add("expected \"" + expected + "\" but ICU returned \"" + actual + "\"");
        }
    }

    static void assertOnSlide(String expected, Object actual) {
        assertEquals(expected, actual);
        if (!slides.contains(expected)) {
            failures.add("\"" + expected + "\" is not in slides.md");
        }
    }

    static int run(String slideTitle, Runnable test) {
        failures.clear();
        assertions = 0;
        if (!slides.contains("# " + slideTitle)) {
            failures.add("no slide titled \"" + slideTitle + "\"");
        }
        try {
            test.run();
        } catch (RuntimeException e) {
            failures.add("threw " + e);
        }
        System.out.printf("%s  %-50s %2d checks%n",
                failures.isEmpty() ? "PASS" : "FAIL", slideTitle, assertions);
        failures.forEach(failure -> System.out.println("      " + failure));
        return failures.isEmpty() ? 0 : 1;
    }

    public static void main(String[] args) throws Exception {
        slides = Files.readString(Path.of(args.length > 0 ? args[0] : "slides.md"));
        int failed = 0;
        failed += run("Is 30 degrees hot or cold?", UnitsTest::isThirtyDegreesHotOrCold);
        failed += run("How tall are you?", UnitsTest::howTallAreYou);
        failed += run("How tall is your child?", UnitsTest::howTallIsYourChild);
        failed += run("What the CLDR data says", UnitsTest::whatTheCldrDataSays);
        failed += run("Follow 1.8 m through the CLDR data", UnitsTest::followPersonHeight);
        failed += run("Follow 150 m through the CLDR data", UnitsTest::followRoad);
        failed += run("Conversion data in CLDR", UnitsTest::conversionDataInCldr);
        failed += run("Every unit hangs from a base unit", UnitsTest::everyUnitHangsFromABaseUnit);
        failed += run("Compound units: each part climbs its own tree", UnitsTest::compoundUnits);
        failed += run("Step 1: Single convert", UnitsTest::stepOneConvert);
        failed += run("Step 2: Cascading convert", UnitsTest::stepTwoMixedUnits);
        failed += run("Step 3: Round through the cascade", UnitsTest::stepThreeRounding);
        failed += run("Step 4: Route each value to the best unit", UnitsTest::stepFourRoute);
        failed += run("Step 4: the first match wins", UnitsTest::routerStepByStep);
        failed += run("ICU4J", UnitsTest::icu4j);
        failed += run("Without `.usage()`", UnitsTest::withoutUsage);
        failed += run("1.7 meters: set your own precision", UnitsTest::ownPrecision);
        failed += run("Person height: 1.8 meters", UnitsTest::personHeightTable);
        failed += run("Road distance: same code, different values", UnitsTest::roadDistance);
        failed += run("Gender vs. case", UnitsTest::genderVsCase);
        failed += run("Grammatical gender: the unit changes the sentence", UnitsTest::genderChangesTheMessage);
        failed += run("Tutorial 2: grammatical gender", UnitsTest::tutorialTwo);
        failed += run("The gender is only known at runtime", UnitsTest::genderAtRuntime);
        failed += run("Grammatical case: the sentence changes the unit", UnitsTest::caseChangesTheUnit);
        failed += run("The same unit in different cases", UnitsTest::sameUnitInDifferentCases);
        failed += run("Tutorial 3: grammatical case", UnitsTest::tutorialThree);
        System.out.println(failed == 0 ? "ICU4J: all slide tests passed"
                : "ICU4J: " + failed + " slide test(s) failed");
        System.exit(failed == 0 ? 0 : 1);
    }
}
