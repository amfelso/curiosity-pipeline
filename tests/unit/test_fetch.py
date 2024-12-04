from functions.fetch_mars_images import app


def test_fetch_images():
    input_payload = {"sols": [4061]}

    data = app.lambda_handler(input_payload, "")

    assert data["statusCode"] == 200
    assert len(data["body"]) > 0
    assert "img_src" in data["body"][0]
    assert "earth_date" in data["body"][0]
    assert "sol" in data["body"][0]
    assert "camera" in data["body"][0]
    assert "rover" in data["body"][0]
    assert "id" in data["body"][0]
