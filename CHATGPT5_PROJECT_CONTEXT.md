# NestWatch NVIDIA NeMo Agent - Technical Context for AI Assistants

## Project Overview
**NestWatch** is a production-ready Site Reliability Engineering (SRE) monitoring dashboard that aggregates real-time alerts from multiple sources and provides AI-powered incident analysis. It's currently operational and monitoring 81+ live production events.

## Architecture Summary

### Technology Stack
```
Frontend: Next.js 14 + TypeScript + Tailwind CSS (Port 3000)
Backend: FastAPI + Python + Uvicorn (Port 8000)
AI: Anthropic Claude (claude-3-5-sonnet-20241022)
Data Sources: SRE API, Datadog, JIRA, JAMS
Theme: Custom NestWatch design system (light/dark mode)
```

### Core Components
```
/pages/dashboard.tsx          # Main SRE dashboard (1,349 lines)
/backend/app.py              # FastAPI server (1,889 lines)
/plugins/nemo_llm_provider.py # AI integration
/components/SRE/             # React components
/ui/icons/nestwatch/         # Custom icon system
```

## Current System Status
- **✅ Operational**: Both frontend (3000) and backend (8000) running
- **✅ Live Data**: Fetching 81 real events from `sre-api-service-ext.bestegg.com`
- **✅ AI Integration**: Anthropic Claude for intelligent analysis
- **✅ Multi-source**: Datadog, JIRA, JAMS alert aggregation

## Key Features for AI Understanding

### 1. Real-Time Event Monitoring
```javascript
// Frontend fetches from backend API
GET /api/events/real?limit=100
// Backend proxies to external SRE API
https://sre-api-service-ext.bestegg.com/event_interactions/events
```

### 2. Priority-Based Filtering
```
P1 (Critical): Red diamond icons - immediate attention
P2 (High): Yellow warning triangles - fix today  
P3 (Medium): Blue info circles - fix when possible
```

### 3. AI-Powered Analysis
```python
# AI assistant "Hawky" provides:
- Event interpretation and context
- Suggested remediation steps
- Impact analysis
- Root cause insights
```

### 4. Multi-Source Integration
```
Data Sources:
- SRE API (primary): Real production events
- Datadog: Infrastructure monitoring
- JIRA: Incident tickets
- JAMS: Job scheduling alerts
```

## File Structure Context
```
├── backend/
│   ├── app.py                    # Main FastAPI application
│   └── requirements.txt          # Python dependencies
├── pages/
│   ├── dashboard.tsx             # Primary dashboard interface
│   └── api/events/real.ts        # Event API endpoint
├── plugins/
│   ├── nemo_llm_provider.py      # Anthropic Claude integration
│   ├── llm_cache.py              # Response caching (5min TTL)
│   ├── llm_circuit.py            # Circuit breaker pattern
│   └── sre_tools_unified.py      # SRE operations toolkit
├── components/SRE/               # React components
├── ui/icons/nestwatch/           # Custom SVG icon system
└── styles/                       # NestWatch design system
```

## API Endpoints for AI Reference
```
Health Checks:
GET /api/v1/health              # Backend health
GET /api/v1/nemo/health         # AI service health

Event Data:
GET /event_interactions/events  # All SRE events
GET /api/events/real           # Filtered events with priority/source

AI Integration:
POST /api/v1/nemo/dashboard-insights  # AI analysis
GET /api/v1/sre/usage          # LLM quota status
```

## Environment Configuration
```bash
# Required for full functionality
ANTHROPIC_API_KEY=claude_api_key
SRE_API_BASE_URL=https://sre-api-service-ext.bestegg.com
DATADOG_API_KEY=datadog_key
JIRA_API_TOKEN=jira_token
SLACK_BOT_TOKEN=slack_token

# LLM Controls
LLM_CACHE_TTL_SEC=300
LLM_RPS=0.5
LLM_BURST=2
```

## Data Flow for AI Understanding
```
1. External APIs → Backend aggregation
2. Backend → Event normalization & caching
3. Frontend → Real-time dashboard updates
4. User interaction → AI analysis request
5. Claude API → Intelligent insights
6. Dashboard → Actionable recommendations
```

## Current Production Metrics
```
Active Events: 81+ live production alerts
Response Time: 1-6 seconds for event fetching
Build Status: ✅ Compiled (290 modules)
API Status: ✅ All endpoints responding
Cache Hit Rate: 80-90% (LLM responses)
```

## Key Business Context
- **Problem**: DevOps teams juggle multiple monitoring dashboards
- **Solution**: Single unified dashboard with AI assistance
- **Value**: Faster incident resolution, reduced alert fatigue
- **Users**: SRE teams, DevOps engineers, on-call personnel

## Technical Capabilities
```
✅ Real-time event aggregation from multiple sources
✅ AI-powered incident analysis and recommendations
✅ Priority-based filtering and visual indicators
✅ Responsive design with accessibility features
✅ Quota controls and caching for cost optimization
✅ Circuit breaker patterns for reliability
✅ Rate limiting and security middleware
```

## Development Commands
```bash
# Backend
cd backend && python app.py

# Frontend  
npm run dev

# Health checks
curl http://localhost:8000/api/v1/health
curl http://localhost:3000/dashboard
```

## AI Integration Details
```python
# Current AI Provider: Anthropic Claude
Model: claude-3-5-sonnet-20241022
Temperature: 0.0
Max Tokens: 600
Use Cases:
- Event analysis and interpretation
- Incident response recommendations
- Context-aware SRE guidance
- Automated summary generation
```

## Deployment Status
- **Current**: Development environment (localhost)
- **Ready For**: AWS cloud deployment
- **Infrastructure**: Containerized (Docker-ready)
- **Scaling**: Horizontal scaling capable
- **Monitoring**: CloudWatch integration ready

## For AI Assistants Working With This Project

### Common Tasks:
1. **Debugging**: Check logs in terminal output, verify API connectivity
2. **Feature Development**: Extend dashboard components, add new data sources
3. **AI Enhancement**: Improve Claude prompts, add new analysis capabilities
4. **Infrastructure**: Deploy to AWS, optimize performance
5. **Integration**: Add new monitoring sources, enhance existing APIs

### Key Files to Reference:
- `backend/app.py`: Core API logic and external integrations
- `pages/dashboard.tsx`: Main user interface and React components
- `plugins/nemo_llm_provider.py`: AI integration and prompt engineering
- `README.md`: Comprehensive setup and usage documentation

### Current System State:
The system is **fully operational** with both services running, successfully fetching live production data, and ready for team adoption or cloud deployment.

---

**This context should enable any AI assistant to understand the project architecture, current status, and technical implementation details for effective collaboration.**
