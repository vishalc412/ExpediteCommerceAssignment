import boto3
import json
import os
import base64
import hashlib
import hmac
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-east-2")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "us-east-2_ZXpNZtEWj")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "ituinvaceh6g4ranropd5k1mc")
COGNITO_CLIENT_SECRET = os.environ.get("COGNITO_CLIENT_SECRET", "u4ghg5mltfpl57qlbjp4t7jdg1mq1c36vmgl3rv3ipi4n7kak8f")

# Initialize Cognito client
client = boto3.client("cognito-idp", region_name=COGNITO_REGION)

def get_secret_hash(username, client_id, client_secret):
    msg = username + client_id
    dig = hmac.new(
        str(client_secret).encode("utf-8"),
        msg=msg.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()

def lambda_handler(event, context):
    # Log the event for debugging
    logger.info(f"Event: {json.dumps(event)}")
    
    # Updated CORS headers - make sure these match your API Gateway settings

    headers = {
        'Access-Control-Allow-Origin': '*',  # Replace with specific domain in production
        'Access-Control-Allow-Headers': "Content-Type, Authorization",
        'Access-Control-Allow-Methods': "GET, POST, OPTIONS",
        'Access-Control-Max-Age': '86400',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS request (CORS preflight)
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,  # Changed from 204 to 200 for better compatibility
            'headers': headers,
            'body': json.dumps({'message': 'CORS preflight request successful'})
        }
    
    try:
        # Parse body
        body_str = event.get("body", "{}")
        logger.info(f"Request body: {body_str}")
        
        if isinstance(body_str, str):
            body = json.loads(body_str)
        else:
            body = body_str
            
        username = body.get("username")
        password = body.get("password")
        
        if not username or not password:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Missing username or password"})
            }
        
        secret_hash = get_secret_hash(username, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET)
        
        # Log auth attempt (without password)
        logger.info(f"Attempting auth for user: {username}")
        
        response = client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password,
                "SECRET_HASH": secret_hash
            },
            ClientId=COGNITO_CLIENT_ID
        )
        
        # Log success (without sensitive data)
        logger.info(f"Authentication successful for user: {username}")
        
        # On success, return tokens
        tokens = response["AuthenticationResult"]
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "id_token": tokens["IdToken"],
                "access_token": tokens["AccessToken"],
                "refresh_token": tokens["RefreshToken"],
                "expires_in": tokens["ExpiresIn"]
            })
        }
    
    except client.exceptions.NotAuthorizedException as e:
        logger.error(f"Authentication failed: {str(e)}")
        return {
            "statusCode": 401,
            "headers": headers,
            "body": json.dumps({"error": "Invalid credentials"})
        }
    except Exception as e:
        logger.error(f"Error in login handler: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)})
        }