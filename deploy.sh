#!/bin/bash

# make the bucket
aws s3 mb "s3://${PROJECT_NAME}"

aws s3api put-bucket-cors \
    --bucket ${PROJECT_NAME} \
    --cors-configuration file://cors.json

# create the lambda function, package and upload upload the source code and schedule invocations
source package.sh

aws lambda create-function \
    --function-name ${PROJECT_NAME} \
    --zip-file fileb://package.zip \
    --handler function.lambda_handler \
    --runtime python3.8 \
    --role ${AWS_LAMBDA_ROLE} \
    --timeout 900 \
    > 'function.json'

rm package.zip

source set-env-vars.sh

source schedule.sh
