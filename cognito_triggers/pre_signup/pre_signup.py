import traceback
import json
import os
import boto3

error_topic_arn = os.getenv('ERROR_TOPIC_ARN')
notification_topic_arn = os.getenv('NOTIFICATION_TOPIC_ARN')
aws_region = os.getenv('AWS_REGION')

sns_client = boto3.client('sns')
dynamodb_client = boto3.client('dynamodb')


# invoked by AWS Cognito when a user is confirmed
def lambda_handler(event, context):
    try:
        original_user_id = event['userName']  # UUID, does not include the region
        user_id = create_user_id_accepted_by_iam(original_user_id)
        email = event['request']['userAttributes']['email']
        print(f'New user has been signed up by admin. Sub (unique ID including region): {user_id}, email: {email}')
        subscribe_user_to_notification_topic(user_id, email)
        print('New user has been subscribed to notifications and initialized!')
    except BaseException:
        print(f'Error while invoking post confirmation callback. Event was: {json.dumps(event)}')
        traceback.print_exc()
        sns_client.publish(
            TopicArn=error_topic_arn,
            Subject='Pre Signup Trigger error',
            Message='Error while invoking pre signup callback. Details in CloudWatch logs'
        )
    return event


def create_user_id_accepted_by_iam(original_user_id: str) -> str:
    return f'{aws_region}:{original_user_id}'


def subscribe_user_to_notification_topic(user_id: str, email: str):
    filter_policy = {
        "user_id": [user_id]
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
