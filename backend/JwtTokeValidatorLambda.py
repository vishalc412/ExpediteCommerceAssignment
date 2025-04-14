import boto3
import json
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-east-2")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "us-east-2_ZXpNZtEWj")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "ituinvaceh6g4ranropd5k1mc")

# Initialize Cognito client
client = boto3.client("cognito-idp", region_name=COGNITO_REGION)

def lambda_handler(event, context):
    # Log the event for debugging
    logger.info(f"Event: {json.dumps(event)}")
    
    # CORS headers for all responses
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Requested-With,Origin',
        'Access-Control-Allow-Methods': 'OPTIONS,GET',
        'Content-Type': 'application/json'
    }
    
    # Handle preflight CORS requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS preflight request successful'})
        }
    
    try:
        # Parse headers
        headers_dict = event.get('headers', {})
        
        # Check if headers is a string (JSON string)
        if isinstance(headers_dict, str):
            try:
                headers_dict = json.loads(headers_dict)
                logger.info(f"Parsed headers from JSON string")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse headers JSON: {e}")
                headers_dict = {}
        
        # Check for Authorization header (case insensitive)
        auth_header = None
        for key, value in headers_dict.items():
            if key.lower() == 'authorization':
                auth_header = value
                break
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing or invalid Authorization header'
                })
            }
        
        # Extract the token
        token = auth_header.split(' ')[1]
        logger.info(f"Token validation attempt")
        
        # Validate token with Cognito
        try:
            # For access tokens, use get_user
            user_info = client.get_user(
                AccessToken=token
            )
            
            # Extract user attributes
            user_attributes = {}
            for attr in user_info.get('UserAttributes', []):
                user_attributes[attr['Name']] = attr['Value']
            
            logger.info(f"Token validation successful for user: {user_info.get('Username')}")
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'message': 'Token is valid',
                    'user': {
                        'username': user_info.get('Username'),
                        'attributes': user_attributes
                    }
                })
            }
        except client.exceptions.NotAuthorizedException as e:
            logger.error(f"Token validation failed - not authorized: {str(e)}")
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid or expired token'
                })
            }
        except Exception as e:
            logger.error(f"Token validation failed with error: {str(e)}")
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': f'Token validation error: {str(e)}'
                })
            }
        
    except Exception as e:
        logger.error(f"Error in token validator: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }