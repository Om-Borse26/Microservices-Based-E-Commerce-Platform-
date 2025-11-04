## Project Overview

Microservices-based e-commerce demo with five Python/Flask services and a static frontend. Each service owns its data and exposes a small REST API. A MySQL instance backs the domain data. Docker Compose is used for local orchestration, and images can be published to Docker Hub for easy distribution.

### Architecture
- Services (default ports):
	- product_service: 5000 — product catalog and seeding
	- user_service: 5001 — user registration/login, JWT
	- order_service: 5002 — order creation and status
	- payment_service: 5003 — payment processing triggers notifications
	- notification_service: 5005 — email notifications (SMTP)
	- frontend (Nginx): 8081 — static UI calling backend APIs
- Database: MySQL 8.0 (host port 3307 → container 3306)
- Service discovery: HTTP via known hostnames/ports; in Docker, services reach each other by service name defined in `docker-compose.yml`.

### Docker Images
Published images under Docker Hub account `omborse1618`:

- product_service: https://hub.docker.com/r/omborse1618/product_service
	- ![pulls](https://img.shields.io/docker/pulls/omborse1618/product_service) ![size](https://img.shields.io/docker/image-size/omborse1618/product_service/latest)
- user_service: https://hub.docker.com/r/omborse1618/user_service
	- ![pulls](https://img.shields.io/docker/pulls/omborse1618/user_service) ![size](https://img.shields.io/docker/image-size/omborse1618/user_service/latest)
- order_service: https://hub.docker.com/r/omborse1618/order_service
	- ![pulls](https://img.shields.io/docker/pulls/omborse1618/order_service) ![size](https://img.shields.io/docker/image-size/omborse1618/order_service/latest)
- payment_service: https://hub.docker.com/r/omborse1618/payment_service
	- ![pulls](https://img.shields.io/docker/pulls/omborse1618/payment_service) ![size](https://img.shields.io/docker/image-size/omborse1618/payment_service/latest)
- notification_service: https://hub.docker.com/r/omborse1618/notification_service
	- ![pulls](https://img.shields.io/docker/pulls/omborse1618/notification_service) ![size](https://img.shields.io/docker/image-size/omborse1618/notification_service/latest)
- frontend: https://hub.docker.com/r/omborse1618/frontend
	- ![pulls](https://img.shields.io/docker/pulls/omborse1618/frontend) ![size](https://img.shields.io/docker/image-size/omborse1618/frontend/latest)

### Data Flow (happy path)
1) User registers/logs in (user_service)
2) User views products (product_service)
3) User creates an order (order_service)
4) Payment processed (payment_service) → notifies notification_service
5) Notification emails users upon successful payment

### Environment Variables (key ones)
- SECRET_KEY: Flask/JWT secret
- MYSQL_ROOT_PASSWORD: MySQL root password (compose)
- DATABASE_URI: Optional override per service; default points to MySQL in compose
- SERVICE_URLs: Base URLs for inter-service calls (set via compose)
- Email/SMTP (notification_service):
	- ENABLE_REAL_EMAIL_SENDING=True|False
	- SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD, FROM_NAME
- DOCKERHUB_USER: Docker Hub namespace for image tags

Keep real secrets out of git. Use `.env` for local development and Docker Compose.

## APIs and Independent Testing

Below are core endpoints and minimal test examples. Replace sample values as needed. All commands are PowerShell-friendly.

Note: Each service exposes `/health` returning 200 when ready.

### product_service (5000)
- Seed demo products:

```powershell
Invoke-RestMethod -Method POST http://localhost:5000/init-data
```

- List products (typical):

```powershell
Invoke-RestMethod http://localhost:5000/products
```

### user_service (5001)
- Register:

```powershell
$body = @{ name = "Alice"; email = "alice@example.com"; password = "Passw0rd!" } | ConvertTo-Json
Invoke-RestMethod -Method POST http://localhost:5001/register -ContentType 'application/json' -Body $body
```

- Login (returns token):

```powershell
$body = @{ email = "alice@example.com"; password = "Passw0rd!" } | ConvertTo-Json
$login = Invoke-RestMethod -Method POST http://localhost:5001/login -ContentType 'application/json' -Body $body
$token = $login.token
```

### order_service (5002)
- Create order:

```powershell
$body = @{ user_email = "alice@example.com"; items = @(@{ product_id = 1; quantity = 1 }) } | ConvertTo-Json
Invoke-RestMethod -Method POST http://localhost:5002/orders -ContentType 'application/json' -Body $body
```

### payment_service (5003)
- Process payment:

```powershell
$body = @{ order_id = 1; amount = 49.99; method = "card" } | ConvertTo-Json
Invoke-RestMethod -Method POST http://localhost:5003/payments -ContentType 'application/json' -Body $body
```

### notification_service (5005)
- Send a test email:

```powershell
$body = @{ to = "you@example.com"; subject = "Test"; message = "Hello from notification_service" } | ConvertTo-Json
Invoke-RestMethod -Method POST http://localhost:5005/test-email -ContentType 'application/json' -Body $body
```

Ensure SMTP environment is configured and `ENABLE_REAL_EMAIL_SENDING=True` to send real emails.

## Local Development (without Docker for services)

You can run services directly with Python for quick iteration. The simplest setup is: use Docker for MySQL only, and run Flask apps locally.

### 1) Start MySQL via Compose

```powershell
docker compose up -d mysql
```

MySQL is on `localhost:3307` (host) → `3306` (container).

### 2) Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3) Run a service

Example for product_service:

```powershell
$env:PORT = "5000"
$env:DATABASE_URI = "mysql+pymysql://root:root@localhost:3307/product_db"
python .\product_service.py
```

Repeat similarly for other services (ports 5001, 5002, 5003, 5005). Set `SERVICE_URL` variables if the service calls others. Alternatively, use the provided `start_services.bat` to launch multiple services for practice (beware of conflicts if Docker Compose is running the same ports).

---

## Containerization

This project includes Dockerfiles for each microservice and a `docker-compose.yml` to run everything locally.

### Prerequisites
- Docker Desktop installed and running
- Optional: Docker Hub account (for pushing images)

### Quick Start (compose)

Run all services (MySQL + microservices + frontend on port 8081):

```powershell
docker compose up --build
```

Services map to host ports:
- product_service: `http://localhost:5000`
- user_service: `http://localhost:5001`
- order_service: `http://localhost:5002`
- payment_service: `http://localhost:5003`
- notification_service: `http://localhost:5005`
- frontend (static): `http://localhost:8081`

Environment overrides (PowerShell examples):

```powershell
$env:MYSQL_ROOT_PASSWORD = "root"; `
$env:SECRET_KEY = "change-me"; `
$env:EMAIL_USER = "your-email@gmail.com"; `
$env:EMAIL_PASSWORD = "app-password"; `
$env:ENABLE_REAL_EMAIL_SENDING = "False"; `
docker compose up --build
```

### Build and tag images

You can also build images individually and tag for Docker Hub:

```powershell
$dockerId = "<your-dockerhub-username>"
docker build -f Dockerfile.product -t $dockerId/product_service:latest .
docker build -f Dockerfile.user -t $dockerId/user_service:latest .
docker build -f Dockerfile.order -t $dockerId/order_service:latest .
docker build -f Dockerfile.payment -t $dockerId/payment_service:latest .
docker build -f Dockerfile.notification -t $dockerId/notification_service:latest .
docker build -f Dockerfile.frontend -t $dockerId/frontend:latest .
```

### Push images to Docker Hub

```powershell
docker login
$dockerId = "<your-dockerhub-username>"
docker push $dockerId/product_service:latest
docker push $dockerId/user_service:latest
docker push $dockerId/order_service:latest
docker push $dockerId/payment_service:latest
docker push $dockerId/notification_service:latest
docker push $dockerId/frontend:latest
```

### Notes
- DB URIs and inter-service URLs are driven by environment variables (see `docker-compose.yml`).
- `frontend/script.js` points to localhost services; when running with compose, these still resolve because ports are published to the host.
- For production, consider API gateway or environment-based endpoint injection for the frontend.

## End-to-End: Build, Publish, and Run from Docker Hub

Follow this workflow to create Docker Hub repositories, build and push images, and run the app anywhere by pulling published images. All commands are for Windows PowerShell.

### 1) Prerequisites
- Docker Desktop installed and running
- Docker Hub account (free) and you are logged in: `docker login`

### 2) Configure environment
Use either a `.env` file (recommended) or PowerShell environment variables. The compose file reads `DOCKERHUB_USER` to name images and uses SMTP values for real email.

Sample `.env` (adjust values):

```env
DOCKERHUB_USER=your-dockerhub-username
SECRET_KEY=change-me
MYSQL_ROOT_PASSWORD=root
ENABLE_REAL_EMAIL_SENDING=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
FROM_NAME=E-Commerce Demo
```

PowerShell alternative for a one-off session:

```powershell
$env:DOCKERHUB_USER = "your-dockerhub-username"
```

### 3) Create Docker Hub repositories (one per service)
Create these public repositories in Docker Hub under your account:
- `<user>/product_service`
- `<user>/user_service`
- `<user>/order_service`
- `<user>/payment_service`
- `<user>/notification_service`
- `<user>/frontend`

Tip: In Docker Hub UI → Repositories → Create repository → Name exactly as above.

### 4) Build images tagged to your account
Compose uses `${DOCKERHUB_USER}` to tag images automatically.

```powershell
$env:DOCKERHUB_USER = "your-dockerhub-username"
docker compose build --pull
```

This builds:
- `your-dockerhub-username/product_service:latest`
- `your-dockerhub-username/user_service:latest`
- `your-dockerhub-username/order_service:latest`
- `your-dockerhub-username/payment_service:latest`
- `your-dockerhub-username/notification_service:latest`
- `your-dockerhub-username/frontend:latest`

### 5) Push images to Docker Hub

```powershell
docker login
docker compose push
```

Verify in Docker Hub that each repo has the `latest` tag.

### 6) Pull and run the published images (any machine)
On any host with Docker Desktop:

```powershell
# Ensure DOCKERHUB_USER matches the publisher account
$env:DOCKERHUB_USER = "your-dockerhub-username"

# Pull images referenced in docker-compose.yml
docker compose pull

# Start the full stack
docker compose up -d

# Optional: list containers and check ports
docker compose ps

# Quick check: frontend should return 200
Invoke-WebRequest -UseBasicParsing http://localhost:8081 | Select-Object -ExpandProperty StatusCode
```

Open `http://localhost:8081` to use the app.

### 7) Test the application flow
- Register/login a user (user_service on port 5001)
- View products (product_service on port 5000)
- Create an order (order_service on port 5002)
- Pay for the order (payment_service on port 5003)
- Expect an email from `notification_service` (port 5005) if SMTP is configured and `ENABLE_REAL_EMAIL_SENDING=True`

Health endpoints (optional):

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:5000/health | % StatusCode
Invoke-WebRequest -UseBasicParsing http://localhost:5001/health | % StatusCode
Invoke-WebRequest -UseBasicParsing http://localhost:5002/health | % StatusCode
Invoke-WebRequest -UseBasicParsing http://localhost:5003/health | % StatusCode
Invoke-WebRequest -UseBasicParsing http://localhost:5005/health | % StatusCode
```

### 8) Optional: add version tags
Tag a release alongside `latest` and push it.

```powershell
$env:DOCKERHUB_USER = "your-dockerhub-username"
$tag = "v0.1.0"
foreach ($img in "product_service","user_service","order_service","payment_service","notification_service","frontend") {
	docker tag "$env:DOCKERHUB_USER/$img:latest" "$env:DOCKERHUB_USER/$img:$tag"
	docker push "$env:DOCKERHUB_USER/$img:$tag"
}
```

### 9) Troubleshooting
- If push fails: confirm `docker login` and repository names match exactly.
- If ports are busy: update host port mappings in `docker-compose.yml` (frontend uses 8081; MySQL maps host 3307 → container 3306).
- Email not received: verify Gmail App Password, `SMTP_SERVER/PORT`, and that `ENABLE_REAL_EMAIL_SENDING=True`.

---

## CI/CD with Jenkins

Automate build, test, and image publishing when you push to GitHub, using the provided `Jenkinsfile` and helper scripts.

### Requirements (Jenkins agent)
- Linux agent recommended (shell steps use `bash`)
- Docker Engine + Docker Compose v2 (`docker compose` CLI)
- `curl` and `jq` installed for smoke tests

### Jenkins plugins
- Pipeline (Declarative)
- Git / Git client
- Email Extension Plugin (or Mailer)
- GitHub (optional, for webhooks and status)

### Credentials to configure
Create these in Jenkins > Manage Jenkins > Credentials:
- `dockerhub-username-only` (Secret text): your Docker Hub username (used for `DOCKERHUB_USER`)
- `dockerhub-credentials` (Username with password): Docker Hub username + PAT/password (for `docker login`)

Optional Jenkins global env or job parameter:
- `NOTIFY_EMAIL`: recipient for build notifications

### Job setup
1) Create a Pipeline job
2) Choose “Pipeline script from SCM” and point to this Git repo (branch `main`)
3) Script path: `Jenkinsfile`
4) Set build triggers:
	- Option A: Check “Build when a change is pushed to GitHub” and configure a GitHub webhook to your Jenkins URL `/github-webhook/`
	- Option B: Configure polling (e.g., `H/5 * * * *`) if webhooks aren’t possible

### What the pipeline does
1) Checkout and compute image tag from short Git SHA
2) Build all images with `docker compose`
3) Bring up stack for health checks
4) Run smoke tests via `scripts/smoke_test.sh`
5) Login to Docker Hub and push:
	- `latest` via `docker compose push`
	- version tag (short SHA) for all images
6) On success/failure: send notification email (requires Email Extension configured)

### Helper scripts
- `scripts/wait_for_http.sh`: wait for HTTP 200/301/302 or timeout
- `scripts/smoke_test.sh`: minimal end-to-end flow (seed → register/login → order → pay)

### Common CI issues
- Missing `jq`: install with your distro package manager (e.g., `apt-get install -y jq`)
- Compose command not found: ensure Docker Desktop is not required; install Docker Compose v2 on the agent
- Docker perms: add Jenkins user to `docker` group or run on an agent with proper privileges
- Email fails: configure SMTP in Jenkins and/or switch to the simpler `mail` step

