import os
import sys
import time
from decimal import Decimal
import boto3

# Get AWS region (default to us-east-1 if not set)
region = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS clients
s3 = boto3.client('s3', region_name=region)
rekognition = boto3.client('rekognition', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)

def analyze_image(file_path, branch):
    filename = os.path.basename(file_path)

    bucket = os.environ.get('S3_BUCKET')
    if not bucket:
        raise ValueError("Missing environment variable: S3_BUCKET")

    table_name = (
        os.environ.get('DYNAMODB_TABLE_BETA') if branch == 'beta'
        else os.environ.get('DYNAMODB_TABLE_PROD')
    )
    if not table_name:
        raise ValueError("Missing environment variable for DynamoDB table.")

    table = dynamodb.Table(table_name)

    # Upload image to S3
    s3.upload_file(file_path, bucket, f"rekognition-input/{filename}")
    print(f"Uploaded {filename} to S3 bucket {bucket}")

    # Analyze image with Rekognition
    response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': f"rekognition-input/{filename}"}},
        MaxLabels=10,
        MinConfidence=70
    )
    print(f"Rekognition response for {filename}: {response}")

    if response.get('Labels'):
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
        print(f"Successfully wrote labels for {filename} to DynamoDB table: {table_name}")
    else:
        print(f"No labels detected in {filename}. Nothing written to DynamoDB.")

def list_items(table_name):
    table = dynamodb.Table(table_name)
    response = table.scan()
    items = response.get('Items', [])

    print(f"\nFound {len(items)} items in table '{table_name}':\n")

    for item in items:
        print(f"Filename: {item.get('filename')}")
        print(f"Timestamp: {item.get('timestamp')}")
        print("Labels:")
        for label in item.get('labels', []):
            print(f"  - {label['Name']}: {label['Confidence']}")
        print("-" * 40)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        file_path = sys.argv[1]
        branch = sys.argv[2]
        analyze_image(file_path, branch)

    elif len(sys.argv) == 2:
        table_name = sys.argv[1]
        list_items(table_name)

    else:
        print("Usage:")
        print("  To analyze an image: python analyze_image.py <file_path> <branch>")
        print("  To list DynamoDB items: python analyze_image.py <table_name>")
        sys.exit(1)
