import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes.icons import router as icons_router

app = FastAPI(title="TFT Vision Service & Icon Studio")

# Enable CORS for local dev / frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
STATIC_DIR = os.path.join(PROJECT_ROOT, "app", "static")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Include API routes
app.include_router(icons_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "tft-vision-service"}


# Mount static data directory for images
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

# Mount frontend web application at root
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
