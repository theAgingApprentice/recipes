import pytest
from app.app import create_app


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_returns_200(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_returns_json(client):
    response = client.get("/api/health")
    data = response.get_json()
    assert "status" in data
