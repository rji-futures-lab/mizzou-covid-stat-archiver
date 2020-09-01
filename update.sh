#!/bin/bash
# package and upload the source code

source package.sh

aws lambda update-function-code \
    --function-name ${PROJECT_NAME} \
    --zip-file fileb://package.zip \
    > 'function.json'

rm package.zip

source set-env-vars.sh