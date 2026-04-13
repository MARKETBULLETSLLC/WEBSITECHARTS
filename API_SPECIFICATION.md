# Phase 1 API Specification

**Version:** 1.0.0  
**Status:** Ready for deployment  
**Base URL:** `https://your-vercel-url` (after deployment)  
**Local:** `http://localhost:3000` (development)  

---

## API Contract - 4 Endpoints

All endpoints:
- Accept only `GET` requests
- Return JSON
- Include `timestamp` in every response
- Have cache headers configured
- Return 500 + error message on failure

---

## Endpoint 1: Health Check

### Request
```
GET /api/health
```

### Response (200 OK)
```json
{
  "status": "healthy",
  "timestamp": "2026-04-15T12:34:56.789Z",
  "service": "MarketBullets API Phase 1",
  "version": "1.0.0",
  "uptime": 45.234,
  "memory": {
    "used": 125,
    "total": 512
  }
}
```

### Cache Headers
```
Cache-Control: public, max-age=60, s-maxage=60
```

### Purpose
- Server status monitoring
- Uptime verification
- Memory usage tracking
- Deployment health check

### Example Usage
```bash
curl http://localhost:3000/api/health
```

---

## Endpoint 2: Charts

### Request
```
GET /api/charts
```

### Response (200 OK)
```json
{
  "success": true,
  "timestamp": "2026-04-15T12:34:56.789Z",
  "count": 55,
  "data": {
    "Wheat Futures": [
      {
        "id": "WHEAT_SRW_D",
        "name": "SRW Wheat Daily",
        "category": "Wheat Futures",
        "url": "https://tradingnavigator.com/WHEAT_SRW_D.png",
        "lastUpdated": "2026-04-15T08:30:00Z",
        "description": "CBOT Soft Red Winter daily chart"
      }
    ],
    "Spreads & Ratios": [...],
    "Currencies": [...],
    "Interest Rates": [...],
    "General Macro": [...]
  }
}
```

### Cache Headers
```
Cache-Control: public, max-age=60, s-maxage=60, stale-while-revalidate=120
```

### Data Source
Google Sheets: `Charts` sheet (columns: id, name, category, url, lastUpdated, description)

### Purpose
- Display 55+ charts on dashboard
- Group charts by category
- Provide URLs for embedded images
- Track last update time

### Example Usage
```bash
curl http://localhost:3000/api/charts | jq '.data | keys'
# Output: ["Wheat Futures", "Spreads & Ratios", "Currencies", "Interest Rates", "General Macro"]
```

---

## Endpoint 3: Quotes

### Request
```
GET /api/quotes
```

### Response (200 OK)
```json
{
  "success": true,
  "timestamp": "2026-04-15T12:34:56.789Z",
  "count": 8,
  "summary": {
    "totalVolume": 1245000,
    "maxChange": 3.5,
    "minPrice": 520.25,
    "maxPrice": 580.75
  },
  "data": [
    {
      "contract": "ZWK25",
      "month": "May 2025",
      "bid": 545.25,
      "ask": 545.75,
      "last": 545.50,
      "change": 2.25,
      "volume": 124500,
      "timestamp": "2026-04-15T08:30:00Z"
    },
    {
      "contract": "ZWU25",
      "month": "Jul 2025",
      "bid": 548.75,
      "ask": 549.25,
      "last": 549.00,
      "change": 2.50,
      "volume": 98200,
      "timestamp": "2026-04-15T08:30:00Z"
    }
  ]
}
```

### Cache Headers
```
Cache-Control: public, max-age=30, s-maxage=30, stale-while-revalidate=60
```

### Data Source
Google Sheets: `Quotes` sheet (columns: contract, month, bid, ask, last, change, volume, timestamp)

### Purpose
- Display live futures quotes
- Show market summary stats
- Enable real-time pricing widgets
- Track daily changes

### Summary Calculations
- `totalVolume` = sum of all volume values
- `maxChange` = largest absolute price change
- `minPrice` = lowest bid/ask/last price
- `maxPrice` = highest bid/ask/last price

### Example Usage
```bash
curl http://localhost:3000/api/quotes | jq '.summary'
# Output: { "totalVolume": 1245000, "maxChange": 3.5, "minPrice": 520.25, "maxPrice": 580.75 }
```

---

## Endpoint 4: Box-o-Rox Status

### Request
```
GET /api/bor-status
```

### Response (200 OK)
```json
{
  "success": true,
  "timestamp": "2026-04-15T12:34:56.789Z",
  "phase": "LOADED",
  "color": "#FFD700",
  "description": "Accumulation phase"
}
```

### Phase Values & Colors
| Phase | Color | Hex | Meaning |
|-------|-------|-----|---------|
| LOADED | Gold | #FFD700 | Accumulation phase - market building |
| LOCKED & LOADED | Red | #FF6B6B | Setup complete - ready for signal |
| AIM | Cyan | #4ECDC4 | Signal confirmed - locking in |
| FIRE | Red | #FF0000 | Execution - act now |

### Cache Headlines
```
Cache-Control: public, max-age=60, s-maxage=60, stale-while-revalidate=120
```

### Data Source
Google Sheets: `BoR_Status` sheet (columns: phase, description, color)

### Purpose
- Display market stance indicator
- Signal marketing stance (LOADED = accumulate, FIRE = execute)
- Email alert trigger system (Phase 3)
- Dashboard status badge

### Example Usage
```bash
curl http://localhost:3000/api/bor-status | jq '.phase'
# Output: "LOADED"
```

---

## Error Handling

### Invalid Method
```
POST /api/health
```

Response (405 Method Not Allowed):
```json
{
  "error": "Method not allowed"
}
```

### Server Error
Response (500 Internal Server Error):
```json
{
  "success": false,
  "error": "Error message describing what went wrong",
  "timestamp": "2026-04-15T12:34:56.789Z"
}
```

### Fallback Behavior
If Google Sheets API fails:
1. Endpoint logs error to Vercel console
2. Returns mock data (not an error)
3. Client still gets valid response
4. Ensures availability even if Google Sheets is temporarily down

---

## Testing Your Deployment

### Verify All Endpoints
```bash
# Save this as verify.sh and run after deployment
BASE_URL="https://your-vercel-url"

echo "Testing Phase 1 API endpoints..."
echo "Base URL: $BASE_URL"
echo ""

echo "1. Health endpoint:"
curl -s $BASE_URL/api/health | jq '.'

echo ""
echo "2. Charts endpoint:"
curl -s $BASE_URL/api/charts | jq '.count, .data | keys'

echo ""
echo "3. Quotes endpoint:"
curl -s $BASE_URL/api/quotes | jq '.summary'

echo ""
echo "4. BoR Status endpoint:"
curl -s $BASE_URL/api/bor-status | jq '.phase, .color'
```

### Quick Health Check
```bash
curl https://your-vercel-url/api/health | jq '.status'
# Should output: "healthy"
```

### Test Response Times
```bash
time curl -s https://your-vercel-url/api/health > /dev/null
# Should be < 500ms
```

---

## Rate Limiting

**No explicit rate limiting** on these endpoints, but:
- Google Sheets API: 1,000 reads/min per project
- Cache strategy prevents excessive API calls
- At max throughput: 4 endpoints × 60s cache = ~1 read/min per user
- 100 concurrent users = ~100 reads/min (well under limit)

---

## Authentication

**No authentication required** for Phase 1.

- All endpoints are public
- No API keys needed
- CORS enabled (wildcard * for MVP)
- Phase 2 will add member authentication

---

## Request/Response Examples

### Using curl
```bash
# Test health
curl -i http://localhost:3000/api/health

# Test charts with formatting
curl -s http://localhost:3000/api/charts | jq '.'

# Test quotes and get only summary
curl -s http://localhost:3000/api/quotes | jq '.summary'

# Test BoR with verbose output
curl -v http://localhost:3000/api/bor-status
```

### Using JavaScript/Fetch
```javascript
// Fetch all 4 endpoints in parallel
const baseUrl = 'http://localhost:3000';

Promise.all([
  fetch(`${baseUrl}/api/health`).then(r => r.json()),
  fetch(`${baseUrl}/api/charts`).then(r => r.json()),
  fetch(`${baseUrl}/api/quotes`).then(r => r.json()),
  fetch(`${baseUrl}/api/bor-status`).then(r => r.json()),
]).then(([health, charts, quotes, bor]) => {
  console.log('Health:', health.status);
  console.log('Charts:', charts.count);
  console.log('Quotes:', quotes.summary);
  console.log('BoR:', bor.phase);
});
```

### Using Python
```python
import requests
import json

base_url = 'http://localhost:3000'

endpoints = {
  'health': '/api/health',
  'charts': '/api/charts',
  'quotes': '/api/quotes',
  'bor': '/api/bor-status',
}

for name, path in endpoints.items():
  response = requests.get(f"{base_url}{path}")
  print(f"{name}: {response.status_code}")
  print(json.dumps(response.json(), indent=2))
```

---

## Cache Strategy

### Why These Cache Durations?

| Endpoint | Max-Age | Rationale |
|----------|---------|-----------|
| Health | 60s | Frequent monitoring, non-critical |
| Charts | 60s | Changes only when Gary exports new charts |
| Quotes | 30s | Freshest data, updated more frequently |
| BoR | 60s | Changes only when market phase shifts |

### Stale-While-Revalidate
- Charts: 120s — Acceptable 2min stale if backend down
- Quotes: 60s — Acceptable 1min stale if backend down
- BoR: 120s — Acceptable 2min stale if backend down

### Effect on Users
- First request: Live data from Google Sheets
- Subsequent requests within cache window: Cached response (instant)
- After cache expires: Fresh data from Google Sheets

---

## Monitoring & Alerts

**You should monitor:**
- `/api/health` response time (should be < 100ms)
- `/api/health` uptime (should be > 99.9%)
- Error rates (should be < 0.1%)
- Google Sheets connectivity (test in Vercel dashboard logs)

---

## Future Endpoints (Phase 2+)

Not part of Phase 1, but planned:
- `GET /api/alerts` — Email alert subscriptions
- `GET /api/user/[id]` — Member data (requires authentication)
- `POST /api/quotes` — Historical quote data (Phase 4: Barchart integration)
- `GET /api/sentiment` — Market sentiment (Phase 3)

---

## Support

**For deployment issues:** See README_PHASE1.md Part 5 (Deployment & Troubleshooting)  
**For data questions:** See EXECUTION_BRIEF.md (Gary's data entry guide)  
**For testing:** Run `node test-api.js <base-url>`  

---

**Version 1.0.0 - Production Ready for April 26, 2026 Deployment**
