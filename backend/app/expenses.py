from fastapi import APIRouter, HTTPException, Query
from app.database import get_db
from app.models import ExpenseCreate, ExpenseUpdate, ExpenseResponse

router = APIRouter(prefix="/api")

# Allow-lists prevent SQL injection in the dynamic ORDER BY clause.
# Any value not in the set is rejected with a 400 before it reaches SQL.
ALLOWED_SORT_FIELDS = {"date", "amount", "category"}
ALLOWED_ORDER = {"asc", "desc"}


def _row_to_expense(row) -> dict:
    """Convert a sqlite3.Row to a plain dict for Pydantic serialization.

    sqlite3.Row objects cannot be directly serialized to JSON by FastAPI,
    so this helper extracts the columns into a dict that Pydantic can
    validate against ExpenseResponse.
    """
    return {
        "id": row["id"],
        "name": row["name"],
        "notes": row["notes"],
        "category": row["category"],
        "amount": row["amount"],
        "date": row["date"],
    }


@router.get("/expenses", response_model=list[ExpenseResponse])
def list_expenses(
    category: str | None = Query(None, description="Filter by category name"),
    sort_by: str = Query("date", description="Sort field: date, amount, or category"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
):
    """List expenses with optional filtering, sorting, and date-range.

    This is the primary data endpoint — the dashboard and expenses page both
    call it. Filters are additive (AND-ed together). Sorting is dynamic but
    safe because sort_by and order are validated against allow-lists before
    being interpolated into the SQL.
    """
    if sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(400, f"Invalid sort_by: {sort_by}. Allowed: date, amount, category")
    if order not in ALLOWED_ORDER:
        raise HTTPException(400, f"Invalid order: {order}. Allowed: asc, desc")

    with get_db() as db:
        query = "SELECT * FROM expenses WHERE 1=1"
        params: list = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if date_from:
            query += " AND date >= ?"
            params.append(date_from)

        if date_to:
            query += " AND date <= ?"
            params.append(date_to)

        # Safe to use f-string here — sort_by and order are validated against allowlists
        query += f" ORDER BY {sort_by} {order}"

        rows = db.execute(query, params).fetchall()
        return [_row_to_expense(r) for r in rows]


@router.post("/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(data: ExpenseCreate):
    """Create a new expense.

    Validates that the requested category exists before inserting. This
    maintains referential integrity at the application level (the expenses
    table uses a plain TEXT column for category, not a foreign key, to keep
    the schema simple and categories easy to rename later).
    """
    with get_db() as db:
        # Validate category exists
        cat = db.execute(
            "SELECT id FROM categories WHERE name = ?", (data.category,)
        ).fetchone()
        if not cat:
            raise HTTPException(400, f"Category '{data.category}' does not exist")

        cursor = db.execute(
            "INSERT INTO expenses (name, notes, category, amount, date) VALUES (?, ?, ?, ?, ?)",
            (data.name, data.notes, data.category, data.amount, data.date),
        )
        row = db.execute("SELECT * FROM expenses WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_expense(row)


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, data: ExpenseUpdate):
    """Update an expense. Only the fields provided in the request are changed.

    Uses model_dump(exclude_unset=True) to detect which fields the client
    actually sent, then builds a dynamic SET clause. This means the frontend
    can send just { "amount": 9.99 } and only the amount column is updated
    — all other fields remain unchanged.
    """
    with get_db() as db:
        existing = db.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        if not existing:
            raise HTTPException(404, f"Expense {expense_id} not found")

        # Build SET clause from provided (non-None) fields
        updates: dict = data.model_dump(exclude_unset=True)
        if not updates:
            return _row_to_expense(existing)

        # Validate category if being changed
        if "category" in updates:
            cat = db.execute(
                "SELECT id FROM categories WHERE name = ?", (updates["category"],)
            ).fetchone()
            if not cat:
                raise HTTPException(400, f"Category '{updates['category']}' does not exist")

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [expense_id]
        db.execute(f"UPDATE expenses SET {set_clause} WHERE id = ?", values)

        row = db.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        return _row_to_expense(row)


@router.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int):
    """Delete an expense by ID.

    Returns 204 No Content on success. Returns 404 if the expense doesn't
    exist, so the frontend can distinguish between "already deleted" and
    "successfully deleted by this request."
    """
    with get_db() as db:
        existing = db.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        if not existing:
            raise HTTPException(404, f"Expense {expense_id} not found")
        db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
