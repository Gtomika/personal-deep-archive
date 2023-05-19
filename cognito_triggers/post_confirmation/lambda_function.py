import traceback
import json
import os
import boto3

error_topic_arn = os.getenv('ERROR_TOPIC_ARN')

sns_client = boto3.client('sns')


# invoked by AWS Cognito when a user is confirmed
def lambda_handler(event, context):
    try:
        sub = event['request']['userAttributes']['sub']
        email = event['request']['userAttributes']['email']
        print(f'New user has been confirmed. Sub (unique ID): {sub}, email: {email}')
        # TODO do something with the user?
    except BaseException:
        print(f'Error while invoking post confirmation callback. Event was: {json.dumps(event)}')
        traceback.print_exc()
        sns_client.publish(
            TopicArn=error_topic_arn,
            Subject='Post Confirmation Trigger error',
            message='Error while invoking post confirmation callback. Details in CloudWatch logs'
        )
    return event
