@echo off
tasklist | find "cmd.exe" >recordCmdPid.txt
start  /min cmd /k  AutoReset.bat

set file=Input.txt
@rem set /p file=请输入文件名：
echo %file%

:reload_file

for /f "tokens=1-2 " %%i  in (%file%) do (
    if not "%%i"=="" (
        if not "%%j"=="" (
            F:\SystemSofts\Python38\python.exe LoadM3U8.py %%i False %%j 2
        ) else ( 
            echo "can't find %%%% j in line:"
            echo. %%i
        )
    ) else echo "can't find %%%% i"
@rem F:\SystemSofts\Python38\python.exe LoadM3U8.py %%i False %%j 2
)

set /p i="输入任意非空字符退出:"
echo "%i%"
if "%i%"=="" goto reload_file
