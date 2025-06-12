import os
import sys
import time
from decimal import Decimal
import boto3

# AWS setup
region = os.environ.get('AWS_REGION', 'us-east-1')
s3 = boto3.client('s3', region_name=region)
rekognition = boto3.client('rekognition', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)

def process_folder(images_folder, branch):
    bucket = os.environ.get('S3_BUCKET')
    if not bucket:
        raise ValueError("Missing S3_BUCKET environment variable")

    # Choose DynamoDB table
    table_name = os.environ.get('DYNAMODB_TABLE_BETA') if branch == 'beta' else os.environ.get('DYNAMODB_TABLE_PROD')
    if not table_name:
        raise ValueError("Missing DynamoDB table environment variable")

    table = dynamodb.Table(table_name)

    for filename in os.listdir(images_folder):
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        file_path = os.path.join(images_folder, filename)
        s3_key = f"rekognition-input/{filename}"

        # Upload to S3
        s3.upload_file(file_path, bucket, s3_key)
        print(f"Uploaded {filename}")

        # Analyze with Rekognition
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': s3_key}},
            MaxLabels=10,
            MinConfidence=70
        )

        # Save to DynamoDB
        table.put_item(Item={
            'filename': filename,
            'labels': [
                {'Name': l['Name'], 'Confidence': Decimal(str(l['Confidence']))}
                for l in response.get('Labels', [])
            ],
            'timestamp': int(time.time())
        })
        print(f"Saved results for {filename}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python analyze_images_batch.py <images_folder> <branch>")
        sys.exit(1)

    folder = sys.argv[1]
    branch = sys.argv[2]

    if not os.path.isdir(folder):
        print(f"Folder not found: {folder}")
        sys.exit(1)

    process_folder(folder, branch)
    print("Processing complete.")
