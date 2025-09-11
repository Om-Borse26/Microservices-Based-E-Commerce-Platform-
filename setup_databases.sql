-- Database Setup Script for E-commerce Microservices
-- Run this script in MySQL to create all required databases

-- Create databases for each microservice
CREATE DATABASE IF NOT EXISTS productdb;
CREATE DATABASE IF NOT EXISTS userdb;
CREATE DATABASE IF NOT EXISTS orderdb;
CREATE DATABASE IF NOT EXISTS paymentdb;
CREATE DATABASE IF NOT EXISTS notificationdb;

-- Show all databases
SHOW DATABASES;

-- Optional: Create a dedicated user for the application (recommended for production)
-- CREATE USER IF NOT EXISTS 'ecommerce_user'@'localhost' IDENTIFIED BY 'secure_password';
-- GRANT ALL PRIVILEGES ON productdb.* TO 'ecommerce_user'@'localhost';
-- GRANT ALL PRIVILEGES ON userdb.* TO 'ecommerce_user'@'localhost';
-- GRANT ALL PRIVILEGES ON orderdb.* TO 'ecommerce_user'@'localhost';
-- GRANT ALL PRIVILEGES ON paymentdb.* TO 'ecommerce_user'@'localhost';
-- GRANT ALL PRIVILEGES ON notificationdb.* TO 'ecommerce_user'@'localhost';
-- FLUSH PRIVILEGES;
