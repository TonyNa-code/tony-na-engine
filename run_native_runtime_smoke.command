#!/bin/zsh
cd "$(dirname "$0")"
python3 tools/runtime/run_native_runtime_smoke.py "$@"
exit_code=$?
echo ""
echo "原生 Runtime 渲染 smoke 已结束。"
read -r -p "按回车关闭..." _
exit "$exit_code"
