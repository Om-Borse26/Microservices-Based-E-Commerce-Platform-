@echo off
echo Starting E-Commerce Microservices Platform (local, non-Docker)...

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start services in separate windows (ensure no Docker containers are using these ports)
echo Starting Product Service on port 5000...
start "Product Service" cmd /k "call venv\Scripts\activate.bat ^&^& set PORT=5000 ^&^& python product_service.py"

timeout /t 3 >NUL

echo Starting User Service on port 5001...
start "User Service" cmd /k "call venv\Scripts\activate.bat ^&^& set PORT=5001 ^&^& python user_service.py"

timeout /t 3 >NUL

echo Starting Order Service on port 5002...
start "Order Service" cmd /k "call venv\Scripts\activate.bat ^&^& set PORT=5002 ^&^& python order_service.py"

timeout /t 3 >NUL

echo Starting Payment Service on port 5003...
start "Payment Service" cmd /k "call venv\Scripts\activate.bat ^&^& set PORT=5003 ^&^& python payment_service.py"

timeout /t 3 >NUL

echo Starting Notification Service on port 5005...
start "Notification Service" cmd /k "call venv\Scripts\activate.bat ^&^& set PORT=5005 ^&^& python notification_service.py"

echo.
echo ======================================
echo All services are starting (local mode)...
echo ======================================
echo Product Service:      http://localhost:5000
echo User Service:         http://localhost:5001
echo Order Service:        http://localhost:5002
echo Payment Service:      http://localhost:5003
echo Notification Service: http://localhost:5005
echo Frontend (Compose):   http://localhost:8081
echo.
echo Tip: Stop Docker Compose or change ports to avoid conflicts.

pause
