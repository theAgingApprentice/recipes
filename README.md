# recipes
MitchellNET Recipes app — Flask + MariaDB service for browsing, importing, and planning meals.
Accessible at `https://mitchellnet.local/recipes/` over the LAN.

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
Secondary prefixes (e.g. `/recipes/api/`) must use `proxy_pass` **without** a trailing slash so the full path is preserved:

```nginx
location /recipes/api/ {
    proxy_pass http://recipes-app:5000;  # no trailing slash — preserves /recipes/api/
}
```

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
