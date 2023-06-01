import traceback
import json
import os

import boto3

error_topic_arn = os.getenv('ERROR_TOPIC_ARN')
notification_topic_arn = os.getenv('NOTIFICATION_TOPIC_ARN')
restoration_notifications_table_name = os.getenv('RESTORATION_NOTIFICATIONS_TABLE_NAME')

sns_client = boto3.client('sns')
dynamodb_client = boto3.client('dynamodb')


def lambda_handler(event, context):
    try:
        pass
        # TODO get user ID
        # TODO if this notification is for restoration completion: reduce users restoration count by one
        # TODO send email is restoration count is 0 INCLUDING user_id message attribute!
    except BaseException:
        print(f'Failed to aggregate S3 event notification. Full event was: {json.dumps(event)}')
        traceback.print_exc()
        sns_client.publish(
            TopicArn=error_topic_arn,
            Subject='Notifications aggregator lambda error',
            Message='Error while invoking notifications aggregator lambda. Details in CloudWatch logs'
        )
