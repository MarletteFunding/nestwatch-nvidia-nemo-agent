# 🚀 Quick Setup Guide

## Prerequisites


- Node.js 18+ and npm
- Python 3.10+
- OpenAI API key (optional, for AI features)

## Installation

### 1. Clone and Install Dependencies


```bash

git clone <your-repo-url>
cd NeMo-Agent-Toolkit-develop
npm install

```

### 2. Backend Setup


```bash

cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

```

### 3. Environment Configuration


```bash

# Copy example files
cp .env.example .env
cp credentials.py.example credentials.py

# Edit .env with your API keys

nano .env

```

### 4. Start the Application


```bash

# Terminal 1: Start Backend
cd backend
source venv/bin/activate
python app.py

# Terminal 2: Start Frontend

npm run dev

```

### 5. Access the Application


- **Frontend**: http://localhost:3000
- **SRE Dashboard**: http://localhost:3000/sre-dashboard
- **Backend API**: http://localhost:8000

## Configuration

### Required Environment Variables


- `OPENAI_API_KEY`: Your OpenAI API key (for AI features)
- `SRE_API_BASE_URL`: Your SRE API endpoint

### Optional Configuration


- Slack, JIRA, Datadog integrations
- Redis for caching
- LLM quota controls

## Features


- 📊 Real-time SRE event monitoring
- 🤖 AI-powered analysis (with OpenAI)
- 🔌 Circuit breakers and quota controls
- 📈 Enhanced dashboards and analytics
- 🔧 JIRA, Slack, Datadog integrations

## Troubleshooting


- Check logs in `backend/server.log`
- Verify environment variables in `.env`
- Ensure all dependencies are installed
- Check API key quotas and limits
