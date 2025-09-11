@echo off
echo Starting E-Commerce Microservices...

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
echo Starting Product Service on port 5000...
start "Product Service" cmd /k "venv\Scripts\activate.bat && python product_service.py"

timeout /t 3

echo Starting User Service on port 5001...
start "User Service" cmd /k "venv\Scripts\activate.bat && python user_service.py"

timeout /t 3

echo Starting Order Service on port 5002...
start "Order Service" cmd /k "venv\Scripts\activate.bat && python order_service.py"

echo All services are starting...
echo Product Service: http://localhost:5000
echo User Service: http://localhost:5001  
echo Order Service: http://localhost:5002
echo Frontend: http://localhost:5000 (served by Product Service)

pause
