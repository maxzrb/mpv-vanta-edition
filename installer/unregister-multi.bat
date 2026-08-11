@echo off
call "%~dp0associations\current-user\unregister-multi.bat" %*
exit /b %errorlevel%
