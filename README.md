Gureume Management API
==============================================

This is the management interfae for the Gureume Container Platform.

What's Here
-----------

This repository includes:

* README.md - this file
* buildspec.yml - this file is used by AWS CodeBuild to package your
  application for deployment to AWS Lambda and API Gateway
* template.yml - this file contains the AWS Serverless Application Model (AWS SAM) used
  by AWS CloudFormation to deploy your application to AWS Lambda and Amazon API
  Gateway.
* src/ - this directory contains the source code for the AWS Lambda functions
* tests/ - this directory contains unit tests for your application


What Do I Do Next?
------------------

To run your tests locally, go to the root directory of the
sample code and run the `python -m unittest discover tests` command, which
AWS CodeBuild also runs through your `buildspec.yml` file.

To test your new code during the release process, modify the existing tests or
add tests to the tests directory. AWS CodeBuild will run the tests during the
build stage of your project pipeline. You can find the test results
in the AWS CodeBuild console.

Learn more about AWS CodeBuild and how it builds and tests your application here:
https://docs.aws.amazon.com/codebuild/latest/userguide/concepts.html

Learn more about AWS Serverless Application Model (AWS SAM) and how it works here:
https://github.com/awslabs/serverless-application-model/blob/master/HOWTO.md

AWS Lambda Developer Guide:
http://docs.aws.amazon.com/lambda/latest/dg/deploying-lambda-apps.html

What Should I Do Before Running My Project in Production?
------------------

AWS recommends you review the security best practices recommended by the framework
author of your selected sample application before running it in production. You
should also regularly review and apply any available patches or associated security
advisories for dependencies used within your application.
