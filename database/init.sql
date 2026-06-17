-- TEMPLATE: Replace this with your actual schema.
-- This file runs automatically when the MariaDB container first starts.
-- It does NOT re-run if the volume already exists.

CREATE DATABASE IF NOT EXISTS `recipes_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `recipes_db`;

-- Example table — replace with your actual schema:
-- CREATE TABLE IF NOT EXISTS example (
--   id INT AUTO_INCREMENT PRIMARY KEY,
--   name VARCHAR(255) NOT NULL,
--   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
