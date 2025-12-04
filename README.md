# Curiosity Rover Memory System

[![.github/workflows/Develop.yml](https://github.com/amfelso/curiosity-pipeline/actions/workflows/Develop.yml/badge.svg)](https://github.com/amfelso/curiosity-pipeline/actions/workflows/Develop.yml)
[![.github/workflows/Release.yml](https://github.com/amfelso/curiosity-pipeline/actions/workflows/Release.yml/badge.svg?branch=release)](https://github.com/amfelso/curiosity-pipeline/actions/workflows/Release.yml)

This application automates the retrieval, processing, and embedding of Mars rover images into a memory system designed for Retrieval-Augmented Generation (RAG). The pipeline is built on AWS Step Functions and serverless architecture to orchestrate data processing with scalability and efficiency.

## Overview

The pipeline runs on a nightly schedule (disabled by default to save costs) and performs the following steps:

0. **Daily Scheduler**:

   - Triggers the pipeline on a nightly schedule to automate the retrieval and processing of Mars rover images.

1. **Fetch Images and Metadata**:

   - Retrieves 1-5 random images from NASA's Mars Rover API for a specific date (Earth date or sol).
   - Outputs a list of image URLs and associated metadata.

2. **Generate Memories and Diary**:

   - Writes daily memory entries for each image, describing key features, speculation, and reflection.
   - Writes a daily diary entry summarizing all image memories for the date.
   - Stores these entries in an **S3 bucket** structured by date.

3. **Embed Memories into PineconeDB**:
   - Embeds memories and diary entries into Pinecone for use in RAG workflows and chatbot conversations.

The pipeline is designed to enable a chatbot with contextual memory, simulating the ability to "remember" and reference Mars Rover data in conversations.

---

## Project Structure

- **`functions`**: Code for Lambda functions handling each pipeline step:
  - `daily_scheduler`: Triggers the pipeline on a nightly schedule.
  - `fetch_images_with_metadata`: Retrieves images and metadata.
  - `generate_memories_and_diary`: Creates structured memory and diary entries in S3.
  - `embed_memories_to_pinecone`: Embeds memories and diary entries for RAG use.
- **`statemachines`**: Step Function definition orchestrating the pipeline's tasks.
- **`tests`**: Unit and integration tests for pipeline components.
- **`template.yaml`**: AWS SAM template defining serverless resources.

---

## Setup and Deployment

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/amfelso/curiosity-pipeline.git
   cd curiosity-pipeline
   ```

2. **Set up your environment**
   ```bash
   make setup
   ```
   This will:
   - Install Python dependencies from `layers/curiosity_pipeline/requirements.txt`
   - Create a `.env` file from `.env.example`

3. **Configure your API keys**
   Edit the `.env` file with your actual API keys:
   ```bash
   PINECONE_API_KEY=your-pinecone-api-key-here
   OPENAI_API_KEY=your-openai-api-key-here
   NASA_API_KEY=your-nasa-api-key-here
   ```

### Available Make Commands

- `make check-tools` - Verify required tools installed
- `make setup` - Create venv, install dependencies, and create `.env`
- `make install` - Install Python dependencies only
- `make login` - Configure AWS credentials from `.env`
- `make test` - Run all tests (automatically loads `.env`)
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests only (requires deployed stack)
- `make lint` - Run flake8 linter and SAM template validation
- `make build` - Build SAM application
- `make deploy` - Lint, test, build, and deploy to AWS
- `make clean` - Clean build artifacts, venv, and Python cache files

### Deploying the Pipeline

**Automatic Deployment:**
Pipeline will automatically deploy via Github Actions when code updates are merged to the release branch.

**Manual Deployment:**
```bash
make deploy
```

This will lint, test, build, and deploy the application to AWS using SAM.

## **Simulated Dates Table and EventBridge**

The **Simulated Dates Table** and **EventBridge** work together to manage and trigger the Mars Rover simulation.

### **Simulated Dates Table**

This DynamoDB table stores the current Earth date for each active simulation. It allows the simulation to track and increment the Earth date daily or maintain a static date for testing purposes.

#### **Table Structure**

| Attribute       | Type   | Description                                                              |
| --------------- | ------ | ------------------------------------------------------------------------ |
| `simulation_id` | String | Primary key that uniquely identifies a simulation (e.g., `mvp`, `test`). |
| `earth_date`    | String | Current Earth date for the simulation in `YYYY-MM-DD` format.            |

#### **Example Table Entry**

```json
{
  "simulation_id": "mvp",
  "earth_date": "2012-08-06"
}
```

### **EventBridge and Daily Scheduler**

EventBridge is used to schedule the simulation’s daily updates. It triggers the **DailySchedulerLambda**, which handles the following tasks:

1. **Fetch the Simulation Date**:

   - Reads the current `earth_date` for the specified `simulation_id` from the **Simulated Dates Table**.

2. **Increment the Date**:

   - Increments the `earth_date` for simulations like `mvp`. For `test`, the date remains static.

3. **Trigger the Pipeline**:
   - Starts the Step Function for the pipeline with the current `earth_date`.

#### **EventBridge Rule**

- **Frequency**: `"rate(1 day)"` ensures the simulation progresses daily.
- **Target**: The rule invokes the **DailySchedulerLambda** with a payload specifying the `simulation_id`.

#### **Example EventBridge Payload**

```json
{
  "simulation_id": "mvp"
}
```

### Enabling the Schedule

The pipeline's nightly schedule is disabled by default. To enable it:

1. Open the `template.yaml` file in the project directory.
2. Locate the `MVPEventBridgeRule` resource under the `Resources` section.
3. Update the `State` property to `ENABLED`:

```yaml
MVPEventBridgeRule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: "rate(1 day)"
    Targets:
      - Arn: !GetAtt DailySchedulerLambda.Arn
        Id: "DailySchedulerLambdaTarget"
        Input: '{"simulation_id": "mvp"}'
    State: DISABLED
```

---

## **DynamoDB Pipeline Log**

The DynamoDB pipeline log is used to track the execution status and outputs of each stage in the pipeline. It ensures a complete record of the pipeline’s progress and aids in debugging or auditing.

### **Table Name**

- `PipelineTransactionLogTable`

### **Primary Key**

- `EarthDate` (String): Represents the Earth date corresponding to the pipeline run.

### **Attributes**

The table structure includes the following attributes:

| Attribute                   | Type   | Description                                                                         |
| --------------------------- | ------ | ----------------------------------------------------------------------------------- |
| `EarthDate`                 | String | Primary key indicating the Earth date of the pipeline execution.                    |
| `sol`                       | Number | Corresponding Mars Sol (Martian day) for the Earth date.                            |
| `Lambda1__FetchImages`      | Map    | Contains the status, output, and update timestamp for the Fetch Images Lambda.      |
| `Lambda2__GenerateMemories` | Map    | Contains the status, output, and update timestamp for the Generate Memories Lambda. |
| `Lambda3__EmbedToPinecone`  | Map    | Contains the status, output, and update timestamp for the Embed to Pinecone Lambda. |
| `updated_at`                | String | Timestamp of the most recent update to the log entry.                               |

### **Lambda Logs Structure**

Each Lambda log entry is stored as a map with the following keys:

| Key          | Type     | Description                                                      |
| ------------ | -------- | ---------------------------------------------------------------- |
| `output`     | List/Map | The output of the Lambda, such as URLs, metadata, or embeddings. |
| `status`     | String   | Execution status of the Lambda (`Success`, `Error`, etc.).       |
| `updated_at` | String   | Timestamp of the last update for this Lambda entry.              |

### **Example Log Entry**

```json
{
  "EarthDate": "2012-08-07",
  "sol": 1,
  "Lambda1__FetchImages": {
    "output": [
      {
        "earth_date": "2012-08-07",
        "id": 2674,
        "img_src": "http://mars.jpl.nasa.gov/msl-raw-images/proj/msl/redops/ods/surface/sol/00001/opgs/edr/ncam/NRA_397586928EDR_F0010008AUT_04096M_.JPG",
        "sol": 1
      }
    ],
    "status": "Success",
    "updated_at": "2024-12-07T20:42:50.015223"
  },
  "Lambda2__GenerateMemories": {
    "output": [
      "https://curiosity-data.s3.amazonaws.com/memories/2012-08-07/image2674_memory.txt"
    ],
    "status": "Success",
    "updated_at": "2024-12-07T21:09:47.448240"
  },
  "Lambda3__EmbedToPinecone": {
    "output": [
      {
        "date": "2012-08-07",
        "id": "4a8f85ba-bd21-404c-8de8-a85ee5801396",
        "s3_url": "https://curiosity-data.s3.amazonaws.com/memories/2012-08-07/image2674_memory.txt",
        "type": "memory"
      }
    ],
    "status": "Success",
    "updated_at": "2024-12-07T21:03:25.350127"
  },
  "updated_at": "2024-12-07T21:09:47.448240"
}
```

### **Usage**

1. **Log Updates:**
   Each Lambda function updates its corresponding entry in the DynamoDB log upon completion or failure.
2. **Tracking Progress:**
   Use the `EarthDate` key to retrieve pipeline logs for a specific date and check the progress or status of each Lambda.
3. **Error Handling:**
   The `status` field in each Lambda log helps identify and debug pipeline failures.

## Folder Structure for Memories

Memories are stored in an S3 bucket with the following structure for simplicity and cost savings:

```plaintext
memories/
├── YYYY-MM-DD/
│   ├── image1_memory.txt
│   ├── image2_memory.txt
│   └── diary.txt
```

- **`imageX_memory.txt`**: Contains memory details for each image (data, description, speculation, and reflection).
- **`diary.txt`**: Summarizes the day’s memories into a single diary entry.

---

## Tests

Tests ensure the functionality of individual Lambda functions and the pipeline as a whole.

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run only integration tests (requires the stack to be deployed)
make test-integration
```

**Note:** Integration tests require the SAM stack to be deployed to AWS first. Unit tests can run locally without any AWS resources.

---

## Resources

- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html): Introduction to SAM specification, the SAM CLI, and serverless application concepts.
- [NASA Mars Rover API](https://api.nasa.gov/): Official NASA API documentation for accessing Mars rover data.
- [Pinecone Documentation](https://www.pinecone.io/docs/): Guide to setting up and managing vector embeddings for efficient RAG workflows.
