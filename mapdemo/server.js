// server.js
const express = require('express');
const fs = require('fs');
const path = require('path');
const { z } = require('zod');

const app = express();
const PORT = process.env.PORT || 3000;

// Zod schemas
function defineZodSchemas() {
  global.NodeSchema = z.object({
    id: z.number(),
    name: z.string(),
  });
  global.NodesSchema = z.array(global.NodeSchema);

  global.LatLonSchema = z.object({
    id: z.number(),
    lat: z.number(),
    lon: z.number(),
  });
  global.LatLonsSchema = z.array(global.LatLonSchema);

  global.LinkSchema = z.object({
    node_a: z.number(),
    node_b: z.number(),
    weight: z.number(),
  });
  global.LinksSchema = z.array(global.LinkSchema);
}

defineZodSchemas();

// Helper to read and validate JSON files
function readAndValidateJSON(filename, schema) {
  const raw = fs.readFileSync(path.join(__dirname, filename), 'utf8');
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    throw new Error(`${filename} is not valid JSON: ${e.message}`);
  }
  const result = schema.safeParse(parsed);
  if (!result.success) {
    throw new Error(`${filename} failed validation: ${result.error.toString()}`);
  }
  return result.data;
}

function processData() {
  const nodes = readAndValidateJSON('nodes.json', global.NodesSchema);
  const latlons = readAndValidateJSON('latlon.json', global.LatLonsSchema);
  const links = readAndValidateJSON('links.json', global.LinksSchema);

  // Normalize links to {source, target, strength}
  const normalizedLinks = links.map(l => ({
    source: l.source ?? l.node_a,
    target: l.target ?? l.node_b,
    strength: l.strength ?? l.weight
  }));

  // Map latlon by id for quick lookup
  const latlonMap = {};
  latlons.forEach(ll => {
    latlonMap[ll.id] = ll;
  });

  // Map links by node id
  const linksMap = {};
  normalizedLinks.forEach(link => {
    // Each link: { source, target, strength }
    if (!linksMap[link.source]) linksMap[link.source] = [];
    if (!linksMap[link.target]) linksMap[link.target] = [];
    linksMap[link.source].push({ target: link.target, strength: link.strength });
    linksMap[link.target].push({ target: link.source, strength: link.strength }); // undirected
  });

  // Build final node list
  const resultNodes = [];
  nodes.forEach(node => {
    const hasLatLon = !!latlonMap[node.id];
    const nodeLinks = linksMap[node.id] || [];
    if (hasLatLon || nodeLinks.length > 0) {
      resultNodes.push({
        id: node.id,
        name: node.name,
        lat: hasLatLon ? latlonMap[node.id].lat : undefined,
        lon: hasLatLon ? latlonMap[node.id].lon : undefined,
        links: nodeLinks
      });
    }
    // else: exclude node
  });
  return resultNodes;
}

// Serve static files from public' directory
app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/nodes', (req, res) => {
  try {
    const data = processData();
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to process data', details: err.message });
  }
});

app.get('/api/latlon', (req, res) => {
  fs.readFile(path.join(__dirname, 'latlon.json'), 'utf8', (err, data) => {
    if (err) return res.status(500).json({ error: 'Failed to read latlon.json' });
    res.json(JSON.parse(data));
  });
});

app.get('/api/links', (req, res) => {
  fs.readFile(path.join(__dirname, 'links.json'), 'utf8', (err, data) => {
    if (err) return res.status(500).json({ error: 'Failed to read links.json' });
    res.json(JSON.parse(data));
  });
});

// Fallback to index.html for SPA
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
}); 