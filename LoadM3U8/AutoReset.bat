@echo off

@REM ping -n 30 127.0.0.1
echo ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
set /p = ■<nul
for /L %%i in (1 1 52) do @set /p a=■<nul&ping -n 5 127.0.0.1>nul
echo 100%%
echo └────────────────────────────────────────────────────────────────────────────────────────────────────────┘

for /f "tokens=2" %%i in (recordCmdPid.txt) do taskkill /pid %%i

for /f "tokens=* skip=1" %%i in (Input.txt) do (	
	echo %%i>>$
)
for /f "tokens=*" %%i in (Input.txt) do (
	echo "FirstLine:" %%i
	echo %%i>>$
	goto out
)
:out
move $ Input.txt
@REM start cmd /k AutoLoad.bat
@REM exit
pause
