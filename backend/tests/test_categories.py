"""Tests for category listing, creation, and validation."""

def test_list_categories_defaults(client):
    """A fresh database contains exactly the 4 default categories, all marked is_default."""
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    data = resp.json()
    names = [c["name"] for c in data]
    assert "grocery" in names
    assert "medicine" in names
    assert "transportation" in names
    assert "miscellaneous" in names
    assert len(data) == 4
    for c in data:
        assert c["is_default"] is True


def test_create_category(client):
    """Creating a new category returns 201 with is_default=false."""
    resp = client.post("/api/categories", json={"name": "entertainment"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "entertainment"
    assert data["is_default"] is False


def test_create_category_duplicate(client):
    """Creating a category with an existing name (custom or default) returns 409."""
    client.post("/api/categories", json={"name": "entertainment"})
    resp = client.post("/api/categories", json={"name": "entertainment"})
    assert resp.status_code == 409


def test_create_category_duplicate_default(client):
    """Attempting to create a category that matches a default name returns 409."""
    resp = client.post("/api/categories", json={"name": "grocery"})
    assert resp.status_code == 409


def test_create_category_empty_name(client):
    """Pydantic validation rejects an empty category name with 422."""
    resp = client.post("/api/categories", json={"name": ""})
    assert resp.status_code == 422


def test_custom_category_appears_in_list(client):
    """After creation, the custom category appears in the unified list alongside defaults."""
    client.post("/api/categories", json={"name": "entertainment"})
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    names = [c["name"] for c in data]
    assert "entertainment" in names


def test_custom_category_usable_for_expense(client):
    """A newly created category can immediately be used when creating an expense."""
    client.post("/api/categories", json={"name": "pets"})
    resp = client.post("/api/expenses", json={
        "name": "Dog food",
        "notes": "",
        "category": "pets",
        "amount": 30.0,
        "date": "2026-06-15",
    })
    assert resp.status_code == 201


def test_create_category_whitespace_not_trimmed(client):
    """Leading/trailing whitespace in a category name is preserved (not trimmed),
    so ' entertainment ' is distinct from 'entertainment'."""
    client.post("/api/categories", json={"name": "entertainment"})
    resp = client.post("/api/categories", json={"name": " entertainment "})
    assert resp.status_code == 201
    # Both appear in the list as separate entries
    list_resp = client.get("/api/categories")
    names = [c["name"] for c in list_resp.json()]
    assert "entertainment" in names
    assert " entertainment " in names


def test_create_category_special_characters(client):
    """Categories can include special characters and emoji."""
    for name in ("café", "🍕", "home & garden"):
        resp = client.post("/api/categories", json={"name": name})
        assert resp.status_code == 201, f"Expected 201 for name '{name}'"


def test_create_category_name_max_length(client):
    """A category name exactly 100 characters is accepted."""
    resp = client.post("/api/categories", json={"name": "A" * 100})
    assert resp.status_code == 201


def test_create_category_name_too_long(client):
    """A category name over 100 characters is rejected with 422."""
    resp = client.post("/api/categories", json={"name": "A" * 101})
    assert resp.status_code == 422
