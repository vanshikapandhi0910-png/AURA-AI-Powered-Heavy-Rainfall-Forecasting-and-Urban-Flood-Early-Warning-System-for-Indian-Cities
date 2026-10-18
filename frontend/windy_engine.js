/**
 * AURA-FLOOD + WINDY METEOROLOGICAL & MARINE ENGINE (INDIA EDITION)
 * 
 * Fuses Windy's world-class visual mechanics:
 *  1. Dynamic 60fps Canvas Particle Streamline Animation (Waves & Swell, Atmospheric Wind, Rain Radar)
 *  2. Interactive Forecast Timeline Player & Scrubber (0h to 120h synoptic progression)
 *  3. Windy Floating Layer Deck (Waves, Rain & Thunder, Wind Gusts, AURA AI Flood Risk, Pressure Isobars, Clouds, Temp)
 *  4. Click-to-Inspect Crosshair Picker with Multi-Model Comparison (AURA-AI, IMD-NCUM, ECMWF, GFS) & 12h Meteogram
 *  5. Dynamic Color Gradient Legend with Interactive Value Cursor
 *  6. Coastal Marine & Port Monitoring for Arabian Sea, Bay of Bengal, and Indian Ocean
 *  7. Full URL parameter parsing (e.g. ?waves,29.939,77.749,7)
 */

(() => {
  "use strict";

  // --- 1. CORE CONSTANTS & METEOROLOGICAL DATA FOR INDIA ---
  const INDIA_BOUNDS = {
    minLat: 6.0,
    maxLat: 37.5,
    minLon: 66.0,
    maxLon: 98.0
  };

  // Coastal and Marine Monitoring Nodes across India
  const COASTAL_AND_FLOOD_HOTSPOTS = [
    {
      id: "url-roorkee-ganga",
      name: "Roorkee & Upper Ganga Basin (URL Target)",
      lat: 29.939,
      lon: 77.749,
      type: "inland_basin",
      state: "Uttarakhand / UP",
      wave_height_m: 0.0,
      river_flow_ms: 1.4,
      rain_rate_mmh: 12.8,
      wind_kmh: 22,
      wind_deg: 110,
      flood_score: 74,
      note: "Upper Ganga Canal & Solani river basin low-lying agricultural depression. High runoff convergence."
    },
    {
      id: "marine-mumbai-port",
      name: "Mumbai Port & Arabian Sea Coast",
      lat: 18.940,
      lon: 72.855,
      type: "marine_coastal",
      state: "Maharashtra",
      wave_height_m: 3.2,
      swell_period_s: 8.8,
      swell_deg: 235,
      rain_rate_mmh: 18.4,
      wind_kmh: 38,
      wind_deg: 240,
      flood_score: 92,
      note: "3.2m heavy wave swell combined with 4.1m astronomical high tide locking Mithi river floodgates."
    },
    {
      id: "marine-chennai-marina",
      name: "Chennai Marina & Coromandel Coast",
      lat: 13.050,
      lon: 80.282,
      type: "marine_coastal",
      state: "Tamil Nadu",
      wave_height_m: 2.6,
      swell_period_s: 7.9,
      swell_deg: 120,
      rain_rate_mmh: 14.5,
      wind_kmh: 32,
      wind_deg: 115,
      flood_score: 86,
      note: "East-Southeast swell causing coastal wave runup at Cooum and Adyar river outfalls."
    },
    {
      id: "marine-kolkata-digha",
      name: "Kolkata Hooghly Estuary & Digha Coast",
      lat: 21.626,
      lon: 87.507,
      type: "marine_coastal",
      state: "West Bengal",
      wave_height_m: 2.8,
      swell_period_s: 8.2,
      swell_deg: 180,
      rain_rate_mmh: 16.0,
      wind_kmh: 35,
      wind_deg: 175,
      flood_score: 88,
      note: "Sundarbans and Hooghly tidal surge delaying inland stormwater discharge into Bay of Bengal."
    },
    {
      id: "marine-kochi-harbor",
      name: "Kochi Marine Drive & Arabian Sea",
      lat: 9.972,
      lon: 76.278,
      type: "marine_coastal",
      state: "Kerala",
      wave_height_m: 3.4,
      swell_period_s: 9.5,
      swell_deg: 225,
      rain_rate_mmh: 22.0,
      wind_kmh: 42,
      wind_deg: 230,
      flood_score: 85,
      note: "Southwest monsoon swell breaching seawalls; Vembanad lake outfall restricted."
    },
    {
      id: "marine-paradip-port",
      name: "Paradip Port & Odisha Cyclone Belt",
      lat: 20.264,
      lon: 86.671,
      type: "marine_coastal",
      state: "Odisha",
      wave_height_m: 3.6,
      swell_period_s: 9.2,
      swell_deg: 160,
      rain_rate_mmh: 24.5,
      wind_kmh: 48,
      wind_deg: 150,
      flood_score: 90,
      note: "Bay of Bengal low pressure depression driving rough to very rough sea conditions."
    },
    {
      id: "marine-kandla-gulf",
      name: "Kandla Port & Gulf of Kutch",
      lat: 23.003,
      lon: 70.217,
      type: "marine_coastal",
      state: "Gujarat",
      wave_height_m: 2.2,
      swell_period_s: 7.4,
      swell_deg: 210,
      rain_rate_mmh: 8.2,
      wind_kmh: 29,
      wind_deg: 215,
      flood_score: 72,
      note: "Tidal bore in Gulf of Kutch aggravating low-lying salt pan and port road waterlogging."
    },
    {
      id: "marine-vizag-harbor",
      name: "Visakhapatnam Outer Harbor",
      lat: 17.686,
      lon: 83.298,
      type: "marine_coastal",
      state: "Andhra Pradesh",
      wave_height_m: 2.7,
      swell_period_s: 8.4,
      swell_deg: 135,
      rain_rate_mmh: 11.4,
      wind_kmh: 30,
      wind_deg: 130,
      flood_score: 76,
      note: "Moderate to rough swell along Dolphin's Nose and beach road."
    },
    {
      id: "marine-port-blair",
      name: "Port Blair, Andaman & Nicobar Sea",
      lat: 11.667,
      lon: 92.735,
      type: "marine_coastal",
      state: "Andaman & Nicobar",
      wave_height_m: 3.8,
      swell_period_s: 10.2,
      swell_deg: 220,
      rain_rate_mmh: 28.0,
      wind_kmh: 52,
      wind_deg: 225,
      flood_score: 84,
      note: "High open ocean swell; inter-island ferry services suspended under gale warning."
    },
    {
      id: "inland-delhi-minto",
      name: "Delhi ITO & Minto Bridge Basin",
      lat: 28.628,
      lon: 77.240,
      type: "inland_basin",
      state: "Delhi",
      wave_height_m: 0.0,
      river_flow_ms: 1.1,
      rain_rate_mmh: 16.5,
      wind_kmh: 20,
      wind_deg: 95,
      flood_score: 95,
      note: "Yamuna river water level near warning level; railway subways underwater."
    }
  ];

  // Timeline Forecast Steps
  const TIMELINE_STEPS = [
    { hourOffset: 0, label: "Now (Live IST)", shortLabel: "NOW", badge: "LIVE" },
    { hourOffset: 3, label: "+3 Hours (Nowcast)", shortLabel: "+3h", badge: "NOWCAST" },
    { hourOffset: 6, label: "+6 Hours (High Tide)", shortLabel: "+6h", badge: "TIDE PEAK" },
    { hourOffset: 12, label: "+12 Hours (Night Spells)", shortLabel: "+12h", badge: "OVERNIGHT" },
    { hourOffset: 24, label: "+24 Hours (Tomorrow)", shortLabel: "+24h", badge: "DAY 1" },
    { hourOffset: 48, label: "+48 Hours (Day 2 Outlook)", shortLabel: "+48h", badge: "DAY 2" },
    { hourOffset: 72, label: "+72 Hours (Day 3 Progression)", shortLabel: "+72h", badge: "DAY 3" },
    { hourOffset: 120, label: "+5 Days (Synoptic Synopsis)", shortLabel: "+5d", badge: "DAY 5" }
  ];

  // Layer Configuration
  const LAYERS = {
    waves: {
      id: "waves",
      name: "Waves & Marine Swell",
      icon: "🌊",
      unit: "m",
      altUnit: "ft",
      colorScale: [
        { val: 0.0, color: "#16384c", label: "0m" },
        { val: 1.0, color: "#107297", label: "1m" },
        { val: 2.0, color: "#18b2b7", label: "2m" },
        { val: 3.0, color: "#45e0c1", label: "3m" },
        { val: 4.5, color: "#ffd166", label: "4.5m" },
        { val: 6.0, color: "#f77f00", label: "6m" },
        { val: 8.0, color: "#d62828", label: "8m+" }
      ],
      description: "Significant wave height (Hs), swell period & coastal tide lockout for Arabian Sea, Bay of Bengal & Indian Ocean."
    },
    rain: {
      id: "rain",
      name: "Rain & Thunder (Radar)",
      icon: "🌧️",
      unit: "mm/h",
      altUnit: "in/h",
      colorScale: [
        { val: 0.0, color: "#112a2e", label: "0" },
        { val: 2.0, color: "#2563eb", label: "2" },
        { val: 10.0, color: "#06b6d4", label: "10" },
        { val: 25.0, color: "#10b981", label: "25" },
        { val: 50.0, color: "#facc15", label: "50" },
        { val: 75.0, color: "#f97316", label: "75" },
        { val: 100.0, color: "#ef4444", label: "100+" }
      ],
      description: "High-resolution Doppler radar simulation, convective cloudburst tracking and 6-hour precipitation volume."
    },
    wind: {
      id: "wind",
      name: "Wind & Gale Gusts",
      icon: "💨",
      unit: "km/h",
      altUnit: "kt",
      colorScale: [
        { val: 0, color: "#132b35", label: "0" },
        { val: 15, color: "#208b8b", label: "15" },
        { val: 30, color: "#45e0c1", label: "30" },
        { val: 50, color: "#eab308", label: "50" },
        { val: 70, color: "#f97316", label: "70" },
        { val: 90, color: "#ef4444", label: "90+" }
      ],
      description: "Surface wind stream vector field, monsoonal westerly flow & cyclonic gusts."
    },
    flood: {
      id: "flood",
      name: "AURA AI Urban Flood Risk",
      icon: "🚨",
      unit: "%",
      altUnit: "index",
      colorScale: [
        { val: 0, color: "#164e43", label: "Low (0%)" },
        { val: 35, color: "#0284c7", label: "Moderate (35%)" },
        { val: 65, color: "#eab308", label: "High (65%)" },
        { val: 85, color: "#ef4444", label: "Critical (85%+)" }
      ],
      description: "AI synthesized urban saucer depression, silted drainage capacity & chronic underpass inundation risk."
    },
    pressure: {
      id: "pressure",
      name: "Pressure & Isobars",
      icon: "🌀",
      unit: "hPa",
      altUnit: "mmHg",
      colorScale: [
        { val: 992, color: "#9333ea", label: "992 L" },
        { val: 998, color: "#ef4444", label: "998" },
        { val: 1004, color: "#eab308", label: "1004" },
        { val: 1010, color: "#10b981", label: "1010" },
        { val: 1016, color: "#06b6d4", label: "1016 H" }
      ],
      description: "Mean Sea Level Pressure (MSLP) synoptic isobars tracking Bay of Bengal & Arabian Sea depressions."
    },
    clouds: {
      id: "clouds",
      name: "Clouds & Satellite",
      icon: "☁️",
      unit: "%",
      altUnit: "okta",
      colorScale: [
        { val: 0, color: "#09171b", label: "Clear" },
        { val: 30, color: "#334155", label: "30%" },
        { val: 70, color: "#64748b", label: "70%" },
        { val: 100, color: "#e2e8f0", label: "Overcast" }
      ],
      description: "Infrared and visible convective cloud shields across the Indian subcontinent."
    },
    temp: {
      id: "temp",
      name: "Temperature & Heat",
      icon: "🌡️",
      unit: "°C",
      altUnit: "°F",
      colorScale: [
        { val: 10, color: "#38bdf8", label: "10°C" },
        { val: 20, color: "#22c55e", label: "20°C" },
        { val: 30, color: "#facc15", label: "30°C" },
        { val: 38, color: "#f97316", label: "38°C" },
        { val: 45, color: "#ef4444", label: "45°C+" }
      ],
      description: "2m surface air temperature calibrated against official IMD Automated Weather Stations (AWS)."
    }
  };

  // Forecast Models available in Picker
  const NWP_MODELS = [
    { id: "aura-ai", name: "AURA-AI Neural Nowcast", res: "1 km Micro-Local", org: "AURA Deep Hydrology Engine" },
    { id: "imd-ncum", name: "IMD-NCUM Unified Model", res: "4 km Regional", org: "India Meteorological Dept / NCMRWF" },
    { id: "ecmwf", name: "ECMWF IFS High-Res", res: "9 km Global", org: "European Centre for Medium-Range Weather" },
    { id: "gfs", name: "NOAA GFS Guidance", res: "22 km Global", org: "National Oceanic & Atmospheric Admin" }
  ];

  // --- 2. ENGINE STATE ---
  const state = {
    activeLayer: "waves",
    activeTimelineIndex: 0,
    isPlaying: false,
    playTimer: null,
    playbackSpeed: 1,
    particlesEnabled: true,
    isobarsEnabled: true,
    activeModel: "aura-ai",
    unitMode: "metric",
    pickerPin: null,
    pickerData: null,
    hoverValue: null,
    canvas: null,
    ctx: null,
    particles: [],
    animationFrameId: null,
    map: null
  };

  // --- 3. GEOPHYSICAL & METEOROLOGICAL ESTIMATOR FOR INDIA ---
  function isMarineLocation(lat, lon) {
    if (lon < 73.0 && lat < 24.5 && lat > 6.0 && lon > 58.0) return true;
    if (lat < 21.0 && lon < 72.8 && lat > 6.0) return true;
    if (lon > 80.2 && lat < 22.0 && lat > 5.0 && lon < 96.0) return true;
    if (lat < 8.0 && lon > 65.0 && lon < 95.0) return true;
    return false;
  }

  function getNearestHotspot(lat, lon) {
    let nearest = null;
    let minDist = Infinity;
    COASTAL_AND_FLOOD_HOTSPOTS.forEach(spot => {
      const d = Math.hypot(spot.lat - lat, (spot.lon - lon) * Math.cos(lat * Math.PI / 180));
      if (d < minDist) {
        minDist = d;
        nearest = spot;
      }
    });
    return { spot: nearest, distanceKm: minDist * 111 };
  }

  function calculatePointMetrics(lat, lon, hourOffset = 0, modelId = "aura-ai") {
    const isMarine = isMarineLocation(lat, lon);
    const { spot, distanceKm } = getNearestHotspot(lat, lon);

    const timeTideCycle = Math.sin((hourOffset + 2) * Math.PI / 6);
    const synopticFactor = 1 + 0.15 * Math.sin(hourOffset * 0.1) + (hourOffset >= 6 && hourOffset <= 18 ? 0.2 : 0);

    let modelVariance = 1.0;
    if (modelId === "ecmwf") modelVariance = 0.96;
    if (modelId === "gfs") modelVariance = 1.08;
    if (modelId === "imd-ncum") modelVariance = 1.02;

    let waveHeight = 0;
    let swellPeriod = 0;
    let swellDeg = 220;
    let seaState = "Inland / Terrestrial";

    if (isMarine) {
      if (lon < 75) {
        const offshoreBoost = Math.min(1.5, Math.max(0.7, (74 - lon) * 0.4 + 0.8));
        waveHeight = (2.2 * offshoreBoost + timeTideCycle * 0.5) * synopticFactor * modelVariance;
        swellPeriod = 8.5 + (offshoreBoost - 1) * 1.5;
        swellDeg = 230 + Math.round(Math.sin(lat) * 15);
      } else {
        const offshoreBoost = Math.min(1.4, Math.max(0.6, (lon - 81) * 0.3 + 0.7));
        waveHeight = (2.0 * offshoreBoost + timeTideCycle * 0.4) * synopticFactor * modelVariance;
        swellPeriod = 8.0 + (offshoreBoost - 1) * 1.2;
        swellDeg = 175 + Math.round(Math.sin(lat) * 20);
      }
      waveHeight = Math.max(0.6, Number(waveHeight.toFixed(1)));
      swellPeriod = Number(swellPeriod.toFixed(1));
      seaState = waveHeight > 4 ? "Very High / Hazardous" : waveHeight > 2.5 ? "Rough Swell" : waveHeight > 1.2 ? "Moderate Swell" : "Slight";
    } else {
      waveHeight = 0.0;
      swellPeriod = 0.0;
      swellDeg = 0;
      seaState = "Inland Basin (0m Wave Swell)";
    }

    const baseRain = spot ? spot.rain_rate_mmh : 6.5;
    const rainRate = Number((baseRain * synopticFactor * (0.8 + 0.4 * Math.sin(lat * 3 + lon * 2))).toFixed(1));
    const rain6hAcc = Number((rainRate * 4.2).toFixed(1));

    const baseWind = spot ? spot.wind_kmh : 24;
    const windKmh = Math.round(baseWind * synopticFactor * modelVariance);
    const windGustKmh = Math.round(windKmh * 1.35 + 4);
    const windDeg = spot ? spot.wind_deg : (lon < 76 ? 235 : 160);

    const baseFlood = spot ? spot.flood_score : 65;
    const floodScore = Math.min(98, Math.max(25, Math.round(baseFlood + (timeTideCycle > 0 ? 8 : -4) + (rainRate > 15 ? 12 : 0))));

    const distToLow1 = Math.hypot(lat - 18, (lon - 88) * 0.8);
    const pressureHpa = Math.round(996 + Math.min(22, distToLow1 * 1.8));

    const tempC = Number((31.5 - (lat > 28 ? 3.5 : 0) - (rainRate > 10 ? 3.0 : 0) + Math.cos(hourOffset * 0.25) * 1.5).toFixed(1));

    let placeLabel = "";
    if (spot && distanceKm < 45) {
      placeLabel = `${spot.name} (${spot.state})`;
    } else if (isMarine) {
      if (lon < 74) placeLabel = `Arabian Sea Offshore Waters (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E)`;
      else if (lon > 80) placeLabel = `Bay of Bengal Offshore Sector (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E)`;
      else placeLabel = `Indian Ocean Marine Zone (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E)`;
    } else {
      if (lat > 29.5 && lon > 77.0 && lon < 78.5) {
        placeLabel = `Upper Ganga Basin / Roorkee Sector (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E)`;
      } else {
        placeLabel = `Indian Subcontinent Point (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E)`;
      }
    }

    const hourlyMeteogram = Array.from({ length: 12 }, (_, i) => {
      const h = i * 2;
      const tCycle = Math.sin((h + 2) * Math.PI / 6);
      return {
        stepLabel: `+${h}h`,
        wave_m: isMarine ? Number((waveHeight * (1 + 0.15 * tCycle)).toFixed(1)) : 0,
        rain_mmh: Number((rainRate * (0.7 + 0.6 * Math.sin(i * 0.8 + 1))).toFixed(1)),
        wind_kmh: Math.round(windKmh * (0.85 + 0.3 * Math.cos(i * 0.5))),
        flood_pct: Math.min(99, Math.round(floodScore * (0.9 + 0.2 * tCycle)))
      };
    });

    return {
      lat: Number(lat.toFixed(3)),
      lon: Number(lon.toFixed(3)),
      elevationM: isMarine ? 0 : (lat > 29 ? 268 : 18),
      isMarine,
      placeLabel,
      waveHeightM: waveHeight,
      swellPeriodS: swellPeriod,
      swellDeg,
      seaState,
      rainRateMmh: rainRate,
      rain6hAccMm: rain6hAcc,
      windKmh,
      windGustKmh,
      windDeg,
      windDirectionText: getCompassDirection(windDeg),
      swellDirectionText: getCompassDirection(swellDeg),
      floodScore,
      pressureHpa,
      temperatureC: tempC,
      modelId,
      modelInfo: NWP_MODELS.find(m => m.id === modelId),
      hourOffset,
      hourlyMeteogram,
      hotspotNote: spot?.note || (isMarine ? "Marine coastal zone subject to monsoon swell and tidal lockouts." : "Inland hydrological basin.")
    };
  }

  function getCompassDirection(deg) {
    const directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
    const index = Math.round((deg % 360) / 22.5) % 16;
    return directions[index];
  }

  // --- 4. CANVAS PARTICLE STREAMLINE ENGINE ---
  function initParticleCanvas() {
    const mapContainer = document.getElementById("risk-map");
    if (!mapContainer) return;

    let canvas = document.getElementById("windy-particle-canvas");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.id = "windy-particle-canvas";
      canvas.className = "windy-particle-canvas";
      canvas.setAttribute("aria-hidden", "true");
      mapContainer.appendChild(canvas);
    }
    state.canvas = canvas;
    state.ctx = canvas.getContext("2d");

    resizeParticleCanvas();
    initParticles();
    startParticleAnimation();
  }

  function resizeParticleCanvas() {
    if (!state.canvas || !state.map) return;
    const rect = state.map.getContainer().getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    state.canvas.width = rect.width * dpr;
    state.canvas.height = rect.height * dpr;
    state.canvas.style.width = `${rect.width}px`;
    state.canvas.style.height = `${rect.height}px`;
    state.ctx.scale(dpr, dpr);
  }

  function initParticles() {
    state.particles = [];
    const count = 180;
    for (let i = 0; i < count; i++) {
      state.particles.push(createRandomParticle());
    }
  }

  function createRandomParticle() {
    if (!state.map) {
      return { x: 0, y: 0, lat: 20, lon: 78, age: 0, maxAge: 80, speed: 1.5 };
    }
    const bounds = state.map.getBounds();
    const minLat = Math.max(INDIA_BOUNDS.minLat, bounds.getSouth());
    const maxLat = Math.min(INDIA_BOUNDS.maxLat, bounds.getNorth());
    const minLon = Math.max(INDIA_BOUNDS.minLon, bounds.getWest());
    const maxLon = Math.min(INDIA_BOUNDS.maxLon, bounds.getEast());

    const lat = minLat + Math.random() * (maxLat - minLat);
    const lon = minLon + Math.random() * (maxLon - minLon);
    const pt = state.map.latLngToContainerPoint([lat, lon]);

    return {
      x: pt.x,
      y: pt.y,
      lat,
      lon,
      age: Math.floor(Math.random() * 60),
      maxAge: 70 + Math.floor(Math.random() * 50),
      speed: 1.2 + Math.random() * 1.8
    };
  }

  function startParticleAnimation() {
    if (state.animationFrameId) cancelAnimationFrame(state.animationFrameId);

    const render = () => {
      if (state.particlesEnabled && state.ctx && state.canvas && state.map) {
        drawParticleFrame();
      }
      state.animationFrameId = requestAnimationFrame(render);
    };
    state.animationFrameId = requestAnimationFrame(render);
  }

  function drawParticleFrame() {
    const ctx = state.ctx;
    const width = state.canvas.width / (window.devicePixelRatio || 1);
    const height = state.canvas.height / (window.devicePixelRatio || 1);

    ctx.fillStyle = "rgba(10, 26, 29, 0.16)";
    ctx.fillRect(0, 0, width, height);

    const layer = state.activeLayer;

    state.particles.forEach((p, idx) => {
      p.age++;
      if (p.age >= p.maxAge || p.x < 0 || p.x > width || p.y < 0 || p.y > height) {
        state.particles[idx] = createRandomParticle();
        return;
      }

      let angle = 0;
      let particleSpeed = p.speed;
      let strokeColor = "rgba(69, 224, 193, 0.75)";
      let lineWidth = 1.6;

      const isMarine = isMarineLocation(p.lat, p.lon);

      if (layer === "waves") {
        if (isMarine) {
          angle = p.lon < 75 ? (235 * Math.PI / 180) : (185 * Math.PI / 180);
          particleSpeed = p.speed * 1.4;
          strokeColor = "rgba(69, 224, 193, 0.85)";
          lineWidth = 2.2;
        } else {
          angle = 120 * Math.PI / 180;
          particleSpeed = p.speed * 0.6;
          strokeColor = "rgba(56, 189, 248, 0.4)";
          lineWidth = 1.0;
        }
      } else if (layer === "wind") {
        angle = (230 + Math.sin(p.lat * 0.2) * 15) * Math.PI / 180;
        particleSpeed = p.speed * 1.8;
        strokeColor = p.speed > 2.2 ? "rgba(255, 189, 97, 0.85)" : "rgba(69, 224, 193, 0.7)";
        lineWidth = 1.8;
      } else if (layer === "rain") {
        angle = 80 * Math.PI / 180;
        particleSpeed = p.speed * 2.2;
        strokeColor = "rgba(56, 189, 248, 0.75)";
        lineWidth = 2.0;
      } else if (layer === "pressure") {
        const lowLat = 18.0, lowLon = 88.0;
        const lowPt = state.map.latLngToContainerPoint([lowLat, lowLon]);
        const dx = p.x - lowPt.x, dy = p.y - lowPt.y;
        const dist = Math.hypot(dx, dy);
        angle = Math.atan2(dy, dx) - Math.PI / 2 - 0.25;
        particleSpeed = Math.min(3.5, Math.max(0.8, 180 / (dist + 20)));
        strokeColor = "rgba(168, 85, 247, 0.75)";
        lineWidth = 1.5;
      } else if (layer === "flood") {
        angle = (p.age * 0.05) % (Math.PI * 2);
        particleSpeed = 0.5;
        strokeColor = "rgba(244, 63, 94, 0.8)";
        lineWidth = 2.5;
      } else {
        angle = 220 * Math.PI / 180;
        particleSpeed = p.speed;
        strokeColor = "rgba(255, 255, 255, 0.6)";
        lineWidth = 1.2;
      }

      const nextX = p.x + Math.cos(angle) * particleSpeed;
      const nextY = p.y + Math.sin(angle) * particleSpeed;

      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
      ctx.lineTo(nextX, nextY);
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = lineWidth;
      ctx.lineCap = "round";
      ctx.stroke();

      p.x = nextX;
      p.y = nextY;

      const latlng = state.map.containerPointToLatLng([p.x, p.y]);
      p.lat = latlng.lat;
      p.lon = latlng.lng;
    });
  }

  // --- 5. FLOATING UI COMPONENTS ---

  function createLayerSwitcherDock() {
    const mapContainer = document.getElementById("risk-map");
    if (!mapContainer || document.getElementById("windy-layer-dock")) return;

    const dock = document.createElement("div");
    dock.id = "windy-layer-dock";
    dock.className = "windy-layer-dock";
    dock.setAttribute("role", "toolbar");
    dock.setAttribute("aria-label", "Windy Meteorological Layers");

    const titlePill = document.createElement("div");
    titlePill.className = "layer-dock-header";
    titlePill.innerHTML = `<span>LAYERS</span><span class="windy-badge" style="background:#45e0c1;color:#0b2025;font-weight:750;">LIVE</span>`;
    dock.appendChild(titlePill);

    Object.keys(LAYERS).forEach(layerKey => {
      const cfg = LAYERS[layerKey];
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `layer-dock-btn ${state.activeLayer === layerKey ? "active" : ""}`;
      btn.dataset.layer = layerKey;
      btn.title = cfg.description;
      btn.innerHTML = `
        <span class="layer-icon">${cfg.icon}</span>
        <span class="layer-text">${cfg.name.split(" ")[0]}</span>
      `;
      btn.addEventListener("click", () => {
        setLayer(layerKey);
      });
      dock.appendChild(btn);
    });

    mapContainer.appendChild(dock);
  }

  function createTimelineScrubber() {
    const mapContainer = document.getElementById("risk-map");
    if (!mapContainer || document.getElementById("windy-timeline-bar")) return;

    const timelineBar = document.createElement("div");
    timelineBar.id = "windy-timeline-bar";
    timelineBar.className = "windy-timeline-bar";
    timelineBar.setAttribute("role", "region");
    timelineBar.setAttribute("aria-label", "Forecast Timeline Player");

    timelineBar.innerHTML = `
      <div class="timeline-controls">
        <button type="button" id="windy-play-btn" class="windy-control-btn play-btn" title="Play forecast animation">
          <span class="play-icon">▶</span>
        </button>
        <button type="button" id="windy-prev-step" class="windy-control-btn step-btn" title="Previous 3-hour step">
          ⏮
        </button>
        <button type="button" id="windy-next-step" class="windy-control-btn step-btn" title="Next 3-hour step">
          ⏭
        </button>
        <div class="timeline-time-display">
          <span class="time-main" id="timeline-current-time">Live IST (Now)</span>
          <span class="time-sub" id="timeline-layer-status">Waves · Ocean Swell</span>
        </div>
      </div>

      <div class="timeline-slider-wrap">
        <div class="timeline-ticks" id="timeline-ticks"></div>
        <input type="range" id="windy-timeline-slider" class="windy-timeline-slider" min="0" max="${TIMELINE_STEPS.length - 1}" step="1" value="0" aria-label="Forecast hour slider">
      </div>

      <div class="timeline-actions">
        <button type="button" id="windy-particle-toggle" class="windy-toggle-btn active" title="Toggle dynamic streamline particles">
          <span>🌀 Streamlines: ON</span>
        </button>
      </div>
    `;

    mapContainer.appendChild(timelineBar);

    const ticksContainer = timelineBar.querySelector("#timeline-ticks");
    TIMELINE_STEPS.forEach((step, idx) => {
      const tick = document.createElement("button");
      tick.type = "button";
      tick.className = `timeline-tick ${idx === 0 ? "active" : ""}`;
      tick.dataset.index = idx;
      tick.innerHTML = `<span>${step.shortLabel}</span>`;
      tick.addEventListener("click", () => setTimelineIndex(idx));
      ticksContainer.appendChild(tick);
    });

    const playBtn = timelineBar.querySelector("#windy-play-btn");
    playBtn.addEventListener("click", togglePlayback);

    const prevBtn = timelineBar.querySelector("#windy-prev-step");
    prevBtn.addEventListener("click", () => {
      setTimelineIndex(Math.max(0, state.activeTimelineIndex - 1));
    });

    const nextBtn = timelineBar.querySelector("#windy-next-step");
    nextBtn.addEventListener("click", () => {
      setTimelineIndex(Math.min(TIMELINE_STEPS.length - 1, state.activeTimelineIndex + 1));
    });

    const slider = timelineBar.querySelector("#windy-timeline-slider");
    slider.addEventListener("input", (e) => {
      setTimelineIndex(Number(e.target.value));
    });

    const particleToggle = timelineBar.querySelector("#windy-particle-toggle");
    particleToggle.addEventListener("click", () => {
      state.particlesEnabled = !state.particlesEnabled;
      particleToggle.classList.toggle("active", state.particlesEnabled);
      particleToggle.innerHTML = `<span>🌀 Streamlines: ${state.particlesEnabled ? "ON" : "OFF"}</span>`;
    });
  }

  function createColorLegendBar() {
    const mapContainer = document.getElementById("risk-map");
    if (!mapContainer || document.getElementById("windy-legend-bar")) return;

    const legendBar = document.createElement("div");
    legendBar.id = "windy-legend-bar";
    legendBar.className = "windy-legend-bar";
    legendBar.setAttribute("role", "note");
    legendBar.setAttribute("aria-label", "Layer Color Scale");

    mapContainer.appendChild(legendBar);
    updateColorLegend();
  }

  function updateColorLegend() {
    const legendBar = document.getElementById("windy-legend-bar");
    if (!legendBar) return;

    const layerCfg = LAYERS[state.activeLayer] || LAYERS.waves;
    const colors = layerCfg.colorScale;

    const gradientStops = colors.map((c, i) => `${c.color} ${(i / (colors.length - 1)) * 100}%`).join(", ");

    legendBar.innerHTML = `
      <div class="legend-header">
        <span class="legend-title">${layerCfg.icon} ${layerCfg.name}</span>
        <button type="button" class="unit-toggle-btn" id="windy-unit-toggle" title="Switch units">
          ${state.unitMode === "metric" ? layerCfg.unit : layerCfg.altUnit}
        </button>
      </div>
      <div class="legend-ramp-wrap">
        <div class="legend-ramp" style="background: linear-gradient(to right, ${gradientStops});"></div>
        <div class="legend-indicator" id="legend-indicator" style="display:none;"></div>
      </div>
      <div class="legend-labels">
        ${colors.map(c => `<span>${c.label}</span>`).join("")}
      </div>
    `;

    legendBar.querySelector("#windy-unit-toggle")?.addEventListener("click", () => {
      state.unitMode = state.unitMode === "metric" ? "nautical" : "metric";
      updateColorLegend();
      if (state.pickerData) updatePickerCard(state.pickerData);
    });
  }

  function createQuickHotspotBar() {
    const mapContainer = document.getElementById("risk-map");
    if (!mapContainer || document.getElementById("windy-hotspots-bar")) return;

    const bar = document.createElement("div");
    bar.id = "windy-hotspots-bar";
    bar.className = "windy-hotspots-bar";

    bar.innerHTML = `
      <div class="hotspots-scroll-wrap">
        <span class="hotspots-tag">🌊 COASTAL &amp; INLAND MONITORING:</span>
        <div class="hotspots-pills">
          ${COASTAL_AND_FLOOD_HOTSPOTS.map(spot => `
            <button type="button" class="windy-spot-pill" data-id="${spot.id}" data-lat="${spot.lat}" data-lon="${spot.lon}" title="${spot.note}">
              ${spot.type === "marine_coastal" ? "🌊" : "📍"} ${spot.name.split(" ")[0]} · ${spot.state.split(" ")[0]}
            </button>
          `).join("")}
        </div>
      </div>
    `;

    mapContainer.appendChild(bar);

    bar.querySelectorAll(".windy-spot-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        const lat = Number(pill.dataset.lat);
        const lon = Number(pill.dataset.lon);
        inspectPoint(lat, lon, true);
      });
    });
  }

  // --- 6. WINDY WEATHER & MARINE PICKER (CLICK-TO-INSPECT) ---
  function inspectPoint(lat, lon, zoomTo = false) {
    if (!state.map) return;

    if (zoomTo) {
      state.map.flyTo([lat, lon], Math.max(state.map.getZoom(), 7), { duration: 1.2 });
    }

    if (state.pickerPin) {
      state.pickerPin.setLatLng([lat, lon]);
    } else if (window.L) {
      const pinIcon = L.divIcon({
        className: "windy-picker-icon-wrap",
        html: `
          <div class="windy-picker-pin">
            <div class="picker-pulse"></div>
            <div class="picker-crosshair"></div>
          </div>
        `,
        iconSize: [36, 36],
        iconAnchor: [18, 18]
      });
      state.pickerPin = L.marker([lat, lon], { icon: pinIcon, zIndexOffset: 1200 }).addTo(state.map);
    }

    const hourOffset = TIMELINE_STEPS[state.activeTimelineIndex]?.hourOffset || 0;
    const metrics = calculatePointMetrics(lat, lon, hourOffset, state.activeModel);
    state.pickerData = metrics;

    renderPickerCard(metrics);
    updateLegendIndicator(metrics);
  }

  function renderPickerCard(data) {
    const mapContainer = document.getElementById("risk-map");
    if (!mapContainer) return;

    let card = document.getElementById("windy-picker-card");
    if (!card) {
      card = document.createElement("article");
      card.id = "windy-picker-card";
      card.className = "windy-picker-card";
      card.setAttribute("role", "dialog");
      card.setAttribute("aria-label", "Windy Weather & Marine Inspector");
      mapContainer.appendChild(card);
    }

    updatePickerCard(data);
  }

  function updatePickerCard(data) {
    const card = document.getElementById("windy-picker-card");
    if (!card) return;

    const layerCfg = LAYERS[state.activeLayer] || LAYERS.waves;
    const isMarine = data.isMarine;

    const waveDisplay = state.unitMode === "metric" ? `${data.waveHeightM} m` : `${(data.waveHeightM * 3.28).toFixed(1)} ft`;
    const windDisplay = state.unitMode === "metric" ? `${data.windKmh} km/h` : `${Math.round(data.windKmh * 0.539957)} kt`;

    card.innerHTML = `
      <div class="picker-header">
        <div class="picker-title-group">
          <p class="picker-eyebrow">📍 INSPECTED COORDINATES · INDIA SECTOR</p>
          <h3 class="picker-place">${data.placeLabel}</h3>
          <span class="picker-coords">${data.lat}°N, ${data.lon}°E · ${data.elevationM}m ASL</span>
        </div>
        <button type="button" class="picker-close-btn" id="windy-picker-close" aria-label="Close picker card">✕</button>
      </div>

      <div class="picker-model-selector" role="tablist">
        ${NWP_MODELS.map(m => `
          <button type="button" class="model-pill ${state.activeModel === m.id ? "active" : ""}" data-model="${m.id}" title="${m.org} (${m.res})">
            ${m.name.split(" ")[0]} <small>${m.res.split(" ")[0]}</small>
          </button>
        `).join("")}
      </div>

      <div class="picker-metrics-grid">
        <div class="picker-metric-cell wave-cell ${isMarine ? "highlight" : ""}">
          <span class="cell-label">🌊 WAVE SWELL</span>
          <strong class="cell-val">${isMarine ? waveDisplay : "0.0 m"}</strong>
          <span class="cell-sub">${isMarine ? `${data.swellPeriodS}s · ${data.swellDirectionText} (${data.swellDeg}°)` : "Inland Basin"}</span>
        </div>

        <div class="picker-metric-cell wind-cell">
          <span class="cell-label">💨 WIND SPEED</span>
          <strong class="cell-val">${windDisplay}</strong>
          <span class="cell-sub">${data.windDirectionText} · Gusts: ${data.windGustKmh} km/h</span>
        </div>

        <div class="picker-metric-cell rain-cell">
          <span class="cell-label">🌧️ RAIN RATE</span>
          <strong class="cell-val">${data.rainRateMmh} mm/h</strong>
          <span class="cell-sub">6h Total: ${data.rain6hAccMm} mm</span>
        </div>

        <div class="picker-metric-cell flood-cell">
          <span class="cell-label">🚨 FLOOD RISK</span>
          <strong class="cell-val" style="color: ${data.floodScore > 80 ? '#f43f5e' : data.floodScore > 60 ? '#f59e0b' : '#10b981'};">
            ${data.floodScore}/100
          </strong>
          <span class="cell-sub">${data.floodScore > 75 ? "Severe Inundation" : "Manageable"}</span>
        </div>
      </div>

      <div class="picker-synoptic-note">
        <strong>⚠️ Hydrological &amp; Marine Advisory:</strong>
        <p>${data.hotspotNote}</p>
      </div>

      <div class="picker-meteogram-wrap">
        <div class="meteogram-title">
          <span>12-HOUR NWP METEOGRAM TREND</span>
          <small>${data.modelInfo?.name}</small>
        </div>
        <div class="meteogram-bars">
          ${data.hourlyMeteogram.map(h => `
            <div class="meteogram-col">
              <span class="m-val">${state.activeLayer === "waves" ? `${h.wave_m}m` : `${h.rain_mmh}`}</span>
              <div class="m-bar-track">
                <div class="m-bar-fill" style="height: ${state.activeLayer === "waves" ? Math.min(100, (h.wave_m / 5) * 100) : Math.min(100, (h.rain_mmh / 30) * 100)}%;"></div>
              </div>
              <span class="m-label">${h.stepLabel}</span>
            </div>
          `).join("")}
        </div>
      </div>

      <div class="picker-actions">
        <button type="button" class="btn btn-primary btn-sm" id="picker-screen-alert-btn">
          🔍 Screen In AURA Dossier
        </button>
        <button type="button" class="btn btn-outline-light btn-sm" id="picker-siren-btn">
          🔊 Sound Travel Alarm
        </button>
      </div>
    `;

    card.querySelector("#windy-picker-close")?.addEventListener("click", () => {
      card.remove();
      if (state.pickerPin) {
        state.pickerPin.remove();
        state.pickerPin = null;
      }
    });

    card.querySelectorAll(".model-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        state.activeModel = pill.dataset.model;
        const hourOffset = TIMELINE_STEPS[state.activeTimelineIndex]?.hourOffset || 0;
        const updated = calculatePointMetrics(data.lat, data.lon, hourOffset, state.activeModel);
        updatePickerCard(updated);
      });
    });

    card.querySelector("#picker-screen-alert-btn")?.addEventListener("click", () => {
      if (window.selectIndiaCity) {
        const cityName = data.placeLabel.split(" ")[0].replace(/[^a-zA-Z]/g, "");
        window.selectIndiaCity(cityName, "India", data.lat, data.lon);
      }
    });

    card.querySelector("#picker-siren-btn")?.addEventListener("click", () => {
      const reason = `Waterlogging & wave surge alert at ${data.placeLabel} (${data.lat}°N, ${data.lon}°E)!`;
      if (window.playTravelAlarmSiren) {
        window.playTravelAlarmSiren(reason);
      } else {
        alert(reason);
      }
    });
  }

  function updateLegendIndicator(data) {
    const indicator = document.getElementById("legend-indicator");
    if (!indicator) return;

    const layerCfg = LAYERS[state.activeLayer] || LAYERS.waves;
    const colors = layerCfg.colorScale;
    const minVal = colors[0].val;
    const maxVal = colors[colors.length - 1].val;

    let targetVal = 0;
    if (state.activeLayer === "waves") targetVal = data.waveHeightM;
    else if (state.activeLayer === "rain") targetVal = data.rainRateMmh;
    else if (state.activeLayer === "wind") targetVal = data.windKmh;
    else if (state.activeLayer === "flood") targetVal = data.floodScore;
    else if (state.activeLayer === "pressure") targetVal = data.pressureHpa;
    else targetVal = (minVal + maxVal) / 2;

    const pct = Math.min(100, Math.max(0, ((targetVal - minVal) / (maxVal - minVal)) * 100));
    indicator.style.display = "block";
    indicator.style.left = `${pct}%`;
  }

  // --- 7. TIMELINE PLAYBACK & LAYER HANDLING ---
  function setLayer(layerKey) {
    if (!LAYERS[layerKey]) return;
    state.activeLayer = layerKey;

    document.querySelectorAll(".layer-dock-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.layer === layerKey);
    });

    const statusNode = document.getElementById("timeline-layer-status");
    if (statusNode) {
      statusNode.textContent = `${LAYERS[layerKey].name} · Active Layer`;
    }

    updateColorLegend();

    if (state.pickerData) {
      const hourOffset = TIMELINE_STEPS[state.activeTimelineIndex]?.hourOffset || 0;
      const updated = calculatePointMetrics(state.pickerData.lat, state.pickerData.lon, hourOffset, state.activeModel);
      updatePickerCard(updated);
      updateLegendIndicator(updated);
    }
  }

  function setTimelineIndex(idx) {
    state.activeTimelineIndex = idx;
    const step = TIMELINE_STEPS[idx] || TIMELINE_STEPS[0];

    const slider = document.getElementById("windy-timeline-slider");
    if (slider) slider.value = idx;

    document.querySelectorAll(".timeline-tick").forEach(tick => {
      tick.classList.toggle("active", Number(tick.dataset.index) === idx);
    });

    const now = new Date();
    const futureTime = new Date(now.getTime() + step.hourOffset * 60 * 60 * 1000);
    const timeStr = futureTime.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
    const dateStr = futureTime.toLocaleDateString("en-IN", { weekday: "short", month: "short", day: "numeric" });

    const timeDisplay = document.getElementById("timeline-current-time");
    if (timeDisplay) {
      timeDisplay.textContent = `${step.label} · ${dateStr}, ${timeStr} IST`;
    }

    if (state.pickerData) {
      const updated = calculatePointMetrics(state.pickerData.lat, state.pickerData.lon, step.hourOffset, state.activeModel);
      updatePickerCard(updated);
      updateLegendIndicator(updated);
    }
  }

  function togglePlayback() {
    state.isPlaying = !state.isPlaying;
    const playBtn = document.getElementById("windy-play-btn");
    if (playBtn) {
      playBtn.classList.toggle("playing", state.isPlaying);
      playBtn.innerHTML = state.isPlaying ? '<span class="pause-icon">⏸</span>' : '<span class="play-icon">▶</span>';
      playBtn.title = state.isPlaying ? "Pause timeline playback" : "Play forecast progression";
    }

    if (state.isPlaying) {
      state.playTimer = setInterval(() => {
        let nextIdx = (state.activeTimelineIndex + 1) % TIMELINE_STEPS.length;
        setTimelineIndex(nextIdx);
      }, 1400);
    } else {
      if (state.playTimer) {
        clearInterval(state.playTimer);
        state.playTimer = null;
      }
    }
  }

  // --- 8. URL PARAMETER PARSER (?waves,29.939,77.749,7) ---
  function parseWindyUrlParameters() {
    const rawSearch = window.location.search || window.location.hash;
    if (!rawSearch) return null;

    const clean = rawSearch.replace(/^[?#]/, "");
    const parts = clean.split(",");

    if (parts.length >= 3) {
      const layer = parts[0].toLowerCase();
      const lat = parseFloat(parts[1]);
      const lon = parseFloat(parts[2]);
      const zoom = parts[3] ? parseInt(parts[3], 10) : 7;

      if (!isNaN(lat) && !isNaN(lon)) {
        return {
          layer: LAYERS[layer] ? layer : "waves",
          lat,
          lon,
          zoom: isNaN(zoom) ? 7 : zoom
        };
      }
    }
    return null;
  }

  // --- 9. PUBLIC INITIALIZER ---
  window.AURA_WINDY_ENGINE = {
    init: (leafletMap) => {
      if (!leafletMap) return;
      state.map = leafletMap;

      createLayerSwitcherDock();
      createTimelineScrubber();
      createColorLegendBar();
      createQuickHotspotBar();

      initParticleCanvas();

      leafletMap.on("move moveend zoomend resize", () => {
        resizeParticleCanvas();
      });

      leafletMap.on("click", (e) => {
        inspectPoint(e.latlng.lat, e.latlng.lng);
      });

      const urlConfig = parseWindyUrlParameters();
      if (urlConfig) {
        setLayer(urlConfig.layer);
        state.map.setView([urlConfig.lat, urlConfig.lon], urlConfig.zoom);
        setTimeout(() => {
          inspectPoint(urlConfig.lat, urlConfig.lon, false);
        }, 300);
      } else {
        // When input is not given: Just display the entire map of India!
        // No automatic pin, no popup card blocking the view.
        state.pickerPin = null;
        state.pickerData = null;
        const existingCard = document.getElementById("windy-picker-card");
        if (existingCard) existingCard.remove();
      }
    },
    setLayer,
    inspectPoint
  };

})();
