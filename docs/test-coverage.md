# Test Coverage

**27 tests across 2 test files** — all passing. Tests use `pytest` with an isolated temporary SQLite database per test, so they run independently and in any order.

---

## Test Infrastructure

### `conftest.py` — `client` fixture

Each test receives a `client` parameter that provides a FastAPI `TestClient` backed by a fresh temporary database. The fixture:

1. Creates a temporary `.db` file on disk
2. Overrides the application's `DB_PATH` to point at the temp file
3. Runs `init_db()` to create tables and seed the 4 default categories (grocery, medicine, transportation, miscellaneous)
4. Yields the `TestClient` for the test to use
5. Restores the original `DB_PATH` and deletes the temp file after the test

This means tests never touch the real `backend/data/expenses.db` and never interfere with each other.

---

## Expense Tests — `test_expenses.py` (20 tests)

### Create Expense (5 tests)

| Test | What it verifies |
|------|-----------------|
| `test_create_expense` | A valid expense returns **201 Created** with all fields echoed back, including the auto-assigned `id` |
| `test_create_expense_invalid_category` | Using a category that doesn't exist returns **400 Bad Request** with a message saying the category does not exist |
| `test_create_expense_missing_name` | Omitting the required `name` field returns **422 Unprocessable Entity** (Pydantic validation) |
| `test_create_expense_negative_amount` | A negative amount is rejected with **422** because the model enforces `Field(gt=0)` |
| `test_create_expense_invalid_date_format` | A date like `15-06-2026` (DD-MM-YYYY) is rejected with **422** — only `YYYY-MM-DD` is accepted per the regex pattern |

### List / Filter / Sort (9 tests)

| Test | What it verifies |
|------|-----------------|
| `test_list_expenses_empty` | A fresh database returns an **empty array** (200) |
| `test_list_expenses_multiple` | After creating 2 expenses, listing returns **both** (sorted newest-first by default) |
| `test_list_expenses_filter_by_category` | `?category=grocery` returns only expenses with that category |
| `test_list_expenses_filter_by_date_range` | `?date_from=2026-06-01&date_to=2026-06-30` filters inclusively — expenses outside the range are excluded |
| `test_list_expenses_sort_by_date_asc` | `?sort_by=date&order=asc` puts the **oldest** expense first |
| `test_list_expenses_sort_by_amount_desc` | `?sort_by=amount&order=desc` puts the **most expensive** expense first |
| `test_list_expenses_sort_by_category_asc` | `?sort_by=category&order=asc` returns items **alphabetically by category name** |
| `test_list_expenses_invalid_sort_by` | `?sort_by=nonexistent` is rejected with **400** (allow-listed sort fields prevent SQL injection) |
| `test_list_expenses_invalid_order` | `?order=sideways` is rejected with **400** (only `asc` and `desc` are allowed) |

### Update Expense (4 tests)

| Test | What it verifies |
|------|-----------------|
| `test_update_expense` | **Partial update** — sending only `name` and `amount` changes those fields while leaving `category` and `notes` unchanged |
| `test_update_expense_not_found` | Updating a non-existent ID returns **404 Not Found** |
| `test_update_expense_change_category` | Changing an expense's category to a different valid category succeeds and returns the updated category |
| `test_update_expense_to_invalid_category` | Changing to a non-existent category returns **400 Bad Request** |

### Delete Expense (2 tests)

| Test | What it verifies |
|------|-----------------|
| `test_delete_expense` | Deleting an existing expense returns **204 No Content** and the expense is actually removed from the database |
| `test_delete_expense_not_found` | Deleting a non-existent ID returns **404 Not Found** |

---

## Category Tests — `test_categories.py` (7 tests)

| Test | What it verifies |
|------|-----------------|
| `test_list_categories_defaults` | A fresh database returns exactly **4 categories** (grocery, medicine, transportation, miscellaneous), all with `is_default: true` |
| `test_create_category` | Creating a custom category returns **201 Created** with `is_default: false` |
| `test_create_category_duplicate` | Creating the same custom category twice returns **409 Conflict** |
| `test_create_category_duplicate_default` | Attempting to create a category that matches a default name (e.g. "grocery") returns **409 Conflict** |
| `test_create_category_empty_name` | An empty name is rejected with **422** (Pydantic validation) |
| `test_custom_category_appears_in_list` | After creating a custom category, the unified list shows **5 categories** (4 defaults + 1 custom) |
| `test_custom_category_usable_for_expense` | A newly created custom category can be used immediately in an expense — the expense is created successfully (201) |

---

## What's NOT covered (by design)

- **Auth** — deferred until the auth system is implemented
- **Frontend** — no frontend test framework is set up yet (e.g. Vitest + React Testing Library)
- **Edge-case amounts** — zero, very large numbers, floating-point precision
- **Concurrent requests** — no race-condition testing
- **Database corruption / disk full** — no filesystem-level failure testing

---

## Running Tests

```bash
cd backend
pytest                          # Run all 27 tests
pytest tests/test_expenses.py   # Expense tests only
pytest tests/test_categories.py # Category tests only
pytest -v                       # Verbose output with test names
```
