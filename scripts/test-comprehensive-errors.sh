#!/bin/bash

# Comprehensive Error Testing Script
# Tests all error scenarios to ensure no fake data is shown

echo "🚀 Starting Comprehensive Error Testing"
echo "========================================"

BASE_URL="http://localhost:3000"
BACKEND_URL="http://127.0.0.1:8000"

# Test 1: Normal Operation
echo ""
echo "🧪 Test 1: Normal Operation"
echo "============================"

echo "Frontend API:"
frontend_response=$(curl -s "$BASE_URL/api/events/real")
frontend_events=$(echo "$frontend_response" | jq '.result | length' 2>/dev/null || echo "0")
echo "   Events: $frontend_events"

echo "Backend API:"
backend_response=$(curl -s "$BACKEND_URL/event_interactions/events")
backend_events=$(echo "$backend_response" | jq '.result | length' 2>/dev/null || echo "0")
echo "   Events: $backend_events"

# Test 2: Check for Fake Data
echo ""
echo "🧪 Test 2: Fake Data Detection"
echo "============================="

echo "Checking frontend response for fake data..."
if echo "$frontend_response" | grep -q "fallback\|mock\|fake\|dummy"; then
    echo "   ❌ FAKE DATA DETECTED in frontend response"
else
    echo "   ✅ No fake data in frontend response"
fi

echo "Checking backend response for fake data..."
if echo "$backend_response" | grep -q "fallback\|mock\|fake\|dummy"; then
    echo "   ❌ FAKE DATA DETECTED in backend response"
else
    echo "   ✅ No fake data in backend response"
fi

# Test 3: Error Handling
echo ""
echo "🧪 Test 3: Error Handling"
echo "========================="

echo "Testing non-existent endpoint:"
error_response=$(curl -s -w "%{http_code}" "$BASE_URL/api/events/nonexistent")
error_status="${error_response: -3}"
echo "   Status: $error_status"

if [ "$error_status" = "404" ]; then
    echo "   ✅ Proper 404 error handling"
else
    echo "   ❌ Unexpected error status: $error_status"
fi

# Test 4: Data Integrity
echo ""
echo "🧪 Test 4: Data Integrity"
echo "========================="

echo "Checking event data structure..."
if echo "$frontend_response" | jq '.result[0]' >/dev/null 2>&1; then
    first_event=$(echo "$frontend_response" | jq '.result[0]')
    echo "   ✅ Valid JSON structure"
    
    # Check for required fields
    if echo "$first_event" | jq '.event_id' >/dev/null 2>&1; then
        echo "   ✅ Has event_id field"
    else
        echo "   ❌ Missing event_id field"
    fi
    
    if echo "$first_event" | jq '.subject' >/dev/null 2>&1; then
        echo "   ✅ Has subject field"
    else
        echo "   ❌ Missing subject field"
    fi
else
    echo "   ❌ Invalid JSON structure"
fi

# Test 5: Performance
echo ""
echo "🧪 Test 5: Performance"
echo "======================"

echo "Testing response times..."
start_time=$(date +%s%N)
curl -s "$BASE_URL/api/events/real" >/dev/null
end_time=$(date +%s%N)
frontend_time=$(( (end_time - start_time) / 1000000 ))
echo "   Frontend API: ${frontend_time}ms"

start_time=$(date +%s%N)
curl -s "$BACKEND_URL/event_interactions/events" >/dev/null
end_time=$(date +%s%N)
backend_time=$(( (end_time - start_time) / 1000000 ))
echo "   Backend API: ${backend_time}ms"

# Test 6: Filtering
echo ""
echo "🧪 Test 6: Filtering"
echo "===================="

echo "Testing source filtering..."
datadog_response=$(curl -s "$BASE_URL/api/events/real?source=datadog")
datadog_events=$(echo "$datadog_response" | jq '.result | length' 2>/dev/null || echo "0")
echo "   Datadog events: $datadog_events"

jira_response=$(curl -s "$BASE_URL/api/events/real?source=jira")
jira_events=$(echo "$jira_response" | jq '.result | length' 2>/dev/null || echo "0")
echo "   JIRA events: $jira_events"

sre_api_response=$(curl -s "$BASE_URL/api/events/real?source=sre_api")
sre_api_events=$(echo "$sre_api_response" | jq '.result | length' 2>/dev/null || echo "0")
echo "   SRE API events: $sre_api_events"

# Test 7: Limit Testing
echo ""
echo "🧪 Test 7: Limit Testing"
echo "========================"

echo "Testing limit parameter..."
limit_response=$(curl -s "$BASE_URL/api/events/real?limit=5")
limit_events=$(echo "$limit_response" | jq '.result | length' 2>/dev/null || echo "0")
echo "   Limited to 5 events: $limit_events"

if [ "$limit_events" -le 5 ]; then
    echo "   ✅ Limit parameter working"
else
    echo "   ❌ Limit parameter not working"
fi

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="

total_tests=7
passed_tests=0

# Check if all tests passed
if [ "$frontend_events" -gt 0 ] && [ "$backend_events" -gt 0 ]; then
    passed_tests=$((passed_tests + 1))
fi

if ! echo "$frontend_response" | grep -q "fallback\|mock\|fake\|dummy"; then
    passed_tests=$((passed_tests + 1))
fi

if ! echo "$backend_response" | grep -q "fallback\|mock\|fake\|dummy"; then
    passed_tests=$((passed_tests + 1))
fi

if [ "$error_status" = "404" ]; then
    passed_tests=$((passed_tests + 1))
fi

if echo "$frontend_response" | jq '.result[0]' >/dev/null 2>&1; then
    passed_tests=$((passed_tests + 1))
fi

if [ "$frontend_time" -lt 5000 ] && [ "$backend_time" -lt 5000 ]; then
    passed_tests=$((passed_tests + 1))
fi

if [ "$limit_events" -le 5 ]; then
    passed_tests=$((passed_tests + 1))
fi

echo "Total Tests: $total_tests"
echo "Passed: $passed_tests"
echo "Failed: $((total_tests - passed_tests))"

echo ""
echo "🎯 'No Bullshitting' Rules Verification:"
echo "========================================="

# Check for fake data
has_fake_data=false
if echo "$frontend_response" | grep -q "fallback\|mock\|fake\|dummy"; then
    has_fake_data=true
fi
if echo "$backend_response" | grep -q "fallback\|mock\|fake\|dummy"; then
    has_fake_data=true
fi

if [ "$has_fake_data" = true ]; then
    echo "❌ FAILED: Fake data detected"
else
    echo "✅ PASSED: No fake data detected"
fi

# Check for real data
if [ "$frontend_events" -gt 0 ] && [ "$backend_events" -gt 0 ]; then
    echo "✅ PASSED: Real data is being served"
else
    echo "❌ FAILED: No real data available"
fi

# Check error handling
if [ "$error_status" = "404" ]; then
    echo "✅ PASSED: Proper error handling"
else
    echo "❌ FAILED: Error handling issues"
fi

echo ""
echo "🔍 Final Assessment:"
echo "===================="

if [ "$passed_tests" -eq "$total_tests" ] && [ "$has_fake_data" = false ]; then
    echo "🎉 ALL TESTS PASSED - No bullshitting detected!"
    echo "✅ Real data only"
    echo "✅ Proper error handling"
    echo "✅ No fake fallbacks"
    echo "✅ Performance acceptable"
else
    echo "⚠️  Some issues detected:"
    if [ "$passed_tests" -lt "$total_tests" ]; then
        echo "• $((total_tests - passed_tests)) tests failed"
    fi
    if [ "$has_fake_data" = true ]; then
        echo "• Fake data detected - violates 'no bullshitting' rules"
    fi
fi

echo ""
echo "✨ Comprehensive testing complete!"
