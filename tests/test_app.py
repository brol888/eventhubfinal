import pytest
from app import app, db
from models import User, Event
from werkzeug.security import generate_password_hash
from datetime import datetime


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()



def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_login(client):
    with app.app_context():
        user = User(name="Test User", email="test@example.com", password=generate_password_hash("password123"))
        db.session.add(user)
        db.session.commit()

    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Logout" in response.data



def test_cannot_edit_others_event(client):
    with app.app_context():
        user_a = User(name="User A", email="a@example.com", password=generate_password_hash("password123"))
        user_b = User(name="User B", email="b@example.com", password=generate_password_hash("password123"))
        db.session.add_all([user_a, user_b])
        db.session.commit()

        event = Event(
            title="User A's Event",
            short_description="short",
            full_description="full",
            location="Tbilisi",
            event_date=datetime(2026, 12, 1, 18, 0),
            ticket_price=10.0,
            organizer="User A",
            category="Music",
            user_id=user_a.id
        )
        db.session.add(event)
        db.session.commit()
        event_id = event.id

    client.post("/login", data={"email": "b@example.com", "password": "password123"})

    response = client.get(f"/event/{event_id}/edit")

    assert response.status_code == 403