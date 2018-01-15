.PHONY: venv virtualenv mkvirtualenv deps test

PYTEST_ARGS ?=
ENV_NAME=ledgerbil

venv:
	python3 -m venv ~/.venv/$(ENV_NAME)

virtualenv:
	pip install virtualenv --upgrade
	virtualenv ve --python=python3.6 --prompt="($(ENV_NAME)) "

mkvirtualenv:
	source virtualenvwrapper.sh; mkvirtualenv --python=python3.6 $(ENV_NAME)

deps:
	pip install --requirement requirements.txt

test:
	python -m pytest $(PT) | grep -Ev '^[^T].*100%' && flake8

