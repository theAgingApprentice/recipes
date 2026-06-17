# High Level Architecture
## MitchellNET Recipes App (Item 15)

**Version:** 1.0  
**Date:** June 16, 2026  
**Status:** Draft — pending BRD approval

---

## 1. Overview

The Recipes app is a Flask + MariaDB web application deployed as a Docker service on the MitchellNET server. It follows the `python-flask-db` service type established in `mitchellnet-infra/docs/SERVICE-TYPES.md` and mirrors the fitness-tracker architecture.

It is accessible at `https://mitchellnet.local/recipes/` over the LAN. The app uses the Claude API for AI-assisted recipe extraction from URLs and uploaded documents, and for shopping list ingredient categorization.

---

## 2. System Context

```
Browser (Mac/iPhone on LAN)
        │
        │ HTTPS :443
        ▼
   nginx-proxy  ──────────────────────────────────────────
        │                                                  │
        │ /recipes/                                        │ /fitness/, /api/bench/, etc.
        ▼                                                  ▼
  recipes-app:5000                              (other services unchanged)
  (Flask + Gunicorn)
        │
        │ TCP :3306
        ▼
  recipes-db (MariaDB)
        │
        ▼
  recipes_data (Docker volume)

  recipes-app also calls:
        │
        │ HTTPS
        ▼
  api.anthropic.com  (Claude API — recipe extraction, ingredient categorization)
```

---

## 3. Service Architecture

### 3.1 Repo

New repo: `recipes` (created via `aaNewService recipes --type python-flask-db`)

### 3.2 Containers

| Container | Image | Role |
|-----------|-------|------|
| `recipes-app` | Custom Flask image | Web app + API |
| `recipes-db` | `mariadb:11` | Relational data store |

### 3.3 Networks

| Network | Purpose |
|---------|---------|
| `mitchellnet` (external) | nginx-proxy → recipes-app |
| `recipes-internal` (bridge) | recipes-app → recipes-db only |

MariaDB is on the internal network only — never exposed to `mitchellnet`. This matches the fitness-tracker dual-network pattern.

### 3.4 Volumes

| Volume | Contents |
|--------|----------|
| `recipes_data` | MariaDB data files |
| `recipes_uploads` | Uploaded PDFs and images (mounted into recipes-app) |

### 3.5 Ports

No host ports exposed. All traffic via Docker network.

---

## 4. Application Architecture

### 4.1 Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12 |
| Web framework | Flask |
| WSGI server | Gunicorn |
| Database ORM | Flask-SQLAlchemy |
| Migrations | Flask-Migrate (Alembic) |
| HTTP client | requests (URL import) |
| PDF parsing | PyMuPDF (fitz) |
| AI extraction | Anthropic Python SDK |
| Frontend | Vanilla HTML/CSS/JS (Jinja2 templates) |

### 4.2 Directory Structure

```
recipes/
├── app/
│   ├── Dockerfile
│   ├── app.py               # Flask app init, blueprint registration
│   ├── config/
│   │   ├── database.py      # SQLAlchemy setup
│   │   └── settings.py      # Config from env vars
│   ├── models/
│   │   ├── recipe.py        # Recipe, Ingredient, Step models
│   │   ├── cook_log.py      # CookLog model
│   │   └── meal_plan.py     # MealPlan model
│   ├── routes/
│   │   ├── recipes.py       # Browse, view, add, edit routes
│   │   ├── import_.py       # URL import, document upload routes
│   │   ├── meal_plan.py     # Meal plan routes
│   │   └── shopping.py      # Shopping list routes
│   ├── services/
│   │   ├── extractor.py     # Claude API — recipe extraction from text
│   │   ├── fetcher.py       # URL fetch + HTML cleaning
│   │   └── categorizer.py   # Claude API — ingredient category assignment
│   ├── templates/
│   │   ├── base.html
│   │   ├── recipes/
│   │   │   ├── list.html
│   │   │   ├── detail.html
│   │   │   └── form.html
│   │   ├── import/
│   │   │   ├── url.html
│   │   │   └── upload.html
│   │   ├── meal_plan/
│   │   │   └── index.html
│   │   └── shopping/
│   │       └── list.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── database/
│   └── structure/
│       └── schema.sql       # Reference schema (Alembic manages migrations)
├── migrations/              # Flask-Migrate generated
├── seeds/
│   └── migrate_static.py   # One-time migration of existing recipes.html data
├── tests/
│   ├── test_health.py
│   ├── test_recipes.py
│   └── test_import.py
├── requirements.txt
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## 5. Data Model

### 5.1 Entity Relationship Summary

```
Recipe ──< Ingredient
Recipe ──< Step
Recipe ──< CookLog
Recipe ──< MealPlanEntry >── MealPlan
```

### 5.2 Tables

**recipes**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| name | VARCHAR(255) | Required |
| source_name | VARCHAR(255) | e.g. "RecipeTin Eats", "Nagi cookbook" |
| source_url | TEXT | External URL (nullable) |
| cuisine | VARCHAR(100) | e.g. "Thai", "Italian" |
| protein | VARCHAR(100) | e.g. "Chicken", "Beef", "Seafood" |
| prep_time_mins | INT | Nullable |
| cook_time_mins | INT | Nullable |
| notes | TEXT | Free text notes |
| wishlist | BOOLEAN | Default false |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**ingredients**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| recipe_id | INT FK | |
| name | VARCHAR(255) | e.g. "garlic" |
| quantity | VARCHAR(100) | e.g. "3 cloves" |
| category | VARCHAR(100) | e.g. "Produce", "Meat", "Pantry" |
| sort_order | INT | Display order |

**steps**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| recipe_id | INT FK | |
| step_number | INT | |
| instruction | TEXT | |

**cook_logs**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| recipe_id | INT FK | |
| cooked_on | DATE | |
| rating | TINYINT | 1–5, nullable |
| notes | TEXT | Per-cook notes, nullable |

**meal_plans**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| week_start | DATE | Monday of the planned week |
| created_at | DATETIME | |

**meal_plan_entries**
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| meal_plan_id | INT FK | |
| day_of_week | TINYINT | 0=Mon, 6=Sun |
| recipe_id | INT FK | |

---

## 6. Claude API Integration

### 6.1 Recipe Extraction (UC-03, UC-04)

**Input:** Raw HTML text (from URL fetch) or extracted PDF text  
**Output:** Structured JSON — name, ingredients list, steps list, cuisine, protein, prep time  
**Model:** `claude-sonnet-4-6`  
**When called:** On URL import or document upload, before showing the review form  
**Failure mode:** If extraction fails or returns incomplete data, user is shown a blank manual entry form with a warning

### 6.2 Ingredient Categorization (UC-10)

**Input:** List of ingredient names  
**Output:** Each ingredient assigned a category (Produce, Meat, Seafood, Dairy, Pantry, Spices, Other)  
**When called:** At shopping list generation time, for any ingredient not already categorized  
**Caching:** Category stored in the `ingredients` table — only uncategorized ingredients call the API

### 6.3 API Key

Stored in `~/services/recipes/.env` as `ANTHROPIC_API_KEY`. Never committed to git.

---

## 7. NGINX Integration

Add location block to `InternalWebServer/nginx/conf.d/prod.conf` and `000-bareip.conf`:

```nginx
location /recipes/ {
    include conf.d/security-headers.conf;
    proxy_pass http://recipes-app:5000/;
    proxy_http_version 1.1;
    add_header X-Upstream recipes-app;
}
```

Note: trailing slash on `proxy_pass` per MitchellNET NGINX pattern (strips `/recipes/` prefix before forwarding to Flask).

---

## 8. Migration Plan

A one-time seed script (`seeds/migrate_static.py`) will:

1. Parse all links from the existing `recipes.html`
2. De-duplicate entries (same URL appearing multiple times)
3. Insert each as a `Recipe` record with `source_url` and `name` populated
4. Set `cuisine`, `protein`, `prep_time_mins` to NULL (to be filled in over time via edit)
5. Handle cookbook references as recipes with `source_url = NULL` and `notes` = page reference
6. Mark all migrated recipes with `wishlist = false`

The `porkStroganoff.pdf` will be imported manually via the document upload UI (UC-04) after launch.

The static `recipes.html` page in InternalWebServer will be removed in the same PR that adds the NGINX location block.

---

## 9. Deployment

Follows standard MitchellNET pattern:

- GitHub Actions self-hosted runner on the server
- On merge to `main`: build image, run tests, deploy via `docker compose up -d`
- Health check: `GET /api/health` → `{"status": "healthy", "database": "connected"}`
- Server-side `.env` at `~/services/recipes/.env`

---

## 10. Open Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should the weekly meal plan support multiple meals per day (lunch + dinner)? | Data model change if yes |
| 2 | Should uploaded documents be stored permanently or discarded after extraction? | Storage volume sizing |
| 3 | Should the shopping list be exportable (email, text file)? | Additional routes needed |
| 4 | Should cuisine and protein be free-text or constrained picklists? | UI complexity |

---

## 11. PRs Expected

| Repo | PR | What |
|------|----|------|
| `recipes` (new) | #1 | Initial scaffold — flask-db template, schema, README |
| `recipes` | #2 | Core models and browse/detail/add/edit routes |
| `recipes` | #3 | Claude API import (URL + document upload) |
| `recipes` | #4 | Meal plan + shopping list |
| `recipes` | #5 | Seed script + data migration |
| `InternalWebServer` | #158 | Add `/recipes/` location block, remove static recipes.html |
| `mitchellnet-infra` | #28 | ARCHITECTURE.md update |
