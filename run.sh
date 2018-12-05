#!/bin/bash

main=${1:-"main.py"}
export FLASK_ENV=development
export FLASK_APP=$main
flask run