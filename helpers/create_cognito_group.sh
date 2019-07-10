#!/bin/bash
echo -e "Checking if the platform has been setup..\n"

## Retreive Cognito Details
POOL_ID=$(aws cognito-idp list-user-pools --max-results 20 | jq -r '.UserPools[] | select(.Name == "gureume_users") | .Id')
if [ -z $POOL_ID ]; then 
    echo "No user pool found. Ensure the platform has been setup first."
    exit 1
fi

echo "Enter a name for the group:"
read GROUP_NAME

aws cognito-idp create-group --group-name $GROUP_NAME --user-pool-id $POOL_ID > /dev/null

