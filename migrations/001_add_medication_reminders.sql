-- Migration: Add medication_reminders and adherence_logs tables
-- Created: 2025-11-25
-- Description: Support medication reminder feature with adherence tracking

-- Table: medication_reminders
CREATE TABLE IF NOT EXISTS medication_reminders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    medicine_id INT NULL COMMENT 'Optional: Link to medicines table for database medicines',
    medicine_name VARCHAR(255) NOT NULL COMMENT 'Required: User-entered or from database',
    title VARCHAR(255) NOT NULL COMMENT 'Reminder title/description',
    dosage VARCHAR(100) NULL COMMENT 'Dosage information (e.g., 500mg, 2 viên)',
    frequency VARCHAR(50) NOT NULL COMMENT 'Frequency: daily, weekly, custom',
    times JSON NOT NULL COMMENT 'Array of time strings in HH:MM format: ["08:00", "14:00", "20:00"]',
    days_of_week JSON NULL COMMENT 'For weekly frequency: [0,1,2,3,4,5,6] where 0=Monday',
    start_date DATE NOT NULL COMMENT 'Start date for reminder',
    end_date DATE NULL COMMENT 'Optional end date',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Whether reminder is active',
    notes TEXT NULL COMMENT 'Additional notes',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE SET NULL,
    
    INDEX idx_user_active (user_id, is_active),
    INDEX idx_start_end (start_date, end_date),
    INDEX idx_medicine (medicine_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Medication reminders for users';

-- Table: adherence_logs
CREATE TABLE IF NOT EXISTS adherence_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    reminder_id INT NOT NULL,
    user_id INT NOT NULL,
    scheduled_time DATETIME NOT NULL COMMENT 'When the reminder was scheduled',
    action_time DATETIME NULL COMMENT 'When user took action',
    action_type VARCHAR(20) NOT NULL COMMENT 'User action: taken, snoozed, skipped',
    snooze_minutes INT NULL COMMENT 'Snooze duration in minutes (5-60)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (reminder_id) REFERENCES medication_reminders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_reminder_scheduled (reminder_id, scheduled_time),
    INDEX idx_user_month (user_id, scheduled_time),
    INDEX idx_action_type (action_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Adherence tracking logs for medication reminders';
