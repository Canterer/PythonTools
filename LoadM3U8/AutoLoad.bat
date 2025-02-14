@echo off
setlocal enabledelayedexpansion
@rem tasklist | find "cmd.exe" >recordCmdPid.txt
@rem start  /min cmd /k  AutoReset.bat

set file=Input.txt
@rem set /p file=请输入文件名：
echo %file%
@rem set tes="a23456.mp4"
@rem echo %tes:~-5%

:reload_file

for /f "tokens=1,2,*" %%i  in (%file%) do (
    if not %%i=="" (
        if not %%j=="" (
	set "ttemp=%%j"
	set "ttemp=!ttemp:~-4!"
	if  "!ttemp!"==".mp4" (
		if "%%k"=="" (
           			@rem E:\Softs\Python38\python.exe LoadM3U8.py %%i False %%j 3
			@rem echo "can't find arg k !!! in line: %%i  %% j"
		) else (
			E:\Softs\Python38\python.exe LoadM3U8.py %%i False %%j %%k
			@rem echo "%%k contains non-numeric characters"	
		)
	)
        ) else ( 
            echo "can't find %%%% j in line:"
            echo. %%i
        )
    ) else echo "can't find %%%% i"
@rem E:\Softs\Python38\python.exe LoadM3U8.py %%i False %%j 2
)

set /p i="输入任意非空字符退出:"
echo "%i%"
if "%i%"=="" goto reload_file