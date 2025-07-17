// public/main.js

window.initApp = function() {
  // Fetch all data and initialize the visualization
  Promise.all([
    fetch('/api/nodes').then(r => r.json()),
    fetch('/api/latlon').then(r => r.json()),
    fetch('/api/links').then(r => r.json())
  ]).then(([nodes, latlon, links]) => {
    // Normalize all IDs to numbers
    nodes.forEach(n => n.id = Number(n.id));
    latlon.forEach(l => l.id = Number(l.id));
    links = links.map(l => ({
      source: Number(l.source ?? l.node_a),
      target: Number(l.target ?? l.node_b),
      strength: l.strength ?? l.weight
    }));

    // Map from id to latlon
    const latlonMap = new Map(latlon.map(d => [d.id, d]));

    // Build adjacency list for all nodes
    const adjacency = new Map();
    links.forEach(l => {
      if (!adjacency.has(l.source)) adjacency.set(l.source, []);
      if (!adjacency.has(l.target)) adjacency.set(l.target, []);
      adjacency.get(l.source).push(l.target);
      adjacency.get(l.target).push(l.source);
    });

    // Find all nodes connected (directly or indirectly) to a geo node
    const geoNodeIds = new Set(latlon.map(d => d.id));
    const connected = new Set();
    const queue = Array.from(geoNodeIds);
    while (queue.length > 0) {
      const current = queue.shift();
      if (connected.has(current)) continue;
      connected.add(current);
      const neighbors = adjacency.get(current) || [];
      for (const neighbor of neighbors) {
        if (!connected.has(neighbor)) {
          queue.push(neighbor);
        }
      }
    }

    // Only include nodes that are geo nodes or connected to a geo node
    const filteredNodes = nodes.filter(n => connected.has(n.id));
    const geoNodes = filteredNodes.filter(n => latlonMap.has(n.id));
    const graphNodes = filteredNodes.filter(n => !latlonMap.has(n.id));

    // Debug logging
    console.log('All nodes:', nodes);
    console.log('Filtered nodes:', filteredNodes);
    console.log('Geo nodes:', geoNodes);
    console.log('Graph nodes:', graphNodes);
    console.log('Links:', links);

    // Prepare graph data: only include links where both nodes are in filteredNodes
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredLinks = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));

    // Initialize map and graph
    initMapAndGraph(geoNodes, graphNodes, latlonMap, filteredLinks, nodes);
  });

  function initMapAndGraph(geoNodes, graphNodes, latlonMap, links, allNodes) {
    try {
      // Debug logs
      console.log('geoNodes:', geoNodes);
      console.log('graphNodes:', graphNodes);
      console.log('links:', links);

      // 1. Initialize Leaflet map
      const map = L.map('map', {
        zoomControl: true,
        attributionControl: false,
        dragging: true,
        scrollWheelZoom: true,
        doubleClickZoom: true,
        boxZoom: true,
        keyboard: true,
        tap: false
      }).setView([0, 0], 2);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
      }).addTo(map);

      // 2. Fit map to geoNodes
      if (geoNodes.length > 0) {
        const bounds = L.latLngBounds(geoNodes.map(n => {
          const { lat, lon } = latlonMap.get(n.id);
          return [lat, lon];
        }));
        map.fitBounds(bounds, { padding: [50, 50] });
      }

      // 3. Prepare D3 force-directed graph for all connected nodes (geo + graph)
      // Move the SVG into the Leaflet overlayPane so it moves with the map
      let svg = d3.select(map.getPanes().overlayPane).select('svg#graph-overlay');
      if (!svg.node()) {
        svg = d3.select(map.getPanes().overlayPane)
          .append('svg')
          .attr('id', 'graph-overlay');
      } else {
        svg.selectAll('*').remove();
      }
      const width = window.innerWidth;
      const height = window.innerHeight;
      svg.attr('width', width).attr('height', height);

      // All nodes in the force simulation
      const allSimNodes = geoNodes.concat(graphNodes);

      // D3 simulation
      const simulation = d3.forceSimulation(allSimNodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(d => 100 / (d.strength || 1)))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .on('tick', ticked);

      // Draw links
      const link = svg.append('g')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke-width', d => Math.sqrt(d.strength || 1));

      // Draw nodes: allSimNodes, color by type
      const node = svg.append('g')
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .selectAll('circle')
        .data(allSimNodes)
        .join('circle')
        .attr('r', 12)
        .attr('fill', d => latlonMap.has(d.id) ? '#4CAF50' : '#0074D9') // green for geo, blue for graph
        .attr('class', 'd3-node')
        .call(drag(simulation));

      // Node labels: allSimNodes
      const label = svg.append('g')
        .selectAll('text')
        .data(allSimNodes)
        .join('text')
        .attr('text-anchor', 'middle')
        .attr('dy', 4)
        .attr('font-size', 12)
        .attr('fill', '#222')
        .text(d => d.name);

      // Synchronize geo node positions with map
      function updateGeoNodePositions() {
        geoNodes.forEach(node => {
          const { lat, lon } = latlonMap.get(node.id);
          const point = map.latLngToLayerPoint([lat, lon]);
          node.x = point.x;
          node.y = point.y;
        });
      }

      // Update overlay position/size and reproject all node positions
      function updateOverlay() {
        // Resize SVG to match map container
        const mapSize = map.getSize();
        svg.attr('width', mapSize.x).attr('height', mapSize.y);
        // Reproject geo node positions
        updateGeoNodePositions();
        // Update D3 elements
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);
        node
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
        label
          .attr('x', d => d.x)
          .attr('y', d => d.y - 18);
      }

      // Drag behavior
      function drag(simulation) {
        function dragstarted(event, d) {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        }
        function dragged(event, d) {
          d.fx = event.x;
          d.fy = event.y;
        }
        function dragended(event, d) {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }
        return d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended);
      }

      // Update positions on tick
      function ticked() {
        updateGeoNodePositions();
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);
        node
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
        label
          .attr('x', d => d.x)
          .attr('y', d => d.y - 18);
      }

      // On map move/zoom, update overlay and reproject nodes
      map.on('move zoom', updateOverlay);

      // Call updateOverlay once after initial render
      updateOverlay();

      // Responsive resize
      window.addEventListener('resize', () => {
        const w = window.innerWidth;
        const h = window.innerHeight;
        svg.attr('width', w).attr('height', h);
        simulation.force('center', d3.forceCenter(w / 2, h / 2));
        simulation.alpha(0.5).restart();
      });

      // Hide loading modal when all rendering is complete
      const loading = document.getElementById('loading');
      if (loading) loading.style.display = 'none';
    } catch (err) {
      console.error('Error in initMapAndGraph:', err);
      const loading = document.getElementById('loading');
      if (loading) loading.innerHTML = '<h3>Error loading visualization</h3><pre>' + err.message + '</pre>';
    }
  }
};

window.initApp(); 