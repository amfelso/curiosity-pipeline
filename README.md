# Mars Image Processing Pipeline

![DEV Workflow](https://github.com/amfelso/curiosity-pipeline/actions/workflows/Develop.yml/badge.svg)
![PROD Workflow](https://github.com/amfelso/curiosity-pipeline/actions/workflows/Release.yml/badge.svg)

This application automates the retrieval, processing, and embedding of Mars rover images using AWS Step Functions and serverless architecture. It demonstrates the use of Step Functions to orchestrate Lambda functions, S3, DynamoDB, and Pinecone for a robust, event-driven data pipeline optimized for Retrieval-Augmented Generation (RAG) applications.

## Overview

The pipeline runs on a nightly schedule (disabled by default to avoid incurring charges) and performs the following steps:

1. **Fetch Latest Images**: Retrieves the latest images from NASA's Mars Rover API.
2. **Process Metadata**: Structures image metadata into a flat JSON object, optimized for RAG, and stores it in S3.
3. **Generate Embeddings**: Creates vector embeddings for the images using a pre-trained model and stores them in Pinecone with associated metadata.

### Project Structure

- **`functions`**: Code for the Lambda functions that perform each pipeline step (fetching images, processing metadata, generating embeddings).
- **`statemachines`**: Definition for the Step Function state machine that orchestrates the pipeline.
- **`tests`**: Unit tests for Lambda functions' application logic.
- **`template.yaml`**: AWS SAM template defining the application's resources.

---

## Setup and Deployment

### Deploying the Pipeline

1. Install the AWS SAM CLI. See [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) for installation instructions.
2. Clone the repository and navigate to the project directory.
3. Build and deploy the application:
   ```bash
   sam build
   sam deploy --guided
   ```

### Enabling the Schedule

The pipeline schedule is disabled by default. To enable it:

1. Open the `template.yaml` file in the project directory.
2. Locate the `NightlySchedule` resource under the `Events` section of the state machine definition.
3. Update the `Enabled` property to `True`:
   ```yaml
   NightlySchedule:
     Type: Schedule
     Properties:
       Description: Schedule to run the Mars Image Processing State Machine nightly
       Enabled: True
       Schedule: "rate(1 day)"

### Tests

Tests are defined in the tests folder. Use pip to install dependencies and run the tests.

```bash
# Install test dependencies
pip install -r tests/requirements.txt --user

# Run unit tests
python -m pytest tests/unit -v

# Run integration tests (requires the stack to be deployed)
AWS_SAM_STACK_NAME="mars-image-pipeline" python -m pytest tests/integration -v
```

## Resources

- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html): Introduction to SAM specification, the SAM CLI, and serverless application concepts.
- [NASA Mars Rover API](https://api.nasa.gov/): Official NASA API documentation for accessing Mars rover data.
- [Pinecone Documentation](https://www.pinecone.io/docs/): Guide to setting up and managing vector embeddings for efficient RAG workflows.
