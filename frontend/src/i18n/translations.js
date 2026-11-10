export const translations = {
  en: {
    title: "Waitless AI",
    tagline: "Know your bus before it arrives.",
    splash: {
      tagline: "Chennai Bus Reliability & Crowd Intelligence",
      status_preloading: "Connecting to Chennai transit network...",
      status_routes: "Loading active bus routes and landmarks...",
      status_ready: "Transit network ready. Starting...",
      skip: "Skip Introduction"
    },
    nav: {
      plan: "Journey Planner",
      live: "Live Map",
      predict: "Predict",
      bestbus: "Best Bus",
      whatif: "What-If Lab",
      operator: "Operator Console",
      companion: "Trip Companion",
      replay: "City Replay",
      about: "About",
      dev: "Dev Tools"
    },
    plan_tab: {
      title: "Plan Your Transit Journey",
      subtitle: "Discover direct and seamless transfer routes across Chennai",
      from_label: "Starting From",
      to_label: "Destination",
      from_placeholder: "e.g. Chennai Central, Egmore, CMBT...",
      to_placeholder: "e.g. Airport, T. Nagar, Tambaram...",
      find_routes_btn: "Find Bus Routes",
      quick_landmarks: "Popular Landmarks:",
      direct_tag: "Direct Route",
      transfer_tag: "1 Transfer",
      walk: "Walk",
      stops: "stops",
      select_to_predict: "Select to Inspect & Predict"
    },
    predict_tab: {
      title: "Predict Arrival Delay & Crowding",
      subtitle: "Results are generated only when you press the button below",
      route_label: "Route",
      stop_label: "Boarding Stop",
      rain_toggle: "Rain Along Route",
      predict_btn: "Predict Arrival & Crowding",
      loading_step_1: "Reading live bus positions & telemetry...",
      loading_step_2: "Estimating delay cascade & traffic friction...",
      loading_step_3: "Evaluating passenger crowding and seat outlook...",
      outdated_banner: "Inputs changed! Results outdated — press Predict again to refresh.",
      predicted_delay: "Predicted Delay",
      ontime_prob: "P(On-Time ≤ 5m)",
      interval_80: "80% Conformal Interval",
      crowding_level: "Crowding Level",
      seat_outlook: "Seat Availability Outlook",
      voice_readout: "Read Out Aloud",
      freshness: "Data Freshness",
      stamp_valid: "Predicted at",
      stamp_duration: "valid for ~5 min"
    },
    crowding_scales: {
      low: "Low (0–20 passengers, seats free)",
      medium: "Medium (21–40 passengers, some standing)",
      high: "High (41+ passengers, crowded)"
    },
    bestbus_tab: {
      title: "Best Bus Recommender",
      subtitle: "Compare approaching buses and choose your preferred travel style",
      slider_label: "Commute Preference:",
      speed_side: "⚡ Fastest Arrival",
      comfort_side: "🪑 Maximum Comfort",
      find_btn: "Find Best Bus to Board",
      eta_countdown: "ETA in",
      score_pts: "pts"
    },
    whatif_tab: {
      title: "What-If Disruption Simulator",
      subtitle: "Simulate traffic congestion and extreme weather variations",
      hour_label: "Time of Day (Hour):",
      rain_label: "Simulate Monsoon Rain Intensity:",
      peak_label: "Peak Rush Hour (8-10 AM / 5-8 PM)",
      upstream_label: "Upstream Injected Delay:",
      run_btn: "Run Scenario Simulation",
      baseline: "Standard Baseline",
      simulated: "Simulated Outcome",
      delta: "Delay Added:"
    },
    operator_tab: {
      title: "Transit Operator Console",
      subtitle: "Fleet-wide reliability index, bunching alarms, and headway health",
      health_title: "Route Reliability Health Index",
      events_title: "Active Headway & Bunching Alerts",
      ack_btn: "Acknowledge",
      snooze_btn: "Snooze 15m",
      simulate_btn: "Simulate Incident (Demo)"
    },
    companion_tab: {
      title: "Live Trip Companion",
      subtitle: "Keep this screen open while riding your bus",
      tracking_bus: "Tracking Bus",
      next_stop: "Next Stop:",
      destination: "Your Alighting Stop:",
      alight_alert: "Alight Alert (Notify 2 stops before)",
      stops_remaining: "stops remaining"
    },
    replay_tab: {
      title: "Citywide Time Replay",
      subtitle: "Replay 24 hours of bus transit dynamics across Chennai",
      play: "Play",
      pause: "Pause",
      speed: "Playback Speed:"
    },
    about_tab: {
      title: "About Waitless AI",
      how_it_works: "How it Works",
      desc_1: "Waitless AI provides decision-support arrival estimates, uncertainty intervals, and crowding classifications for Chennai MTC commuters.",
      desc_2: "All predictions are estimates calculated from transit modeling pipelines. Coverage varies by route.",
      disclaimer: "Decision support aid only; does not constitute an operational dispatch guarantee.",
      attributions: "Attributions & Licences:",
      attr_carto: "• Basemap tiles © CARTO, © OpenStreetMap contributors (ODbL).",
      attr_weather: "• Live weather data by Open-Meteo.",
      attr_transit: "• Route network parameters based on MTC Chennai transit feeds."
    }
  },
  ta: {
    title: "வெயிட்லெஸ் AI",
    tagline: "பேருந்து வரும் முன்பே அறிந்திடுங்கள்.",
    splash: {
      tagline: "சென்னை பேருந்து நேரலை மற்றும் கூட்ட நெரிசல் கணிப்பு",
      status_preloading: "சென்னை பேருந்து நெட்வொர்க்குடன் இணைகிறது...",
      status_routes: "பேருந்து தடங்கள் மற்றும் நிறுத்தங்கள் தயாராகின்றன...",
      status_ready: "அனைத்தும் தயார். தொடங்குகிறது...",
      skip: "தவிர்க்கவும்"
    },
    nav: {
      plan: "பயணத் திட்டம்",
      live: "நேரலை வரைபடம்",
      predict: "கணிப்பு",
      bestbus: "சிறந்த பேருந்து",
      whatif: "நிலைமை மாற்றம்",
      operator: "இயக்க மையம்",
      companion: "பயணத் துணை",
      replay: "மறுஒளிபரப்பு",
      about: "விளக்கம்",
      dev: "டெவ் டூல்ஸ்"
    },
    plan_tab: {
      title: "உங்கள் பேருந்து பயணத்தை திட்டமிடுங்கள்",
      subtitle: "சென்னையின் முக்கிய வழித்தடங்களில் நேரடி மற்றும் மாற்றுப் பேருந்துகள்",
      from_label: "புறப்படும் இடம்",
      to_label: "சேருமிடம்",
      from_placeholder: "எ.கா: சென்னை சென்ட்ரல், எழும்பூர், கோயம்பேடு...",
      to_placeholder: "எ.கா: விமான நிலையம், தி நகர், தாம்பரம்...",
      find_routes_btn: "பேருந்து தடங்களை காண்க",
      quick_landmarks: "முக்கிய இடங்கள்:",
      direct_tag: "நேரடி தடம்",
      transfer_tag: "1 மாற்று தடம்",
      walk: "நடை",
      stops: "நிறுத்தங்கள்",
      select_to_predict: "கணிக்க தேர்வு செய்யவும்"
    },
    predict_tab: {
      title: "தாமதம் மற்றும் கூட்ட கணிப்பு",
      subtitle: "கீழே உள்ள பட்டனை அழுத்தினால் மட்டுமே கணிப்பு காட்டப்படும்",
      route_label: "தடம்",
      stop_label: "ஏறும் நிறுத்தம்",
      rain_toggle: "மழை தாக்கம்",
      predict_btn: "தாமதம் & கூட்டத்தை கணிக்கவும்",
      loading_step_1: "பேருந்தின் நேரலை இருப்பிடங்கள் பெறப்படுகின்றன...",
      loading_step_2: "போக்குவரத்து நெரிசல் மற்றும் தாமதம் கணக்கிடப்படுகிறது...",
      loading_step_3: "கூட்ட நெரிசல் மற்றும் இருக்கை வசதி சரிபார்க்கப்படுகிறது...",
      outdated_banner: "விவரங்கள் மாற்றப்பட்டுள்ளன! மீண்டும் கணிக்க பட்டனை அழுத்தவும்.",
      predicted_delay: "கணிக்கப்பட்ட தாமதம்",
      ontime_prob: "சரியான நேர நிகழ்தகவு (≤ 5 நிமி)",
      interval_80: "80% உறுதி இடைவெளி",
      crowding_level: "கூட்ட நெரிசல் அளவு",
      seat_outlook: "இருக்கை கிடைக்கும் வாய்ப்பு",
      voice_readout: "குரலில் கேட்கவும்",
      freshness: "நேரலை புத்துணர்வு",
      stamp_valid: "கணிக்கப்பட்ட நேரம்",
      stamp_duration: "~5 நிமிடங்களுக்கு செல்லுபடியாகும்"
    },
    crowding_scales: {
      low: "குறைவு (0–20 பயணிகள், இருக்கைகள் உள்ளன)",
      medium: "நடுத்தரம் (21–40 பயணிகள், நின்றபடி)",
      high: "அதிகம் (41+ பயணிகள், நெரிசல்)"
    },
    bestbus_tab: {
      title: "சிறந்த பேருந்து தேர்வு",
      subtitle: "அடுத்தடுத்து வரும் பேருந்துகளில் உங்களுக்கு ஏற்றதை தேர்வு செய்யுங்கள்",
      slider_label: "பயண விருப்பம்:",
      speed_side: "⚡ விரைவான வருகை",
      comfort_side: "🪑 அதிக வசதி",
      find_btn: "சிறந்த பேருந்தை கண்டறியவும்",
      eta_countdown: "வருகை",
      score_pts: "புள்ளிகள்"
    },
    whatif_tab: {
      title: "நிலைமை மாற்ற பரிசோதனை",
      subtitle: "கனமழை அல்லது பீக் நேர மாற்றங்களை பரிசோதித்து பாருங்கள்",
      hour_label: "பயண நேரம் (மணி):",
      rain_label: "மழை அளவு:",
      peak_label: "பீக் நேரம் (8-10 காலை / 5-8 மாலை)",
      upstream_label: "முந்தைய தாமதம்:",
      run_btn: "பரிசோதனையை இயக்கவும்",
      baseline: "வழக்கமான நிலை",
      simulated: "மாற்றப்பட்ட நிலை",
      delta: "கூடுதல் தாமதம்:"
    },
    operator_tab: {
      title: "பேருந்து இயக்க மையம்",
      subtitle: "தடங்களின் நம்பகத்தன்மை குறியீடு மற்றும் நெரிசல் எச்சரிக்கைகள்",
      health_title: "தட நம்பகத்தன்மை குறியீடு",
      events_title: "அடுத்தடுத்து வரும் பேருந்து எச்சரிக்கைகள்",
      ack_btn: "ஏற்றுக்கொள்",
      snooze_btn: "15 நிமிடம் ஒத்திவை",
      simulate_btn: "மாதிரி எச்சரிக்கை"
    },
    companion_tab: {
      title: "நேரலை பயணத் துணை",
      subtitle: "பேருந்தில் பயணிக்கும்போது இந்த திரையை திறந்து வைக்கவும்",
      tracking_bus: "கண்காணிக்கப்படும் பேருந்து",
      next_stop: "அடுத்த நிறுத்தம்:",
      destination: "உங்கள் இலக்கு நிறுத்தம்:",
      alight_alert: "இறங்கும் முன் நினைவூட்டு (2 நிறுத்தம் முன்)",
      stops_remaining: "நிறுத்தங்கள் உள்ளன"
    },
    replay_tab: {
      title: "நகர பேருந்து மறுஒளிபரப்பு",
      subtitle: "சென்னையின் 24 மணி நேர பேருந்து இயக்கத்தை மீண்டும் காண்க",
      play: "இயக்கு",
      pause: "நிறுத்து",
      speed: "வேகம்:"
    },
    about_tab: {
      title: "வெயிட்லெஸ் AI பற்றி",
      how_it_works: "எவ்வாறு செயல்படுகிறது",
      desc_1: "வெயிட்லெஸ் AI சென்னை பயணிகளுக்கு பேருந்து தாமதம் மற்றும் கூட்ட நெரிசலை முன்கூட்டியே திட்டமிட உதவுகிறது.",
      desc_2: "அனைத்து கணிப்புகளும் போக்குவரத்து மாதிரி அமைப்புகளால் கணிக்கப்படும் மதிப்பீடுகள் மட்டுமே.",
      disclaimer: "இது பயணிகளுக்கு உதவும் ஒரு வழிகாட்டி அமைப்பு மட்டுமே.",
      attributions: "உரிமங்கள் மற்றும் நன்றிகள்:",
      attr_carto: "• வரைபடம் © CARTO, © OpenStreetMap contributors.",
      attr_weather: "• நேரலை வானிலை: Open-Meteo.",
      attr_transit: "• சென்னை மாநகரப் போக்குவரத்துக் கழக நெட்வொர்க்."
    }
  }
};
