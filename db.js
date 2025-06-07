const { Pool } = require('pg');

const pool = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'ufc_fight_hub',
  password: 'tsubasa', // Replace with your actual password
  port: 5432, // Default PostgreSQL port
});

module.exports = pool;