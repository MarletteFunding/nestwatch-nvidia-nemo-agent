#!/bin/bash

# Error Scenario Testing Script
# Tests that no fake data is shown when APIs fail

echo "🚀 Starting Error Scenario Testing"
echo "====================================="

BASE_URL="http://localhost:3000"
BACKEND_URL="http://127.0.0.1:8000"

# Test 1: Frontend API - Normal Operation
echo ""
echo "🧪 Testing: Frontend API - Normal Operation"
echo "   URL: $BASE_URL/api/events/real"

response=$(curl -s -w "%{http_code}" -o /tmp/frontend_response.json "$BASE_URL/api/events/real")
status_code="${response: -3}"

echo "   Status: $status_code"

if [ "$status_code" = "200" ]; then
    echo "   ✅ Status OK"
    
    # Check for fake data
    if grep -q "fallback\|mock" /tmp/frontend_response.json; then
        echo "   ❌ Contains fake/fallback data"
    else
        echo "   ✅ No fake data detected"
    fi
    
    # Count events
    event_count=$(jq '.result | length' /tmp/frontend_response.json 2>/dev/null || echo "0")
    echo "   Events: $event_count"
else
    echo "   ❌ Status error"
fi

# Test 2: Frontend API - With Limit
echo ""
echo "🧪 Testing: Frontend API - With Limit"
echo "   URL: $BASE_URL/api/events/real?limit=10"

response=$(curl -s -w "%{http_code}" -o /tmp/frontend_limit_response.json "$BASE_URL/api/events/real?limit=10")
status_code="${response: -3}"

echo "   Status: $status_code"

if [ "$status_code" = "200" ]; then
    echo "   ✅ Status OK"
    
    # Check for fake data
    if grep -q "fallback\|mock" /tmp/frontend_limit_response.json; then
        echo "   ❌ Contains fake/fallback data"
    else
        echo "   ✅ No fake data detected"
    fi
    
    # Count events
    event_count=$(jq '.result | length' /tmp/frontend_limit_response.json 2>/dev/null || echo "0")
    echo "   Events: $event_count"
else
    echo "   ❌ Status error"
fi

# Test 3: Backend Direct - Events Endpoint
echo ""
echo "🧪 Testing: Backend Direct - Events Endpoint"
echo "   URL: $BACKEND_URL/event_interactions/events"

response=$(curl -s -w "%{http_code}" -o /tmp/backend_response.json "$BACKEND_URL/event_interactions/events")
status_code="${response: -3}"

echo "   Status: $status_code"

if [ "$status_code" = "200" ]; then
    echo "   ✅ Status OK"
    
    # Check for fake data
    if grep -q "fallback\|mock" /tmp/backend_response.json; then
        echo "   ❌ Contains fake/fallback data"
    else
        echo "   ✅ No fake data detected"
    fi
    
    # Count events
    event_count=$(jq '.result | length' /tmp/backend_response.json 2>/dev/null || echo "0")
    echo "   Events: $event_count"
else
    echo "   ❌ Status error"
fi

# Test 4: Backend Health Check
echo ""
echo "🧪 Testing: Backend Health Check"
echo "   URL: $BACKEND_URL/api/v1/health"

response=$(curl -s -w "%{http_code}" -o /tmp/backend_health.json "$BACKEND_URL/api/v1/health")
status_code="${response: -3}"

echo "   Status: $status_code"

if [ "$status_code" = "200" ]; then
    echo "   ✅ Status OK"
else
    echo "   ❌ Status error"
fi

# Test 5: Test Error Scenarios
echo ""
echo "🧪 Testing: Error Scenarios"
echo "   Testing non-existent endpoint"

response=$(curl -s -w "%{http_code}" -o /tmp/error_response.json "$BASE_URL/api/events/nonexistent")
status_code="${response: -3}"

echo "   Status: $status_code"

if [ "$status_code" = "404" ]; then
    echo "   ✅ Proper 404 error"
else
    echo "   ⚠️  Unexpected status: $status_code"
fi

echo ""
echo "📊 Test Results Summary"
echo "========================"

# Count successful tests
success_count=0
total_tests=5

# Check each test result
if curl -s "$BASE_URL/api/events/real" | jq '.result | length' >/dev/null 2>&1; then
    success_count=$((success_count + 1))
fi

if curl -s "$BASE_URL/api/events/real?limit=10" | jq '.result | length' >/dev/null 2>&1; then
    success_count=$((success_count + 1))
fi

if curl -s "$BACKEND_URL/event_interactions/events" | jq '.result | length' >/dev/null 2>&1; then
    success_count=$((success_count + 1))
fi

if curl -s "$BACKEND_URL/api/v1/health" | jq '.status' >/dev/null 2>&1; then
    success_count=$((success_count + 1))
fi

if curl -s "$BASE_URL/api/events/nonexistent" | grep -q "404"; then
    success_count=$((success_count + 1))
fi

echo "Total Tests: $total_tests"
echo "Successful: $success_count"
echo "Failed: $((total_tests - success_count))"

echo ""
echo "🎯 'No Bullshitting' Rules Check:"

# Check for fake data in all responses
has_fake_data=false
for file in /tmp/frontend_response.json /tmp/frontend_limit_response.json /tmp/backend_response.json; do
    if [ -f "$file" ] && grep -q "fallback\|mock" "$file"; then
        has_fake_data=true
        break
    fi
done

if [ "$has_fake_data" = true ]; then
    echo "❌ FAILED: Fake data detected in responses"
else
    echo "✅ PASSED: No fake data detected"
fi

echo ""
echo "🔍 Recommendations:"
if [ "$has_fake_data" = true ]; then
    echo "• Remove any remaining fake/fallback data"
    echo "• Ensure error states show proper messages instead of fake data"
fi

echo ""
echo "✨ Testing complete!"

# Cleanup
rm -f /tmp/*_response.json /tmp/*_health.json
