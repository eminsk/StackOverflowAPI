@echo off
setlocal
echo ==============================================================================
echo Building Stack Overflow Search Pro (FASM x64 Edition)
echo Toolchain: C:\asm\hdd\FASM.EXE
echo ==============================================================================

set "FASM_BIN=C:\asm\hdd\FASM.EXE"
set "INCLUDE=C:\asm\hdd\INCLUDE"

if not exist "%FASM_BIN%" (
    echo [ERROR] FASM compiler not found at "%FASM_BIN%"!
    pause
    exit /b 1
)

echo Compiling stackoverflow.asm ...
"%FASM_BIN%" "%~dp0stackoverflow.asm" "%~dp0StackOverflowSearch.exe"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Compilation failed with error code %ERRORLEVEL%!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ==============================================================================
echo [SUCCESS] Built: "%~dp0StackOverflowSearch.exe"
echo Size: 32 KB (x86-64 pure native PE)
echo ==============================================================================
