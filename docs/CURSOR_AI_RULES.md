# 🤖 Cursor AI Rules & Configuration

## Overview

NestWatch uses Cursor AI with specific rules to ensure consistent, high-quality development that follows the "no bs" philosophy.

## 📁 Rule Files

### `.cursor/rules/core.mdc`
**Purpose**: Core development guidelines for NestWatch SRE platform

```markdown
---
description: NestWatch SRE Platform - focused development rules
globs: ["**/*"]
alwaysApply: true
---
- Focus on Python/TypeScript for this enterprise SRE monitoring platform
- Maintain existing multi-provider AI architecture patterns
- Support corporate environments (Zscaler, proxy handling)
- Handle real-time event processing and fallback systems
- Never log/print secrets, API keys, or sensitive data
- Use environment variables for configuration
- Follow existing project structure and naming conventions
- Prefer functions over classes for simple utilities
- Use existing dependencies before adding new ones
- Handle real-time event streaming with proper connection management
- Follow existing error handling patterns (circuit breakers, rate limiting)
```

### `.cursor/rules/anti-patterns.mdc`
**Purpose**: Catch dangerous patterns in SRE platform

```markdown
---
description: Catch dangerous patterns in SRE platform
globs: ["**/*"]
alwaysApply: true
---
- Broad/bare except blocks without proper error handling
- Network calls without timeouts/retries (use existing rate limiting)
- Global mutable state; mutable default arguments
- Logging secrets/tokens/API keys; dumping full request/response bodies
- Silent fallbacks that mask real outages (log fallback usage)
- Ignoring circuit breaker/rate limit signals
- Adding new external endpoints without proper error handling
- Hardcoded URLs (use environment variables)
- Bypassing corporate proxy settings in production
- Unbounded loops or memory buffers
- Missing error handling in AI provider calls
- Not handling provider failures gracefully
- WebSocket connections without reconnection logic
- Event stream failures without fallback to cached data
```

### `.cursor/rules/no-bs-mode.mdc`
**Purpose**: Enforce "no bs" philosophy

```markdown
---
description: No bs, no theater, real data only
globs: ["**/*"]
alwaysApply: true
---
- Be terse and literal. Implement the spec only.
- Do not invent libraries, files, APIs, endpoints, or data—say "unknown" instead.
- If scope is ambiguous, ask ≤3 targeted questions; otherwise produce a minimal diff and list assumptions.
- Prefer stdlib > deps; use only approved stack.
- Never print/log secrets.
- Before finalizing, self-check: syntax ok, timeouts/retries for IO, tests/smoke present, no forbidden ops.
- Always include a REVIEW BUNDLE.
- No fake data, mock responses, or placeholder content
- No non-functional endpoints or APIs
- No unnecessary complexity or "theater" features
- No features not explicitly requested
- No fake/mock data when real data is available
- No placeholder files or dummy implementations
- No features that don't solve the actual problem
- If it doesn't work, give a clear error message
- No silent failures or hidden errors
- No fake success messages
- No pretending something works when it doesn't
```

## 🎯 Rule Philosophy

### Core Principles
1. **Real Data Only** - No fake data, mock responses, or placeholder content
2. **Honest Error Reporting** - Clear, specific error messages with actionable guidance
3. **No Silent Failures** - All errors are properly logged and displayed
4. **Professional Error States** - Comprehensive error handling with retry mechanisms
5. **Transparent System Status** - Real-time, honest system health reporting

### Development Guidelines
1. **Focus on SRE Platform** - Enterprise-grade monitoring and incident response
2. **Maintain Architecture Patterns** - Multi-provider AI, corporate compatibility
3. **Handle Real-time Events** - Proper connection management and fallback systems
4. **Follow Security Practices** - Never log secrets, use environment variables
5. **Implement Proper Error Handling** - Circuit breakers, rate limiting, retry logic

## 🔧 Rule Implementation

### Error Handling Rules
```typescript
// ✅ CORRECT - Real error handling
if (error) {
  return <APIErrorState error={error} service="SRE API" onRetry={retry} />;
}

// ❌ WRONG - Fake data fallback
if (error) {
  return <div>{fakeEvent1, fakeEvent2, fakeEvent3}</div>;
}
```

### Data Handling Rules
```python
# ✅ CORRECT - Real data only
try:
    events = fetch_sre_events()
    return {"result": events}
except Exception as e:
    raise HTTPException(status_code=503, detail="SRE API unavailable")

# ❌ WRONG - Mock data fallback
try:
    events = fetch_sre_events()
except Exception:
    return {"result": [mock_event1, mock_event2]}
```

### Error Message Rules
```typescript
// ✅ CORRECT - Specific error messages
content: `❌ **SRE AI Service Error**: ${error.message}
**Diagnostic Info**:
• AI Provider: ${aiAvailable ? 'Available' : 'Unavailable'}
• Events Loaded: ${events.length}
• Backend Status: Check if SRE API is running`

// ❌ WRONG - Generic error messages
content: 'Sorry, there was an error processing your request.'
```

## 🧪 Testing Rules

### Automated Testing
```bash
# Test error scenarios
./scripts/test-error-scenarios.sh

# Comprehensive error testing
./scripts/test-comprehensive-errors.sh
```

### Manual Testing Checklist
- [ ] **No fake data** in any response
- [ ] **Specific error messages** with actionable guidance
- [ ] **Proper error states** for all failure scenarios
- [ ] **Real data only** in all API responses
- [ ] **Honest status reporting** throughout

## 📊 Rule Compliance

### Code Review Checklist
- [ ] **Follows core.mdc rules** for SRE platform development
- [ ] **Avoids anti-patterns.mdc** dangerous patterns
- [ ] **Implements no-bs-mode.mdc** "no bs" philosophy
- [ ] **No fake data** in any response
- [ ] **Specific error messages** with diagnostic information
- [ ] **Proper error states** for all failure scenarios
- [ ] **Real data only** in all API responses
- [ ] **Comprehensive testing** of all error scenarios

### Quality Assurance
- [ ] **Error scenarios tested** and working
- [ ] **No fake data detected** in any response
- [ ] **Error states functional** with retry mechanisms
- [ ] **Real data verified** in all successful responses
- [ ] **Performance acceptable** for all error states

## 🚀 Benefits

### For Development
- **Consistent code quality** across the platform
- **Clear error handling** patterns to follow
- **Professional error states** that users can trust
- **Transparent system** that's easy to debug

### For SRE Teams
- **Complete trust** in system accuracy
- **Real-time visibility** into system health
- **Actionable error information** for troubleshooting
- **No misleading data** that could cause wrong decisions

### For System Reliability
- **Honest error reporting** helps identify real issues
- **No fake data** prevents false confidence
- **Real metrics** enable accurate capacity planning
- **Transparent status** improves system monitoring

## 🔍 Rule Verification

### Automated Checks
```bash
# Verify no fake data
grep -r "fallback\|mock\|fake\|dummy" src/ || echo "✅ No fake data found"

# Test error scenarios
./scripts/test-comprehensive-errors.sh

# Verify error handling
./scripts/test-error-scenarios.sh
```

### Manual Verification
1. **Check all error states** show specific, actionable messages
2. **Verify empty states** when no real data is available
3. **Test retry mechanisms** work properly
4. **Confirm no fake data** is ever served
5. **Validate diagnostic information** is accurate

## 📋 Summary

The Cursor AI rules ensure that NestWatch maintains the highest standards of:
- **Real data only** - No fake, mock, or placeholder content
- **Honest error reporting** - Specific, actionable error messages
- **Professional error handling** - Comprehensive error states with retry mechanisms
- **Transparent system status** - Real-time, honest system health reporting
- **Enterprise-grade quality** - Consistent, reliable, and trustworthy system

This approach ensures that SRE teams can trust the system completely and make informed decisions based on real, accurate data without any misleading information.
