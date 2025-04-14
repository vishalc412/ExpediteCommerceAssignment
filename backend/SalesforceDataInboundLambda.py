#!/usr/bin/env python3
"""
lambda_function.py
A Lambda function for receiving Salesforce customer data and storing it in DynamoDB
Includes simplified Cognito JWT token validation without external dependencies

Author: Your Organization
Date: April 2025
"""

import json
import boto3
from datetime import datetime
import os
import base64
import urllib.request
import time

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'CustomerData')
table = dynamodb.Table(table_name)

# Cognito configuration
COGNITO_REGION = os.environ.get('COGNITO_REGION', 'us-east-2')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', 'us-east-2_ZXpNZtEWj')
COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_APP_CLIENT_ID', 'ituinvaceh6g4ranropd5k1mc')

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    - Receives API Gateway event
    - Verifies JWT authentication
    - Processes customer data
    - Stores in DynamoDB
    """
    try:
        print("Received event:", json.dumps(event))
        
        # Check for authentication
        auth_result = authenticate_request(event)
        if not auth_result['authenticated']:
            return {
                'statusCode': 401,
                'body': json.dumps({'error': auth_result['message']})
            }
            
        # Store the user info for authorization checks if needed
        user_info = auth_result.get('user_info', {})
        print("Authenticated user:", json.dumps(user_info))
            
        # Check if this is a health check
        if event.get('resource') == '/health' and event.get('httpMethod') == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'healthy'})
            }
            
        # Get body from request
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No request body provided'})
            }
            
        # Parse body - could be string or already parsed depending on API Gateway settings
        if isinstance(event['body'], str):
            data = json.loads(event['body'])
        else:
            data = event['body']
        
        print("Request data:", json.dumps(data))
        
        # Check for required fields
        required_fields = ['name', 'age', 'phone', 'dob', 'address', 'email']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Missing required fields: {", ".join(missing_fields)}'})
            }
        
        # Process customer data
        if 'customer_id' in data and data['customer_id']:
            # Convert to integer if it's a string
            if isinstance(data['customer_id'], str) and data['customer_id'].isdigit():
                customer_id = int(data['customer_id'])
            else:
                customer_id = data['customer_id']
        else:
            # Generate a new ID (timestamp-based)
            customer_id = int(datetime.now().timestamp() * 1000)
            data['customer_id'] = customer_id
            
        # Add timestamps
        data['updated_at'] = datetime.now().isoformat()
        # Use the Cognito username from token as the updater
        if 'username' in user_info:
            data['updated_by'] = user_info['username']
        elif 'cognito:username' in user_info:
            data['updated_by'] = user_info['cognito:username']
        elif 'sub' in user_info:
            data['updated_by'] = user_info['sub']
            
        # Check if the customer already exists
        try:
            response = table.get_item(Key={'customer_id': customer_id})
            if 'Item' in response:
                # Customer exists, update timestamps only if not present
                if 'created_at' not in data and 'created_at' in response['Item']:
                    data['created_at'] = response['Item']['created_at']
                if 'created_by' not in data and 'created_by' in response['Item']:
                    data['created_by'] = response['Item']['created_by']
            else:
                # New customer
                data['created_at'] = datetime.now().isoformat()
                # Use the Cognito username from token as the creator
                if 'username' in user_info:
                    data['created_by'] = user_info['username']
                elif 'cognito:username' in user_info:
                    data['created_by'] = user_info['cognito:username']
                elif 'sub' in user_info:
                    data['created_by'] = user_info['sub']
        except Exception as e:
            print(f"Error checking existing customer: {str(e)}")
            # Default to creating a new customer record
            data['created_at'] = datetime.now().isoformat()
            if 'username' in user_info:
                data['created_by'] = user_info['username']
            elif 'cognito:username' in user_info:
                data['created_by'] = user_info['cognito:username']
            elif 'sub' in user_info:
                data['created_by'] = user_info['sub']
                
        # Store in DynamoDB
        print("Saving customer data to DynamoDB")
        table.put_item(Item=data)
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'message': 'Customer data saved successfully',
                'customer_id': str(data['customer_id'])
            })
        }
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def authenticate_request(event):
    """
    Simple JWT token validator that extracts the payload but delegates full
    validation to API Gateway's Cognito Authorizer
    
    When using an API Gateway Cognito Authorizer, API Gateway verifies the token
    before the request even reaches your Lambda function. If the token is invalid,
    API Gateway will reject the request with a 401 error.
    
    This function extracts user info from the token payload, assuming the token
    has already been validated by API Gateway.
    """
    try:
        # Get auth header
        headers = event.get('headers', {}) or {}
        if not headers:
            print("No headers provided in event")
            return {'authenticated': False, 'message': 'No headers provided'}
            
        # Convert headers to lowercase for consistent access
        headers_lower = {k.lower(): v for k, v in headers.items()}
        auth_header = headers_lower.get('authorization')
        
        if not auth_header:
            print("No Authorization header found")
            return {'authenticated': False, 'message': 'Authorization header is missing'}
            
        # Check Bearer token format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            print("Invalid Authorization header format")
            return {
                'authenticated': False, 
                'message': 'Authorization header must be in format: Bearer token'
            }
            
        token = parts[1]
        
        # Extract token payload without validation (assuming API Gateway does the validation)
        token_parts = token.split('.')
        if len(token_parts) != 3:
            print("Token does not have three parts")
            return {'authenticated': False, 'message': 'Invalid token format'}
            
        # Decode the payload part (second part)
        try:
            # Add padding if needed
            payload_part = token_parts[1]
            padding = '=' * (4 - len(payload_part) % 4)
            if padding == 4:
                padding = ''
                
            # Base64 decode
            payload_bytes = base64.urlsafe_b64decode(payload_part + padding)
            payload_str = payload_bytes.decode('utf-8')
            payload = json.loads(payload_str)
            
            # Check for token expiration
            current_time = int(time.time())
            if 'exp' in payload and current_time > payload['exp']:
                print(f"Token expired. Current time: {current_time}, token exp: {payload['exp']}")
                return {'authenticated': False, 'message': 'Token has expired'}
                
            # Check for Cognito audience (client ID)
            if 'client_id' in payload and payload['client_id'] != COGNITO_APP_CLIENT_ID:
                if 'aud' in payload and payload['aud'] != COGNITO_APP_CLIENT_ID:
                    print(f"Invalid token audience")
                    return {'authenticated': False, 'message': 'Invalid token audience'}
                    
            # Check for Cognito issuer
            expected_issuer = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'
            if 'iss' in payload and payload['iss'] != expected_issuer:
                print(f"Invalid token issuer")
                return {'authenticated': False, 'message': 'Invalid token issuer'}
                
            print("Successfully parsed JWT payload")
            return {
                'authenticated': True,
                'user_info': payload
            }
            
        except Exception as e:
            print(f"Error parsing JWT payload: {str(e)}")
            return {'authenticated': False, 'message': f'Error parsing token: {str(e)}'}
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return {'authenticated': False, 'message': f'Authentication error: {str(e)}'}