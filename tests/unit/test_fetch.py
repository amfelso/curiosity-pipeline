from functions.fetch_images_with_metadata import app
from unittest.mock import patch


def test_fetch_images():
    input_payload = {"earth_date": "2012-08-07"}

    # Mock the NASA API response
    mock_photos = [
        {
            "id": 2674,
            "sol": 1,
            "camera": {"name": "NAVCAM"},
            "img_src": (
                "http://mars.jpl.nasa.gov/msl-raw-images/proj/msl/redops/ods/"
                "surface/sol/00001/opgs/edr/ncam/NRA_397586928EDR_F0010008AUT_04096M_.JPG"
            ),
            "earth_date": "2012-08-07"
        }
    ]

    with patch(
        'functions.fetch_images_with_metadata.app.fetch_images_by_sol',
        return_value=mock_photos
    ):
        data = app.lambda_handler(input_payload, "")

    assert data["statusCode"] == 200

