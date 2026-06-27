# High Level Architecture
## MitchellNET Recipes App (Item 15)

**Version:** 1.5
**Date:** June 27, 2026
**Status:** Active — PRs #1–#9 complete; cookbook manual entries (PR #10) pending build

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | June 16, 2026 | Initial draft |
| 1.1 | June 18, 2026 | Updated data model for prep_ahead flag; categorizer bug fix; Claude API lessons learned; updated PR table |
| 1.2 | June 22, 2026 | Added cook log routes, templates, and query helpers (UC-15) |
| 1.3 | June 23, 2026 | Added dish_type field; UC-16 AI Meal Planning; UC-17 Recipe Linking; admin extended; wishlist un-flag prompt in cook log flow; extractor schema updated |
| 1.4 | June 26, 2026 | UC-16 complete (PR #32); UC-19 Help page complete (PR #33); nav links added (PRs #34–#35); directory structure corrected; routes table updated; DB migrations updated; NGINX blocks marked complete |
| 1.5 | June 27, 2026 | UC-17 Recipe Linking complete (PR #8 — recipe_links table live, RecipeLink model, recipe_links blueprint, linked recipes card on detail page); UC-08 wishlist prompt complete (PR #9 — wishlist_prompt routes + template); routes table updated; DB state updated; PR plan updated |

---

## 1. Overview

The Recipes app is a Flask + MariaDB web application deployed as a Docker service on the MitchellNET server. It follows the `python-flask-db` service type and mirrors the fitness-tracker architecture.

Accessible at `https://mitchellnet.local/recipes/` over the LAN. Uses Claude API for recipe extraction, ingredient categorization, and AI meal planning.

---

## 2. System Context

```text
Browser (Mac/iPhone on LAN)
        │
        │ HTTPS :443
        ▼
   nginx-proxy
        │
        │ /recipes/  /meal-plan/  /shopping-list/  /ai-plan/  /recipe-links/
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

```text
recipes/
├── app/
│   ├── app.py               # App factory; registers all blueprints
│   ├── config/
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py      # RejectionReason, AiSuggestion models
│   │   ├── recipe.py        # Recipe, Ingredient, Step, CookLog, Cuisine, DishType, RecipeLink models
│   │   └── meal_plan.py     # MealPlan, MealPlanEntry models
│   ├── routes/
│   │   ├── recipes.py       # Browse, view, add, edit, delete, help
│   │   ├── cook_log.py      # Cook log CRUD + wishlist un-flag prompt (UC-08)
│   │   ├── import_.py       # URL import, document upload, save
│   │   ├── meal_plan.py     # Meal plan manual entry
│   │   ├── shopping.py      # Shopping list
│   │   ├── ai_plan.py       # AI meal planning (UC-16) ✅
│   │   ├── recipe_links.py  # Recipe linking (UC-17) ✅
│   │   └── admin.py         # Admin picklist management (Cuisines, Dish Types, Rejection Reasons)
│   ├── services/
│   │   ├── extractor.py     # Claude API — extraction (dish_type in schema)
│   │   ├── fetcher.py       # URL fetch + HTML cleaning
│   │   ├── categorizer.py   # Claude API — ingredient categorization
│   │   └── ai_planner.py    # Claude API — meal planning suggestions (UC-16) ✅
│   └── templates/
│       ├── base.html        # ? Help + ⚙ Admin links in header
│       ├── recipes/
│       │   ├── browse.html  # dish_type filter + Meal Plan / Shopping List nav links
│       │   ├── detail.html  # dish_type, linked recipes card (UC-17) ✅
│       │   ├── form.html    # dish_type dropdown
│       │   └── help.html    # Searchable help page (UC-19) ✅
│       ├── import/
│       │   ├── import.html
│       │   └── review.html  # dish_type dropdown
│       ├── cook_log/
│       │   ├── edit.html
│       │   └── wishlist_prompt.html  # Wishlist un-flag prompt (UC-08) ✅
│       ├── meal_plan/
│       │   └── view.html    # ← Recipes, Save Plan, 🛒 Shopping List, ✨ AI Suggest buttons
│       ├── shopping/
│       │   └── view.html    # ← Recipes, 📅 Meal Plan, ↓ Export .txt buttons
│       ├── ai_plan/         # UC-16 ✅
│       │   ├── suggest.html
│       │   └── review.html
│       └── admin/
│           └── index.html   # Cuisines + Dish Types + Rejection Reasons
├── database/
│   └── init.sql             # Full schema including all tables live as of 27 June 2026
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
Recipe ──< RecipeLink >── Recipe  (self-referential, bidirectional) ✅
Cuisine        (picklist)
DishType       (picklist)
RejectionReason (picklist)
AiSuggestion >── RejectionReason
```

### 5.2 Tables

**recipes**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| name | VARCHAR(255) | Required |
| source_name | VARCHAR(255) | |
| source_url | TEXT | |
| cuisine | VARCHAR(100) | Free text; guided by cuisines picklist |
| dish_type | VARCHAR(100) | e.g. "Main", "Starter"; guided by dish_types picklist |
| protein | VARCHAR(100) | |
| prep_time_mins | INT | |
| cook_time_mins | INT | |
| notes | TEXT | |
| wishlist | BOOLEAN | Default false |
| prep_ahead | BOOLEAN | Default false |
| prep_ahead_override | BOOLEAN | Default false |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**cuisines** *(live — 18 values)*

**dish_types** *(live — 7 values)*

**proteins** *(live — 7 values)*

**ingredients** *(unchanged)*

**steps** *(unchanged)*

**cook_logs** *(unchanged)*

**meal_plans** *(unchanged)*

**meal_plan_entries** *(unchanged)*

**rejection_reasons** *(live — PR #32 — 5 values seeded)*

**ai_suggestions** *(live — PR #32)*
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| recipe_id | INT FK | |
| meal_plan_id | INT FK | nullable |
| scope | VARCHAR(20) | "meal", "day", or "week" |
| composition | VARCHAR(20) | "mains_only" or "full_meals" |
| criteria | TEXT | JSON array |
| day_of_week | TINYINT | 0=Mon, 6=Sun |
| meal_slot | VARCHAR(20) | |
| explanation | TEXT | Claude's plain-English reason |
| accepted | BOOLEAN | NULL=pending |
| rejection_reason_id | INT FK | nullable |
| rejection_reason_text | TEXT | |
| created_at | DATETIME | |

**recipe_links** *(live — PR #8 — June 27, 2026)*
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| recipe_id | INT FK | One side of the link |
| linked_recipe_id | INT FK | Other side of the link |
| UNIQUE KEY | (recipe_id, linked_recipe_id) | Prevents duplicates |

> Bidirectionality: two rows stored per link pair (A→B and B→A). Adding a link writes both rows. Removing a link deletes both rows. The detail page queries `WHERE recipe_id=X` to get all links for a recipe.

---

## 6. Claude API Integration

### 6.1 Recipe Extraction (UC-03, UC-04)

**Model:** `claude-sonnet-4-6`, **max_tokens:** 4096

### 6.2 Ingredient Categorization (UC-10)

*(unchanged from v1.2)*

### 6.3 Prep-Ahead Detection (UC-12)

*(unchanged from v1.2)*

### 6.4 Duplicate Detection (UC-11)

*(unchanged from v1.2)*

### 6.5 AI Meal Planning (UC-16) ✅ Live — PR #32

**File:** `app/services/ai_planner.py`

**Model:** `claude-sonnet-4-6`, **max_tokens:** 2048

*(unchanged from v1.4)*

---

## 7. Routes Summary

### Current routes (v1.5)

| Blueprint | Method | Path | Description | Status |
|-----------|--------|------|-------------|--------|
| `recipes` | GET | `/` | Browse recipes | ✅ |
| `recipes` | GET | `/<id>` | Recipe detail | ✅ |
| `recipes` | GET/POST | `/add` | Add recipe manually | ✅ |
| `recipes` | GET/POST | `/<id>/edit` | Edit recipe | ✅ |
| `recipes` | POST | `/<id>/delete` | Delete recipe | ✅ |
| `recipes` | GET | `/help` | Help / user guide | ✅ PR #33 |
| `import_` | GET/POST | `/import` | URL import + document upload | ✅ |
| `cook_log` | POST | `/<id>/cook` | Record a cook | ✅ |
| `cook_log` | GET | `/<id>/wishlist-prompt` | Wishlist un-flag prompt page | ✅ PR #9 |
| `cook_log` | POST | `/<id>/wishlist-prompt` | Handle Yes/No response | ✅ PR #9 |
| `cook_log` | GET/POST | `/cook-log/<id>/edit` | Edit cook log entry | ✅ |
| `cook_log` | POST | `/cook-log/<id>/delete` | Delete cook log entry | ✅ |
| `meal_plan` | GET/POST | `/meal-plan/` | Weekly meal plan | ✅ |
| `shopping` | GET | `/shopping-list/` | Shopping list | ✅ |
| `ai_plan` | GET/POST | `/ai-plan/suggest` | AI planning form + generate | ✅ PR #32 |
| `ai_plan` | GET | `/ai-plan/review` | Review suggestions list | ✅ PR #32 |
| `ai_plan` | POST | `/ai-plan/accept/<id>` | Accept suggestion | ✅ PR #32 |
| `ai_plan` | POST | `/ai-plan/reject/<id>` | Reject suggestion | ✅ PR #32 |
| `recipe_links` | GET | `/recipe-links/<id>` | List links for a recipe (JSON) | ✅ PR #8 |
| `recipe_links` | POST | `/recipe-links/` | Add a link (bidirectional) | ✅ PR #8 |
| `recipe_links` | POST | `/recipe-links/<id>/delete` | Remove a link (bidirectional) | ✅ PR #8 |
| `admin` | GET | `/admin/` | Admin picklist management | ✅ |
| `admin` | POST | `/admin/cuisines/add` | Add cuisine | ✅ |
| `admin` | POST | `/admin/dish-types/add` | Add dish type | ✅ |
| `admin` | POST | `/admin/rejection-reasons/add` | Add rejection reason | ✅ PR #32 |

### NGINX location blocks

All blocks present in both `prod.conf` and `000-bareip.conf` per the Bare-IP Parity Standard:

| Prefix | Upstream | Trailing slash on proxy_pass | Status |
|--------|----------|------------------------------|--------|
| `/recipes/` | `recipes-app:5000` | Yes (Approach A) | ✅ |
| `/meal-plan/` | `recipes-app:5000` | No (multi-prefix) | ✅ |
| `/shopping-list/` | `recipes-app:5000` | No (multi-prefix) | ✅ |
| `/ai-plan/` | `recipes-app:5000` | No (multi-prefix) | ✅ PR #169 |
| `/recipe-links/` | `recipes-app:5000` | No (multi-prefix) | ✅ PR #169 |

---

## 8. DB State (as of 27 June 2026)

All tables are live on the server. `database/init.sql` reflects the full current schema. No outstanding migrations.

| Table | Status | Notes |
|-------|--------|-------|
| recipes | ✅ Live | |
| cuisines | ✅ Live | 18 values seeded, dynamic |
| dish_types | ✅ Live | 7 values seeded |
| proteins | ✅ Live | 7 values seeded |
| ingredients | ✅ Live | |
| steps | ✅ Live | |
| cook_logs | ✅ Live | |
| meal_plans | ✅ Live | |
| meal_plan_entries | ✅ Live | |
| rejection_reasons | ✅ Live | 5 values seeded (PR #32) |
| ai_suggestions | ✅ Live | (PR #32) |
| recipe_links | ✅ Live | (PR #8 — applied via docker exec June 27, 2026) |

---

## 9. PR Plan (updated)

| Repo | PR | Status | What |
|------|----|--------|------|
| `recipes` | #28 | ✅ Done | Fix shopping list ingredient aggregation |
| `recipes` | #29 | ✅ Done | Dynamic cuisine list from DB + admin page |
| `recipes` | #30 | ✅ Done | BRD/HLA updated to v1.3 |
| `recipes` | #31 | ✅ Done | dish_type field full stack |
| `recipes` | #32 | ✅ Done | AI meal planning (UC-16) — June 26, 2026 |
| `recipes` | #33 | ✅ Done | Searchable Help page (UC-19) — June 26, 2026 |
| `recipes` | #34 | ✅ Done | Meal Plan + Shopping List nav links — June 26, 2026 |
| `recipes` | #35 | ✅ Done | Recipes back link on Meal Plan and Shopping List pages — June 26, 2026 |
| `InternalWebServer` | #169 | ✅ Done | NGINX /ai-plan/ + /recipe-links/ blocks both vhosts — June 26, 2026 |
| `recipes` | #37 | ✅ Done | Recipe linking (UC-17) — June 27, 2026. main → ac46e20 |
| `recipes` | #38 | ✅ Done | Wishlist un-flag prompt (UC-08 enhancement) — June 27, 2026. main → 2245645 |
| `recipes` | #10 | 🔲 Planned | 6 cookbook recipe manual entries |

---

## 10. Lessons Learned

- Flask `url_for()` is prefix-unaware — always use hard-coded absolute paths for redirects
- Jinja2 templates must use `<a>` tags — Markdown-style links render as literal text
- Picklist dropdowns must use `{{ object.name }}` when values come from DB queries returning model objects
- VSCode Claude plugin can silently truncate large file overwrites — verify with `wc -l` and `head`/`tail`
- DB changes must go through `init.sql` and models in the repo, not directly on the server
- max_tokens for Claude API: use 4096 for extraction, 2048 for structured planning JSON
- The live DB does not automatically pick up new `CREATE TABLE IF NOT EXISTS` statements on redeploy when the DB container already exists — apply new tables via `docker exec` after the first deploy

---

## 11. Open Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should the weekly meal plan support multiple meals per day (lunch + dinner)? | Already supported by meal_slot — UI decision only |
| 2 | Should uploaded documents be stored permanently or discarded after extraction? | Storage volume sizing |
| 3 | Should the shopping list be exportable via email? | Additional routes needed |
| 4 | Should recipe-level rating be derived from CookLog average, or a separate field? | Deferred until CookLog is in active use |
| 5 | For AI planning full-meals mode, should Claude pick starter + main + dessert as a set, or allow user to accept/reject each component independently? | UX decision at build time |
