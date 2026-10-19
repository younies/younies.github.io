# Build the reveal.js deck from slides.md (needs pandoc 3).
#
#   make           → slides.html (loads reveal.js from a CDN, so it needs internet)
#   make offline   → slides-offline.html (one self-contained file; needs internet
#                    only while building)
#
# reveal-template.html is pandoc's default reveal.js template plus the reveal.js
# highlight plugin, which steps through code blocks that set data-line-numbers.

PANDOC_FLAGS = -t revealjs --standalone --slide-level=1 --css slides.css \
               --template reveal-template.html --no-highlight

slides.html: slides.md slides.css reveal-template.html
	pandoc slides.md $(PANDOC_FLAGS) -o slides.html

offline: slides.md slides.css reveal-template.html
	pandoc slides.md $(PANDOC_FLAGS) --embed-resources -o slides-offline.html

# Runs the slide test cases in ICU4J and ICU4C: every output on the slides must
# come from ICU (needs an ICU checkout with ICU4J and ICU4C built).
ICU ?= ../../../icu
ICU4C = $(ICU)/icu4c/source

test: test-java test-cpp

test-java:
	java -cp $(ICU)/icu4j/main/core/target/classes demos/java/UnitsTest.java slides.md

test-cpp: demos/cpp/units_test
	LD_LIBRARY_PATH=$(ICU4C)/lib demos/cpp/units_test slides.md

demos/cpp/units_test: demos/cpp/units_test.cpp
	g++ -std=c++17 -I$(ICU4C)/common -I$(ICU4C)/i18n $< -L$(ICU4C)/lib \
	    -licui18n -licuuc -licudata -o $@

.PHONY: offline test test-java test-cpp
