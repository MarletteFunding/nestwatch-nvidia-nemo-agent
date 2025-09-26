# 🏢 BestEgg SRE API Integration Guide

This guide will help you configure the NeMo Agent Toolkit to work with the BestEgg SRE API service.

## 🎯 Overview

The NeMo Agent Toolkit has been configured to integrate with the BestEgg SRE API service, which provides:

- **Event Management**: Create, read, update, and delete SRE events
- **Alert Processing**: Datadog, JAMS, and other alert sources
- **Integration Hub**: JIRA, Slack, xMatters, and more
- **Multi-Environment Support**: SBX (Sandbox), UAT, and PRD (Production)

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Node.js 16+
- Access to BestEgg SRE API (contact your SRE team)

### 2. Configure Credentials

```bash

# Copy the credentials template
cp credentials.py.example credentials.py

# Edit credentials.py with your actual values

nano credentials.py

```

### 3. Test Your Configuration

```bash

# Run the BestEgg API test suite
python test_bestegg_api.py

```

### 4. Start the Toolkit

```bash

# Start the backend
cd backend
python app.py

# Start the frontend (in another terminal)

npm run dev

```

## 🔧 Configuration Details

### BestEgg SRE API Endpoints

The toolkit is configured to work with these BestEgg SRE API endpoints:

| Endpoint | Purpose | Method |
|----------|---------|--------|
| `/health` | Health check | GET |
| `/event_interactions/events` | Get all events | GET |
| `/event_interactions/events/{id}` | Get specific event | GET |
| `/event_interactions/create` | Create new event | POST |
| `/event_interactions/update` | Update event | POST |
| `/event_interactions/delete` | Delete event | POST |
| `/jams/history` | JAMS job history | GET |
| `/datadog_alert_filter` | Datadog alerts | GET |
| `/jams_alert_filter` | JAMS alerts | GET |
| `/jira_interactions` | JIRA integration | POST |
| `/slack_interactions` | Slack integration | POST |
| `/xmatters_interactions` | xMatters alerts | POST |

### Environment Configuration

The toolkit supports multiple BestEgg environments:

#### SBX (Sandbox) - Default

```python
BESTEGG_ENV = "sbx"
BESTEGG_WAF_ACL = "bbd31730-4cc1-4b48-afa5-eb75c5dd2ead"
```

#### UAT (User Acceptance Testing)

```python
BESTEGG_ENV = "uat"
BESTEGG_WAF_ACL = "fa6cdaef-d56b-411c-b4d5-0d11bb7ad2fb"
```

#### PRD (Production)

```python
BESTEGG_ENV = "prd"
BESTEGG_WAF_ACL = "3c2a7c5e-cfb0-45cb-9c92-768ff33b3995"
```

### Authentication Methods

The toolkit supports two authentication methods:

#### Method 1: API Key (Recommended)

```python
SRE_API_KEY = "your_bestegg_api_key_here"
```

#### Method 2: Bearer Token

```python
SRE_API_TOKEN = "your_bestegg_bearer_token_here"
```

## 🧪 Testing Your Setup

### Run the Test Suite

```bash
python test_bestegg_api.py
```

The test suite will:

1. ✅ Test basic connectivity to BestEgg SRE API
2. ✅ Verify authentication methods
3. ✅ Test all API endpoints
4. ✅ Validate SRE toolkit integration
5. ✅ Check event fetching and processing

### Expected Output

```text
🧪 Basic Connectivity Test
📍 API URL: https://sre-api-service-ext.bestegg.com
🌍 Environment: sbx
🔑 API Key: ✅ Set
🌐 Testing: https://sre-api-service-ext.bestegg.com/health
📊 Status Code: 200
✅ SUCCESS! BestEgg SRE API is accessible

```

## 🎮 Using the Toolkit

### Web Interface

1. Open [http://localhost:3000](http://localhost:3000)
2. Try these commands:
   - `"show SRE events"` → See all BestEgg events
   - `"P1 events"` → Filter critical events
   - `"jira events"` → Show JIRA tickets
   - `"enhanced summary"` → Get priority breakdown

### API Usage

```python

from plugins.sre_tools_unified import create_sre_tool

# Create enhanced SRE tool

tool = create_sre_tool("enhanced")

# Get all events

events = tool.fetch_events()

# Get health status

health = tool.get_health_status()

# Get JAMS history

jams_history = tool.get_jams_history()

# Get Datadog alerts

datadog_alerts = tool.get_datadog_alerts()

# Create new event

new_event = tool.create_event({
    "subject": "Test Event",
    "description": "Created via NeMo Toolkit",
    "priority": "P3"
})

```

### Chat Interface

```bash

# SRE event queries
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show SRE events", "messages": []}'

# AI-powered assistance

curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "nemo: Database connection timeout affecting 1000+ users", "messages": []}'

```

## 🔗 Integration Features

### Event Management

- **Create Events**: Automatically create SRE events from alerts
- **Update Events**: Modify event status, priority, and details
- **Delete Events**: Archive resolved events
- **Priority Filtering**: P1 (Critical), P2 (High), P3 (Medium)

### Alert Processing

- **Datadog Integration**: Process and filter Datadog alerts
- **JAMS Integration**: Monitor job failures and history
- **Multi-Source**: Handle alerts from various sources

### Communication

- **Slack Integration**: Send alerts to Slack channels
- **JIRA Integration**: Create and update tickets
- **xMatters Integration**: Trigger on-call alerts

## 🛠️ Troubleshooting

### Common Issues

#### 1. "403 Forbidden" Error

```text
❌ FORBIDDEN - API key may be invalid or insufficient permissions
```

**Solution**: Contact your SRE team to verify API credentials and permissions.

#### 2. "401 Unauthorized" Error

```text
❌ UNAUTHORIZED - Check your API credentials
```

**Solution**: Verify your API key or token in `credentials.py`.

#### 3. Connection Timeout

```text
⏰ TIMEOUT - API server may be down or slow
```

**Solution**: Check if the BestEgg SRE API service is running and accessible.

#### 4. Environment Issues

```text
❌ Environment not found
```

**Solution**: Verify `BESTEGG_ENV` is set to `sbx`, `uat`, or `prd`.

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

Test individual components:

```bash

# Test API connectivity
curl -H "X-API-Key: your_key" https://sre-api-service-ext.bestegg.com/health

# Test toolkit health

curl http://localhost:8000/api/v1/health

```

## 📞 Support

### Getting Help

1. **SRE Team**: Contact your BestEgg SRE team for API access
2. **Documentation**: Check the BestEgg SRE API documentation
3. **Logs**: Check application logs for detailed error messages
4. **Test Suite**: Run `python test_bestegg_api.py` for diagnostics

### Useful Commands

```bash

# Check configuration
python -c "from config import config; print(config.get_credential_status())"

# Test specific endpoint

python -c "from plugins.sre_tools_unified import create_sre_tool; tool = create_sre_tool(); print(tool.get_health_status())"

# View available events

python -c "from plugins.sre_tools_unified import create_sre_tool; tool = create_sre_tool(); events = tool.fetch_events(); print(f'Found {len(events)} events')"

```

## 🎉 Success Examples

### Real Production Events

The toolkit can process real BestEgg production events:

- **Subpool Lambda API Processor Failure** - Individual failures detected
- **Opportunity Orchestrator High Error Rate** - Instant qualification issues
- **IQ Affiliates p95 Latency Monitor** - Performance degradation

### Active JIRA Tickets

- **SREPS-1929** - Manual Loan Verification CSV issue
- **SREPS-1913** - FB&T OFAC File not running
- **SREPS-1909** - Website loading slowly, redirecting to homepage

## 🔄 Next Steps

1. **Configure Credentials**: Set up your API access
2. **Run Tests**: Verify connectivity with `test_bestegg_api.py`
3. **Start Toolkit**: Launch the web interface
4. **Explore Features**: Try different commands and integrations
5. **Customize**: Modify prompts and configurations as needed

---

**🎯 The NeMo Agent Toolkit is now ready to work with your BestEgg SRE API service!**
