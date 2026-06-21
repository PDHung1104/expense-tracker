# Expense Tracker

A personal expense tracking application with a **FastAPI** backend and **React** frontend, containerized with Docker.

## Tech Stack

| Layer    | Technology                          |
| -------- | ----------------------------------- |
| Backend  | Python 3.12+, FastAPI, SQLite       |
| Frontend | React 19, Vite, React Router, CSS   |
| Infra    | Docker, Docker Compose, nginx       |
| Testing  | pytest, httpx (backend)             |

The database is **SQLite** via Python's standard library — zero external database dependencies. The frontend uses plain CSS (no framework), with CSS custom properties for theming.

## Project Structure

```
Expense_tracker/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app factory, CORS, SPA serving
│   │   ├── database.py       # SQLite connection, init_db(), seed defaults
│   │   ├── models.py         # Pydantic request/response schemas
│   │   ├── expenses.py       # Expense CRUD + filtering/sorting
│   │   └── categories.py     # Category management
│   ├── tests/
│   │   ├── conftest.py       # Isolated test DB fixture
│   │   ├── test_expenses.py  # 20 tests
│   │   └── test_categories.py# 7 tests
│   ├── data/                 # SQLite DB (gitignored)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.jsx          # React entry point
│   │   ├── App.jsx           # Routes: / (dashboard), /expenses
│   │   ├── api/client.js     # Centralized fetch wrapper
│   │   ├── pages/            # DashboardPage, ExpensesPage
│   │   └── components/       # Navbar, ExpenseForm, ExpenseList, etc.
│   ├── Dockerfile            # Multi-stage: Node build → nginx serve
│   ├── nginx.conf            # SPA + /api reverse proxy
│   └── package.json
├── docker-compose.yml        # Two services: backend + frontend
└── docs/
    └── test-coverage.md      # Detailed test documentation
```

## Quick Start

### Prerequisites

- **Python 3.12+** (backend)
- **Node.js 20+** (frontend, dev only)
- **Docker** (optional, for containerized deployment)

### Local Development

**Backend:**

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash)
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend (separate terminal):**

```bash
cd frontend
npm install
npm run dev       # Vite dev server on http://localhost:5173
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`, so you can hit the full app at **http://localhost:5173** without CORS issues.

### Docker

```bash
docker compose up -d           # Build and start (app on http://localhost)
docker compose down            # Stop
docker compose up -d --build   # Rebuild and restart
docker compose logs -f         # Follow all logs
```

The Docker setup uses two containers:

- **backend** — FastAPI on internal port 8000 (not exposed externally)
- **frontend** — nginx on port 80 proxying `/api` to the backend

SQLite data is persisted via a named Docker volume (`expense-data`).

## API Endpoints

All endpoints are prefixed with `/api`.

| Method   | Path                  | Description                     |
| -------- | --------------------- | ------------------------------- |
| `GET`    | `/api/expenses`       | List expenses (with filters)    |
| `POST`   | `/api/expenses`       | Create an expense               |
| `PUT`    | `/api/expenses/{id}`  | Update an expense (partial)     |
| `DELETE` | `/api/expenses/{id}`  | Delete an expense               |
| `GET`    | `/api/categories`     | List all categories             |
| `POST`   | `/api/categories`     | Add a custom category           |

### Query Parameters for `GET /api/expenses`

| Parameter   | Type   | Description                              |
| ----------- | ------ | ---------------------------------------- |
| `category`  | string | Filter by category name                  |
| `sort_by`   | string | Sort field: `date`, `amount`, `category` |
| `order`     | string | Sort order: `asc` or `desc`              |
| `date_from` | string | Start date (ISO 8601, YYYY-MM-DD)        |
| `date_to`   | string | End date (ISO 8601, YYYY-MM-DD)          |

## Database Schema

Two tables in a single SQLite file:

### `categories`

| Column      | Type    | Constraints                |
| ----------- | ------- | -------------------------- |
| `id`        | INTEGER | PRIMARY KEY AUTOINCREMENT  |
| `name`      | TEXT    | UNIQUE NOT NULL            |
| `is_default`| INTEGER | DEFAULT 0                  |

Default categories seeded on startup: **grocery**, **medicine**, **transportation**, **miscellaneous**.

### `expenses`

| Column     | Type    | Constraints                |
| ---------- | ------- | -------------------------- |
| `id`       | INTEGER | PRIMARY KEY AUTOINCREMENT  |
| `name`     | TEXT    | NOT NULL                   |
| `notes`    | TEXT    | DEFAULT ''                 |
| `category` | TEXT    | NOT NULL                   |
| `amount`   | REAL    | NOT NULL                   |
| `date`     | TEXT    | NOT NULL (ISO 8601)        |

## Testing

```bash
cd backend
pytest                    # Run all 27 tests
pytest -v                 # Verbose output
pytest tests/test_expenses.py          # Expense tests only
pytest tests/test_categories.py        # Category tests only
```

Tests use an isolated temporary SQLite database for each test run — the real database is never touched. See [`docs/test-coverage.md`](docs/test-coverage.md) for a detailed breakdown of all test cases.

## Key Design Decisions

- **SQLite via stdlib** — No external database engine needed; single-file storage ideal for a personal app.
- **Vite dev proxy** — Vite proxies `/api` to the FastAPI server in dev, avoiding CORS headaches.
- **SPA fallback** — When `frontend/dist/` exists, FastAPI serves the built React app directly (convenience for running without Docker).
- **Docker with nginx** — Two decoupled containers with nginx as the single entry point, proxying API calls internally.
- **No ORM** — Raw SQL with parameterized queries keeps the backend lean and dependency-light.

## Auth

Authentication is **not yet implemented** — the app currently runs in single-user mode. Session-based login/register is planned for a future phase.

## License

[MIT](https://choosealicense.com/licenses/mit/)
