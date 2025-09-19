@echo off
setlocal enabledelayedexpansion

REM Usage: wait_for_http.bat <url> <timeout-seconds>
if "%~2"=="" (
    echo Usage: %~nx0 ^<url^> ^<timeout-seconds^>
    exit /b 2
)
set "url=%~1"
set "limit=%~2"
set "i=1"

:loop
for /f "tokens=*" %%A in ('powershell -Command "try { (Invoke-WebRequest -Uri '%url%' -UseBasicParsing -TimeoutSec 5).StatusCode } catch { '' }"') do set "code=%%A"
if "!code!"=="200" ( echo OK: %url% -> !code! & exit /b 0 )
if "!code!"=="301" ( echo OK: %url% -> !code! & exit /b 0 )
if "!code!"=="302" ( echo OK: %url% -> !code! & exit /b 0 )
echo Waiting for %url% (got !code!) [!i!/%limit%]
set /a i+=1
if !i! gtr %limit% (
    echo ERROR: %url% not healthy in %limit%s
    exit /b 1
)
timeout /t 1 >nul
goto loop
