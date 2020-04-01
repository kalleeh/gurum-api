# Gurum Management API

This reference architecture provides a set of YAML templates for deploying the Gurum Management API with [AWS CloudFormation](https://aws.amazon.com/cloudformation/).

## Overview

The architecture consists of two parts, the supporting platform and the management API.
This repository and templates deploy the management API. To modify or deploy the platform, please see the gurum-platform repository.

### Architecture Overview

![architecture-overview](docs/images/architecture-overview.png)

### API Overview

![api-overview](docs/images/api-overview.png)

## Template details

The templates below are included in this repository and reference architecture:

| Template | Description |
| --- | --- |
| [lambda_layers/dependencies/](lambda_layers/dependencies/) | Shared Python libraries deployed as a Lambda Layer. |
| [src/](src/) | Source code for Lambda functions corresponding to API actions. |
| [template.yaml](template.yaml) | This is the master template - deploy it to CloudFormation and it includes all of the others automatically. |

## Deployment Instructions

### Prerequisites

#### AWS X-Ray SDK

This repository does not include a shared lambda layer with the [AWS X-Ray SDK](https://github.com/aws/aws-xray-sdk-python). You can either disable the use of AWS X-Ray in the source code or follow below instructions to create a [Lambda Deployment Package](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html) that is referenced in the template.yaml and automatically attached as a [AWS Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html) to the required lambda functions.

```bash
[project_root] pip3 install aws-xray-sdk --target lambda_layers/aws-xray-sdk/python
```

### Manual Deployment

You can use the included bash script to quickly deploy the API in your account. Modify the properties in the deploy.sh and then run the following commands.

```bash
./deploy.sh
```

## User Account Setup

Once you have the API up and running you will need to configure your developer accounts so that they can interact with the platform. Follow the below steps to create groups and user accounts for your development teams.

### 1. Configure Cognito

#### 1.1 Create Teams (Cognito Groups)

1.1.1 Use the `./helpers/cognito_quick_group.sh` script to create a new Gurum Team that your users can collaborate on.
This effectively functions as a tenant in Gurum and ownership of apps and services are linked to the Team.

#### 1.2 Create Users

1.2.1 Use the `./helpers/cognito_quick_user.sh` script to create a new cognito user.
