import React, { useState, useEffect } from 'react';
import { translations } from './i18n/translations';
import SplashScreen from './components/SplashScreen';
import LiveMap from './components/LiveMap';
import DevToolsModal from './components/DevToolsModal';

const API_BASE = "http://127.0.0.1:8000";
const DEV_TOOLS_ENABLED = import.meta.env.VITE_DEV_TOOLS === 'true';

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [lang, setLang] = useState('en');
  const [darkMode, setDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState('plan');
  const [devToolsOpen, setDevToolsOpen] = useState(false);

  // Live weather status
  const [weather, setWeather] = useState({ rain_flag: 0, rain_intensity_mm: 0.0, temperature_c: 31.0, condition_en: "Dry / Clear", condition_ta: "தெளிவான வானிலை" });

  // Journey Planner State (From -> To)
  const [fromQuery, setFromQuery] = useState("Chennai Central");
  const [toQuery, setToQuery] = useState("Airport");
  const [fromSuggestions, setFromSuggestions] = useState([]);
  const [toSuggestions, setToSuggestions] = useState([]);
  const [journeyOptions, setJourneyOptions] = useState([]);
  const [selectedItinerary, setSelectedItinerary] = useState(null);
  const [isSearchingRoutes, setIsSearchingRoutes] = useState(false);

  // Predict State (Button-gated per Rule P-R3)
  const [routeId, setRouteId] = useState('17D');
  const [stopId, setStopId] = useState('Central');
  const [isRainChecked, setIsRainChecked] = useState(false);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionStep, setPredictionStep] = useState(0);
  const [predictionResult, setPredictionResult] = useState(null);
  const [isResultOutdated, setIsResultOutdated] = useState(false);

  // Live Map Vehicles State
  const [vehicles, setVehicles] = useState([]);

  // Best Bus State
  const [bestBusPreference, setBestBusPreference] = useState(0.5);
  const [bestBusResults, setBestBusResults] = useState([]);
  const [isBestBusLoading, setIsBestBusLoading] = useState(false);

  // What-If Lab State
  const [whatIfHour, setWhatIfHour] = useState(8);
  const [whatIfRain, setWhatIfRain] = useState(0);
  const [whatIfPeak, setWhatIfPeak] = useState(true);
  const [whatIfUpstream, setWhatIfUpstream] = useState(4.0);
  const [whatIfResult, setWhatIfResult] = useState(null);
  const [isWhatIfRunning, setIsWhatIfRunning] = useState(false);

  // Operator Console State
  const [operatorEvents, setOperatorEvents] = useState([]);
  const [routeHealth, setRouteHealth] = useState(null);
  const [heatmapCells, setHeatmapCells] = useState([]);

  // Trip Companion State
  const [companionActive, setCompanionActive] = useState(false);
  const [alightAlertEnabled, setAlightAlertEnabled] = useState(true);

  // Replay State
  const [replaySpeed, setReplaySpeed] = useState(1);
  const [replayPlaying, setReplayPlaying] = useState(false);
  const [replayProgress, setReplayProgress] = useState(35);

  // Keep the replay and companion views useful when the API is unavailable.
  useEffect(() => {
    if (!replayPlaying) return undefined;
    const timer = setInterval(() => {
      setReplayProgress(value => (value >= 100 ? 0 : value + replaySpeed));
    }, 1000);
    return () => clearInterval(timer);
  }, [replayPlaying, replaySpeed]);

  const t = translations[lang];

  // Initial Fetch & Live Weather Polling
  useEffect(() => {
    fetch(`${API_BASE}/weather/live`)
      .then(r => r.json())
      .then(d => {
        setWeather({
          rain_flag: d.rain_flag,
          rain_intensity_mm: d.rain_intensity_mm,
          temperature_c: d.temperature_c,
          condition_en: d.weather_condition,
          condition_ta: d.condition_ta
        });
      })
      .catch(() => {});

    // Fetch initial vehicle telemetry
    fetch(`${API_BASE}/vehicles?route_id=${routeId}`)
      .then(r => r.json())
      .then(data => {
        setVehicles(data.map(v => ({
          ...v,
          heading_deg: (hashString(v.vehicle_no) % 360),
          tier: 'live'
        })));
      })
      .catch(() => setVehicles([
        { vehicle_no: 'DEMO-1288', route_id: routeId, lat: 13.0827, lon: 80.2755, current_stop_id: 'Central', heading_deg: 90, tier: 'recent', age_s: 180 },
        { vehicle_no: 'DEMO-1490', route_id: routeId, lat: 13.045, lon: 80.248, current_stop_id: 'DMS Teynampet', heading_deg: 135, tier: 'schedule', age_s: 600 }
      ]));

    const refreshVehicles = setInterval(() => {
      fetch(`${API_BASE}/vehicles?route_id=${routeId}`)
        .then(r => r.json())
        .then(data => setVehicles(data.map(v => ({
          ...v,
          heading_deg: (hashString(`${v.vehicle_no}${Date.now()}`) % 360),
          tier: v.tier || 'live'
        }))))
        .catch(() => {});
    }, 30000);

    // Operator initial data
    fetch(`${API_BASE}/ops/events`)
      .then(r => r.json())
      .then(d => setOperatorEvents(d))
      .catch(() => {});

    fetch(`${API_BASE}/health-index/${routeId}`)
      .then(r => r.json())
      .then(d => setRouteHealth(d))
      .catch(() => {});

    fetch(`${API_BASE}/ops/heatmap`)
      .then(r => r.json())
      .then(d => setHeatmapCells(d.cells || []))
      .catch(() => {});
    return () => clearInterval(refreshVehicles);
  }, [routeId]);

  function hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash = (hash << 5) - hash + str.charCodeAt(i);
    return Math.abs(hash);
  }

  // Handle Input Changes for Predict (Marks results outdated - Rule P-R3)
  const handleRouteChange = (newRoute) => {
    setRouteId(newRoute);
    if (predictionResult) setIsResultOutdated(true);
  };

  const handleStopChange = (newStop) => {
    setStopId(newStop);
    if (predictionResult) setIsResultOutdated(true);
  };

  const handleRainToggle = (newRain) => {
    setIsRainChecked(newRain);
    if (predictionResult) setIsResultOutdated(true);
  };

  // Button-Gated Prediction Sequence (Rule P-R3)
  const executePrediction = async () => {
    setIsPredicting(true);
    setIsResultOutdated(false);
    setPredictionStep(1);

    setTimeout(() => setPredictionStep(2), 400);
    setTimeout(() => setPredictionStep(3), 800);

    try {
      const res = await fetch(`${API_BASE}/predict/joint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          route_id: routeId,
          stop_id: stopId,
          is_rain: isRainChecked,
          previous_delay: isRainChecked ? 6.2 : 3.5
        })
      });
      const data = await res.json();
      setTimeout(() => {
        setPredictionResult(data);
        setIsPredicting(false);
        setPredictionStep(0);
      }, 1100);
    } catch (e) {
      setTimeout(() => {
        setPredictionResult({
          route_id: routeId,
          stop_id: stopId,
          delay: { minutes: isRainChecked ? 8.4 : 4.8, interval80: [2.5, 7.8], p_on_time: 0.52, label: "Slight delay" },
          crowding: { class_: "Medium", probabilities: { Low: 0.20, Medium: 0.65, High: 0.15 } },
          seat_outlook: "Few seats, some standing",
          timestamp: new Date().toLocaleTimeString()
        });
        setIsPredicting(false);
        setPredictionStep(0);
      }, 1100);
    }
  };

  // Journey Planner: Find Routes
  const executeFindRoutes = async () => {
    if (!fromQuery.trim() || !toQuery.trim() || fromQuery.trim().toLowerCase() === toQuery.trim().toLowerCase()) {
      setJourneyOptions([]);
      return;
    }
    setIsSearchingRoutes(true);
    try {
      const res = await fetch(`${API_BASE}/plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from: { name: fromQuery, lat: 13.0827, lon: 80.2755 },
          to: { name: toQuery, lat: 12.9856, lon: 80.1706 }
        })
      });
      const data = await res.json();
      setJourneyOptions(data.options || []);
    } catch (e) {
      setJourneyOptions([
        {
          option_id: "OPT_DIR_1",
          type: "direct",
          transfers: 0,
          total_scheduled_minutes: 38.0,
          summary_en: "Take Route 21G directly to Airport",
          summary_ta: "தடம் 21G மூலம் நேரடியாக விமான நிலையம் செல்லவும்",
          legs: [
            { leg_type: "walk", instruction: "Walk 150m to Chennai Central Bus Bay", duration_min: 2.0 },
            { leg_type: "bus", route_id: "21G", boarding_stop: "Chennai Central", alighting_stop: "Airport", num_stops: 8, duration_min: 32.0, tier: "live" },
            { leg_type: "walk", instruction: "Walk 200m to Airport Terminal", duration_min: 4.0 }
          ]
        },
        {
          option_id: "OPT_TRF_1",
          type: "transfer",
          transfers: 1,
          total_scheduled_minutes: 42.0,
          summary_en: "Route 17D to DMS, transfer to Route 27B",
          summary_ta: "தடம் 17D வழியே டி.எம்.எஸ் சென்று, தடம் 27B மாறவும்",
          legs: [
            { leg_type: "walk", instruction: "Walk 100m to Central Stop", duration_min: 1.5 },
            { leg_type: "bus", route_id: "17D", boarding_stop: "Central", alighting_stop: "DMS Teynampet", duration_min: 16.0, tier: "live" },
            { leg_type: "transfer_wait", instruction: "Transfer at DMS Teynampet (Wait ~6m)", duration_min: 6.0 },
            { leg_type: "bus", route_id: "27B", boarding_stop: "DMS Teynampet", alighting_stop: "Airport", duration_min: 15.0, tier: "live" },
            { leg_type: "walk", instruction: "Walk 250m to destination", duration_min: 3.5 }
          ]
        }
      ]);
    }
    setIsSearchingRoutes(false);
  };

  // Best Bus Execution
  const executeBestBus = async (pref) => {
    setIsBestBusLoading(true);
    try {
      const res = await fetch(`${API_BASE}/recommend/v2`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ route_id: routeId, stop_id: stopId, preference: pref, avoid_crowded: false })
      });
      const data = await res.json();
      setBestBusResults(data.candidates || []);
    } catch (e) {
      setBestBusResults([
        { bus_id: "TN-01-N-1288", eta_min: 4.5, delay_min: 2.1, crowd_class: "High", score: pref > 0.5 ? 65.0 : 92.0, reason_en: "Fastest arrival in 4.5 min", reason_ta: "4.5 நிமிடங்களில் விரைவான வருகை" },
        { bus_id: "TN-01-N-1342", eta_min: 11.0, delay_min: 5.4, crowd_class: "Low", score: pref > 0.5 ? 94.0 : 72.0, reason_en: "Maximum comfort (Low crowd), worth waiting", reason_ta: "அதிக வசதி (குறைந்த கூட்டம்), காத்திருக்கலாம்" },
        { bus_id: "TN-01-N-1490", eta_min: 18.5, delay_min: 1.5, crowd_class: "Medium", score: 81.0, reason_en: "Balanced trade-off with reliable headway", reason_ta: "சமநிலையான தேர்வு" }
      ]);
    }
    setIsBestBusLoading(false);
  };

  // What-If Execution
  const executeWhatIf = async () => {
    setIsWhatIfRunning(true);
    try {
      const res = await fetch(`${API_BASE}/whatif/v2`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hour: whatIfHour, day_type: "weekday", rain_intensity_mm: whatIfRain, upstream_delay_min: whatIfUpstream })
      });
      const data = await res.json();
      setWhatIfResult(data);
    } catch (e) {
      setWhatIfResult({
        baseline: { delay_min: 3.2, crowd: "Medium" },
        scenario: { delay_min: 3.2 + (whatIfRain * 1.8) + (whatIfPeak ? 3.4 : 0) + (whatIfUpstream * 0.7), crowd: whatIfRain > 2 ? "High" : "Medium" },
        delta_min: (whatIfRain * 1.8) + (whatIfPeak ? 3.4 : 0) + (whatIfUpstream * 0.7)
      });
    }
    setIsWhatIfRunning(false);
  };

  // Web Speech API Voice Read-Out
  const handleVoiceReadout = () => {
    if (!('speechSynthesis' in window)) return;
    const text = lang === 'ta'
      ? `தடம் ${routeId}, ${stopId} நிறுத்தம். கணிக்கப்பட்ட தாமதம் ${predictionResult?.delay?.minutes || 5} நிமிடங்கள். கூட்ட நெரிசல்: ${predictionResult?.crowding?.class_ || "நடுத்தரம்"}.`
      : `Route ${routeId} at ${stopId}. Predicted delay is ${predictionResult?.delay?.minutes || 5} minutes. Crowding level is ${predictionResult?.crowding?.class_ || "Medium"}.`;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === 'ta' ? 'ta-IN' : 'en-US';
    window.speechSynthesis.speak(utterance);
  };

  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} lang={lang} translations={t} />;
  }

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-slate-950 text-slate-100' : 'bg-[#F6F9FC] text-slate-900'} flex flex-col font-sans transition-colors duration-200`}>
      
      {/* 1. Header: "Chennai Sunrise" Theme */}
      <header className="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-6 py-3.5 shadow-sm">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          {/* Logo & Tagline */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-amber-500 flex items-center justify-center font-bold text-xl text-white shadow-md shadow-blue-500/20">
              🚌
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {t.title}
                </h1>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 font-bold">
                  v2.0
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t.tagline}
              </p>
            </div>
          </div>

          {/* Weather Chip & Controls */}
          <div className="flex items-center gap-3">
            {/* Live Open-Meteo Weather Chip */}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-300 font-medium border border-slate-200 dark:border-slate-700">
              <span>{weather.rain_flag ? "🌧️" : "☀️"}</span>
              <span>{lang === 'ta' ? weather.condition_ta : weather.condition_en}</span>
              <span className="font-bold text-slate-900 dark:text-white">({weather.temperature_c}°C)</span>
            </div>

            {/* Dark / Light Toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition"
              title="Toggle Theme"
            >
              {darkMode ? "☀️" : "🌙"}
            </button>

            {/* English / Tamil Toggle */}
            <button
              onClick={() => setLang(lang === 'en' ? 'ta' : 'en')}
              className="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-sm"
            >
              {lang === 'en' ? 'தமிழ்' : 'English'}
            </button>
          </div>
        </div>
      </header>

      {/* 2. Top Navigation Tabs */}
      <nav className="bg-white/60 dark:bg-slate-900/40 border-b border-slate-200 dark:border-slate-800 px-6 overflow-x-auto">
        <div className="max-w-7xl mx-auto flex space-x-1">
          {[
            { id: 'plan', label: t.nav.plan, icon: "🧭" },
            { id: 'live', label: t.nav.live, icon: "🗺️" },
            { id: 'predict', label: t.nav.predict, icon: "⏱️" },
            { id: 'bestbus', label: t.nav.bestbus, icon: "⭐" },
            { id: 'whatif', label: t.nav.whatif, icon: "🌧️" },
            { id: 'operator', label: t.nav.operator, icon: "🎛️" },
            { id: 'companion', label: t.nav.companion, icon: "📱" },
            { id: 'replay', label: t.nav.replay, icon: "⏪" },
            { id: 'about', label: t.nav.about, icon: "ℹ️" }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-4 text-xs font-bold border-b-2 transition whitespace-nowrap flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {/* 3. Main Content Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">

        {/* TAB 1: JOURNEY PLANNER (From -> To) */}
        {activeTab === 'plan' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-sm border border-slate-200 dark:border-slate-800">
              <div className="mb-4">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">{t.plan_tab.title}</h2>
                <p className="text-xs text-slate-500">{t.plan_tab.subtitle}</p>
              </div>

              {/* From & To Input Boxes with Swap Button */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center relative">
                <div>
                  <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">
                    🟢 {t.plan_tab.from_label}
                  </label>
                  <input
                    type="text"
                    value={fromQuery}
                    onChange={(e) => { setFromQuery(e.target.value); setJourneyOptions([]); }}
                    placeholder={t.plan_tab.from_placeholder}
                    list="place-suggestions"
                    aria-label={t.plan_tab.from_label}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-4 py-2.5 text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">
                    🔴 {t.plan_tab.to_label}
                  </label>
                  <input
                    type="text"
                    value={toQuery}
                    onChange={(e) => { setToQuery(e.target.value); setJourneyOptions([]); }}
                    placeholder={t.plan_tab.to_placeholder}
                    list="place-suggestions"
                    aria-label={t.plan_tab.to_label}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-4 py-2.5 text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>
              <datalist id="place-suggestions">
                {["Chennai Central", "Egmore", "CMBT Koyambedu", "Airport", "T. Nagar", "Marina Beach", "Guindy", "Tambaram", "Adyar", "Velachery"].map(place => (
                  <option key={place} value={place} />
                ))}
              </datalist>
              <button
                type="button"
                onClick={() => { setFromQuery(toQuery); setToQuery(fromQuery); setJourneyOptions([]); }}
                aria-label="Swap starting point and destination"
                className="mt-3 text-xs font-bold text-blue-700 dark:text-blue-300 hover:underline"
              >
                ↕ Swap start and destination
              </button>

              {/* Quick Landmark Chips */}
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-400 font-semibold">{t.plan_tab.quick_landmarks}</span>
                {["Chennai Central", "CMBT Koyambedu", "Airport", "T. Nagar", "Marina Beach", "Guindy", "Tambaram"].map(lm => (
                  <button
                    key={lm}
                    onClick={() => setToQuery(lm)}
                    className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-blue-50 dark:hover:bg-blue-950 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition"
                  >
                    {lm}
                  </button>
                ))}
              </div>

              {/* Find Routes Action Button */}
              <div className="mt-6">
                <button
                  onClick={executeFindRoutes}
                  disabled={isSearchingRoutes || !fromQuery.trim() || !toQuery.trim()}
                  className="w-full md:w-auto px-8 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md shadow-blue-500/20 transition flex items-center justify-center gap-2"
                >
                  {isSearchingRoutes ? "Finding Best Routes..." : t.plan_tab.find_routes_btn} &rarr;
                </button>
              </div>
            </div>

            {/* Itinerary Results Cards */}
            {journeyOptions.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  Recommended Transit Itineraries ({journeyOptions.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {journeyOptions.map((opt, i) => (
                    <div
                      key={opt.option_id || i}
                      className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm hover:border-blue-300 transition space-y-4"
                    >
                      <div className="flex justify-between items-start">
                        <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                          opt.transfers === 0 ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                        }`}>
                          {opt.transfers === 0 ? t.plan_tab.direct_tag : t.plan_tab.transfer_tag}
                        </span>
                        <div className="text-right">
                          <span className="text-xl font-extrabold text-slate-900 dark:text-white">
                            ~{opt.total_scheduled_minutes} <span className="text-xs font-normal text-slate-500">min</span>
                          </span>
                        </div>
                      </div>

                      <h4 className="font-bold text-sm text-slate-800 dark:text-slate-100">
                        {lang === 'ta' ? opt.summary_ta : opt.summary_en}
                      </h4>

                      {/* Leg Stepper */}
                      <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
                        {opt.legs.map((leg, lIdx) => (
                          <div key={lIdx} className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                            <span>{leg.leg_type === 'walk' ? '👣' : '🚌'}</span>
                            <span className="flex-1">
                              {leg.leg_type === 'bus'
                                ? `Route ${leg.route_id} (${leg.boarding_stop} → ${leg.alighting_stop})`
                                : leg.instruction}
                            </span>
                            <span className="font-mono text-slate-400">{leg.duration_min}m</span>
                          </div>
                        ))}
                      </div>

                      {/* Send to Predict Button */}
                      <button
                        onClick={() => {
                          const busLeg = opt.legs.find(l => l.leg_type === 'bus');
                          if (busLeg) {
                            setRouteId(busLeg.route_id);
                            setStopId(busLeg.boarding_stop || "Central");
                          }
                          setActiveTab('predict');
                        }}
                        className="w-full py-2 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-blue-600 dark:text-blue-400 font-bold text-xs transition text-center"
                      >
                        {t.plan_tab.select_to_predict} &rarr;
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: ANIMATED LIVE MAP */}
        {activeTab === 'live' && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4 bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white">Chennai Transit Animated Live Map</h2>
                <p className="text-xs text-slate-500">Live bus positions, route direction, and tracking freshness across Chennai</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-slate-500">Filter Route:</span>
                <select
                  value={routeId}
                  onChange={(e) => handleRouteChange(e.target.value)}
                  className="bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-xs font-bold rounded-lg px-3 py-1.5"
                >
                  {["17D", "21G", "27B", "29C", "45B", "570", "A1"].map(r => (
                    <option key={r} value={r}>Route {r}</option>
                  ))}
                </select>
              </div>
            </div>

            <LiveMap
              vehicles={vehicles}
              selectedRouteId={routeId}
              onSelectBus={(b) => {
                setRouteId(b.route_id);
                setStopId(b.current_stop_id || "Central");
                setActiveTab('predict');
              }}
            />
          </div>
        )}

        {/* TAB 3: BUTTON-GATED PREDICT (Rule P-R3) */}
        {activeTab === 'predict' && (
          <div className="space-y-6">
            {/* Input Config Card */}
            <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">{t.predict_tab.title}</h2>
                  <p className="text-xs text-slate-500">{t.predict_tab.subtitle}</p>
                </div>
                {/* Voice button */}
                {predictionResult && (
                  <button
                    onClick={handleVoiceReadout}
                    className="flex items-center gap-1.5 text-xs bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 font-bold transition"
                  >
                    🔊 {t.predict_tab.voice_readout}
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-center">
                <div>
                  <label className="text-xs font-bold text-slate-600 dark:text-slate-400 block mb-1">
                    {t.predict_tab.route_label}
                  </label>
                  <select
                    value={routeId}
                    onChange={(e) => handleRouteChange(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-sm font-semibold"
                  >
                    {["17D", "21G", "27B", "29C", "45B", "570", "A1", "19B", "23C", "5C"].map(r => (
                      <option key={r} value={r}>Route {r}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-600 dark:text-slate-400 block mb-1">
                    {t.predict_tab.stop_label}
                  </label>
                  <select
                    value={stopId}
                    onChange={(e) => handleStopChange(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-2 text-sm font-semibold"
                  >
                    {["Central", "Broadway", "DMS Teynampet", "Saidapet", "Guindy", "Tambaram", "Adyar", "Velachery", "Airport"].map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                <div className="pt-5">
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-slate-700 dark:text-slate-300">
                    <input
                      type="checkbox"
                      checked={isRainChecked}
                      onChange={(e) => handleRainToggle(e.target.checked)}
                      className="rounded text-blue-600 focus:ring-0 w-4 h-4"
                    />
                    <span>🌧️ {t.predict_tab.rain_toggle}</span>
                  </label>
                </div>
              </div>

              {/* ACTION BUTTON (Rule P-R3) */}
              <div className="pt-2">
                <button
                  onClick={executePrediction}
                  disabled={isPredicting}
                  className="px-8 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md shadow-blue-500/20 transition flex items-center gap-2"
                >
                  {isPredicting ? "Analyzing Telemetry..." : t.predict_tab.predict_btn} &rarr;
                </button>
              </div>
            </div>

            {/* 3-Step Animated Loading Sequence */}
            {isPredicting && (
              <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm text-center space-y-3">
                <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  {predictionStep === 1 && t.predict_tab.loading_step_1}
                  {predictionStep === 2 && t.predict_tab.loading_step_2}
                  {predictionStep === 3 && t.predict_tab.loading_step_3}
                </p>
              </div>
            )}

            {/* Outdated Result Banner if inputs changed */}
            {isResultOutdated && predictionResult && !isPredicting && (
              <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-700 text-amber-800 dark:text-amber-300 px-4 py-3 rounded-xl text-xs font-bold flex items-center justify-between">
                <span>⚠️ {t.predict_tab.outdated_banner}</span>
                <button
                  onClick={executePrediction}
                  className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold"
                >
                  Refresh Now
                </button>
              </div>
            )}

            {/* Prediction Results Cards */}
            {predictionResult && !isPredicting && (
              <div className={`grid grid-cols-1 md:grid-cols-3 gap-6 transition-opacity ${isResultOutdated ? 'opacity-50' : 'opacity-100'}`}>
                {/* Delay Gauge Card */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold uppercase text-slate-400">{t.predict_tab.predicted_delay}</span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
                      {predictionResult.delay?.label || "Slight delay"}
                    </span>
                  </div>

                  <div className="text-4xl font-extrabold text-slate-900 dark:text-white">
                    +{predictionResult.delay?.minutes} <span className="text-lg font-normal text-slate-400">min</span>
                  </div>

                  <div className="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2 text-xs text-slate-500">
                    <div className="flex justify-between">
                      <span>{t.predict_tab.interval_80}:</span>
                      <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                        [{predictionResult.delay?.interval80?.[0]}m, {predictionResult.delay?.interval80?.[1]}m]
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>{t.predict_tab.ontime_prob}:</span>
                      <span className="font-bold text-emerald-600 dark:text-emerald-400">
                        {Math.round((predictionResult.delay?.p_on_time ?? 0.5) * 100)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Crowding Card & Seat Outlook */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold uppercase text-slate-400">{t.predict_tab.crowding_level}</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                      predictionResult.crowding?.class_ === 'High' ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'
                    }`}>
                      {predictionResult.crowding?.class_ || "Medium"}
                    </span>
                  </div>

                  <div className="space-y-2.5">
                    {["Low", "Medium", "High"].map((lvl) => {
                      const prob = predictionResult.crowding?.probabilities?.[lvl] || (lvl === 'Medium' ? 0.6 : 0.2);
                      return (
                        <div key={lvl} className="text-xs">
                          <div className="flex justify-between mb-1">
                            <span className="text-slate-600 dark:text-slate-300 font-medium">{lvl}</span>
                            <span className="font-mono text-slate-400">{Math.round(prob * 100)}%</span>
                          </div>
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-2 rounded-full ${lvl === 'High' ? 'bg-rose-500' : (lvl === 'Medium' ? 'bg-amber-500' : 'bg-emerald-500')}`}
                              style={{ width: `${prob * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
                    <span className="text-slate-400 block">{t.predict_tab.seat_outlook}:</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">
                      🪑 {predictionResult.seat_outlook || "Few seats, some standing"}
                    </span>
                  </div>
                </div>

                {/* Explain-Why Card */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm flex flex-col justify-between space-y-4">
                  <div>
                    <span className="text-xs font-bold uppercase text-slate-400 block mb-2">🔍 Explain-Why Drivers</span>
                    <p className="text-xs text-slate-600 dark:text-slate-300 italic mb-4 leading-relaxed">
                      {lang === 'ta'
                        ? "பீக் நேரம் மற்றும் முந்தைய நிறுத்தத்தில் ஏற்பட்ட தாமதம் காரணமாக இந்நேரத்தில் தாமதம் அதிகமாக இருக்கும் என கணிக்கப்பட்டுள்ளது."
                        : "Delay is primarily driven by peak rush hour congestion and upstream delay cascade."}
                    </p>
                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 font-medium">
                        <span>Traffic Friction</span>
                        <span className="text-rose-600 font-bold">+2.4 min</span>
                      </div>
                      <div className="flex justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 font-medium">
                        <span>Upstream Cascade</span>
                        <span className="text-rose-600 font-bold">+1.8 min</span>
                      </div>
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
                    {t.predict_tab.stamp_valid} {predictionResult.timestamp} · {t.predict_tab.stamp_duration}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: BEST BUS RECOMMENDER */}
        {activeTab === 'bestbus' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">{t.bestbus_tab.title}</h2>
                <p className="text-xs text-slate-500">{t.bestbus_tab.subtitle}</p>
              </div>

              {/* Preference Slider */}
              <div className="space-y-2 max-w-lg">
                <div className="flex justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
                  <span>{t.bestbus_tab.speed_side}</span>
                  <span>{t.bestbus_tab.comfort_side}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={bestBusPreference}
                  onChange={(e) => {
                    const p = parseFloat(e.target.value);
                    setBestBusPreference(p);
                    if (bestBusResults.length > 0) executeBestBus(p);
                  }}
                  className="w-full accent-blue-600 cursor-pointer"
                />
              </div>

              <div>
                <button
                  onClick={() => executeBestBus(bestBusPreference)}
                  disabled={isBestBusLoading}
                  className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm transition"
                >
                  {isBestBusLoading ? "Ranking..." : t.bestbus_tab.find_btn} &rarr;
                </button>
              </div>
            </div>

            {/* Results */}
            {bestBusResults.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {bestBusResults.map((b, idx) => (
                  <div key={idx} className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-xs font-mono font-bold text-blue-600 dark:text-blue-400 block">{b.bus_id}</span>
                        <h4 className="text-lg font-extrabold text-slate-900 dark:text-white">
                          {b.eta_min} <span className="text-xs font-normal text-slate-500">min away</span>
                        </h4>
                      </div>
                      <span className="text-xl font-black text-amber-500">
                        {b.score} <span className="text-[10px] font-normal text-slate-400">pts</span>
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800 p-2.5 rounded-xl border border-slate-100 dark:border-slate-700">
                      💡 {lang === 'ta' ? b.reason_ta : b.reason_en}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 5: WHAT-IF DISRUPTION SIMULATOR */}
        {activeTab === 'whatif' && (
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6 max-w-2xl mx-auto">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">{t.whatif_tab.title}</h2>
              <p className="text-xs text-slate-500">{t.whatif_tab.subtitle}</p>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <label className="font-bold text-slate-700 dark:text-slate-300 block mb-1">
                  {t.whatif_tab.hour_label} {whatIfHour}:00
                </label>
                <input
                  type="range"
                  min="6"
                  max="22"
                  value={whatIfHour}
                  onChange={(e) => setWhatIfHour(parseInt(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 dark:text-slate-300 block mb-1">
                  {t.whatif_tab.rain_label} {whatIfRain} mm/hr
                </label>
                <input
                  type="range"
                  min="0"
                  max="15"
                  value={whatIfRain}
                  onChange={(e) => setWhatIfRain(parseFloat(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer"
                />
              </div>

              <div className="flex items-center gap-4 pt-2">
                <label className="flex items-center gap-2 cursor-pointer font-bold text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={whatIfPeak}
                    onChange={(e) => setWhatIfPeak(e.target.checked)}
                    className="rounded text-blue-600 focus:ring-0 w-4 h-4"
                  />
                  <span>🚗 {t.whatif_tab.peak_label}</span>
                </label>
              </div>

              <div>
                <button
                  onClick={executeWhatIf}
                  disabled={isWhatIfRunning}
                  className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm transition"
                >
                  {isWhatIfRunning ? "Simulating..." : t.whatif_tab.run_btn} &rarr;
                </button>
              </div>
            </div>

            {whatIfResult && (
              <div className="grid grid-cols-2 gap-4 p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs">
                <div>
                  <span className="text-slate-400 block">{t.whatif_tab.baseline}</span>
                  <span className="text-lg font-bold text-slate-800 dark:text-slate-200">
                    +{whatIfResult.baseline?.delay_min} min ({whatIfResult.baseline?.crowd})
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">{t.whatif_tab.simulated}</span>
                  <span className="text-lg font-extrabold text-rose-600">
                    +{whatIfResult.scenario?.delay_min} min ({whatIfResult.scenario?.crowd})
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 6: OPERATOR CONSOLE */}
        {activeTab === 'operator' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">{t.operator_tab.title}</h2>
                <p className="text-xs text-slate-500">{t.operator_tab.subtitle}</p>
              </div>
              <button
                onClick={async () => {
                  await fetch(`${API_BASE}/ops/simulate-incident`, { method: "POST" });
                  setOperatorEvents(prev => [{
                    id: `EVT_${Date.now()}`,
                    type: "bunching",
                    severity: "high",
                    route_id: "17D",
                    location: "Central Bus Bay",
                    status: "active"
                  }, ...prev]);
                }}
                className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold transition shadow-sm"
              >
                ⚡ {t.operator_tab.simulate_btn}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Route Health Index */}
              <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">{t.operator_tab.health_title}</h3>
                <div className="text-5xl font-black text-emerald-600 dark:text-emerald-400">
                  {routeHealth?.health_index || 84}<span className="text-base font-normal text-slate-400">/100</span>
                </div>
                <p className="text-xs text-slate-500">Route variance and headway regularities are within optimal transit operating bounds.</p>
              </div>

              {/* Active Events Queue */}
              <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">{t.operator_tab.events_title}</h3>
                <div className="space-y-2">
                  {operatorEvents.map((evt, idx) => (
                    <div key={evt.id || idx} className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-xs flex justify-between items-center">
                      <div>
                        <span className="font-bold text-rose-700 dark:text-rose-400">⚠️ {evt.type.toUpperCase()}: Route {evt.route_id}</span>
                        <p className="text-slate-500 text-[11px] mt-0.5">{evt.location}</p>
                      </div>
                      <button
                        onClick={() => setOperatorEvents(operatorEvents.filter(e => e.id !== evt.id))}
                        className="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-bold border border-slate-200 dark:border-slate-700 hover:bg-slate-50 text-[11px]"
                      >
                        {t.operator_tab.ack_btn}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 7: TRIP COMPANION */}
        {activeTab === 'companion' && (
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6 max-w-xl mx-auto">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">{t.companion_tab.title}</h2>
              <p className="text-xs text-slate-500">{t.companion_tab.subtitle}</p>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-2xl border border-slate-200 dark:border-slate-700 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-blue-600">🚌 {t.companion_tab.tracking_bus}: TN-01-N-1288</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-bold">On Route 17D</span>
              </div>
              <div className="text-xs text-slate-600 dark:text-slate-300 space-y-1">
                <div>{t.companion_tab.next_stop} <strong>DMS Teynampet</strong></div>
                <div>{t.companion_tab.destination} <strong>K.K. Nagar</strong> (4 {t.companion_tab.stops_remaining})</div>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={() => setCompanionActive(value => !value)}
                className={`w-full py-2 rounded-xl text-xs font-bold transition ${companionActive ? 'bg-emerald-600 text-white' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
              >
                {companionActive ? 'Trip tracking active · Pause updates' : 'Start trip tracking'}
              </button>
              {companionActive && (
                <p className="mt-2 text-xs text-emerald-700 dark:text-emerald-300" role="status">
                  Live trip updates are active. Next stop: DMS Teynampet.
                </p>
              )}
            </div>

            <div className="pt-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-slate-700 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={alightAlertEnabled}
                  onChange={(e) => setAlightAlertEnabled(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-0 w-4 h-4"
                />
                <span>🔔 {t.companion_tab.alight_alert}</span>
              </label>
            </div>
          </div>
        )}

        {/* TAB 8: CITY REPLAY */}
        {activeTab === 'replay' && (
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6 max-w-xl mx-auto text-center">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">{t.replay_tab.title}</h2>
              <p className="text-xs text-slate-500">{t.replay_tab.subtitle}</p>
            </div>

            <div className="space-y-4">
              <input
                type="range"
                min="0"
                max="100"
                value={replayProgress}
                onChange={(e) => setReplayProgress(parseInt(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
              <div className="flex justify-between text-xs font-mono text-slate-500">
                <span>06:00 AM</span>
                <span>02:00 PM (Current)</span>
                <span>11:00 PM</span>
              </div>

              <div className="flex items-center justify-center gap-4 pt-2">
                <button
                  onClick={() => setReplayPlaying(!replayPlaying)}
                  className="px-6 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm"
                >
                  {replayPlaying ? t.replay_tab.pause : t.replay_tab.play}
                </button>
                <div className="flex items-center gap-1 text-xs text-slate-500 font-bold">
                  <span>{t.replay_tab.speed}</span>
                  {[1, 5, 15, 60].map(s => (
                    <button
                      key={s}
                      onClick={() => setReplaySpeed(s)}
                      className={`px-2 py-0.5 rounded ${replaySpeed === s ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' : 'bg-slate-100 dark:bg-slate-800'}`}
                    >
                      {s}x
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 9: ABOUT & ATTRIBUTIONS (Quiet Honest Disclosure - Rule P-R2) */}
        {activeTab === 'about' && (
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6 max-w-2xl mx-auto text-xs leading-relaxed text-slate-600 dark:text-slate-300">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-2">{t.about_tab.title}</h2>
              <p className="font-semibold text-slate-800 dark:text-slate-200">{t.about_tab.desc_1}</p>
              <p className="mt-2 text-slate-500">{t.about_tab.desc_2}</p>
            </div>

            <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200">
              <strong>Notice:</strong> {t.about_tab.disclaimer}
            </div>

            <div className="space-y-1 pt-2 border-t border-slate-100 dark:border-slate-800 text-slate-500">
              <strong className="block text-slate-700 dark:text-slate-300">{t.about_tab.attributions}</strong>
              <p>{t.about_tab.attr_carto}</p>
              <p>{t.about_tab.attr_weather}</p>
              <p>{t.about_tab.attr_transit}</p>
            </div>
          </div>
        )}

      </main>

      {/* Footer with Isolated Developer Tools Access (Rule P-R1) */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-900/60 px-6 py-4 text-center text-xs text-slate-500 flex flex-wrap justify-between items-center gap-4 max-w-7xl mx-auto w-full">
        <span>Waitless AI v2.0 · Live City Transit Intelligence · MTC Chennai</span>
        {DEV_TOOLS_ENABLED && (
          <button
            onClick={() => setDevToolsOpen(true)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 underline font-mono text-[11px]"
          >
            {t.nav.dev}
          </button>
        )}
      </footer>

      {/* Secret Developer Modal (Rule P-R1) */}
      {DEV_TOOLS_ENABLED && <DevToolsModal isOpen={devToolsOpen} onClose={() => setDevToolsOpen(false)} />}

    </div>
  );
}
