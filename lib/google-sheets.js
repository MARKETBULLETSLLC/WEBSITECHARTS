const { google } = require('googleapis');

// Initialize Google Sheets client with service account
const getAuthClient = () => {
  const auth = new google.auth.GoogleAuth({
    credentials: {
      type: 'service_account',
      project_id: process.env.GOOGLE_SHEETS_PROJECT_ID,
      private_key_id: process.env.GOOGLE_SHEETS_PRIVATE_KEY_ID || 'key-id',
      private_key: process.env.GOOGLE_SHEETS_PRIVATE_KEY?.replace(/\\n/g, '\n'),
      client_email: process.env.GOOGLE_SHEETS_CLIENT_EMAIL,
      client_id: process.env.GOOGLE_SHEETS_CLIENT_ID || '123456',
      auth_uri: 'https://accounts.google.com/o/oauth2/auth',
      token_uri: 'https://oauth2.googleapis.com/token',
    },
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });
  return auth;
};

/**
 * Fetch chart data from Google Sheets
 * @returns {Promise<Array>} Array of chart objects with metadata
 */
async function getCharts() {
  try {
    const auth = getAuthClient();
    const sheets = google.sheets({ version: 'v4', auth });
    
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: process.env.GOOGLE_SHEETS_ID,
      range: 'Charts!A1:Z1000',
    });
    
    const rows = response.data.values || [];
    if (rows.length < 2) return [];
    
    const headers = rows[0];
    const charts = rows.slice(1).map((row) => ({
      id: row[0],
      name: row[1],
      category: row[2],
      url: row[3],
      lastUpdated: row[4],
      description: row[5],
    })).filter(c => c.id && c.name);
    
    return charts;
  } catch (error) {
    console.error('Error fetching charts:', error.message);
    return getMockCharts();
  }
}

/**
 * Fetch futures quote data from Google Sheets
 * @returns {Promise<Array>} Array of quote objects
 */
async function getQuotes() {
  try {
    const auth = getAuthClient();
    const sheets = google.sheets({ version: 'v4', auth });
    
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: process.env.GOOGLE_SHEETS_ID,
      range: 'Quotes!A1:Z100',
    });
    
    const rows = response.data.values || [];
    if (rows.length < 2) return [];
    
    const quotes = rows.slice(1).map((row) => ({
      contract: row[0],
      month: row[1],
      bid: parseFloat(row[2]),
      ask: parseFloat(row[3]),
      last: parseFloat(row[4]),
      change: parseFloat(row[5]),
      volume: parseInt(row[6]),
      timestamp: row[7],
    })).filter(q => q.contract);
    
    return quotes;
  } catch (error) {
    console.error('Error fetching quotes:', error.message);
    return getMockQuotes();
  }
}

/**
 * Fetch Box-o-Rox status from Google Sheets
 * @returns {Promise<Object>} Status object with phase and color
 */
async function getBoRStatus() {
  try {
    const auth = getAuthClient();
    const sheets = google.sheets({ version: 'v4', auth });
    
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: process.env.GOOGLE_SHEETS_ID,
      range: 'BoR_Status!A1:B10',
    });
    
    const rows = response.data.values || [];
    if (rows.length < 2) return getMockBoRStatus();
    
    const phase = rows[1]?.[0] || 'LOADED';
    const statusMap = {
      'LOADED': { phase: 'LOADED', color: '#FFD700', description: 'Accumulation phase' },
      'LOCKED & LOADED': { phase: 'LOCKED & LOADED', color: '#FF6B6B', description: 'Setup complete' },
      'AIM': { phase: 'AIM', color: '#4ECDC4', description: 'Signal confirmation' },
      'FIRE': { phase: 'FIRE', color: '#FF0000', description: 'Execution' },
    };
    
    return statusMap[phase] || statusMap['LOADED'];
  } catch (error) {
    console.error('Error fetching BoR status:', error.message);
    return getMockBoRStatus();
  }
}

// Mock data fallbacks
function getMockCharts() {
  return [
    {
      id: 'SRW_D',
      name: 'SRW Wheat Daily',
      category: 'Wheat Futures',
      url: 'https://via-placeholder.com/WHEAT_SRW_D.png',
      lastUpdated: new Date().toISOString(),
      description: 'CBOT Soft Red Winter Wheat daily chart',
    },
  ];
}

function getMockQuotes() {
  return [
    {
      contract: 'ZWK25',
      month: 'May 2025',
      bid: 545.25,
      ask: 545.75,
      last: 545.50,
      change: 2.25,
      volume: 124500,
      timestamp: new Date().toISOString(),
    },
  ];
}

function getMockBoRStatus() {
  return {
    phase: 'LOADED',
    color: '#FFD700',
    description: 'Accumulation phase',
  };
}

module.exports = {
  getCharts,
  getQuotes,
  getBoRStatus,
};
