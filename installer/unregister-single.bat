@echo off
call "%~dp0associations\current-user\unregister-single.bat" %*
exit /b %errorlevel%
