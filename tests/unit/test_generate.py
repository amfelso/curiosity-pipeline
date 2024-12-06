from functions.generate_memories_and_diary import app
import json


def test_generate_memories():
    input_payload = {
        'statusCode': 200,
        'body': json.dumps([])
    }

    data = app.lambda_handler(input_payload, "")

    assert data["statusCode"] == 200
