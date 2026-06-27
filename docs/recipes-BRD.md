# Business Requirements Document
## MitchellNET Recipes App (Item 15)

**Version:** 1.5
**Date:** June 27, 2026
**Author:** MitchellNET
**Status:** Active — PRs #1–#9 complete; cookbook manual entries (PR #10) pending build

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | June 16, 2026 | Initial draft |
| 1.1 | June 18, 2026 | Added UC-11 through UC-14; updated PR table; wishlist retention decision documented |
| 1.2 | June 22, 2026 | Added UC-15 Cook Log; updated UC-02 and UC-08 |
| 1.3 | June 23, 2026 | Added UC-16 AI Meal Planning, UC-17 Recipe Linking; added dish_type field; wishlist enhancement; admin extended with dish_types and rejection_reasons |
| 1.4 | June 26, 2026 | UC-16 AI Meal Planning marked complete; added UC-19 Help / User Guide; updated success criteria; PRs #32–#35 shipped |
| 1.5 | June 27, 2026 | UC-17 Recipe Linking marked complete (PR #8 — recipe_links table, RecipeLink model, bidirectional linked recipes card on detail page); UC-08 wishlist un-flag prompt marked complete (PR #9); success criteria updated |

---

## 1. Background

The MitchellNET internal website previously hosted a static HTML page (`/recipes/recipes.html`) containing approximately 50 recipe links. This project replaced it with a dedicated, database-backed Flask application with a full web UI.

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
**Status:** ✅ Complete
**Description:** User opens the app and sees all recipes. Can scroll, search, and filter the list.
**Acceptance criteria:**
- All recipes visible in a clean list/card layout
- Filter by cuisine type, protein, and dish type
- Each recipe shows: name, cuisine, protein, dish type, prep time
- Delete button available per recipe on the browse page
- Duplicates removed from migrated data

---

### UC-02 — View a Recipe
**Actor:** Any user
**Status:** ✅ Complete
**Description:** User clicks a recipe to see its full detail page.
**Acceptance criteria:**
- Shows all stored metadata: name, source, cuisine, protein, dish type, prep time, cook time, notes
- Shows full ingredient list with quantities and categories
- Shows cooking steps
- Shows link back to original external source (opens in new tab)
- Shows cook log summary (times made · average rating) at the top of the cook history section
- Shows full cook log history below the summary
- "We made this!" button visible on the detail page
- Shows wishlist status with toggle
- Shows prep-ahead flag with manual override toggle
- Shows dish type
- Shows linked recipes (if any) with clickable links to their detail pages

---

### UC-03 — Add a Recipe via URL
**Actor:** Andrew
**Status:** ✅ Complete
**Description:** Andrew pastes a URL into the app. The app fetches the page and uses Claude API to extract structured recipe data including dish type. Andrew reviews, edits if needed, and saves.
**Acceptance criteria:**
- Claude attempts to detect dish type (Main, Starter, Dessert, Side, Snack, Breakfast, Other)
- Dish type shown as editable dropdown on review form (values from dish_types table)
- Duplicate check run at review time

---

### UC-04 — Add a Recipe via Document Upload
**Actor:** Andrew
**Status:** ✅ Complete
**Description:** Andrew uploads a PDF or image of a recipe. Claude extracts structured data including dish type.
**Acceptance criteria:**
- Claude attempts to detect dish type
- Dish type shown as editable dropdown on review form

---

### UC-05 — Add a Recipe Manually
**Actor:** Andrew
**Status:** ✅ Complete
**Description:** Andrew fills in a form directly to add a recipe.
**Acceptance criteria:**
- Dish type field on form (dropdown from dish_types table, optional)

---

### UC-06 — Edit a Recipe
**Actor:** Andrew
**Status:** ✅ Complete
**Description:** Andrew edits any field of an existing recipe.
**Acceptance criteria:**
- Dish type editable on edit form

---

### UC-07 — Mark as Wishlist
**Actor:** Any user
**Status:** ✅ Complete
**Description:** User tags a recipe as "want to try someday."
**Acceptance criteria:**
- Wishlist toggle on recipe detail page
- Wishlist filter on main browse page
- Wishlist status persists in database
- Wishlist recipes available as a selection pool for AI meal planning (UC-16)

---

### UC-08 — Record a Cook (entry point)
**Actor:** Any user
**Status:** ✅ Complete (PR #9 — June 27, 2026)
**Description:** User confirms they are making (or have made) a recipe. Creates a new cook log entry. If the recipe is on the wishlist, user is prompted to remove the wishlist flag.
**Acceptance criteria:**
- "We made this!" button on the recipe detail page and on the browse page (per-recipe row)
- Pressing the button creates a new cook log entry with `cooked_on` defaulting to today
- No rating or notes required at this point
- If the recipe has `wishlist = true`, user is shown a prompt: "You made [recipe] — remove it from your wishlist?" with Yes / No options
- If Yes: `wishlist` set to false, entry saved, user returned to detail page
- If No: entry saved with wishlist flag unchanged, user returned to detail page
- Cook log summary updates immediately

---

### UC-09 — Meal Plan
**Actor:** Any user
**Status:** ✅ Complete
**Description:** User selects recipes for each day of the upcoming week to build a meal plan manually, or uses AI to suggest recipes (UC-16).
**Acceptance criteria:**
- Weekly calendar view (Mon–Sun) with meal slots (breakfast, lunch, dinner, snack)
- Click to assign a recipe to a day/slot manually
- Each slot shows the assigned recipe name
- Meal plan persists (survives page reload)
- "Generate shopping list" button on meal plan page
- "AI Suggest" button launches UC-16 flow

---

### UC-10 — Generate Shopping List
**Actor:** Any user
**Status:** ✅ Complete
**Description:** From a meal plan, user generates a combined shopping list for all recipes in the plan.
**Acceptance criteria:**
- Shopping list combines ingredients across all planned recipes
- Duplicate ingredients aggregated (quantities combined with +)
- List grouped by category
- Printable / copyable view
- Export as .txt

---

### UC-11 — Duplicate Detection at Import
**Status:** ✅ Complete
*(unchanged from v1.2)*

---

### UC-12 — Prep-Ahead Flag
**Status:** ✅ Complete
*(unchanged from v1.2)*

---

### UC-13 — Loading Indicators During AI Operations
**Status:** ✅ Complete
*(unchanged from v1.2)*

---

### UC-14 — Delete Recipe
**Status:** ✅ Complete
*(unchanged from v1.2)*

---

### UC-15 — Cook Log (view, edit, and delete)
**Status:** ✅ Complete
*(unchanged from v1.2)*

---

### UC-16 — AI Meal Planning
**Actor:** Any user
**Status:** ✅ Complete (PR #32 — June 26, 2026)
**Description:** User asks the app to suggest recipes for a meal, a day, or a week. The user specifies planning criteria. Claude selects recipes and explains each pick. The user accepts or rejects each suggestion from a reviewable list. Accepted suggestions populate the meal plan. All suggestions and accept/reject decisions are recorded for future learning.

**Planning scope options:**
- Single meal (one recipe for one slot)
- Full day (breakfast + lunch + dinner, optionally with snack)
- Full week (Mon–Sun, one or more slots per day)

**Meal composition options:**
- Mains only
- Full meals (starter + main + dessert per dinner slot)

**Selection criteria (user picks one or more):**
- Most beloved (highest average cook log rating)
- Longest since last ate (oldest `cooked_on` date or never cooked)
- Most varied cuisine (avoid repeating cuisines across the plan)
- Prep-ahead friendly (only recipes with `prep_ahead = false`, or user explicitly allows prep-ahead)
- From wishlist (draw only from recipes with `wishlist = true`)
- Surprise me (Claude picks freely with no constraint)

**Acceptance criteria:**
- "AI Suggest" button accessible from the meal plan page
- User selects scope, composition, and one or more criteria
- Claude returns a list of suggestions — each includes: recipe name, dish type, slot, and a plain-English explanation
- User can accept or reject each suggestion individually
- On reject: user selects from rejection reason dropdown; if Other selected, text input appears and new reason added to `rejection_reasons`
- Accepted suggestions written to the meal plan grid
- Every suggestion recorded in `ai_suggestions` table

---

### UC-17 — Recipe Linking
**Actor:** Andrew
**Status:** ✅ Complete (PR #8 — June 27, 2026)
**Description:** Andrew links two recipes that are intended to go together. Links are visible on both recipe detail pages and manageable from the detail page.

**Acceptance criteria:**

**Viewing links:**
- Recipe detail page shows a "Linked Recipes" section listing all linked recipes
- Each linked recipe name is a clickable link to its detail page
- "No linked recipes yet" shown when none exist

**Adding links (detail page):**
- Dropdown of all recipes (excluding current recipe) with a Link button
- On save: link created bidirectionally, list reloads without page refresh

**Removing links:**
- Remove button per link on detail page
- Confirmation required (browser confirm dialog)
- Removing a link removes it from both sides (bidirectional)

**Bidirectionality:**
- `recipe_links` table stores two rows per link pair (A→B and B→A)
- UNIQUE constraint on `(recipe_id, linked_recipe_id)` prevents duplicates
- Removing one link removes both rows

---

### UC-18 — Admin — Manage Picklists
**Actor:** Andrew
**Status:** ✅ Complete
**Description:** Admin page allows Andrew to manage the cuisine, dish type, and rejection reason picklists used throughout the app.

**Acceptance criteria:**
- Admin page at `/recipes/admin/` accessible via "⚙ Admin" link in every page header
- Three managed lists: Cuisines, Dish Types, Rejection Reasons
- Each list shows current values, with Other always last
- Each list has an "Add" form — new value added to DB on submit
- If the name already exists (case-insensitive), silently ignored (no duplicate)
- Rejection Reasons: when "Other" is selected during AI suggestion rejection (UC-16), the entered text is automatically added to this list for future use

---

### UC-19 — Help / User Guide
**Actor:** Any user
**Status:** ✅ Complete (PR #33 — June 26, 2026)
**Description:** A searchable help page is accessible from every page in the app, providing task-oriented guidance for all major features.

**Acceptance criteria:**
- Help page at `/recipes/help` accessible via "? Help" link in every page header
- 11 topic sections covering all major features
- Search box at top filters visible sections live as the user types (client-side JavaScript, no page reload)
- "No results" message shown when search matches nothing
- Each section uses plain task-oriented prose

---

## 4. Data to Migrate

*(unchanged — 44 of 48 URLs imported; 6 cookbook references still need manual entry via PR #10)*

---

## 5. Non-Functional Requirements

*(unchanged from v1.2)*

---

## 6. Out of Scope

- External internet access
- Per-user accounts or login
- Nutrition tracking or calorie counting
- Integration with grocery delivery services
- Mobile app (browser on phone over LAN is sufficient)
- Recipe sharing or social features
- Recipe-level aggregate rating derived from CookLog (deferred — pending CookLog usage review)

---

## 7. Success Criteria

- All existing recipes migrated and accessible in the new app ✅
- No duplicate recipes in the database ✅
- URL import works for RecipeTin Eats and at least 3 other sources ✅
- Meal plan + shopping list flow works end to end ✅
- Cook log entries can be created from both the detail page and the browse page ✅
- Cook log ratings and notes persist correctly and are editable after the fact ✅
- Cook summary (times made, average rating) displays correctly on detail and browse pages ✅
- Prep-ahead flag correctly detected for at least 80% of recipes where it applies ✅
- Dish type correctly detected by Claude for at least 80% of imported recipes ✅
- AI meal planning produces a suggestion set that the user accepts at least partially — pending full browser test
- Recipe links visible and manageable from detail page ✅
- Wishlist un-flag prompt appears correctly after cooking a wishlist recipe ✅
- Partner can use the app without any instruction ✅ (Help page live)
