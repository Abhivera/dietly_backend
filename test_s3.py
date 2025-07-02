import boto3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION','ap-south-1')

print("AWS_ACCESS_KEY_ID =", aws_access_key_id)
print("AWS_SECRET_ACCESS_KEY =", aws_secret_access_key)

s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

response = s3.list_buckets()
print("Buckets:", [b['Name'] for b in response['Buckets']])
