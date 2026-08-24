from fastapi import FastAPI

app = FastAPI(title="TFT Vision Service")


@app.get("/health")
def health():
    return {"status": "ok"}
