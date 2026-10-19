// UTW 2026 tutorial: "Beyond Meters and Miles". ICU4C test cases.
//
// The same slide tests as UnitsTest.java, for the outputs that the C++ API has:
//   ASSERT_ON_SLIDE(expected, actual)  checks that ICU returns `expected` and that
//                                      `expected` is in slides.md.
// The test also checks that each slide title is in slides.md.
//
// Build and run from the talk folder against an ICU4C checkout (or: make test):
//   ICU=<icu>/icu4c/source
//   g++ -std=c++17 -I$ICU/common -I$ICU/i18n demos/cpp/units_test.cpp -L$ICU/lib -licui18n -licuuc -licudata -o demos/cpp/units_test
//   LD_LIBRARY_PATH=$ICU/lib demos/cpp/units_test slides.md

#include <fstream>
#include <functional>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "unicode/displayoptions.h"
#include "unicode/locid.h"
#include "unicode/measunit.h"
#include "unicode/numberformatter.h"
#include "unicode/unistr.h"

using icu::DisplayOptions;
using icu::Locale;
using icu::MeasureUnit;
using icu::UnicodeString;
using icu::number::FormattedNumber;
using icu::number::LocalizedNumberFormatter;
using icu::number::NumberFormatter;
using icu::number::Precision;

namespace {

// --- A tiny test runner (no gtest needed) -------------------------------------

std::string slides;
int assertions = 0;
std::vector<std::string> failures;

void assertOnSlide(const std::string& expected, const std::string& actual) {
    assertions++;
    if (expected != actual) {
        failures.push_back("expected \"" + expected + "\" but ICU returned \"" + actual + "\"");
    }
    if (slides.find(expected) == std::string::npos) {
        failures.push_back("\"" + expected + "\" is not in slides.md");
    }
}

#define ASSERT_ON_SLIDE(expected, actual) assertOnSlide(expected, actual)

int run(const std::string& slideTitle, const std::function<void()>& test) {
    failures.clear();
    assertions = 0;
    if (slides.find("# " + slideTitle) == std::string::npos) {
        failures.push_back("no slide titled \"" + slideTitle + "\"");
    }
    test();
    std::printf("%s  %-50s %2d checks\n", failures.empty() ? "PASS" : "FAIL",
                slideTitle.c_str(), assertions);
    for (const std::string& failure : failures) {
        std::cout << "      " << failure << "\n";
    }
    return failures.empty() ? 0 : 1;
}

// --- Helpers -------------------------------------------------------------------

std::string toUtf8(const UnicodeString& text) {
    std::string result;
    text.toUTF8String(result);
    return result;
}

std::string check(UErrorCode status, const std::string& text) {
    return U_FAILURE(status) ? std::string("error ") + u_errorName(status) : text;
}

LocalizedNumberFormatter usageFormatter(const char* localeTag, const char* unit,
                                        const char* usage) {
    UErrorCode status = U_ZERO_ERROR;
    return NumberFormatter::with()
        .unit(MeasureUnit::forIdentifier(unit, status))
        .usage(usage)
        .unitWidth(UNUM_UNIT_WIDTH_FULL_NAME)
        .locale(Locale::forLanguageTag(localeTag, status));
}

struct Result {
    std::string text;
    std::string unit;
    std::string nounClass;
};

Result format(const LocalizedNumberFormatter& formatter, double value) {
    UErrorCode status = U_ZERO_ERROR;
    FormattedNumber result = formatter.formatDouble(value, status);
    std::string text = toUtf8(result.toString(status));
    // Keep the MeasureUnit alive: getIdentifier() points into the object.
    MeasureUnit unit = result.getOutputUnit(status);
    const char* nounClass = udispopt_getNounClassIdentifier(result.getNounClass(status));
    return {check(status, text), unit.getIdentifier(), nounClass};
}

Result formatWithUsage(const char* localeTag, const char* unit, const char* usage,
                       double value) {
    return format(usageFormatter(localeTag, unit, usage), value);
}

std::string formatWithCase(const char* localeTag, const char* unit, double value,
                           UDisplayOptionsGrammaticalCase grammaticalCase) {
    UErrorCode status = U_ZERO_ERROR;
    LocalizedNumberFormatter formatter =
        NumberFormatter::with()
            .unit(MeasureUnit::forIdentifier(unit, status))
            .unitWidth(UNUM_UNIT_WIDTH_FULL_NAME)
            .displayOptions(DisplayOptions::builder().setGrammaticalCase(grammaticalCase).build())
            .locale(Locale::forLanguageTag(localeTag, status));
    return check(status, format(formatter, value).text);
}

void assertPersonHeight(const char* localeTag, const std::string& expected,
                        const std::string& expectedUnit) {
    Result result = formatWithUsage(localeTag, "meter", "person-height", 1.8);
    ASSERT_ON_SLIDE(expected, result.text);
    ASSERT_ON_SLIDE(expectedUnit, result.unit);
}

Result frenchDuration(const char* unit) {
    UErrorCode status = U_ZERO_ERROR;
    LocalizedNumberFormatter formatter = NumberFormatter::with()
            .unit(MeasureUnit::forIdentifier(unit, status))
            .unitWidth(UNUM_UNIT_WIDTH_FULL_NAME)
            .locale(Locale::getFrench());
    return format(formatter, 1);
}

// "1 semaine" → "semaine" (the number is followed by a U+00A0 no-break space).
std::string unitName(const std::string& text) {
    const std::string nbsp = "\xC2\xA0";
    size_t pos = text.find(nbsp);
    return pos == std::string::npos ? text : text.substr(pos + nbsp.size());
}

// --- Slide tests -------------------------------------------------------------

// Slide "How tall are you?": Sam's final answer.
void howTallAreYou() {
    ASSERT_ON_SLIDE("5 feet, 11 inches", formatWithUsage("en-US", "meter", "person-height", 1.8).text);
}

// Slide "How tall is your child?" (0.7 m).
void howTallIsYourChild() {
    ASSERT_ON_SLIDE("28 inches", formatWithUsage("en-US", "meter", "person-height", 0.7).text);
}

// Slide "What the CLDR data says".
void whatTheCldrDataSays() {
    ASSERT_ON_SLIDE("foot-and-inch", formatWithUsage("en-US", "meter", "person-height", 1.8).unit);
    ASSERT_ON_SLIDE("inch", formatWithUsage("en-US", "meter", "person-height", 0.7).unit);
    ASSERT_ON_SLIDE("meter-and-centimeter", formatWithUsage("fr-FR", "meter", "person-height", 1.8).unit);
    ASSERT_ON_SLIDE("centimeter", formatWithUsage("de-DE", "meter", "person-height", 1.8).unit);
    ASSERT_ON_SLIDE("50 feet", formatWithUsage("en-US", "meter", "road", 15).text);
    ASSERT_ON_SLIDE("7 feet", formatWithUsage("en-US", "meter", "road", 2).text);
    ASSERT_ON_SLIDE("30 yards", formatWithUsage("en-GB", "meter", "road", 25).text);
    ASSERT_ON_SLIDE("2 yards", formatWithUsage("en-GB", "meter", "road", 2).text);
    ASSERT_ON_SLIDE("300 Meter", formatWithUsage("de-DE", "meter", "road", 320).text);
    ASSERT_ON_SLIDE("20 Meter", formatWithUsage("de-DE", "meter", "road", 24).text);
    ASSERT_ON_SLIDE("7 Meter", formatWithUsage("de-DE", "meter", "road", 7.4).text);
}

// Slide "Step 1: Single convert": fuel consumption is a reciprocal.
void stepOneConvert() {
    ASSERT_ON_SLIDE("36 miles per gallon",
                    formatWithUsage("en-US", "liter-per-100-kilometer", "vehicle-fuel", 6.5).text);
    ASSERT_ON_SLIDE("43 miles per gallon",
                    formatWithUsage("en-GB", "liter-per-100-kilometer", "vehicle-fuel", 6.5).text);
}

// Slide "Step 3: Round through the cascade" (1.826 m).
void stepThreeRounding() {
    ASSERT_ON_SLIDE("6 feet, 0 inches",
                    formatWithUsage("en-US", "meter", "person-height", 1.826).text);
}

// Slide "Step 4: Route each value to the best unit".
void stepFourRoute() {
    ASSERT_ON_SLIDE("500 feet", formatWithUsage("en-US", "meter", "road", 150).text);
    ASSERT_ON_SLIDE("0.56 miles", formatWithUsage("en-US", "meter", "road", 900).text);
    ASSERT_ON_SLIDE("75 miles", formatWithUsage("en-US", "meter", "road", 120000).text);
    ASSERT_ON_SLIDE("150 yards", formatWithUsage("en-GB", "meter", "road", 150).text);
}

// Slide "ICU4C": the code on the slide (.usage() last).
void icu4c() {
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

    ASSERT_ON_SLIDE("5 feet, 11 inches", check(status, toUtf8(text)));
    ASSERT_ON_SLIDE("foot-and-inch", id);
}

// Slide "1.7 meters: set your own precision".
void ownPrecision() {
    LocalizedNumberFormatter formatter = usageFormatter("en-US", "meter", "person-height");
    // Without the ICU-23558 fix (reverted for ICU 79). With it, the default is "5 feet, 7 inches".
    ASSERT_ON_SLIDE("5 feet, 6.9 inches", format(formatter, 1.7).text);
    ASSERT_ON_SLIDE("5 feet, 7 inches", format(formatter.precision(Precision::integer()), 1.7).text);
    ASSERT_ON_SLIDE("5 feet, 6.93 inches",
                    format(formatter.precision(Precision::maxFraction(2)), 1.7).text);
}

// Slide "Person height: 1.8 meters".
void personHeightTable() {
    assertPersonHeight("en-US", "5 feet, 11 inches", "foot-and-inch");
    assertPersonHeight("en-GB", "5 feet, 11 inches", "foot-and-inch");
    assertPersonHeight("de-DE", "180 Zentimeter", "centimeter");
    assertPersonHeight("fr-FR", "1 mètre et 80 centimètres", "meter-and-centimeter");
    assertPersonHeight("ja-JP", "180 センチメートル", "centimeter");
    assertPersonHeight("ar-EG", "متر و٨٠ سنتيمتر", "meter-and-centimeter");
    assertPersonHeight("en-US-u-ms-metric", "180 centimeters", "centimeter");
}

// Slide "Road distance: same code, different values".
void roadDistance() {
    const std::vector<std::vector<std::string>> table = {
        {"en-US", "500 feet", "0.56 miles", "3.1 miles", "75 miles"},
        {"en-GB", "150 yards", "0.56 miles", "3.1 miles", "75 miles"},
        {"de-DE", "150 Meter", "0,9 Kilometer", "5 Kilometer", "120 Kilometer"}};
    const double meters[] = {150, 900, 5000, 120000};
    for (const auto& row : table) {
        for (int i = 0; i < 4; i++) {
            ASSERT_ON_SLIDE(row[i + 1],
                            formatWithUsage(row[0].c_str(), "meter", "road", meters[i]).text);
        }
    }
    ASSERT_ON_SLIDE("86 degrees Fahrenheit",
                    formatWithUsage("en-US", "celsius", "weather", 30).text);
    ASSERT_ON_SLIDE("30 degrees Celsius",
                    formatWithUsage("en-US-u-mu-celsius", "celsius", "weather", 30).text);
}

// Slide "Grammatical gender changes the message" (French free trial): the
// adjective follows the noun class that ICU returns.
void genderChangesTheMessage() {
    for (const char* unit : {"month", "week"}) {
        Result duration = frenchDuration(unit);
        std::string adjective = duration.nounClass == std::string("feminine") ? "offerte" : "offert";
        ASSERT_ON_SLIDE("**" + duration.text + " " + adjective + "** ✅ · *" +
                            unitName(duration.text) + "* is " + duration.nounClass,
                        std::string(unit) == "month"
                            ? "**1 mois offert** ✅ · *mois* is masculine"
                            : "**1 semaine offerte** ✅ · *semaine* is feminine");
    }
}

// Slide "Tutorial 2: grammatical gender": the duration and its noun class.
void tutorialTwo() {
    Result week = frenchDuration("week");
    ASSERT_ON_SLIDE("[1 semaine]", "[" + week.text + "]");
    ASSERT_ON_SLIDE("[feminine]", "[" + week.nounClass + "]");
}

// Slide "The gender is only known at runtime" (ru-US, usage road).
// ICU4C returns the noun class with usage() (ICU4J has a bug here).
void genderAtRuntime() {
    Result feet = formatWithUsage("ru-US", "meter", "road", 100);
    ASSERT_ON_SLIDE("| 100 m | 350 футов | foot | masculine |",
                    "| 100 m | " + feet.text + " | " + feet.unit + " | " + feet.nounClass + " |");
    Result miles = formatWithUsage("ru-US", "meter", "road", 10000);
    ASSERT_ON_SLIDE("| 10 km | 6,2 мили | mile | feminine |",
                    "| 10 km | " + miles.text + " | " + miles.unit + " | " + miles.nounClass + " |");
}

// Slide "Grammatical case changes the unit" (German).
void caseChangesTheUnit() {
    ASSERT_ON_SLIDE("Erlaubt sind **100 Kilometer pro Stunde**.",
                    "Erlaubt sind **" +
                        formatWithCase("de", "kilometer-per-hour", 100,
                                       UDISPOPT_GRAMMATICAL_CASE_NOMINATIVE) + "**.");
    ASSERT_ON_SLIDE("Er fährt mit **100 Kilometern pro Stunde**.",
                    "Er fährt mit **" +
                        formatWithCase("de", "kilometer-per-hour", 100,
                                       UDISPOPT_GRAMMATICAL_CASE_DATIVE) + "**.");
}

// Slide "The same unit in different cases": the table, row by row.
void sameUnitInDifferentCases() {
    auto row = [](const char* name, UDisplayOptionsGrammaticalCase polishCase,
                  UDisplayOptionsGrammaticalCase russianCase, bool german) {
        std::string de = german ? formatWithCase("de", "meter", 3, polishCase) : "—";
        return std::string("| ") + name + " | " + de + " | " +
               formatWithCase("pl", "meter", 3, polishCase) + " | " +
               formatWithCase("ru", "meter", 3, russianCase) + " |";
    };
    ASSERT_ON_SLIDE("| nominative | 3 Meter | 3 metry | 3 метра |",
                    row("nominative", UDISPOPT_GRAMMATICAL_CASE_NOMINATIVE,
                        UDISPOPT_GRAMMATICAL_CASE_NOMINATIVE, true));
    ASSERT_ON_SLIDE("| genitive | 3 Meter | 3 metrów | 3 метров |",
                    row("genitive", UDISPOPT_GRAMMATICAL_CASE_GENITIVE,
                        UDISPOPT_GRAMMATICAL_CASE_GENITIVE, true));
    ASSERT_ON_SLIDE("| dative | 3 Metern | 3 metrom | 3 метрам |",
                    row("dative", UDISPOPT_GRAMMATICAL_CASE_DATIVE,
                        UDISPOPT_GRAMMATICAL_CASE_DATIVE, true));
    ASSERT_ON_SLIDE("| instrumental | — | 3 metrami | 3 метрами |",
                    row("instrumental", UDISPOPT_GRAMMATICAL_CASE_INSTRUMENTAL,
                        UDISPOPT_GRAMMATICAL_CASE_INSTRUMENTAL, false));
    ASSERT_ON_SLIDE("| locative / prepositional | — | 3 metrach | 3 метрах |",
                    row("locative / prepositional", UDISPOPT_GRAMMATICAL_CASE_LOCATIVE,
                        UDISPOPT_GRAMMATICAL_CASE_PREPOSITIONAL, false));
}

// Slide "Tutorial 3: grammatical case": the dative speed.
void tutorialThree() {
    ASSERT_ON_SLIDE("[100 Kilometern pro Stunde]",
                    "[" + formatWithCase("de", "kilometer-per-hour", 100,
                                         UDISPOPT_GRAMMATICAL_CASE_DATIVE) + "]");
}

}  // namespace

int main(int argc, char** argv) {
    std::ifstream file(argc > 1 ? argv[1] : "slides.md");
    std::stringstream buffer;
    buffer << file.rdbuf();
    slides = buffer.str();
    if (slides.empty()) {
        std::cerr << "cannot read slides.md\n";
        return 2;
    }

    int failed = 0;
    failed += run("How tall are you?", howTallAreYou);
    failed += run("How tall is your child?", howTallIsYourChild);
    failed += run("What the CLDR data says", whatTheCldrDataSays);
    failed += run("Step 1: Single convert", stepOneConvert);
    failed += run("Step 3: Round through the cascade", stepThreeRounding);
    failed += run("Step 4: Route each value to the best unit", stepFourRoute);
    failed += run("ICU4C", icu4c);
    failed += run("1.7 meters: set your own precision", ownPrecision);
    failed += run("Person height: 1.8 meters", personHeightTable);
    failed += run("Road distance: same code, different values", roadDistance);
    failed += run("Grammatical gender changes the message", genderChangesTheMessage);
    failed += run("Tutorial 2: grammatical gender", tutorialTwo);
    failed += run("The gender is only known at runtime", genderAtRuntime);
    failed += run("Grammatical case changes the unit", caseChangesTheUnit);
    failed += run("The same unit in different cases", sameUnitInDifferentCases);
    failed += run("Tutorial 3: grammatical case", tutorialThree);
    std::cout << (failed == 0 ? "ICU4C: all slide tests passed\n"
                              : "ICU4C: " + std::to_string(failed) + " slide test(s) failed\n");
    return failed == 0 ? 0 : 1;
}
