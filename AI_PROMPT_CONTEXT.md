# AI Prompt Context for SRE Dashboard System

## 🎯 **System Overview**

This is a **Site Reliability Engineering (SRE) Dashboard** that integrates with real production SRE APIs to provide event monitoring, analysis, and management capabilities. The system combines a Next.js frontend with a Python FastAPI backend and includes LLM integration for intelligent SRE assistance.

## 🏗️ **Architecture & Components**

### **Frontend (Next.js)**

- **Dashboard**: `pages/sre-dashboard.tsx` - Main SRE events dashboard with dark/light mode
- **Components**: `components/SRE/AccessibleSREEventsDisplay.tsx` - Accessible event display and filtering
- **Theme System**: `components/ThemeContext.tsx` and `components/ThemeToggle.tsx` - Dark/light mode support
- **Styling**: Tailwind CSS with priority-based color coding and accessibility features
- **API Integration**: Proxied through Next.js to backend

### **Backend (Python FastAPI)**

- **Main App**: `backend/app.py` - FastAPI server with SRE endpoints
- **LLM Provider**: `plugins/nemo_llm_provider.py` - OpenAI integration
- **SRE Tools**: `plugins/sre_tools_unified.py` - Unified SRE operations

### **Data Sources**

- **Real SRE API**: `https://your-sre-api.com/event_interactions/events`
- **Current Data**: 60 real SRE events from production
- **Event Types**: P1 (0), P2 (7), P3 (53) priority levels
- **Sources**: JIRA, Datadog, JAMS integration

## 🔧 **Current Functionality**

### **Working Features**

✅ **Event Display**: Real-time SRE events from production API
✅ **Priority Filtering**: P1 Critical, P2 High, P3 Medium buttons
✅ **Source Filtering**: JIRA, Datadog, JAMS source buttons
✅ **Enhanced Summary**: AI-generated event summaries
✅ **Real Data Integration**: 60 production SRE events
✅ **LLM Integration**: OpenAI GPT-3.5-turbo for SRE assistance
✅ **Dark/Light Mode**: Accessible theme switching with persistence
✅ **Accessibility**: WCAG-compliant design with proper contrast and navigation

### **API Endpoints**

- `GET /event_interactions/events` - All SRE events (60 events)
- `GET /api/v1/sre/enhanced-summary` - AI summary with priority breakdown
- `GET /api/v1/sre/events/priority/{P1|P2|P3}` - Filter by priority
- `GET /api/v1/sre/events/source/{jira|datadog|jams}` - Filter by source
- `POST /api/v1/chat` - LLM chat interface for SRE assistance

## 🤖 **LLM Integration Details**

### **Current LLM Provider** (`plugins/nemo_llm_provider.py`)

- **Model**: OpenAI GPT-3.5-turbo
- **Purpose**: SRE expert assistance and event analysis
- **Context**: Site Reliability Engineering operations

### **Existing Prompts**

1. **Main SRE Assistant Prompt**:

   ```text
   "You are an expert SRE (Site Reliability Engineer) assistant. Provide helpful, professional responses focused on practical solutions, best practices, and actionable recommendations for SRE operations."
   ```

2. **Enhanced Analysis Prompt**:

   ```text
   "SRE Assistant: {query}\nResponse:"
   ```

3. **Incident Response Prompt**:

   ```text
   "As an SRE expert, analyze this incident and provide a structured response: ..."
   ```

4. **System Optimization Prompt**:

   ```text
   "As an SRE expert, analyze these system metrics and suggest optimizations: ..."
   ```

## 📊 **Data Structure**

### **SRE Event Format**

```python
@dataclass
class SREEvent:
    id: str                    # Event identifier
    slack_id: str             # Slack channel ID
    summary: str              # Event description
    status: str               # Current status (Open, In Progress, Resolved)
    priority: str             # P1, P2, P3 priority level
    source: str               # jira, datadog, jams
    timestamp: datetime       # Event timestamp

```

### **Current Event Distribution**

- **Total Events**: 60
- **P1 Critical**: 0 events
- **P2 High**: 7 events
- **P3 Medium**: 53 events
- **Datadog**: 44 events
- **JAMS**: 10 events
- **JIRA**: 6 events

## 🎨 **UI/UX Design**

### **Theme Support**

- **Light Mode**: Clean white backgrounds with dark text for daytime use
- **Dark Mode**: Dark gray backgrounds with light text for low-light environments
- **Theme Toggle**: Persistent theme switching with system preference detection
- **Accessibility**: WCAG AA compliant contrast ratios in both themes

### **Priority Color Scheme**

- **P1 Critical**: 🚨 Red (`bg-red-600`, `text-white`)
- **P2 High**: ⚠️ Orange (`bg-orange-600`, `text-white`)
- **P3 Medium**: ℹ️ Blue (`bg-blue-600`, `text-white`)

### **Event Card Styling**

- **Light Mode**:
  - P1: Red background (`bg-red-50`, `border-red-200`)
  - P2: Orange background (`bg-orange-50`, `border-orange-200`)
  - P3: Blue background (`bg-blue-50`, `border-blue-200`)
- **Dark Mode**:
  - P1: Dark red background (`bg-red-900/30`, `border-red-800`)
  - P2: Dark orange background (`bg-orange-900/30`, `border-orange-800`)
  - P3: Dark blue background (`bg-blue-900/30`, `border-blue-800`)

## 🔌 **Integration Capabilities**

### **SRE Tools Available**

- **JIRA Integration**: Ticket creation and management
- **Slack Integration**: Alert notifications with priority emojis
- **Datadog Integration**: Metrics querying and monitoring
- **JAMS Integration**: Job status monitoring

### **LLM Capabilities**

- **Event Analysis**: Intelligent event interpretation
- **Incident Response**: Structured incident handling guidance
- **System Optimization**: Performance improvement recommendations
- **SRE Best Practices**: Expert advice and recommendations

## 🚀 **Prompt Design Requirements**

### **What We Need**

1. **SRE-Specific Prompts**: Focused on Site Reliability Engineering
2. **Event Analysis Prompts**: For interpreting SRE events and incidents
3. **Incident Response Prompts**: For handling P1/P2 critical events
4. **System Health Prompts**: For monitoring and optimization
5. **Integration Prompts**: For JIRA, Slack, Datadog, JAMS operations

### **Context Considerations**

- **Real Production Data**: Working with actual SRE events
- **Priority-Based Responses**: Different approaches for P1 vs P3 events
- **Multi-Source Integration**: JIRA, Datadog, JAMS, Slack coordination
- **Actionable Output**: Prompts should generate executable recommendations

### **Technical Constraints**

- **Model**: OpenAI GPT-3.5-turbo
- **Response Format**: JSON-compatible for API integration
- **Context Length**: Consider token limits for event data
- **Real-time**: Prompts should work with live SRE data

## 📝 **Sample Use Cases**

### **Event Analysis**

- "Analyze this P1 critical event and provide immediate action steps"
- "Explain the impact of this Datadog alert on system performance"
- "Prioritize these 60 SRE events by business impact"

### **Incident Response**


- "Create a runbook for this JIRA incident"
- "Generate Slack notifications for this P2 event"
- "Assess the correlation between these JAMS job failures"

### **System Optimization**


- "Identify patterns in these SRE events for system improvements"
- "Suggest monitoring enhancements based on event frequency"
- "Recommend preventive measures for recurring issues"

## 🎯 **Success Criteria for New Prompts**


1. **SRE-Focused**: Relevant to Site Reliability Engineering
2. **Actionable**: Generate specific, executable recommendations
3. **Context-Aware**: Utilize the real SRE event data effectively
4. **Priority-Sensitive**: Different approaches for different priority levels
5. **Integration-Ready**: Work with existing JIRA/Slack/Datadog/JAMS tools
6. **Scalable**: Handle varying amounts of event data efficiently

---

**Note**: This system is currently fully functional with real production SRE data. All buttons work correctly, and the LLM integration is operational. The focus should be on creating prompts that leverage this existing infrastructure for enhanced SRE operations.
