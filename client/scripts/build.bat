@echo off
setlocal

cd %~dp0..
echo 🧹 Cleaning dist folder...
if exist dist rmdir /s /q dist

echo 🛠️ Building package...
python -m build

echo ✅ Build completed. Check the dist/ directory.
endlocal
