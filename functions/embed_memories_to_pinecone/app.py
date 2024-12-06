from pinecone import Pinecone
from openai import OpenAI
from uuid import uuid4
import json
import logging
import os
import boto3
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

# Initialize Pinecone and OpenAI clients
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# Index Configuration
INDEX_NAME = "rover-memories"
index = pc.Index(INDEX_NAME)

# Define logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_text_from_s3(url):
    # Get text from S3
    s3_client = boto3.client('s3')
    parsed_url = urlparse(url)
    bucket = parsed_url.netloc.split('.')[0]
    logger.info(f"Getting text from S3: {url}")
    logger.info(f"Bucket: {bucket}")
    key = parsed_url.path.lstrip('/')
    logger.info(f"Key: {key}")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    text = response['Body'].read().decode('utf-8')

    # Replace newline with space
    text = text.replace("\n", " ")

    return text


def get_embedding(text, model="text-embedding-3-small"):
   return client.embeddings.create(input = [text], model=model).data[0].embedding


# Function to Embed Text and Upsert Data
def upsert_memory(memory_id, text, date, memory_type, s3_url):
    # Generate embedding for the text
    embedding = get_embedding(text)

    # Prepare the upsert payload
    metadata = {
        "date": date,
        "type": memory_type,
        "s3_url": s3_url,
        "text": text
    }
    index.upsert([{"id": memory_id, "values": embedding, "metadata": metadata}])
    print(f"Memory '{memory_id}' upserted successfully!")


def lambda_handler(event, context):
    """
    Lambda function to generate embeddings for memories and upsert them to Pinecone index.

    Input: {'urls': ['https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/
                      2024-01-08/image1216927_memory.txt']}
    """
    urls = event.get("urls", [])
    results = []
    
    # Iterate through urls, get text from S3, embed the text and upsert to Pinecone
    for url in urls:
        text = get_text_from_s3(url)
        memory_id = str(uuid4())
        date = url.split("/")[-2]
        memory_type = url.split("/")[-1].split("_")[1].replace(".txt", "")
        
        # Embed the text and upsert to Pinecone
        upsert_memory(memory_id, text, date, memory_type, url)
        results.append({"id": memory_id, "date": date, "type": memory_type, "s3_url": url})
    
    # Return the image metadata for the next step
    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }


if __name__ == "__main__":
    # Test the function locally
    logger.info("Testing locally...")
    test_event = {"urls": [("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                            "2024-01-08/image1216927_memory.txt"),
                           ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                            "2024-01-08/image1216942_memory.txt"),
                           ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                            "2024-01-08/image1216944_memory.txt"),
                           ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                            "2024-01-08/image1216948_memory.txt"),
                           ("https://curiosity-data-1205.s3.us-east-1.amazonaws.com/memories/"
                            "2024-01-08/image1216966_memory.txt")]}
    result = lambda_handler(test_event, None)
    logger.info(f"Result: {result}")