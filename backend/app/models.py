from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


def _validate_date_string(value: str) -> str:
    """Validate that a date string is a real calendar date (not just syntactically valid).

    Pydantic's Field(pattern=...) only checks the shape (^\d{4}-\d{2}-\d{2}$).
    This validator ensures impossible dates like "2026-02-30" or "2026-13-01"
    are rejected before they reach the database.
    """
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"'{value}' is not a valid calendar date. Use YYYY-MM-DD.")
    return value


class ExpenseCreate(BaseModel):
    """Schema for creating a new expense. All fields except notes are required.

    Validation: name and category have length limits, amount must be positive,
    date must be ISO 8601 (YYYY-MM-DD) and a real calendar date. FastAPI
    automatically returns 422 with details if any constraint fails, before
    the request reaches the handler.
    """
    name: str = Field(..., min_length=1, max_length=200)
    notes: str = ""
    category: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("date")
    @classmethod
    def validate_date_is_real(cls, v: str) -> str:
        return _validate_date_string(v)


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense. Every field is Optional — only the
    fields that are explicitly provided in the request will be changed.

    model_dump(exclude_unset=True) in the handler uses this to build a
    dynamic SET clause for the SQL UPDATE.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    notes: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[float] = Field(None, gt=0)
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("date")
    @classmethod
    def validate_date_is_real(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _validate_date_string(v)


class ExpenseResponse(BaseModel):
    """Schema for expense data returned to the client.

    from_attributes=True tells Pydantic to read attributes from objects
    (like sqlite3.Row via dict conversion) rather than requiring dicts.
    """
    id: int
    name: str
    notes: str
    category: str
    amount: float
    date: str

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    """Schema for creating a new custom category. Only a name is needed."""
    name: str = Field(..., min_length=1, max_length=100)


class CategoryResponse(BaseModel):
    """Schema for category data returned to the client.

    is_default distinguishes the four built-in categories (grocery, medicine,
    transportation, miscellaneous) from user-created ones. The frontend can
    use this to prevent deletion of defaults if that feature is added later.
    """
    id: int
    name: str
    is_default: bool

    model_config = {"from_attributes": True}
