CREATE DATABASE IF NOT EXISTS product_db;
CREATE DATABASE IF NOT EXISTS user_db;
CREATE DATABASE IF NOT EXISTS order_db;
CREATE DATABASE IF NOT EXISTS payment_db;
CREATE DATABASE IF NOT EXISTS notification_db;

USE product_db;
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(100),
    image_url VARCHAR(500),
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO products (name, description, price, category, image_url, stock) VALUES
('Laptop Pro 15', 'High-performance laptop with 16GB RAM', 1299.99, 'Electronics', 'https://via.placeholder.com/300x200?text=Laptop', 25),
('Wireless Mouse', 'Ergonomic wireless mouse', 29.99, 'Electronics', 'https://via.placeholder.com/300x200?text=Mouse', 100),
('Office Chair', 'Comfortable ergonomic office chair', 249.99, 'Furniture', 'https://via.placeholder.com/300x200?text=Chair', 15),
('Desk Lamp', 'LED desk lamp with adjustable brightness', 39.99, 'Furniture', 'https://via.placeholder.com/300x200?text=Lamp', 50),
('Keyboard Mechanical', 'RGB mechanical gaming keyboard', 89.99, 'Electronics', 'https://via.placeholder.com/300x200?text=Keyboard', 30);

USE user_db;
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

USE order_db;
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

USE payment_db;
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

USE notification_db;
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
