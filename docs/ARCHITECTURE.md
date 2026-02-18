# MediBot Architecture Documentation

## Overview

MediBot is an AI-powered medical assistant that provides health information with visual treatment guides. Built on AWS serverless architecture with React frontend.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CloudFront CDN                          │
│                    (Static Assets + API Caching)                │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌───────────────┐                         ┌─────────────────┐
│  S3 (Frontend)│                         │   API Gateway   │
│  React SPA    │                         │   (HTTP API)    │
└───────────────┘                         └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌───────────────┐
                                          │    Lambda     │
                                          │  (FastAPI)    │
                                          └───────┬───────┘
                                                  │
        ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
        │                                         │                                         │
        ▼                                         ▼                                         ▼
┌───────────────┐                        ┌───────────────┐                        ┌───────────────┐
│   DynamoDB    │                        │   Google AI   │                        │      S3       │
│  - Chats      │                        │   (Gemini)    │                        │  - Images     │
│  - Profiles   │                        │               │                        │  - Reports    │
│  - Guests     │                        └───────────────┘                        └───────────────┘
│  - Audit Logs │
└───────────────┘
        │
        ▼
┌───────────────┐
│    Cognito    │
│  (Auth)       │
└───────────────┘
```

## Components

### Frontend (React 19 + TypeScript + Vite)

| Directory | Purpose |
|-----------|---------|
| `src/components/` | Reusable UI components (StepCard, Toast, LoadingSpinner) |
| `src/pages/` | Route pages (Chat, History, Profile) |
| `src/hooks/` | Custom React hooks |
| `src/api/` | API client functions |
| `src/types/` | TypeScript type definitions |

### Backend (Python FastAPI + AWS Lambda)

| Module | Purpose |
|--------|---------|
| `api_server.py` | FastAPI routes, request handling |
| `model_router.py` | Intelligent routing between Flash (simple) and Pro (complex) models |
| `gemini_client.py` | Google Gemini AI integration |
| `auth.py` | JWT verification, Cognito integration |
| `chat_history.py` | Chat CRUD operations |
| `health_profile.py` | User health profile management |
| `guest_tracking.py` | Server-side guest session tracking |
| `audit_logging.py` | Security audit event logging |
| `llm_safety.py` | Prompt injection detection, output validation |
| `monitoring.py` | CloudWatch metrics and instrumentation |

### Infrastructure (AWS SAM)

| Resource | Service | Purpose |
|----------|---------|---------|
| `MediBotFunction` | Lambda | API backend |
| `MediBotApi` | API Gateway | HTTP API with rate limiting |
| `ChatHistoryTable` | DynamoDB | Chat message storage |
| `HealthProfileTable` | DynamoDB | User health profiles |
| `GuestSessionsTable` | DynamoDB | Guest trial tracking |
| `AuditLogTable` | DynamoDB | Security audit logs |
| `ImagesBucket` | S3 | Generated step images |
| `ReportsBucket` | S3 | Uploaded medical reports |
| `CognitoUserPool` | Cognito | User authentication |

## Data Flow

### Chat Request Flow

1. User sends message via React frontend
2. Request hits CloudFront → API Gateway → Lambda
3. Lambda validates auth (if provided), checks guest limits
4. LLM safety checks sanitize input
5. Gemini processes query with health context (RAG)
6. Response is validated for safety
7. Images are generated and uploaded to S3
8. Chat is saved to DynamoDB (if authenticated)
9. Response returned to frontend

### Authentication Flow

1. User signs in via Cognito hosted UI
2. JWT token stored in frontend
3. Token sent in Authorization header
4. Lambda validates JWT against Cognito JWKS
5. User ID extracted for personalized features

## Security Measures

- **Authentication**: AWS Cognito with JWT validation
- **Rate Limiting**: API Gateway throttling + Lambda-level guest limits
- **Audit Logging**: All sensitive operations logged to DynamoDB
- **LLM Safety**: Prompt injection detection, output validation
- **Encryption**: S3 server-side encryption, HTTPS only
- **Private Reports**: Reports bucket not publicly accessible

## Monitoring

- **CloudWatch Alarms**: API errors, LLM errors, latency, abuse detection
- **Custom Metrics**: Chat requests, LLM calls, image generation, security events
- **Structured Logging**: aws-lambda-powertools for tracing
