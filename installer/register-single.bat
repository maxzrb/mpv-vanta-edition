@echo off
call "%~dp0associations\current-user\register-single.bat" %*
exit /b %errorlevel%
