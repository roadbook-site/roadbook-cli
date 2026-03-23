@echo off
setlocal

cd %~dp0..
echo Launching PyPI Publishing Assistant...
python scripts\publish.py

endlocal
