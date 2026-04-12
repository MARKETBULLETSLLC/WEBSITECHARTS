/**
 * API Route: /api/quotes
 * Returns futures contract quotes and market data
 * Used by: Dashboard real-time quotes, widgets, pricing displays
 */
const { getQuotes } = require('../../lib/google-sheets');

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    res.setHeader('Cache-Control', 'public, max-age=30, s-maxage=30, stale-while-revalidate=60');
    
    const quotes = await getQuotes();
    
    // Calculate market summary
    const summary = {
      totalVolume: quotes.reduce((sum, q) => sum + (q.volume || 0), 0),
      maxChange: Math.max(...quotes.map(q => Math.abs(q.change || 0))),
      minPrice: Math.min(...quotes.map(q => q.last || 0)),
      maxPrice: Math.max(...quotes.map(q => q.last || 0)),
    };
    
    return res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      count: quotes.length,
      summary,
      data: quotes,
    });
  } catch (error) {
    console.error('Quotes fetch error:', error);
    return res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
}
