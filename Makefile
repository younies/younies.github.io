# Builds and previews the site (see README.md). Needs pandoc 3 and Python 3.11+.
#
#   make                        build the site into _site/
#   make serve                  preview at http://localhost:8000/ with drafts,
#                               rebuilding on every change (PORT=8765 for another port)
#   make check                  build, then check every internal link
#   make post TITLE="My title"  start a draft blog post
#   make clean                  delete _site/

PYTHON ?= python3
PORT ?= 8000

build:
	$(PYTHON) tools/build.py

serve:
	$(PYTHON) tools/build.py --serve --port $(PORT)

check:
	$(PYTHON) tools/build.py --check

post:
	@test -n "$(TITLE)" || { echo 'Usage: make post TITLE="My post title"'; exit 1; }
	$(PYTHON) tools/build.py --new-post "$(TITLE)"

clean:
	rm -rf _site _site.new

.PHONY: build serve check post clean
