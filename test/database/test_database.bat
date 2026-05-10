@echo off
REM 运行 database 模块单元测试
REM 用法：双击或在任意目录下执行 test\database\test_database.bat

setlocal

REM 切到脚本所在目录（test\database）
cd /d "%~dp0"

REM 回到项目根目录（上两级）
cd ..\..

REM 临时文件统一放到 test\.pytest_tmp 下，方便查看；记得在 .gitignore 里忽略
if not exist "test\.pytest_tmp" mkdir "test\.pytest_tmp"

python -m pytest test\database\test_database.py -v --basetemp=test\.pytest_tmp %*

set EXITCODE=%ERRORLEVEL%
endlocal & exit /b %EXITCODE%
