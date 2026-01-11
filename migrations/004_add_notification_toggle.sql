-- Migration: Add notification toggle to medication reminders
-- Created: 2025-11-25
-- Description: Add is_notification_enabled field to control push notifications per reminder

ALTER TABLE medication_reminders
ADD COLUMN is_notification_enabled BOOLEAN NOT NULL DEFAULT TRUE 
COMMENT 'Enable/disable push notifications for this reminder';
