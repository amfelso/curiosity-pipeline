import logging
from time import sleep
from unittest import TestCase
from functions.daily_scheduler import app
import boto3


class TestStateMachine(TestCase):
    """
    This integration test will:
    - Call the Daily Scheduler Lambda directly.
    - Verify the Step Function execution status using the run ID returned by the Lambda.
    """

    def _wait_execution(self, execution_arn: str):
        """
        Wait for the Step Function execution to complete and verify its status.
        """
        client = boto3.client("stepfunctions")
        while True:
            response = client.describe_execution(executionArn=execution_arn)
            status = response["status"]
            if status == "RUNNING":
                logging.info(f"Execution {execution_arn} is still running, waiting")
                sleep(3)
            else:
                break

        assert status == "SUCCEEDED", f"Execution {execution_arn} failed with status {status}"

    def test_state_machine(self):
        """
        Test the end-to-end integration:
        - Call the Daily Scheduler Lambda with a test simulation ID.
        - Wait for the Step Function execution to complete.
        """
        # Step 1: Prepare the input payload for the Daily Scheduler Lambda
        input_payload = {"simulation_id": "test"}  # Use "test" for controlled execution

        # Step 2: Invoke the Lambda directly
        response = app.lambda_handler(input_payload, "")
        assert response["statusCode"] == 200, f"Lambda invocation failed: {response}"

        body = response["body"]
        step_function_arn = body["step_function_arn"]
        execution_arn = body["step_function_run_id"]
        logging.info(f"Step Function triggered: {step_function_arn}, Execution ID: {execution_arn}")

        # Step 3: Wait for the Step Function execution to complete and verify
        self._wait_execution(execution_arn)