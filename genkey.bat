@echo off
REM Shortcut to run tools/keygen.ps1 without PowerShell syntax headaches
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\keygen.ps1" %*
