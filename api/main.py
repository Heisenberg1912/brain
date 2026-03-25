"""FastAPI app — thin wrapper around brain/ engine."""
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routers import data_bank, valuation, ai, blockchain

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(title="BuiltAttic Brain", version="0.1.0")

# API routes
app.include_router(data_bank.router, prefix="/api/v1/data", tags=["Data Bank"])
app.include_router(valuation.router, prefix="/api/v1/valuation", tags=["Valuation"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(blockchain.router, prefix="/api/v1/chain", tags=["Blockchain"])

# Serve React build (production) or fallback to source index.html (dev)
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"

# Use the built React app if it exists, otherwise fall back to source
STATIC_DIR = DIST_DIR if DIST_DIR.exists() else FRONTEND_DIR

if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger("api").exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health():
    return {"status": "ok", "service": "builtattic-brain"}


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    """Serve the React SPA — all non-API routes fall through to index.html."""
    file_path = STATIC_DIR / full_path
    if full_path and file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    return FileResponse(str(STATIC_DIR / "index.html"))
