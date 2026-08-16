@echo off
REM 运行 database 模块单元测试
REM 用法：双击或在任意目录下执行 tests\database\run_tests.bat

setlocal

REM 切到脚本所在目录（tests\database）
cd /d "%~dp0"

REM 回到项目根目录（上两级）
cd ..\..

REM 临时文件统一放到 tests\.pytest_tmp 下，方便查看；记得在 .gitignore 里忽略
if not exist "tests\.pytest_tmp" mkdir "tests\.pytest_tmp"

python -m pytest tests\database\test_stock_db.py -v --basetemp=tests\.pytest_tmp %*

set EXITCODE=%ERRORLEVEL%
endlocal & exit /b %EXITCODE%
