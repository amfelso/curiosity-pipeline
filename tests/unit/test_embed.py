from functions.embed_memories_to_pinecone import app
from pinecone import Pinecone
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

# Load environment variables from .env file
load_dotenv()


def test_embed_memories():
    input_payload = {"urls": [("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                                "2024-01-08/image1216927_memory.txt"),
                              ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                                "2024-01-08/image1216942_memory.txt"),
                              ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                                "2024-01-08/image1216944_memory.txt"),
                              ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                                "2024-01-08/image1216948_memory.txt"),
                              ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                                "2024-01-08/image1216966_memory.txt")]}

    data = app.lambda_handler(input_payload, "")

    assert data["statusCode"] == 200
    assert len(json.loads(data["body"])) > 0
