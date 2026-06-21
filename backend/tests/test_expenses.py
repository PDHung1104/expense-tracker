"""Tests for expense CRUD, filtering, and sorting.

Each test uses the `client` fixture which provides an isolated temporary
database, so tests run independently and in any order.
"""

# ---- Create -------------------------------------------------------------

def test_create_expense(client):
    """Creating a valid expense returns 201 with all fields echoed back."""
    resp = client.post("/api/expenses", json={
        "name": "Milk",
        "notes": "2% from Costco",
        "category": "grocery",
        "amount": 5.49,
        "date": "2026-06-15",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == 1
    assert data["name"] == "Milk"
    assert data["notes"] == "2% from Costco"
    assert data["category"] == "grocery"
    assert data["amount"] == 5.49
    assert data["date"] == "2026-06-15"


def test_create_expense_invalid_category(client):
    """Creating an expense with a non-existent category returns 400."""
    resp = client.post("/api/expenses", json={
        "name": "PS5",
        "notes": "",
        "category": "entertainment",
        "amount": 499.99,
        "date": "2026-06-15",
    })
    assert resp.status_code == 400
    assert "does not exist" in resp.json()["detail"]


def test_create_expense_missing_name(client):
    """Pydantic validation rejects a missing required field with 422."""
    resp = client.post("/api/expenses", json={
        "notes": "",
        "category": "grocery",
        "amount": 5.0,
        "date": "2026-06-15",
    })
    assert resp.status_code == 422


def test_create_expense_negative_amount(client):
    """Pydantic Field(gt=0) rejects a negative amount with 422."""
    resp = client.post("/api/expenses", json={
        "name": "Refund",
        "notes": "",
        "category": "grocery",
        "amount": -10.0,
        "date": "2026-06-15",
    })
    assert resp.status_code == 422


def test_create_expense_invalid_date_format(client):
    """The date regex pattern rejects DD-MM-YYYY format (must be YYYY-MM-DD)."""
    resp = client.post("/api/expenses", json={
        "name": "Milk",
        "notes": "",
        "category": "grocery",
        "amount": 5.0,
        "date": "15-06-2026",
    })
    assert resp.status_code == 422


def test_create_expense_zero_amount(client):
    """Pydantic Field(gt=0) rejects amount=0 with 422."""
    resp = client.post("/api/expenses", json={
        "name": "Freebie",
        "notes": "",
        "category": "grocery",
        "amount": 0.0,
        "date": "2026-06-15",
    })
    assert resp.status_code == 422


def test_create_expense_impossible_date(client):
    """The date validator rejects dates that match the regex but aren't real
    calendar dates (e.g. Feb 30 or month 13)."""
    for bad_date in ("2026-02-30", "2026-13-01", "2025-02-29"):
        resp = client.post("/api/expenses", json={
            "name": "Test",
            "notes": "",
            "category": "grocery",
            "amount": 5.0,
            "date": bad_date,
        })
        assert resp.status_code == 422, f"Expected 422 for date '{bad_date}'"


def test_create_expense_name_max_length(client):
    """A name exactly 200 characters is accepted."""
    resp = client.post("/api/expenses", json={
        "name": "A" * 200,
        "notes": "",
        "category": "grocery",
        "amount": 5.0,
        "date": "2026-06-15",
    })
    assert resp.status_code == 201


def test_create_expense_name_too_long(client):
    """A name over 200 characters is rejected with 422."""
    resp = client.post("/api/expenses", json={
        "name": "A" * 201,
        "notes": "",
        "category": "grocery",
        "amount": 5.0,
        "date": "2026-06-15",
    })
    assert resp.status_code == 422


# ---- List / Filter / Sort -----------------------------------------------

def test_list_expenses_empty(client):
    """Listing expenses on a fresh database returns an empty array."""
    resp = client.get("/api/expenses")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_expenses_multiple(client):
    """Default list returns all expenses (newest first by default sort)."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    client.post("/api/expenses", json={
        "name": "Bus pass", "notes": "", "category": "transportation", "amount": 80.0, "date": "2026-06-01",
    })
    resp = client.get("/api/expenses")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_expenses_filter_by_category(client):
    """Filtering by category only returns expenses with that category."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    client.post("/api/expenses", json={
        "name": "Bus pass", "notes": "", "category": "transportation", "amount": 80.0, "date": "2026-06-01",
    })
    resp = client.get("/api/expenses?category=grocery")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Milk"


def test_list_expenses_filter_by_date_range(client):
    """date_from and date_to filter inclusively on the date column."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    client.post("/api/expenses", json={
        "name": "Rent", "notes": "", "category": "miscellaneous", "amount": 1200.0, "date": "2026-05-01",
    })
    resp = client.get("/api/expenses?date_from=2026-06-01&date_to=2026-06-30")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Milk"


def test_list_expenses_sort_by_date_asc(client):
    """Ascending date sort puts the oldest expense first."""
    client.post("/api/expenses", json={
        "name": "Later", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-20",
    })
    client.post("/api/expenses", json={
        "name": "Earlier", "notes": "", "category": "grocery", "amount": 3.0, "date": "2026-06-01",
    })
    resp = client.get("/api/expenses?sort_by=date&order=asc")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["name"] == "Earlier"
    assert data[1]["name"] == "Later"


def test_list_expenses_sort_by_amount_desc(client):
    """Descending amount sort puts the most expensive expense first."""
    client.post("/api/expenses", json={
        "name": "Cheap", "notes": "", "category": "grocery", "amount": 1.0, "date": "2026-06-15",
    })
    client.post("/api/expenses", json={
        "name": "Expensive", "notes": "", "category": "grocery", "amount": 999.0, "date": "2026-06-15",
    })
    resp = client.get("/api/expenses?sort_by=amount&order=desc")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["name"] == "Expensive"
    assert data[1]["name"] == "Cheap"


def test_list_expenses_sort_by_category_asc(client):
    """Ascending category sort returns items alphabetically by category name."""
    client.post("/api/expenses", json={
        "name": "Bus", "notes": "", "category": "transportation", "amount": 5.0, "date": "2026-06-15",
    })
    client.post("/api/expenses", json={
        "name": "Apple", "notes": "", "category": "grocery", "amount": 1.0, "date": "2026-06-15",
    })
    resp = client.get("/api/expenses?sort_by=category&order=asc")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["category"] == "grocery"
    assert data[1]["category"] == "transportation"


def test_list_expenses_invalid_sort_by(client):
    """An invalid sort field is rejected with 400 (prevented from reaching SQL)."""
    resp = client.get("/api/expenses?sort_by=nonexistent")
    assert resp.status_code == 400


def test_list_expenses_invalid_order(client):
    """An invalid sort order is rejected with 400."""
    resp = client.get("/api/expenses?order=sideways")
    assert resp.status_code == 400


def test_list_expenses_filter_by_nonexistent_category(client):
    """Filtering by a category that doesn't exist returns an empty list, not an error."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    resp = client.get("/api/expenses?category=nonexistent")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_expenses_filter_date_from_only(client):
    """date_from without date_to acts as a lower-bound filter."""
    client.post("/api/expenses", json={
        "name": "Early", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-01-01",
    })
    client.post("/api/expenses", json={
        "name": "Late", "notes": "", "category": "grocery", "amount": 10.0, "date": "2026-12-31",
    })
    resp = client.get("/api/expenses?date_from=2026-07-01")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Late"


def test_list_expenses_filter_date_to_only(client):
    """date_to without date_from acts as an upper-bound filter."""
    client.post("/api/expenses", json={
        "name": "Early", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-01-01",
    })
    client.post("/api/expenses", json={
        "name": "Late", "notes": "", "category": "grocery", "amount": 10.0, "date": "2026-12-31",
    })
    resp = client.get("/api/expenses?date_to=2026-06-30")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Early"


def test_list_expenses_default_sort_order(client):
    """When no sort params are given, expenses are sorted by date descending (newest first)."""
    client.post("/api/expenses", json={
        "name": "Old", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-01-01",
    })
    client.post("/api/expenses", json={
        "name": "New", "notes": "", "category": "grocery", "amount": 10.0, "date": "2026-12-31",
    })
    resp = client.get("/api/expenses")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["name"] == "New"
    assert data[1]["name"] == "Old"


def test_list_expenses_sort_by_date_desc(client):
    """Explicit descending date sort puts the newest expense first."""
    client.post("/api/expenses", json={
        "name": "Old", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-01-01",
    })
    client.post("/api/expenses", json={
        "name": "New", "notes": "", "category": "grocery", "amount": 10.0, "date": "2026-12-31",
    })
    resp = client.get("/api/expenses?sort_by=date&order=desc")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["name"] == "New"
    assert data[1]["name"] == "Old"


def test_list_expenses_combo_filter(client):
    """Category and date range filters can be combined (AND-ed)."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    client.post("/api/expenses", json={
        "name": "Rent", "notes": "", "category": "miscellaneous", "amount": 1200.0, "date": "2026-06-01",
    })
    client.post("/api/expenses", json={
        "name": "Old grocery", "notes": "", "category": "grocery", "amount": 3.0, "date": "2026-01-01",
    })
    resp = client.get("/api/expenses?category=grocery&date_from=2026-06-01&date_to=2026-06-30")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Milk"


# ---- Update -------------------------------------------------------------

def test_update_expense(client):
    """Partial update changes only the fields sent in the request."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    resp = client.put("/api/expenses/1", json={
        "name": "Organic Milk",
        "amount": 6.99,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Organic Milk"
    assert data["amount"] == 6.99
    assert data["category"] == "grocery"  # unchanged
    assert data["notes"] == ""  # unchanged


def test_update_expense_not_found(client):
    """Updating a non-existent expense returns 404."""
    resp = client.put("/api/expenses/999", json={"name": "Nope"})
    assert resp.status_code == 404


def test_update_expense_change_category(client):
    """Changing an expense's category to a valid one succeeds."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    resp = client.put("/api/expenses/1", json={"category": "medicine"})
    assert resp.status_code == 200
    assert resp.json()["category"] == "medicine"


def test_update_expense_to_invalid_category(client):
    """Changing to a non-existent category is rejected with 400."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    resp = client.put("/api/expenses/1", json={"category": "doesnotexist"})
    assert resp.status_code == 400


def test_update_expense_empty_body(client):
    """An empty update body returns the existing record unchanged (200)."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    resp = client.put("/api/expenses/1", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Milk"
    assert data["amount"] == 5.0


def test_update_expense_zero_amount(client):
    """Updating amount to zero is rejected with 422 (gt=0)."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    resp = client.put("/api/expenses/1", json={"amount": 0.0})
    assert resp.status_code == 422


def test_update_expense_empty_name(client):
    """Updating name to empty string is rejected with 422 (min_length=1)."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    resp = client.put("/api/expenses/1", json={"name": ""})
    assert resp.status_code == 422


def test_update_expense_invalid_date(client):
    """Updating date to an impossible date is rejected with 422."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    resp = client.put("/api/expenses/1", json={"date": "2026-02-30"})
    assert resp.status_code == 422


# ---- Delete -------------------------------------------------------------

def test_delete_expense(client):
    """Deleting an expense returns 204 and removes it from the database."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    resp = client.delete("/api/expenses/1")
    assert resp.status_code == 204
    # Verify it's gone
    list_resp = client.get("/api/expenses")
    assert list_resp.json() == []


def test_delete_expense_not_found(client):
    """Deleting a non-existent expense returns 404."""
    resp = client.delete("/api/expenses/999")
    assert resp.status_code == 404


def test_delete_expense_twice(client):
    """Deleting the same expense twice — the second call returns 404."""
    client.post("/api/expenses", json={
        "name": "Milk", "notes": "", "category": "grocery", "amount": 5.0, "date": "2026-06-15",
    })
    resp1 = client.delete("/api/expenses/1")
    assert resp1.status_code == 204
    resp2 = client.delete("/api/expenses/1")
    assert resp2.status_code == 404
