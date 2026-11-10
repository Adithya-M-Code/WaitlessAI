import React, { useState, useEffect } from 'react';

// Chennai geographic boundaries for coordinate projection
const CHENNAI_BBOX = {
  min_lat: 12.82,
  max_lat: 13.20,
  min_lon: 80.08,
  max_lon: 80.32
};

export default function LiveMap({ vehicles = [], onSelectBus, selectedRouteId }) {
  const [selectedBus, setSelectedBus] = useState(null);
  const [animatedVehicles, setAnimatedVehicles] = useState(vehicles);

  // Smooth position interpolation simulation
  useEffect(() => {
    setAnimatedVehicles(vehicles);
  }, [vehicles]);

  // Project lat/lon into SVG viewBox 0..800 (width) x 0..600 (height)
  const projectCoords = (lat, lon) => {
    const x = ((lon - CHENNAI_BBOX.min_lon) / (CHENNAI_BBOX.max_lon - CHENNAI_BBOX.min_lon)) * 800;
    // Invert Y because latitude increases upwards
    const y = 600 - (((lat - CHENNAI_BBOX.min_lat) / (CHENNAI_BBOX.max_lat - CHENNAI_BBOX.min_lat)) * 600);
    return [Math.max(20, Math.min(780, x)), Math.max(20, Math.min(580, y))];
  };

  // Prominent Chennai Landmarks for the Map Canvas
  const landmarks = [
    { name: "Broadway Terminus", lat: 13.0878, lon: 80.2871 },
    { name: "Chennai Central", lat: 13.0827, lon: 80.2755 },
    { name: "Marina Beach", lat: 13.0500, lon: 80.2824 },
    { name: "DMS Teynampet", lat: 13.0450, lon: 80.2480 },
    { name: "T. Nagar Terminus", lat: 13.0400, lon: 80.2340 },
    { name: "CMBT Koyambedu", lat: 13.0680, lon: 80.1980 },
    { name: "Guindy Asiad", lat: 13.0067, lon: 80.2025 },
    { name: "Adyar Depot", lat: 13.0060, lon: 80.2550 },
    { name: "Velachery", lat: 12.9750, lon: 80.2200 },
    { name: "Tambaram West", lat: 12.9249, lon: 80.1170 },
    { name: "Airport", lat: 12.9856, lon: 80.1706 },
    { name: "Siruseri IT Park", lat: 12.8280, lon: 80.2180 }
  ];

  return (
    <div className="relative w-full h-[520px] rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 shadow-inner select-none">
      {/* Light Cartographic Basemap Canvas */}
      <svg 
        viewBox="0 0 800 600" 
        className="w-full h-full object-cover"
        style={{ background: "radial-gradient(circle at 60% 40%, #f1f5f9 0%, #e2e8f0 100%)" }}
      >
        <defs>
          {/* Subtle water texture for Bay of Bengal on the right */}
          <linearGradient id="oceanGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#e2e8f0" stopOpacity="0.1" />
            <stop offset="60%" stopColor="#bae6fd" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#7dd3fc" stopOpacity="0.6" />
          </linearGradient>
        </defs>

        {/* Coastline / Bay of Bengal */}
        <path
          d="M 680 0 Q 640 250 670 420 Q 690 520 730 600 L 800 600 L 800 0 Z"
          fill="url(#oceanGrad)"
        />

        {/* Arterial Road Network Polylines (Mount Road / GST / OMR) */}
        {/* GST Road: Central -> Guindy -> Tambaram */}
        <path
          d="M 650 160 Q 560 280 480 340 T 320 500"
          fill="none"
          stroke="#cbd5e1"
          strokeWidth="6"
          strokeLinecap="round"
          className="dark:stroke-slate-800"
        />
        {/* OMR IT Corridor: Adyar -> Velachery -> Siruseri */}
        <path
          d="M 610 340 Q 580 420 540 580"
          fill="none"
          stroke="#cbd5e1"
          strokeWidth="5"
          strokeLinecap="round"
          className="dark:stroke-slate-800"
        />
        {/* Inner Ring Road: CMBT -> Guindy */}
        <path
          d="M 460 210 Q 480 280 480 340"
          fill="none"
          stroke="#cbd5e1"
          strokeWidth="4"
          className="dark:stroke-slate-800"
        />

        {/* Landmark Stops */}
        {landmarks.map((lm, idx) => {
          const [cx, cy] = projectCoords(lm.lat, lm.lon);
          return (
            <g key={idx} className="cursor-pointer group">
              <circle cx={cx} cy={cy} r="4.5" fill="#94a3b8" stroke="#ffffff" strokeWidth="2" />
              <text
                x={cx + 7}
                y={cy + 3}
                fontSize="9"
                fontWeight="500"
                fill="#475569"
                className="dark:fill-slate-400 select-none pointer-events-none"
              >
                {lm.name}
              </text>
            </g>
          );
        })}

        {/* Moving Buses with Heading Arrows & Live Pulse */}
        {animatedVehicles.map((v, i) => {
          const [vx, vy] = projectCoords(v.lat || 13.04, v.lon || 80.24);
          const heading = v.heading_deg || (i * 75) % 360;
          const isSelected = selectedBus?.vehicle_no === v.vehicle_no;
          const isLiveTier = v.tier === 'live';

          return (
            <g
              key={v.vehicle_no || i}
              transform={`translate(${vx}, ${vy})`}
              onClick={() => {
                setSelectedBus(v);
                if (onSelectBus) onSelectBus(v);
              }}
              className="cursor-pointer transition-transform duration-500 ease-out"
            >
              {/* Radar pulse ring for live vehicles */}
              {isLiveTier && (
                <circle
                  r="14"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="1.5"
                  className="animate-bus-radar pointer-events-none"
                />
              )}

              {/* Service Tier Ring */}
              <circle
                r="13"
                fill="#ffffff"
                stroke={isLiveTier ? "#10b981" : "#f59e0b"}
                strokeWidth="2.5"
                filter="drop-shadow(0 2px 4px rgba(0,0,0,0.15))"
              />

              {/* 🚌 Bus Emoji Badge */}
              <text
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="11"
                className="select-none pointer-events-none"
              >
                🚌
              </text>

              {/* Rotating Heading Arrow on border */}
              <g transform={`rotate(${heading})`}>
                <polygon
                  points="0,-16 -3,-12 3,-12"
                  fill={isLiveTier ? "#10b981" : "#f59e0b"}
                />
              </g>

              {/* Route Label Pill */}
              <rect
                x="-16"
                y="15"
                width="32"
                height="13"
                rx="3"
                fill={isSelected ? "#2563eb" : "#0f172a"}
              />
              <text
                x="0"
                y="24"
                textAnchor="middle"
                fontSize="8"
                fontWeight="700"
                fill="#ffffff"
                className="select-none pointer-events-none font-mono"
              >
                {v.route_id || "17D"}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Selected Bus Floating Popover */}
      {selectedBus && (
        <div className="absolute top-4 left-4 z-20 w-72 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md rounded-xl p-4 shadow-xl border border-slate-200 dark:border-slate-800 text-xs space-y-3">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-sm text-slate-900 dark:text-white">
                  {selectedBus.vehicle_no}
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                  Route {selectedBus.route_id}
                </span>
              </div>
              <p className="text-slate-500 text-[11px] mt-0.5">
                {selectedBus.direction_label || "towards Destination"}
              </p>
            </div>
            <button
              onClick={() => setSelectedBus(null)}
              aria-label="Close bus details"
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-base"
            >
              &times;
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-100 dark:border-slate-800 text-[11px]">
            <div>
              <span className="text-slate-400 block">Speed</span>
              <span className="font-bold text-slate-700 dark:text-slate-200">
                {selectedBus.speed_kmh || 24} km/h
              </span>
            </div>
            <p className="text-[11px] text-slate-500 border-t border-slate-100 dark:border-slate-800 pt-2">
              {selectedBus.tier === 'live' ? 'Live tracking' : selectedBus.tier === 'recent' ? 'Recently observed' : 'Schedule-based estimate'}
              {selectedBus.age_s != null ? ` · updated ${Math.round(selectedBus.age_s)}s ago` : ''}
            </p>
            <div>
              <span className="text-slate-400 block">Crowding</span>
              <span className={`font-bold ${selectedBus.crowding_class === 'High' ? 'text-rose-500' : 'text-emerald-500'}`}>
                {selectedBus.crowding_class || 'Medium'} ({selectedBus.passenger_count || 28} riders)
              </span>
            </div>
          </div>

          {/* Button-Gated Action: Predict this bus */}
          <button
            onClick={() => {
              if (onSelectBus) onSelectBus(selectedBus);
            }}
            className="w-full py-2 px-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold transition shadow-sm text-center"
          >
            Predict This Bus &rarr;
          </button>
        </div>
      )}

      {/* Map Legend & CARTO Attribution */}
      <div className="absolute bottom-2 right-2 bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm px-2.5 py-1 rounded-md text-[10px] text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center gap-2">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span> Live telemetry
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-amber-500 inline-block"></span> Schedule estimate
        </span>
        <span>• © OpenStreetMap, © CARTO</span>
      </div>
    </div>
  );
}
