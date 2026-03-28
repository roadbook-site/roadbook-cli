@echo off
setlocal EnableDelayedExpansion

cd %~dp0..
echo Running tests before publish...
python -m pytest
if errorlevel 1 (
	echo.
	echo Tests failed. Publish aborted.
	exit /b 1
)

echo Launching PyPI Publishing Assistant...
python scripts\publish.py
if errorlevel 1 (
	echo.
	echo Publish script failed. Skip git push.
	exit /b 1
)

echo.
set /p AUTO_PUSH=Auto commit and push version changes now? (y/N): 
if /I "%AUTO_PUSH%"=="y" (
	for /f %%i in ('git rev-parse --abbrev-ref HEAD') do set CURRENT_BRANCH=%%i
	if "!CURRENT_BRANCH!"=="" (
		echo Failed to detect current git branch. Push aborted.
		exit /b 1
	)
	if /I "!CURRENT_BRANCH!"=="HEAD" (
		echo Detached HEAD detected. Please checkout a branch before pushing.
		exit /b 1
	)

	git add pyproject.toml skills/*/SKILL.md
	git diff --cached --quiet
	if errorlevel 1 (
		set "PACKAGE_VERSION="
		for /f "tokens=3" %%v in ('findstr /R /C:"^version[ ]*=" pyproject.toml') do set "PACKAGE_VERSION=%%~v"
		set "PACKAGE_VERSION=!PACKAGE_VERSION:"=!"

		set "COMMIT_MSG=chore: bump version"
		if not "!PACKAGE_VERSION!"=="" set "COMMIT_MSG=chore: bump version to !PACKAGE_VERSION!"

		git commit -m "!COMMIT_MSG!"
		if errorlevel 1 (
			echo Commit failed. Push aborted.
			exit /b 1
		)

		git push origin !CURRENT_BRANCH!
		if errorlevel 1 (
			echo Push failed.
			exit /b 1
		)

		echo Version changes pushed to origin/!CURRENT_BRANCH!.
	) else (
		echo No version changes detected. Nothing to commit or push.
	)
)

echo.
echo Installing local package...
python -m pip install -e .

endlocal
