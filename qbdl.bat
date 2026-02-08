@echo off
REM qobuz-dl with handy options for DJs
echo qbdl is a handy downloader using qobuz-dl with common options for DJs

set "mode=%1"
set "params=%*"
REM Remove the first argument (mode)
for /f "tokens=1,* delims= " %%a in ("%*") do set "params=%%b"

if "%mode%"=="dla" (
    set "cmd_flags=dl -q 5 --no-fallback -s --no-db"
    echo [INFO] Mode: Artist/Album ^(Smart Discography, No Flattening^)
) else (
    if "%mode%"=="dlp" (
        set "cmd_flags=dl -q 5 --no-fallback --no-db --folder-format ."
        echo [INFO] Mode: Playlist ^(Flattening, No Smart Discography^)
    ) else (
        echo [ERROR] Invalid mode. Use 'dla' for Artist/Album or 'dlp' for Playlist.
        exit /b 1
    )
)

where uv >nul 2>nul
if %errorlevel% equ 0 (
    echo [INFO] Using uv...
    uv run qobuz-dl %cmd_flags% %params%
    exit /b %errorlevel%
)

echo [INFO] uv not found. Trying mamba...
call mamba activate qobuz 2>nul
if %errorlevel% equ 0 (
    where uv >nul 2>nul
    if %errorlevel% equ 0 (
        echo [INFO] Using uv inside mamba...
        uv run qobuz-dl %cmd_flags% %params%
    ) else (
        echo [INFO] Using qobuz-dl directly inside mamba...
        qobuz-dl %cmd_flags% %params%
    )
    exit /b %errorlevel%
)

echo [INFO] mamba not found or failed. Trying qobuz-dl directly...
qobuz-dl %cmd_flags% %params%