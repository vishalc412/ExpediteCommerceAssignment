#!/usr/bin/env python3

import json
import boto3
import os
import base64
import time
from datetime import datetime

# Initialize resources
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NAME', 'CustomerData'))

# Cognito config
COGNITO_REGION = os.environ.get('COGNITO_REGION', 'us-east-2')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', 'us-east-2_ZXpNZtEWj')
COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_APP_CLIENT_ID', 'ituinvaceh6g4ranropd5k1mc')
EXPECTED_ISSUER = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'


def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        if event.get('resource') == '/health' and event.get('httpMethod') == 'GET':
            return response(200, {'status': 'healthy'})

        auth = authenticate_request(event)
        if not auth['authenticated']:
            return response(401, {'error': auth['message']})
        user_info = auth['user_info']
        print("Authenticated user:", json.dumps(user_info))

        body = event.get('body')
        if not body:
            return response(400, {'error': 'No request body provided'})

        data = json.loads(body) if isinstance(body, str) else body
        print("Request data:", json.dumps(data))

        required = ['name', 'age', 'phone', 'dob', 'address', 'email']
        missing = [f for f in required if f not in data]
        if missing:
            return response(400, {'error': f'Missing required fields: {", ".join(missing)}'})

        customer_id = get_customer_id(data)
        data['customer_id'] = customer_id
        now = datetime.now().isoformat()
        data['updated_at'] = now
        data['updated_by'] = get_username(user_info)

        existing = table.get_item(Key={'customer_id': customer_id}).get('Item')
        if existing:
            data.setdefault('created_at', existing.get('created_at', now))
            data.setdefault('created_by', existing.get('created_by', data['updated_by']))
        else:
            data['created_at'] = now
            data['created_by'] = data['updated_by']

        table.put_item(Item=data)
        return response(200, {
            'status': 'success',
            'message': 'Customer data saved successfully',
            'customer_id': str(customer_id)
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {'error': str(e)})


def authenticate_request(event):
    try:
        headers = {k.lower(): v for k, v in (event.get('headers') or {}).items()}
        auth_header = headers.get('authorization', '')
        if not auth_header.lower().startswith('bearer '):
            return {'authenticated': False, 'message': 'Invalid or missing Authorization header'}

        token = auth_header.split()[1]
        payload = decode_jwt_payload(token)
        now = int(time.time())

        if payload.get('exp', 0) < now:
            return {'authenticated': False, 'message': 'Token has expired'}

        if payload.get('client_id') != COGNITO_APP_CLIENT_ID and payload.get('aud') != COGNITO_APP_CLIENT_ID:
            return {'authenticated': False, 'message': 'Invalid token audience'}

        if payload.get('iss') != EXPECTED_ISSUER:
            return {'authenticated': False, 'message': 'Invalid token issuer'}

        return {'authenticated': True, 'user_info': payload}

    except Exception as e:
        print(f"Auth error: {str(e)}")
        return {'authenticated': False, 'message': 'Token parsing error'}


def decode_jwt_payload(token):
    try:
        parts = token.split('.')
        payload = parts[1] + '=' * (-len(parts[1]) % 4)
        decoded = base64.urlsafe_b64decode(payload).decode('utf-8')
        return json.loads(decoded)
    except Exception as e:
        raise ValueError("Invalid JWT payload") from e


def get_customer_id(data):
    cid = data.get('customer_id')
    if isinstance(cid, str) and cid.isdigit():
        return int(cid)
    elif isinstance(cid, int):
        return cid
    return int(datetime.now().timestamp() * 1000)


def get_username(user_info):
    return user_info.get('username') or user_info.get('cognito:username') or user_info.get('sub', 'unknown')


def response(status, body):
    return {'statusCode': status, 'body': json.dumps(body)}