@echo off
set file=Input.txt
@rem set /p file=请输入文件名：
echo %file%

:reload_file

for /f "tokens=1-4 " %%i  in (%file%) do (
echo %%i
echo %%j
echo %%k
echo %%l
python LoadM3U8.py %%i %%j %%k %%l
)

set /p i="输入任意非空字符退出:"
echo "%i%"
if "%i%"=="" goto reload_file
