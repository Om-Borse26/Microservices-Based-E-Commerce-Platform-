# Microservices E-Commerce Platform

A microservices-based e-commerce platform built with Flask, MySQL, and vanilla JavaScript frontend.

## Architecture

This platform consists of multiple microservices:

1. **Product Service** (Port 5000)
   - Manages product catalog
   - CRUD operations for products
   - Inventory management

2. **User Service** (Port 5001)
   - User authentication and registration
   - JWT token management
   - User profile management

3. **Order Service** (Port 5002)
   - Order creation and management
   - Shopping cart functionality
   - Order status tracking

4. **Frontend** (Served by Product Service)
   - Responsive web interface
   - Shopping cart functionality
   - Admin panel for product management

## Prerequisites

- Python 3.8+
- MySQL Server
- Git

## Database Setup

1. Install MySQL and start the service
2. Create the required databases:

```sql
CREATE DATABASE productdb;
CREATE DATABASE userdb;
CREATE DATABASE orderdb;
```

3. Update database credentials in each service file if needed.

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Combined\ Project
```

2. Run the setup script:
```bash
start_services.bat
```

This will:
- Create a virtual environment
- Install all dependencies
- Start all microservices in separate terminal windows

## Manual Setup (Alternative)

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start each service in separate terminals:

Terminal 1 - Product Service:
```bash
python product_service.py
```

Terminal 2 - User Service:
```bash
python user_service.py
```

Terminal 3 - Order Service:
```bash
python order_service.py
```

## Access Points

- **Frontend Application**: http://localhost:5000
- **Product Service API**: http://localhost:5000/products
- **User Service API**: http://localhost:5001/users
- **Order Service API**: http://localhost:5002/orders

## API Documentation

### Product Service (Port 5000)

- `GET /products` - Get all products
- `GET /products/{id}` - Get specific product
- `POST /products` - Create new product
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product
- `GET /health` - Health check

### User Service (Port 5001)

- `POST /register` - Register new user
- `POST /login` - User login
- `GET /profile` - Get user profile (requires auth)
- `PUT /profile` - Update user profile (requires auth)
- `GET /users` - Get all users (admin)
- `GET /health` - Health check

### Order Service (Port 5002)

- `POST /orders` - Create new order
- `GET /orders/{id}` - Get specific order
- `GET /orders/user/{user_id}` - Get user's orders
- `PUT /orders/{id}/status` - Update order status
- `GET /orders` - Get all orders (admin)
- `DELETE /orders/{id}` - Cancel order
- `GET /health` - Health check

## Frontend Features

### Customer Features:
- Browse product catalog
- Search products
- Add products to cart
- Manage shopping cart
- Place orders
- View order history

### Admin Features:
- Add new products
- Manage inventory
- View all orders
- Update order status

## Development

### Project Structure:
```
├── product_service.py      # Product microservice
├── user_service.py         # User microservice  
├── order_service.py        # Order microservice
├── config.py              # Configuration file
├── requirements.txt       # Python dependencies
├── start_services.bat     # Service startup script
├── frontend/
│   ├── index.html         # Main frontend page
│   ├── script.js          # Frontend JavaScript
│   └── style.css          # Frontend styles
└── README.md              # This file
```

### Adding New Features:

1. **New Microservice**: Create a new Python file with Flask app
2. **Database Changes**: Update models and run migrations
3. **Frontend Changes**: Update HTML/CSS/JS files
4. **Inter-service Communication**: Use HTTP requests between services

### Best Practices:

1. Each microservice has its own database
2. Services communicate via REST APIs
3. Use JWT tokens for authentication
4. Include health check endpoints
5. Handle errors gracefully
6. Use environment variables for configuration

## Troubleshooting

### Common Issues:

1. **Database Connection Error**:
   - Check MySQL service is running
   - Verify database credentials
   - Ensure databases are created

2. **Port Already in Use**:
   - Check if services are already running
   - Change ports in service files if needed

3. **CORS Issues**:
   - Ensure Flask-CORS is installed
   - Check browser console for errors

4. **Service Communication Issues**:
   - Verify all services are running
   - Check service URLs in configuration

## Security Notes

- Change SECRET_KEY in production
- Use environment variables for sensitive data
- Implement proper input validation
- Add rate limiting for APIs
- Use HTTPS in production

## Scaling Considerations

- Use load balancers for high traffic
- Implement service discovery
- Add monitoring and logging
- Use containerization (Docker)
- Consider API Gateway
- Implement circuit breakers

## License

This project is for educational purposes.
