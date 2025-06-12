import os
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

    # Get env vars
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

    # Analyze image using Rekognition
    response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': f"rekognition-input/{filename}"}},
        MaxLabels=10,
        MinConfidence=70
    )

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

# Entry point when running script directly
if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python analyze_image.py <images_folder> <branch>")
        sys.exit(1)

    folder_path = sys.argv[1]
    branch = sys.argv[2]

    supported_extensions = ('.jpg', '.jpeg', '.png')
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(supported_extensions):
            file_path = os.path.join(folder_path, filename)
            analyze_image(file_path, branch)
