@echo off
REM ╔════════════════════════════════════════════════════════╗
REM ║  COMPLETE CI/CD PIPELINE WITH TESTING                  ║
REM ╚════════════════════════════════════════════════════════╝

REM Add AWS CLI to PATH
set PATH=%PATH%;E:\Other Downloaded Apps\AWS CLI\CLI Setup

REM Configure AWS credentials
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
set ECS_CLUSTER_STAGING=shopease-staging-cluster
set ECS_CLUSTER_PRODUCTION=shopease-cluster
set CHANGES_FOUND=0
set TESTS_PASSED=0

echo ════════════════════════════════════════════════════════
echo   🔍 STAGE 1: DETECTING CHANGES
echo ════════════════════════════════════════════════════════
echo.

REM Check what changed
git diff --name-only HEAD~1 HEAD > changed_files.txt

REM Check frontend
findstr /i "frontend" changed_files.txt >nul
if !ERRORLEVEL! EQU 0 (
    echo ✅ CHANGED: frontend
    set CHANGES_FOUND=1
    
    REM ═══════════════════════════════════════════════════════
    echo.
    echo ════════════════════════════════════════════════════════
    echo   🧪 STAGE 2: LINTING ^& UNIT TESTS
    echo ════════════════════════════════════════════════════════
    
    REM Check if package.json exists (for Node.js projects)
    if exist "frontend\package.json" (
        echo [1/2] Running ESLint...
        cd frontend
        call npm install --silent >nul 2>&1
        call npm run lint
        if !ERRORLEVEL! NEQ 0 (
            echo ❌ LINTING FAILED!
            exit /b 1
        )
        echo ✅ Linting passed
        
        echo [2/2] Running unit tests...
        call npm test
        if !ERRORLEVEL! NEQ 0 (
            echo ❌ TESTS FAILED!
            exit /b 1
        )
        echo ✅ Tests passed
        cd ..
    ) else (
        echo ⚠️  No package.json found, skipping tests
    )
    
    set TESTS_PASSED=1
    
    REM ═══════════════════════════════════════════════════════
    echo.
    echo ════════════════════════════════════════════════════════
    echo   🔨 STAGE 3: BUILD IMAGE
    echo ════════════════════════════════════════════════════════
    
    call :BuildImage frontend
    if !ERRORLEVEL! NEQ 0 exit /b 1
    
    REM ═══════════════════════════════════════════════════════
    echo.
    echo ════════════════════════════════════════════════════════
    echo   🚀 STAGE 4: DEPLOY TO STAGING
    echo ════════════════════════════════════════════════════════
    
    call :DeployToStaging frontend
    if !ERRORLEVEL! NEQ 0 exit /b 1
    
    REM ═══════════════════════════════════════════════════════
    echo.
    echo ════════════════════════════════════════════════════════
    echo   🧪 STAGE 5: STAGING TESTS
    echo ════════════════════════════════════════════════════════
    
    call :TestStaging frontend
    if !ERRORLEVEL! NEQ 0 exit /b 1
    
    REM ═══════════════════════════════════════════════════════
    echo.
    echo ════════════════════════════════════════════════════════
    echo   ✋ STAGE 6: MANUAL APPROVAL
    echo ════════════════════════════════════════════════════════
    
    echo ⚠️  Deploy to PRODUCTION requires approval!
    echo Press 'Y' to deploy to production, or 'N' to cancel:
    choice /c YN /n /m "Deploy to production? (Y/N): "
    if !ERRORLEVEL! EQU 2 (
        echo ❌ Deployment cancelled by user
        exit /b 0
    )
    
    REM ═══════════════════════════════════════════════════════
    echo.
    echo ════════════════════════════════════════════════════════
    echo   🌟 STAGE 7: DEPLOY TO PRODUCTION
    echo ════════════════════════════════════════════════════════
    
    call :DeployToProduction frontend
    if !ERRORLEVEL! NEQ 0 exit /b 1
    
) else (
    echo ⏭️  No changes detected
)

if !CHANGES_FOUND! EQU 0 (
    echo ════════════════════════════════════════════════════════
    echo   ⚠️  NO CHANGES - SKIPPING PIPELINE
    echo ════════════════════════════════════════════════════════
    exit /b 0
)

echo.
echo ════════════════════════════════════════════════════════
echo   ✅ PIPELINE COMPLETED SUCCESSFULLY!
echo ════════════════════════════════════════════════════════
exit /b 0

REM ═══════════════════════════════════════════════════════════
REM Function: Build Docker Image
REM ═══════════════════════════════════════════════════════════
:BuildImage
set SERVICE=%1
set LOCAL_IMAGE=%SERVICE%:latest
set ECR_REPO=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%SERVICE%

echo [1/3] Building Docker image...
docker build -t %LOCAL_IMAGE% -f Dockerfile.%SERVICE% .
if !ERRORLEVEL! NEQ 0 (
    echo ❌ BUILD FAILED
    exit /b 1
)
echo ✅ Image built

echo [2/3] Tagging for ECR...
docker tag %LOCAL_IMAGE% %ECR_REPO%:latest
docker tag %LOCAL_IMAGE% %ECR_REPO%:staging
echo ✅ Tagged

echo [3/3] Pushing to ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
docker push %ECR_REPO%:staging
docker push %ECR_REPO%:latest
echo ✅ Pushed to ECR
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Deploy to Staging
REM ═══════════════════════════════════════════════════════════
:DeployToStaging
set SERVICE=%1
echo Deploying %SERVICE% to STAGING...

aws ecs describe-services --cluster %ECS_CLUSTER_STAGING% --services %SERVICE%-staging --region %AWS_REGION% >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ⚠️  Staging service doesn't exist - create it first!
    exit /b 1
)

aws ecs update-service --cluster %ECS_CLUSTER_STAGING% --service %SERVICE%-staging --force-new-deployment --region %AWS_REGION% >nul
echo ✅ Deployed to staging
echo ⏳ Waiting 60 seconds for staging to stabilize...
timeout /t 60 /nobreak >nul
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Test Staging Environment
REM ═══════════════════════════════════════════════════════════
:TestStaging
set SERVICE=%1
echo Testing staging environment...

REM Get staging URL (you'll need to set this)
set STAGING_URL=http://shopease-staging-ALB-xxxx.us-east-1.elb.amazonaws.com

echo Testing HTTP response...
curl -s -o nul -w "%%{http_code}" %STAGING_URL% > staging_response.txt
set /p HTTP_CODE=<staging_response.txt

if "%HTTP_CODE%"=="200" (
    echo ✅ Staging tests passed (HTTP 200)
) else (
    echo ❌ Staging tests failed (HTTP %HTTP_CODE%)
    exit /b 1
)
goto :eof

REM ═══════════════════════════════════════════════════════════
REM Function: Deploy to Production
REM ═══════════════════════════════════════════════════════════
:DeployToProduction
set SERVICE=%1
echo Deploying %SERVICE% to PRODUCTION...

aws ecs update-service --cluster %ECS_CLUSTER_PRODUCTION% --service %SERVICE% --force-new-deployment --region %AWS_REGION% >nul
echo ✅ Deployed to PRODUCTION
echo 🌐 Live at: http://shopease-ALB-sKp3hMBLPetR-1497330103.us-east-1.elb.amazonaws.com
goto :eof