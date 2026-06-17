import pytest
from app import create_app
from config.database import db as _db
from models.recipe import Recipe, Ingredient, Step


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with application.app_context():
        _db.create_all()
    yield application
    with application.app_context():
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_recipe(app):
    with app.app_context():
        r = Recipe(name="Test Pasta", cuisine="Italian", protein="Chicken",
                   prep_time_mins=10, cook_time_mins=20)
        _db.session.add(r)
        _db.session.flush()
        _db.session.add(Ingredient(recipe_id=r.id, name="Pasta", quantity="200g",
                                   category="Dry goods", sort_order=0))
        _db.session.add(Step(recipe_id=r.id, step_number=1, instruction="Boil water"))
        _db.session.commit()
        return r.id


def test_browse_empty(client):
    resp = client.get("/recipes/")
    assert resp.status_code == 200


def test_browse_with_recipe(client, sample_recipe):
    resp = client.get("/recipes/")
    assert resp.status_code == 200
    assert b"Test Pasta" in resp.data


def test_browse_filter_cuisine(client, sample_recipe):
    resp = client.get("/recipes/?cuisine=Italian")
    assert resp.status_code == 200
    assert b"Test Pasta" in resp.data


def test_browse_filter_cuisine_no_match(client, sample_recipe):
    resp = client.get("/recipes/?cuisine=Mexican")
    assert resp.status_code == 200
    assert b"Test Pasta" not in resp.data


def test_detail(client, sample_recipe):
    resp = client.get(f"/recipes/{sample_recipe}")
    assert resp.status_code == 200
    assert b"Test Pasta" in resp.data
    assert b"Pasta" in resp.data
    assert b"Boil water" in resp.data


def test_detail_not_found(client):
    resp = client.get("/99999")
    assert resp.status_code == 404


def test_add_get(client):
    resp = client.get("/recipes/add")
    assert resp.status_code == 200


def test_add_post(client):
    resp = client.post("/recipes/add", data={
        "name": "New Recipe",
        "cuisine": "Mexican",
        "protein": "Beef",
        "prep_time_mins": "15",
        "cook_time_mins": "30",
        "notes": "Test note",
        "ingredient_name": ["Tortilla"],
        "ingredient_quantity": ["2"],
        "ingredient_category": ["Bread"],
        "step_instruction": ["Heat pan"],
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"New Recipe" in resp.data


def test_edit_get(client, sample_recipe):
    resp = client.get(f"/recipes/{sample_recipe}/edit")
    assert resp.status_code == 200
    assert b"Test Pasta" in resp.data


def test_edit_post(client, sample_recipe):
    resp = client.post(f"/recipes/{sample_recipe}/edit", data={
        "name": "Updated Pasta",
        "cuisine": "Italian",
        "protein": "Chicken",
        "ingredient_name": ["Penne"],
        "ingredient_quantity": ["250g"],
        "ingredient_category": ["Dry goods"],
        "step_instruction": ["Boil salted water"],
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Updated Pasta" in resp.data


def test_delete(client, sample_recipe):
    resp = client.post(f"/recipes/{sample_recipe}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Test Pasta" not in resp.data


def test_api_list(client, sample_recipe):
    resp = client.get("/recipes/api/recipes")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert any(r["name"] == "Test Pasta" for r in data)


def test_api_detail(client, sample_recipe):
    resp = client.get(f"/recipes/api/recipes/{sample_recipe}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Test Pasta"
    assert data["cuisine"] == "Italian"
    assert len(data["ingredients"]) == 1
    assert len(data["steps"]) == 1
