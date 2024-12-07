import json
import os
from dotenv import load_dotenv
import logging
import requests
import boto3
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

# Define logger
logger = logging.getLogger()
logger.setLevel("INFO")


def analyze_image(input_img):
    
    rek_client = boto3.client('rekognition')

    with open(input_img, 'rb') as image:
        response = rek_client.detect_labels(Image={'Bytes': image.read()})

    labels = response['Labels']
    label_names = ''
    for label in labels:
        name = label['Name']
        confidence = label['Confidence']
        if confidence > 95:
            label_names = label_names + name + ","

    return label_names


def lambda_handler(event, context):
    """
    Lambda function to generate diary entries and memory entries for the given date.
    """
    fetch_result = event["fetch_result"]
    body = fetch_result.get("body", '[]')
    photos = json.loads(body)
    results = []
    
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
        client = OpenAI(api_key = OPENAI_API_KEY)

        # Prompt a memory for the image
        messages = [
            {
                "role": "system",
                "content":
                    f"""You are Curiosity, NASA's Mars rover, exploring the Red Planet.
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

                    Write the memory entry."""
            }
        ]
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        generated_text = response.choices[0].message.content.strip()
        print("Memory:", generated_text)

        # Upload memory to S3
        s3 = boto3.client('s3')
        bucket = "curiosity-data-1205"
        logger.info(f"Uploading memory to S3 bucket: {bucket}")
        memory_filename = f"image{photo['id']}_memory.txt"
        memory_key = f"memories/{photo['earth_date']}/{memory_filename}"
        response = s3.put_object(
            Bucket=bucket,
            Key=memory_key,
            Body=generated_text.encode('utf-8')
        )
        memory_url = f"https://{bucket}.s3.amazonaws.com/{memory_key}"
        logger.info(f"Memory uploaded to S3: {memory_url}")
        results.append(memory_url)
    
    # Return the image metadata for the next step
    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }


if __name__ == "__main__":
    # Test the function locally
    logger.info("Testing locally...")
    test_event = {
        "earth_date": "2024-01-08",
        "fetch_result": {
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
                }])
            }
        }
    result = lambda_handler(test_event, None)
    logger.info(f"Result: {result}")
