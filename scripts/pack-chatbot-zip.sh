#!/usr/bin/env bash
# Pack the Knowledge Chatbot project into chatbot.zip (source only).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec powershell -ExecutionPolicy Bypass -File "$ROOT/scripts/pack-chatbot-zip.ps1" "$@"
