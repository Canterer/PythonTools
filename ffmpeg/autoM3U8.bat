@echo off
set /p dir="�����뵥���ļ����ļ���·����"
if "%dir%"=="" echo %~dp0
set /p factor="��������������(����Ϊ1Mb/s)��"
@REM for /r %dir% %%a in (*.mp4) do echo %%a
for /r %dir% %%a in (*) do python AutoM3U8.py %%a "--rateScale" %factor%
pause

