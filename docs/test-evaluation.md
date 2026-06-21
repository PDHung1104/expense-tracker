# Test Case Evaluation

Evaluation of all 27 test cases across `backend/tests/test_expenses.py` and `backend/tests/test_categories.py`, plus identification of missing edge cases.

---

## Test Infrastructure

Tests use a `client` fixture (`conftest.py`) that creates an isolated temporary SQLite database per test. The real database is never touched. Each test gets a fresh DB seeded with the four default categories.

---

## Covered Test Cases

### `test_expenses.py` — 20 tests

#### Create (5 tests)

| Test | What it verifies | Assertion |
|---|---|---|
| `test_create_expense` | Valid expense with all fields | 201, all fields echoed back with assigned `id` |
| `test_create_expense_invalid_category` | Non-existent category name | 400, detail mentions "does not exist" |
| `test_create_expense_missing_name` | Omitted required field `name` | 422 (Pydantic validation) |
| `test_create_expense_negative_amount` | `amount: -10.0` violates `gt=0` | 422 |
| `test_create_expense_invalid_date_format` | DD-MM-YYYY instead of YYYY-MM-DD | 422 |

#### List / Filter / Sort (9 tests)

| Test | What it verifies | Assertion |
|---|---|---|
| `test_list_expenses_empty` | Fresh DB, no expenses | 200, `[]` |
| `test_list_expenses_multiple` | Two expenses, no params | 200, `len == 2` |
| `test_list_expenses_filter_by_category` | `?category=grocery` | Only matching item returned |
| `test_list_expenses_filter_by_date_range` | `?date_from=...&date_to=...` | Inclusive filter, only June item returned |
| `test_list_expenses_sort_by_date_asc` | `?sort_by=date&order=asc` | Oldest first |
| `test_list_expenses_sort_by_amount_desc` | `?sort_by=amount&order=desc` | Most expensive first |
| `test_list_expenses_sort_by_category_asc` | `?sort_by=category&order=asc` | Alphabetical by category name |
| `test_list_expenses_invalid_sort_by` | `?sort_by=nonexistent` | 400 (blocked before reaching SQL) |
| `test_list_expenses_invalid_order` | `?order=sideways` | 400 |

#### Update (4 tests)

| Test | What it verifies | Assertion |
|---|---|---|
| `test_update_expense` | Partial update — send only `name` + `amount` | 200, only those fields changed; `category` and `notes` unchanged |
| `test_update_expense_not_found` | `PUT /api/expenses/999` | 404 |
| `test_update_expense_change_category` | Change `category` to a valid one | 200, category updated |
| `test_update_expense_to_invalid_category` | Change `category` to non-existent | 400 |

#### Delete (2 tests)

| Test | What it verifies | Assertion |
|---|---|---|
| `test_delete_expense` | Delete existing expense, then list | 204, list returns `[]` (verifies removal) |
| `test_delete_expense_not_found` | `DELETE /api/expenses/999` | 404 |

---

### `test_categories.py` — 7 tests

| Test | What it verifies | Assertion |
|---|---|---|
| `test_list_categories_defaults` | Fresh DB → 4 defaults | All present, all `is_default: true`, `len == 4` |
| `test_create_category` | Create "entertainment" | 201, `is_default: false` |
| `test_create_category_duplicate` | Create same custom name twice | 409 |
| `test_create_category_duplicate_default` | Create "grocery" (matches a default) | 409 |
| `test_create_category_empty_name` | `{ "name": "" }` | 422 |
| `test_custom_category_appears_in_list` | After creation, list includes it | `len == 5`, "entertainment" in names |
| `test_custom_category_usable_for_expense` | Create category "pets", then an expense using it | 201 |

---

## Missing Edge Cases

### 1. Amount boundaries (`gt=0` in Pydantic)

| Gap | Detail | Risk |
|---|---|---|
| Zero amount | `amount: 0` should be rejected (422). `gt=0` means strictly greater than zero. | Low |
| Very large amounts | e.g. `1e308` — does it overflow? SQLite REAL is an 8-byte float. | Low |
| Floating-point precision | `5.10` round-tripping correctly. No test verifies `5.10` doesn't become `5.099999`. | Low |

### 2. String length boundaries

| Gap | Detail | Risk |
|---|---|---|
| Name at max (200 chars) | `min_length=1, max_length=200` — no upper-boundary test | Low |
| Name over max (201 chars) | Should be 422 | Low |
| Category at max (100 chars) | No upper-boundary test | Low |
| Category over max (101 chars) | Should be 422 | Low |
| Name exactly 1 char | Lower boundary for `min_length=1` — not explicitly tested | Low |
| Notes with very long text | `notes` has no `max_length` — probably fine, but unknown | Low |

### 3. Date validation gaps (regex is structurally weak)

The regex `^\d{4}-\d{2}-\d{2}$` only checks the shape — it does **not** validate that the date actually exists on a calendar.

| Gap | Detail | Risk |
|---|---|---|
| Impossible date that matches regex | `"2026-02-30"`, `"2026-13-01"`, `"2026-00-00"` — all pass the regex and would be inserted into the DB | **Medium** |
| Leap year | `"2024-02-29"` (valid leap) vs `"2025-02-29"` (invalid) — both pass the regex | Low |
| Date with time component | `"2026-06-15T12:00:00"` — fails regex, but no test confirms 422 | Low |
| Empty date string | `""` — the regex requires 10 chars, should be 422. Not tested. | Low |

### 4. Filter and sort edge cases

| Gap | Detail | Risk |
|---|---|---|
| `date_from` without `date_to` | Should work as a lower-bound-only filter. Not tested. | Low |
| `date_to` without `date_from` | Should work as an upper-bound-only filter. Not tested. | Low |
| `date_from > date_to` | e.g. `date_from=2026-12-01&date_to=2026-01-01` — returns empty list silently. Is that the right behavior? No test documents the decision. | Low |
| Filter by non-existent category | e.g. `?category=nonexistent` — should return `[]`, not an error. Not tested. | Low |
| Multiple simultaneous filters | Category + date range together. Not tested in combination. | Low |
| Default sort order | `sort_by` and `order` omitted → default is `ORDER BY date desc`. `test_list_expenses_multiple` creates two dated items but never asserts the actual order. | Low |
| Tiebreaker behavior | Two expenses with the same date, sorted by date — order is undefined (storage order). No test pins expectations. Same for equal amounts. | Low |
| Sort by `date` descending | Only `asc` tested for date. Only `desc` tested for amount. Coverage is asymmetric. | Low |

### 5. Update edge cases

| Gap | Detail | Risk |
|---|---|---|
| **Empty update body** | `PUT /api/expenses/1` with `{}` — code returns existing record unchanged (line 114–115 in `expenses.py`). **No test covers this code path.** | **Medium** |
| Update amount to zero | Should be 422 (`gt=0` in `ExpenseUpdate`) | Low |
| Update name to empty string | Should be 422 (`min_length=1`) | Low |
| Update date to invalid format | Should be 422 | Low |
| Update with all fields | Full replacement (non-partial). Not tested explicitly. | Low |
| Update only `notes` | Single-field update to a non-validated optional field. Not tested in isolation. | Low |

### 6. Delete edge cases

| Gap | Detail | Risk |
|---|---|---|
| Delete with ID = 0 | FastAPI path param — behavior unclear | Low |
| Delete with negative ID | e.g. `DELETE /api/expenses/-1` — 404 from DB, but does FastAPI reject the type first? | Low |
| Double-delete | Delete same ID twice — second call should be 404 (the `not_found` test only covers IDs that never existed) | Low |

### 7. Category edge cases

| Gap | Detail | Risk |
|---|---|---|
| Whitespace in name | `" entertainment "` — leading/trailing space is not trimmed, would create a distinct category | Low |
| Special characters / emoji | `"café"`, `"🍕"` — go through parameterized queries (safe from injection), but no test confirms | Low |
| SQL injection attempt | `"test'; DROP TABLE--"` — parameterized, but no explicit test | Low |
| Category name at max length (100 chars) | Boundary test missing | Low |

### 8. Response shape / contract

| Gap | Detail | Risk |
|---|---|---|
| Expense response keys | No test explicitly asserts all expected keys (`id`, `name`, `notes`, `category`, `amount`, `date`) are present with correct types | Low |
| Category response keys | Same for `id`, `name`, `is_default` | Low |
| Content-Type header | No test asserts `application/json` | Low |
| 204 response body | Should be empty — not verified | Low |

### 9. Cross-cutting

| Gap | Detail | Risk |
|---|---|---|
| Concurrent requests | No test for race conditions (e.g. two simultaneous creates) | Low |
| Cold start / first run | `_ensure_data_dir()` creates the data directory — no test for the first-run scenario | Low |
| SQLite connection failure | Read-only filesystem, disk full — not tested (understandable for a personal app) | N/A |

---

## Summary

| Category | Covered | Missing (notable) |
|---|---|---|
| Create expense | 5 | Zero amount, string boundaries, impossible dates |
| List / filter / sort | 9 | Partial filters, combo filters, default sort assertion, non-existent category filter |
| Update expense | 4 | **Empty body (untested code path)**, zero amount, empty name, invalid date |
| Delete expense | 2 | Double-delete, ID=0 |
| Categories | 7 | Whitespace, special chars, 100-char boundary |
| Response shape | 0 | Key presence, types, Content-Type |
| **Total** | **27** | **~15 notable gaps** |

### Top risks (in order)

1. **Date regex is too permissive** — `"2026-02-30"` and `"2026-13-01"` pass validation and land in the database. A real date parser (or a `datetime.strptime` check in the handler) would close this.

2. **Empty update body path is untested** — `update_expense` has explicit logic for `if not updates: return` (line 114) that no test hits. If that branch regresses, a client sending `{}` would crash instead of returning the existing record.

3. **No combo-filter test** — e.g. category + date range together. The query builder appends clauses additively, so it should work, but there's no integration-level coverage.

Everything else is low-risk polish — boundary values, response shape assertions, and edge-case inputs that Pydantic already guards against.
