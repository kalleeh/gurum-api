S3_BUCKET="storage-kalleh"
STACK_NAME="gureume-api"

aws cloudformation package --template-file template.yaml --s3-bucket $S3_BUCKET --s3-prefix 'gureume' --output-template-file template-deploy.yaml
aws cloudformation deploy --template-file template-deploy.yaml --stack-name $STACK_NAME --capabilities CAPABILITY_NAMED_IAM