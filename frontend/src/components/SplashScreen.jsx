import React, { useEffect, useState } from 'react';

export default function SplashScreen({ onFinish, lang = 'en', translations }) {
  const [progress, setProgress] = useState(15);
  const [statusText, setStatusText] = useState(translations.splash.status_preloading);
  const [busPosition, setBusPosition] = useState(10);

  useEffect(() => {
    // Preload API health check
    const checkApi = async () => {
      try {
        await fetch("http://127.0.0.1:8000/health", { signal: AbortSignal.timeout(2500) });
      } catch (e) {
        // Tolerant fallback if API is not yet running
      }
    };
    checkApi();

    // Sequence progress
    const t1 = setTimeout(() => {
      setProgress(55);
      setBusPosition(48);
      setStatusText(translations.splash.status_routes);
    }, 700);

    const t2 = setTimeout(() => {
      setProgress(100);
      setBusPosition(92);
      setStatusText(translations.splash.status_ready);
    }, 1400);

    const t3 = setTimeout(() => {
      onFinish();
    }, 2000);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, []);

  return (
    <div 
      onClick={onFinish}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center cursor-pointer select-none bg-gradient-to-br from-blue-50 via-amber-50/40 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-blue-950 p-6"
    >
      <div className="w-full max-w-md text-center space-y-6">
        {/* App Logo & Title */}
        <div className="space-y-2">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-tr from-blue-600 to-amber-500 shadow-xl shadow-blue-500/20 text-4xl transform hover:scale-105 transition-transform">
            🚌
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            {translations.title}
          </h1>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
            {translations.splash.tagline}
          </p>
        </div>

        {/* Animated Road with Driving Bus Emoji */}
        <div className="relative pt-6 pb-2">
          {/* Road Line */}
          <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full relative overflow-visible">
            {/* Bus Stops along the road */}
            <div className="absolute top-1/2 -translate-y-1/2 left-[15%] w-3 h-3 rounded-full bg-blue-400 border-2 border-white dark:border-slate-900 shadow"></div>
            <div className="absolute top-1/2 -translate-y-1/2 left-[50%] w-3 h-3 rounded-full bg-amber-400 border-2 border-white dark:border-slate-900 shadow"></div>
            <div className="absolute top-1/2 -translate-y-1/2 left-[85%] w-3 h-3 rounded-full bg-emerald-400 border-2 border-white dark:border-slate-900 shadow"></div>

            {/* Driving Bus */}
            <div 
              className="absolute -top-5 text-2xl transition-all duration-700 ease-out transform -translate-x-1/2"
              style={{ left: `${busPosition}%` }}
            >
              🚌
            </div>
          </div>
        </div>

        {/* Progress Bar & Status Text */}
        <div className="space-y-2">
          <div className="w-full bg-slate-200/80 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-600 to-amber-500 h-1.5 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 animate-pulse">
            {statusText}
          </p>
        </div>

        {/* Skip button */}
        <div>
          <button 
            onClick={(e) => { e.stopPropagation(); onFinish(); }}
            className="text-xs px-3 py-1.5 rounded-full bg-white/80 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 hover:text-slate-900 dark:hover:text-white transition shadow-sm"
          >
            {translations.splash.skip} &rarr;
          </button>
        </div>
      </div>
    </div>
  );
}

