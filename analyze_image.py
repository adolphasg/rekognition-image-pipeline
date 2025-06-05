import os
import boto3
import time
from decimal import Decimal
from botocore.exceptions import BotoCoreError, ClientError
from boto3.dynamodb.conditions import Key

# Initialize AWS clients
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')

def analyze_image(file_path, branch):
    try:
        filename = os.path.basename(file_path)
        print(f"\nAnalyzing: {filename}")

        # Get environment variables
        bucket = os.getenv('S3_BUCKET')
        if not bucket:
            raise EnvironmentError("Missing S3_BUCKET environment variable.")

        table_name = (
            os.getenv('DYNAMODB_TABLE_BETA') if branch == 'beta'
            else os.getenv('DYNAMODB_TABLE_PROD')
        )
        if not table_name:
            raise EnvironmentError("Missing DynamoDB table name environment variable.")

        table = dynamodb.Table(table_name)

        # Upload image to S3
        s3_key = f"rekognition-input/{filename}"
        s3.upload_file(file_path, bucket, s3_key)
        print(f"Uploaded {filename} to S3 bucket: {bucket}")

        # Wait briefly for S3 propagation
        time.sleep(2)

        # Call Rekognition
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': s3_key}},
            MaxLabels=10,
            MinConfidence=70
        )

        # Convert float confidence to Decimal
        labels = [
            {
                'Name': label['Name'],
                'Confidence': Decimal(str(label['Confidence']))
            }
            for label in response['Labels']
        ]

        # Store results in DynamoDB
        table.put_item(Item={
            'filename': filename,
            'labels': labels,
            'timestamp': int(time.time())
        })

        print(f"Stored results for {filename} in table: {table_name}")

    except (BotoCoreError, ClientError, Exception) as e:
        print(f"Error processing {file_path}: {e}")
