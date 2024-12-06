import requests
import json
import os
import sys
from dotenv import load_dotenv
import logging
import random

# Load environment variables from .env file
load_dotenv()

# Define logger
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Adjust log level as needed
logger.addHandler(handler)

# Set your NASA API key here (or fetch it from environment variables)
NASA_API_KEY = os.environ["NASA_API_KEY"]
if not NASA_API_KEY:
    raise ValueError("NASA_API_KEY is not set in the environment variables.")
num_images = os.getenv("num_images", 5)


def fetch_images_by_sol(sol):
    """
    Fetch images from NASA's Mars Rover API for a specific sol.
    """
    base_url = "https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos"
    params = {
        "sol": sol,
        "api_key": NASA_API_KEY
    }
    
    # Make API request
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    
    # Parse response JSON
    data = response.json()
    photos = data.get("photos", [])
    return photos


def lambda_handler(event, context):
    """
    Lambda function to fetch 1-5 random images from Curiosity on the specified date.

    Input: {'sols': [1000, 1001]}
    """
    sols = event.get("sols", [0])  # Default to the first sol if none provided
    results = []
    
    # Fetch data for each sol
    for sol in sols:
        logger.info(f"Fetching images for Sol {sol}...")
        photos = fetch_images_by_sol(sol)
        if photos:
            logger.info(f"Retrieved {len(photos)} photos for Sol {sol}.")
            logger.info(f"Randomly sampling {num_images} MASTCAM photos...")
            navcam_photos = [photo for photo in photos
                            if photo["camera"]["name"] == "NAVCAM"]
            random.shuffle(navcam_photos)
            sampled_photos = navcam_photos[:num_images]
            # filter each item to only return key fields
            sampled_photos = [{k: v for k, v in photo.items() if k in
                             ["id", "earth_date", "sol", "img_src"]} for photo in sampled_photos]
            results.extend(sampled_photos)
        else:
            logger.warning(f"No photos found for Sol {sol}.")
    
    # Return the image metadata for the next step
    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }


if __name__ == "__main__":
    # Test the function locally
    logger.info("Testing locally...")
    test_event = {"sols": [4061]}
    result = lambda_handler(test_event, None)
    logger.info(f"Result: {result}")