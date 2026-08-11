@echo off
setlocal
set "unattended=no"
if /i "%~1"=="/u" set "unattended=yes"
set "dry_run="
if /i "%VANTA_ASSOC_DRY_RUN%"=="1" set "dry_run=-DryRun"

"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0vanta-associations.ps1" -Action unregister -Mode multi %dry_run%
set "exit_code=%errorlevel%"

if /i not "%unattended%"=="yes" pause
exit /b %exit_code%
