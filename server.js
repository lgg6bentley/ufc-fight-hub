const express = require('express');
const path = require('path');
const { Pool } = require('pg');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();  // ✅ Ensure `app` is defined first!

// ✅ Middleware setup
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ✅ Serve `prediction.html` directly from Express
app.get('/prediction', (req, res) => {
    res.sendFile(path.resolve(__dirname, 'public', 'prediction.html'));
});

// ✅ Proxy setup for Flask (port 5000)
app.use('/predict', createProxyMiddleware({
    target: 'http://127.0.0.1:5000',
    changeOrigin: true,
    pathRewrite: { '^/predict': '/' }
}));

// ✅ Database connection
const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'ufc_fight_hub',
    password: 'tsubasa',
    port: 5432
});

// ✅ Define API routes
app.get('/fighters', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM fighters');
        res.json(result.rows);
    } catch (error) {
        console.error('Error fetching fighters:', error.message);
        res.status(500).json({ error: 'Database query failed' });
    }
});

// ✅ Start the server AFTER everything is set up
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🤖 Server running on http://localhost:${PORT}`));