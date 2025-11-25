-- Migration: Add FCM token to users table
-- Created: 2025-11-25
-- Description: Add fcm_token field for Firebase Cloud Messaging push notifications

ALTER TABLE users 
ADD COLUMN fcm_token VARCHAR(255) NULL COMMENT 'Firebase Cloud Messaging token for push notifications',
ADD INDEX idx_fcm_token (fcm_token);
