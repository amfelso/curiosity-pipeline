from pinecone import Pinecone
from openai import OpenAI
from uuid import uuid4
import json
import logging
import os
import sys
import boto3
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to sys.path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
functions_dir = os.path.abspath(os.path.join(current_dir, ".."))
repo_root = os.path.abspath(
    os.path.join(current_dir, "../..")
)  # Adjust path to repo root
if repo_root not in sys.path or functions_dir not in sys.path:
    sys.path.append(repo_root)  # Ensure repo root is in sys.path
    sys.path.append(functions_dir)  # Ensure functions directory is in sys.path

from utils.ddb_utility import update_pipeline_log

# Define logger
logger = logging.getLogger()
if not logger.hasHandlers():  # Prevent duplicate handlers during testing
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)  # Set logging level

# Constants
LAMBDA_NAME = "Lambda3: EmbedToPinecone"


def get_text_from_s3(url):
    # Get text from S3
    s3_client = boto3.client("s3")
    parsed_url = urlparse(url)
    bucket = parsed_url.netloc.split(".")[0]
    logger.info(f"Getting text from S3: {url}")
    key = parsed_url.path.lstrip("/")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    text = response["Body"].read().decode("utf-8")

    # Replace newline with space
    text = text.replace("\n", " ")

    return text


def get_embedding(text, client, model="text-embedding-3-small"):
    return client.embeddings.create(input=[text], model=model).data[0].embedding


# Function to Embed Text and Upsert Data
def upsert_memory(client, index, memory_id, text, date, memory_type, s3_url):
    # Generate embedding for the text
    embedding = get_embedding(text, client)

    # Prepare the upsert payload
    metadata = {"date": date, "type": memory_type, "s3_url": s3_url, "text": text}
    index.upsert([{"id": memory_id, "values": embedding, "metadata": metadata}])
    logger.info(f"Memory '{memory_id}' upserted successfully!")


def lambda_handler(event, context):
    """
    Lambda function to generate embeddings for memories and upsert them to Pinecone index.
    Input: {'urls': ['https://curiosity-data-1205.s3.amazonaws.com/"
                      memories/2012-08-07/image2674_memory.txt']}
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY is not set in the environment variables.")

    earth_date = event["earth_date"]
    process_result = event["process_result"]
    body = process_result.get("body", "[]")
    urls = json.loads(body)
    results = []

    try:
        # Initialize Pinecone and OpenAI clients
        pc = Pinecone(api_key=PINECONE_API_KEY)
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Index Configuration
        INDEX_NAME = "rover-memories"
        index = pc.Index(INDEX_NAME)

        # Iterate through urls, get text from S3, embed the text and upsert to Pinecone
        for url in urls:
            text = get_text_from_s3(url)
            memory_id = str(uuid4())
            date = url.split("/")[-2]
            memory_type = url.split("/")[-1].split("_")[1].replace(".txt", "")

            # Embed the text and upsert to Pinecone
            upsert_memory(client, index, memory_id, text, date, memory_type, url)
            results.append(
                {"id": memory_id, "date": date, "type": memory_type, "s3_url": url}
            )

        update_pipeline_log(
            earth_date,
            lambda_name=LAMBDA_NAME,
            lambda_status="Success",
            lambda_output=results,
        )
        # Return the image metadata for the next step
        return {"statusCode": 200, "body": json.dumps(results)}

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        update_pipeline_log(
            earth_date,
            lambda_name=LAMBDA_NAME,
            lambda_status="Failed",
            lambda_output=str(e),
        )
        raise e


if __name__ == "__main__":
    logger.info("Testing locally...")
    test_event = {
        "earth_date": "2012-08-07",
        "process_result": {
            "statusCode": 200,
            "body": json.dumps(
                [
                    (
                        "https://curiosity-data-1205.s3.amazonaws.com/"
                        "memories/2012-08-07/image2674_memory.txt"
                    ),
                    (
                        "https://curiosity-data-1205.s3.amazonaws.com/"
                        "memories/2012-08-07/image2097_memory.txt"
                    ),
                ]
            ),
        },
    }
    result = lambda_handler(test_event, None)
    logger.info(f"Result: {result}")
