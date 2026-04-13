/**
 * API Route: /api/bor-status
 * Returns current Box-o-Rox market phase (LOADED, LOCKED & LOADED, AIM, FIRE)
 * Used by: Dashboard status display, email alerts, market stance indicator
 */
const { getBoRStatus } = require('../../lib/google-sheets');

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=60, stale-while-revalidate=120');
    
    const status = await getBoRStatus();
    
    return res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      phase: status.phase,
      color: status.color,
      description: status.description,
    });
  } catch (error) {
    console.error('BoR status fetch error:', error);
    return res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
}
