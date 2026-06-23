# High Level Architecture
## MitchellNET Recipes App (Item 15)

**Version:** 1.3
**Date:** June 23, 2026
**Status:** Active — PR #6 complete; dish_type, AI meal planning (UC-16), recipe linking (UC-17), admin extensions pending build

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | June 16, 2026 | Initial draft |
| 1.1 | June 18, 2026 | Updated data model for prep_ahead flag; categorizer bug fix; Claude API lessons learned; updated PR table |
| 1.2 | June 22, 2026 | Added cook log routes, templates, and query helpers (UC-15) |
| 1.3 | June 23, 2026 | Added dish_type field (auto-detected, admin-managed); UC-16 AI Meal Planning (new ai_plan route, ai_suggestions + rejection_reasons tables); UC-17 Recipe Linking (recipe_links table); admin extended with dish_types and rejection_reasons; wishlist un-flag prompt in cook log flow; extractor schema updated |

---

## 1. Overview

The Recipes app is a Flask + MariaDB web application deployed as a Docker service on the MitchellNET server. It follows the `python-flask-db` service type and mirrors the fitness-tracker architecture.

Accessible at `https://mitchellnet.local/recipes/` over the LAN. Uses Claude API for recipe extraction, ingredient categorization, and AI meal planning.

---

## 2. System Context

```
Browser (Mac/iPhone on LAN)
        │
        │ HTTPS :443
        ▼
   nginx-proxy
        │
        │ /recipes/  /meal-plan/  /shopping-list/
        ▼
  recipes-app:5000 (Flask + Gunicorn)
        │
        ├── TCP :3306 ──► recipes-db (MariaDB)
        │
        └── HTTPS ──────► api.anthropic.com (extraction, categorization, AI planning)
```

---

## 3. Service Architecture

*(unchanged from v1.2 — two containers, two networks, one volume)*

---

## 4. Application Architecture

### 4.1 Stack

*(unchanged from v1.2)*

### 4.2 Directory Structure

```
recipes/
├── app/
│   ├── app.py
│   ├── config/
│   │   └── database.py
│   ├── models/
│   │   ├── recipe.py        # Recipe, Ingredient, Step, CookLog, Cuisine, DishType models
│   │   ├── meal_plan.py     # MealPlan, MealPlanEntry models
│   │   └── admin.py         # RejectionReason model (NEW)
│   ├── routes/
│   │   ├── recipes.py       # Browse, view, add, edit, delete
│   │   ├── cook_log.py      # Cook log CRUD + wishlist un-flag prompt
│   │   ├── import_.py       # URL import, document upload, save (dish_type added)
│   │   ├── meal_plan.py     # Meal plan manual entry
│   │   ├── shopping.py      # Shopping list
│   │   ├── ai_plan.py       # AI meal planning (NEW — UC-16)
│   │   ├── recipe_links.py  # Recipe linking (NEW — UC-17)
│   │   └── admin.py         # Admin picklist management (extended)
│   ├── services/
│   │   ├── extractor.py     # Claude API — extraction (dish_type added to schema)
│   │   ├── fetcher.py       # URL fetch + HTML cleaning
│   │   ├── categorizer.py   # Claude API — ingredient categorization
│   │   └── ai_planner.py    # Claude API — meal planning suggestions (NEW)
│   └── templates/
│       ├── base.html        # ⚙ Admin link in header
│       ├── recipes/
│       │   ├── browse.html  # dish_type filter + column added
│       │   ├── detail.html  # dish_type, linked recipes section, wishlist un-flag prompt
│       │   └── form.html    # dish_type dropdown, linked recipes section
│       ├── import/
│       │   ├── import.html
│       │   └── review.html  # dish_type dropdown added
│       ├── cook_log/
│       │   └── edit.html
│       ├── meal_plan/
│       │   └── view.html    # "AI Suggest" button added
│       ├── shopping/
│       │   └── view.html
│       ├── ai_plan/         # NEW
│       │   ├── form.html    # Scope / composition / criteria selection
│       │   └── results.html # Suggestions list with accept/reject per item
│       └── admin/
│           └── index.html   # Extended: Cuisines + Dish Types + Rejection Reasons
├── database/
│   └── init.sql             # Updated with new tables
├── docs/
│   ├── recipes-BRD.md
│   └── recipes-HLA.md
└── ...
```

---

## 5. Data Model

### 5.1 Entity Relationship Summary

```
Recipe ──< Ingredient
Recipe ──< Step
Recipe ──< CookLog
Recipe ──< MealPlanEntry >── MealPlan
Recipe ──< AiSuggestion
Recipe >── DishType
Recipe ──< RecipeLink >── Recipe  (self-referential, bidirectional)
Cuisine  (picklist)
DishType (picklist)
RejectionReason (picklist)
AiSuggestion >── RejectionReason
```

### 5.2 Tables

**recipes** (updated)
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| name | VARCHAR(255) | Required |
| source_name | VARCHAR(255) | |
| source_url | TEXT | |
| cuisine | VARCHAR(100) | Free text; guided by cuisines picklist |
| dish_type | VARCHAR(100) | NEW — e.g. "Main", "Starter"; guided by dish_types picklist |
| protein | VARCHAR(100) | |
| prep_time_mins | INT | |
| cook_time_mins | INT | |
| notes | TEXT | |
| wishlist | BOOLEAN | Default false |
| prep_ahead | BOOLEAN | Default false |
| prep_ahead_override | BOOLEAN | Default false |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**cuisines** (existing)
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| name | VARCHAR(100) UNIQUE | |

**dish_types** (NEW)
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| name | VARCHAR(100) UNIQUE | Seeded: Breakfast, Starter, Main, Side, Dessert, Snack, Other |

**ingredients** *(unchanged)*

**steps** *(unchanged)*

**cook_logs** *(unchanged)*

**meal_plans** *(unchanged)*

**meal_plan_entries** *(unchanged)*

**recipe_links** (NEW)
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| recipe_id | INT FK | One side of the link |
| linked_recipe_id | INT FK | Other side of the link |
| notes | TEXT | Optional — e.g. "Nagi cookbook p.42 — serve together" |
| created_at | DATETIME | |

> Bidirectionality: one row stored per link pair. Queries use `WHERE recipe_id=X OR linked_recipe_id=X` to find all links for a recipe. A UNIQUE constraint on `(LEAST(recipe_id, linked_recipe_id), GREATEST(recipe_id, linked_recipe_id))` prevents A→B and B→A duplicates.

**rejection_reasons** (NEW)
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| name | VARCHAR(255) UNIQUE | Seeded: Already planned recently, Too complex, Wrong cuisine, Missing ingredients, Not in the mood, Other |

**ai_suggestions** (NEW)
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| recipe_id | INT FK | Suggested recipe |
| meal_plan_id | INT FK | Target meal plan (nullable — suggestion may predate plan entry) |
| scope | VARCHAR(20) | "meal", "day", or "week" |
| composition | VARCHAR(20) | "mains_only" or "full_meals" |
| criteria | TEXT | JSON array of criteria strings used |
| day_of_week | TINYINT | 0=Mon, 6=Sun (nullable for single-meal scope) |
| meal_slot | VARCHAR(20) | "breakfast", "lunch", "dinner", "snack" |
| explanation | TEXT | Claude's plain-English reason for this pick |
| accepted | BOOLEAN | True if user accepted, False if rejected, NULL if pending |
| rejection_reason_id | INT FK | FK to rejection_reasons (nullable) |
| rejection_reason_text | TEXT | Free text if user typed a new Other reason |
| created_at | DATETIME | |

---

## 6. Claude API Integration

### 6.1 Recipe Extraction (UC-03, UC-04) — updated

**dish_type added to JSON schema:**
```json
{
  "name": "...",
  "cuisine": "...",
  "dish_type": "Main",
  "protein": "...",
  "prep_time_mins": 15,
  "cook_time_mins": 30,
  "prep_ahead": false,
  "notes": "...",
  "ingredients": [...],
  "steps": [...]
}
```

**System prompt addition:**
> Set `dish_type` to one of: Breakfast, Starter, Main, Side, Dessert, Snack, Other. Use "Main" for primary dinner/lunch dishes. Use "Starter" for appetisers and soups served before a main. Use "Side" for accompaniments not eaten alone. Use "Other" if unclear.

All other extraction parameters unchanged (model: `claude-sonnet-4-6`, max_tokens: 4096).

### 6.2 Ingredient Categorization (UC-10)

*(unchanged from v1.2)*

### 6.3 Prep-Ahead Detection (UC-12)

*(unchanged from v1.2)*

### 6.4 Duplicate Detection (UC-11)

*(unchanged from v1.2)*

### 6.5 AI Meal Planning (UC-16) — NEW

**File:** `app/services/ai_planner.py`

**Input to Claude:**
```json
{
  "scope": "week",
  "composition": "mains_only",
  "criteria": ["most_beloved", "varied_cuisine"],
  "recipes": [
    {
      "id": 5,
      "name": "Garlic Prawns",
      "cuisine": "Italian",
      "dish_type": "Main",
      "protein": "Seafood",
      "prep_ahead": false,
      "wishlist": false,
      "cook_count": 3,
      "avg_rating": 4.7,
      "last_cooked": "2026-06-10"
    },
    ...
  ],
  "slots_needed": [
    {"day": 0, "slot": "dinner"},
    {"day": 1, "slot": "dinner"},
    ...
  ]
}
```

**Output from Claude (JSON):**
```json
{
  "suggestions": [
    {
      "day_of_week": 0,
      "meal_slot": "dinner",
      "recipe_id": 5,
      "recipe_name": "Garlic Prawns",
      "explanation": "Highest rated recipe you haven't made in over two weeks — a reliable crowd-pleaser to start the week."
    },
    ...
  ]
}
```

**Model:** `claude-sonnet-4-6`
**max_tokens:** 2048 (structured JSON output, smaller than extraction)
**System prompt:** Instructs Claude to act as a meal planner, select only from the provided recipe list, apply the specified criteria, and return valid JSON only — no preamble or markdown fences.

**Failure mode:** If Claude returns unparseable JSON, flash an error and return user to the planning form. Do not partially save suggestions.

---

## 6.6 Cook Log Routes (UC-08, UC-15)

### Wishlist Un-Flag Prompt (UC-08 enhancement)

After `POST /recipes/<id>/cook` creates a cook log entry, if `recipe.wishlist == True`:
- Redirect to a lightweight confirmation page (or use a query param on the detail page) asking "This was on your wishlist — remove it from wishlist?"
- `POST /recipes/<id>/unwishlist` — sets `wishlist = False`, redirects to detail page
- "Keep on wishlist" link — redirects to detail page without change

Alternatively implement as a flash message + inline form on the detail page to avoid an extra route — implementation decision at build time.

---

## 7. Routes Summary

### New routes (v1.3)

| Blueprint | Method | Path | Description |
|-----------|--------|------|-------------|
| `ai_plan` | GET | `/ai-plan/` | Planning scope/criteria form |
| `ai_plan` | POST | `/ai-plan/suggest` | Call Claude, render suggestions |
| `ai_plan` | POST | `/ai-plan/accept/<suggestion_id>` | Accept suggestion → write to meal plan |
| `ai_plan` | POST | `/ai-plan/reject/<suggestion_id>` | Reject suggestion → record reason |
| `recipe_links` | POST | `/recipes/<id>/links/add` | Add a link between two recipes |
| `recipe_links` | POST | `/recipe-links/<link_id>/remove` | Remove a link |
| `recipes` | POST | `/recipes/<id>/unwishlist` | Remove wishlist flag after cook |
| `admin` | GET/POST | `/admin/dish-types/add` | Add a dish type |
| `admin` | GET/POST | `/admin/rejection-reasons/add` | Add a rejection reason |

### NGINX — new location blocks needed

`/ai-plan/` is a new secondary prefix on `recipes-app`. Must be added to **both** `prod.conf` and `000-bareip.conf` per the Bare-IP Parity Standard:

```nginx
location /ai-plan/ {
    include conf.d/security-headers.conf;
    proxy_pass http://recipes-app:5000;
    proxy_http_version 1.1;
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
    add_header X-Upstream recipes-app;
}
```

> **120s timeout:** Claude API calls for meal planning may take several seconds, especially for a full week plan across a large recipe library. Match the BIS timeout pattern.

`/recipe-links/` is also a new secondary prefix — same pattern, standard 60s timeout is fine.

---

## 8. DB Migrations Required (v1.3)

Run on live server before deploying code that uses these tables:

```sql
-- 1. dish_type column on recipes
ALTER TABLE recipes ADD COLUMN dish_type VARCHAR(100) NULL AFTER cuisine;

-- 2. dish_types picklist table
CREATE TABLE dish_types (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL UNIQUE
);
INSERT INTO dish_types (name) VALUES
  ('Breakfast'),('Dessert'),('Main'),('Side'),('Snack'),('Starter'),('Other');

-- 3. recipe_links table
CREATE TABLE recipe_links (
  id INT PRIMARY KEY AUTO_INCREMENT,
  recipe_id INT NOT NULL,
  linked_recipe_id INT NOT NULL,
  notes TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
  FOREIGN KEY (linked_recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
  UNIQUE KEY uq_link_pair (
    (LEAST(recipe_id, linked_recipe_id)),
    (GREATEST(recipe_id, linked_recipe_id))
  )
);

-- 4. rejection_reasons table
CREATE TABLE rejection_reasons (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL UNIQUE
);
INSERT INTO rejection_reasons (name) VALUES
  ('Already planned recently'),('Missing ingredients'),('Not in the mood'),
  ('Too complex'),('Wrong cuisine'),('Other');

-- 5. ai_suggestions table
CREATE TABLE ai_suggestions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  recipe_id INT NOT NULL,
  meal_plan_id INT NULL,
  scope VARCHAR(20) NOT NULL,
  composition VARCHAR(20) NOT NULL,
  criteria TEXT NOT NULL,
  day_of_week TINYINT NULL,
  meal_slot VARCHAR(20) NULL,
  explanation TEXT,
  accepted BOOLEAN NULL,
  rejection_reason_id INT NULL,
  rejection_reason_text TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
  FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE SET NULL,
  FOREIGN KEY (rejection_reason_id) REFERENCES rejection_reasons(id) ON DELETE SET NULL
);
```

Also update `database/init.sql` with all new tables so fresh installs are consistent.

---

## 9. PR Plan (updated)

| Repo | PR | Status | What |
|------|----|--------|------|
| `recipes` | #28 | ✅ Done | Fix shopping list ingredient aggregation |
| `recipes` | #29 | ✅ Done | Dynamic cuisine list from DB + admin page |
| `recipes` | #7 | Planned | dish_type field — DB migration, extractor schema, model, routes, templates, admin section |
| `recipes` | #8 | Planned | AI meal planning (UC-16) — ai_planner service, ai_plan routes, templates, NGINX blocks, rejection_reasons table, ai_suggestions table |
| `recipes` | #9 | Planned | Recipe linking (UC-17) — recipe_links table, recipe_links routes, detail + form template updates |
| `recipes` | #10 | Planned | Wishlist un-flag prompt (UC-08 enhancement) |
| `recipes` | #11 | Planned | 6 cookbook recipe manual entries (data, not code) |
| `InternalWebServer` | — | Planned (with PR #8) | Add /ai-plan/ and /recipe-links/ location blocks to prod.conf + 000-bareip.conf |

---

## 10. Lessons Learned

*(unchanged from v1.2 — see § 10 in previous version)*

---

## 11. Open Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should the weekly meal plan support multiple meals per day (lunch + dinner)? | Already supported by meal_slot — UI decision only |
| 2 | Should uploaded documents be stored permanently or discarded after extraction? | Storage volume sizing |
| 3 | Should the shopping list be exportable via email? | Additional routes needed |
| 4 | Should recipe-level rating be derived from CookLog average, or a separate field? | Deferred until CookLog is in active use |
| 5 | Should the wishlist un-flag prompt appear after every cook, or only the first cook? | Currently spec'd as first cook only (wishlist=true check) — naturally stops after first un-flag |
| 6 | For AI planning full-meals mode, should Claude pick starter + main + dessert as a set, or allow user to accept/reject each component independently? | UX decision at build time |
