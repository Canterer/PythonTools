@echo off
set /p dir="请输入单个文件或文件夹路径："
if "%dir%"=="" echo %~dp0
set /p factor="请输入码率因子(乘数为1Mb/s)："
@REM for /r %dir% %%a in (*.mp4) do echo %%a
for /r %dir% %%a in (*) do python AutoM3U8.py %%a "--rateScale" %factor%
pause

