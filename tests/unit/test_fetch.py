from functions.fetch_mars_images import app
import json


def test_fetch_images():
    input_payload = {"sols": [4061]}

    data = app.lambda_handler(input_payload, "")
    first_photo = json.loads(data["body"])[0]

    assert data["statusCode"] == 200
    assert len(data["body"]) > 0
    assert "img_src" in first_photo
    assert "earth_date" in first_photo
    assert "sol" in first_photo
    assert "camera" in first_photo
    assert "rover" in first_photo
    assert "id" in first_photo
