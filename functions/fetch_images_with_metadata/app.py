import requests
import json
import os
import math
from datetime import datetime
from dotenv import load_dotenv
import logging
import random
import sys

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
LAMBDA_NAME = "Lambda1: FetchImages"
LANDING_DATE = datetime(2012, 8, 6)  # Curiosity landing date
SOL_LENGTH_IN_DAYS = 1.027491252  # Length of a sol in Earth days

def earth_date_to_sol(earth_date):
    """
    Convert Earth date to Mars sol.
    """
    earth_date_obj = datetime.strptime(earth_date, "%Y-%m-%d")
    days_since_landing = (earth_date_obj - LANDING_DATE).days + 1
    sol = math.floor(days_since_landing / SOL_LENGTH_IN_DAYS)
    logger.info(f"The day is {earth_date_obj.strftime('%Y-%m-%d')} and the sol is {sol}.")
    return sol


def fetch_images_by_sol(sol, NASA_API_KEY):
    """
    Fetch images from NASA's Mars Rover API for a specific sol.
    Returns NAVCAM photos only.
    """
    base_url = "https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos"
    params = {
        "sol": sol,
        "api_key": NASA_API_KEY
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()
    photos = data.get("photos", [])
    
    # Filter for NAVCAM photos
    navcam_photos = [photo for photo in photos if photo["camera"]["name"] == "NAVCAM"]
    return navcam_photos


def lambda_handler(event, context):
    """
    Lambda function to fetch 1-5 random images from Curiosity on the specified date.
    Input: earth_date (str) - The Earth date for which to fetch images (YYYY-MM-DD)
    """
    earth_date = event.get("earth_date")
    if not earth_date:
        raise ValueError("Missing 'earth_date' in the input event.")
    try:
        datetime.strptime(earth_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid 'earth_date' format. Expected YYYY-MM-DD, got '{earth_date}'.")

    nasa_api_key = os.getenv("NASA_API_KEY")
    if not nasa_api_key:
        raise ValueError("NASA_API_KEY is not set in the environment variables.")

    try:
        num_images = int(os.getenv("NUM_IMAGES", 5))
        sol = earth_date_to_sol(earth_date)
        
        logger.info(f"Fetching images for Sol {sol}...")
        navcam_photos = fetch_images_by_sol(sol, nasa_api_key) or []
        if navcam_photos:
            logger.info(f"Found {len(navcam_photos)} NAVCAM photos.")
            logger.info(f"Randomly sampling {num_images} photos...")
            random.shuffle(navcam_photos)
            sampled_photos = navcam_photos[:num_images]
            navcam_photos = [{k: v for k, v in photo.items() if k in
                            ["id", "earth_date", "sol", "img_src"]} for photo in sampled_photos]
            update_pipeline_log(earth_date, sol=sol, lambda_name=LAMBDA_NAME, lambda_status="Success", lambda_output=navcam_photos)
        return {
                "statusCode": 200,
                "body": json.dumps(navcam_photos)
            }
    except Exception as e:
        logger.error(f"An internal error occurred: {e}")
        update_pipeline_log(earth_date, lambda_name=LAMBDA_NAME, lambda_status="Error", lambda_output=str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


if __name__ == "__main__":
    logger.info("Testing locally...")
    test_event = {"earth_date": "2012-08-07"}
    result = lambda_handler(test_event, None)
    logger.info(f"Result: {result}")