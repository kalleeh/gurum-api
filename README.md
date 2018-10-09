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

### Configure the template to use the Cognito User Pool

You can adjust the Cognito User Pool ID used in this section of the [template.yaml](template.yaml) template:

``` YAML
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