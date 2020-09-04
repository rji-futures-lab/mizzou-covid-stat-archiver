#!/bin/bash
# schedule invocations of lambda function

aws events put-rule \
    --name "${PROJECT_NAME}-rule" \
    --schedule-expression 'rate(2 minutes)' \
    > 'event-rule.json'

aws lambda add-permission \
    --function-name ${PROJECT_NAME} \
    --statement-id "${PROJECT_NAME}-statement" \
    --action 'lambda:InvokeFunction' \
    --principal events.amazonaws.com \
    --source-arn $(cat 'event-rule.json' | jq -r '.RuleArn')

aws events put-targets \
    --rule "${PROJECT_NAME}-rule" \
    --targets "Id"="1","Arn"=$(cat 'function.json' | jq -r '.FunctionArn')
