# analyze_image.py

import os
import boto3
import time

region = os.getenv("AWS_REGION")

s3 = boto3.client("s3", region_name=region)
rekognition = boto3.client("rekognition", region_name=region)
dynamodb = boto3.resource("dynamodb", region_name=region)

def analyze_image(file_path, branch):
    filename = os.path.basename(file_path)
    bucket = os.environ['S3_BUCKET']
    table_name = os.environ['DYNAMODB_TABLE_BETA'] if branch == 'beta' else os.environ['DYNAMODB_TABLE_PROD']
    table = dynamodb.Table(table_name)

    # Upload image to S3
    s3.upload_file(file_path, bucket, f"rekognition-input/{filename}")

    # Rekognition call
    response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': f"rekognition-input/{filename}"}},
        MaxLabels=10,
        MinConfidence=70
    )

    labels = [{'Name': label['Name'], 'Confidence': round(label['Confidence'], 2)} for label in response['Labels']]

    # Store results in DynamoDB
    table.put_item(Item={
        'filename': filename,
        'labels': labels,
        'timestamp': int(time.time()),
        'branch': branch
    })

if __name__ == "__main__":
    import sys
    file_path = sys.argv[1]
    branch = sys.argv[2]
    analyze_image(file_path, branch)