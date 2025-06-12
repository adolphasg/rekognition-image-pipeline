import os
import sys
import time
from decimal import Decimal
import boto3

# Get AWS region (default to us-east-1)
region = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS clients
s3 = boto3.client('s3', region_name=region)
rekognition = boto3.client('rekognition', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)

def analyze_image(file_path, branch):
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    filename = os.path.basename(file_path)
    bucket = os.environ.get('S3_BUCKET')
    if not bucket:
        raise ValueError("Missing S3_BUCKET environment variable")

    # Choose the DynamoDB table
    table_name = os.environ.get('DYNAMODB_TABLE_BETA') if branch == 'beta' else os.environ.get('DYNAMODB_TABLE_PROD')
    if not table_name:
        raise ValueError("Missing DynamoDB table environment variable")

    # Upload to S3
    s3_key = f"rekognition-input/{filename}"
    s3.upload_file(file_path, bucket, s3_key)

    # Detect labels with Rekognition
    response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': s3_key}},
        MaxLabels=10,
        MinConfidence=70
    )

    # Write labels to DynamoDB
    table = dynamodb.Table(table_name)
    table.put_item(Item={
        'filename': filename,
        'labels': [
            {
                'Name': label['Name'],
                'Confidence': Decimal(str(label['Confidence']))
            } for label in response['Labels']
        ],
        'timestamp': int(time.time())
    })

    print(f"Image '{filename}' analyzed and results saved to '{table_name}'")

# Run script
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python analyze_image.py <file_path> <branch>")
        sys.exit(1)

    file_path = sys.argv[1]
    branch = sys.argv[2]
    analyze_image(file_path, branch)
