-- Migration: Enhance medication_reminders with detailed Vietnamese fields
-- Created: 2025-11-29
-- Description: Add unit types, meal timing, and enhanced time structure support

-- Add new columns to medication_reminders table
ALTER TABLE medication_reminders
ADD COLUMN unit VARCHAR(50) NULL COMMENT 'Unit type: Viên, Xit, Ong, ml, Mieng, Lieu, Goi, Giot' AFTER dosage,
ADD COLUMN meal_timing VARCHAR(20) NULL COMMENT 'Meal timing: before_meal or after_meal' AFTER unit;

ALTER TABLE medication_reminders DROP COLUMN title;

-- Update frequency column to support new options
-- Note: This doesn't change the column, just documents new valid values
-- Valid values: 'daily', 'weekly', 'every_other_day', 'specific_days', 'custom'

-- The 'times' JSON column structure is enhanced to support:
-- Old format (still supported): ["08:00", "14:00", "20:00"]
-- New format: [{"time": "08:00", "period": "morning", "dosage": "2"}, ...]
-- Both formats will be handled in the application layer for backward compatibility
