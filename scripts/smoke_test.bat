@echo off
setlocal enabledelayedexpansion
REM Minimal smoke test exercising core API flow
REM Assumes services exposed on localhost via docker compose

REM Health checks
call scripts\wait_for_http.bat http://localhost:5000/health 60
call scripts\wait_for_http.bat http://localhost:5001/health 60
call scripts\wait_for_http.bat http://localhost:5002/health 60
call scripts\wait_for_http.bat http://localhost:5003/health 60
call scripts\wait_for_http.bat http://localhost:5005/health 60

REM Seed products
powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:5000/init-data' -Method POST -ContentType 'application/json' } catch {}"

REM Register user
powershell -Command "$resp = Invoke-RestMethod -Uri 'http://localhost:5001/register' -Method POST -ContentType 'application/json' -Body '{"name":"Alice","email":"alice@example.com","password":"Passw0rd!"}'; Write-Output $resp"

REM Login user
powershell -Command "$login = Invoke-RestMethod -Uri 'http://localhost:5001/login' -Method POST -ContentType 'application/json' -Body '{"email":"alice@example.com","password":"Passw0rd!"}'; Write-Output $login"

REM Create order
powershell -Command "$order = Invoke-RestMethod -Uri 'http://localhost:5002/orders' -Method POST -ContentType 'application/json' -Body '{"user_email":"alice@example.com","items":[{"product_id":1,"quantity":1}]}'; Write-Output $order"

REM Extract order_id (simple parsing, not robust)
for /f "tokens=2 delims=:,}" %%A in ('powershell -Command "$order = Invoke-RestMethod -Uri 'http://localhost:5002/orders' -Method POST -ContentType 'application/json' -Body '{\"user_email\":\"alice@example.com\",\"items\":[{\"product_id\":1,\"quantity\":1}]}'; Write-Output $order" ^| findstr /i \"order_id\"') do set "order_id=%%A"
if "!order_id!"=="" (
    echo Could not extract order_id
    exit /b 1
)

REM Process payment
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:5003/payments' -Method POST -ContentType 'application/json' -Body '{\"order_id\":!order_id!,\"amount\":49.99,\"method\":\"card\"}'"

echo Smoke tests completed
