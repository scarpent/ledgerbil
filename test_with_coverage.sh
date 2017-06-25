#!/bin/bash

if [[ "$1" = "-b" ]]; then
    branch=--branch
fi

coverage run $branch -m unittest discover tests
coverage report -m --omit=/usr/* --omit=/Users/scarpent/.virtualenvs/* | grep -Ev '^[^T].*100%'
coverage html --omit=/usr/* --omit=/Users/scarpent/.virtualenvs/*

