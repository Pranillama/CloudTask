import json
import boto3
import os
from boto3.dynamodb.conditions import Attr

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'CloudTaskTable')
table = dynamodb.Table(table_name)

sns = boto3.client('sns')
topic_arn = os.environ.get('REMINDER_TOPIC_ARN')


def lambda_handler(event, context):
    """
    Scheduled Lambda (triggered daily by EventBridge) that scans for all
    incomplete tasks and emails a summary to a single SNS topic subscriber.
    """
    if not topic_arn:
        print("REMINDER_TOPIC_ARN is not set")
        return {'statusCode': 500, 'body': 'REMINDER_TOPIC_ARN not configured'}

    # Collect all incomplete tasks (handles pagination).
    pending = []
    scan_kwargs = {
        'FilterExpression': Attr('completed').eq(False),
        'ProjectionExpression': '#t',
        'ExpressionAttributeNames': {'#t': 'title'},
    }
    while True:
        response = table.scan(**scan_kwargs)
        pending.extend(response.get('Items', []))
        last_key = response.get('LastEvaluatedKey')
        if not last_key:
            break
        scan_kwargs['ExclusiveStartKey'] = last_key

    count = len(pending)

    # Nothing pending — skip sending so we don't send empty emails.
    if count == 0:
        print("No pending tasks; skipping notification")
        return {'statusCode': 200, 'body': 'No pending tasks'}

    # Build a plain-text summary.
    lines = [f"- {item.get('title', '(untitled)')}" for item in pending]
    message = (
        f"You have {count} pending task(s) in CloudTask:\n\n"
        + "\n".join(lines)
    )
    subject = f"CloudTask: {count} task(s) still pending"

    sns.publish(
        TopicArn=topic_arn,
        Subject=subject[:100],  # SNS subject max length is 100 chars
        Message=message
    )

    print(f"Reminder sent for {count} pending task(s)")
    return {'statusCode': 200, 'body': f'Reminder sent for {count} task(s)'}
