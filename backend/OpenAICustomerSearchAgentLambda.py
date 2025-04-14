import json
import boto3
import urllib.request
import urllib.error
import urllib.parse
from decimal import Decimal
import os
import time
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define CORS headers as a function - this was incorrectly defined at the module level
def get_cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',  # Replace with specific domain in production
        'Access-Control-Allow-Headers': "Content-Type, Authorization, x-openai-api-key",
        'Access-Control-Allow-Methods': "GET, POST, OPTIONS",
        'Access-Control-Max-Age': '86400',
        'Content-Type': 'application/json'
    }

def convert_decimals(obj):
    """Convert Decimal types to float for JSON serialization."""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

def lambda_handler(event, context):
    start_time = time.time()
    logger.info("Lambda function started")
    
    # Handle OPTIONS requests for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({})
        }
    
    try:
        # Extract inputs with simplified access
        body = event.get('body', {})
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = {}
        
        # Get parameters from various places - check headers more carefully
        headers = event.get('headers', {})
        if headers and isinstance(headers, dict):
            # Convert all header keys to lowercase for consistency
            headers = {k.lower(): v for k, v in headers.items()}
        else:
            headers = {}
            
        # Check for API key in various places
        openai_api_key = (
            event.get('openai_api_key') or 
            headers.get('x-openai-api-key') or 
            body.get('api_key') or
            os.environ.get('OPENAI_API_KEY')
        )
        
        table_name = event.get('table_name') or body.get('table_name')
        prompt = event.get('prompt') or body.get('prompt', "Please analyze this data and provide insights.")
        search_query = event.get('search_query') or body.get('search_query', '').strip()
        
        # Log important parameters (omitting sensitive data)
        logger.info(f"Processing request: table_name={table_name}, has_api_key={bool(openai_api_key)}, search_query={search_query}")
        
        # Validation
        if not openai_api_key:
            return {
                "statusCode": 400, 
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Missing OpenAI API key"})
            }
            
        if not table_name:
            return {
                "statusCode": 400, 
                "headers": get_cors_headers(),
                "body": json.dumps({"error": "Missing table_name"})
            }

        # Query DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        response = table.scan(Limit=20)  # Limit for performance
        items = convert_decimals(response.get('Items', []))
        
        # Filter results if search query provided
        if search_query:
            filtered_items = []
            for item in items:
                item_string = json.dumps(item).lower()
                if search_query.lower() in item_string:
                    filtered_items.append(item)
            items = filtered_items
        
        # Truncate data if needed to avoid token limits
        data_str = json.dumps(items)
        if len(data_str) > 4000:
            data_str = data_str[:4000] + "... [truncated]"
        
        # Prepare OpenAI request
        url = "https://api.openai.com/v1/chat/completions"
        openai_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        
        user_message = f"{prompt}\n\n"
        if search_query:
            user_message += f"Search Query: '{search_query}'\n\n"
        user_message += f"Data:\n{data_str}"
            
        # o3-mini specific payload
        payload = {
            "model": "o3-mini",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that analyzes DynamoDB data."},
                {"role": "user", "content": user_message}
            ],
            "max_completion_tokens": 800,
            "reasoning_effort": "low"
        }
        
        # Send OpenAI request using urllib
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=openai_headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            
            # Extract result
            result = response_data.get("choices", [{}])[0].get("message", {}).get("content", "No content found")
            
            execution_time = time.time() - start_time
            return {
                "statusCode": 200,
                "headers": get_cors_headers(),
                "body": json.dumps({
                    "result": result,
                    "items_found": len(items),
                    "execution_time": f"{execution_time:.2f}s"
                })
            }
            
    except urllib.error.HTTPError as e:
        error_message = e.read().decode("utf-8")
        logger.error(f"OpenAI API error: {e.code} - {error_message}")
        return {
            "statusCode": e.code,
            "headers": get_cors_headers(),
            "body": json.dumps({"error": f"OpenAI API error: {error_message}"})
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": get_cors_headers(),
            "body": json.dumps({
                "error": str(e),
                "execution_time": f"{time.time() - start_time:.2f}s"
            })
        }