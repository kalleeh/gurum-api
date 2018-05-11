aws s3 cp swagger.yaml s3://storage-kalleh/gureume/swagger.yaml
aws cloudformation package --template-file template.yaml --s3-bucket storage-kalleh --s3-prefix 'gureume' --output-template-file template-deploy.yaml
aws cloudformation deploy --template-file template-deploy.yaml --stack-name gureume-api-sam --capabilities CAPABILITY_NAMED_IAM