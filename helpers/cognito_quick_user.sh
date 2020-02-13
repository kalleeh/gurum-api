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
CLIENT_ID=$(aws cognito-idp list-user-pool-clients --user-pool-id $USER_POOL_ID | jq -r '.UserPoolClients[] | select(.ClientName == "gurum-client") | .ClientId')
if [ -z $CLIENT_ID ]; then 
    echo "No client id found. Ensure the platform has been setup first."
    exit 1
fi

# USER CREATION
echo "Enter a username:"
read USERNAME

echo "Enter a valid e-mail:"
read EMAIL

echo -e "\nEnter a password:"
read -s PASSWORD

## Create the Cognito user
aws cognito-idp sign-up --client-id $CLIENT_ID --username $USERNAME --password $PASSWORD --user-attributes Name="email",Value="$EMAIL" > /dev/null

## Assign cognito user to group
GROUP_NAMES=$(aws cognito-idp list-groups --user-pool-id $USER_POOL_ID | jq -r '.Groups | map(.GroupName) | join(" , ")')

echo -e "\n\nEnter a group for the user (valid: $GROUP_NAMES):"
read SELECTED_GROUP

aws cognito-idp admin-add-user-to-group --username $USERNAME --user-pool-id $USER_POOL_ID --group-name $SELECTED_GROUP

## Confirm the user account
aws cognito-idp admin-confirm-sign-up --username $USERNAME --user-pool-id $USER_POOL_ID

echo -e "\n\nSuccess! Log-in with your chosen details."
