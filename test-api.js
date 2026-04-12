#!/usr/bin/env node

/**
 * Phase 1 API Integration Test Suite
 * 
 * Gabe: Run this after API is deployed to verify all endpoints respond correctly
 * 
 * Usage:
 *   node test-api.js http://localhost:3000
 *   node test-api.js https://your-vercel-url
 */

const BASE_URL = process.argv[2] || 'http://localhost:3000';

async function testEndpoint(name, path, expectedFields) {
  const url = `${BASE_URL}${path}`;
  
  try {
    const response = await fetch(url);
    const data = await response.json();
    
    // Check HTTP status
    if (!response.ok) {
      console.log(`  ❌ FAIL: ${name} returned ${response.status}`);
      return false;
    }
    
    // Check required fields
    const hasAllFields = expectedFields.every(field => field in data);
    if (!hasAllFields) {
      console.log(`  ❌ FAIL: ${name} missing fields. Got: ${Object.keys(data).join(', ')}`);
      return false;
    }
    
    console.log(`  ✅ PASS: ${name}`);
    console.log(`     Response time: ${response.headers.get('date')}`);
    console.log(`     Cache: ${response.headers.get('cache-control')}`);
    return true;
    
  } catch (error) {
    console.log(`  ❌ ERROR: ${name} - ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log(`\n=== MarketBullets Phase 1 API Verification ===\n`);
  console.log(`Testing against: ${BASE_URL}\n`);
  
  const tests = [
    {
      name: 'Health Endpoint',
      path: '/api/health',
      fields: ['status', 'timestamp', 'service', 'version', 'uptime', 'memory']
    },
    {
      name: 'Charts Endpoint',
      path: '/api/charts',
      fields: ['success', 'timestamp', 'count', 'data']
    },
    {
      name: 'Quotes Endpoint',
      path: '/api/quotes',
      fields: ['success', 'timestamp', 'count', 'summary', 'data']
    },
    {
      name: 'BoR Status Endpoint',
      path: '/api/bor-status',
      fields: ['success', 'timestamp', 'phase', 'color', 'description']
    }
  ];
  
  let passed = 0;
  let failed = 0;
  
  for (const test of tests) {
    const result = await testEndpoint(test.name, test.path, test.fields);
    if (result) passed++;
    else failed++;
  }
  
  console.log(`\n=== Results ===`);
  console.log(`Passed: ${passed}/${tests.length}`);
  console.log(`Failed: ${failed}/${tests.length}`);
  
  if (failed === 0) {
    console.log(`\n✅ All tests passed! Phase 1 API is working correctly.\n`);
    process.exit(0);
  } else {
    console.log(`\n❌ Some tests failed. Check the errors above.\n`);
    process.exit(1);
  }
}

runTests();
