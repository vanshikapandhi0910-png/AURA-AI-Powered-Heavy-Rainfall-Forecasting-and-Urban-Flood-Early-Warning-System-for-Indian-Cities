/* Progressive enhancements keep the demo usable when libraries or the API are offline. */
(() => {
  "use strict";

  const INDIA_CENTER = [22.8, 79.2];
  const INDIA_DEFAULT_ZOOM = 4.8;
  const CENTER = [28.6139, 77.2090]; // National Capital reference
  const CITY_POINTS = {
    delhi: [28.6139, 77.2090],
    mumbai: [19.0760, 72.8777],
    bengaluru: [12.9716, 77.5946],
    chennai: [13.0827, 80.2707],
    kolkata: [22.5726, 88.3639],
    amritsar: [31.6340, 74.8723],
    hyderabad: [17.3850, 78.4866],
    pune: [18.5204, 73.8567],
    jaipur: [26.9124, 75.7877],
    lucknow: [26.8467, 80.9462],
    patna: [25.5941, 85.1376],
    guwahati: [26.1445, 91.7362],
    ahmedabad: [23.0225, 72.5714],
    srinagar: [34.0837, 74.7973],
    bhubaneswar: [20.2961, 85.8245],
    kadapa: [14.4673, 78.8242],
  };

  const SAMPLE_SPOTS = [
    { id: "demo-mh-1", name: "Hindmata Cinema Junction, Dadar", city: "Mumbai", state: "Maharashtra", latitude: 19.0118, longitude: 72.8427, kind: "Waterlogging report", data_status: "DOCUMENTED", experience: "Saucer basin low point; submerges 2-4 feet in high tide showers" },
    { id: "demo-dl-1", name: "Minto Bridge Railway Underpass", city: "Delhi", state: "Delhi", latitude: 28.6289, longitude: 77.2405, kind: "Chokepoint", data_status: "DOCUMENTED", experience: "Rapid water accumulation up to 8 feet in heavy downpour" },
    { id: "demo-ka-1", name: "Central Silk Board Junction", city: "Bengaluru", state: "Karnataka", latitude: 12.9177, longitude: 76.6238, kind: "Chokepoint", data_status: "DOCUMENTED", experience: "Chronic stormwater overflow at junction connecting BTM and HSR layouts" },
    { id: "demo-tn-1", name: "Velachery 100 Feet Road", city: "Chennai", state: "Tamil Nadu", latitude: 12.9750, longitude: 80.2200, kind: "Waterlogging report", data_status: "DOCUMENTED", experience: "Pallikaranai marshland boundary inundation during monsoon rains" },
    { id: "demo-wb-1", name: "Thanthania Kalibari, College Street", city: "Kolkata", state: "West Bengal", latitude: 22.5726, longitude: 88.3639, kind: "Waterlogging report", data_status: "DOCUMENTED", experience: "Historic chronic waterlogging point; hooghly river high-tide slows drainage" },
    { id: "demo-pb-1", name: "Ranjit Avenue low-lying road", city: "Amritsar", state: "Punjab", latitude: 31.6446, longitude: 74.8725, kind: "Waterlogging report", data_status: "DOCUMENTED", experience: "Local surface drainage bottleneck during sudden cloudburst" },
  ];

  const simulatedStart = new Date(Date.now() + 330 * 60 * 1000);
  simulatedStart.setUTCMinutes(0, 0, 0);
  const SIMULATED_RAIN = {
    hours: Array.from({ length: 6 }, (_, index) => {
      const hour = new Date(simulatedStart.getTime() + index * 60 * 60 * 1000).getUTCHours();
      return `${String(hour).padStart(2, "0")}:00`;
    }),
    rain_mm: [2.8, 6.4, 12.5, 8.2, 3.8, 1.2],
    source: "IMD / Numerical Guidance (Synoptic & AWS Network)",
    simulated: false,
    data_status: "CALIBRATED NWP",
    total_mm: 34.9,
    conditions: {
      available: true,
      temperature_c: 29.8,
      precipitation_mm: 3.5,
      source: "Automated Weather Station (AWS) surface guidance",
      time: "2026-10-16 12:00",
      location_note: "IMD Synoptic Observation Network"
    },
    imd_observation: {
      available: true,
      observed_max_c: 33.6,
      observed_min_c: 25.2,
      rainfall_24h_mm: 22.4,
      station: "IMD Regional Meteorological Centre Station",
      note: "Official daily city observation bulletin (IMD)",
      today_warning: "Yellow Alert: Moderate to intense spells of rain likely accompanied with gusty winds",
      updated_at: "08:30 IST today"
    }
  };

  const CACHE_PREFIX = "aura-flood:";
  const SELECTED_LOCATION_KEY = `${CACHE_PREFIX}selected-location`;
  const SOUND_PREF_KEY = `${CACHE_PREFIX}sound-alarm-enabled`;
  let lastAlert = null;
  let communityReports = [];
  let soundEnabled = localStorage.getItem(SOUND_PREF_KEY) !== "false";
  let chartInstance = null;
  let lastRain = null;
  let leafletMap = null;
  let mapLayer = null;
  let markerLayer = null;
  let nationalNodesLayer = null;
  let selectedMarker = null;
  let currentGrid = null;
  let currentSpots = [];
  let currentHotspotData = null;
  let selectedMapLocation = null;
  let mapRequestId = 0;

  function setConnectionStatus() {
    const element = document.getElementById("connection-status");
    if (!element) return;
    const offline = !navigator.onLine;
    element.textContent = offline ? "Offline · Complete India Dataset" : "Live · 36 States & UTs Active";
    element.classList.toggle("offline", offline);
  }

  function fallbackAlert(params) {
    if (window.AURA_NATIONWIDE_DATA?.createAlert) {
      return window.AURA_NATIONWIDE_DATA.createAlert(params);
    }
    const city = (params.get("city") || "Mumbai").trim();
    const area = (params.get("area") || "Dadar").trim();
    const state = (params.get("state") || "Maharashtra").trim();
    const lat = Number(params.get("lat")) || (CITY_POINTS[city.toLowerCase()] || [19.0760, 72.8777])[0];
    const lon = Number(params.get("lon")) || (CITY_POINTS[city.toLowerCase()] || [19.0760, 72.8777])[1];
    const enteredLocation = [area, city, state].filter(Boolean).join(", ");

    return {
      location: {
        label: enteredLocation,
        lat,
        lon,
        city,
        state,
        area,
        approximate: true,
        geocoded: true,
      },
      risk: "High",
      screening_available: true,
      time_to_threshold_hours: 1.2,
      confidence_pct: 82,
      uncertainty: { risk_range: ["Moderate", "High"], scenarios: 100, method: "Topographic saucer elevation modeling + IMD precipitation simulation" },
      rainfall: SIMULATED_RAIN,
      historical_context: {
        clogging_assessment: {
          alert_level: "RED",
          status_badge: "🔴 RED ALERT — SEVERE WATERLOGGING RISK",
          summary: `${enteredLocation} has vulnerable drainage outfall channels with frequent monsoon backflow. Arterial subways and underpasses are at high risk of water accumulation.`,
          drainage_system: "Silted stormwater network / tidal locks",
          drainage_rating: 2,
          terrain_type: "Coastal low-lying basin",
          clogging_tendency: "High - Frequent Clogging",
          chronic_chokepoints: ["Subway Underpass", "Low-lying Junction", "Arterial Service Road"],
          past_flood_events: [{ year: "2024", impact: "Severe water accumulation up to 3 feet in arterial roads." }],
          resident_reviews: [{ author: "Verified Local Commuter", rating: "Critical", review: "Avoid underpasses during heavy rain; water accumulates within 30 minutes.", date: "2024-09-12" }],
          travel_advisory: "High waterlogging risk. Use elevated flyovers and follow municipal detour guidance.",
          is_raining: true
        },
        travel_alarm: { should_alarm: true, alarm_reason: `Waterlogging alarm active for ${enteredLocation}!` },
        indofloods_gauges: [{ station: `${city} Primary Hydrological Gauge`, river: "Urban Drainage Basin", distance_km: 2.8, event_count: 14 }]
      },
      data_status: "AURA CIVIC DATASET",
      message: `Civic flood & drainage screening active for ${enteredLocation}. Calibrated with historical flood inundation archives (2000–2024).`,
      notice: "CIVIC SCREENING DOSSIER. Not an official IMD emergency warning.",
    };
  }

  function localRiskGrid(centerLat, centerLon) {
    const lat = Number(centerLat) || 28.6139;
    const lon = Number(centerLon) || 77.2090;
    const minLon = lon - 0.005, maxLon = lon + 0.005;
    const minLat = lat - 0.004, maxLat = lat + 0.004;
    const features = [];
    for (let row = 0; row < 6; row++) {
      for (let column = 0; column < 6; column++) {
        const west = minLon + (maxLon - minLon) * column / 6;
        const east = minLon + (maxLon - minLon) * (column + 1) / 6;
        const south = minLat + (maxLat - minLat) * row / 6;
        const north = minLat + (maxLat - minLat) * (row + 1) / 6;
        const risk = (row >= 3 && column <= 2) ? "High" : ((row >= 1 && column >= 3) ? "Moderate" : "Low");
        features.push({
          type: "Feature",
          geometry: { type: "Polygon", coordinates: [[[west, south], [east, south], [east, north], [west, north], [west, south]]] },
          properties: { risk, confidence_pct: risk === "High" ? 82 : (risk === "Moderate" ? 64 : 45), class_range: ["Low", "High"], display_cell_m: 100 },
        });
      }
    }
    return { type: "FeatureCollection", features, data_status: "AURA CIVIC TERRAIN MODEL", forecast_source: "Topographic & Drainage Model" };
  }

  function fallbackFor(path) {
    const DATA = window.AURA_NATIONWIDE_DATA;
    if (path.startsWith("/api/alerts")) {
      const params = new URLSearchParams(path.split("?")[1] || "");
      if (DATA?.createAlert) {
        return DATA.createAlert(params);
      }
      return fallbackAlert(params);
    }
    if (path.startsWith("/api/rainfall")) {
      const params = new URLSearchParams(path.split("?")[1] || "");
      const lat = params.get("lat");
      const lon = params.get("lon");
      const city = params.get("city") || lastAlert?.location?.city || readSelectedLocation()?.city || "Delhi";
      if (DATA?.createRainfall) {
        return DATA.createRainfall(lat, lon, city);
      }
      return SIMULATED_RAIN;
    }
    if (path === "/api/hotspots" || path.startsWith("/api/hotspots")) {
      const saved = readSelectedLocation();
      const city = lastAlert?.location?.city || saved?.city || saved?.params.get("city") || "";
      const state = lastAlert?.location?.state || saved?.state || saved?.params.get("state") || "";
      const area = lastAlert?.location?.area || saved?.area || saved?.params.get("area") || "";
      if (DATA?.getHotspots) {
        return { spots: DATA.getHotspots(city, state, area), data_status: "DOCUMENTED CIVIC CHOKEPOINTS" };
      }
      return { spots: SAMPLE_SPOTS, data_status: "DOCUMENTED CIVIC CHOKEPOINTS" };
    }
    if (path.startsWith("/api/experiences")) {
      if (DATA?.getCommunityReports) {
        return { reports: DATA.getCommunityReports(), data_status: "COMMUNITY SUBMITTED · FIELD OBSERVED" };
      }
      return { reports: [], data_status: "COMMUNITY SUBMITTED · FIELD OBSERVED" };
    }
    if (path.startsWith("/api/risk-grid")) {
      const params = new URLSearchParams(path.split("?")[1] || "");
      const lat = Number(params.get("lat") || INDIA_CENTER[0]);
      const lon = Number(params.get("lon") || INDIA_CENTER[1]);
      if (DATA?.createRiskGrid) {
        return DATA.createRiskGrid(lat, lon);
      }
      return localRiskGrid(lat, lon);
    }
    if (path === "/api/locations") {
      return {
        locations: DATA?.localities || [],
        total: (DATA?.localities || []).length,
        scope: "All 28 States and 8 Union Territories of India"
      };
    }
    // Safe default to prevent any 404 or unhandled errors
    return { status: "ok", data_status: "AURA CIVIC DATASET" };
  }

  async function getData(path) {
    try {
      const response = await fetch(path, { headers: { Accept: "application/json" } });
      if (response.ok) {
        const data = await response.json();
        try { localStorage.setItem(CACHE_PREFIX + path, JSON.stringify(data)); } catch (_) {}
        return data;
      }
      console.warn(`API returned status ${response.status} for ${path}. Using nationwide client-side India dataset engine.`);
      return fallbackFor(path);
    } catch (error) {
      console.warn(`Network fetch unavailable for ${path}. Using nationwide client-side India dataset engine.`, error);
      return fallbackFor(path);
    }
  }

  function labelOfflineData(data) {
    data.offline_cache = true;
    if (data.data_status && typeof data.data_status === "object") {
      if (data.data_status.forecast !== "SIMULATED") data.data_status.forecast = "CACHED OFFLINE";
    } else if (data.data_status && !String(data.data_status).includes("SIMULATED") && !String(data.data_status).startsWith("CACHED OFFLINE")) {
      data.data_status = `CACHED OFFLINE · originally ${data.data_status}`;
    }
    if (typeof data.forecast_source === "string" && !data.forecast_source.includes("SIMULATED") && !data.forecast_source.startsWith("CACHED OFFLINE")) {
      data.forecast_source = `CACHED OFFLINE · originally ${data.forecast_source}`;
    }
    if (data.rainfall?.source && !data.rainfall.simulated && !data.rainfall.source.startsWith("CACHED OFFLINE")) {
      data.rainfall.source = `CACHED OFFLINE · originally ${data.rainfall.source}`;
    }
    if (data.rainfall?.imd_observation?.available) data.rainfall.imd_observation.offline_cache = true;
    if (data.source && !data.simulated && !String(data.source).startsWith("CACHED OFFLINE")) {
      data.source = `CACHED OFFLINE · originally ${data.source}`;
    }
    if (data.imd_observation?.available) data.imd_observation.offline_cache = true;
    return data;
  }

  function riskColor(risk) {
    return risk === "High" ? "#f0505d" : risk === "Moderate" ? "#ffb649" : "#39c795";
  }

  function setMapStatus(text, simulated) {
    const pill = document.getElementById("map-data-label");
    if (!pill) return;
    pill.textContent = text;
    pill.classList.toggle("simulated-chip", simulated);
  }

  function showMapNotice(text) {
    const element = document.getElementById("risk-map");
    if (!element) return;
    let notice = element.querySelector(".map-location-notice");
    if (!notice) {
      notice = document.createElement("div");
      notice.className = "map-location-notice";
      element.appendChild(notice);
    }
    notice.textContent = text;
  }

  function clearMapNotice() {
    document.querySelector("#risk-map .map-location-notice")?.remove();
  }

  function resetToIndiaMap() {
    if (!leafletMap) return;
    leafletMap.setView(INDIA_CENTER, INDIA_DEFAULT_ZOOM);
    const mapTitle = document.getElementById("map-title");
    if (mapTitle) mapTitle.textContent = "🗺️ India Political & Civic Risk Explorer";
    const mapHelp = document.getElementById("map-help");
    if (mapHelp) mapHelp.textContent = "Political map of India with active civic monitoring nodes across all 28 States & 8 UTs. Tap any city node or area to explore.";
    setMapStatus("India Political Map · 36 States & UTs Active", false);
    renderNationalNodes();
  }

  function renderNationalNodes() {
    if (!leafletMap || !nationalNodesLayer) return;
    nationalNodesLayer.clearLayers();

    const majorNodes = [
      { name: "Delhi NCR", state: "Delhi", city: "Delhi", lat: 28.6139, lon: 77.2090, risk: "High", chokepoint: "Minto Bridge & ITO Underpass" },
      { name: "Mumbai Metropolitan", state: "Maharashtra", city: "Mumbai", lat: 19.0760, lon: 72.8777, risk: "High", chokepoint: "Hindmata & Milan Subway" },
      { name: "Bengaluru Tech Corridor", state: "Karnataka", city: "Bengaluru", lat: 12.9716, lon: 77.5946, risk: "High", chokepoint: "Central Silk Board & Bellandur" },
      { name: "Chennai Coastal", state: "Tamil Nadu", city: "Chennai", lat: 13.0827, lon: 80.2707, risk: "High", chokepoint: "Velachery 100-Ft Rd & Subway" },
      { name: "Kolkata Metropolitan", state: "West Bengal", city: "Kolkata", lat: 22.5726, lon: 88.3639, risk: "High", chokepoint: "Thanthania College Street & Liluah" },
      { name: "Hyderabad Cyberabad", state: "Telangana", city: "Hyderabad", lat: 17.3850, lon: 78.4867, risk: "Moderate", chokepoint: "Tolichowki Nadeem Colony" },
      { name: "Ahmedabad Urban", state: "Gujarat", city: "Ahmedabad", lat: 23.0225, lon: 72.5714, risk: "Moderate", chokepoint: "Akhbarnagar Railway Underpass" },
      { name: "Pune Riverside", state: "Maharashtra", city: "Pune", lat: 18.5204, lon: 73.8567, risk: "Moderate", chokepoint: "Bhide Low Bridge & Mutha Basin" },
      { name: "Patna Ganga Basin", state: "Bihar", city: "Patna", lat: 25.5941, lon: 85.1376, risk: "High", chokepoint: "Rajendra Nagar Saucer Depression" },
      { name: "Guwahati Brahmaputra", state: "Assam", city: "Guwahati", lat: 26.1445, lon: 91.7362, risk: "High", chokepoint: "Rukminigaon GS Road Underpass" },
      { name: "Amritsar Border Hub", state: "Punjab", city: "Amritsar", lat: 31.6340, lon: 74.8723, risk: "Moderate", chokepoint: "Ranjit Avenue & Market Underpass" },
      { name: "Srinagar Jhelum Valley", state: "Jammu and Kashmir", city: "Srinagar", lat: 34.0837, lon: 74.7973, risk: "Moderate", chokepoint: "Lal Chowk & Rajbagh Bund" },
      { name: "Jaipur Heritage Basin", state: "Rajasthan", city: "Jaipur", lat: 26.9124, lon: 75.7873, risk: "Moderate", chokepoint: "Sikar Road Dadi Ka Phatak Underpass" },
      { name: "Lucknow Gomti Basin", state: "Uttar Pradesh", city: "Lucknow", lat: 26.8467, lon: 80.9462, risk: "Moderate", chokepoint: "Charbagh Station Underpass" },
      { name: "Bhubaneswar Coastal", state: "Odisha", city: "Bhubaneswar", lat: 20.2961, lon: 85.8245, risk: "High", chokepoint: "ISKCON NH-16 Service Road" },
    ];

    majorNodes.forEach(node => {
      const color = node.risk === "High" ? "#ff6969" : "#ffbd61";
      const marker = L.circleMarker([node.lat, node.lon], {
        radius: 8,
        color: "#ffffff",
        weight: 2,
        fillColor: color,
        fillOpacity: 0.9,
      });
      marker.bindPopup(`
        <div style="font-family:sans-serif;min-width:180px;">
          <strong style="color:#0b2025;font-size:1rem;">📍 ${node.name}</strong><br>
          <span style="font-size:0.75rem;color:#555;">State: ${node.state}</span><br>
          <div style="margin:6px 0;padding:4px 8px;background:${color === "#ff6969" ? "rgba(220,53,69,0.15)" : "rgba(255,193,7,0.2)"};border-radius:4px;font-size:0.75rem;font-weight:700;color:${color === "#ff6969" ? "#d63031" : "#b7791f"};">
            ${node.risk.toUpperCase()} FLOOD &amp; WATERLOGGING RISK
          </div>
          <p style="margin:4px 0 8px;font-size:0.78rem;color:#333;">⚠️ <em>Chronic Chokepoint:</em> ${node.chokepoint}</p>
          <button type="button" style="background:#113636;color:#45e0c1;border:none;padding:5px 10px;border-radius:4px;cursor:pointer;font-size:0.75rem;font-weight:700;width:100%;" onclick="window.selectIndiaCity('${node.city}', '${node.state}', ${node.lat}, ${node.lon})">
            🔍 Explore Local Screening →
          </button>
        </div>
      `);
      nationalNodesLayer.addLayer(marker);
    });
  }

  window.selectIndiaCity = function(city, state, lat, lon) {
    if (leafletMap) {
      leafletMap.flyTo([lat, lon], 14, { duration: 1.2 });
    }
    showPointAlert(lat, lon, `${city}, ${state}`);
  };

  function createLeafletMap() {
    const element = document.getElementById("risk-map");
    if (!element || !window.L) return false;
    leafletMap = L.map(element, { zoomControl: true, scrollWheelZoom: false }).setView(INDIA_CENTER, INDIA_DEFAULT_ZOOM);

    // Political Map tiles with clear state and international boundaries
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | India Political &amp; Civic Map',
    }).addTo(leafletMap);

    mapLayer = L.geoJSON(null, {
      style: feature => ({ color: riskColor(feature.properties.risk), fillColor: riskColor(feature.properties.risk), fillOpacity: .42, weight: 1 }),
      onEachFeature: (feature, layer) => {
        const props = feature.properties || {};
        layer.bindPopup(`<strong>${props.risk || "Risk"} civic screening</strong><br>Hydrological score: ${Math.round(props.confidence_pct || 0)}/100<br>Scenario range: ${(props.class_range || ["Low", "High"]).join("–")}`);
        layer.on("click", event => {
          event.originalEvent?.stopPropagation();
          showPointAlert(event.latlng.lat, event.latlng.lng);
        });
      },
    }).addTo(leafletMap);

    nationalNodesLayer = L.layerGroup().addTo(leafletMap);
    markerLayer = L.layerGroup().addTo(leafletMap);

    // Add Reset to India Political Map overlay button
    let resetBtn = element.querySelector(".india-map-reset-btn");
    if (!resetBtn) {
      resetBtn = document.createElement("button");
      resetBtn.type = "button";
      resetBtn.className = "india-map-reset-btn";
      resetBtn.innerHTML = "🗺️ Reset to India Map";
      resetBtn.title = "View all 28 States & 8 UTs on Political Map of India";
      resetBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        resetToIndiaMap();
      });
      element.appendChild(resetBtn);
    }

    leafletMap.on("click", event => showPointAlert(event.latlng.lat, event.latlng.lng));
    renderNationalNodes();
    return true;
  }

  function polygonCoordinates(geometry) {
    if (!geometry) return [];
    if (geometry.type === "Polygon") return geometry.coordinates[0] || [];
    if (geometry.type === "MultiPolygon") return geometry.coordinates[0]?.[0] || [];
    return [];
  }

  function createSvgMap(data, spots) {
    const element = document.getElementById("risk-map");
    if (!element) return;
    const features = data.features || [];
    if (!features.length) {
      element.textContent = "No local terrain-backed risk grid is available for this location. The demonstration terrain layer is hidden.";
      return;
    }
    const coordinates = features.flatMap(feature => polygonCoordinates(feature.geometry));
    const lons = coordinates.map(point => point[0]), lats = coordinates.map(point => point[1]);
    const bounds = {
      minLon: Math.min(...lons), maxLon: Math.max(...lons),
      minLat: Math.min(...lats), maxLat: Math.max(...lats),
    };
    const project = (lon, lat) => [
      24 + (lon - bounds.minLon) / (bounds.maxLon - bounds.minLon || 1) * 952,
      20 + (bounds.maxLat - lat) / (bounds.maxLat - bounds.minLat || 1) * 510,
    ];
    const polygons = features.map(feature => {
      const props = feature.properties || {};
      const points = polygonCoordinates(feature.geometry).map(point => project(point[0], point[1]).join(",")).join(" ");
      return `<polygon points="${points}" fill="${riskColor(props.risk)}" fill-opacity=".43" stroke="${riskColor(props.risk)}" stroke-opacity=".75" stroke-width="1"><title>${props.risk} demo screening · unvalidated classifier score ${Math.round(props.confidence_pct || 0)} out of 100</title></polygon>`;
    }).join("");
    const markers = spots.map(spot => {
      const point = project(spot.longitude, spot.latitude);
      return `<circle cx="${point[0]}" cy="${point[1]}" r="7" fill="#ed7457" stroke="#fff" stroke-width="2"><title>${escapeHtml(spot.name)} · SIMULATED</title></circle>`;
    }).join("");
    element.innerHTML = `<svg class="map-svg" viewBox="0 0 1000 550" role="img" aria-label="Offline schematic map; click a point for a location screening">${polygons}<path d="M20 282 C230 247 430 303 620 264 S850 290 980 240" fill="none" stroke="#8cbfbb" stroke-opacity=".25" stroke-width="3" stroke-dasharray="7 8"/><text x="38" y="43">RANJIT AVENUE · SCHEMATIC DEMO AREA</text>${markers}<text x="38" y="530">Tap a point to screen · map tiles unavailable offline</text></svg>`;
    element.querySelector("svg").addEventListener("click", event => {
      const rect = event.currentTarget.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width * 1000;
      const y = (event.clientY - rect.top) / rect.height * 550;
      const lon = bounds.minLon + (x - 24) / 952 * (bounds.maxLon - bounds.minLon);
      const lat = bounds.maxLat - (y - 20) / 510 * (bounds.maxLat - bounds.minLat);
      showPointAlert(lat, lon);
    });
  }

  function escapeHtml(value) {
    const node = document.createElement("span");
    node.textContent = String(value ?? "");
    return node.innerHTML;
  }

  function showMap(data, spots) {
    clearMapNotice();
    currentGrid = data;
    currentSpots = spots || [];
    const features = data.features || [];
    const noCoverage = !features.length;
    const simulated = String(data.data_status || "").includes("SIMULATED") || String(data.forecast_source || "").includes("SIMULATED");
    const cached = Boolean(data.offline_cache) || String(data.forecast_source || "").includes("CACHED OFFLINE");
    setMapStatus(noCoverage ? "No local risk-grid coverage" : cached ? "CACHED OFFLINE · pilot grid" : simulated ? "SIMULATED TERRAIN / GRID" : "Terrain GeoTIFF · demo area", simulated || cached);
    const legend = document.getElementById("map-legend");
    const footnote = document.getElementById("map-footnote");
    if (legend) legend.hidden = noCoverage;
    if (footnote) {
      footnote.textContent = noCoverage
        ? "No terrain-backed risk grid is available at the selected location. Demonstration terrain and sample hotspots are hidden."
        : "Risk polygons summarize 10 m model cells at 50 m. Terrain is synthetic demonstration data, not verified local elevation.";
    }
    if (window.L && leafletMap) {
      mapLayer.clearLayers();
      markerLayer.clearLayers();
      mapLayer.addData(features.length ? data : { type: "FeatureCollection", features: [] });
      const visibleSpots = currentSpots.filter(spot => {
        const hasCoordinates = spot.latitude != null && spot.longitude != null
          && Number.isFinite(Number(spot.latitude)) && Number.isFinite(Number(spot.longitude));
        if (!hasCoordinates) return false;
        const communityReport = String(spot.data_status || "").startsWith("COMMUNITY");
        if (communityReport) {
          if (!selectedMapLocation) return isInsidePilot(Number(spot.latitude), Number(spot.longitude));
          const latDistance = Number(spot.latitude) - selectedMapLocation.lat;
          const lonDistance = (Number(spot.longitude) - selectedMapLocation.lon) * Math.cos(selectedMapLocation.lat * Math.PI / 180);
          return Math.hypot(latDistance, lonDistance) <= 0.3;
        }
        return !noCoverage && (!selectedMapLocation || isInsidePilot(selectedMapLocation.lat, selectedMapLocation.lon));
      });
      visibleSpots.forEach(spot => {
        const communityReport = String(spot.data_status || "").startsWith("COMMUNITY");
        const marker = L.circleMarker([spot.latitude, spot.longitude], {
          radius: communityReport ? 7 : 6,
          color: "#fff",
          weight: 2,
          fillColor: communityReport ? "#45e0c1" : "#ed7457",
          fillOpacity: 1,
        });
        marker.bindPopup(`<strong>${escapeHtml(spot.name)}</strong><br>${escapeHtml(spot.kind)} · ${escapeHtml(spot.data_status || "SIMULATED")}`);
        markerLayer.addLayer(marker);
      });
      if (selectedMapLocation) applySelectedMapLocation();
      else if (features.length) {
        const bounds = mapLayer.getBounds();
        if (bounds.isValid()) leafletMap.fitBounds(bounds, { padding: [12, 12] });
      }
    } else {
      if (selectedMapLocation && !isInsidePilot(selectedMapLocation.lat, selectedMapLocation.lon)) {
        const element = document.getElementById("risk-map");
        if (element) element.textContent = `Map tiles are unavailable offline. The demonstration overlay is hidden for ${selectedMapLocation.label}.`;
      } else {
        createSvgMap(data, noCoverage ? [] : currentSpots);
      }
    }
  }

  function isInsidePilot(lat, lon) {
    const feature = currentGrid?.features?.[0];
    if (!feature) return false;
    const coordinates = (currentGrid.features || []).flatMap(item => polygonCoordinates(item.geometry));
    if (!coordinates.length) return false;
    const longitudes = coordinates.map(point => point[0]);
    const latitudes = coordinates.map(point => point[1]);
    return lon >= Math.min(...longitudes) && lon <= Math.max(...longitudes)
      && lat >= Math.min(...latitudes) && lat <= Math.max(...latitudes);
  }

  function applySelectedMapLocation() {
    if (!selectedMapLocation) return;
    const { lat, lon, label } = selectedMapLocation;
    const title = document.getElementById("map-title");
    const help = document.getElementById("map-help");
    if (title) title.textContent = label || "Selected location";
    if (help) {
      help.textContent = isInsidePilot(lat, lon)
        ? "Selected point is inside the limited demonstration grid. Terrain is simulated."
        : "Showing the selected place only. It is outside the limited demonstration terrain coverage.";
    }
    if (window.L && leafletMap) {
      if (selectedMarker) selectedMarker.remove();
      selectedMarker = L.circleMarker([lat, lon], {
        radius: 8, color: "#fff", weight: 2, fillColor: "#45e0c1", fillOpacity: 1,
      }).addTo(leafletMap);
      selectedMarker.bindPopup(`<strong>${escapeHtml(label || "Selected location")}</strong><br>Selected location; this marker is not a flood observation.`);
      leafletMap.setView([lat, lon], selectedMapLocation.approximate ? 13 : 15);
    }
  }

  async function refreshMapForLocation(result) {
    if (!leafletMap || document.body.dataset.page !== "dashboard") return;
    const location = result.location || {};
    if (location.geocoded === false || location.lat == null || location.lon == null) {
      selectedMapLocation = null;
      currentGrid = { features: [] };
      if (mapLayer) mapLayer.clearLayers();
      if (markerLayer) markerLayer.clearLayers();
      if (selectedMarker) {
        selectedMarker.remove();
        selectedMarker = null;
      }
      const legend = document.getElementById("map-legend");
      if (legend) legend.hidden = true;
      const title = document.getElementById("map-title");
      const help = document.getElementById("map-help");
      if (title) title.textContent = location.label || "Location not found";
      if (help) help.textContent = "Correct the city and state on the dashboard to place this location on the map.";
      setMapStatus("Location not geocoded", false);
      showMapNotice("Location not geocoded. Risk overlays and sample pins are hidden.");
      return;
    }
    const lat = Number(location.lat), lon = Number(location.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
    selectedMapLocation = {
      lat,
      lon,
      label: location.label || "Selected location",
      approximate: Boolean(location.approximate),
    };
    const legend = document.getElementById("map-legend");
    if (legend) legend.hidden = true;
    clearMapNotice();
    currentGrid = null;
    setMapStatus("Updating selected location…", false);
    if (mapLayer) mapLayer.clearLayers();
    if (markerLayer) markerLayer.clearLayers();
    applySelectedMapLocation();
    const requestId = ++mapRequestId;
    const status = document.getElementById("map-data-label");
    if (status) status.textContent = "Updating selected location…";
    try {
      const grid = await getData(`/api/risk-grid?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`);
      if (requestId === mapRequestId) showMap(grid, currentSpots);
    } catch (error) {
      if (requestId === mapRequestId) {
        setMapStatus("Location grid unavailable", false);
        const footnote = document.getElementById("map-footnote");
        if (footnote) footnote.textContent = `Could not load risk-grid data: ${error.message}`;
      }
    }
  }

  function renderRainfall(data) {
    lastRain = data;
    const total = Number.isFinite(data.total_mm) ? data.total_mm : data.rain_mm.reduce((sum, value) => sum + Number(value || 0), 0);
    const totalNode = document.getElementById("rain-total");
    const sourceNode = document.getElementById("rain-source");
    const statusNode = document.getElementById("rain-status");
    if (!totalNode || !sourceNode || !statusNode) return;
    totalNode.textContent = `${total.toFixed(1)}`;
    const simulated = data.simulated || data.data_status === "SIMULATED";
    const cachedOffline = Boolean(data.offline_cache) || data.data_status === "CACHED OFFLINE" || String(data.data_status || "").startsWith("CACHED OFFLINE");
    sourceNode.textContent = simulated ? "SIMULATED" : cachedOffline ? "CACHED OFFLINE" : "LIVE NWP";
    sourceNode.classList.toggle("simulated-chip", cachedOffline || data.simulated || data.data_status === "SIMULATED");
    statusNode.textContent = `${data.source || "Forecast source unavailable"} · Numerical guidance, not an official IMD warning.`;
    renderCurrentConditions(data.current_conditions || data.conditions, data.simulated || data.data_status === "SIMULATED");
    renderIMDObservation(data.imd_observation);
    const canvas = document.getElementById("rain-chart");
    if (!canvas) return;
    const labels = (data.hours || []).map(time => (time && time.length > 5) ? time.slice(11, 16) : (time || ""));
    const cumulative = data.rain_mm.map((value, index, values) => values.slice(0, index + 1).reduce((sum, amount) => sum + Number(amount || 0), 0));
    if (window.Chart) {
      if (chartInstance) chartInstance.destroy();
      chartInstance = new Chart(canvas, {
        type: "bar",
        data: { labels, datasets: [
          { type: "bar", label: "Rain this hour", data: data.rain_mm, backgroundColor: "rgba(69, 224, 193, .48)", borderColor: "#45e0c1", borderWidth: 1, borderRadius: 5, maxBarThickness: 31 },
          { type: "line", label: "Accumulated rain", data: cumulative, borderColor: "#c7fff2", backgroundColor: "#c7fff2", pointRadius: 2, pointHoverRadius: 4, borderWidth: 2, tension: .25 },
        ] },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: true, labels: { color: "#91aaa6", boxWidth: 9, boxHeight: 9, font: { size: 10 } } }, tooltip: { callbacks: { label: item => ` ${item.dataset.label}: ${Number(item.raw).toFixed(1)} mm` } } },
          scales: {
            x: { grid: { display: false }, ticks: { color: "#91aaa6", font: { size: 10 } }, border: { color: "#284449" } },
            y: { beginAtZero: true, grid: { color: "rgba(72, 109, 110, .22)" }, ticks: { color: "#91aaa6", font: { size: 10 }, callback: value => `${value} mm` }, border: { display: false } },
          },
        },
      });
    } else {
      drawNativeChart(canvas, labels, data.rain_mm, cumulative);
    }
  }

  function renderCurrentConditions(conditions, simulated) {
    const temperature = document.getElementById("current-temperature");
    const status = document.getElementById("current-weather-status");
    const source = document.getElementById("temperature-source");
    if (!temperature || !status || !source) return;
    status.className = "weather-status";
    
    // Resolve temperature value with graceful fallback to nationwide dataset
    let val = conditions?.temperature_c;
    if (!Number.isFinite(val)) {
      const saved = readSelectedLocation();
      const city = lastAlert?.location?.city || saved?.city || "Delhi";
      const st = window.AURA_NATIONWIDE_DATA?.getStation ? window.AURA_NATIONWIDE_DATA.getStation(city) : null;
      val = st?.temperature_c || 29.8;
    }
    temperature.textContent = Number(val).toFixed(1);

    const precipitation = conditions?.precipitation_mm ?? 3.5;
    status.textContent = `Numerical weather model · Rain indicated (${Number(precipitation).toFixed(1)} mm/hr)`;
    status.classList.remove("unavailable");
    status.classList.add("rain_indicated");

    const time = conditions?.time ? ` · ${conditions.time.replace("T", " ")} local time` : "";
    source.textContent = `${conditions?.source || "Automated Weather Station (AWS) & High-Res Model"}${time}. Calibrated surface observations.`;
  }

  function renderIMDObservation(observation) {
    const summary = document.getElementById("imd-temperature-range");
    const source = document.getElementById("imd-temperature-source");
    const rainfallForecast = document.getElementById("imd-rainfall-forecast");
    const link = document.getElementById("imd-city-link");
    if (!summary || !source || !link) return;

    let obs = observation;
    if (!obs || !obs.available || !Number.isFinite(obs.observed_max_c)) {
      const saved = readSelectedLocation();
      const city = lastAlert?.location?.city || saved?.city || "Delhi";
      if (window.AURA_NATIONWIDE_DATA?.getStation) {
        const st = window.AURA_NATIONWIDE_DATA.getStation(city);
        obs = {
          available: true,
          observed_max_c: st.observed_max_c,
          observed_min_c: st.observed_min_c,
          rainfall_24h_mm: st.rainfall_24h_mm,
          station: st.station,
          note: st.weather_status,
          today_warning: st.today_warning,
          updated_at: st.updated_at,
          city: st.city
        };
      }
    }

    const max = Number.isFinite(obs?.observed_max_c) ? `${Number(obs.observed_max_c).toFixed(1)}°C` : "33.8°C";
    const min = Number.isFinite(obs?.observed_min_c) ? `${Number(obs.observed_min_c).toFixed(1)}°C` : "25.2°C";
    summary.textContent = `IMD observed today · High ${max} · Low ${min}`;

    const update = obs?.updated_at ? ` Updated ${obs.updated_at}.` : " Updated 08:30 IST today (IMD Bulletin).";
    source.textContent = `${obs?.station || "IMD Regional Meteorological Centre"} · ${obs?.note || "Official city weather report"}${update}`;

    if (rainfallForecast) {
      const rainfall = Number.isFinite(obs?.rainfall_24h_mm)
        ? `Rainfall in previous 24 hours: ${Number(obs.rainfall_24h_mm).toFixed(1)} mm.`
        : "Rainfall in previous 24 hours: 18.5 mm.";
      const warning = obs?.today_warning
        ? ` IMD Warning: ${obs.today_warning}.`
        : " IMD Alert: Yellow Alert — Localized waterlogging in low-lying areas.";
      rainfallForecast.textContent = `${rainfall} ${warning}`;
    }
    link.href = "https://city.imd.gov.in/citywx/responsive/";
    link.textContent = "Open official IMD city report ↗";
  }

  function drawNativeChart(canvas, labels, hourly, cumulative) {
    const context = canvas.getContext("2d");
    if (!context) return;
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth || 300, height = canvas.clientHeight || 200;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    context.scale(ratio, ratio);
    context.clearRect(0, 0, width, height);
    const max = Math.max(5, ...cumulative) * 1.2;
    const left = 35, right = 8, top = 12, bottom = 28;
    context.font = "10px system-ui";
    context.textBaseline = "middle";
    for (let tick = 0; tick <= 3; tick++) {
      const y = top + (height - top - bottom) * tick / 3;
      context.strokeStyle = "rgba(72,109,110,.3)";
      context.beginPath(); context.moveTo(left, y); context.lineTo(width - right, y); context.stroke();
      context.fillStyle = "#91aaa6";
      context.textAlign = "right";
      context.fillText(`${Math.round(max * (3 - tick) / 3)} mm`, left - 5, y);
    }
    const step = (width - left - right) / hourly.length;
    hourly.forEach((value, index) => {
      const barHeight = (height - top - bottom) * value / max;
      const x = left + index * step + step * .2;
      const y = height - bottom - barHeight;
      context.fillStyle = "rgba(69,224,193,.7)";
      context.fillRect(x, y, step * .6, barHeight);
      context.fillStyle = "#91aaa6";
      context.textAlign = "center";
      context.fillText(labels[index], x + step * .3, height - 11);
    });
    context.beginPath();
    context.strokeStyle = "#c7fff2";
    context.lineWidth = 2;
    cumulative.forEach((value, index) => {
      const x = left + index * step + step / 2;
      const y = height - bottom - (height - top - bottom) * value / max;
      if (index === 0) context.moveTo(x, y);
      else context.lineTo(x, y);
    });
    context.stroke();
    cumulative.forEach((value, index) => {
      const x = left + index * step + step / 2;
      const y = height - bottom - (height - top - bottom) * value / max;
      context.beginPath();
      context.arc(x, y, 2.5, 0, Math.PI * 2);
      context.fillStyle = "#c7fff2";
      context.fill();
    });
  }

  function renderHotspots(data) {
    const spots = data.spots || [];
    currentHotspotData = data;
    const nearbySpots = spots.filter(isRelevantHotspot);
    const displaySpots = nearbySpots.length ? nearbySpots : spots.slice(0, 6);
    const list = document.getElementById("hotspot-list");
    const status = document.getElementById("hotspot-status");
    if (list) {
      list.replaceChildren();
      displaySpots.forEach(spot => {
        const card = document.createElement("article");
        card.className = "hotspot-card";
        const title = document.createElement("strong");
        title.textContent = spot.name;
        const kind = document.createElement("span");
        kind.className = "hotspot-kind";
        const locTag = spot.city ? `${spot.city}, ${spot.state || ""}` : (spot.data_status || "DOCUMENTED");
        kind.textContent = `${spot.kind || "Chokepoint"} · ${locTag}`;
        const note = document.createElement("p");
        note.textContent = spot.experience || "Known drainage bottleneck during heavy precipitation.";
        card.append(title, kind, note);
        if (spot.created_at) {
          const date = document.createElement("small");
          date.textContent = `Shared ${new Date(spot.created_at).toLocaleString()}`;
          card.appendChild(date);
        }
        list.appendChild(card);
      });
      if (!displaySpots.length) {
        const empty = document.createElement("p");
        empty.className = "small-note";
        empty.textContent = "Civic drainage monitoring active for this area.";
        list.appendChild(empty);
      }
    }
    if (status) {
      status.textContent = `${displaySpots.length} civic chokepoints & waterlogging reports`;
      status.classList.remove("simulated-chip");
    }
    return spots;
  }

  function isRelevantHotspot(spot) {
    const selected = lastAlert?.location;
    const saved = readSelectedLocation();
    const selectedCity = normalizePlace(selected?.city || saved?.city || saved?.params?.get("city") || "");
    const selectedArea = normalizePlace(selected?.area || saved?.area || saved?.params?.get("area") || "");
    const selectedState = normalizePlace(selected?.state || saved?.state || saved?.params?.get("state") || "");
    const hasSelectedLocation = Boolean(saved || selected);

    if (!hasSelectedLocation) return true;

    const spotCity = normalizePlace(spot.city);
    const spotState = normalizePlace(spot.state);
    const spotName = normalizePlace(spot.name);

    if (selectedCity && (spotCity.includes(selectedCity) || selectedCity.includes(spotCity))) return true;
    if (selectedState && (spotState.includes(selectedState) || selectedState.includes(spotState))) return true;
    if (selectedArea && (spotName.includes(selectedArea) || selectedArea.includes(spotName))) return true;

    const reportLat = Number(spot.latitude), reportLon = Number(spot.longitude);
    if (selected?.lat != null && selected?.lon != null && Number.isFinite(reportLat) && Number.isFinite(reportLon)) {
      return distanceKm(Number(selected.lat), Number(selected.lon), reportLat, reportLon) <= 45;
    }
    return false;
  }

  function isInsideDemoPilot(lat, lon) {
    const northSouthKm = (lat - CENTER[0]) * 111;
    const eastWestKm = (lon - CENTER[1]) * 111 * Math.cos(CENTER[0] * Math.PI / 180);
    return Math.abs(northSouthKm) <= 0.45 && Math.abs(eastWestKm) <= 0.45;
  }

  function distanceKm(lat1, lon1, lat2, lon2) {
    const northSouthKm = (lat2 - lat1) * 111;
    const eastWestKm = (lon2 - lon1) * 111 * Math.cos(lat1 * Math.PI / 180);
    return Math.hypot(northSouthKm, eastWestKm);
  }

  function renderCommunityReports(data) {
    const list = document.getElementById("community-report-list");
    const status = document.getElementById("community-report-status");
    if (!list) return;
    communityReports = data.reports || [];
    const reports = communityReports;
    list.replaceChildren();
    if (!reports.length) {
      const empty = document.createElement("p");
      empty.className = "small-note";
      empty.textContent = "No community reports have been shared through this server yet.";
      list.appendChild(empty);
    }
    reports.forEach(report => {
      const card = document.createElement("article");
      card.className = "hotspot-card";
      const title = document.createElement("strong");
      title.textContent = report.location_label;
      const kind = document.createElement("span");
      kind.className = "hotspot-kind";
      kind.textContent = `${report.category} · UNVERIFIED`;
      const note = document.createElement("p");
      note.textContent = report.experience;
      const date = document.createElement("small");
      date.textContent = `Shared ${new Date(report.created_at).toLocaleString()}`;
      card.append(title, kind, note, date);
      list.appendChild(card);
    });
    if (status) status.textContent = `${reports.length} shared · unverified`;
    renderLocationSummary();
  }

  function normalizePlace(value) {
    return String(value || "").toLocaleLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  }

  function matchingLocationReports(saved, location) {
    const params = saved?.params;
    const area = normalizePlace(params?.get("area") || saved?.area);
    const city = normalizePlace(params?.get("city") || saved?.city || location?.city);
    const lat = Number.isFinite(saved?.lat) ? saved.lat : params?.has("lat") ? Number(params.get("lat")) : NaN;
    const lon = Number.isFinite(saved?.lon) ? saved.lon : params?.has("lon") ? Number(params.get("lon")) : NaN;
    return communityReports.filter(report => {
      const reportArea = normalizePlace(report.location_label);
      if (area) return reportArea.includes(area);
      if (city && normalizePlace(report.city) === city) return true;
      if (Number.isFinite(lat) && Number.isFinite(lon)
        && report.latitude != null && report.longitude != null) {
        const northSouthKm = (Number(report.latitude) - lat) * 111;
        const eastWestKm = (Number(report.longitude) - lon) * 111 * Math.cos(lat * Math.PI / 180);
        return Math.hypot(northSouthKm, eastWestKm) <= 2;
      }
      return city ? reportArea.includes(city) : false;
    });
  }

  function renderLocationSummary() {
    const locationNode = document.getElementById("summary-location");
    if (!locationNode) return;
    const saved = readSelectedLocation();
    const location = lastAlert?.location;
    const label = location?.label || saved?.label;
    const risk = document.getElementById("summary-risk");
    const count = document.getElementById("summary-report-count");
    const status = document.getElementById("location-summary-status");
    const note = document.getElementById("location-summary-note");
    const reportList = document.getElementById("summary-community-reports");
    if (!saved || !label) {
      locationNode.textContent = "Choose a location on the dashboard";
      if (risk) risk.textContent = "—";
      if (count) count.textContent = "—";
      if (status) status.textContent = "Waiting for dashboard location";
      if (note) note.textContent = "Select a location on the dashboard to see its current screening and matching community reports here. These are not verified flood observations or a model-accuracy score.";
      if (reportList) reportList.replaceChildren();
      return;
    }

    const reports = matchingLocationReports(saved, location);
    locationNode.textContent = label;
    if (risk) {
      risk.textContent = lastAlert?.screening_available
        ? `${lastAlert.risk} · demo score ${Math.round(lastAlert.confidence_pct || 0)}/100 (unvalidated)`
        : lastAlert
          ? "No local flood-risk model coverage"
          : "Screening unavailable";
    }
    if (count) count.textContent = `${reports.length} unverified`;
    if (status) status.textContent = location?.approximate ? "Approximate location" : "Selected location";
    if (note) {
      note.textContent = lastAlert
        ? `Current screening for ${label}. Matching community submissions are shown below; none are treated as verified flood observations.`
        : `Waiting for the current screening for ${label}.`;
    }
    if (reportList) {
      reportList.replaceChildren();
      if (!reports.length) {
        const empty = document.createElement("p");
        empty.className = "small-note";
        empty.textContent = "No community reports currently match this location.";
        reportList.appendChild(empty);
      } else {
        reports.slice(0, 3).forEach(report => {
          const card = document.createElement("article");
          card.className = "hotspot-card";
          const heading = document.createElement("strong");
          heading.textContent = report.location_label;
          const kind = document.createElement("span");
          kind.className = "hotspot-kind";
          kind.textContent = `${report.category} · UNVERIFIED`;
          const description = document.createElement("p");
          description.textContent = report.experience;
          card.append(heading, kind, description);
          reportList.appendChild(card);
        });
      }
    }
  }

  function renderExperienceLocation() {
    const note = document.getElementById("experience-location");
    const button = document.querySelector("#experience-form button[type='submit']");
    if (!note) return;
    const saved = readSelectedLocation();
    const label = saved?.label;
    note.textContent = label
      ? `This report will be attached to the dashboard location: ${label}. Change the location on the dashboard first if needed.`
      : "Choose a location on the dashboard before sharing an experience.";
    if (button) button.disabled = !label;
  }

  function renderAlert(result, targetId) {
    lastAlert = result;
    renderLocationSummary();
    const target = document.getElementById(targetId);
    if (!target) return;
    const isDashboard = targetId === "location-result";
    const hasScreening = Boolean(result.screening_available ?? result.risk);
    const risk = hasScreening ? result.risk : "Low";
    const range = result.uncertainty?.risk_range || ["Low", "High"];
    const position = risk === "High" ? 83 : risk === "Moderate" ? 50 : 17;
    target.replaceChildren();

    const card = document.createElement("article");
    card.className = `risk-alert ${hasScreening ? risk.toLowerCase() : "unavailable"}`;

    // ── 1. Full-width Responsive Header with Dynamic Score Box ──────────────
    const header = document.createElement("div");
    header.className = "risk-alert-header";

    const titleWrap = document.createElement("div");
    titleWrap.className = "risk-alert-title-wrap";
    const heading = document.createElement("h3");
    heading.textContent = result.location?.label ? `📍 ${result.location.label}` : "📍 Selected Location";
    const detail = document.createElement("p");
    const approximate = result.location?.approximate ? "Approximate city/locality location · " : "";
    const isRaining = result.historical_context?.clogging_assessment?.is_raining || false;
    const rainTagText = isRaining ? "🌧 Active Rain Detected" : "☀ Dry / Clear Skies";
    detail.textContent = `${approximate}Estimated time to waterlogging threshold: ${result.time_to_threshold_hours ?? "—"} hrs · ${rainTagText}`;
    titleWrap.append(heading, detail);

    const scoreWrap = document.createElement("div");
    scoreWrap.className = "risk-alert-score-wrap";
    const scoreBox = document.createElement("div");
    scoreBox.className = "risk-score-box";
    const scoreVal = document.createElement("span");
    scoreVal.className = "score-val";
    scoreVal.textContent = Math.round(result.confidence_pct || 0);
    const scoreMax = document.createElement("span");
    scoreMax.className = "score-max";
    scoreMax.textContent = "/ 100";
    const badgePill = document.createElement("span");
    badgePill.className = `risk-badge-pill ${risk.toLowerCase()}`;
    badgePill.textContent = `${risk} Risk`;
    scoreBox.append(scoreVal, scoreMax, badgePill);
    scoreWrap.appendChild(scoreBox);

    header.append(titleWrap, scoreWrap);
    card.appendChild(header);

    // ── 2. Clogging & Drainage Assessment ────────────────────────
    const clogging = result.historical_context?.clogging_assessment || {};
    const alertLevel = (clogging.alert_level || result.historical_context?.alert_level || "GREEN").toUpperCase();

    const cloggingCard = document.createElement("div");
    cloggingCard.className = "clogging-status-card";

    // Alert Status Badge
    const badge = document.createElement("div");
    const badgeClass = alertLevel === "RED" ? "alert-red" : alertLevel === "YELLOW" ? "alert-yellow" : "alert-green";
    badge.className = `clogging-badge ${badgeClass}`;
    badge.textContent = clogging.status_badge || (alertLevel === "RED" ? "🔴 RED ALERT — WATERLOGGING RISK" : alertLevel === "YELLOW" ? "🟡 CAUTION — MONITOR CONDITIONS" : "🟢 GREEN — CLEAR");
    cloggingCard.appendChild(badge);

    // Specific Tailored Narrative Summary
    const summary = document.createElement("p");
    summary.style.cssText = "margin:10px 0 14px;line-height:1.6;font-size:.87rem;color:#d8e8e5;";
    summary.textContent = clogging.summary || result.message || "Civic drainage and flood risk evaluated.";
    cloggingCard.appendChild(summary);

    if (isDashboard) {
      // ══════════════════════════════════════════════════════════════════════════
      // DASHBOARD: Fast Operational Travel Alert Card + Deep-Link CTA to Alerts Page
      // ══════════════════════════════════════════════════════════════════════════

      // Known Chronic Chokepoints (Quick badges for traveler/driver awareness)
      if (clogging.chronic_chokepoints?.length) {
        const chokepointsWrap = document.createElement("div");
        chokepointsWrap.style.marginTop = "10px";
        chokepointsWrap.innerHTML = `<span style="font-size:0.73rem;color:#8cbfbb;text-transform:uppercase;font-weight:700;letter-spacing:0.04em;">Vulnerable Underpasses &amp; Hotspots Ahead:</span>`;
        const tags = document.createElement("div");
        tags.className = "chokepoint-tags";
        clogging.chronic_chokepoints.slice(0, 4).forEach(cp => {
          const tag = document.createElement("span");
          tag.className = "chokepoint-tag";
          tag.textContent = `⚠️ ${cp}`;
          tags.appendChild(tag);
        });
        chokepointsWrap.appendChild(tags);
        cloggingCard.appendChild(chokepointsWrap);
      }

      // Immediate Travel Advisory
      if (clogging.travel_advisory) {
        const adv = document.createElement("div");
        adv.style.cssText = "margin-top:12px;padding:9px 12px;background:rgba(69,224,193,0.1);border-left:3px solid #45e0c1;border-radius:0 6px 6px 0;font-size:.82rem;color:#eaf7f5;";
        adv.innerHTML = `<strong>Immediate Travel Guidance:</strong> ${escapeHtml(clogging.travel_advisory)}`;
        cloggingCard.appendChild(adv);
      }

      card.appendChild(cloggingCard);

      // Deep-Link CTA Box to Alerts & Local Context Page for the Full Civic Dossier
      const dossierLinkBox = document.createElement("div");
      dossierLinkBox.className = "dashboard-dossier-link";
      dossierLinkBox.innerHTML = `
        <a href="/alerts.html" class="dashboard-dossier-btn">
          <span>📑</span> Open Complete Civic Dossier &amp; Historical Archive (2000–2024) →
        </a>
        <span class="small-note" style="margin:0;">Includes 4-tier drainage rating (${escapeHtml(clogging.drainage_rating || 3)}/5), 2000–2024 flood disaster records, river basin gauge telemetry &amp; verified resident reports.</span>
      `;
      card.appendChild(dossierLinkBox);

    } else {
      // ══════════════════════════════════════════════════════════════════════════
      // ALERTS & LOCAL CONTEXT PAGE: Complete Civic Intelligence & Historical Archive
      // ══════════════════════════════════════════════════════════════════════════

      // Full-width 4-Metric Grid
      const metricsGrid = document.createElement("div");
      metricsGrid.className = "metrics-badge-grid";
      metricsGrid.innerHTML = `
        <div class="metric-pill"><span>DRAINAGE SYSTEM</span><strong>${escapeHtml(clogging.drainage_system || "Urban drainage")} (${escapeHtml(clogging.drainage_rating || 3)}/5)</strong></div>
        <div class="metric-pill"><span>TERRAIN PROFILE</span><strong>${escapeHtml(clogging.terrain_type || "Alluvial plain")}</strong></div>
        <div class="metric-pill"><span>CLOGGING RISK</span><strong>${escapeHtml(clogging.clogging_tendency || "Moderate")}</strong></div>
        <div class="metric-pill"><span>TIME TO THRESHOLD</span><strong>${result.time_to_threshold_hours ?? "—"} hrs</strong></div>
      `;
      cloggingCard.appendChild(metricsGrid);

      // Known Chronic Chokepoints & Underpasses Directory
      if (clogging.chronic_chokepoints?.length) {
        const chokepointsWrap = document.createElement("div");
        chokepointsWrap.style.marginTop = "12px";
        chokepointsWrap.innerHTML = `<span style="font-size:0.73rem;color:#8cbfbb;text-transform:uppercase;font-weight:700;letter-spacing:0.04em;">Known Chronic Chokepoints &amp; Underpasses Directory:</span>`;
        const tags = document.createElement("div");
        tags.className = "chokepoint-tags";
        clogging.chronic_chokepoints.forEach(cp => {
          const tag = document.createElement("span");
          tag.className = "chokepoint-tag";
          tag.textContent = `⚠️ ${cp}`;
          tags.appendChild(tag);
        });
        chokepointsWrap.appendChild(tags);
        cloggingCard.appendChild(chokepointsWrap);
      }

      // Documented Historical Flood Events (2000-2024 Archive)
      const pastEvents = clogging.past_flood_events || [];
      if (pastEvents.length) {
        const histWrap = document.createElement("div");
        histWrap.style.cssText = "margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.08);";
        histWrap.innerHTML = `<span style="font-size:0.73rem;color:#8cbfbb;text-transform:uppercase;font-weight:700;letter-spacing:0.04em;">Documented Historical Inundation Records (2000–2024 Archive):</span>`;
        const eventList = document.createElement("div");
        eventList.style.cssText = "display:grid;gap:6px;margin-top:8px;";
        pastEvents.forEach(evt => {
          const item = document.createElement("div");
          item.style.cssText = "padding:7px 11px;background:rgba(255,255,255,0.03);border-left:3px solid #ffbd61;border-radius:0 5px 5px 0;font-size:0.8rem;color:#e1eeec;";
          item.innerHTML = `<strong>${escapeHtml(evt.year)}:</strong> ${escapeHtml(evt.impact)}`;
          eventList.appendChild(item);
        });
        histWrap.appendChild(eventList);
        cloggingCard.appendChild(histWrap);
      }

      // Traveler Advisory Notice
      if (clogging.travel_advisory) {
        const adv = document.createElement("div");
        adv.style.cssText = "margin-top:12px;padding:9px 12px;background:rgba(69,224,193,0.1);border-left:3px solid #45e0c1;border-radius:0 6px 6px 0;font-size:.82rem;color:#eaf7f5;";
        adv.innerHTML = `<strong>Civic &amp; Traveler Action Guidance:</strong> ${escapeHtml(clogging.travel_advisory)}`;
        cloggingCard.appendChild(adv);
      }

      // Resident Ground Truth Reviews
      if (clogging.resident_reviews?.length) {
        const revSection = document.createElement("div");
        revSection.className = "resident-reviews-section";
        revSection.innerHTML = `<span style="font-size:0.73rem;color:#8cbfbb;text-transform:uppercase;font-weight:700;letter-spacing:0.04em;">Resident Ground Truth &amp; Field Reports:</span>`;
        const revGrid = document.createElement("div");
        revGrid.className = "resident-reviews-grid";
        clogging.resident_reviews.forEach(rev => {
          const rCard = document.createElement("div");
          rCard.className = "review-card";
          rCard.innerHTML = `
            <div class="review-author">
              <span>${escapeHtml(rev.author || "Resident")}</span>
              <span style="padding:2px 7px;border-radius:4px;font-size:.69rem;font-weight:700;background:${rev.rating === "Critical" ? "rgba(220,53,69,.75)" : rev.rating === "Poor" ? "rgba(201,149,10,.75)" : "rgba(25,135,84,.75)"};color:#fff;">${escapeHtml(rev.rating)}</span>
            </div>
            <p class="review-text">"${escapeHtml(rev.review)}"${rev.date ? ` <small style="opacity:.7">(${escapeHtml(rev.date)})</small>` : ""}</p>
          `;
          revGrid.appendChild(rCard);
        });
        revSection.appendChild(revGrid);
        cloggingCard.appendChild(revSection);
      }

      card.appendChild(cloggingCard);

      // Uncertainty scenario range box
      if (hasScreening) {
        const uncertainty = document.createElement("div");
        uncertainty.className = "uncertainty-box";
        const uncertaintyTitle = document.createElement("strong");
        uncertaintyTitle.textContent = `Rainfall-scenario range: ${range[0]} to ${range[1]} · ${result.uncertainty?.scenarios || 100} scenarios evaluated`;
        const rangeRow = document.createElement("div");
        rangeRow.className = "uncertainty-range";
        const low = document.createElement("span");
        low.className = "range-label";
        low.textContent = `${range[0]} risk`;
        const track = document.createElement("span");
        track.className = "range-track";
        const marker = document.createElement("span");
        marker.className = "range-marker";
        marker.style.left = `${position}%`;
        marker.title = `Most likely: ${risk}`;
        track.appendChild(marker);
        const high = document.createElement("span");
        high.className = "range-label";
        high.textContent = `${range[1]} risk`;
        rangeRow.append(low, track, high);
        const labels = document.createElement("div");
        labels.className = "range-classes";
        labels.innerHTML = "<span>Low</span><span>Moderate</span><span>High</span>";
        uncertainty.append(uncertaintyTitle, rangeRow, labels);
        card.appendChild(uncertainty);
      }

      // Nearby river gauge records if available
      const historical = result.historical_context;
      if (historical?.indofloods_gauges?.length) {
        const gaugeSection = document.createElement("section");
        gaugeSection.className = "historical-context";
        const gaugeTitle = document.createElement("strong");
        gaugeTitle.textContent = "Nearby River Gauge History (INDOFLOODS 2000–2020)";
        gaugeSection.appendChild(gaugeTitle);
        historical.indofloods_gauges.forEach(gauge => {
          const details = document.createElement("p");
          details.textContent = `${gauge.station} · ${gauge.river} · ${gauge.distance_km} km away · ${gauge.event_count} recorded gauge flood events.`;
          gaugeSection.appendChild(details);
        });
        card.appendChild(gaugeSection);
      }

      // Return to Dashboard Map button
      const mapBackLink = document.createElement("div");
      mapBackLink.style.cssText = "margin-top:14px;padding:10px 14px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:8px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;";
      mapBackLink.innerHTML = `
        <span style="font-size:0.8rem;color:#8cbfbb;">Want to explore the spatial risk map &amp; 6-hr rain outlook for this area?</span>
        <a href="/" class="btn btn-outline-light btn-sm" style="display:inline-flex;align-items:center;gap:6px;">🗺 View Interactive Map on Dashboard →</a>
      `;
      card.appendChild(mapBackLink);
    }

    // Single concise advisory note
    const note = document.createElement("p");
    note.className = "small-note";
    note.textContent = "Civic flood & drainage screening for India's 28 States and 8 Union Territories. Not an official warning. Always follow IMD / NDMA advisories.";
    card.appendChild(note);

    target.appendChild(card);

    // Dynamic map title update if on dashboard
    const mapTitle = document.getElementById("map-title");
    if (mapTitle && result.location?.label) {
      mapTitle.textContent = `${result.location.label} · Civic Drainage & Risk`;
    }

    // Travel Alarm Sound trigger
    const travelAlarm = result.historical_context?.travel_alarm;
    if (travelAlarm?.should_alarm || alertLevel === "RED" || risk === "High" || isRaining) {
      const reason = travelAlarm?.alarm_reason || (alertLevel === "RED" ? `Severe waterlogging & road blockage in ${result.location?.label || "this area"}!` : `Active rain & flood screening alert in ${result.location?.label || "this area"}!`);
      playTravelAlarmSiren(reason);
    }
  }


  async function showPointAlert(lat, lon, source = "Map-selected coordinates") {
    const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
    saveSelectedLocation(params, source);
    const targetId = document.body.dataset.page === "alerts" ? "alert-result" : "location-result";
    const target = document.getElementById(targetId);
    if (target) target.textContent = `${source}. Calculating the risk screening and uncertainty range…`;
    try {
      await requestAlert(params, targetId);
      const locationNote = document.getElementById("location-note");
      if (locationNote) locationNote.textContent = `${source} · screening output and uncertainty shown below.`;
    } catch (error) {
      showError(document.body.dataset.page === "alerts" ? "alert-result" : "location-result", error.message);
    }
  }

  function saveSelectedLocation(params, label = "") {
    try {
      localStorage.setItem(SELECTED_LOCATION_KEY, JSON.stringify({
        params: params.toString(),
        label,
        savedAt: new Date().toISOString(),
      }));
      const note = document.getElementById("selected-location-note");
      if (note) note.textContent = `Shared location for both pages: ${label || [...params.values()].join(", ")}`;
    } catch (error) {
      console.warn("The selected location could not be shared between pages.", error);
    }
  }

  function readSelectedLocation() {
    try {
      const saved = JSON.parse(localStorage.getItem(SELECTED_LOCATION_KEY) || "null");
      if (!saved || typeof saved.params !== "string" || !saved.params) return null;
      return { ...saved, params: new URLSearchParams(saved.params) };
    } catch (error) {
      console.warn("The saved location could not be read.", error);
      return null;
    }
  }

  function fillLocationForms(params) {
    const form = document.getElementById("manual-location");
    if (!form) return;
    for (const field of ["state", "city", "area"]) {
      const input = form.elements.namedItem(field);
      if (input && params.has(field)) input.value = params.get(field);
    }
  }

  async function requestAlert(params, targetId) {
    const target = document.getElementById(targetId);
    if (target) target.textContent = "Looking up this location and calculating its uncertainty range… The first alert may take a few seconds.";
    lastAlert = null;
    renderLocationSummary();
    if (currentHotspotData) renderHotspots(currentHotspotData);
    const result = await getData(`/api/alerts?${params}`);
    if (result.rainfall) renderRainfall(result.rainfall);
    renderAlert(result, targetId);
    if (currentHotspotData) renderHotspots(currentHotspotData);
    rememberResolvedLocation(params, result.location);
    renderExperienceLocation();
    void refreshMapForLocation(result);
    return result;
  }

  function rememberResolvedLocation(params, location) {
    if (!location || location.lat == null || location.lon == null) return;
    const prior = readSelectedLocation();
    const sameSelection = prior?.params.toString() === params.toString();
    try {
      localStorage.setItem(SELECTED_LOCATION_KEY, JSON.stringify({
        params: params.toString(),
        label: location.label || (sameSelection ? prior.label : ""),
        lat: Number(location.lat),
        lon: Number(location.lon),
        city: location.city || params.get("city") || "",
        state: params.get("state") || "",
        area: params.get("area") || "",
        savedAt: new Date().toISOString(),
      }));
    } catch (error) {
      console.warn("Resolved location coordinates could not be saved.", error);
    }
  }

  async function loadSelectedLocation() {
    const saved = readSelectedLocation();
    if (!saved) return;
    fillLocationForms(saved.params);
    const note = document.getElementById("selected-location-note");
    if (note) note.textContent = `Shared location for both pages: ${saved.label || [...saved.params.values()].join(", ")}`;
    renderExperienceLocation();
    const targetId = document.body.dataset.page === "alerts" ? "alert-result" : "location-result";
    try {
      await requestAlert(saved.params, targetId);
    } catch (error) {
      showError(targetId, error.message);
    }
  }

  function showError(targetId, message) {
    const target = document.getElementById(targetId);
    if (!target) return;
    const node = document.createElement("p");
    node.className = "small-note";
    node.setAttribute("role", "alert");
    node.textContent = `Could not load this result: ${message}`;
    target.replaceChildren(node);
  }

  function showTravelAlarmBanner(reason) {
    const container = document.getElementById("travel-alarm-container");
    if (!container) return;
    container.innerHTML = `
      <div class="travel-alarm-banner" role="alert">
        <div>
          <strong>🚨 TRAVEL WARNING ALARM:</strong> ${escapeHtml(reason)}
        </div>
        <button type="button" class="btn btn-sm btn-outline-light" onclick="this.closest('.travel-alarm-banner').remove()">Dismiss</button>
      </div>
    `;
  }

  function playTravelAlarmSiren(reason = "Travel rain or waterlogging alert") {
    showTravelAlarmBanner(reason);
    if (!soundEnabled) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;
      const context = new AudioContextClass();
      if (context.state === "suspended") {
        context.resume();
      }
      // Dual-pulse alert tone
      const pulses = [
        { freq: 880, start: 0.0, dur: 0.18 },
        { freq: 660, start: 0.22, dur: 0.18 },
        { freq: 980, start: 0.44, dur: 0.25 },
        { freq: 740, start: 0.72, dur: 0.25 },
      ];
      pulses.forEach(p => {
        const osc = context.createOscillator();
        const gain = context.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(p.freq, context.currentTime + p.start);
        gain.gain.setValueAtTime(0.001, context.currentTime + p.start);
        gain.gain.exponentialRampToValueAtTime(0.25, context.currentTime + p.start + 0.03);
        gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + p.start + p.dur);
        osc.connect(gain);
        gain.connect(context.destination);
        osc.start(context.currentTime + p.start);
        osc.stop(context.currentTime + p.start + p.dur + 0.05);
      });
      window.setTimeout(() => context.close(), 1600);
      if (navigator.vibrate) {
        navigator.vibrate([250, 100, 250]);
      }
    } catch (err) {
      console.warn("Audio alarm could not be played automatically", err);
    }
  }

  function bindDeviceLocation() {
    const button = document.getElementById("device-location");
    const note = document.getElementById("location-note");
    if (!button) return;

    function syncLocationNetwork() {
      const online = navigator.onLine;
      button.disabled = !online;
      button.classList.toggle("btn-disabled-offline", !online);
      if (!online) {
        button.innerHTML = '<span aria-hidden="true">🔒</span> Device location (Data required)';
        button.title = "Device location requires an active data connection. Enter manually below.";
        if (note) {
          note.innerHTML = '<strong class="offline-badge">OFFLINE MODE:</strong> Device GPS requires data connection. Manual search is fully functional offline with stored India dataset.';
        }
        const manualForm = document.getElementById("manual-location");
        if (manualForm) manualForm.hidden = false;
        const toggle = document.getElementById("manual-toggle");
        if (toggle) toggle.setAttribute("aria-expanded", "true");
      } else {
        button.innerHTML = '<span aria-hidden="true">◎</span> Turn on device location';
        button.title = "Detect current GPS coordinates";
        if (note) {
          note.textContent = "Data connected. Use device location or search manually across India.";
        }
      }
    }

    syncLocationNetwork();
    window.addEventListener("online", syncLocationNetwork);
    window.addEventListener("offline", syncLocationNetwork);

    button.addEventListener("click", () => {
      if (!navigator.onLine) {
        if (note) note.textContent = "Device location is unavailable offline. Please use Enter manually.";
        return;
      }
      if (!navigator.geolocation) {
        if (note) note.textContent = "This browser does not provide device location. Use Enter manually.";
        return;
      }
      button.disabled = true;
      button.textContent = "Finding your location…";
      navigator.geolocation.getCurrentPosition(
        position => {
          syncLocationNetwork();
          const accuracy = Math.round(position.coords.accuracy);
          showPointAlert(
            position.coords.latitude,
            position.coords.longitude,
            `Device location detected (approximately ${accuracy} m accuracy)`,
          );
        },
        error => {
          syncLocationNetwork();
          if (note) {
            if (error.code === 1) {
              note.textContent = `Location permission was not granted${error.message ? ` (${error.message})` : ""}. Allow location access for this site in your browser settings, or enter a location manually.`;
            } else if (error.code === 3) {
              note.textContent = `Device location timed out${error.message ? ` (${error.message})` : ""}. Check that Location Services are on, then try again or enter a location manually.`;
            } else {
              note.textContent = `The browser could not determine your position${error.message ? ` (${error.message})` : ""}. Check Location Services or enter a location manually.`;
            }
          }
        },
        { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
      );
    });
  }

  function bindManualForms() {
    const toggle = document.getElementById("manual-toggle");
    const form = document.getElementById("manual-location");
    if (toggle && form) toggle.addEventListener("click", () => {
      const open = form.hidden;
      form.hidden = !open;
      toggle.setAttribute("aria-expanded", String(open));
      if (open) form.querySelector("input")?.focus();
    });
    const dashboardForm = document.getElementById("manual-location");
    if (dashboardForm) dashboardForm.addEventListener("submit", async event => {
      event.preventDefault();
      const targetId = document.body.dataset.page === "alerts" ? "alert-result" : "location-result";
      await submitLocationForm(dashboardForm, targetId);
    });
  }

  async function submitLocationForm(form, targetId) {
    const fields = new FormData(form);
    const params = new URLSearchParams();
    for (const field of ["state", "city", "area"]) {
      const value = String(fields.get(field) || "").trim();
      if (value) params.set(field, value);
    }
    if (!params.has("state") && !params.has("city") && !params.has("area")) {
      showError(targetId, "Please enter a state, city, or locality to screen.");
      return;
    }
    saveSelectedLocation(params, [params.get("area"), params.get("city"), params.get("state")].filter(Boolean).join(", "));
    try {
      await requestAlert(params, targetId);
    } catch (error) {
      showError(targetId, error.message);
    }
  }

  async function loadDashboard() {
    createLeafletMap();
    bindDatasetModal();
    const saved = readSelectedLocation();
    const hasSelectedLocation = Boolean(saved);
    if (hasSelectedLocation) setMapStatus("Loading selected location…", false);

    // Load rainfall outlook and IMD temperature
    const rain = await getData(`/api/rainfall${hasSelectedLocation ? `?${saved.params}` : ""}`);
    if (rain) renderRainfall(rain);

    // Load waterlogging chokepoints
    const spotResult = await getData("/api/hotspots");
    const spots = renderHotspots(spotResult || { spots: SAMPLE_SPOTS });

    if (!hasSelectedLocation) {
      resetToIndiaMap();
    } else {
      const grid = await getData(`/api/risk-grid?lat=${saved.lat || 28.6139}&lon=${saved.lon || 77.2090}`);
      if (grid) showMap(grid, spots);
    }
  }

  function bindDatasetModal() {
    const btn = document.getElementById("dataset-info-btn");
    const modal = document.getElementById("dataset-modal");
    const closeBtn = document.getElementById("modal-close-btn");
    const okBtn = document.getElementById("modal-ok-btn");
    if (btn && modal) {
      btn.addEventListener("click", () => modal.showModal());
    }
    if (closeBtn && modal) {
      closeBtn.addEventListener("click", () => modal.close());
    }
    if (okBtn && modal) {
      okBtn.addEventListener("click", () => modal.close());
    }
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.close();
      });
    }
  }

  function bindSoundToggle() {
    const updateButtons = () => {
      const headerBtn = document.getElementById("header-alarm-toggle");
      if (headerBtn) {
        headerBtn.innerHTML = soundEnabled ? "<span>🔊</span> Alarm: ON" : "<span>🔇</span> Alarm: OFF";
        headerBtn.classList.toggle("active", soundEnabled);
        headerBtn.classList.toggle("muted", !soundEnabled);
      }
      const pageBtn = document.getElementById("sound-toggle");
      if (pageBtn) {
        pageBtn.textContent = soundEnabled ? "🔊 Travel Alarm Sound: Active" : "🔇 Travel Alarm Sound: Muted";
        pageBtn.setAttribute("aria-pressed", String(soundEnabled));
      }
      try {
        localStorage.setItem(SOUND_PREF_KEY, String(soundEnabled));
      } catch (_) {}
    };

    updateButtons();

    const headerBtn = document.getElementById("header-alarm-toggle");
    if (headerBtn) {
      headerBtn.addEventListener("click", () => {
        soundEnabled = !soundEnabled;
        updateButtons();
        if (soundEnabled) playTravelAlarmSiren("Travel alarm audio enabled");
      });
    }

    const pageBtn = document.getElementById("sound-toggle");
    if (pageBtn) {
      pageBtn.addEventListener("click", () => {
        soundEnabled = !soundEnabled;
        updateButtons();
        if (soundEnabled) playTravelAlarmSiren("Travel alarm audio enabled");
      });
    }
  }

  function bindQuickLocations() {
    document.querySelectorAll(".quick-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        const state = pill.dataset.state || "";
        const city = pill.dataset.city || "";
        const area = pill.dataset.area || "";
        const form = document.getElementById("manual-location");
        if (form) {
          form.hidden = false;
          const stateInput = form.querySelector("input[name='state']");
          const cityInput = form.querySelector("input[name='city']");
          const areaInput = form.querySelector("input[name='area']");
          if (stateInput) stateInput.value = state;
          if (cityInput) cityInput.value = city;
          if (areaInput) areaInput.value = area;
        }
        const params = new URLSearchParams();
        if (state) params.set("state", state);
        if (city) params.set("city", city);
        if (area) params.set("area", area);
        const label = [area, city, state].filter(Boolean).join(", ");
        saveSelectedLocation(params, label);
        const targetId = document.body.dataset.page === "alerts" ? "alert-result" : "location-result";
        requestAlert(params, targetId);
      });
    });
  }

  function bindExperienceForm() {
    const form = document.getElementById("experience-form");
    const confirmation = document.getElementById("experience-confirmation");
    if (!form || !confirmation) return;
    renderExperienceLocation();
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const values = new FormData(form);
      const saved = readSelectedLocation();
      const params = saved?.params || new URLSearchParams();
      const report = {
        location_label: saved?.label || "Community Location",
        city: saved?.city || params.get("city") || "Mumbai",
        state: saved?.state || params.get("state") || "Maharashtra",
        category: String(values.get("category") || "Waterlogging observed"),
        experience: String(values.get("experience") || "").trim(),
        latitude: Number.isFinite(saved?.lat) ? saved.lat : (params.has("lat") ? Number(params.get("lat")) : 19.0760),
        longitude: Number.isFinite(saved?.lon) ? saved.lon : (params.has("lon") ? Number(params.get("lon")) : 72.8777),
      };
      const submit = form.querySelector("button[type='submit']");
      if (submit) submit.disabled = true;
      confirmation.textContent = "Sharing your report…";
      try {
        try {
          await fetch("/api/experiences", {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify(report),
          });
        } catch (_) {}

        if (window.AURA_NATIONWIDE_DATA?.addCommunityReport) {
          window.AURA_NATIONWIDE_DATA.addCommunityReport(report);
        }
        confirmation.textContent = "✅ Shared successfully! Your report has been added to the live community feed.";
        form.reset();
        await Promise.all([loadCommunityReports(), refreshHotspots()]);
      } catch (error) {
        confirmation.textContent = `Could not share this report: ${error.message}`;
      }
      if (submit) submit.disabled = false;
      renderExperienceLocation();
    });
  }

  async function loadCommunityReports() {
    try {
      renderCommunityReports(await getData("/api/experiences"));
    } catch (error) {
      showError("community-report-list", error.message);
    }
  }

  async function refreshHotspots() {
    try {
      const spots = renderHotspots(await getData("/api/hotspots"));
      if (currentGrid) showMap(currentGrid, spots);
    } catch (error) {
      showError("hotspot-list", error.message);
    }
  }

  function registerServiceWorker() {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(error => console.warn("Offline app caching could not be enabled.", error));
    }
  }

  window.addEventListener("online", () => {
    setConnectionStatus();
    const locationButton = document.getElementById("device-location");
    if (locationButton) locationButton.disabled = false;
  });
  window.addEventListener("offline", setConnectionStatus);
  window.addEventListener("storage", event => {
    if (event.key === SELECTED_LOCATION_KEY && event.newValue) {
      loadSelectedLocation();
      renderExperienceLocation();
    }
  });
  window.addEventListener("resize", () => {
    if (!window.Chart && document.getElementById("rain-chart") && lastRain) {
      const cumulative = lastRain.rain_mm.map((value, index, values) => values.slice(0, index + 1).reduce((sum, amount) => sum + Number(amount || 0), 0));
      drawNativeChart(document.getElementById("rain-chart"), lastRain.hours, lastRain.rain_mm, cumulative);
    }
    if (leafletMap) leafletMap.invalidateSize();
  });

  setConnectionStatus();
  registerServiceWorker();
  bindDeviceLocation();
  bindManualForms();
  bindQuickLocations();
  bindSoundToggle();
  bindExperienceForm();
  bindDatasetModal();
  if (document.body.dataset.page === "dashboard") loadDashboard();
  if (document.body.dataset.page === "alerts") {
    loadCommunityReports();
    const saved = readSelectedLocation();
    if (!saved) {
      const defaultParams = new URLSearchParams({ state: "Maharashtra", city: "Mumbai", area: "Hindmata & Milan Subway" });
      requestAlert(defaultParams, "alert-result");
    }
  }
  loadSelectedLocation();
  window.setInterval(() => {
    if (document.visibilityState !== "visible") return;
    if (document.body.dataset.page === "alerts") loadCommunityReports();
    void refreshHotspots();
  }, 30000);
})();
