# 📚 NestWatch Documentation

## 🎯 Quick Start

Your NestWatch Multi-Provider AI system is **fully operational**:

- **Dashboard**: http://localhost:3000/dashboard
- **Backend API**: http://localhost:8000/
- **Status**: ✅ Production Ready

## 📖 Documentation Structure

### 🚀 Setup & Installation
- [`setup/SETUP.md`](setup/SETUP.md) - Basic setup instructions
- [`setup/MULTI_PROVIDER_SETUP.md`](setup/MULTI_PROVIDER_SETUP.md) - Multi-provider AI configuration
- [`setup/BESTEGG_SETUP.md`](setup/BESTEGG_SETUP.md) - Advanced setup guide

### 🏢 Corporate Deployment
- [`corporate/ZSCALER_DEPLOYMENT_GUIDE.md`](corporate/ZSCALER_DEPLOYMENT_GUIDE.md) - Corporate/Zscaler deployment
- [`corporate/CORPORATE_SETUP_COMPLETE.md`](corporate/CORPORATE_SETUP_COMPLETE.md) - Corporate setup summary

### 🎯 Production
- [`deployment/PRODUCTION_READY_GUIDE.md`](deployment/PRODUCTION_READY_GUIDE.md) - Production deployment guide
- [`deployment/PROJECT_SUMMARY.md`](deployment/PROJECT_SUMMARY.md) - Project overview

### 🔧 Development
- [`PLUGIN_MIGRATION.md`](../PLUGIN_MIGRATION.md) - Plugin migration guide
- [`GITHUB_CHECKLIST.md`](../GITHUB_CHECKLIST.md) - Development checklist

## 🎉 Current Status

Your system includes:
- ✅ **4 AI Providers**: Bedrock, NeMo Local, Anthropic, OpenAI
- ✅ **Corporate Compatible**: Works with Zscaler/proxy environments
- ✅ **Dashboard Active**: Full NestWatch UI operational
- ✅ **Health Monitoring**: Real-time system status
- ✅ **Production Ready**: Can be used immediately

## 🚀 Quick Commands

```bash
# Start dashboard (if not running)
npm run dev

# Start backend (if not running)  
cd backend && python app.py

# Check system health
curl http://localhost:8000/api/v1/providers/health

# Run production demo
python scripts/demo/production_demo.py
```

## 📞 Support

- Check system status: `curl http://localhost:8000/`
- View logs: `tail -f backend/logs/app.log`
- Test integration: `python scripts/demo/production_demo.py`
