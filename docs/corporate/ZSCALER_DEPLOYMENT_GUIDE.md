# 🏢 Zscaler Corporate Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the NestWatch Multi-Provider AI system in corporate environments with Zscaler proxy and security controls.

## 🔍 Corporate Environment Detection

The system automatically detects corporate environments by checking for:

- **Proxy Environment Variables**: `HTTP_PROXY`, `HTTPS_PROXY`, `ZSCALER_PROXY`
- **Corporate Hostnames**: Contains `corp`, `corporate`, or `company`
- **Corporate Mode Flag**: `CORPORATE_MODE=true`

## 🚀 Quick Start for Corporate Environments

### 1. Run Corporate Installation Script

```bash
# Make script executable
chmod +x scripts/install_corporate.sh

# Run corporate-friendly installation
./scripts/install_corporate.sh
```

### 2. Configure Environment

```bash
# Copy corporate environment template
cp zscaler.env.example .env.local

# Edit with your corporate settings
nano .env.local
```

### 3. Test Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Run Zscaler-aware setup
python scripts/setup_zscaler_environment.py

# Test backend
cd backend && python -c "import app; print('✅ Backend ready')"
```

## 🔧 Corporate Environment Configuration

### SSL/TLS Configuration

For corporate environments with SSL inspection:

```bash
# In .env.local
PYTHONHTTPSVERIFY=0
REQUESTS_CA_BUNDLE=""
CURL_CA_BUNDLE=""
CORPORATE_MODE=true
```

### Proxy Configuration

If your environment requires explicit proxy settings:

```bash
# In .env.local
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
NO_PROXY=localhost,127.0.0.1,.company.com
```

### Pip Configuration

The installation script automatically creates `~/.pip/pip.conf`:

```ini
[global]
timeout = 300
retries = 10
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
               download.pytorch.org
               developer.download.nvidia.com
               huggingface.co

[install]
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
```

## 🤖 AI Provider Configuration for Corporate

### Recommended Provider Priority

```bash
# Conservative corporate setup
PROVIDER_PRIORITY=bedrock,anthropic,openai

# Security-focused setup
PROVIDER_PRIORITY=nemo_local,bedrock,anthropic
```

### AWS Bedrock (Recommended for Corporate)

```bash
# Works well through corporate proxies
ENABLE_BEDROCK=true
AWS_REGION=us-east-1
AWS_PROFILE=your-corporate-profile  # Preferred
# OR
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Local NeMo (Corporate Safe)

```bash
# For sensitive corporate data
ENABLE_LOCAL_NEMO=true
NEMO_MODEL_PATH=microsoft/DialoGPT-medium
NEMO_DEVICE=cpu
NEMO_MAX_MEMORY_GB=4
```

### Anthropic Direct API

```bash
# Your existing setup continues to work
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

## 🔒 Security Considerations

### Data Routing for Corporate Security

```bash
# Route sensitive requests to local processing
SENSITIVE_PROVIDER=nemo_local
CONFIDENTIAL_PROVIDER=nemo_local

# Route general requests to cloud providers
DASHBOARD_PROVIDER=bedrock
INCIDENT_PROVIDER=anthropic
```

### Conservative Quota Settings

```bash
# Corporate-friendly limits
MAX_TOKENS_PER_REQUEST=300
MAX_REQUESTS_PER_MINUTE=30
MAX_COST_PER_HOUR=5.0
ENABLE_COST_TRACKING=true
```

## 🌐 Network Troubleshooting

### Common Issues and Solutions

#### SSL Certificate Verification Errors

**Problem**: `certificate verify failed: Basic Constraints of CA cert not marked critical`

**Solution**:
```bash
# In .env.local
PYTHONHTTPSVERIFY=0
REQUESTS_CA_BUNDLE=""

# Or set corporate certificate bundle
REQUESTS_CA_BUNDLE=/path/to/corporate-ca-bundle.crt
```

#### Proxy Connection Issues

**Problem**: Connection timeouts or proxy errors

**Solution**:
```bash
# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Test connectivity
curl -v --proxy $HTTP_PROXY https://api.anthropic.com/
```

#### Package Installation Failures

**Problem**: pip install fails with SSL or timeout errors

**Solution**:
```bash
# Use corporate-friendly pip settings
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org package_name

# Or use the corporate installation script
./scripts/install_corporate.sh
```

### Network Connectivity Test

```bash
# Test connectivity to required services
python scripts/setup_zscaler_environment.py

# Manual connectivity test
curl -s --max-time 10 https://pypi.org/simple/ && echo "✅ PyPI"
curl -s --max-time 10 https://api.anthropic.com/ && echo "✅ Anthropic"
```

## 📦 Corporate-Friendly Dependencies

### Modified Requirements

The corporate installation uses modified dependencies:

```txt
# Heavy dependencies commented out for corporate environments
# nemo_toolkit[nlp]>=1.22.0  # Install manually if needed
# nvidia-ml-py3>=11.0.0      # GPU optional in corporate
# pytorch-lightning>=2.0.0   # Heavy dependency
# torchmetrics>=0.11.0       # Optional

# Added corporate-friendly alternatives
requests>=2.31.0
urllib3>=2.0.0
certifi>=2023.7.22
huggingface_hub>=0.17.0
psutil>=5.9.0
```

### PyTorch Installation

```bash
# CPU-only PyTorch for corporate environments
pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu
```

## 🚀 Deployment Steps

### Phase 1: Basic Setup (No Changes Required)

1. ✅ Your existing system works unchanged
2. ✅ All current endpoints function normally
3. ✅ Anthropic integration preserved

### Phase 2: Add Corporate-Friendly Providers

1. **Configure AWS Bedrock**:
   ```bash
   # Set up AWS credentials (use IAM roles when possible)
   aws configure --profile corporate
   
   # Enable Bedrock
   echo "ENABLE_BEDROCK=true" >> .env.local
   echo "AWS_PROFILE=corporate" >> .env.local
   ```

2. **Test Multi-Provider System**:
   ```bash
   # Check provider health
   curl http://localhost:8000/api/v1/providers/health
   
   # Test generation
   curl -X POST http://localhost:8000/api/v1/providers/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Test corporate deployment", "max_tokens": 100}'
   ```

### Phase 3: Enable Local Processing (Optional)

1. **Setup Local NeMo**:
   ```bash
   # Enable local processing for sensitive data
   echo "ENABLE_LOCAL_NEMO=true" >> .env.local
   echo "NEMO_MODEL_PATH=microsoft/DialoGPT-medium" >> .env.local
   ```

2. **Configure Security Routing**:
   ```bash
   # Route sensitive requests locally
   echo "SENSITIVE_PROVIDER=nemo_local" >> .env.local
   echo "CONFIDENTIAL_PROVIDER=nemo_local" >> .env.local
   ```

## 🔍 Monitoring and Logging

### Corporate Logging Configuration

```python
# In backend/app.py - already configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/corporate.log'),
        logging.StreamHandler()
    ]
)
```

### Health Check Endpoints

```bash
# System health
GET /api/v1/providers/health

# Usage statistics
GET /api/v1/providers/usage

# Provider availability
GET /api/v1/providers/status
```

## 🆘 Support and Troubleshooting

### Common Corporate Environment Issues

1. **SSL Verification Failures**
   - Solution: Set `PYTHONHTTPSVERIFY=0` in environment
   - Alternative: Configure corporate CA bundle

2. **Proxy Authentication**
   - Solution: Include credentials in proxy URL
   - Format: `http://username:password@proxy.company.com:8080`

3. **Firewall Restrictions**
   - Solution: Use local NeMo models for sensitive processing
   - Alternative: Request firewall exceptions for AI APIs

4. **Model Download Issues**
   - Solution: Use corporate-approved model repositories
   - Alternative: Download models manually and place in `models/` directory

### Getting Help

1. **Check Logs**: `tail -f backend/logs/corporate.log`
2. **Test Connectivity**: `python scripts/setup_zscaler_environment.py`
3. **Validate Configuration**: `curl http://localhost:8000/api/v1/providers/health`

## 📋 Corporate Deployment Checklist

- [ ] Run corporate installation script
- [ ] Configure `.env.local` with corporate settings
- [ ] Test network connectivity
- [ ] Configure SSL/proxy settings
- [ ] Set up AWS credentials (if using Bedrock)
- [ ] Test provider health endpoints
- [ ] Configure security routing rules
- [ ] Set up monitoring and logging
- [ ] Document corporate-specific configurations
- [ ] Train team on corporate deployment

## 🎯 Success Metrics

Your corporate deployment is successful when:

- ✅ Backend starts without errors
- ✅ Provider health checks pass
- ✅ API endpoints respond correctly
- ✅ Sensitive data routes to local processing
- ✅ Cost tracking and quotas work
- ✅ Fallback systems function properly

---

**🏢 Your NestWatch system is now ready for enterprise corporate deployment with Zscaler compatibility!**
