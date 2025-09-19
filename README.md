## Containerization

This project includes Dockerfiles for each microservice and a `docker-compose.yml` to run everything locally.

### Prerequisites
- Docker Desktop installed and running
- Optional: Docker Hub account (for pushing images)

### Quick Start (compose)

Run all services (MySQL + microservices + frontend on port 8080):

```powershell
docker compose up --build
```

Services map to host ports:
- product_service: `http://localhost:5000`
- user_service: `http://localhost:5001`
- order_service: `http://localhost:5002`
- payment_service: `http://localhost:5003`
- notification_service: `http://localhost:5005`
- frontend (static): `http://localhost:8080`

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
