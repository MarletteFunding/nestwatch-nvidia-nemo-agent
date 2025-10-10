# 🏗️ NestWatch Project Structure

## 📁 Organized File Structure

```
NeMo-Agent-Toolkit-develop/
├── 🌐 Frontend (Next.js Dashboard)
│   ├── pages/
│   │   ├── dashboard.tsx          # Main SRE dashboard
│   │   ├── index.tsx              # Homepage
│   │   └── api/events/real.ts     # Event API endpoint
│   ├── components/
│   │   ├── SRE/AIAssistant.tsx    # AI chat interface
│   │   ├── ThemeContext.tsx       # Theme management
│   │   ├── ErrorBoundary.tsx      # Error handling
│   │   └── ErrorStates/           # Professional error state components
│   │       ├── APIErrorState.tsx  # API error handling
│   │       ├── EmptyState.tsx     # Empty state handling
│   │       └── LoadingState.tsx   # Loading state handling
│   └── ui/                        # NestWatch UI components
│
├── 🔧 Backend (FastAPI + Multi-Provider AI)
│   ├── backend/
│   │   ├── app.py                 # Main FastAPI application (2091 lines)
│   │   └── requirements.txt       # Python dependencies
│   ├── plugins/
│   │   ├── multi_provider_llm.py  # Multi-provider AI system (834 lines)
│   │   ├── nemo_llm_provider.py   # Enhanced NeMo provider (650 lines)
│   │   ├── llm_cache.py           # Caching system
│   │   ├── llm_circuit.py         # Circuit breaker
│   │   └── sre_tools_unified.py   # SRE tools
│   ├── config/
│   │   ├── multi_provider_config.py # Multi-provider configuration
│   │   ├── anthropic_config.py    # Anthropic settings
│   │   └── openai_config.py       # OpenAI settings
│   └── middleware/
│       └── rate_limit.py          # Rate limiting
│
├── 📚 Documentation (Organized)
│   ├── docs/
│   │   ├── README.md              # Documentation index
│   │   ├── setup/
│   │   │   ├── SETUP.md           # Basic setup
│   │   │   ├── MULTI_PROVIDER_SETUP.md # AI setup
│   │   │   └── BESTEGG_SETUP.md   # Advanced setup
│   │   ├── corporate/
│   │   │   ├── ZSCALER_DEPLOYMENT_GUIDE.md # Corporate deployment
│   │   │   └── CORPORATE_SETUP_COMPLETE.md # Corporate summary
│   │   └── deployment/
│   │       ├── PRODUCTION_READY_GUIDE.md # Production guide
│   │       └── PROJECT_SUMMARY.md # Project overview
│   ├── AI_PROMPT_CONTEXT.md       # AI context
│   ├── CHATGPT5_PROJECT_CONTEXT.md # Project context
│   ├── PLUGIN_MIGRATION.md        # Migration guide
│   └── GITHUB_CHECKLIST.md        # Development checklist
│
├── 🛠️ Scripts (Organized)
│   ├── scripts/
│   │   ├── setup/
│   │   │   ├── setup_anthropic.py # Anthropic setup
│   │   │   ├── setup_api_credentials.py # API setup
│   │   ├── test-error-scenarios.sh # Error testing automation
│   │   └── test-comprehensive-errors.sh # Comprehensive error testing
│   │   │   └── setup_zscaler_environment.py # Corporate setup
│   │   ├── corporate/
│   │   │   ├── download_models_corporate.py # Model downloader
│   │   │   └── install_corporate.sh # Corporate installer
│   │   └── demo/
│   │       └── production_demo.py # System demonstration
│   └── verify-contrast.js         # Accessibility testing
│
├── 🤖 AI Models & Configuration
│   ├── models/
│   │   ├── offline_config.json    # Offline model config
│   │   └── corporate_config.json  # Corporate model settings
│   ├── prompts/
│   │   ├── system/sre_core_v3.md  # System prompts
│   │   └── cards/event_analysis_v1.md # Analysis prompts
│   └── schemas/
│       └── event_analysis_v1.json # Event schemas
│
├── 🎨 UI & Styling
│   ├── styles/
│   │   ├── globals.css            # Global styles
│   │   ├── components/nestwatch.css # Component styles
│   │   └── tokens/nestwatch.css   # Design tokens
│   ├── public/
│   │   ├── images/                # Logos and assets
│   │   └── icons/                 # Icon assets
│   └── stories/                   # Storybook components
│
├── ⚙️ Configuration
│   ├── package.json               # Node.js dependencies
│   ├── next.config.js             # Next.js configuration
│   ├── tailwind.config.js         # Tailwind CSS config
│   ├── tsconfig.json              # TypeScript config
│   ├── zscaler.env.example        # Corporate environment template
│   └── multi-provider.env.example # Multi-provider template
│
├── 🧪 Testing & Quality
│   ├── tests/
│   │   └── test_quota_controls.py # Backend tests
│   └── .gitignore                 # Git ignore rules
│
└── 📊 Data & Runtime
    ├── sre_events.db              # SQLite database
    ├── venv/                      # Python virtual environment
    └── node_modules/              # Node.js modules
```

## 🎯 Key Components Status

### ✅ **Fully Operational**
- **Dashboard**: http://localhost:3000/dashboard
- **Backend API**: http://localhost:8000/
- **Multi-Provider AI**: 4 providers available
- **Corporate Compatibility**: Zscaler-ready
- **Health Monitoring**: Real-time status
- **Documentation**: Comprehensive guides

### 🔧 **Architecture Overview**

```
┌─────────────────────────────────────────────────┐
│                Frontend Layer                   │
│         Next.js Dashboard (Port 3000)          │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │  Dashboard  │  │AI Assistant │  │  Themes  │ │
│  │   (React)   │  │   (Hawky)   │  │   (CSS)  │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────▼───────────────────────────────┐
│               Backend Layer                     │
│         FastAPI Server (Port 8000)             │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │   Legacy    │  │Multi-Provider│  │   New    │ │
│  │ Endpoints   │  │  AI System   │  │ Features │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────┬───────────────────────────────┘
                  │ Provider APIs
┌─────────────────▼───────────────────────────────┐
│              AI Provider Layer                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │   Bedrock   │  │  Anthropic  │  │   NeMo   │ │
│  │    (AWS)    │  │  (Direct)   │  │ (Local)  │ │
│  └─────────────┘  └─────────────┘  └──────────┘ │
└─────────────────────────────────────────────────┘
```

## 📋 **File Organization Benefits**

### 🎯 **Clear Structure**
- **Logical grouping**: Related files together
- **Easy navigation**: Clear directory purposes
- **Scalable**: Easy to add new components
- **Maintainable**: Clear separation of concerns

### 🔍 **Quick Access**
- **Documentation**: All guides in `docs/`
- **Scripts**: Organized by purpose in `scripts/`
- **Configuration**: Centralized settings
- **Components**: Modular frontend/backend

### 🛡️ **Production Ready**
- **Corporate compliance**: Zscaler-compatible
- **Monitoring**: Health checks and logging
- **Scalability**: Multi-provider architecture
- **Reliability**: Fallback systems

## 🚀 **Usage Patterns**

### **Development**
```bash
# Start development
npm run dev                    # Frontend
cd backend && python app.py   # Backend

# Check status
curl http://localhost:8000/api/v1/providers/health
```

### **Corporate Deployment**
```bash
# Corporate setup
./scripts/corporate/install_corporate.sh

# Zscaler configuration
python scripts/setup/setup_zscaler_environment.py
```

### **Production**
```bash
# Production demo
python scripts/demo/production_demo.py

# Health monitoring
curl http://localhost:8000/api/v1/providers/usage
```

---

**🎉 Your NestWatch system is now beautifully organized and fully functional!**
