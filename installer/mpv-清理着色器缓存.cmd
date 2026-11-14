@echo off
setlocal
chcp 65001 >nul
echo 1. 清理 mpv 编译着色器缓存
echo 2. 同时重置 AMD Vulkan 驱动缓存（其他应用也会重新编译）
echo 缓存将移入 backup\shader-cache，等待全部 mpv 窗口退出后执行。
choice /C 12 /N /M "请选择 [1/2]："
set "cache_mode=mpv"
if errorlevel 2 set "cache_mode=amd-vulkan"
set "MPV_CACHE_HELPER=%~dp0clear-shader-cache.ps1"
set "MPV_CACHE_CONFIG=%~dp0..\portable_config"
powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create([IO.File]::ReadAllText($env:MPV_CACHE_HELPER,[Text.Encoding]::UTF8))) -ConfigDirectory $env:MPV_CACHE_CONFIG -Mode $env:cache_mode"
echo.
echo 清理结果和备份位置见上方输出；下次启动将重新编译缓存。
pause
