@echo off
setlocal enableextensions enabledelayedexpansion

REM Deploy only changed services with minimal disruption
REM Requires: DOCKERHUB_USER to be set (or .env present), docker compose v2

if not exist changed_services.txt (
  echo No changed_services.txt found. Nothing to deploy.
  exit /b 0
)

set /p SERVICES=<changed_services.txt
if /I "%SERVICES%"=="ALL" (
  set "SERVICES=product_service user_service order_service payment_service notification_service frontend"
)

if "%DOCKERHUB_USER%"=="" (
  echo INFO: DOCKERHUB_USER not set. If your compose relies on it, ensure a .env file exists.
)


REM Read deploy info (namespace and exact tag)
if exist deploy_info.txt (
  for /f "tokens=1,2 delims==" %%A in (deploy_info.txt) do set %%A=%%B
)

if not defined NS (
  if defined DOCKERHUB_USER (
    set "NS=%DOCKERHUB_USER%"
  ) else (
    echo WARN: Namespace NS not found; will fall back to compose defaults.
  )
)

set "OVERRIDE=compose.override.deploy.yml"
if defined NS if defined TAG (
  echo Using exact tag %TAG% for deterministic rollout.
  > "%OVERRIDE%" echo services:
  for %%s in (%SERVICES%) do (
    >> "%OVERRIDE%" echo ^  %%s:
    >> "%OVERRIDE%" echo ^    image: %NS%/%%s:%TAG%
  )
)

for %%s in (%SERVICES%) do (
  if defined TAG (
    echo Pulling image %NS%/%%s:%TAG% ...
    docker pull %NS%/%%s:%TAG% || (echo WARN: Pull failed for %%s:%TAG%. Continuing.)
  ) else (
    echo Pulling latest image for %%s...
    docker compose pull %%s || (echo WARN: Pull failed for %%s. Continuing.)
  )
)

if exist "%OVERRIDE%" (
  echo Recreating services with override file %OVERRIDE% ...
  docker compose -f docker-compose.yml -f "%OVERRIDE%" up -d --no-build --force-recreate %SERVICES% || (echo ERROR: Recreate failed & del "%OVERRIDE%" & exit /b 1)
  del "%OVERRIDE%"
  goto :done
)

echo Recreating services with compose defaults ...
docker compose up -d --no-build --force-recreate %SERVICES% || (echo ERROR: Recreate failed & exit /b 1)

:done
echo Deployment complete.
exit /b 0
