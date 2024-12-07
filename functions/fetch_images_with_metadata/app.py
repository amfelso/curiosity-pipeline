import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
import random

# Load environment variables from .env file
load_dotenv()

# Define logger
logger = logging.getLogger()
logger.setLevel("INFO")

# Set your NASA API key here (or fetch it from environment variables)
NASA_API_KEY = os.environ["NASA_API_KEY"]
if not NASA_API_KEY:
    raise ValueError("NASA_API_KEY is not set in the environment variables.")
num_images = os.getenv("num_images", 5)


def earth_date_to_sol(earth_date):
    # Constants
    landing_date = datetime(2012, 8, 6)  # Curiosity landing date
    sol_length_in_days = 1.027491252  # Length of a sol in Earth days

    # Calculate difference in days
    earth_date_obj = datetime.strptime(earth_date, "%Y-%m-%d")
    days_since_landing = (earth_date_obj - landing_date).days + 1

    # Convert to sols
    sol = days_since_landing / sol_length_in_days
    logger.info(f"The day is {earth_date_obj} and the sol is {sol}.")

    return round(sol)


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

    Input: earth_date (str) - The Earth date for which to fetch images (YYYY-MM-DD)
    """
    earth_date = event["earth_date"]
    sol = earth_date_to_sol(earth_date)
    
    # Fetch images for the sol
    logger.info(f"Fetching images for Sol {sol}...")
    photos = fetch_images_by_sol(sol)
    if photos:
        logger.info(f"Found {len(photos)} photos.")
        logger.info(f"Randomly sampling {num_images} NAVCAM photos...")
        navcam_photos = [photo for photo in photos
                        if photo["camera"]["name"] == "NAVCAM"]
        random.shuffle(navcam_photos)
        sampled_photos = navcam_photos[:num_images]
        # filter each item to only return key fields
        sampled_photos = [{k: v for k, v in photo.items() if k in
                         ["id", "earth_date", "sol", "img_src"]} for photo in sampled_photos]
        return {
                "statusCode": 200,
                "body": json.dumps(sampled_photos)
            }
    else:
        logger.warning(f"No photos found for Sol {sol}.")


if __name__ == "__main__":
    # Test the function locally
    logger.info("Testing locally...")
    test_event = {"earth_date": "2012-08-07"}
    result = lambda_handler(test_event, None)
    logger.info(f"Result: {result}")