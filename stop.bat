@echo off
echo Stopping Interview Detection System...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    if NOT "%%a"=="0" (
        taskkill /F /PID %%a
    )
)
echo System stopped.
pause
