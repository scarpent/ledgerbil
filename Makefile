PYTEST_ARGS ?=

.PHONY: virtualenv deps unittest testpdb unittest

virtualenv:
	pip install virtualenv --upgrade
	virtualenv ve --python=python2.7 --prompt="(ledgerbil) "

mkvirtualenv:
	source virtualenvwrapper.sh; mkvirtualenv --python=python2.7 ledgerbil

deps:
	pip install --requirement requirements.txt

test:
	python -m pytest $(PYTEST_ARGS) --cov-report term-missing --cov-report html --cov . | grep -Ev '^[^T].*100%'

testpdb:
	python -m pytest $(PYTEST_ARGS) -s

unittest:
	./test_with_coverage.sh
