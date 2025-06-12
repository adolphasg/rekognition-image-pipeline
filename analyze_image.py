import os
import sys
import boto3
from decimal import Decimal

# Get AWS region
region = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize clients
s3 = boto3.client('s3', region_name=region)
rekognition = boto3.client('rekognition', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)

# Analyze image function
def analyze_image(file_path, branch):
    filename = os.path.basename(file_path)
    bucket = os.environ['S3_BUCKET']
    table_name = os.environ['DYNAMODB_TABLE_BETA'] if branch == 'beta' else os.environ['DYNAMODB_TABLE_PROD']
    table = dynamodb.Table(table_name)

    # Upload to S3
    s3.upload_file(file_path, bucket, filename)

    # Analyze with Rekognition
    with open(file_path, 'rb') as image:
        response = rekognition.detect_labels(Image={'Bytes': image.read()})

    # Format and upload to DynamoDB
    labels = response['Labels']
    label_data = {label['Name']: Decimal(str(label['Confidence'])) for label in labels}

    item = {'filename': filename, 'labels': label_data}
    table.put_item(Item=item)
    print(f"Processed: {filename}")

# Main script
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_image.py <branch>")
        sys.exit(1)

    branch = sys.argv[1]
    image_folder = "images"

    # Check and loop through supported image files
    supported_extensions = ('.jpg', '.jpeg', '.png')
    for file in os.listdir(image_folder):
        if file.lower().endswith(supported_extensions):
            file_path = os.path.join(image_folder, file)
            analyze_image(file_path, branch)
