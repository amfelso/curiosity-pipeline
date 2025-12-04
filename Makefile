.PHONY: help check-tools venv activate setup install login test test-unit test-integration lint build deploy clean

help:
	@echo "Available commands:"
	@echo "  make check-tools     - Verify aws, sam, python3, uv installed"
	@echo "  make setup           - Create venv, install deps, create .env"
	@echo "  make install         - Install dependencies only"
	@echo "  make login           - Configure AWS CLI from .env"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make lint            - Run flake8 and sam validate"
	@echo "  make build           - Build SAM application"
	@echo "  make deploy          - Lint, test, build, deploy to AWS"
	@echo "  make clean           - Remove build artifacts and venv"

check-tools:
	@command -v aws >/dev/null 2>&1 || (echo "AWS CLI not found (brew install awscli)" && exit 1)
	@command -v sam >/dev/null 2>&1 || (echo "SAM CLI not found (brew install aws-sam-cli)" && exit 1)
	@command -v python3 >/dev/null 2>&1 || (echo "Python 3 not found" && exit 1)
	@command -v uv >/dev/null 2>&1 || (echo "uv not found (curl -LsSf https://astral.sh/uv/install.sh | sh)" && exit 1)

setup:
	@[ ! -d .venv ] && uv venv .venv -p "3.13.0" --seed --clear || true
	@. .venv/bin/activate && pip install -q -r layers/curiosity_pipeline/requirements.txt
	@[ ! -f .env ] && cp .env.example .env || true

install:
	@pip install -q -r layers/curiosity_pipeline/requirements.txt

login:
	@export $$(grep -v '^#' .env | grep -v '^$$' | xargs) && \
	aws configure set aws_access_key_id $$AWS_ACCESS_KEY && \
	aws configure set aws_secret_access_key $$AWS_SECRET_ACCESS_KEY && \
	aws configure set region us-east-1 && aws configure set output json && \
	aws sts get-caller-identity

test:
	@export $$(grep -v '^#' .env | grep -v '^$$' | xargs) && python -m pytest tests -v

test-unit:
	@export $$(grep -v '^#' .env | grep -v '^$$' | xargs) && python -m pytest tests/unit -v

test-integration:
	@export $$(grep -v '^#' .env | grep -v '^$$' | xargs) && python -m pytest tests/integration -v

lint:
	@python -m flake8 --select F401,F821,E302,E305,E501,F841,W291 --max-line-length 100 --exclude .venv,.aws-sam
	@sam validate --lint

build:
	@sam build

deploy: lint test build
	@export $$(grep -v '^#' .env | grep -v '^$$' | xargs) && \
	sam deploy --no-confirm-changeset --no-fail-on-empty-changeset --stack-name mars-image-pipeline \
		--capabilities CAPABILITY_IAM $$([ -n "$$S3_BUCKET" ] && echo "--s3-bucket $$S3_BUCKET" || echo "--resolve-s3") \
		--parameter-overrides ParameterKey=NasaApiKey,ParameterValue=$$NASA_API_KEY \
			ParameterKey=PineconeApiKey,ParameterValue=$$PINECONE_API_KEY \
			ParameterKey=OpenAiApiKey,ParameterValue=$$OPENAI_API_KEY
	@STEP_FUNCTION_ARN=$$(aws cloudformation describe-stacks --stack-name mars-image-pipeline \
		--query 'Stacks[0].Outputs[?OutputKey==`MarsImageProcessingStateMachineArn`].OutputValue' --output text) && \
	S3_BUCKET=$$(aws cloudformation describe-stacks --stack-name mars-image-pipeline \
		--query 'Stacks[0].Outputs[?OutputKey==`MarsImageDataBucketName`].OutputValue' --output text) && \
	grep -q "STEP_FUNCTION_ARN=" .env && sed -i.bak "s|STEP_FUNCTION_ARN=.*|STEP_FUNCTION_ARN=$$STEP_FUNCTION_ARN|" .env || echo "STEP_FUNCTION_ARN=$$STEP_FUNCTION_ARN" >> .env && \
	grep -q "S3_BUCKET=" .env && sed -i.bak "s|S3_BUCKET=.*|S3_BUCKET=$$S3_BUCKET|" .env || echo "S3_BUCKET=$$S3_BUCKET" >> .env && \
	rm -f .env.bak

clean:
	@rm -rf .aws-sam .venv .pytest_cache .DS_Store
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete