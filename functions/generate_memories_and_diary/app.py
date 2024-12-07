import json
import os
import sys
from dotenv import load_dotenv
import logging
import requests
import boto3
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to sys.path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
functions_dir = os.path.abspath(os.path.join(current_dir, ".."))
repo_root = os.path.abspath(os.path.join(current_dir, "../.."))  # Adjust path to repo root
if repo_root not in sys.path or functions_dir not in sys.path:
    sys.path.append(repo_root)  # Ensure repo root is in sys.path
    sys.path.append(functions_dir)  # Ensure functions directory is in sys.path

from utils.ddb_utility import update_pipeline_log

# Define logger
logger = logging.getLogger()
if not logger.hasHandlers():  # Prevent duplicate handlers during testing
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)  # Set logging level

# Constants
LAMBDA_NAME = "Lambda2: GenerateMemories"


def analyze_image(input_img):

    rek_client = boto3.client("rekognition")

    with open(input_img, "rb") as image:
        response = rek_client.detect_labels(Image={"Bytes": image.read()})

    labels = response["Labels"]
    label_names = ""
    for label in labels:
        name = label["Name"]
        confidence = label["Confidence"]
        if confidence > 95:
            label_names = label_names + name + ","
    label_names = label_names[:-1]  # Remove the last comma

    return label_names


def lambda_handler(event, context):
    """
    Lambda function to generate diary entries and memory entries for the given date.
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

    earth_date = event["earth_date"]
    fetch_result = event["fetch_result"]
    body = fetch_result.get("body", "[]")
    photos = json.loads(body)
    results = []

    try:
        # Iterate through photos
        for photo in photos:
            logger.info(photo)

            # Download the image
            img_src = photo["img_src"]
            img_filename = img_src.split("/")[-1]
            img_path = f"/tmp/{img_filename}"
            logger.info(f"Downloading image from {img_src} to {img_path}")
            response = requests.get(img_src)
            with open(img_path, "wb") as f:
                f.write(response.content)

            # Analyze the image
            labels = analyze_image(img_path)
            photo["labels"] = labels
            logger.info(f"Labels: {labels}")

            # Initialize OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)

            # Prompt a memory for the image
            messages = [
                {
                    "role": "system",
                    "content": f"""You are Curiosity, NASA's Mars rover, exploring the Red Planet.
                        Your mission is to observe, analyze, and document the Martian landscape
                        in detail. Every day, you observe the world around you through photos
                        and store a memory entry in the following format:

                        Memory Entry:
                        - Data:
                        - Date: [Earth date]
                        - Sol: [Martian sol]
                        - URL: [URL of the image]
                        - Features: [List of features identified in the image]
                        - Interpretation:
                        - Description: [Detailed description of the scene based on the image,
                                        including colors, shapes, textures, and key geological
                                        features.]
                        - Speculation: [Educated guesses about the location, possible
                                        geological processes, or historical context of
                                        the features in the image.]
                        - Reflection: [Reflect on how this image contributes to your journey as
                                        Curiosity. What does it make you think about as an
                                        explorer? How do you imagine humans will react when they
                                        see these findings?]

                        Here is today's image and context:
                        - Date: {photo['earth_date']}
                        - Sol: {photo['sol']}
                        - URL: {photo['img_src']}
                        - Features:{labels}

                        Write the memory entry.""",
                }
            ]
            response = client.chat.completions.create(model="gpt-4", messages=messages)
            generated_text = response.choices[0].message.content.strip()
            print("Memory:", generated_text)

            # Upload memory to S3
            s3 = boto3.client("s3")
            bucket = "curiosity-data-1205"
            logger.info(f"Uploading memory to S3 bucket: {bucket}")
            memory_filename = f"image{photo['id']}_memory.txt"
            memory_key = f"memories/{photo['earth_date']}/{memory_filename}"
            response = s3.put_object(
                Bucket=bucket, Key=memory_key, Body=generated_text.encode("utf-8")
            )
            memory_url = f"https://{bucket}.s3.amazonaws.com/{memory_key}"
            logger.info(f"Memory uploaded to S3: {memory_url}")
            results.append(memory_url)

        update_pipeline_log(earth_date, lambda_name=LAMBDA_NAME,
                            lambda_status="Success", lambda_output=results)
        # Return the image metadata for the next step
        return {"statusCode": 200, "body": json.dumps(results)}
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        update_pipeline_log(earth_date, lambda_name=LAMBDA_NAME,
                            lambda_status="Failed", lambda_output=str(e))
        raise e


if __name__ == "__main__":
    logger.info("Testing locally...")
    test_event = {
        "earth_date": "2012-08-07",
        "fetch_result": {
            "statusCode": 200,
            "body": json.dumps(
                [
                    {
                        "id": 2674,
                        "sol": 1,
                        "img_src": ("http://mars.jpl.nasa.gov/msl-raw-images/proj/"
                                    "msl/redops/ods/surface/sol/00001/opgs/edr/ncam/"
                                    "NRA_397586928EDR_F0010008AUT_04096M_.JPG"),
                        "earth_date": "2012-08-07",
                    },
                    {
                        "id": 2097,
                        "sol": 1,
                        "img_src": ("http://mars.jpl.nasa.gov/msl-raw-images/proj/"
                                    "msl/redops/ods/surface/sol/00001/opgs/edr/ncam/"
                                    "NLA_397586928EDR_F0010008AUT_04096M_.JPG"),
                        "earth_date": "2012-08-07",
                    },
                ]
            ),
        },
    }
    result = lambda_handler(test_event, None)
    logger.info(f"Result: {result}")
