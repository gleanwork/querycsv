#!/bin/zsh

echo "vars: $@"
set -a; source .env; set +a && python3 -B querycsv.py $@