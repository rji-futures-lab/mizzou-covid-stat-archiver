#!/bin/bash
# set the environment variables in AWS Lambda

aws lambda update-function-configuration \
    --function-name ${PROJECT_NAME} \
    --environment "Variables={PROJECT_NAME=${PROJECT_NAME}, SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}}"
