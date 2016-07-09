#!/bin/bash
PROJECT_DIR=$( dirname "${BASH_SOURCE[0]}" )/..
CURRENT_DIR=$( pwd )

if [ ! -f "$CURRENT_DIR"/selection.json ]; then
    echo "ERROR: selection.json not found in current directory."
    echo "Please execute in your downloaded icomoon assets directory."
    exit 1
fi

BASE_DIR="$PROJECT_DIR"/vj4/ui

find . -type f -exec chmod 0644 {} \; && find . -type d -exec chmod 0755 {} \;

cp selection.json "$BASE_DIR"/misc/fonts/.icomoon_selection.json
cp variables.styl "$BASE_DIR"/common/webicon.inc.styl
cp fonts/icomoon.* "$BASE_DIR"/misc/fonts/
tail -n +3 style.styl > "$BASE_DIR"/misc/webicon.styl
