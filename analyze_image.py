import os
import sys
import boto3
from decimal import Decimal
from datetime import datetime

# Get AWS region
region = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS clients
s3 = boto3.client('s3', region_name=region)
rekognition = boto3.client('rekognition', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)

# Analyze a single image
def analyze_image(file_path, branch):
    filename = os.path.basename(file_path)
    bucket = os.environ['S3_BUCKET']
    table_name = os.environ['DYNAMODB_TABLE_BETA'] if branch == 'beta' else os.environ['DYNAMODB_TABLE_PROD']
    table = dynamodb.Table(table_name)

    # Upload image to S3
    s3.upload_file(file_path, bucket, filename)

    # Detect labels with Rekognition
    with open(file_path, 'rb') as image:
        response = rekognition.detect_labels(Image={'Bytes': image.read()})

    # Format label data as { label: confidence }
    labels = {
        label['Name']: Decimal(str(label['Confidence']))
        for label in response['Labels']
    }

    # Build item to store in DynamoDB
    item = {
        'filename': filename,
        'labels': labels,
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'branch': branch
    }

    # Write to DynamoDB
    table.put_item(Item=item)
    print(f"✔ Processed: {filename}")

# Main entry point
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_image.py <branch>")
        sys.exit(1)

    branch = sys.argv[1]
    image_folder = "images"
    supported_extensions = ('.jpg', '.jpeg', '.png')

    # Loop through images in the folder
    for file in os.listdir(image_folder):
        if file.lower().endswith(supported_extensions):
            file_path = os.path.join(image_folder, file)
            analyze_image(file_path, branch)