# Business Requirements Document
## MitchellNET Recipes App (Item 15)

**Version:** 1.1  
**Date:** June 18, 2026  
**Author:** MitchellNET  
**Status:** Active — PR #3 complete, PR #4 in progress

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | June 16, 2026 | Initial draft |
| 1.1 | June 18, 2026 | Added UC-11 through UC-14 based on post-PR-#3 review; updated PR table; wishlist retention decision documented |

---

## 1. Background

The MitchellNET internal website currently hosts a static HTML page (`/recipes/recipes.html`) containing approximately 50 recipe links organized by source website, plus one local PDF and references to physical cookbook pages. This page has served as a quick-reference list but has significant limitations:

- No search or filtering capability
- Duplicate entries (same recipe appears multiple times)
- No metadata (cuisine, protein, prep time, rating)
- Requires HTML editing to add or update recipes
- Physical cookbook references mixed with web links, with no consistent structure
- No meal planning or shopping list capability
- No record of what has been cooked or how it was rated

This project extracts the recipes content from InternalWebServer into a dedicated, database-backed Flask application with a full web UI.

---

## 2. Users

| User | Description |
|------|-------------|
| Andrew | Primary user. Adds and manages recipes, plans meals, generates shopping lists. |
| Partner | Co-user. Browses recipes, contributes to meal planning, views shopping lists. |

Both users access the app from the home LAN only. No external access is required.

---

## 3. Use Cases

### UC-01 — Browse Recipes
**Actor:** Any user  
**Description:** User opens the app and sees all recipes. Can scroll, search, and filter the list.  
**Acceptance criteria:**
- All recipes visible in a clean list/card layout
- Filter by cuisine type and protein
- Each recipe shows: name, cuisine, protein, prep time
- Delete button available per recipe on the browse page
- Duplicates removed from migrated data

---

### UC-02 — View a Recipe
**Actor:** Any user  
**Description:** User clicks a recipe to see its full detail page.  
**Acceptance criteria:**
- Shows all stored metadata: name, source, cuisine, protein, prep time, cook time, notes
- Shows full ingredient list with quantities and categories
- Shows cooking steps
- Shows link back to original external source (opens in new tab)
- Shows cooking history (dates cooked, ratings, per-cook notes)
- Shows wishlist status with toggle
- Shows prep-ahead flag with manual override toggle

---

### UC-03 — Add a Recipe via URL
**Actor:** Andrew  
**Description:** Andrew pastes a URL into the app. The app fetches the page and uses AI (Claude API) to extract the recipe name, ingredients, steps, cuisine type, protein, prep time, and prep-ahead flag into structured fields. Andrew reviews, edits if needed, and saves.  
**Acceptance criteria:**
- URL input field accessible from recipe browse page
- App fetches and parses the URL server-side
- Loading indicator shown while fetch + extraction is in progress
- Claude API extracts structured recipe data from page content
- Claude attempts to detect if recipe requires day-before prep (e.g. marinating overnight, dough resting)
- Extracted data presented in an editable review form before saving
- Duplicate check run at review time — if a likely duplicate is found, user is warned and can choose to save anyway or discard
- Source URL stored and linked on the recipe detail page
- Loading indicator shown while save is in progress
- Handles fetch failures gracefully — falls back to manual entry form with error message

---

### UC-04 — Add a Recipe via Document Upload
**Actor:** Andrew  
**Description:** Andrew uploads a PDF or image of a recipe. The app uses Claude API to extract structured recipe data. Andrew reviews, edits if needed, and saves.  
**Acceptance criteria:**
- File upload accepts PDF and common image formats (JPG, PNG, WebP, GIF)
- Loading indicator shown while extraction is in progress
- Claude API extracts structured recipe data from document content
- Claude attempts to detect prep-ahead requirement
- Extracted data presented in an editable review form before saving
- Duplicate check run at review time
- Source noted as "Uploaded document" with filename stored
- Existing `porkStroganoff.pdf` migrated using this flow

---

### UC-05 — Add a Recipe Manually
**Actor:** Andrew  
**Description:** Andrew fills in a form directly to add a recipe (for cookbook references or recipes with no URL/document).  
**Acceptance criteria:**
- Form fields: name, source description, source URL (optional), cuisine, protein, prep time, cook time, ingredients (list), steps (list), notes, prep-ahead flag
- Cookbook references can be entered as: source = "Nagi cookbook", notes = "Page 39 — Bizarrely good chicken wings"
- All fields except name are optional

---

### UC-06 — Edit a Recipe
**Actor:** Andrew  
**Description:** Andrew edits any field of an existing recipe.  
**Acceptance criteria:**
- Edit form pre-populated with existing data
- All fields editable including prep-ahead flag
- Save updates the record; cancel discards changes

---

### UC-07 — Mark as Wishlist
**Actor:** Any user  
**Description:** User tags a recipe as "want to try someday."  
**Acceptance criteria:**
- Wishlist toggle on recipe detail page
- Wishlist filter on main browse page
- Wishlist status persists in database

> **Note (June 2026):** The wishlist feature is retained as-is. A 1–5 star rating system exists on CookLog entries (per cook session). A recipe-level overall rating derived from CookLog is deferred until CookLog is in active use and the right aggregation approach is clear.

---

### UC-08 — Record a Cook
**Actor:** Any user  
**Description:** After cooking a recipe, user records that it was made today and optionally rates it.  
**Acceptance criteria:**
- "We made this!" button on recipe detail page
- Records date cooked (defaults to today, editable)
- Optional rating: 1–5 stars
- Optional notes for that cook (e.g. "added more chilli next time")
- Cook history visible on recipe detail page (list of dates + ratings + notes)
- Most recent cook date shown on recipe detail page

---

### UC-09 — Meal Plan
**Actor:** Any user  
**Description:** User selects recipes for each day of the upcoming week to build a meal plan.  
**Acceptance criteria:**
- Weekly calendar view (Mon–Sun)
- Click to assign a recipe to a day
- Each day shows the assigned recipe name
- Meal plan persists (survives page reload)
- "Generate shopping list" button on meal plan page

---

### UC-10 — Generate Shopping List
**Actor:** Any user  
**Description:** From a meal plan, user generates a combined shopping list for all recipes in the plan.  
**Acceptance criteria:**
- Shopping list combines ingredients across all planned recipes
- Duplicate ingredients aggregated (e.g. "garlic: 6 cloves" not "garlic: 2 cloves" × 3)
- List grouped by category (Produce, Meat, Seafood, Dairy, Grains & Pasta, Canned & Jarred, Condiments & Sauces, Spices & Seasonings, Baking, Oils & Vinegars, Frozen, Beverages, Other)
- Printable / copyable view

---

### UC-11 — Duplicate Detection at Import
**Actor:** Andrew  
**Description:** When a recipe is imported (URL or document), the app checks whether a recipe with the same or similar name already exists before saving.  
**Acceptance criteria:**
- Exact name match always flagged as duplicate
- Fuzzy name match (e.g. "Garlic Prawns" vs "Garlic Prawns (Shrimp)") flagged as likely duplicate
- Warning shown on the review page before save — includes the name of the matching recipe and a link to it
- User can choose to save anyway (if the duplicate is intentional) or discard
- Does not block save — user decision is final

---

### UC-12 — Prep-Ahead Flag
**Actor:** Andrew / Claude  
**Description:** Recipes that require work the day before (overnight marinating, resting dough, soaking, etc.) are flagged so users know to plan ahead.  
**Acceptance criteria:**
- Claude attempts to detect prep-ahead requirement during import and sets the flag automatically
- Flag shown clearly on recipe detail page and browse list
- User can manually toggle the flag on the review form and on the edit form
- Flag persists in database

---

### UC-13 — Loading Indicators During AI Operations
**Actor:** Any user  
**Description:** When the app is waiting for Claude API responses (URL extraction, document extraction) or saving a recipe, a loading indicator is shown so the user knows the app is working.  
**Acceptance criteria:**
- "Extracting recipe…" indicator shown from form submit until review page loads
- "Saving…" indicator shown from save submit until redirect to recipe detail
- Indicator disappears automatically on completion or error
- No JavaScript frameworks required — vanilla JS acceptable

---

### UC-14 — Delete Recipe
**Actor:** Andrew  
**Description:** Andrew can delete a recipe from the browse page.  
**Acceptance criteria:**
- Delete button visible per recipe on the browse page
- Confirmation required before delete (browser confirm dialog is acceptable)
- Recipe and all related records (ingredients, steps, cook logs) deleted via cascade
- User returned to browse page after delete

---

## 4. Data to Migrate

The following data from the existing static page must be migrated into the database at launch:

- All ~50 recipe links from `recipes.html` (de-duplicated)
- Physical cookbook references (Nagi cookbook pages)
- `porkStroganoff.pdf` — import via UC-04 document upload flow

Migration will be done via a one-time seed script run at deploy time.

---

## 5. Non-Functional Requirements

| Requirement | Detail |
|-------------|--------|
| Access | LAN-only (`https://mitchellnet.local/recipes/`) |
| Authentication | No per-user login — household access, same as fitness-tracker |
| Performance | Page load < 2s for recipe list up to 500 recipes |
| Availability | `restart: unless-stopped` — survives server reboots |
| Data safety | MariaDB volume backed up via existing server backup process |
| API key security | Claude API key stored in server `.env`, never in git |

---

## 6. Out of Scope

- External internet access
- Per-user accounts or login
- Nutrition tracking or calorie counting
- Integration with grocery delivery services
- Mobile app (browser on phone over LAN is sufficient)
- Recipe sharing or social features
- Recipe-level aggregate rating derived from CookLog (deferred — see UC-07 note)

---

## 7. Success Criteria

- All existing recipes migrated and accessible in the new app
- No duplicate recipes in the database
- URL import works for RecipeTin Eats and at least 3 other sources
- Meal plan + shopping list flow works end to end
- Cook history and ratings persist correctly
- Prep-ahead flag correctly detected for at least 80% of recipes where it applies
- Partner can use the app without any instruction
