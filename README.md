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
                    "arn:aws:iam::[ACCOUNT_ID]:role/gureume-api-CreateServiceRole-1MIEWAEXAMPLE",
                    "arn:aws:iam::[ACCOUNT_ID]:role/gureume-api-CreatePipelineRole-19IKJ4QEXAMPLE",
                    "arn:aws:iam::[ACCOUNT_ID]:role/gureume-api-CreateAppRole-WH782EXAMPLE",
                    "arn:aws:iam::[ACCOUNT_ID]:role/gureume-api-UpdateAppRole-M6P8CEXAMPLE",
                    "arn:aws:iam::[ACCOUNT_ID]:role/gureume-api-UpdatePipelineRole-1Q61BEXAMPLE",
                    "arn:aws:iam::[ACCOUNT_ID]:role/gureume-api-UpdateServiceRole-PQFE2EXAMPLE"
                ]
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::[STORAGE_BUCKET]/cfn/app/*"
        }
    ]
}
```

## Pipeline Deployment

![Pipeline Sample Image](img/pipeline-sample.png)

## Requirements

- AWS CLI already configured with Administrator access
  - Alternatively, you can use a [Cloudformation Service Role with Admin access](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html)

## Modify default pipeline settings

If you don't use Python or don't want to trigger the Pipeline from the `master` branch you need to take additional steps.

Before we create this 3-environment Pipeline through Cloudformation you may want to change a couple of things to fit your environment/runtime:

- **CodeBuild** uses a `Python` build image by default and if you're not using `Python` as a runtime you can change that
  - [CodeBuild offers multiple images](https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-available.html) and you can  update the `Image` property under `pipeline.yaml` file accordingly

```yaml
    CodeBuildProject:
        Type: AWS::CodeBuild::Project
        Properties:
            ...
            Environment:
                Type: LINUX_CONTAINER
                ComputeType: BUILD_GENERAL1_SMALL
                Image: aws/codebuild/python:3.6.5 # More info on Images: https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-available.html
                EnvironmentVariables:
                  -
                    Name: BUILD_OUTPUT_BUCKET
                    Value: !Ref BuildArtifactsBucket
...
```

- **CodePipeline** uses the `master` branch to trigger the CI/CD pipeline and if you want to specify another branch you can do so by updating the following section in the `pipeline.yaml` file.

```yaml
...
    Stages:
        - Name: Source
            Actions:
            - Name: SourceCodeRepo
                ActionTypeId:
                # More info on Possible Values: https://docs.aws.amazon.com/codepipeline/latest/userguide/reference-pipeline-structure.html#action-requirements
                Category: Source
                Owner: AWS
                Provider: CodeCommit
                Version: 1
                Configuration:
                RepositoryName: !GetAtt CodeRepository.Name
                BranchName: master
                OutputArtifacts:
                - Name: SourceCodeAsZip
                RunOrder: 1
```

## Deploy the pipeline in your account

Run the following AWS CLI command to create your first pipeline for your SAM based Serverless App:

```bash
aws cloudformation create-stack \
    --stack-name gureume-api-pipeline \
    --template-body file://pipeline.yaml \
    --capabilities CAPABILITY_NAMED_IAM
```

This may take a couple of minutes to complete, therefore give it a minute or two and then run the following command to retrieve the Git repository:

```bash
aws cloudformation describe-stacks \
    --stack-name gureume-api-pipeline \
    --query 'Stacks[].Outputs'
```

## Release through the newly built Pipeline

Although CodePipeline will orchestrate this 3-environment CI/CD pipeline we need to learn how to integrate our toolchain to fit the following sections:

> **Source code**

All you need to do here is to initialize a local `git repository` for your existing service if you haven't done already and connect to the `git repository` that you retrieved in the previous section.

```bash
git init
```

Next, add a new Git Origin to connect your local repository to the remote repository:

- [Git Instructions for SSH access](https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-ssh-unixes.html)
- [Git Instructions for HTTPS access](https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-https-unixes.html)

> **Build steps**

This Pipeline expects `buildspec.yaml` to be at the root of this `git repository` and **CodeBuild** expects will read and execute all sections during the Build stage.

Open up `buildspec.yaml` using your favourite editor and customize it to your needs - Comments have been added to guide you what's needed

> **Triggering a deployment through the Pipeline**

The Pipeline will be listening for new git commits pushed to the `master` branch (unless you changed), therefore all we need to do now is to commit to master and watch our pipeline run through:

```bash
git add .
git commit -m "Triggering first deploy through CI/CD pipeline"
git push origin master
```