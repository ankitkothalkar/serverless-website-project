# lambda_function.py

import json
import boto3
import os

ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])

SENDER_EMAIL = os.environ['SENDER_EMAIL']
RECIPIENT_EMAIL = os.environ['RECIPIENT_EMAIL']

def lambda_handler(event, context):
    try:
        # Parse the JSON body from the API Gateway event
        body = json.loads(event['body'])
        name = body['name']
        email = body['email']
        message = body['message']
        
        email_body = f"""
        Name: {name}
        Email: {email}
        Message: {message}
        """

        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': [RECIPIENT_EMAIL]
            },
            Message={
                'Subject': {
                    'Data': 'New Contact Form Submission'
                },
                'Body': {
                    'Text': {
                        'Data': email_body
                    }
                }
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Email sent successfully!'}),
            'headers': {
                'Access-Control-Allow-Origin': 'https://yourdomain.com',
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            }
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Failed to send message. Please try again later.'}),
            'headers': {
                'Access-Control-Allow-Origin': 'https://yourdomain.com',
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            }
        }