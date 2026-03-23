@echo off
setlocal

REM Usage:
REM   scripts\sync_skills.bat
REM   scripts\sync_skills.bat --scope project --force

python "%~dp0dev_sync_skills.py" --mode link --scope all %*
