/* Progressive enhancements keep the demo usable when libraries or the API are offline. */
(() => {
  "use strict";

  const CENTER = [31.6446, 74.8725];
  const CITY_POINTS = {
    amritsar: [31.634, 74.8723],
    delhi: [28.6139, 77.209],
    mumbai: [19.076, 72.8777],
    chennai: [13.0827, 80.2707],
    bengaluru: [12.9716, 77.5946],
    kolkata: [22.5726, 88.3639],
    hyderabad: [17.385, 78.4866],
    pune: [18.5204, 73.8567],
    jaipur: [26.9124, 75.7877],
    lucknow: [26.8467, 80.9462],
    kadapa: [14.4673, 78.8242],
    cuddapah: [14.4673, 78.8242],
  };
  const SAMPLE_SPOTS = [
    { id: "demo-1", name: "Ranjit Avenue low-lying road", city: "Amritsar", state: "Punjab", latitude: 31.6446, longitude: 74.8725, kind: "Waterlogging report", data_status: "SIMULATED", experience: "Illustrative resident-reported drainage concern; not verified" },
    { id: "demo-2", name: "Market road underpass", city: "Amritsar", state: "Punjab", latitude: 31.6377, longitude: 74.8792, kind: "Chokepoint", data_status: "SIMULATED", experience: "Illustrative sample chokepoint; not verified" },
    { id: "demo-3", name: "Bus stand junction", city: "Amritsar", state: "Punjab", latitude: 31.6336, longitude: 74.8762, kind: "Waterlogging report", data_status: "SIMULATED", experience: "Illustrative resident-reported waterlogging; not verified" },
  ];
  const simulatedStart = new Date(Date.now() + 330 * 60 * 1000);
  simulatedStart.setUTCMinutes(0, 0, 0);
  const SIMULATED_RAIN = {
    hours: Array.from({ length: 6 }, (_, index) => {
      const hour = new Date(simulatedStart.getTime() + index * 60 * 60 * 1000).getUTCHours();
      return `${String(hour).padStart(2, "0")}:00`;
    }),
    rain_mm: [1.2, 3.8, 8.4, 12, 7.1, 2.6],
    source: "SIMULATED sample forecast; live weather source unavailable",
    simulated: true,
    data_status: "SIMULATED",
    total_mm: 35.1,
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
    element.textContent = offline ? "Offline · demo data" : "Online · source varies";
    element.classList.toggle("offline", offline);
  }

  function fallbackAlert(params) {
    const city = (params.get("city") || "").trim();
    const area = (params.get("area") || "").trim();
    const hasCoordinates = params.has("lat") && params.has("lon");
    const unresolved = Boolean(city && !CITY_POINTS[city.toLowerCase()] && !hasCoordinates);
    const lat = Number(params.get("lat")) || (CITY_POINTS[city.toLowerCase()] || CENTER)[0];
    const lon = Number(params.get("lon")) || (CITY_POINTS[city.toLowerCase()] || CENTER)[1];
    const ranjit = !unresolved && (area.toLowerCase().includes("ranjit") || Math.hypot(lat - CENTER[0], (lon - CENTER[1]) * Math.cos(lat * Math.PI / 180)) < 0.0014);
    const enteredLocation = [area, city, params.get("state")].filter(Boolean).join(", ") || "Approximate selected area";
    return {
      location: {
        label: unresolved ? `${enteredLocation} (not geocoded; Amritsar demo coordinates only)` : enteredLocation,
        lat: unresolved ? null : lat,
        lon: unresolved ? null : lon,
        approximate: true,
        geocoded: !unresolved,
      },
        risk: ranjit ? "High" : null,
        screening_available: ranjit,
        time_to_threshold_hours: ranjit ? 1.4 : null,
        confidence_pct: ranjit ? 54 : null,
        uncertainty: ranjit ? { risk_range: ["Moderate", "High"], scenarios: 100, method: "Offline sample range; no live model request" } : null,
        rainfall: SIMULATED_RAIN,
        data_status: { forecast: "SIMULATED", terrain: "SIMULATED" },
        message: ranjit
          ? "SIMULATED offline Amritsar pilot only; not validated against observed floods. Current flooding and road access are not confirmed."
          : "Offline mode has no local flood-risk model coverage for this location. Current flooding and road access are not confirmed.",
        notice: "SIMULATED OFFLINE DEMO. Not an official forecast or emergency warning.",
    };
  }

  function localRiskGrid() {
    const minLon = CENTER[1] - 0.0045, maxLon = CENTER[1] + 0.0045;
    const minLat = CENTER[0] - 0.0037, maxLat = CENTER[0] + 0.0037;
    const features = [];
    for (let row = 0; row < 8; row++) {
      for (let column = 0; column < 8; column++) {
        const west = minLon + (maxLon - minLon) * column / 8;
        const east = minLon + (maxLon - minLon) * (column + 1) / 8;
        const south = minLat + (maxLat - minLat) * row / 8;
        const north = minLat + (maxLat - minLat) * (row + 1) / 8;
        const risk = row > 4 && column < 4 ? "High" : (row > 1 && column > 4 ? "Moderate" : "Low");
        features.push({
          type: "Feature",
          geometry: { type: "Polygon", coordinates: [[[west, south], [east, south], [east, north], [west, north], [west, south]]] },
          properties: { risk, confidence_pct: 38, class_range: ["Low", "High"], display_cell_m: 100 },
        });
      }
    }
    return { type: "FeatureCollection", features, data_status: "SIMULATED OFFLINE SAMPLE", forecast_source: SIMULATED_RAIN.source };
  }

  function fallbackFor(path) {
    if (path.startsWith("/api/alerts")) return fallbackAlert(new URLSearchParams(path.split("?")[1] || ""));
    if (path.startsWith("/api/rainfall")) return SIMULATED_RAIN;
    if (path === "/api/hotspots") return { spots: SAMPLE_SPOTS, data_status: "SIMULATED sample locations; not independently verified" };
    if (path.startsWith("/api/experiences")) return { reports: [], data_status: "OFFLINE · shared reports unavailable" };
    if (path.startsWith("/api/risk-grid")) {
      const params = new URLSearchParams(path.split("?")[1] || "");
      const lat = Number(params.get("lat") || CENTER[0]);
      const lon = Number(params.get("lon") || CENTER[1]);
      if (Math.abs(lat - CENTER[0]) > 0.0045 || Math.abs(lon - CENTER[1]) > 0.0045) {
        return {
          type: "FeatureCollection",
          features: [],
          data_status: "NO LOCAL TERRAIN COVERAGE",
          method: "This location is outside the limited terrain-backed demonstration area.",
        };
      }
      return localRiskGrid();
    }
    throw new Error("No offline fallback is available for this request.");
  }

  async function getData(path) {
    try {
      const response = await fetch(path, { headers: { Accept: "application/json" } });
      if (!response.ok) {
        let detail = `Request failed (${response.status}).`;
        try {
          const body = await response.json();
          if (body.detail) detail = body.detail;
        } catch (error) {
          if (!(error instanceof SyntaxError)) throw error;
        }
        throw new Error(detail);
      }
      const data = await response.json();
      try { localStorage.setItem(CACHE_PREFIX + path, JSON.stringify(data)); } catch (error) { console.warn("Could not cache demo response locally.", error); }
      return data;
    } catch (error) {
      if (!navigator.onLine || error instanceof TypeError) {
        console.warn(`Using explicitly labeled offline data for ${path}.`, error);
        try {
          const saved = localStorage.getItem(CACHE_PREFIX + path);
          if (saved) return labelOfflineData(JSON.parse(saved));
        } catch (storageError) {
          console.warn("Saved response could not be read; using the labeled offline sample.", storageError);
        }
        return fallbackFor(path);
      }
      throw error;
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
    if (data.historical_context) {
      data.historical_context.current_rain_status = "unavailable";
      data.historical_context.rain_indicated_by_live_model = false;
      data.historical_context.rain_status = "Cached offline weather; fresh live rain check is not available";
      data.historical_context.warning = false;
      data.historical_context.warning_text = null;
    }
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

  function createLeafletMap() {
    const element = document.getElementById("risk-map");
    if (!element || !window.L) return false;
    leafletMap = L.map(element, { zoomControl: true, scrollWheelZoom: false }).setView(CENTER, 15);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(leafletMap);
    mapLayer = L.geoJSON(null, {
      style: feature => ({ color: riskColor(feature.properties.risk), fillColor: riskColor(feature.properties.risk), fillOpacity: .42, weight: 1 }),
      onEachFeature: (feature, layer) => {
        const props = feature.properties || {};
        layer.bindPopup(`<strong>${props.risk || "Risk"} demo screening</strong><br>Unvalidated classifier score: ${Math.round(props.confidence_pct || 0)}/100<br>Scenario range, not a confidence interval: ${(props.class_range || ["Low", "High"]).join("–")}`);
        layer.on("click", event => {
          event.originalEvent?.stopPropagation();
          showPointAlert(event.latlng.lat, event.latlng.lng);
        });
      },
    }).addTo(leafletMap);
    markerLayer = L.layerGroup().addTo(leafletMap);
    leafletMap.on("click", event => showPointAlert(event.latlng.lat, event.latlng.lng));
    if (!navigator.onLine) {
      const badge = document.createElement("span");
      badge.className = "map-offline";
      badge.textContent = "Map tiles need internet · demo overlay shown";
      element.appendChild(badge);
    }
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
    renderCurrentConditions(data.current_conditions, data.simulated || data.data_status === "SIMULATED");
    renderIMDObservation(data.imd_observation);
    const canvas = document.getElementById("rain-chart");
    if (!canvas) return;
    const labels = data.hours.map(time => time.slice(11, 16));
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
    const value = conditions?.temperature_c;
    temperature.textContent = conditions?.available && Number.isFinite(value) ? Number(value).toFixed(1) : "--";
    if (!conditions?.available || !Number.isFinite(value)) {
      status.textContent = simulated ? "Model temperature unavailable in simulated/offline data" : "Weather-model temperature estimate unavailable";
      status.classList.add("unavailable");
      source.textContent = "No temperature is invented. See the official IMD observation map below.";
      return;
    }
    const precipitation = conditions.precipitation_mm;
    const hasPrecipitation = precipitation !== null
      && precipitation !== undefined
      && Number.isFinite(Number(precipitation));
    status.textContent = !hasPrecipitation
      ? "Numerical weather-model estimate"
      : Number(precipitation) < 0.1
        ? "Model indicates no rain for the current hour"
        : `Model indicates rain · ${Number(precipitation).toFixed(1)} mm`;
    status.classList.add(
      !hasPrecipitation ? "unavailable" : Number(precipitation) < 0.1 ? "not_indicated" : "rain_indicated",
    );
    const time = conditions.time ? ` · ${conditions.time.replace("T", " ")} local time` : "";
    const grid = conditions.model_grid_location;
    const gridText = Number.isFinite(grid?.latitude) && Number.isFinite(grid?.longitude)
      ? ` · Model grid near ${Number(grid.latitude).toFixed(3)}, ${Number(grid.longitude).toFixed(3)}${Number.isFinite(grid.elevation_m) ? ` · grid elevation ${Math.round(grid.elevation_m)} m` : ""}`
      : "";
    const locationNote = conditions.location_note ? ` ${conditions.location_note}` : "";
    source.textContent = `${conditions.source || "Open-Meteo current model"}${time}${gridText}. This is not an IMD station observation.${locationNote}`;
  }

  function renderIMDObservation(observation) {
    const summary = document.getElementById("imd-temperature-range");
    const source = document.getElementById("imd-temperature-source");
    const rainfallForecast = document.getElementById("imd-rainfall-forecast");
    const link = document.getElementById("imd-city-link");
    if (!summary || !source || !link) return;
    if (!observation?.available) {
      summary.textContent = "IMD observed high / low unavailable";
      source.textContent = observation?.source || "No IMD city report is available for this location.";
      if (rainfallForecast) rainfallForecast.textContent = `${observation?.source || "No matching IMD city station report is available."}. Check the official IMD forecast and district warnings for this area.`;
      link.href = "https://mausam.imd.gov.in/";
      link.textContent = "Open IMD forecasts & district warnings ↗";
      return;
    }
    const max = Number.isFinite(observation.observed_max_c)
      ? `${Number(observation.observed_max_c).toFixed(1)}°C`
      : "—";
    const min = Number.isFinite(observation.observed_min_c)
      ? `${Number(observation.observed_min_c).toFixed(1)}°C`
      : "—";
    summary.textContent = `IMD observed today · High ${max} · Low ${min}`;
    const update = observation.updated_at ? ` Updated ${observation.updated_at} (IMD timestamp).` : "";
    const cached = observation.offline_cache ? "CACHED OFFLINE · " : "";
    source.textContent = `${cached}${observation.station || "IMD station"} · ${observation.note || "Official city weather report."}${update}`;
    if (rainfallForecast) {
      const rainfall = Number.isFinite(observation.rainfall_24h_mm)
        ? `Rainfall in previous 24 hours (to 0830 IST): ${Number(observation.rainfall_24h_mm).toFixed(1)} mm.`
        : "Previous 24-hour rainfall: unavailable in this report.";
      const forecast = observation.today_forecast
        ? `Today's IMD forecast: ${observation.today_forecast}.`
        : "Today's IMD forecast: unavailable in this report.";
      const warning = observation.today_warning && observation.today_warning.toLowerCase() !== "no warning"
        ? ` IMD warning: ${observation.today_warning}.`
        : observation.today_warning
          ? " IMD city report: no warning listed for today."
          : "";
      rainfallForecast.textContent = `${rainfall} ${forecast}${warning}`;
    }
    link.href = observation.station_id
      ? `https://city.imd.gov.in/citywx/responsive/?id=${encodeURIComponent(observation.station_id)}`
      : "https://city.imd.gov.in/citywx/responsive/";
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
    const list = document.getElementById("hotspot-list");
    const status = document.getElementById("hotspot-status");
    if (list) {
      list.replaceChildren();
      nearbySpots.forEach(spot => {
        const card = document.createElement("article");
        card.className = "hotspot-card";
        const title = document.createElement("strong");
        title.textContent = spot.name;
        const kind = document.createElement("span");
        kind.className = "hotspot-kind";
        kind.textContent = `${spot.kind} · ${spot.data_status || "SIMULATED"}`;
        const note = document.createElement("p");
        note.textContent = spot.experience;
        card.append(title, kind, note);
        if (spot.created_at) {
          const date = document.createElement("small");
          date.textContent = `Shared ${new Date(spot.created_at).toLocaleString()}`;
          card.appendChild(date);
        }
        list.appendChild(card);
      });
      if (!nearbySpots.length) {
        const empty = document.createElement("p");
        empty.className = "small-note";
        empty.textContent = "No sample or community locations are available for the selected area. This does not mean the area is flood-free.";
        list.appendChild(empty);
      }
    }
    if (status) {
      status.textContent = nearbySpots.length
        ? `${nearbySpots.length} nearby · ${data.data_status || "SIMULATED · unverified"}`
        : "No matching locations in this list";
      status.classList.toggle("simulated-chip", String(data.data_status || "").includes("SIMULATED"));
    }
    return spots;
  }

  function isRelevantHotspot(spot) {
    const selected = lastAlert?.location;
    const saved = readSelectedLocation();
    const selectedCity = normalizePlace(selected?.city || saved?.city || saved?.params.get("city") || "");
    const selectedArea = normalizePlace(saved?.area || saved?.params.get("area") || "");
    const hasSelectedLocation = Boolean(saved || selected);
    const isDemoSpot = String(spot.data_status || "").includes("SIMULATED");

    if (isDemoSpot) {
      if (!hasSelectedLocation) return true;
      if (selected?.lat != null && selected?.lon != null) {
        return isInsideDemoPilot(Number(selected.lat), Number(selected.lon));
      }
      return selectedCity === "amritsar" && (!selectedArea || selectedArea.includes("ranjit"));
    }

    if (!hasSelectedLocation) return true;
    const reportLat = Number(spot.latitude), reportLon = Number(spot.longitude);
    if (!Number.isFinite(reportLat) || !Number.isFinite(reportLon)) return false;
    if (selected?.lat != null && selected?.lon != null) {
      return distanceKm(Number(selected.lat), Number(selected.lon), reportLat, reportLon) <= 2;
    }
    const spotCity = normalizePlace(spot.city);
    const spotState = normalizePlace(spot.state);
    const selectedState = normalizePlace(saved?.state || saved?.params.get("state") || "");
    return Boolean(selectedCity && selectedCity === spotCity && (!selectedState || selectedState === spotState));
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
    const hasScreening = Boolean(result.screening_available ?? result.risk);
    const risk = hasScreening ? result.risk : "Low";
    const range = result.uncertainty?.risk_range || ["Low", "High"];
    const position = risk === "High" ? 83 : risk === "Moderate" ? 50 : 17;
    target.replaceChildren();

    const card = document.createElement("article");
    card.className = `risk-alert ${hasScreening ? risk.toLowerCase() : "unavailable"}`;
    const info = document.createElement("div");
    const heading = document.createElement("h3");
    heading.textContent = result.location?.label || "Selected area";
    const detail = document.createElement("p");
    const approximate = result.location?.approximate ? "Approximate city/locality location · " : "";
    detail.textContent = `${approximate}Time-to-threshold estimate: ${result.time_to_threshold_hours ?? "—"} h · ${result.data_status?.forecast || "Weather model active"}`;
    info.append(heading, detail);

    const modelScore = document.createElement("div");
    modelScore.className = "risk-value";
    modelScore.textContent = `Screening score ${Math.round(result.confidence_pct || 0)}/100`;
    modelScore.setAttribute("aria-label", `Screening score ${Math.round(result.confidence_pct || 0)} out of 100`);
    card.append(info, modelScore);

    // ─────────────────────────────────────────────────────────────────────
    // CLOGGING & ALERT STATUS CARD
    // RED / YELLOW / GREEN driven by live rain + temperature.
    // "once clogged" banner shown prominently when past records exist.
    // ─────────────────────────────────────────────────────────────────────
    const clogging = result.historical_context?.clogging_assessment || {};
    const alertLevel = (clogging.alert_level || result.historical_context?.alert_level || "GREEN").toUpperCase();
    const hasPastRecords = clogging.has_past_records || result.historical_context?.has_past_records || false;
    const isRaining = clogging.is_raining || false;
    const tempC = clogging.temperature_c ?? result.historical_context?.temperature_c ?? null;

    const cloggingCard = document.createElement("div");
    cloggingCard.className = "clogging-status-card";

    const isAlertsPage = document.body.dataset.page === "alerts" || targetId === "alert-result";

    // ── 1. Weather Strip: temperature + raining indicator (omitted on second page / alerts page) ──
    if (!isAlertsPage) {
      const weatherStrip = document.createElement("div");
      weatherStrip.className = "weather-strip";
      const rainTagClass = isRaining ? "raining" : (result.historical_context?.current_rain_status === "unavailable" ? "unknown" : "dry");
      const rainLabel = isRaining ? "🌧 Raining Now" : (result.historical_context?.current_rain_status === "unavailable" ? "⚪ Rain Status Unknown" : "☀ No Active Rain");
      weatherStrip.innerHTML = `
        <span class="temp-big">${tempC !== null ? Math.round(tempC) : "--"}<span class="temp-unit">°C</span></span>
        <span class="rain-tag ${rainTagClass}">${rainLabel}</span>
        <span style="color:#8cbfbb;font-size:.75rem;flex:1;text-align:right;">Live conditions · IMD / Open-Meteo</span>
      `;
      cloggingCard.appendChild(weatherStrip);
    }

    // ── 2. Alert Badge (RED / YELLOW / GREEN) ────────────────────────────
    const badge = document.createElement("div");
    const badgeClass = alertLevel === "RED" ? "alert-red" : alertLevel === "YELLOW" ? "alert-yellow" : "alert-green";
    badge.className = `clogging-badge ${badgeClass}`;
    badge.textContent = clogging.status_badge || (alertLevel === "RED" ? "🔴 RED ALERT — WATERLOGGING RISK" : alertLevel === "YELLOW" ? "🟡 CAUTION — MONITOR CONDITIONS" : "🟢 GREEN — CLEAR");
    cloggingCard.appendChild(badge);

    // ── 3. "Once Clogged / Past Experience" highlighted banner (main mission) ──────────────
    if (hasPastRecords && !isRaining) {
      const onceBanner = document.createElement("div");
      onceBanner.className = "once-clogged-banner";
      onceBanner.innerHTML = `⚠️ <strong>PAST EXPERIENCES &amp; FLOOD EVENTS:</strong> Documented past flood events and resident observations show this area has a history of severe flooding and waterlogging. <strong>It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.</strong> Stay alert and avoid low-lying underpasses and river corridors when rain starts.`;
      cloggingCard.appendChild(onceBanner);
    } else if (hasPastRecords && isRaining) {
      const onceBanner = document.createElement("div");
      onceBanner.className = "once-clogged-banner";
      onceBanner.style.background = "linear-gradient(135deg,rgba(220,53,69,.25),rgba(180,30,40,.3))";
      onceBanner.style.borderLeftColor = "#e05050";
      onceBanner.style.color = "#ffa8a8";
      onceBanner.innerHTML = `🚨 <strong>PAST FLOODING + ACTIVE RAIN:</strong> This area has documented past flood events witnessed by residents. It once flooded and has <strong>HIGH CHANCES of being flooded or clogged RIGHT NOW</strong>. <strong>It may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too.</strong> Avoid low-lying roads, underpasses, and riverbanks.`;
      cloggingCard.appendChild(onceBanner);
    } else if (!hasPastRecords && isRaining) {
      const noBanner = document.createElement("div");
      noBanner.style.cssText = "padding:10px 12px;margin:8px 0;background:rgba(255,193,7,.1);border:1px solid rgba(255,193,7,.4);border-radius:6px;color:#ffe49a;font-size:.82rem;";
      noBanner.innerHTML = `ℹ️ <strong>ACTIVE RAIN IN THIS AREA:</strong> While no specific local historical flood record is cataloged here, <strong>it may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too</strong>. Use local judgment and watch low-lying underpasses.`;
      cloggingCard.appendChild(noBanner);
    }

    // ── 4. Summary text ──────────────────────────────────────────────────
    const summary = document.createElement("p");
    summary.style.cssText = "margin:8px 0 10px;line-height:1.5;font-size:.84rem;color:#c8d8d5;";
    summary.textContent = clogging.summary || result.message || "Drainage and road status evaluated.";
    cloggingCard.appendChild(summary);

    // ── 5. Metrics grid ──────────────────────────────────────────────────
    const metricsGrid = document.createElement("div");
    metricsGrid.className = "metrics-badge-grid";
    metricsGrid.innerHTML = `
      <div class="metric-pill"><span>DRAINAGE SYSTEM</span><strong>${escapeHtml(clogging.drainage_system || "Urban drainage")} (${escapeHtml(clogging.drainage_rating || 3)}/5)</strong></div>
      <div class="metric-pill"><span>TERRAIN PROFILE</span><strong>${escapeHtml(clogging.terrain_type || "Alluvial plain")}</strong></div>
      <div class="metric-pill"><span>CLOGGING RISK</span><strong>${escapeHtml(clogging.clogging_tendency || "Moderate")}</strong></div>
      <div class="metric-pill"><span>TIME TO THRESHOLD</span><strong>${result.time_to_threshold_hours ?? "—"} hrs</strong></div>
    `;
    cloggingCard.appendChild(metricsGrid);

    // ── 6. Chronic chokepoints ───────────────────────────────────────────
    if (clogging.chronic_chokepoints?.length) {
      const chokepointsWrap = document.createElement("div");
      chokepointsWrap.innerHTML = `<span style="font-size:0.72rem;color:#8cbfbb;text-transform:uppercase;font-weight:600;">Known Chokepoints &amp; Underpasses:</span>`;
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

    // ── 7. Traveler advisory ─────────────────────────────────────────────
    if (clogging.travel_advisory) {
      const adv = document.createElement("div");
      adv.style.cssText = "margin-top:10px;padding:8px 10px;background:rgba(69,224,193,0.1);border-left:3px solid #45e0c1;border-radius:0 4px 4px 0;font-size:.78rem;";
      adv.innerHTML = `<strong>Traveler Notice:</strong> ${escapeHtml(clogging.travel_advisory)}`;
      cloggingCard.appendChild(adv);
    }

    // ── 8. Resident reviews ──────────────────────────────────────────────
    if (clogging.resident_reviews?.length) {
      const revSection = document.createElement("div");
      revSection.className = "resident-reviews-section";
      revSection.innerHTML = `<span style="font-size:0.72rem;color:#8cbfbb;text-transform:uppercase;font-weight:600;">Resident Ground Truth &amp; Reviews:</span>`;
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

    // ── 9. No records message for entirely new/unknown locations ─────────
    if (!hasPastRecords && !isRaining) {
      const noRecord = document.createElement("div");
      noRecord.style.cssText = "margin-top:10px;padding:9px 12px;background:rgba(255,255,255,.04);border:1px dashed rgba(255,255,255,.12);border-radius:6px;color:#9ab5b2;font-size:.78rem;line-height:1.5;";
      const tempDisplay = (!isAlertsPage && tempC !== null) ? `Current temperature: <strong style="color:#e7f5f1;">${Math.round(tempC)}°C</strong> &nbsp;·&nbsp; ` : "";
      noRecord.innerHTML = `
        <strong style="color:#c8d8d5;">Civic flood &amp; drainage screening for this location.</strong><br>
        ${tempDisplay}Rainfall: <strong>${isRaining ? "🌧 Active" : "☀ None detected"}</strong><br>
        <div style="margin-top:6px;padding:6px 10px;background:rgba(255,193,7,.08);border-left:3px solid #ffc107;border-radius:0 4px 4px 0;color:#ffe49a;font-size:.78rem;">
          ℹ️ <strong>Resident Experience Advisory:</strong> While dry right now, <strong>it may be flooded as per past experiences/events witnessed by residents if it rains heavily in future too</strong>. Always monitor official IMD warnings and local drainage conditions.
        </div>
      `;
      cloggingCard.appendChild(noRecord);
    }

    card.appendChild(cloggingCard);



    // Uncertainty scenario box
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

    // Clean single advisory note (NO duplicate text!)
    const note = document.createElement("p");
    note.className = "small-note";
    note.textContent = "Civic flood & drainage screening for India's 28 States and 8 Union Territories. Not an official warning. Always follow IMD / NDMA advisories.";
    card.appendChild(note);

    const historical = result.historical_context;
    if (historical) {
      const context = document.createElement("section");
      context.className = "historical-context";
      const contextTitle = document.createElement("strong");
      contextTitle.textContent = "Documented Historical Flood & Inundation Events";
      const rainStatus = document.createElement("p");
      rainStatus.className = `travel-rain-status ${historical.current_rain_status || "unavailable"}`;
      rainStatus.setAttribute("role", "status");
      rainStatus.textContent = historical.current_rain_status === "rain_indicated"
        ? "Current rain (weather model): Indicated / Active"
        : historical.current_rain_status === "not_indicated"
          ? "Current rain (weather model): Not indicated (Dry)"
          : "Current rain (weather model): Synthesized model active";
      context.append(contextTitle, rainStatus);

      (historical.records || []).forEach(record => {
        const report = document.createElement("p");
        report.textContent = `${record.place_name} · ${record.event_date} · ${record.hazard}. ${record.reported_impact}`;
        context.appendChild(report);
      });

      const gaugeSection = document.createElement("section");
      gaugeSection.className = "indofloods-context";
      const gaugeTitle = document.createElement("strong");
      gaugeTitle.textContent = "Nearby River Gauge History (INDOFLOODS)";
      gaugeSection.appendChild(gaugeTitle);
      const gaugeRecords = historical.indofloods_gauges || [];
      if (gaugeRecords.length) {
        gaugeRecords.forEach(gauge => {
          const details = document.createElement("p");
          details.textContent = `${gauge.station} · ${gauge.river} · ${gauge.distance_km} km away · ${gauge.event_count} recorded gauge flood events in 2000–2020.`;
          gaugeSection.appendChild(details);
        });
      } else {
        const noGauge = document.createElement("p");
        noGauge.textContent = "Regional river gauge records monitored.";
        gaugeSection.appendChild(noGauge);
      }
      context.appendChild(gaugeSection);
      card.appendChild(context);
    }

    target.appendChild(card);

    // Dynamic map title update
    const mapTitle = document.getElementById("map-title");
    if (mapTitle && result.location?.label) {
      mapTitle.textContent = `${result.location.label} · Civic Drainage & Risk`;
    }

    // Travel Alarm Sound trigger (Requirement 4)
    const travelAlarm = result.historical_context?.travel_alarm;
    // isRaining is already declared above in the clogging card block
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
      await submitLocationForm(dashboardForm, "location-result");
    });
  }

  async function submitLocationForm(form, targetId) {
    const fields = new FormData(form);
    const params = new URLSearchParams();
    for (const field of ["state", "city", "area"]) {
      const value = String(fields.get(field) || "").trim();
      if (value) params.set(field, value);
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
    const hasSelectedLocation = Boolean(readSelectedLocation());
    if (hasSelectedLocation) setMapStatus("Loading selected location…", false);
    const statuses = await Promise.allSettled([
      hasSelectedLocation ? Promise.resolve(null) : getData("/api/risk-grid"),
      getData("/api/rainfall"),
      getData("/api/hotspots"),
    ]);
    const [gridResult, rainResult, spotResult] = statuses;
    let spots = SAMPLE_SPOTS;
    if (spotResult.status === "fulfilled") spots = renderHotspots(spotResult.value);
    else showError("hotspot-list", spotResult.reason.message);
    if (gridResult.status === "fulfilled" && gridResult.value) showMap(gridResult.value, spots);
    else if (gridResult.status === "rejected") setMapStatus("Map unavailable", false);
    if (rainResult.status === "fulfilled") renderRainfall(rainResult.value);
    else showError("rain-status", rainResult.reason.message);
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
      if (!saved?.label) {
        confirmation.textContent = "Select a location on the dashboard before sharing an experience.";
        return;
      }
      const params = saved.params;
      const report = {
        location_label: saved.label,
        city: saved.city || params.get("city") || "",
        state: saved.state || params.get("state") || "",
        category: String(values.get("category") || ""),
        experience: String(values.get("experience") || "").trim(),
        latitude: Number.isFinite(saved.lat) ? saved.lat : (params.has("lat") ? Number(params.get("lat")) : null),
        longitude: Number.isFinite(saved.lon) ? saved.lon : (params.has("lon") ? Number(params.get("lon")) : null),
      };
      const submit = form.querySelector("button[type='submit']");
      if (submit) submit.disabled = true;
      confirmation.textContent = "Sharing your report with this server…";
      try {
        const response = await fetch("/api/experiences", {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(report),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || `Request failed (${response.status}).`);
        confirmation.textContent = "Shared successfully. It is saved on this server and visible to other users of this site; the report remains unverified.";
        form.reset();
        await Promise.all([loadCommunityReports(), refreshHotspots()]);
      } catch (error) {
        confirmation.textContent = `Could not share this report: ${error.message}`;
      }
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
  if (document.body.dataset.page === "dashboard") loadDashboard();
  if (document.body.dataset.page === "alerts") {
    loadDashboard();
    loadCommunityReports();
  }
  loadSelectedLocation();
  window.setInterval(() => {
    if (document.visibilityState !== "visible") return;
    if (document.body.dataset.page === "alerts") loadCommunityReports();
    void refreshHotspots();
  }, 30000);
})();
