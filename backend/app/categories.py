from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.models import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/api")


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories():
    """Return all categories (system defaults + user-created), sorted alphabetically.

    This endpoint is called by the frontend to populate category dropdowns in
    the expense form, filter bar, and the AddCategory component. It returns
    both default categories (is_default=true) and custom ones (is_default=false)
    so the user sees a single unified list.
    """
    with get_db() as db:
        rows = db.execute(
            "SELECT id, name, is_default FROM categories ORDER BY name"
        ).fetchall()
        return [{"id": r["id"], "name": r["name"], "is_default": bool(r["is_default"])} for r in rows]


@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(data: CategoryCreate):
    """Create a new user-defined category.

    Duplicate names are rejected with 409 Conflict — this includes both
    existing custom categories and the built-in defaults (grocery, medicine,
    transportation, miscellaneous), since they all share the same UNIQUE
    constraint on the name column.
    """
    with get_db() as db:
        existing = db.execute(
            "SELECT id FROM categories WHERE name = ?", (data.name,)
        ).fetchone()
        if existing:
            raise HTTPException(409, f"Category '{data.name}' already exists")

        cursor = db.execute(
            "INSERT INTO categories (name, is_default) VALUES (?, 0)",
            (data.name,),
        )
        row = db.execute(
            "SELECT id, name, is_default FROM categories WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return {"id": row["id"], "name": row["name"], "is_default": bool(row["is_default"])}
