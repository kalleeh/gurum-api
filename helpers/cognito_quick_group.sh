#!/bin/bash
set -e

echo -e "Checking if the platform has been setup..\n"

## Retreive Cognito Details
USER_POOL_ID=$(aws cognito-idp list-user-pools --max-results 20 | jq -r '.UserPools[] | select(.Name == "gurum_users") | .Id')
if [ -z $USER_POOL_ID ]; then 
    echo "No user pool found. Ensure the platform has been setup first."
    exit 1
fi

##App client id
IDENTITY_POOL_ID=$(aws cognito-identity list-identity-pools --max-results 20 | jq -r '.IdentityPools[] | select(.IdentityPoolName == "gurum_idp") | .IdentityPoolId')
if [ -z $IDENTITY_POOL_ID ]; then 
    echo "No identity pool found. Ensure the platform has been setup first."
    exit 1
fi

# MODIFY TRUST POLICY JSON
MYDIR="$(dirname "$(which "$0")")"
sed "s/###RESERVED_FOR_QUICK_GROUP_SCRIPT###/$IDENTITY_POOL_ID/g" $MYDIR/group_trust_policy.json > $MYDIR/group_trust_policy.deploy

# USER CREATION
echo "Enter a group name:"
read GROUP_NAME

## Create the IAM Role
ROLE_NAME="gurum-$GROUP_NAME-role"
ROLE_ARN=$(aws iam create-role \
    --path '/gurum/groups/' \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file://$MYDIR/group_trust_policy.deploy \
    --description "Gurum Cognito Group Assume Role for $GROUP_NAME" \
    --tags Key=gurum-groups,Value=$GROUP_NAME | jq -r '.Role.Arn')
rm $MYDIR/group_trust_policy.deploy # clean up temporary deploy file

## Attach IAM role policy
ACCOUNT_ID=$(aws sts get-caller-identity --output text --query 'Account')
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/gurum/gurum-group-policy"

## Create the Cognito Group
aws cognito-idp create-group \
    --group-name $GROUP_NAME \
    --user-pool-id $USER_POOL_ID \
    --role-arn $ROLE_ARN > /dev/null

echo -e "\n\nSuccess! Group created and mapped to an IAM role."
