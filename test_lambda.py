import boto3
from botocore.config import Config
import json
import time
# Initialize Lambda client

config = Config(
    read_timeout=600,  # 10 minutes
    connect_timeout=60,
    retries={'max_attempts': 0}
)
lambda_client = boto3.client('lambda', region_name='us-east-1', config=config)

page_url = "https://documents.pelles.ai/level-app-staging/1949fed8-2d02-4a2a-a696-43ca1cf46d08/bc688860-8f5c-40ef-828f-f0312174d6ae/5?se=2025-06-11T09%3A21%3A09Z&sp=r&sv=2023-11-03&sr=b&sig=1KSA6U8t7rpIs4MeHr9CK0GpQpcJO6EOXWRtgKdl8so%3D"

# page_url = 'https://morth.nic.in/sites/default/files/dd12-13_0.pdf'

print("\n" + "=" * 50)
print("Testing Lambda function...")

# Invoke function
start_time = time.time()
response = lambda_client.invoke(
    FunctionName='aws-serverless-docling',
    Payload=json.dumps({
        'presignedUrl': page_url, 'isImagePresent': True,
    })
)
end_time = time.time()

# Parse response
print(f"Time taken: {round(end_time - start_time, 2)} seconds")
result = json.loads(response['Payload'].read())
print(f"Processing result: {result}")