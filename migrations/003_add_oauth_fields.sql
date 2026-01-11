-- Migration: Add OAuth fields to users table
-- Created: 2025-11-25
-- Description: Add OAuth provider fields for Google and Facebook authentication

ALTER TABLE users 
ADD COLUMN oauth_provider VARCHAR(20) NULL COMMENT 'google, facebook, or null for email/password',
ADD COLUMN google_id VARCHAR(255) NULL UNIQUE COMMENT 'Google user ID',
ADD COLUMN facebook_id VARCHAR(255) NULL UNIQUE COMMENT 'Facebook user ID',
ADD INDEX idx_google_id (google_id),
ADD INDEX idx_facebook_id (facebook_id);
