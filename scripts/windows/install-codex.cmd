@echo off
REM Double-click launcher for install-codex.ps1.
REM Bypasses the PowerShell execution policy for this one run only.
REM Pass -Uninstall or -ExePath "C:\...\vmware-knight.exe" to forward them.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-codex.ps1" %*
echo.
pause
