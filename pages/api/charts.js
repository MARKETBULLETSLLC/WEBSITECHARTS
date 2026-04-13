/**
 * API Route: /api/charts
 * Returns chart metadata and URLs from Google Sheets
 * Used by: Dashboard, website chart galleries, embedding
 */
const { getCharts } = require('../../lib/google-sheets');

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=60, stale-while-revalidate=120');
    
    const charts = await getCharts();
    
    // Group by category
    const grouped = {};
    charts.forEach((chart) => {
      if (!grouped[chart.category]) {
        grouped[chart.category] = [];
      }
      grouped[chart.category].push(chart);
    });
    
    return res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      count: charts.length,
      data: grouped,
    });
  } catch (error) {
    console.error('Charts fetch error:', error);
    return res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
}
