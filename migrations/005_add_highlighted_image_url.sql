-- Migration: Add highlighted_image_url column to scans table
-- Date: 2025-12-21
-- Description: Add column to store URL of highlighted/annotated scan images with boundary detection

-- Add highlighted_image_url column
ALTER TABLE scans 
ADD COLUMN highlighted_image_url VARCHAR(500) NULL 
COMMENT 'URL of highlighted/annotated scan image with boundary detection';

-- Add index for faster queries
CREATE INDEX idx_scans_highlighted_url ON scans(highlighted_image_url);
