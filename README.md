# Medical Assistant Chatbot - Serverless AWS Deployment

A modern, AI-powered medical assistant chatbot with:
- 🤖 **AWS Bedrock LLM** (Mistral Small) for fast, accurate medical advice
- 🖼️ **AI-generated medical illustrations** (Titan Image Generator v1) for **every treatment step**
- ☁️ **Serverless Architecture** (Lambda, API Gateway, S3, CloudFront)
- 🚀 **Parallel Processing** for low-latency responses (<15s)
- 🌐 **Multilingual support** (English, Telugu, Hindi)
- 📱 **Responsive design** (mobile, tablet, desktop)

## 🏗️ Architecture

- **Frontend**: Next.js static export deployed to Amazon S3, served via CloudFront (CDN).
- **Backend**: FastAPI on AWS Lambda (via Mangum), exposed via API Gateway.
- **Storage**: Amazon S3 for storing AI-generated medical images (auto-deleted after 1 day).
- **AI Models**: 
    - LLM: `mistral.mistral-small-2402-v1:0` (Optimized for speed)
    - Image: `amazon.titan-image-generator-v1`

## 🚀 Deployment Status

**Production Environment (us-east-1)**
- **Frontend URL**: [https://d17eixu2k5iihu.cloudfront.net](https://d17eixu2k5iihu.cloudfront.net)
- **API URL**: `https://khucwqfzv4.execute-api.us-east-1.amazonaws.com/production`

## 🛠️ Project Structure

```
├── backend/                 # Python FastAPI backend (Lambda compatible)
│   ├── api_server.py       # Main API server with parallel processing
│   ├── bedrock_client.py   # AWS Bedrock & S3 integration
│   ├── translation.py      # Multilingual support
│   ├── lambda_handler.py   # Mangum adapter for Lambda
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # Next.js React frontend
│   ├── app/               # Main application steps
│   └── next.config.ts     # Configured for static export
│
├── infrastructure/         # Infrastructure as Code
│   └── template.yaml      # AWS SAM Template (Lambda, S3, API Gateway, CloudFront)
│
└── deploy.sh              # One-click deployment script
```

## ⚡ Key Features

### 1. Unlimited Visual Guides
Unlike standard chatbots, MediBot generates a unique medical illustration for **every single step** of a treatment guide. 
- *Example*: "How to treat a cut on neck" -> Generates specific images for neck wound care.
- **Technology**: Uses parallel execution (ThreadPoolExecutor) to generate 5-10 images in <10 seconds.

### 2. Low-Latency Performance
- **Optimized Model**: Switched from Mistral Large (26s) to Mistral Small (5s) for rapid responses.
- **Parallel Uploads**: Images are uploaded to S3 concurrently with generation.

### 3. Smart Context Awareness
- **Conversation Mode**: Handles greetings ("Hi") naturally without hallucinating medical issues.
- **Medical Mode**: Enforces strict step-by-step format only when real medical queries are detected.
- **Body Part Detection**: Dynamically injects the body part (e.g., "neck", "hand") into image prompts for anatomical accuracy.

### 4. User-Friendly Interface
- **New Chat Button**: Instantly reset conversation history with a single click.
- **Multilingual Toggle**: Easy switching between English, Telugu, and Hindi.

## 📈 Scalability & Capacity

This project is built on AWS Serverless architecture (Lambda + API Gateway), making it highly scalable:

| Metric | Capacity | Notes |
| :--- | :--- | :--- |
| **Concurrent Users** | **~1,000** | Default AWS Lambda burst limit (can be increased). |
| **Frontend Traffic** | **Unlimited** | Served via CloudFront (CDN) + S3. |
| **Bottleneck** | **Image Gen** | AWS Bedrock limits image generation rate per account. |

**Performance**: 
- Validated for **100+ simultaneous chats** in testing.
- Auto-scaling handles traffic spikes instantly without manual intervention.

## 💻 Local Development

### 1. Install Backend
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` with AWS credentials:
```env
AWS_BEARER_TOKEN_BEDROCK=your_token
BEDROCK_REGION=us-east-1
IMAGES_BUCKET=your-existing-bucket-name  # Optional for local test
```

### 3. Run Locally
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
./deploy.sh
```

Or manually:
```bash
cd infrastructure
sam build
sam deploy --guided
```

## License

MIT License
