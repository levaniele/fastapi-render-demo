from fastapi import FastAPI

app = FastAPI(title="FastAPI Render Demo")

@app.get("/")
def root():
    return {"ok": True, "service": "fastapi-render-demo"}

@app.get("/health")
def health():
    return {"status": "healthy"}
