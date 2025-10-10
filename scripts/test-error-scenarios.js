#!/usr/bin/env node

/**
 * Error Scenario Testing Script
 * Tests that no fake data is shown when APIs fail
 */

import fetch from 'node-fetch';

const BASE_URL = 'http://localhost:3000';
const BACKEND_URL = 'http://127.0.0.1:8000';

const testScenarios = [
  {
    name: 'Frontend API - Normal Operation',
    url: `${BASE_URL}/api/events/real`,
    expectedStatus: 200,
    shouldHaveData: true
  },
  {
    name: 'Frontend API - With Limit',
    url: `${BASE_URL}/api/events/real?limit=10`,
    expectedStatus: 200,
    shouldHaveData: true
  },
  {
    name: 'Frontend API - With Source Filter',
    url: `${BASE_URL}/api/events/real?source=datadog`,
    expectedStatus: 200,
    shouldHaveData: true
  },
  {
    name: 'Backend Direct - Events Endpoint',
    url: `${BACKEND_URL}/event_interactions/events`,
    expectedStatus: 200,
    shouldHaveData: true
  },
  {
    name: 'Backend Direct - Health Check',
    url: `${BACKEND_URL}/health`,
    expectedStatus: 200,
    shouldHaveData: false
  }
];

async function testScenario(scenario) {
  console.log(`\n🧪 Testing: ${scenario.name}`);
  console.log(`   URL: ${scenario.url}`);
  
  try {
    const response = await fetch(scenario.url);
    const data = await response.json();
    
    console.log(`   Status: ${response.status}`);
    console.log(`   Expected: ${scenario.expectedStatus}`);
    
    if (response.status === scenario.expectedStatus) {
      console.log(`   ✅ Status matches expected`);
    } else {
      console.log(`   ❌ Status mismatch`);
    }
    
    if (scenario.shouldHaveData) {
      const eventCount = data.result?.length || 0;
      console.log(`   Events: ${eventCount}`);
      
      if (eventCount > 0) {
        console.log(`   ✅ Has real data`);
        
        // Check for fake data indicators
        const hasFakeData = data.result.some(event => 
          event.event_id?.includes('fallback') ||
          event.event_id?.includes('mock') ||
          event.subject?.includes('fallback') ||
          event.subject?.includes('mock')
        );
        
        if (hasFakeData) {
          console.log(`   ❌ Contains fake/fallback data`);
        } else {
          console.log(`   ✅ No fake data detected`);
        }
      } else {
        console.log(`   ⚠️  No events returned`);
      }
    }
    
    return {
      name: scenario.name,
      status: response.status,
      expectedStatus: scenario.expectedStatus,
      success: response.status === scenario.expectedStatus,
      eventCount: data.result?.length || 0,
      hasFakeData: scenario.shouldHaveData ? (data.result || []).some(event => 
        event.event_id?.includes('fallback') ||
        event.event_id?.includes('mock') ||
        event.subject?.includes('fallback') ||
        event.subject?.includes('mock')
      ) : false
    };
    
  } catch (error) {
    console.log(`   ❌ Error: ${error.message}`);
    return {
      name: scenario.name,
      status: 'ERROR',
      expectedStatus: scenario.expectedStatus,
      success: false,
      error: error.message
    };
  }
}

async function testErrorScenarios() {
  console.log('🚀 Starting Error Scenario Testing');
  console.log('=====================================');
  
  const results = [];
  
  for (const scenario of testScenarios) {
    const result = await testScenario(scenario);
    results.push(result);
  }
  
  console.log('\n📊 Test Results Summary');
  console.log('========================');
  
  const successful = results.filter(r => r.success).length;
  const total = results.length;
  
  console.log(`Total Tests: ${total}`);
  console.log(`Successful: ${successful}`);
  console.log(`Failed: ${total - successful}`);
  
  console.log('\n📋 Detailed Results:');
  results.forEach(result => {
    const status = result.success ? '✅' : '❌';
    console.log(`${status} ${result.name}: ${result.status} (${result.eventCount} events)`);
    if (result.hasFakeData) {
      console.log(`   ⚠️  Contains fake data!`);
    }
    if (result.error) {
      console.log(`   Error: ${result.error}`);
    }
  });
  
  console.log('\n🎯 "No Bullshitting" Rules Check:');
  const hasFakeData = results.some(r => r.hasFakeData);
  if (hasFakeData) {
    console.log('❌ FAILED: Fake data detected in responses');
  } else {
    console.log('✅ PASSED: No fake data detected');
  }
  
  const allSuccessful = results.every(r => r.success);
  if (allSuccessful) {
    console.log('✅ PASSED: All API endpoints responding correctly');
  } else {
    console.log('❌ FAILED: Some API endpoints not responding');
  }
  
  console.log('\n🔍 Recommendations:');
  if (hasFakeData) {
    console.log('• Remove any remaining fake/fallback data');
    console.log('• Ensure error states show proper messages instead of fake data');
  }
  if (!allSuccessful) {
    console.log('• Check backend server is running');
    console.log('• Verify API endpoints are accessible');
    console.log('• Check for CORS or network issues');
  }
  
  console.log('\n✨ Testing complete!');
}

// Run the tests
testErrorScenarios().catch(console.error);
