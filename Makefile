PYTEST_ARGS ?=

.PHONY: virtualenv deps unittest testpdb unittest

virtualenv:
	pip install virtualenv --upgrade
	virtualenv ve --python=python3.6 --prompt="(ledgerbil3) "

mkvirtualenv:
	source virtualenvwrapper.sh; mkvirtualenv --python=python3.6 ledgerbil3

deps:
	pip install --requirement requirements.txt

test:
	python -m pytest $(PYTEST_ARGS) -rw -x --no-cov-on-fail --cov-report term-missing --cov-report html --cov . | grep -Ev '^[^T].*100%'

pdbtest:
	python -m pytest $(PYTEST_ARGS) -s -x --no-cov-on-fail

unittest:
	./test_with_coverage.sh
