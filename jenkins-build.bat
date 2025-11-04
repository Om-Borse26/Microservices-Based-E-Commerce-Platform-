@echo off
REM ╔════════════════════════════════════════════════════════╗
REM ║  AUTO-DETECT CHANGES & DEPLOY - SINGLE JOB             ║
REM ╚════════════════════════════════════════════════════════╝

setlocal enabledelayedexpansion

set AWS_REGION=us-east-1
set AWS_ACCOUNT_ID=852048987212
set ECS_CLUSTER=shopease-cluster
set CHANGES_FOUND=0

echo ════════════════════════════════════════════════════════
echo   🔍 Detecting Changed Microservices...
echo ════════════════════════════════════════════════════════
echo.

REM Check what changed in last commit
git diff --name-only HEAD~1 HEAD > changed_files.txt

REM Check each microservice
set SERVICES=product-service user-service order-service payment-service notification-service

for %%S in (%SERVICES%) do (
    findstr /i "microservices\\%%S" changed_files.txt >nul
    if !ERRORLEVEL! EQU 0 (
        echo ✅ CHANGED: %%S
        set CHANGES_FOUND=1
        call :BuildAndDeploy %%S
    ) else (
        echo ⏭️  No changes: %%S
    )
)

REM Check frontend
findstr /i "frontend" changed_files.txt >nul
if !ERRORLEVEL! EQU 0 (
    echo ✅ CHANGED: frontend
    set CHANGES_FOUND=1
    call :BuildAndDeployFrontend
) else (
    echo ⏭️  No changes: frontend
)

echo.
if !CHANGES_FOUND! EQU 0 (
    echo ════════════════════════════════════════════════════════
    echo   ⚠️  NO CHANGES DETECTED - SKIPPING BUILD
    echo ════════════════════════════════════════════════════════
    exit /b 0
)

echo ════════════════════════════════════════════════════════
echo   ✅ ALL DEPLOYMENTS COMPLETED SUCCESSFULLY!
echo ════════════════════════════════════════════════════════
exit /b 0

REM ═══════════════════════════════════════════════════════════
REM Function: Build and Deploy Microservice
REM ═══════════════════════════════════════════════════════════
:BuildAndDeploy
set SERVICE_NAME=%1
set ECR_REPO=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%SERVICE_NAME%

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  DEPLOYING: %SERVICE_NAME%
echo ╚════════════════════════════════════════════════════════╝

echo [1/5] Building Docker image...
docker build -t %ECR_REPO%:latest -f microservices\%SERVICE_NAME%\Dockerfile microservices\%SERVICE_NAME%
if !ERRORLEVEL! NEQ 0 (
    echo ❌ BUILD FAILED: %SERVICE_NAME%
    exit /b 1
)
echo ✅ Image built

echo [2/5] Logging into ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo ❌ ECR LOGIN FAILED
    exit /b 1
)
echo ✅ Logged in

echo [3/5] Pushing to ECR...
docker push %ECR_REPO%:latest
if !ERRORLEVEL! NEQ 0 (
    echo ❌ PUSH FAILED: %SERVICE_NAME%
    exit /b 1
)
echo ✅ Image pushed

echo [4/5] Checking if service exists...
aws ecs describe-services --cluster %ECS_CLUSTER% --services %SERVICE_NAME% --region %AWS_REGION% >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Service not found, skipping deployment
    goto :eof
)

echo [5/5] Updating ECS service...
aws ecs update-service --cluster %ECS_CLUSTER% --service %SERVICE_NAME% --force-new-deployment --region %AWS_REGION% >nul
if !ERRORLEVEL! NEQ 0 (
    echo ❌ DEPLOYMENT FAILED: %SERVICE_NAME%
    exit /b 1
)
echo ✅ Deployment triggered

echo.
echo ✅✅✅ %SERVICE_NAME% DEPLOYED SUCCESSFULLY! ✅✅✅
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Build and Deploy Frontend
REM ═══════════════════════════════════════════════════════════
:BuildAndDeployFrontend
set ECR_REPO=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/frontend

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  DEPLOYING: FRONTEND
echo ╚════════════════════════════════════════════════════════╝

echo [1/5] Building Docker image...
docker build -t %ECR_REPO%:latest -f Dockerfile.frontend .
if !ERRORLEVEL! NEQ 0 (
    echo ❌ BUILD FAILED: frontend
    exit /b 1
)
echo ✅ Image built

echo [2/5] Logging into ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo ❌ ECR LOGIN FAILED
    exit /b 1
)
echo ✅ Logged in

echo [3/5] Pushing to ECR...
docker push %ECR_REPO%:latest
if !ERRORLEVEL! NEQ 0 (
    echo ❌ PUSH FAILED: frontend
    exit /b 1
)
echo ✅ Image pushed

echo [4/5] Checking if service exists...
aws ecs describe-services --cluster %ECS_CLUSTER% --services frontend --region %AWS_REGION% >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Service not found, skipping deployment
    goto :eof
)

echo [5/5] Updating ECS service...
aws ecs update-service --cluster %ECS_CLUSTER% --service frontend --force-new-deployment --region %AWS_REGION% >nul
if !ERRORLEVEL! NEQ 0 (
    echo ❌ DEPLOYMENT FAILED: frontend
    exit /b 1
)
echo ✅ Deployment triggered

echo.
echo ✅✅✅ FRONTEND DEPLOYED SUCCESSFULLY! ✅✅✅
echo 🌐 URL: http://shopease-ALB-sKp3hMBLPetR-1497330103.us-east-1.elb.amazonaws.com
goto :eof