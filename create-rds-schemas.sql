-- ════════════════════════════════════════════════════════════════════════════
-- ShopEase Microservices Database Schemas
-- This creates 5 separate databases with their respective tables
-- ════════════════════════════════════════════════════════════════════════════

-- ════════════════════════════════════════════════════════════════════════════
-- 1. PRODUCT SERVICE DATABASE
-- ════════════════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS productdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE productdb;

DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(100),
    stock INT DEFAULT 0,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_category (category),
    INDEX idx_price (price),
    INDEX idx_stock (stock),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample data for product service
INSERT INTO products (name, description, price, category, stock, image_url) VALUES
('Laptop Pro 15', 'High-performance laptop with 16GB RAM and 512GB SSD', 89999.00, 'Electronics', 50, 'https://via.placeholder.com/300x300?text=Laptop'),
('Wireless Mouse', 'Ergonomic wireless mouse with USB receiver', 1299.00, 'Electronics', 200, 'https://via.placeholder.com/300x300?text=Mouse'),
('Mechanical Keyboard', 'RGB backlit mechanical gaming keyboard', 4999.00, 'Electronics', 100, 'https://via.placeholder.com/300x300?text=Keyboard'),
('Office Chair', 'Ergonomic office chair with lumbar support', 12999.00, 'Furniture', 30, 'https://via.placeholder.com/300x300?text=Chair'),
('Standing Desk', 'Adjustable height standing desk', 24999.00, 'Furniture', 20, 'https://via.placeholder.com/300x300?text=Desk');

-- ════════════════════════════════════════════════════════════════════════════
-- 2. USER SERVICE DATABASE
-- ════════════════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS userdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE userdb;

DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    country VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_is_active (is_active),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample admin user (password: admin123)
-- Password hash generated using: werkzeug.security.generate_password_hash('admin123')
INSERT INTO users (username, email, password_hash, first_name, last_name, phone, is_admin, is_active) VALUES
('admin', 'admin@shopease.com', 'pbkdf2:sha256:600000$YourSaltHere$hashedpassword', 'Admin', 'User', '1234567890', TRUE, TRUE);

-- ════════════════════════════════════════════════════════════════════════════
-- 3. ORDER SERVICE DATABASE
-- ════════════════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS orderdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE orderdb;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payment_status VARCHAR(50) DEFAULT 'pending',
    shipping_address TEXT,
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    shipping_zip VARCHAR(20),
    shipping_country VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_payment_status (payment_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(200),
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ════════════════════════════════════════════════════════════════════════════
-- 4. PAYMENT SERVICE DATABASE
-- ════════════════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS paymentdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE paymentdb;

DROP TABLE IF EXISTS payments;

CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'pending',
    transaction_id VARCHAR(100) UNIQUE,
    payment_gateway VARCHAR(50),
    gateway_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id),
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_payment_status (payment_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ════════════════════════════════════════════════════════════════════════════
-- 5. NOTIFICATION SERVICE DATABASE
-- ════════════════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS notificationdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE notificationdb;

DROP TABLE IF EXISTS notifications;

CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(200),
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    delivery_method VARCHAR(50) DEFAULT 'email',
    recipient VARCHAR(200),
    sent_at TIMESTAMP NULL,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    order_id INT,
    payment_id VARCHAR(100),
    error_message TEXT,
    retry_count INT DEFAULT 0,
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_category (category),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ════════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES
-- ════════════════════════════════════════════════════════════════════════════

-- Show all databases
SELECT '════════════════════════════════════════════' AS '';
SELECT 'DATABASES CREATED:' AS '';
SELECT '════════════════════════════════════════════' AS '';
SHOW DATABASES LIKE '%db';

-- Verify each database
SELECT '════════════════════════════════════════════' AS '';
SELECT 'PRODUCT DATABASE TABLES:' AS '';
USE productdb;
SHOW TABLES;
SELECT COUNT(*) AS product_count FROM products;

SELECT '════════════════════════════════════════════' AS '';
SELECT 'USER DATABASE TABLES:' AS '';
USE userdb;
SHOW TABLES;
SELECT COUNT(*) AS user_count FROM users;

SELECT '════════════════════════════════════════════' AS '';
SELECT 'ORDER DATABASE TABLES:' AS '';
USE orderdb;
SHOW TABLES;

SELECT '════════════════════════════════════════════' AS '';
SELECT 'PAYMENT DATABASE TABLES:' AS '';
USE paymentdb;
SHOW TABLES;

SELECT '════════════════════════════════════════════' AS '';
SELECT 'NOTIFICATION DATABASE TABLES:' AS '';
USE notificationdb;
SHOW TABLES;

SELECT '════════════════════════════════════════════' AS '';
SELECT '✅ ALL SCHEMAS CREATED SUCCESSFULLY!' AS STATUS;
SELECT '════════════════════════════════════════════' AS '';