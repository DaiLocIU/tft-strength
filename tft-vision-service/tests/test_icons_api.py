from fastapi.testclient import TestClient
from PIL import Image
import os
import io
from app.main import app

client = TestClient(app)


def test_list_screenshots():
    response = client.get("/api/screenshots")
    assert response.status_code == 200
    data = response.json()
    assert "screenshots" in data
    assert isinstance(data["screenshots"], list)


def test_list_reference_icons():
    response = client.get("/api/icons")
    assert response.status_code == 200
    data = response.json()
    assert "icons" in data
    assert isinstance(data["icons"], list)


def test_crop_batch_and_delete():
    # 1. First ensure we have a test image in screenshots
    screenshots_res = client.get("/api/screenshots")
    screenshots = screenshots_res.json().get("screenshots", [])

    if not screenshots:
        # Upload a synthetic image
        img = Image.new("RGB", (500, 500), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        upload_res = client.post(
            "/api/screenshots/upload",
            files={"file": ("test_sample.png", buf, "image/png")},
        )
        assert upload_res.status_code == 200
        screenshot_name = "test_sample.png"
    else:
        screenshot_name = screenshots[0]["name"]

    # 2. Crop batch
    crop_payload = {
        "screenshot_name": screenshot_name,
        "crops": [
            {
                "name": "test_unit_autocrop",
                "xmin": 0.1,
                "ymin": 0.1,
                "xmax": 0.3,
                "ymax": 0.3,
            }
        ],
    }

    res = client.post("/api/icons/crop-batch", json=crop_payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "success"
    assert res_data["count"] == 1
    assert res_data["saved_icons"][0]["name"] == "test_unit_autocrop"

    # 3. Verify it appears in icons list
    icons_res = client.get("/api/icons")
    icon_names = [i["name"] for i in icons_res.json()["icons"]]
    assert "test_unit_autocrop" in icon_names

    # 4. Clean up / delete test icon
    del_res = client.delete("/api/icons/test_unit_autocrop.png")
    assert del_res.status_code == 200


def test_detect_and_annotations_feedback():
    # 1. Test detect endpoint on image_1 or sample
    screenshots_res = client.get("/api/screenshots")
    screenshots = screenshots_res.json().get("screenshots", [])
    if not screenshots:
        return

    first_name = screenshots[0]["name"]
    detect_res = client.post(
        "/api/vision/detect",
        json={"screenshot_name": first_name, "threshold": 0.55},
    )
    assert detect_res.status_code == 200
    detect_data = detect_res.json()
    assert detect_data["status"] == "success"
    assert "detections" in detect_data
    assert isinstance(detect_data["detections"], list)

    # 2. Test saving active learning annotations
    save_res = client.post(
        "/api/annotations/save",
        json={
            "screenshot_name": first_name,
            "items": [
                {
                    "id": "item_1",
                    "name": "test_feedback_champ",
                    "x": 100,
                    "y": 100,
                    "width": 50,
                    "height": 50,
                    "confidence": 95.0,
                    "status": "confirmed",
                }
            ],
        },
    )
    assert save_res.status_code == 200
    assert save_res.json()["status"] == "success"
    assert save_res.json()["saved_templates_count"] >= 1

    # Clean up test template
    client.delete("/api/icons/test_feedback_champ.png")

