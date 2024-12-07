from functions.fetch_images_with_metadata import app


def test_fetch_images():
    input_payload = {"earth_date": "2012-08-06"}

    data = app.lambda_handler(input_payload, "")

    assert data["statusCode"] == 200

