@echo off

ping -n 600 127.0.0.1
for /f "tokens=2" %%i in (recordCmdPid.txt) do taskkill /pid %%i

for /f "tokens=* skip=1" %%i in (Input.txt) do (
	echo %%i>>$
)
for /f "tokens=*" %%i in (Input.txt) do (
	echo %%i>>$
	goto out
)
:out
move $ Input.txt
start cmd /k AutoLoad.bat
exit