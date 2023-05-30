import traceback
import json
import os
import boto3

error_topic_arn = os.getenv('ERROR_TOPIC_ARN')
notification_topic_arn = os.getenv('NOTIFICATION_TOPIC_ARN')

sns_client = boto3.client('sns')


# invoked by AWS Cognito when a user is confirmed
def lambda_handler(event, context):
    try:
        sub = event['request']['userAttributes']['sub']
        email = event['request']['userAttributes']['email']
        print(f'New user has been confirmed. Sub (unique ID): {sub}, email: {email}')
        subscribe_user_to_notification_topic(sub, email)
    except BaseException:
        print(f'Error while invoking post confirmation callback. Event was: {json.dumps(event)}')
        traceback.print_exc()
        sns_client.publish(
            TopicArn=error_topic_arn,
            Subject='Post Confirmation Trigger error',
            message='Error while invoking post confirmation callback. Details in CloudWatch logs'
        )
    return event


def subscribe_user_to_notification_topic(user_id: str, email: str):
    filter_policy = {
        "user_id": user_id
    }
    sns_client.subscribe(
        TopicArn=notification_topic_arn,
        Protocol='email',
        Endpoint=email,
        Attributes={
            'FilterPolicy': json.dumps(filter_policy),
            'FilterPolicyScope': 'MessageAttributes'
        }
    )
    # email owner must confirm subscription
