#!/bin/bash

aws events remove-targets \
    --rule "${PROJECT_NAME}-rule" \
    --ids 1

aws lambda remove-permission \
    --function-name ${PROJECT_NAME} \
    --statement-id "${PROJECT_NAME}-statement"

aws events delete-rule \
    --name "${PROJECT_NAME}-rule"

aws lambda delete-function \
    --function-name ${PROJECT_NAME}

rm event-rule.json
rm function.json
