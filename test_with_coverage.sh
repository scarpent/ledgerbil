#!/bin/bash

if [[ "$1" = "-b" ]]; then
    branch=--branch
fi

coverage run $branch -m unittest discover tests
coverage report -m --omit=/usr/*
coverage html --omit=/usr/*

