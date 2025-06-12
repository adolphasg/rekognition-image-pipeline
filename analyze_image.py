import os
import sys
import boto3
import time
from decimal import Decimal

# Get AWS region (required to avoid NoRegionError)
region = os.environ.get('AWS_REGION', 'us-east-1')  # Default to us-east-1

# Initialize clients with region
s3 = boto3.client('s3', region_name=region)
rekognition = boto3.client('rekognition', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)

def analyze_image(file_path, branch):
    filename = os.path.basename(file_path)
    bucket = os.environ.get('AWS_S3_BUCKET')
    input_prefix = 'rekognition-input/'

    if not bucket:
        raise ValueError("Missing AWS_S3_BUCKET environment variable.")

    # Upload image to S3
    s3.upload_file(file_path, bucket, input_prefix + filename)

    # Analyze image using Rekognition
    response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': input_prefix + filename}},
        MaxLabels=10,
        MinConfidence=70
    )

    # Select DynamoDB table based on branch
    table_name = (
        os.environ.get('DYNAMODB_TABLE_BETA') if branch == 'beta'
        else os.environ.get('DYNAMODB_TABLE_PROD')
    )

    if not table_name:
        raise ValueError("Missing environment variable for DynamoDB table.")

    table = dynamodb.Table(table_name)

    # Write labels and confidence scores to DynamoDB
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

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python analyze_image.py <file_path> <branch>")
        sys.exit(1)

    file_path = sys.argv[1]
    branch = sys.argv[2]

    if not os.path.isfile(file_path):
        print(f"Error: File not found -> {file_path}")
        sys.exit(1)

    analyze_image(file_path, branch)
