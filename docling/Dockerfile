# Use AWS Lambda Python 3.13 base image (Amazon Linux 2023 minimal)
FROM public.ecr.aws/lambda/python:3.13

# Set the working directory to the Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements file first
COPY docling/requirements.txt ${LAMBDA_TASK_ROOT}/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Optional: Set Torch cache directory
ENV TORCH_HOME=/tmp/torch

# Copy the rest of the application code
COPY docling/ ${LAMBDA_TASK_ROOT}/

# Set the entry point for the Lambda function
CMD ["lambda_function.lambda_handler"]