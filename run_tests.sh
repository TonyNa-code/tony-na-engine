#!/bin/sh
cd "$(dirname "$0")" || exit 1

if command -v python3 >/dev/null 2>&1; then
  exec python3 -m unittest discover -s tests -v
fi

exec python -m unittest discover -s tests -v
