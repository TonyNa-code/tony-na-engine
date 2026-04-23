#!/bin/zsh
cd "$(dirname "$0")"
python3 -m unittest discover -s tests -p 'test_browser_playwright_smoke.py' -v
