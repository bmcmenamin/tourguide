// server.js
const express = require('express');
const fs = require('fs');
const path = require('path');
const { NodeSchema, NodesSchema, LatLonSchema, LatLonsSchema, LinkSchema, LinksSchema, readAndValidateJSON } = require('./data/validation');
const { processData, processAndFilterNodes } = require('./process_geodata');

const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files from public' directory
app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/nodes', (req, res) => {
  try {
    const nodes = processData();
    const result = processAndFilterNodes(nodes);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Failed to process data', details: err.message });
  }
});

// Fallback to index.html for SPA
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
}); 