/**
 * API Route: /api/health
 * Returns server status and basic health metrics
 * Used for: Monitoring, uptime checks, deployment verification
 */
export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=60');
    
    return res.status(200).json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'MarketBullets API Phase 1',
      version: '1.0.0',
      uptime: process.uptime(),
      memory: {
        used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
        total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
      },
    });
  } catch (error) {
    console.error('Health check error:', error);
    return res.status(500).json({
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
}
