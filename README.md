# recipes
MitchellNET Recipes app — Flask + MariaDB service for browsing, importing, and planning meals.
Accessible at `https://mitchellnet.local/recipes/` over the LAN.

## Features
- Browse, add, edit, and delete recipes
- Import recipes via URL or document upload (Claude AI extraction)
- Manual recipe entry
- Cuisine, protein, and dish type filtering
- Cook log — record cooks, ratings, and notes
- Prep-ahead flag (auto-detected by Claude, manually overridable)
- Wishlist — tag recipes to try later
- Weekly meal planning (manual and AI-assisted)
- AI meal planning — Claude suggests recipes based on criteria (most beloved, longest since last ate, varied cuisine, prep-ahead, from wishlist, surprise me)
- Shopping list — generated from meal plan, grouped by category, exportable as .txt
- Admin — manage cuisine, dish type, and rejection reason picklists
- Searchable help page at `/recipes/help`

## Docs
- [Business Requirements](docs/recipes-BRD.md)
- [High Level Architecture](docs/recipes-HLA.md)

## Development
See `mitchellnet-infra/docs/` for service type reference, framework guide, and runbook.

## Development Notes

### NGINX Routing — Approach A
This app uses Approach A: NGINX `proxy_pass` with a trailing slash strips the route prefix before forwarding to Flask, so Flask routes use simple paths without the `/recipes` prefix.

```nginx
location /recipes/ {
    proxy_pass http://recipes-app:5000/;  # trailing slash strips /recipes
}
```

Flask route example:
```python
@app.route("/")            # handles /recipes/
@app.route("/<int:id>")    # handles /recipes/<id>
```

### NGINX Multi-Prefix Exception
Secondary prefixes on the same Flask app must use `proxy_pass` **without** a trailing slash so the full path is preserved. Current secondary prefixes: `/meal-plan/`, `/shopping-list/`, `/ai-plan/`, `/recipe-links/`.

```nginx
location /ai-plan/ {
    proxy_pass http://recipes-app:5000;  # no trailing slash — preserves /ai-plan/
}
```

Every secondary prefix must be added to **both** `nginx/conf.d/prod.conf` and `nginx/conf.d/000-bareip.conf` per the Bare-IP Parity Standard.

### Flask `url_for()` is Prefix-Unaware
`url_for()` generates paths relative to Flask's own routing and does not know about the `/recipes` prefix NGINX adds. Never use `url_for()` for redirects — use hard-coded absolute paths instead:

```python
# Wrong — generates /1, not /recipes/1
return redirect(url_for("recipe_detail", id=r.id))

# Correct
return redirect(f"/recipes/{r.id}")
```

### Templates Must Use HTML Anchor Tags
Jinja2 templates served through this NGINX setup must use HTML `<a>` tags for links. Markdown-style links are not rendered:

```html
<!-- Correct -->
<a href="/recipes/{{ recipe.id }}">View Recipe</a>

<!-- Wrong — renders as literal text -->
[View Recipe](/recipes/{{ recipe.id }})
```

### Picklist Dropdowns — Use object.name
When a dropdown is populated from a DB query returning model objects, always use `{{ item.name }}` in the template — not `{{ item }}`, which renders the Python object repr:

```html
<!-- Correct -->
<option value="{{ c.name }}">{{ c.name }}</option>

<!-- Wrong — renders <Cuisine 'Italian'> -->
<option value="{{ c }}">{{ c }}</option>
```
