"""FastAPI app — thin wrapper around brain/ engine."""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import data_bank, valuation, ai, blockchain

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(title="BuiltAttic Brain", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://builtattic.com",
        "https://www.builtattic.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(data_bank.router, prefix="/api/v1/data", tags=["Data Bank"])
app.include_router(valuation.router, prefix="/api/v1/valuation", tags=["Valuation"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(blockchain.router, prefix="/api/v1/chain", tags=["Blockchain"])


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger("api").exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health():
    return {"status": "ok", "service": "builtattic-brain"}
