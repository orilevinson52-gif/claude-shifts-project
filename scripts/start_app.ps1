$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
& "$root\venv\Scripts\python.exe" main.py
