from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://verceldev-seven.vercel.app",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import asyncio
import logging
from db import test_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("fastapi_app")

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI startup: checking DB connection")
    ok, msg = await asyncio.to_thread(test_connection)
    if ok:
        logger.info("DB connection OK")
    else:
        logger.error("DB connection failed on startup: %s", msg)

@app.get("/health")
def health():
    logger.info("Health endpoint requested; returning healthy")
    return {"status": "healthy"}

@app.get("/db-health")
async def db_health():
    ok, msg = await asyncio.to_thread(test_connection)
    status = "healthy" if ok else "unhealthy"
    logger.info("DB health check requested; status=%s detail=%s", status, msg)
    return {"status": status, "detail": msg}
