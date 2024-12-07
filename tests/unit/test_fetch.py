from functions.fetch_images_with_metadata import app
import json


def test_fetch_images():
    input_payload = {"earth_date": "2012-08-07"}

    data = app.lambda_handler(input_payload, "")
    first_photo = json.loads(data["body"])[0]

    assert data["statusCode"] == 200
    assert len(data["body"]) > 0
    assert "id" in first_photo
    assert "sol" in first_photo
    assert "earth_date" in first_photo
    assert "img_src" in first_photo
