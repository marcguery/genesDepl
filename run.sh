#!/bin/bash

if [[ ! -f log/last-mod.txt ]];then
	touch log/last-mod.txt
fi

main=${1:-"main.py"}

export FLASK_ENV=development
export FLASK_APP=$main
flask run