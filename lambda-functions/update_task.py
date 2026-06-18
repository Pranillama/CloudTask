import json
import boto3
import os

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'CloudTaskTable') 
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Lambda function to update a task (toggle completion status)
    """
    try:
        # Get user ID from Cognito authorizer
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Get task ID from path parameters
        task_id = event['pathParameters']['taskId']

        # Parse request body
        body = json.loads(event['body'])

        # Build the update dynamically from whichever fields are provided.
        # Supports toggling completion and/or renaming the task title.
        # Use attribute-name placeholders since 'completed'/'title' can collide
        # with DynamoDB reserved words.
        update_parts = []
        expr_names = {}
        expr_values = {}

        if 'completed' in body:
            update_parts.append('#completed = :completed')
            expr_names['#completed'] = 'completed'
            expr_values[':completed'] = bool(body['completed'])

        if 'title' in body:
            title = body.get('title', '').strip()
            if not title:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Task title cannot be empty'})
                }
            update_parts.append('#title = :title')
            expr_names['#title'] = 'title'
            expr_values[':title'] = title

        if not update_parts:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'No updatable fields provided'})
            }

        # Update task in DynamoDB
        response = table.update_item(
            Key={
                'userId': user_id,
                'taskId': task_id
            },
            UpdateExpression='SET ' + ', '.join(update_parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Task updated successfully',
                'task': response['Attributes']
            })
        }
        
    except KeyError as e:
        print(f"Missing key: {e}")
        return {
            'statusCode': 401,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Unauthorized - Invalid token'})
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }

def get_cors_headers():
    """
    Return CORS headers for API responses
    """
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
    }
