# Medical Assistant Chatbot - Cloud AI Powered

![Phase](https://img.shields.io/badge/Phase-1%20Complete-brightgreen)
![LLM](https://img.shields.io/badge/LLM-Gemini%202.5%20Pro-blue)
![Status](https://img.shields.io/badge/Status-Production-success)

A modern, AI-powered medical assistant chatbot with:
- 🤖 **Google Gemini 2.5 Pro** for fast, accurate medical advice
- 🖼️ **AI-generated medical illustrations** (Gemini 2.5 Flash Image) for **every treatment step**
- ☁️ **Serverless Architecture** (AWS Lambda, API Gateway, S3, CloudFront)
- 🚀 **Parallel Processing** for low-latency responses
- 🌐 **Multilingual support** (English, Telugu, Hindi)
- 📱 **Responsive design** (mobile, tablet, desktop)

---

## 📍 Project Roadmap

### ✅ Phase 1: Core MVP (Complete)
| Feature | Status |
| :--- | :--- |
| FastAPI backend on AWS Lambda | ✅ Done |
| Next.js frontend on CloudFront | ✅ Done |
| Google Gemini 2.5 Pro LLM integration | ✅ Done |
| Gemini 2.5 Flash Image generation | ✅ Done |
| Step-by-step visual treatment guides | ✅ Done |
| S3 image storage with presigned URLs | ✅ Done |
| Multilingual support (EN, TE, HI) | ✅ Done |
| Parallel image generation (5 max) | ✅ Done |
| Production deployment (us-east-1) | ✅ Done |

### 🔜 Phase 2: Custom Domain & Enhancements (Upcoming)
| Feature | Status |
| :--- | :--- |
| Custom domain (ganeshmakkena.online) | 🔜 Planned |
| SSL certificate via ACM | 🔜 Planned |
| API Gateway custom domain | 🔜 Planned |
| WebSocket for streaming responses | 🔜 Planned |
| Async processing for unlimited images | 🔜 Planned |

### 📋 Phase 3: Advanced Features (Future)
| Feature | Status |
| :--- | :--- |
| User authentication (Cognito) | 📋 Planned |
| Chat history persistence (DynamoDB) | 📋 Planned |
| Voice input/output (speech-to-text) | 📋 Planned |
| Mobile app (React Native) | 📋 Planned |
| Analytics dashboard | 📋 Planned |

---

## 🏗️ Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Frontend   │────▶│   API Gateway   │────▶│   AWS Lambda     │
│  (CloudFront │     │    (REST API)   │     │   (FastAPI)      │
│    + S3)     │     └─────────────────┘     └────────┬─────────┘
└──────────────┘                                      │
                                                      ▼
                              ┌────────────────────────────────────────┐
                              │           Google Gemini API            │
                              │  ┌─────────────┐  ┌──────────────────┐ │
                              │  │ Gemini 2.5  │  │ Gemini 2.5 Flash │ │
                              │  │    Pro      │  │      Image       │ │
                              │  │   (LLM)     │  │  (Image Gen)     │ │
                              │  └─────────────┘  └──────────────────┘ │
                              └────────────────────────────────────────┘
                                                      │
                                                      ▼
                              ┌────────────────────────────────────────┐
                              │             Amazon S3                  │
                              │       (Generated Images Storage)       │
                              └────────────────────────────────────────┘
```

### Components:
- **Frontend**: Next.js static export deployed to Amazon S3, served via CloudFront
- **Backend**: FastAPI on AWS Lambda (via Mangum), exposed via API Gateway
- **Storage**: Amazon S3 for AI-generated medical images (presigned URLs, 2hr expiry)
- **AI Models**: 
    - LLM: **`gemini-2.5-pro`** (Google's advanced reasoning model)
    - Image: **`gemini-2.5-flash-image`** (Native image generation)

## 🚀 Deployment Status

**Production Environment (us-east-1)**
- **Frontend URL**: [https://d17eixu2k5iihu.cloudfront.net](https://d17eixu2k5iihu.cloudfront.net)
- **API URL**: `https://khucwqfzv4.execute-api.us-east-1.amazonaws.com/production`
- **Health Check**: `/health` returns model version

## 🛠️ Project Structure

```
├── backend/                 # Python FastAPI backend (Lambda compatible)
│   ├── api_server.py       # Main API server with parallel processing
│   ├── gemini_client.py    # Google Gemini API integration
│   ├── bedrock_client.py   # AWS Bedrock integration (legacy)
│   ├── translation.py      # Multilingual support
│   ├── lambda_handler.py   # Mangum adapter for Lambda
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # Next.js React frontend
│   ├── app/               # Main application pages
│   └── next.config.ts     # Configured for static export
│
├── infrastructure/         # Infrastructure as Code
│   └── template.yaml      # AWS SAM Template
│
└── README.md              # This file
```

## ⚡ Key Features

### 1. Visual Step-by-Step Guides
MediBot generates a unique medical illustration for **every treatment step**:
- *Example*: "How to treat a cut on neck" → Generates specific images for neck wound care
- **Limit**: 5 images per request (API Gateway 29s timeout)
- **Technology**: Parallel execution with ThreadPoolExecutor

### 2. Advanced AI Models
| Component | Model | Provider |
| :--- | :--- | :--- |
| **LLM** | gemini-2.5-pro | Google |
| **Image** | gemini-2.5-flash-image | Google |

### 3. Smart Context Awareness
- **Conversation Mode**: Handles greetings naturally without hallucinating medical issues
- **Medical Mode**: Strict step-by-step format for real medical queries
- **Body Part Detection**: Injects specific body parts into image prompts

### 4. User-Friendly Interface
- **New Chat Button**: Instantly reset conversation history
- **Multilingual Toggle**: Easy switching between English, Telugu, Hindi
- **Responsive Design**: Works on mobile, tablet, desktop

## 📈 Scalability & Limits

| Metric | Capacity | Notes |
| :--- | :--- | :--- |
| **Concurrent Users** | ~1,000 | AWS Lambda burst limit |
| **Frontend Traffic** | Unlimited | CloudFront CDN + S3 |
| **Lambda Timeout** | 90 seconds | Configured in SAM template |
| **API Gateway Timeout** | 29 seconds | AWS hard limit |
| **Max Images** | 5 per request | Fits within 29s timeout |

## 💻 Local Development

### 1. Install Backend
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` with:
```env
GOOGLE_API_KEY=your_gemini_api_key
BEDROCK_REGION=us-east-1
IMAGES_BUCKET=your-s3-bucket  # Optional
```

### 3. Run Backend
```bash
uvicorn api_server:app --reload --port 8000
```

### 4. Run Frontend
```bash
cd frontend
npm install
npm run dev
```

## ☁️ Deployment

Deploy to AWS using SAM:

```bash
cd infrastructure
sam build
sam deploy --guided --parameter-overrides \
  "GoogleApiKey=YOUR_API_KEY" \
  "GeminiLlmModel=gemini-2.5-pro"
```

## 🔧 Configuration

Key environment variables in `template.yaml`:

| Variable | Description |
| :--- | :--- |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `GEMINI_LLM_MODEL` | LLM model (default: gemini-2.5-pro) |
| `IMAGES_BUCKET` | S3 bucket for generated images |

## 📄 License

MIT License
