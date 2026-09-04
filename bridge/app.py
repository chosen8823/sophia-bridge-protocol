from fastapi import FastAPI

app = FastAPI(title="SOPHIAEL Runtime Bridge")

@app.get("/health")
def health():
    return {"ok": True}
