#!/bin/bash
STACK_NAME="gurum-api"
ACCOUNT_ID=$(aws sts get-caller-identity --output text --query 'Account')
REGION=$(aws configure get region)
S3_BUCKET="gurum-deployment-artifacts-$ACCOUNT_ID-$REGION"

# Only create the artifacts bucket if one does not exist.
if aws s3 ls "s3://$S3_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating initial artifacts bucket"
    aws s3 mb "s3://$S3_BUCKET"
    aws s3api put-bucket-encryption --bucket $S3_BUCKET --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }'
    aws s3api put-public-access-block \
    --bucket $S3_BUCKET \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
fi

# Automatically create a deployment package for the AWS X-Ray Lambda Layer if it doesn't exist.
if [ ! -d "lambda_layers/aws-xray-sdk" ]; then
    pip3 install aws-xray-sdk --target lambda_layers/aws-xray-sdk/python
fi

# Clear local pycache in lambda layer dependencies
find lambda_layers -type d -name "__pycache__" -exec rm -r {} \;

aws cloudformation package --template-file src/template.yaml --s3-bucket $S3_BUCKET --output-template-file template-deploy.yaml
aws cloudformation deploy --template-file template-deploy.yaml --stack-name $STACK_NAME --capabilities CAPABILITY_NAMED_IAM
