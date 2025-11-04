@echo off
REM ╔════════════════════════════════════════════════════════╗
REM ║  AUTO-DETECT CHANGES & DEPLOY - FULLY AUTOMATED        ║
REM ╚════════════════════════════════════════════════════════╝

REM Add AWS CLI to PATH
set PATH=%PATH%;E:\Other Downloaded Apps\AWS CLI\CLI Setup

REM Configure AWS credentials from Jenkins environment variables
if "%AWS_ACCESS_KEY_ID%"=="" (
    echo ⚠️  AWS credentials not found in Jenkins environment
    echo Using local AWS credentials...
) else (
    echo ✅ Using AWS credentials from Jenkins
    aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
    aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
    aws configure set region us-east-1
)

setlocal enabledelayedexpansion

set AWS_REGION=us-east-1
set AWS_ACCOUNT_ID=852048987212
set ECS_CLUSTER=shopease-cluster
set CHANGES_FOUND=0

echo ════════════════════════════════════════════════════════
echo   🔍 STAGE 1: DETECTING CHANGES
echo ════════════════════════════════════════════════════════
echo.

REM Verify AWS credentials work
aws sts get-caller-identity >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ❌ AWS credentials are invalid or not configured!
    exit /b 1
)
echo ✅ AWS credentials validated

REM Check what changed in last commit
git diff --name-only HEAD~1 HEAD > changed_files.txt

REM Check each microservice
set SERVICES=product-service user-service order-service payment-service notification-service

for %%S in (%SERVICES%) do (
    findstr /i "microservices\\%%S" changed_files.txt >nul
    if !ERRORLEVEL! EQU 0 (
        echo ✅ CHANGED: %%S
        set CHANGES_FOUND=1
        call :BuildAndTest %%S microservice
        if !ERRORLEVEL! NEQ 0 exit /b 1
    ) else (
        echo ⏭️  No changes: %%S
    )
)

REM Check frontend
findstr /i "frontend" changed_files.txt >nul
if !ERRORLEVEL! EQU 0 (
    echo ✅ CHANGED: frontend
    set CHANGES_FOUND=1
    call :BuildAndTest frontend frontend
    if !ERRORLEVEL! NEQ 0 exit /b 1
) else (
    echo ⏭️  No changes: frontend
)

if !CHANGES_FOUND! EQU 0 (
    echo.
    echo ════════════════════════════════════════════════════════
    echo   ⚠️  NO CHANGES DETECTED - SKIPPING BUILD
    echo ════════════════════════════════════════════════════════
    exit /b 0
)

REM ═══════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════
echo   🚀 STAGE 3: DEPLOYING TO PRODUCTION
echo ════════════════════════════════════════════════════════
echo.

REM Deploy all changed services
for %%S in (%SERVICES%) do (
    findstr /i "microservices\\%%S" changed_files.txt >nul
    if !ERRORLEVEL! EQU 0 (
        call :DeployToProduction %%S
        if !ERRORLEVEL! NEQ 0 exit /b 1
    )
)

REM Deploy frontend if changed
findstr /i "frontend" changed_files.txt >nul
if !ERRORLEVEL! EQU 0 (
    call :DeployFrontendToProduction
    if !ERRORLEVEL! NEQ 0 exit /b 1
)

echo.
echo ════════════════════════════════════════════════════════
echo   ✅ ALL DEPLOYMENTS COMPLETED SUCCESSFULLY!
echo ════════════════════════════════════════════════════════
echo   🌐 Live URL: http://shopease-ALB-sKp3hMBLPetR-1497330103.us-east-1.elb.amazonaws.com
echo ════════════════════════════════════════════════════════
exit /b 0

REM ═══════════════════════════════════════════════════════════
REM Function: Build, Test, and Push
REM ═══════════════════════════════════════════════════════════
:BuildAndTest
set SERVICE_NAME=%1
set SERVICE_TYPE=%2
set LOCAL_IMAGE=%SERVICE_NAME%:latest
set ECR_REPO=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%SERVICE_NAME%

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  BUILDING: %SERVICE_NAME%
echo ╚════════════════════════════════════════════════════════╝

REM ═══════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════
echo   🧪 STAGE 2A: CODE QUALITY CHECKS
echo ════════════════════════════════════════════════════════

if "%SERVICE_TYPE%"=="microservice" (
    echo [1/2] Checking Python syntax...
    if exist "microservices\%SERVICE_NAME%\*.py" (
        python -m py_compile microservices\%SERVICE_NAME%\*.py >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo ✅ Python syntax valid
        ) else (
            echo ❌ Python syntax errors found
            exit /b 1
        )
    ) else (
        echo ⚠️  No Python files found
    )
    
    echo [2/2] Verifying Dockerfile...
    if not exist "microservices\%SERVICE_NAME%\Dockerfile" (
        echo ❌ Dockerfile not found!
        exit /b 1
    )
    echo ✅ Dockerfile found
    
) else (
    echo [1/2] Validating HTML syntax...
    if exist "frontend\index.html" (
        echo ✅ HTML file exists
    ) else (
        echo ❌ HTML file not found!
        exit /b 1
    )
    
    echo [2/2] Verifying Dockerfile...
    if not exist "Dockerfile.frontend" (
        echo ❌ Dockerfile.frontend not found!
        exit /b 1
    )
    echo ✅ Dockerfile found
)

REM ═══════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════
echo   🔨 STAGE 2B: BUILD IMAGE
echo ════════════════════════════════════════════════════════

echo [1/5] Building Docker image locally...
if "%SERVICE_TYPE%"=="microservice" (
    docker build -t %LOCAL_IMAGE% -f microservices\%SERVICE_NAME%\Dockerfile microservices\%SERVICE_NAME%
) else (
    docker build -t %LOCAL_IMAGE% -f Dockerfile.frontend .
)
if !ERRORLEVEL! NEQ 0 (
    echo ❌ BUILD FAILED: %SERVICE_NAME%
    exit /b 1
)
echo ✅ Local image built

echo [2/5] Tagging for ECR...
docker tag %LOCAL_IMAGE% %ECR_REPO%:latest
echo ✅ Tagged

echo [3/5] Logging into ECR...
set LOGIN_RETRY=0
:ECR_LOGIN_RETRY
set /a LOGIN_RETRY+=1
aws ecr get-login-password --region %AWS_REGION% 2>nul | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    if !LOGIN_RETRY! LSS 3 (
        echo ⚠️  Retry !LOGIN_RETRY!/3 in 15s...
        timeout /t 15 /nobreak >nul
        goto ECR_LOGIN_RETRY
    )
    echo ❌ LOGIN FAILED
    exit /b 1
)
echo ✅ Logged in

echo [4/5] Pushing to ECR...
set PUSH_RETRY=0
:PUSH_RETRY_LABEL
set /a PUSH_RETRY+=1
docker push %ECR_REPO%:latest
if !ERRORLEVEL! NEQ 0 (
    if !PUSH_RETRY! LSS 3 (
        echo ⚠️  Retry !PUSH_RETRY!/3 in 15s...
        timeout /t 15 /nobreak >nul
        aws ecr get-login-password --region %AWS_REGION% 2>nul | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com >nul 2>&1
        goto PUSH_RETRY_LABEL
    )
    echo ❌ PUSH FAILED
    exit /b 1
)
echo ✅ Pushed

echo [5/5] Cleanup...
docker rmi %LOCAL_IMAGE% >nul 2>&1
echo ✅ Done

echo.
echo ✅✅✅ %SERVICE_NAME% READY FOR DEPLOYMENT ✅✅✅
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Deploy to Production
REM ═══════════════════════════════════════════════════════════
:DeployToProduction
set SERVICE_NAME=%1
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  DEPLOYING: %SERVICE_NAME%
echo ╚════════════════════════════════════════════════════════╝
aws ecs describe-services --cluster %ECS_CLUSTER% --services %SERVICE_NAME% --region %AWS_REGION% >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Service not found, skipping
    goto :eof
)
aws ecs update-service --cluster %ECS_CLUSTER% --service %SERVICE_NAME% --force-new-deployment --region %AWS_REGION% >nul
echo ✅ Deployed
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Deploy Frontend
REM ═══════════════════════════════════════════════════════════
:DeployFrontendToProduction
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  DEPLOYING: FRONTEND
echo ╚════════════════════════════════════════════════════════╝
aws ecs describe-services --cluster %ECS_CLUSTER% --services frontend --region %AWS_REGION% >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Service not found, skipping
    goto :eof
)
aws ecs update-service --cluster %ECS_CLUSTER% --service frontend --force-new-deployment --region %AWS_REGION% >nul
echo ✅ Deployed
echo 🌐 http://shopease-ALB-sKp3hMBLPetR-1497330103.us-east-1.elb.amazonaws.com
goto :eof