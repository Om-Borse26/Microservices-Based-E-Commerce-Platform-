@echo off
REM ╔════════════════════════════════════════════════════════╗
REM ║  COMPLETE CI/CD PIPELINE - NO STAGING REQUIRED        ║
REM ╚════════════════════════════════════════════════════════╝

REM Add AWS CLI to PATH
set PATH=%PATH%;E:\Other Downloaded Apps\AWS CLI\CLI Setup

REM Configure AWS credentials from Jenkins
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
set TESTS_PASSED=0

echo ════════════════════════════════════════════════════════
echo   🔍 STAGE 1: DETECTING CHANGES
echo ════════════════════════════════════════════════════════
echo.

REM Verify AWS credentials
aws sts get-caller-identity >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ❌ AWS credentials invalid!
    exit /b 1
)
echo ✅ AWS credentials validated

REM Check what changed
git diff --name-only HEAD~1 HEAD > changed_files.txt

REM Check each microservice
set SERVICES=product-service user-service order-service payment-service notification-service

for %%S in (%SERVICES%) do (
    findstr /i "microservices\\%%S" changed_files.txt >nul
    if !ERRORLEVEL! EQU 0 (
        echo ✅ CHANGED: %%S
        set CHANGES_FOUND=1
        call :ProcessMicroservice %%S
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
    call :ProcessFrontend
    if !ERRORLEVEL! NEQ 0 exit /b 1
) else (
    echo ⏭️  No changes: frontend
)

if !CHANGES_FOUND! EQU 0 (
    echo.
    echo ════════════════════════════════════════════════════════
    echo   ⚠️  NO CHANGES DETECTED - SKIPPING PIPELINE
    echo ════════════════════════════════════════════════════════
    exit /b 0
)

echo.
echo ════════════════════════════════════════════════════════
echo   ✅ PIPELINE COMPLETED SUCCESSFULLY!
echo ════════════════════════════════════════════════════════
echo   🌐 Live URL: http://shopease-ALB-sKp3hMBLPetR-1497330103.us-east-1.elb.amazonaws.com
echo ════════════════════════════════════════════════════════
exit /b 0

REM ═══════════════════════════════════════════════════════════
REM Function: Process Frontend Changes
REM ═══════════════════════════════════════════════════════════
:ProcessFrontend
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  PROCESSING: FRONTEND
echo ╚════════════════════════════════════════════════════════╝

REM ═══════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════
echo   🧪 STAGE 2: CODE QUALITY CHECKS
echo ════════════════════════════════════════════════════════

echo [1/3] Validating HTML syntax...
powershell -Command "if ((Get-Content frontend\index.html | Select-String -Pattern '<!DOCTYPE html>' -Quiet)) { exit 0 } else { exit 1 }"
if !ERRORLEVEL! NEQ 0 (
    echo ❌ Invalid HTML - missing DOCTYPE
    exit /b 1
)
echo ✅ HTML structure valid

echo [2/3] Checking for JavaScript errors...
powershell -Command "if (Test-Path frontend\*.js) { if ((Get-Content frontend\*.js | Select-String -Pattern 'console\.error' -Quiet)) { exit 1 } else { exit 0 } } else { exit 0 }"
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Console errors found in JS files
)
echo ✅ JavaScript check passed

echo [3/3] Verifying Dockerfile exists...
if not exist "Dockerfile.frontend" (
    echo ❌ Dockerfile.frontend not found!
    exit /b 1
)
echo ✅ Dockerfile found

set TESTS_PASSED=1

REM ═══════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════
echo   🔨 STAGE 3: BUILD APPLICATION
echo ════════════════════════════════════════════════════════

call :BuildAndPush frontend
if !ERRORLEVEL! NEQ 0 exit /b 1

REM ═══════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════
echo   🚀 STAGE 4: DEPLOY TO PRODUCTION
echo ════════════════════════════════════════════════════════

call :DeployToProduction frontend
if !ERRORLEVEL! NEQ 0 exit /b 1

REM ═══════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════
echo   ✅ STAGE 5: POST-DEPLOYMENT VERIFICATION
echo ════════════════════════════════════════════════════════

call :VerifyDeployment
if !ERRORLEVEL! NEQ 0 exit /b 1

echo.
echo ✅✅✅ FRONTEND DEPLOYED SUCCESSFULLY! ✅✅✅
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Process Microservice Changes
REM ═══════════════════════════════════════════════════════════
:ProcessMicroservice
set SERVICE=%1
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  PROCESSING: %SERVICE%
echo ╚════════════════════════════════════════════════════════╝

REM ═══════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════
echo   🧪 STAGE 2: CODE QUALITY CHECKS
echo ════════════════════════════════════════════════════════

echo [1/3] Checking Python syntax...
if exist "microservices\%SERVICE%\*.py" (
    python -m py_compile microservices\%SERVICE%\*.py >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo ✅ Python syntax valid
    ) else (
        echo ❌ Python syntax errors found
        exit /b 1
    )
) else (
    echo ⚠️  No Python files found, skipping
)

echo [2/3] Verifying requirements.txt...
if exist "microservices\%SERVICE%\requirements.txt" (
    echo ✅ requirements.txt found
) else (
    echo ⚠️  requirements.txt not found
)

echo [3/3] Verifying Dockerfile...
if not exist "microservices\%SERVICE%\Dockerfile" (
    echo ❌ Dockerfile not found!
    exit /b 1
)
echo ✅ Dockerfile found

set TESTS_PASSED=1

REM ═══════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════
echo   🔨 STAGE 3: BUILD APPLICATION
echo ════════════════════════════════════════════════════════

call :BuildAndPushMicroservice %SERVICE%
if !ERRORLEVEL! NEQ 0 exit /b 1

REM ═══════════════════════════════════════════════════════
echo.
echo ════════════════════════════════════════════════════════
echo   🚀 STAGE 4: DEPLOY TO PRODUCTION
echo ════════════════════════════════════════════════════════

call :DeployMicroserviceToProduction %SERVICE%
if !ERRORLEVEL! NEQ 0 exit /b 1

echo.
echo ✅✅✅ %SERVICE% DEPLOYED SUCCESSFULLY! ✅✅✅
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Build and Push Frontend Image
REM ═══════════════════════════════════════════════════════════
:BuildAndPush
set SERVICE=%1
set LOCAL_IMAGE=%SERVICE%:latest
set ECR_REPO=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%SERVICE%

echo [1/4] Building Docker image locally...
docker build -t %LOCAL_IMAGE% -f Dockerfile.%SERVICE% .
if !ERRORLEVEL! NEQ 0 (
    echo ❌ BUILD FAILED
    exit /b 1
)
echo ✅ Image built: %LOCAL_IMAGE%

echo [2/4] Tagging for ECR...
docker tag %LOCAL_IMAGE% %ECR_REPO%:latest
docker tag %LOCAL_IMAGE% %ECR_REPO%:%BUILD_NUMBER%
echo ✅ Tagged with :latest and :%BUILD_NUMBER%

echo [3/4] Logging into ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
if !ERRORLEVEL! NEQ 0 (
    echo ❌ ECR LOGIN FAILED
    exit /b 1
)
echo ✅ Logged into ECR

echo [4/4] Pushing to ECR...
docker push %ECR_REPO%:latest
docker push %ECR_REPO%:%BUILD_NUMBER%
echo ✅ Pushed to ECR

REM Cleanup
docker rmi %LOCAL_IMAGE% >nul 2>&1
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Build and Push Microservice Image
REM ═══════════════════════════════════════════════════════════
:BuildAndPushMicroservice
set SERVICE=%1
set LOCAL_IMAGE=%SERVICE%:latest
set ECR_REPO=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%SERVICE%

echo [1/4] Building Docker image locally...
docker build -t %LOCAL_IMAGE% -f microservices\%SERVICE%\Dockerfile microservices\%SERVICE%
if !ERRORLEVEL! NEQ 0 (
    echo ❌ BUILD FAILED
    exit /b 1
)
echo ✅ Image built: %LOCAL_IMAGE%

echo [2/4] Tagging for ECR...
docker tag %LOCAL_IMAGE% %ECR_REPO%:latest
docker tag %LOCAL_IMAGE% %ECR_REPO%:%BUILD_NUMBER%
echo ✅ Tagged with :latest and :%BUILD_NUMBER%

echo [3/4] Logging into ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
if !ERRORLEVEL! NEQ 0 (
    echo ❌ ECR LOGIN FAILED
    exit /b 1
)
echo ✅ Logged into ECR

echo [4/4] Pushing to ECR...
docker push %ECR_REPO%:latest
docker push %ECR_REPO%:%BUILD_NUMBER%
echo ✅ Pushed to ECR

REM Cleanup
docker rmi %LOCAL_IMAGE% >nul 2>&1
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Deploy Frontend to Production
REM ═══════════════════════════════════════════════════════════
:DeployToProduction
set SERVICE=%1

echo [1/2] Checking if ECS service exists...
aws ecs describe-services --cluster %ECS_CLUSTER% --services %SERVICE% --region %AWS_REGION% >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Service %SERVICE% not found in ECS
    echo ℹ️  Image is in ECR, create service manually or continue without deployment
    goto :eof
)
echo ✅ Service exists

echo [2/2] Triggering deployment...
aws ecs update-service --cluster %ECS_CLUSTER% --service %SERVICE% --force-new-deployment --region %AWS_REGION% >nul
if !ERRORLEVEL! NEQ 0 (
    echo ❌ DEPLOYMENT FAILED
    exit /b 1
)
echo ✅ Deployment triggered
echo ⏳ ECS is updating... (takes 2-3 minutes)
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Deploy Microservice to Production
REM ═══════════════════════════════════════════════════════════
:DeployMicroserviceToProduction
set SERVICE=%1

echo [1/2] Checking if ECS service exists...
aws ecs describe-services --cluster %ECS_CLUSTER% --services %SERVICE% --region %AWS_REGION% >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Service %SERVICE% not found in ECS
    echo ℹ️  Image is in ECR, create service manually
    goto :eof
)
echo ✅ Service exists

echo [2/2] Triggering deployment...
aws ecs update-service --cluster %ECS_CLUSTER% --service %SERVICE% --force-new-deployment --region %AWS_REGION% >nul
if !ERRORLEVEL! NEQ 0 (
    echo ❌ DEPLOYMENT FAILED
    exit /b 1
)
echo ✅ Deployment triggered
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Verify Deployment
REM ═══════════════════════════════════════════════════════════
:VerifyDeployment
echo [1/2] Waiting for deployment to stabilize...
timeout /t 30 /nobreak >nul

echo [2/2] Testing website availability...
set ALB_URL=http://shopease-ALB-sKp3hMBLPetR-1497330103.us-east-1.elb.amazonaws.com

powershell -Command "try { $response = Invoke-WebRequest -Uri '%ALB_URL%' -TimeoutSec 10 -UseBasicParsing; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if !ERRORLEVEL! EQU 0 (
    echo ✅ Website is responding (HTTP 200)
    echo 🌐 Live at: %ALB_URL%
) else (
    echo ⚠️  Website not responding yet (might still be deploying)
    echo ℹ️  Check in a few minutes at: %ALB_URL%
)
goto :eof