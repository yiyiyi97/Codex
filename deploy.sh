#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-8000}"

nohup python3 "$ROOT_DIR/app.py" > "$ROOT_DIR/server.log" 2>&1 &

echo "EHS系统已启动: http://<server-ip>:$PORT"
echo "日志文件: $ROOT_DIR/server.log"
