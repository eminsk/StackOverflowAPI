@echo off
setlocal
cd /d "%~dp0"
if not exist "StackOverflowSearch.exe" (
    call build.bat
)
if exist "StackOverflowSearch.exe" (
    start "" "StackOverflowSearch.exe"
)
