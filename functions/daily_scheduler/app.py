import json
import logging
import os
import sys
import boto3
from datetime import datetime, timedelta
from dotenv import load_dotenv

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
LAMBDA_NAME = "Lambda0: Daily Scheduler"

# Initialize clients
dynamodb = boto3.resource("dynamodb")
stepfunctions = boto3.client("stepfunctions")


def lambda_handler(event, context):
    # Get environment variables
    SIMULATED_DATES_TABLE = os.environ["SIMULATED_DATES_TABLE"]
    STEP_FUNCTION_ARN = os.environ["STEP_FUNCTION_ARN"]
    if not SIMULATED_DATES_TABLE or not STEP_FUNCTION_ARN:
        raise ValueError("Environment variables not set.")

    # Get simulation_id from the EventBridge input
    simulation_id = event.get("simulation_id", "test") # Default to test
        
    # Fetch current earth_date for the given simulation_id
    table = dynamodb.Table(SIMULATED_DATES_TABLE)
    response = table.get_item(Key={"simulation_id": simulation_id})

    # Handle missing simulation_id by seeding a new simulation
    if "Item" not in response:
        logger.warning(f"Simulation ID '{simulation_id}' not found. Creating a new entry.")
        default_date = "2012-08-06"  # Default starting date for new simulations
        table.put_item(
            Item={
                "simulation_id": simulation_id,
                "earth_date": default_date
            }
        )
        logger.info(f"Created new simulation '{simulation_id}' with Earth date {default_date}.")
        current_date_str = default_date
    else:
        current_date_str = response["Item"]["earth_date"]
        logger.info(f"Current date for simulation '{simulation_id}': {current_date_str}")
    
    try:
        # Determine if date should increment
        if simulation_id != "test":
            # Increment date for non-test simulations
            current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
            next_date = current_date + timedelta(days=1)
            next_date_str = next_date.strftime("%Y-%m-%d")

            # Update the SimulatedDates table with the incremented date
            table.update_item(
                Key={"simulation_id": simulation_id},
                UpdateExpression="SET earth_date = :next_date",
                ExpressionAttributeValues={":next_date": next_date_str}
            )
            logger.info(f"Updated date for simulation '{simulation_id}' to: {next_date_str}")
        else:
            logger.info(f"No date increment for simulation '{simulation_id}' (test mode).")
        
        # Start the Step Function with the current date
        step_function_input = {
            "earth_date": current_date_str
        }
        response = stepfunctions.start_execution(
            stateMachineArn=STEP_FUNCTION_ARN,
            input=json.dumps(step_function_input)
        )
        step_function_run_id = response["executionArn"]
        logger.info(f"Triggered Step Function with Earth date {current_date_str}.")
        update_pipeline_log(earth_date=current_date_str, lambda_name=LAMBDA_NAME,
                            lambda_status="SUCCESS", lambda_output=step_function_run_id)
        return {
            "statusCode": 200,
            "body": {"earth_date": current_date_str, "step_function_arn": STEP_FUNCTION_ARN,
                     "step_function_run_id": step_function_run_id}
        }
    
    except Exception as e:
        logger.error(f"An internal error occurred: {e}")
        update_pipeline_log(earth_date=current_date_str, lambda_name=LAMBDA_NAME,
                            lambda_status="ERROR", lambda_output=str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


if __name__ == "__main__":
    logger.info("Testing locally...")
    test_event = {"simulation_id": "test"}
    result = lambda_handler(test_event, None)
    logger.info(f"Result: {result}")