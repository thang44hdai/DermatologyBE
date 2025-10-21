-- =============================================
-- Database Setup for Dermatology Backend API
-- XAMPP MySQL Configuration
-- =============================================

-- Create database
CREATE DATABASE IF NOT EXISTS dermatology_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Use the database
USE dermatology_db;

-- Show existing tables (will be created automatically by SQLAlchemy)
SHOW TABLES;

-- =============================================
-- Optional: Create a dedicated user (recommended for production)
-- =============================================

-- Uncomment these lines if you want to create a dedicated user
-- CREATE USER IF NOT EXISTS 'dermatology_user'@'localhost' IDENTIFIED BY 'your_password_here';
-- GRANT ALL PRIVILEGES ON dermatology_db.* TO 'dermatology_user'@'localhost';
-- FLUSH PRIVILEGES;

-- =============================================
-- Verify database creation
-- =============================================

SELECT 
    SCHEMA_NAME as 'Database Name',
    DEFAULT_CHARACTER_SET_NAME as 'Character Set',
    DEFAULT_COLLATION_NAME as 'Collation'
FROM information_schema.SCHEMATA 
WHERE SCHEMA_NAME = 'dermatology_db';

-- =============================================
-- Notes:
-- =============================================
-- Tables will be automatically created by SQLAlchemy when you run the app:
-- - users
-- - prediction_history
--
-- Default XAMPP MySQL Settings:
-- - Host: localhost
-- - Port: 3306
-- - User: root
-- - Password: (empty)
-- =============================================
