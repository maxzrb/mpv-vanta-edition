@echo off
call "%~dp0associations\current-user\register-multi.bat" %*
exit /b %errorlevel%
