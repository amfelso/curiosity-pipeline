from functions.embed_memories_to_pinecone import app
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()


def test_embed_memories():
    input_payload = {"urls": []}

    data = app.lambda_handler(input_payload, "")

    assert data["statusCode"] == 200

