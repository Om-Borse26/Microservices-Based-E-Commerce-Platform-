@echo off
setlocal enableextensions enabledelayedexpansion

REM Jenkins Freestyle CI script for Windows agents
REM Requires: Git, Docker Desktop/CLI, docker-compose v2
REM Inputs via Jenkins:
REM   - DOCKERHUB_USER (String parameter) e.g. your Docker Hub namespace
REM   - Credentials Binding for dockerhub-credentials -> DOCKERHUB_USERNAME, DOCKERHUB_TOKEN

if "%DOCKERHUB_USER%"=="" (
  if "%DOCKERHUB_USERNAME%"=="" (
    echo ERROR: Neither DOCKERHUB_USER nor DOCKERHUB_USERNAME is set. Configure a job parameter DOCKERHUB_USER or bind credentials.
    exit /b 1
  ) else (
    set "NS=%DOCKERHUB_USERNAME%"
  )
) else (
  set "NS=%DOCKERHUB_USER%"
)
echo Using Docker Hub namespace: %NS%

REM Ensure compose uses the same namespace for image names
set "DOCKERHUB_USER=%NS%"

echo Validating docker-compose.yml ...
docker compose config -q || exit /b 1

REM Determine base commit (previous commit if possible)
set "BASE="
for /f "usebackq delims=" %%a in (`git rev-parse --verify HEAD~1 2^>NUL`) do set BASE=%%a
if defined BASE (
  echo Base commit: %BASE%
  git diff --name-only %BASE% HEAD > files.txt || exit /b 1
) else (
  echo No previous commit found; will consider all tracked files.
  git ls-files > files.txt || exit /b 1
)

REM Map changed files to services
set add_all=
set add_product=
set add_user=
set add_order=
set add_payment=
set add_notification=
set add_frontend=

for /f "usebackq delims=" %%f in (files.txt) do (
  set "file=%%f"
  if /I "!file!"=="docker-compose.yml" set add_all=1
  if /I "!file:~0,14!"=="requirements.txt" set add_all=1

  if /I "!file:~0,18!"=="Dockerfile.product" set add_product=1
  if /I "!file!"=="product_service.py" set add_product=1

  if /I "!file:~0,15!"=="Dockerfile.user" set add_user=1
  if /I "!file!"=="user_service.py" set add_user=1

  if /I "!file:~0,16!"=="Dockerfile.order" set add_order=1
  if /I "!file!"=="order_service.py" set add_order=1

  if /I "!file:~0,18!"=="Dockerfile.payment" set add_payment=1
  if /I "!file!"=="payment_service.py" set add_payment=1

  if /I "!file:~0,23!"=="Dockerfile.notification" set add_notification=1
  if /I "!file!"=="notification_service.py" set add_notification=1

  if /I "!file:~0,19!"=="Dockerfile.frontend" set add_frontend=1
  if /I "!file:~0,9!"=="frontend/" set add_frontend=1
)

set "SERVICES="
if defined add_all (
  set "SERVICES=product_service user_service order_service payment_service notification_service frontend"
) else (
  if defined add_product set "SERVICES=!SERVICES! product_service"
  if defined add_user set "SERVICES=!SERVICES! user_service"
  if defined add_order set "SERVICES=!SERVICES! order_service"
  if defined add_payment set "SERVICES=!SERVICES! payment_service"
  if defined add_notification set "SERVICES=!SERVICES! notification_service"
  if defined add_frontend set "SERVICES=!SERVICES! frontend"
)

if not "%SERVICES%"=="" (
  for /f "tokens=* delims= " %%s in ("%SERVICES%") do set "SERVICES=%%s"
)

for /f "usebackq delims=" %%a in (`git rev-parse --short HEAD`) do set TAG=%%a
echo Image tag (short SHA): %TAG%

REM Build images
if "%SERVICES%"=="" (
  echo No specific service changes detected; building all services.
  docker compose build --pull || exit /b 1
) else (
  echo Building changed services: %SERVICES%
  for %%s in (%SERVICES%) do (
    docker compose build --pull %%s || exit /b 1
  )
)

REM Login and push
if "%DOCKERHUB_USERNAME%"=="" (
  echo WARNING: DOCKERHUB_USERNAME not provided; skipping push. Ensure Credentials Binding is configured.
  goto :end
)

echo Logging into Docker Hub as %DOCKERHUB_USERNAME%
> tmp_pwd.txt echo %DOCKERHUB_TOKEN%
docker login -u "%DOCKERHUB_USERNAME%" --password-stdin < tmp_pwd.txt || exit /b 1
del tmp_pwd.txt
echo Current Docker Hub login:
docker info | findstr /I "Username:"

if "%SERVICES%"=="" set "SERVICES=product_service user_service order_service payment_service notification_service frontend"

REM Tag flow: create SHA tag from latest, then make latest point to the SHA tag
for %%s in (%SERVICES%) do (
  echo Tagging built image as %NS%/%%s:%TAG% from latest
  docker tag %NS%/%%s:latest %NS%/%%s:%TAG% || exit /b 1
  echo Tagging latest from %NS%/%%s:%TAG%
  docker tag %NS%/%%s:%TAG% %NS%/%%s:latest || exit /b 1
  echo Image digest for %NS%/%%s:%TAG%:
  docker inspect --format="{{.Id}}" %NS%/%%s:%TAG%
  echo Image digest for %NS%/%%s:latest:
  docker inspect --format="{{.Id}}" %NS%/%%s:latest
)

REM Push SHA first, then latest, so both reflect the same image
for %%s in (%SERVICES%) do (
  echo Pushing %NS%/%%s:%TAG%
  docker push %NS%/%%s:%TAG% || (echo ERROR: Push failed for %NS%/%%s:%TAG%. Ensure repo exists and your token has write access.& exit /b 1)
)
for %%s in (%SERVICES%) do (
  echo Pushing %NS%/%%s:latest
  docker push %NS%/%%s:latest || (echo ERROR: Push failed for %NS%/%%s:latest. Ensure repo exists and your token has write access.& exit /b 1)
)

docker logout

:end
echo Done.
exit /b 0
