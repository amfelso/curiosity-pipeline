from functions.embed_memories_to_pinecone import app
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()


def test_embed_memories():
    input_payload = {
        "earth_date": "2024-01-08",
        "process_result": {
            'statusCode': 200,
            'body': json.dumps([])
        }
    }

    data = app.lambda_handler(input_payload, "")

    assert data["statusCode"] == 200

