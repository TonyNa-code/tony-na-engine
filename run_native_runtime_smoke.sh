#!/bin/sh
cd "$(dirname "$0")" || exit 1

if command -v python3 >/dev/null 2>&1; then
  exec python3 tools/runtime/run_native_runtime_smoke.py "$@"
fi

exec python tools/runtime/run_native_runtime_smoke.py "$@"
