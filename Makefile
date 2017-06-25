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
	python -m pytest $(PT) | grep -Ev '^[^T].*100%' && flake8

unittest:
	./test_with_coverage.sh
