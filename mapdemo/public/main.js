// public/main.js

window.initApp = function() {
  // Fetch all data and initialize the visualization
  fetch('/api/nodes').then(r => r.json()).then(({ geoNodes, graphNodes, latlonMap, filteredLinks, allNodes }) => {
    // Convert latlonMap from object to Map if needed
    const latlonMapObj = latlonMap instanceof Map ? latlonMap : new Map(Object.entries(latlonMap).map(([k, v]) => [Number(k), v]));

    // Initialize map and graph
    initMapAndGraph(geoNodes, graphNodes, latlonMapObj, filteredLinks, allNodes);
  });

  function initMapAndGraph(geoNodes, graphNodes, latlonMap, links, allNodes) {
    try {

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
        const boundsPoints = geoNodes
          .map(n => latlonMap.get(n.id))
          .filter(geo => geo && typeof geo.lat === 'number' && typeof geo.lon === 'number')
          .map(geo => [geo.lat, geo.lon]);
        if (boundsPoints.length > 0) {
          const bounds = L.latLngBounds(boundsPoints);
          map.fitBounds(bounds, { padding: [50, 50] });
        }
      } else {
        map.setView([0, 0], 2);
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

      const nodeRadius = 12;

      // D3 simulation
      const simulation = d3.forceSimulation(allSimNodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(d => 1 / (d.strength || 1)))
        .force('collide', d3.forceCollide(nodeRadius * 1.01).strength(0.7))
        .on('tick', ticked);

      // Draw links
      const g = svg.append('g').attr('class', 'leaflet-zoom-hide');
      const link = g.append('g')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke-width', d => Math.sqrt(d.strength || 1));

      // Draw nodes: allSimNodes, color by type
      const node = g.append('g')
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .selectAll('circle')
        .data(allSimNodes)
        .join('circle')
        .attr('r', nodeRadius)
        .attr('fill', d => latlonMap.has(d.id) ? '#4CAF50' : '#0074D9') // green for geo, blue for graph
        .attr('class', 'd3-node')
        .call(drag(simulation));

      // Node labels: allSimNodes
      const label = g.append('g')
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
          const geo = latlonMap.get(node.id);
          if (geo) {
            const { lat, lon } = geo;
            const point = map.latLngToLayerPoint([lat, lon]);
            node.x = point.x;
            node.y = point.y;
            node.fx = point.x; // Pin to projected position
            node.fy = point.y;
            node.vx = 0; // Stop any momentum
            node.vy = 0;
          }
        });
      }

      // (Undo offset-based anchoring: do nothing here)

      // Update overlay position/size and reproject all node positions
      function updateOverlay() {
        // Resize SVG to match map container
        const mapSize = map.getSize();
        svg.attr('width', mapSize.x).attr('height', mapSize.y);

        // Reproject geo node positions
        updateGeoNodePositions();

        // (Undo offset-based anchoring: do nothing here)
        const topLeft = map.latLngToLayerPoint(map.getBounds().getNorthWest());

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

        // Kick the force simulation to let graph nodes resettle
        simulation.alpha(0.7).restart();
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
          // Only unpin if not a geo node
          if (!latlonMap.has(d.id)) {
            d.fx = null;
            d.fy = null;
          }
          // For geo nodes, fx/fy will be reset on next tick by updateGeoNodePositions
        }
        return d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended);
      }

      // Update positions on tick
      function ticked() {
        // Always update geo node positions first
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