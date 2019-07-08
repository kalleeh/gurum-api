#!/bin/bash

##
# IAM SETUP
##
aws iam create-policy --policy-name gureume-default-team-policy --policy-document file://default_team_policy.json