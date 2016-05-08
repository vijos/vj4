#!/bin/bash
PROJECT_DIR=$( dirname "${BASH_SOURCE[0]}" )/..
CURRENT_DIR=$( pwd )

if [ ! -f "$CURRENT_DIR"/selection.json ]; then
    echo "ERROR: selection.json not found in current directory."
    echo "Please execute in your downloaded icomoon assets directory."
    exit 1
fi

BASE_DIR="$PROJECT_DIR"/vj4/ui/misc

cp selection.json "$BASE_DIR"/fonts/.icomoon_selection.json
cp fonts/icomoon.* "$BASE_DIR"/fonts/
cp style.css "$BASE_DIR"/webicon.css
chmod 600 "$BASE_DIR"/fonts/*
