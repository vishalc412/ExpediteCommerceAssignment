# ExpediteCommerce Assignment

Hey there! 👋 This is my demo app showcasing an AI-powered SaaS solution.

## What I Built

I've created a demo that shows how to build a modern AI-powered SaaS application using AWS serverless architecture, custom AI agents, and Salesforce integration. The goal was to demonstrate a scalable, secure solution that could be used in real-world enterprise environments.

## Architecture Highlights

The app follows a serverless, event-driven approach with these main components:

- **Frontend**: Vue.js UI where users interact with AI agents and customer data
- **Backend**: AWS Lambda functions handling API requests, AI orchestration, and Salesforce integration
- **AI Engine**: Custom API set of Open AI
- **Data Layer**: DynamoDB for storing structured data and maintaining agent state
- **Event Handling**: Need to fully implement only api gateway to sqs and sqs to Lambda has been created but not fully tested
- **Security**: JWT auth with Cognito 

## Cool Features

### 🤖 Custom AI Agent System

I built a custom AI agent framework that:
- Maintains state between conversations
- Supports different agent types for various tasks
- Works asynchronously to handle complex requests

### ☁️ AWS Serverless Stack

Everything runs on serverless AWS components:
- API Gateway → Lambda → DynamoDB core flow
- SQS for handling background tasks
- CloudWatch for monitoring what's happening
- WAF keeping the bad actors out

### 🔄 Salesforce Data Integration

Customer data flows from Salesforce using:
- OAuth 2.0 for secure authentication
- REST API calls for data exchange
- Scheduled sync jobs to keep everything up-to-date

### 🌎 Multi-Region Ready

The app can run across multiple AWS regions with:
- DynamoDB global tables for data replication
- Regional API endpoints for lower latency
- Stateless Lambda functions that work anywhere

## Why I Made These Choices


I decided to create my own AI agent framework with OpenAI instead of using OpenAI's SDK directly because it was more complex and keepoing my application simple:

1. I wanted more control over how agents manage state
2. OpenAI offers more fexibility
3. This approach makes it easier to switch AI providers later

Downside: It means more code for me to maintain.

### Async Processing for AI Tasks

I implemented async processing for AI tasks because:

1. It scales better with lots of concurrent users
2. Users don't have to wait for AI to finish thinking
3. If something fails, we can retry without affecting the user

Downside: It makes the client-side a bit more complex with polling.

### Why DynamoDB?

I picked DynamoDB as the main database because:

1. It fits perfectly with the serverless architecture
2. It handles high traffic without breaking a sweat
3. Global tables feature makes multi-region deployment simple

Downside: Complex queries are harder than with SQL databases.

## What I'd Improve With More Time

This was built in about 8 hours, so there are several things I'd enhance given more time:

1. Better error handling and recovery flows
2. Add API caching for frequently accessed data
3. SQS implementation
4. Write comprehensive tests
5. Set up a proper CI/CD pipeline
6. Integrate specialized AI models for specific tasks
7. Add websockets for real-time updates
8. Cognito advance features

## Getting Started

### Prerequisites

You'll need:
- Node.js 14+ and npm
- Python 3.9+
- AWS CLI set up with the right permissions
- OpenAI Key
- Salesforce developer account

### Quick Setup

1. Clone the repo
   ```
   git clone https://github.com/vishalc412/ExpediteCommerceAssignment.git
   cd ai-saas-demo
   ```

2. Set up the backend
   ```
   cd backend
   pip install -r requirements.txt
   ```

3. Set up the frontend
   ```
   cd ../frontend
   npm install
   ```

4. Set your environment variables
   ```
   cp .env.example .env
   # Then edit .env with your settings
   ```

5. Deploy to AWS
   ```
   cd ../infrastructure
   ./scripts/deploy.sh dev
   ```

6. Run locally for development
   ```
   cd ../frontend
   npm run serve
   ```

### Demo Login

For the demo, use:
- Email: VishalChawla
- Password: Password@123#

Feel free to reach out if you have any questions or feedback!