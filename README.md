# Curiosity Rover Memory System

![DEV Workflow](https://github.com/amfelso/curiosity-pipeline/actions/workflows/Develop.yml/badge.svg)
![PROD Workflow](https://github.com/amfelso/curiosity-pipeline/actions/workflows/Release.yml/badge.svg)

![DEV Workflow](https://github.com/amfelso/curiosity-pipeline/actions/workflows/Develop.yml/badge.svg)
![PROD Workflow](https://github.com/amfelso/curiosity-pipeline/actions/workflows/Release.yml/badge.svg)

This application automates the retrieval, processing, and embedding of Mars rover images into a memory system designed for Retrieval-Augmented Generation (RAG). The pipeline is built on AWS Step Functions and serverless architecture to orchestrate data processing with scalability and efficiency.

## Overview

The pipeline runs on a nightly schedule (disabled by default to save costs) and performs the following steps:

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
  - `fetch_images_with_metadata`: Retrieves images and metadata.
  - `generate_memories_and_diary`: Creates structured memory and diary entries in S3.
  - `embed_memories_to_pinecone`: Embeds memories and diary entries for RAG use.
- **`statemachines`**: Step Function definition orchestrating the pipeline's tasks.
- **`tests`**: Unit and integration tests for pipeline components.
- **`template.yaml`**: AWS SAM template defining serverless resources.

---

## Setup and Deployment

### Deploying the Pipeline

Pipeline will automatically deploy via Github action when code updates are merged to release branch.

### Enabling the Schedule

The pipeline's nightly schedule is disabled by default. To enable it:

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
   ```

---

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
# Install test dependencies
pip install -r tests/requirements.txt --user

# Run unit tests
python -m pytest tests/unit -v

# Run integration tests (requires the stack to be deployed)
AWS_SAM_STACK_NAME="mars-image-pipeline" python -m pytest tests/integration -v
```

---

## Resources

- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html): Introduction to SAM specification, the SAM CLI, and serverless application concepts.
- [NASA Mars Rover API](https://api.nasa.gov/): Official NASA API documentation for accessing Mars rover data.
- [Pinecone Documentation](https://www.pinecone.io/docs/): Guide to setting up and managing vector embeddings for efficient RAG workflows.
