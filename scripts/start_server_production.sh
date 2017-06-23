#!/bin/bash
PROJECT_DIR=$( dirname "${BASH_SOURCE[0]}" )/..
cd "$PROJECT_DIR"

npm run build:production
python3.5 -m vj4.unix_server
