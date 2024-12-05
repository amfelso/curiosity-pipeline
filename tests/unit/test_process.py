from functions.generate_memories_and_diary import app
import json

import sys
print(sys.executable)


def test_process_metadata():
    input_payload = {
        'statusCode': 200,
        'body': json.dumps([
            {
                "id": 1216944,
                "sol": 4061,
                "img_src": (
                            "https://mars.nasa.gov/msl-raw-images/proj/msl/"
                            "redops/ods/surface/sol/04061/opgs/edr/ncam/"
                            "NRB_757995593EDR_S1051222NCAM00593M_.JPG"
                            ),
                "earth_date": "2024-01-08"
            },
            {
                "id": 1216966,
                "sol": 4061,
                "img_src": (
                            "https://mars.nasa.gov/msl-raw-images/proj/msl/"
                            "redops/ods/surface/sol/04061/opgs/edr/ncam/"
                            "NRB_758015288EDR_D1051222NCAM00581M_.JPG"
                            ),
                "earth_date": "2024-01-08"
            },
            {
                "id": 1216948,
                "sol": 4061,
                "img_src": (
                            "https://mars.nasa.gov/msl-raw-images/proj/msl/"
                            "redops/ods/surface/sol/04061/opgs/edr/ncam/"
                            "NRB_757995542EDR_S1051222NCAM00593M_.JPG"
                            ),
                "earth_date": "2024-01-08"
            },
            {
                "id": 1216942,
                "sol": 4061,
                "img_src": (
                            "https://mars.nasa.gov/msl-raw-images/proj/msl/"
                            "redops/ods/surface/sol/04061/opgs/edr/ncam/"
                            "NRB_757995619EDR_S1051222NCAM00593M_.JPG"
                            ),
                "earth_date": "2024-01-08"
            },
            {
                "id": 1216927,
                "sol": 4061,
                "img_src": (
                            "https://mars.nasa.gov/msl-raw-images/proj/msl/"
                            "redops/ods/surface/sol/04061/opgs/edr/ncam/"
                            "NLB_757996498EDR_F1051222CCAM05059M_.JPG"
                            ),
                "earth_date": "2024-01-08"
            }
        ])
    }

    data = app.lambda_handler(input_payload, "")

    assert data["statusCode"] == 200
    assert len(data["body"]) > 0
