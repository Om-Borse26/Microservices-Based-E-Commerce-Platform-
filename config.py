# Microservices Configuration

# Database Configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Yog@101619'

# Service Ports
PRODUCT_SERVICE_PORT = 5000
USER_SERVICE_PORT = 5001
ORDER_SERVICE_PORT = 5002

# Service URLs
PRODUCT_SERVICE_URL = f'http://localhost:{PRODUCT_SERVICE_PORT}'
USER_SERVICE_URL = f'http://localhost:{USER_SERVICE_PORT}'
ORDER_SERVICE_URL = f'http://localhost:{ORDER_SERVICE_PORT}'

# Security
SECRET_KEY = 'your-secret-key-change-in-production'
JWT_EXPIRATION_HOURS = 24

# Frontend
FRONTEND_PORT = 3000
