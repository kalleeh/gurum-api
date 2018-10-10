# Gureume Management API

This reference architecture provides a set of YAML templates for deploying the Gureume Management API with [AWS CloudFormation](https://aws.amazon.com/cloudformation/).

## Overview

![architecture-overview](images/architecture-overview.png)

The architecture consists of two parts, the supporting platform and the management API.

This repository consists of a set of nested templates to deploy the supporting platform:

- A tiered [VPC](http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Introduction.html) with public and private subnets, spanning an AWS region.

## Template details

The templates below are included in this repository and reference architecture:

| Template | Description |
| --- | --- |
| [template.yaml](template.yaml) | This is the master template - deploy it to CloudFormation and it includes all of the others automatically. |

After the CloudFormation templates have been deployed, the [stack outputs](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/outputs-section-structure.html) contain a

The ECS instances should also appear in the Managed Instances section of the EC2 console.

## Deployment Instructions

### Prerequisites

#### Cognito User Pool

You'll need a Cognito User Pool to manage the identities that will authenticate through your API. [ECS Service Discovery](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-discovery.html#create-service-discovery)

1. Create a new service discovery namespace for our cluster

    ``` bash
    aws servicediscovery create-private-dns-namespace --name PLATFORM_NAME --vpc vpc-abcd1234 --region us-east-1
    ```

2. Using the OperationId from the previous output, verify that the private namespace was created successfully.

    ``` bash
    aws servicediscovery get-operation --operation-id h2qe3s6dxftvvt7riu6lfy2f6c3jlhf4-je6chs2e
    ```

#### Configure the template to use the Cognito User Pool

You can adjust the Cognito User Pool ID used in this section of the [template.yaml](template.yaml) template:

```yaml
securityDefinitions:
    CognitoUserPool:
    in: header
    type: apiKey
    name: Authorization
    x-amazon-apigateway-authtype: cognito_user_pools
    x-amazon-apigateway-authorizer:
        type: cognito_user_pools
        providerARNs:
            - 'arn:aws:cognito-idp:REGION:ACCOUNT_ID:userpool/eu-west-1_MkMfew8eN'
```

#### S3 Bucket for the Product templates

The CreateApp and CreatePipeline lambda requires permissions to read the templates from an S3-bucket in order to provision applications and pipelines. The templates that the functions need access to is already synchronized as part of the platform deployment however you need to add the necessary permissions for these functions to get the templates to deploy.
Update the bucket policy to something similar,

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": [
                    "arn:aws:iam::ACCOUNT_ID:role/gureume-api-CreatePipelineRole-19IKJ4QRFEF4J",
                    "arn:aws:iam::ACCOUNT_ID:role/gureume-api-CreateAppRole-WH212SG7TQVR"
                ]
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::STORAGE_BUCKET/cfn/app/*"
        }
    ]
}
```