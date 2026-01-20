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
from db import test_connection

@app.on_event("startup")
async def startup_event():
    ok, msg = await asyncio.to_thread(test_connection)
    if not ok:
        print("DB connection failed on startup:", msg)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/db-health")
async def db_health():
    ok, msg = await asyncio.to_thread(test_connection)
    return {"status": "healthy" if ok else "unhealthy", "detail": msg}
