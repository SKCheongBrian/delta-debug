@echo off
setlocal enabledelayedexpansion

set VERBOSE=false
set OUTPUT_DIR=showcase_output

:: Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
)

:: Parse command-line args
:parse_args
if "%~1"=="" goto end_parse_args
if "%~1"=="--verbose" (
    set VERBOSE=true
) else (
    echo Unknown option: %~1
    exit /b 1
)
shift
goto parse_args
:end_parse_args

:: Loop over all showcase*.py files
for %%F in (showcase*.py) do (
    set "FILENAME=%%~nF"
    if "%VERBOSE%"=="true" (
        echo Running %%F with --verbose
        python %%F --verbose > "%OUTPUT_DIR%\verbose-!FILENAME!.out"
    ) else (
        echo Running %%F
        python %%F > "%OUTPUT_DIR%\!FILENAME!.out"
    )
)

echo All outputs saved in %OUTPUT_DIR%
