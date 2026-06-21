import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.database import init_db
from app.expenses import router as expenses_router
from app.categories import router as categories_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan — runs init_db() on startup.

    This replaces the deprecated @app.on_event("startup") pattern. The
    database tables and default categories are guaranteed to exist before
    any request is handled. The yield point is where the application serves
    requests; cleanup code (if any) would go after it.
    """
    init_db()
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    This factory function exists so tests can create isolated app instances
    with their own temporary databases. It wires up CORS (for the Vite dev
    server on port 5173), includes all API routers, registers a global JSON
    exception handler, and — when a production frontend build is detected
    on disk — serves the React SPA as static files.
    """
    app = FastAPI(title="Expense Tracker", lifespan=lifespan)

    # CORS for React dev server (Vite on :5173).
    # In Docker/nginx production the browser talks to a single origin so
    # no cross-origin requests occur; this middleware is harmless there.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(expenses_router)
    app.include_router(categories_router)

    # Global exception handler — guarantee every error response is JSON.
    # Without this, unhandled exceptions would return Starlette's default
    # HTML traceback page, which breaks the frontend's `resp.json()` calls.
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    # In production, serve the built React app.
    # When frontend/dist/ exists (Docker single-container mode, or after a
    # local `npm run build`), FastAPI serves both the API and static files
    # from one process. The catch-all GET route enables React Router's
    # client-side navigation to work on page reload.
    static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
    if os.path.isdir(static_dir):
        app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str = ""):
            index_path = os.path.join(static_dir, "index.html")
            if os.path.isfile(index_path):
                return FileResponse(index_path)
            return {"detail": "Not Found"}

    return app


app = create_app()
