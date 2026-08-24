# TFT Vision Service

Phase 2 Computer Vision service for Teamfight Tactics board detection, champion template matching, star-level recognition, and trait extraction.

## Tech Stack
- **FastAPI** `0.115.0`
- **Uvicorn** `0.30.6`
- **OpenCV Python** `4.10.0.84`
- **Pillow** `10.4.0`
- **NumPy** `1.26.4`
- **Python Multipart** `0.0.12`

## Project Structure
```
tft-vision-service/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI application entry point
├── data/
│   ├── screenshots/         # Raw full-board screenshots (Day 9+)
│   └── reference_icons/     # Cropped champion icons (Day 10)
├── tests/
│   └── test_main.py         # Test suite
├── requirements.txt         # Dependencies
├── pytest.ini
└── .gitignore
```

## Quickstart

### 1. Activate Environment
```bash
source venv/bin/activate
```

### 2. Run the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Run Tests
```bash
pytest
```

## Dataset Guidelines (Day 9 & 10)
Place 5–10 native resolution raw board screenshots into `data/screenshots/`. These unedited full-board screenshots will be used for template cropping and accuracy benchmarking.
