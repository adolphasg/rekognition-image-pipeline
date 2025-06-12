import os
import sys
import time
from decimal import Decimal
import boto3

# AWS region (default to us-east-1)
region = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS clients
s3 = boto3.client('s3', region_name=region)
rekognition = boto3.client('rekognition', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)

# Folder with images
IMAGES_FOLDER = 'images'

def analyze_all_images(branch):
    bucket = os.environ.get('S3_BUCKET')
    if not bucket:
        raise ValueError("Missing S3_BUCKET environment variable")

    table_name = os.environ.get('DYNAMODB_TABLE_BETA') if branch == 'beta' else os.environ.get('DYNAMODB_TABLE_PROD')
    if not table_name:
        raise ValueError("Missing DynamoDB table environment variable")

    table = dynamodb.Table(table_name)

    for filename in os.listdir(IMAGES_FOLDER):
        if not (filename.endswith(".jpg") or filename.endswith(".png")):
            continue  # skip non-image files

        file_path = os.path.join(IMAGES_FOLDER, filename)
        s3_key = f"rekognition-input/{filename}"

        # Upload image to S3
        s3.upload_file(file_path, bucket, s3_key)
        print(f"Uploaded {filename} to s3://{bucket}/{s3_key}")

        # Analyze image with Rekognition
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': s3_key}},
            MaxLabels=10,
            MinConfidence=70
        )

        # Save results to DynamoDB
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

        print(f"Analyzed and saved labels for {filename}")

# Entry point
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python analyze_image.py <branch>")
        sys.exit(1)

    branch = sys.argv[1]
    analyze_all_images(branch)
