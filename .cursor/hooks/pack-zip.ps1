# Cursor hook: refresh chatbot.zip after agent edits (debounced in pack script).
$ErrorActionPreference = "SilentlyContinue"
$null = [Console]::In.ReadToEnd()
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
& powershell -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\pack-chatbot-zip.ps1")
exit 0
