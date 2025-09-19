@echo off
echo Starting E-Commerce Microservices Platform...

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

REM Start services in separate windows
echo Starting User Service on port 5001...
start "User Service" cmd /k "venv\Scripts\activate.bat && python user_service.py"

timeout /t 3

echo Starting Product Service on port 5002...
start "Product Service" cmd /k "venv\Scripts\activate.bat && python product_service.py"

timeout /t 3

echo Starting Order Service on port 5003...
start "Order Service" cmd /k "venv\Scripts\activate.bat && python order_service.py"

timeout /t 3

echo Starting Payment Service on port 5004...
start "Payment Service" cmd /k "venv\Scripts\activate.bat && python payment_service.py"

timeout /t 3

echo Starting Notification Service on port 5005...
start "Notification Service" cmd /k "venv\Scripts\activate.bat && python notification_service.py"

echo.
echo ================================
echo All services are starting...
echo ================================
echo User Service:         http://localhost:5001  
echo Product Service:      http://localhost:5002
echo Order Service:        http://localhost:5003
echo Payment Service:      http://localhost:5004
echo Notification Service: http://localhost:5005
echo.
echo Frontend Application: http://localhost:5000
echo ================================

pause