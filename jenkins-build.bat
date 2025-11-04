@echo off
REM ╔════════════════════════════════════════════════════════╗
REM ║  AUTO-DETECT CHANGES & DEPLOY - BUILD LOCALLY          ║
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
echo   🔍 Detecting Changed Microservices...
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
        call :BuildAndDeploy %%S
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
    call :BuildAndDeployFrontend
    if !ERRORLEVEL! NEQ 0 exit /b 1
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
set LOCAL_IMAGE=%SERVICE_NAME%:latest
set ECR_REPO=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%SERVICE_NAME%

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  DEPLOYING: %SERVICE_NAME%
echo ╚════════════════════════════════════════════════════════╝

REM Build locally first
echo [1/6] Building Docker image locally...
docker build -t %LOCAL_IMAGE% -f microservices\%SERVICE_NAME%\Dockerfile microservices\%SERVICE_NAME%
if !ERRORLEVEL! NEQ 0 (
    echo ❌ BUILD FAILED: %SERVICE_NAME%
    exit /b 1
)
echo ✅ Local image built: %LOCAL_IMAGE%

REM Tag for ECR
echo [2/6] Tagging image for ECR...
docker tag %LOCAL_IMAGE% %ECR_REPO%:latest
if !ERRORLEVEL! NEQ 0 (
    echo ❌ TAG FAILED: %SERVICE_NAME%
    exit /b 1
)
echo ✅ Image tagged: %ECR_REPO%:latest

REM Login to ECR
echo [3/6] Logging into ECR...
for /f "tokens=*" %%i in ('aws ecr get-login-password --region %AWS_REGION%') do set ECR_PASSWORD=%%i
echo !ECR_PASSWORD! | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
if !ERRORLEVEL! NEQ 0 (
    echo ❌ ECR LOGIN FAILED
    exit /b 1
)
echo ✅ Logged into ECR

REM Push to ECR
echo [4/6] Pushing to ECR...
docker push %ECR_REPO%:latest
if !ERRORLEVEL! NEQ 0 (
    echo ❌ PUSH FAILED: %SERVICE_NAME%
    exit /b 1
)
echo ✅ Image pushed to ECR

REM Check if service exists
echo [5/6] Checking if ECS service exists...
aws ecs describe-services --cluster %ECS_CLUSTER% --services %SERVICE_NAME% --region %AWS_REGION% >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Service %SERVICE_NAME% not found in ECS, skipping deployment
    echo ℹ️  Image is in ECR, you can create the service manually
    goto :eof
)

REM Update ECS service
echo [6/6] Updating ECS service...
aws ecs update-service --cluster %ECS_CLUSTER% --service %SERVICE_NAME% --force-new-deployment --region %AWS_REGION% >nul
if !ERRORLEVEL! NEQ 0 (
    echo ❌ DEPLOYMENT FAILED: %SERVICE_NAME%
    exit /b 1
)
echo ✅ ECS deployment triggered

REM Cleanup local image to save space
docker rmi %LOCAL_IMAGE% >nul 2>&1

echo.
echo ✅✅✅ %SERVICE_NAME% DEPLOYED SUCCESSFULLY! ✅✅✅
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Build and Deploy Frontend
REM ═══════════════════════════════════════════════════════════
:BuildAndDeployFrontend
set LOCAL_IMAGE=frontend:latest
set ECR_REPO=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/frontend

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  DEPLOYING: FRONTEND
echo ╚════════════════════════════════════════════════════════╝

REM Build locally first
echo [1/6] Building Docker image locally...
docker build -t %LOCAL_IMAGE% -f Dockerfile.frontend .
if !ERRORLEVEL! NEQ 0 (
    echo ❌ BUILD FAILED: frontend
    exit /b 1
)
echo ✅ Local image built: %LOCAL_IMAGE%

REM Tag for ECR
echo [2/6] Tagging image for ECR...
docker tag %LOCAL_IMAGE% %ECR_REPO%:latest
if !ERRORLEVEL! NEQ 0 (
    echo ❌ TAG FAILED: frontend
    exit /b 1
)
echo ✅ Image tagged: %ECR_REPO%:latest

REM Login to ECR
echo [3/6] Logging into ECR...
for /f "tokens=*" %%i in ('aws ecr get-login-password --region %AWS_REGION%') do set ECR_PASSWORD=%%i
echo !ECR_PASSWORD! | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
if !ERRORLEVEL! NEQ 0 (
    echo ❌ ECR LOGIN FAILED
    exit /b 1
)
echo ✅ Logged into ECR

REM Push to ECR
echo [4/6] Pushing to ECR...
docker push %ECR_REPO%:latest
if !ERRORLEVEL! NEQ 0 (
    echo ❌ PUSH FAILED: frontend
    exit /b 1
)
echo ✅ Image pushed to ECR

REM Check if service exists
echo [5/6] Checking if ECS service exists...
aws ecs describe-services --cluster %ECS_CLUSTER% --services frontend --region %AWS_REGION% >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Frontend service not found in ECS, skipping deployment
    echo ℹ️  Image is in ECR, you can create the service manually
    goto :eof
)

REM Update ECS service
echo [6/6] Updating ECS service...
aws ecs update-service --cluster %ECS_CLUSTER% --service frontend --force-new-deployment --region %AWS_REGION% >nul
if !ERRORLEVEL! NEQ 0 (
    echo ❌ DEPLOYMENT FAILED: frontend
    exit /b 1
)
echo ✅ ECS deployment triggered

REM Cleanup local image to save space
docker rmi %LOCAL_IMAGE% >nul 2>&1

echo.
echo ✅✅✅ FRONTEND DEPLOYED SUCCESSFULLY! ✅✅✅
echo 🌐 URL: http://shopease-ALB-sKp3hMBLPetR-1497330103.us-east-1.elb.amazonaws.com
goto :eof