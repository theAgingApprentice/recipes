# High Level Architecture
## MitchellNET Recipes App (Item 15)

**Version:** 1.1
**Date:** June 18, 2026
**Status:** Active — PR #3 complete, PR #4 in progress

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | June 16, 2026 | Initial draft |
| 1.1 | June 18, 2026 | Updated data model for prep_ahead flag; documented categorizer bug fix; added Claude API lessons learned; updated PR table |

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

Repo: `recipes`

### 3.2 Containers

| Container | Image | Role |
|-----------|-------|------|
| `recipes-app` | Custom Flask image | Web app + API |
| `recipes-db` | `mariadb:11` | Relational data store |

### 3.3 Networks

| Network | Purpose |
|---------|---------|
| `mitchellnet` (external) | nginx-proxy to recipes-app |
| `recipes-internal` (bridge) | recipes-app to recipes-db only |

MariaDB is on the internal network only — never exposed to `mitchellnet`. This matches the fitness-tracker dual-network pattern.

### 3.4 Volumes

| Volume | Contents |
|--------|----------|
| `recipes_data` | MariaDB data files |

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
│   ├── app.py               # Flask app init, blueprint registration
│   ├── config/
│   │   └── database.py      # SQLAlchemy + Flask-Migrate setup
│   ├── models/
│   │   ├── recipe.py        # Recipe, Ingredient, Step, CookLog models
│   │   └── meal_plan.py     # MealPlan, MealPlanEntry models
│   ├── routes/
│   │   ├── recipes.py       # Browse, view, add, edit, delete routes
│   │   ├── import_.py       # URL import, document upload, save routes
│   │   ├── meal_plan.py     # Meal plan routes
│   │   └── shopping.py      # Shopping list routes
│   ├── services/
│   │   ├── extractor.py     # Claude API — recipe extraction from text/documents
│   │   ├── fetcher.py       # URL fetch + HTML cleaning
│   │   └── categorizer.py   # Claude API — ingredient category assignment
│   └── templates/
│       ├── base.html
│       ├── recipes/
│       │   ├── browse.html
│       │   ├── detail.html
│       │   └── form.html
│       ├── import/
│       │   ├── import.html
│       │   └── review.html
│       ├── meal_plan/
│       │   └── view.html
│       └── shopping/
│           └── view.html
├── database/
│   └── init.sql
├── migrations/              # Flask-Migrate generated
├── tests/
│   ├── test_health.py
│   └── test_recipes.py
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
| prep_ahead | BOOLEAN | Default false — Claude-detected or manually set |
| prep_ahead_override | BOOLEAN | Default false — true if user has manually set the flag |
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

**Input:** Cleaned plain text (from URL fetch) or base64-encoded PDF/image
**Output:** Structured JSON — name, ingredients list, steps list, cuisine, protein, prep time, cook time, notes, prep_ahead flag
**Model:** `claude-sonnet-4-6`
**max_tokens:** 4096 (1000 was too low for recipes with many ingredients — caused truncated JSON)
**When called:** On URL import or document upload, before showing the review form
**Failure mode:** If extraction fails or returns unparseable JSON, user is shown a flash error and returned to the import form

### 6.2 Ingredient Categorization (UC-10)

**Input:** List of `{sort_order, name}` dicts
**Output:** List of `{sort_order, category}` dicts
**Model:** `claude-sonnet-4-6`
**When called:** After recipe save, as a best-effort background step
**Caching:** Category stored in the `ingredients` table — only uncategorized ingredients need re-categorization
**Important:** Categorizer must use its own direct Anthropic API call with its own system prompt. It must NOT reuse `extractor.call_claude()` — that function uses the recipe extraction system prompt, which is wrong for categorization. Fixed in PR #4.

### 6.3 Prep-Ahead Detection (UC-12)

**Input:** Recipe text (same payload as extraction)
**Output:** Boolean `prep_ahead` field in the extraction JSON
**When called:** During extraction — the extractor system prompt instructs Claude to set `prep_ahead: true` if the recipe contains any overnight or day-before steps (marinating, dough resting, soaking, chilling)
**Override:** User can manually toggle on review form and edit form; override stored in `prep_ahead_override` column

### 6.4 Duplicate Detection (UC-11)

**Approach:** Python-only, no Claude API call needed
**Method:** On import, query all existing recipe names and compare using exact match (case-insensitive) and fuzzy match via `difflib.SequenceMatcher` — threshold 0.8 similarity flagged as likely duplicate
**When:** Check run server-side when review form is first rendered, before user saves
**Result:** Duplicate warning injected into review page if match found; user can save anyway or discard

### 6.5 API Key

Stored in `~/services/recipes/.env` as `ANTHROPIC_API_KEY`. Never committed to git.

---

## 7. NGINX Integration

Location block in `InternalWebServer/nginx/conf.d/prod.conf` and `000-bareip.conf`:

```nginx
location /recipes/ {
    proxy_pass http://recipes-app:5000/;
    proxy_http_version 1.1;
    add_header X-Upstream recipes-app;
}
```

Trailing slash on `proxy_pass` strips the `/recipes/` prefix before forwarding to Flask (Approach A). See `InternalWebServer/docs/nginx-routing.md` for full pattern documentation.

---

## 8. Migration Plan

A one-time seed script will:

1. Parse all links from the existing `recipes.html`
2. De-duplicate entries (same URL appearing multiple times)
3. Insert each as a `Recipe` record with `source_url` and `name` populated
4. Set `cuisine`, `protein`, `prep_time_mins` to NULL (to be filled in over time via edit)
5. Handle cookbook references as recipes with `source_url = NULL` and `notes` = page reference
6. Mark all migrated recipes with `wishlist = false`, `prep_ahead = false`

The `porkStroganoff.pdf` will be imported manually via the document upload UI after launch.

---

## 9. Deployment

Follows standard MitchellNET pattern:

- GitHub Actions self-hosted runner on the server
- On merge to `main`: build image, run tests, deploy via `docker compose up -d`
- Health check: `GET /api/health` returns `{"status": "healthy", "database": "connected"}`
- Server-side `.env` at `~/services/recipes/.env`

---

## 10. Lessons Learned

| # | Lesson | Detail |
|---|--------|--------|
| 1 | `max_tokens` must be generous | Set to 1000 initially — caused truncated JSON for recipes with many ingredients. Now 4096. |
| 2 | Do not share Claude API call functions across services with different system prompts | `categorizer.py` initially called `extractor.call_claude()`, which used the recipe extraction system prompt. Categorizer needs its own API call with its own system prompt. |
| 3 | `curl` smoke tests on server need `-k` flag | `mitchellnet.local` uses a self-signed cert. Always use `curl -sk` when testing HTTPS endpoints from the server itself. |

---

## 11. Open Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should the weekly meal plan support multiple meals per day (lunch + dinner)? | Data model change if yes |
| 2 | Should uploaded documents be stored permanently or discarded after extraction? | Storage volume sizing |
| 3 | Should the shopping list be exportable (email, text file)? | Additional routes needed |
| 4 | Should cuisine and protein be free-text or constrained picklists? | UI complexity |
| 5 | Should recipe-level rating be derived from CookLog average, or a separate field? | Deferred until CookLog is in active use |

---

## 12. PRs Completed / Planned

| Repo | PR | Status | What |
|------|----|--------|------|
| `recipes` | #1 | Done | Initial scaffold — flask-db template, schema, health check |
| `recipes` | #2 | Done | Core models and browse/detail/add/edit routes |
| `recipes` | #16 | Done | Claude API import (URL + document upload) |
| `recipes` | #17 | Done | Fix max_tokens 1000 to 4096 |
| `recipes` | #4 | Next | Loading indicators, delete, duplicate detection, prep-ahead flag, categorizer bug fix |
| `recipes` | #5 | Planned | Meal plan + shopping list |
| `recipes` | #6 | Planned | Seed script + data migration |
| `InternalWebServer` | — | Planned | Add /recipes/ location block, remove static recipes.html |
| `mitchellnet-infra` | — | Planned | ARCHITECTURE.md update |
