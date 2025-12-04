-- Migration: Add Categories for Medicines
-- Version: 003
-- Description: Add categories table and link to medicines

-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_name (name),
    INDEX idx_is_active (is_active)
);

-- Add category_id to medicines table
ALTER TABLE medicines 
ADD COLUMN category_id INT AFTER brand_id,
ADD FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
ADD INDEX idx_category_id (category_id);

-- Insert default categories
INSERT INTO categories (name) VALUES
('Thuốc giảm đau'),
('Kháng sinh'),
('Vitamin & Khoáng chất'),
('Thuốc dạ dày'),
('Thuốc da liễu'),
('Thuốc tim mạch'),
('Thuốc hô hấp'),
('Khác');
