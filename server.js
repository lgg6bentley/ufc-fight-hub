// ✅ UFC Fight Hub Backend Server
const express = require('express');
const path = require('path');
const { Pool } = require('pg'); // ✅ PostgreSQL setup
const cors = require('cors'); // ✅ Allow frontend API requests

const app = express();

// ✅ Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ✅ PostgreSQL Connection Setup
const pool = new Pool({
    user: 'postgres',          // Replace with your PostgreSQL username
    host: 'localhost',
    database: 'ufc_fight_hub', // Replace with your database name
    password: 'tsubasa',       // Replace with your password
    port: 5432                 // Default PostgreSQL port
});

// ✅ Fetch Fighters Data from Database
app.get('/fighters', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM fighters');
        res.json(result.rows);
    } catch (error) {
        console.error('Error fetching fighters:', error.message);
        res.status(500).json({ error: 'Database query failed' });
    }
});

// ✅ Fetch Upcoming Fights from Database
app.get('/upcoming-fights', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM upcoming_fights ORDER BY date ASC');
        res.json(result.rows);
    } catch (error) {
        console.error('Error fetching upcoming fights:', error.message);
        res.status(500).json({ error: 'Database query failed' });
    }
});

// ✅ Fetch Real-Time UFC Fight Card (Merged & Updated)
app.get("/fight-card", async (req, res) => {
    try {
        const fights = await pool.query(
            "SELECT fighter1, fighter2, event_name, date, weight_class, fighter1_image, fighter2_image FROM upcoming_fights WHERE event_name = 'UFC 316'"
        );

        // ✅ Add default placeholder images if missing
        fights.rows = fights.rows.map(fight => {
            fight.fighter1_image = fight.fighter1_image || "https://ufc.com/default-fighter-image.jpg";
            fight.fighter2_image = fight.fighter2_image || "https://ufc.com/default-fighter-image.jpg";
            return fight;
        });

        res.json(fights.rows);
    } catch (error) {
        console.error("Error fetching fight card:", error.message);
        res.status(500).json({ error: "Failed to retrieve fight card" });
    }
});

// ✅ Serve Static HTML Pages
app.get('/', (req, res) => res.sendFile(path.resolve(__dirname, 'public', 'index.html')));
app.get('/predictions', (req, res) => res.sendFile(path.resolve(__dirname, 'public', 'predictions.html')));
app.get('/upcoming', (req, res) => res.sendFile(path.resolve(__dirname, 'public', 'upcoming.html')));

// ✅ Start the Express Server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🤖 Server running on http://localhost:${PORT}`));