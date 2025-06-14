# Pixel Learning - Image Recognition Pipeline

This project uses Amazon Rekognition to analyze image content, Amazon S3 to store image files, and Amazon DynamoDB to log analysis results. When you upload new images to your GitHub repository, an automated workflow uploads them to AWS, scans them for recognizable objects or scenes, and stores the results in a DynamoDB table.

---

## What This Project Does

1. You place images into the `images/` folder.
2. A GitHub Actions workflow is triggered on new commits.
3. The workflow runs a Python script that:
   - Uploads each image to your S3 bucket
   - Uses Rekognition to detect image labels and confidence scores
   - Writes those results into a DynamoDB table, along with the image name, upload time, and branch name

---

## AWS Setup Instructions

### 1. Set Up Your S3 Bucket

- Go to the AWS Management Console
- Navigate to **S3** and click **Create bucket**
- Give the bucket a unique name 
- Leave all other settings as default or configure based on your security needs

### 2. Set Up Your DynamoDB Tables

You will need two tables—one for testing and one for production.

Create both tables in the DynamoDB console:

- Table 1: `beta_results`
  - Partition key: `filename` (String)

- Table 2: `prod_results`
  - Partition key: `filename` (String)

No sort key or secondary indexes are required.

---

## GitHub Secrets Configuration

In your GitHub repository, go to:

**Settings → Secrets and variables → Actions → New repository secret**

Add the following secrets:

| Name                  | Description                                  |
|-----------------------|----------------------------------------------|
| `AWS_ACCESS_KEY_ID`   | Your AWS access key                          |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key                        |
| `AWS_REGION`          | Your AWS region (e.g., `us-east-1`)         |
| `S3_BUCKET`           | Your S3 bucket name                          |
| `DYNAMODB_TABLE_BETA` | Name of your beta DynamoDB table (`beta_results`) |
| `DYNAMODB_TABLE_PROD` | Name of your production DynamoDB table (`prod_results`) |

Ensure the secret names match exactly—case matters.

---

## How to Add and Analyze New Images

1. Add image files (JPG or PNG) to the `images/` directory in your repository.
2. Push your changes to a GitHub branch:
   - Use the `beta` branch to log to `beta_results`
   - Use the `main` or `prod` branch to log to `prod_results`
3. GitHub Actions will automatically run the analysis pipeline.

The workflow will:
- Upload the new images to your S3 bucket under `rekognition-input/`
- Detect the top 10 labels in each image (confidence > 70%)
- Log the results in the appropriate DynamoDB table

---

## How to Verify Your Results

To check if everything worked:

1. Go to the AWS DynamoDB Console
2. Select either `beta_results` or `prod_results`
3. Click on **Explore Table Items**

Each entry should look like this:

```json
{
  "filename": "rekognition-input/image123.jpg",
  "labels": [
    {"Name": "Balloon", "Confidence": 98.49},
    {"Name": "Aircraft", "Confidence": 98.46}
  ],
  "timestamp": "2025-06-01T14:55:32Z",
  "branch": "beta"
}
