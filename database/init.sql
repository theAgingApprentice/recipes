CREATE DATABASE IF NOT EXISTS `recipes_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE `recipes_db`;

CREATE TABLE IF NOT EXISTS cuisines (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS proteins (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO cuisines (name) VALUES
  ('American'), ('Asian'), ('British'), ('Cantonese'), ('Chinese'),
  ('Eastern European'), ('French'), ('Indonesian'), ('Israeli'), ('Italian'),
  ('Italian-American'), ('Mediterranean'), ('Mexican'), ('Russian'),
  ('Thai'), ('Vietnamese'), ('Western'), ('Other');

CREATE TABLE IF NOT EXISTS dish_types (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO dish_types (name) VALUES
  ('Breakfast'), ('Dessert'), ('Main'), ('Side'), ('Snack'), ('Starter'), ('Other');

INSERT INTO proteins (name) VALUES
  ('Beef'), ('Chicken'), ('Fish'), ('Pork'), ('Vegan'), ('Vegetarian'), ('Other');

CREATE TABLE IF NOT EXISTS recipes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  source_name VARCHAR(255),
  source_url TEXT,
  cuisine VARCHAR(100),
  dish_type VARCHAR(100),
  protein VARCHAR(100),
  prep_time_mins INT,
  cook_time_mins INT,
  notes TEXT,
  wishlist BOOLEAN NOT NULL DEFAULT FALSE,
  prep_ahead BOOLEAN NOT NULL DEFAULT FALSE,
  prep_ahead_override BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ingredients (
  id INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  quantity VARCHAR(100),
  category VARCHAR(100),
  sort_order INT NOT NULL DEFAULT 0,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS steps (
  id INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id INT NOT NULL,
  step_number INT NOT NULL,
  instruction TEXT NOT NULL,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cook_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id INT NOT NULL,
  cooked_on DATE NOT NULL,
  rating TINYINT,
  notes TEXT,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meal_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  week_start DATE NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meal_plan_entries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  meal_plan_id INT NOT NULL,
  day_of_week TINYINT NOT NULL COMMENT '0=Mon, 6=Sun',
  meal_slot ENUM('breakfast','lunch','dinner','snack') NOT NULL DEFAULT 'dinner',
  recipe_id INT NOT NULL,
  FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS rejection_reasons (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO rejection_reasons (name) VALUES
  ('Not in the mood'),
  ('Too complex'),
  ('Missing ingredients'),
  ('Recently eaten'),
  ('Other');

CREATE TABLE IF NOT EXISTS ai_suggestions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id INT NOT NULL,
  meal_plan_id INT,
  scope VARCHAR(20) NOT NULL,
  composition VARCHAR(20) NOT NULL,
  criteria TEXT,
  day_of_week TINYINT,
  meal_slot VARCHAR(20),
  explanation TEXT,
  accepted BOOLEAN,
  rejection_reason_id INT,
  rejection_reason_text VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
  FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE SET NULL,
  FOREIGN KEY (rejection_reason_id) REFERENCES rejection_reasons(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recipe_links (
  id INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id INT NOT NULL,
  linked_recipe_id INT NOT NULL,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
  FOREIGN KEY (linked_recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
  UNIQUE KEY uq_link (recipe_id, linked_recipe_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
