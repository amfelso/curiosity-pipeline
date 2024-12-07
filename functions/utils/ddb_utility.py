import boto3
from botocore.exceptions import BotoCoreError, ClientError
from datetime import datetime
import os

# DynamoDB Table Name
TABLE_NAME = os.environ["DDB_TABLE_NAME"]

# DynamoDB Client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def update_pipeline_log(earth_date, sol=None, lambda_name=None, lambda_status=None, lambda_output=None):
    """
    Update the PipelineLog table in DynamoDB with the status and output of a Lambda function.

    Each Lambda's output will be stored in its own nested structure within the DynamoDB item.
    """
    try:
        # Create timestamp
        timestamp = datetime.utcnow().isoformat()

        # Define the Lambda-specific field name
        lambda_field = lambda_name.replace(" ", "_").replace(":", "_")  # Normalize the name for DynamoDB keys

        # Prepare the update expression for the specific Lambda
        update_expression = f"SET {lambda_field} = :lambda_data, updated_at = :updated_at"
        expression_values = {
            ":lambda_data": {
                "status": lambda_status,
                "output": lambda_output,
                "updated_at": timestamp
            },
            ":updated_at": timestamp
        }

        # Add sol to the update if provided
        if sol is not None:
            update_expression += ", sol = :sol"
            expression_values[":sol"] = sol

        # Perform the update
        response = table.update_item(
            Key={"EarthDate": earth_date},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="UPDATED_NEW"
        )
        return response
    except (BotoCoreError, ClientError) as e:
        print(f"Error updating DynamoDB: {e}")
        return {"error": str(e)}