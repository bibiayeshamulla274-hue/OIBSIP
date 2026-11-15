/**
 * Atmosphere Weather Studio — Vanilla JavaScript (works via file:// double-click)
 *
 * Expects config.js to be loaded beforehand defining:
 *   const API_KEY = "YOUR_OPENWEATHERMAP_KEY";
 */

(function () {
  "use strict";

  const OPENWEATHER_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather";
  const OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast";
  const OPENWEATHER_ICON_URL = (code) => `https://openweathermap.org/img/wn/${code}@2x.png`;
  const IPINFO_URL = "https://ipinfo.io/json";
  const TIMEOUT_MS = 10000;
  const PLACEHOLDER_KEY = "PASTE_YOUR_KEY_HERE";
  const RECENT_STORAGE_KEY = "atmosphere_recent_cities_v1";

  // Sample OpenWeatherMap-shaped dummy data for instant preview on open
  function buildSampleBundle(cfg) {
    const baseNow = Math.floor(Date.now() / 1000);
    const list = [];
    for (let i = 1; i <= 40; i += 1) {
      const dt = baseNow + i * 10800;
      const offsetWave = Math.sin(i * 0.8) * 2.5;
      const temp = Number((cfg.temp + offsetWave).toFixed(1));
      list.push({
        dt,
        main: {
          temp,
          feels_like: Number((temp - 0.8).toFixed(1)),
          temp_min: Number((temp - 2.4).toFixed(1)),
          temp_max: Number((temp + 2.1).toFixed(1)),
          humidity: cfg.humidity,
        },
        pop: cfg.pop,
        weather: [{ main: cfg.main, description: cfg.desc, icon: cfg.icon }],
      });
    }
    return {
      current: {
        name: cfg.name,
        sys: {
          country: cfg.country,
          sunrise: baseNow - 14400,
          sunset: baseNow + 21600,
        },
        coord: { lat: cfg.lat, lon: cfg.lon },
        timezone: cfg.tz,
        dt: baseNow,
        visibility: cfg.vis,
        clouds: { all: cfg.clouds },
        wind: { speed: cfg.wind, gust: cfg.gust, deg: cfg.deg },
        main: {
          temp: cfg.temp,
          feels_like: cfg.feels,
          temp_min: cfg.min,
          temp_max: cfg.max,
          humidity: cfg.humidity,
          pressure: cfg.pressure,
        },
        weather: [{ main: cfg.main, description: cfg.desc, icon: cfg.icon }],
      },
      forecast: {
        city: { name: cfg.name, country: cfg.country, timezone: cfg.tz },
        list,
      },
    };
  }

  const SAMPLE_BUNDLES = {
    Tokyo: buildSampleBundle({
      name: "Tokyo",
      country: "JP",
      lat: 35.68,
      lon: 139.69,
      tz: 32400,
      temp: 19.4,
      feels: 18.8,
      min: 12.6,
      max: 21.2,
      humidity: 54,
      pressure: 1018,
      vis: 16000,
      clouds: 18,
      wind: 4.2,
      gust: 6.8,
      deg: 135,
      pop: 0.1,
      main: "Clear",
      desc: "clear sky",
      icon: "01d",
    }),
    London: buildSampleBundle({
      name: "London",
      country: "GB",
      lat: 51.51,
      lon: -0.13,
      tz: 0,
      temp: 11.2,
      feels: 9.1,
      min: 7.4,
      max: 12.8,
      humidity: 84,
      pressure: 1004,
      vis: 9500,
      clouds: 88,
      wind: 6.7,
      gust: 11.2,
      deg: 245,
      pop: 0.75,
      main: "Rain",
      desc: "light rain",
      icon: "10d",
    }),
    Reykjavik: buildSampleBundle({
      name: "Reykjavik",
      country: "IS",
      lat: 64.15,
      lon: -21.94,
      tz: 0,
      temp: -1.6,
      feels: -6.4,
      min: -4.2,
      max: 0.8,
      humidity: 79,
      pressure: 996,
      vis: 7200,
      clouds: 74,
      wind: 8.9,
      gust: 14.1,
      deg: 35,
      pop: 0.7,
      main: "Snow",
      desc: "light snow",
      icon: "13d",
    }),
    Mumbai: buildSampleBundle({
      name: "Mumbai",
      country: "IN",
      lat: 19.08,
      lon: 72.88,
      tz: 19800,
      temp: 31.6,
      feels: 35.2,
      min: 25.4,
      max: 33.1,
      humidity: 76,
      pressure: 1011,
      vis: 11000,
      clouds: 34,
      wind: 3.8,
      gust: 5.9,
      deg: 290,
      pop: 0.8,
      main: "Thunderstorm",
      desc: "thunderstorm with rain",
      icon: "11d",
    }),
  };

  // Application State
  const state = {
    unit: "C", // "C" or "F"
    hourlyMode: 6, // 6 (next 2 entries = 6h) or 18 (next 6 entries = 18h)
    currentData: SAMPLE_BUNDLES.Tokyo.current,
    forecastData: SAMPLE_BUNDLES.Tokyo.forecast,
    pinnedCities: ["Tokyo", "London", "Reykjavik"].map((name) => {
      const c = SAMPLE_BUNDLES[name].current;
      const w = c.weather[0];
      return {
        key: `${c.name}-${c.sys.country}`,
        name: `${c.name}, ${c.sys.country}`,
        tempC: c.main.temp,
        feelsC: c.main.feels_like,
        humidity: c.main.humidity,
        windMs: c.wind.speed,
        description: w.description,
        icon: w.icon,
      };
    }),
    recentCities: loadRecentCities(),
  };

  // DOM References
  const els = {
    searchForm: document.getElementById("search-form"),
    cityInput: document.getElementById("city-input"),
    searchBtn: document.getElementById("search-btn"),
    locateBtn: document.getElementById("locate-btn"),
    quickCities: document.getElementById("quick-cities"),
    sampleCityControls: document.getElementById("sample-city-controls"),
    recentGroup: document.getElementById("recent-group"),
    recentCities: document.getElementById("recent-cities"),
    errorBox: document.getElementById("error-box"),
    errorMessage: document.getElementById("error-message"),
    errorClose: document.getElementById("error-close"),
    loadingBox: document.getElementById("loading-box"),
    loadingText: document.getElementById("loading-text"),
    landingShowcase: document.getElementById("landing-showcase"),
    dashboard: document.getElementById("weather-dashboard"),
    particles: document.getElementById("atmosphere-particles"),

    btnUnitC: document.getElementById("btn-unit-c"),
    btnUnitF: document.getElementById("btn-unit-f"),

    localTimeLabel: document.getElementById("local-time-label"),
    coordsLabel: document.getElementById("coords-label"),
    cityTitle: document.getElementById("city-title"),
    conditionDesc: document.getElementById("condition-desc"),
    primaryTemp: document.getElementById("primary-temp"),
    altTemp: document.getElementById("alt-temp"),
    feelsLike: document.getElementById("feels-like"),
    minmaxToday: document.getElementById("minmax-today"),
    pinCompareBtn: document.getElementById("pin-compare-btn"),
    currentIconWrap: document.getElementById("current-icon-wrap"),
    currentIcon: document.getElementById("current-icon"),

    metricHumidity: document.getElementById("metric-humidity"),
    metricDewpoint: document.getElementById("metric-dewpoint"),
    metricWind: document.getElementById("metric-wind"),
    metricWindSub: document.getElementById("metric-wind-sub"),
    metricPressure: document.getElementById("metric-pressure"),
    metricClouds: document.getElementById("metric-clouds"),
    metricVisibility: document.getElementById("metric-visibility"),
    metricComfort: document.getElementById("metric-comfort"),
    advisoryText: document.getElementById("advisory-text"),

    hourlyHeading: document.getElementById("hourly-heading"),
    hourlySub: document.getElementById("hourly-sub"),
    hourlyMode6: document.getElementById("hourly-mode-6"),
    hourlyMode18: document.getElementById("hourly-mode-18"),
    hourlySparklineWrap: document.getElementById("hourly-sparkline-wrap"),
    hourlyList: document.getElementById("hourly-list"),
    dailyList: document.getElementById("daily-list"),

    sunArcSvg: document.getElementById("sun-arc-svg"),
    daylightDuration: document.getElementById("daylight-duration"),
    sunriseTime: document.getElementById("sunrise-time"),
    sunsetTime: document.getElementById("sunset-time"),
    daylightPct: document.getElementById("daylight-pct"),

    windCompassSvg: document.getElementById("wind-compass-svg"),
    beaufortLabel: document.getElementById("beaufort-label"),
    compassDir: document.getElementById("compass-dir"),
    compassSpeed: document.getElementById("compass-speed"),
    compassGust: document.getElementById("compass-gust"),
    compassComfort: document.getElementById("compass-comfort"),

    compareEmpty: document.getElementById("compare-empty"),
    compareGrid: document.getElementById("compare-grid"),
    clearCompareBtn: document.getElementById("clear-compare-btn"),
  };

  // ------------------------------------------------------------------------
  // Initialization & Event Wiring
  // ------------------------------------------------------------------------

  function init() {
    renderRecentCities();
    renderAll();

    els.searchForm.addEventListener("submit", (event) => {
      event.preventDefault();
      handleSearch(els.cityInput.value);
    });

    els.locateBtn.addEventListener("click", handleUseMyLocation);
    els.errorClose.addEventListener("click", hideError);

    els.btnUnitC.addEventListener("click", () => setUnit("C"));
    els.btnUnitF.addEventListener("click", () => setUnit("F"));

    els.hourlyMode6.addEventListener("click", () => setHourlyMode(6));
    els.hourlyMode18.addEventListener("click", () => setHourlyMode(18));

    els.pinCompareBtn.addEventListener("click", handlePinCurrentCity);
    els.clearCompareBtn.addEventListener("click", () => {
      state.pinnedCities = [];
      renderComparisonBoard();
    });

    // Quick-pick destination buttons
    els.quickCities.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-city]");
      if (!btn) return;
      const city = btn.getAttribute("data-city");
      els.cityInput.value = city;
      handleSearch(city);
    });

    // Sample city preview buttons (no API call needed)
    if (els.sampleCityControls) {
      els.sampleCityControls.addEventListener("click", (event) => {
        const btn = event.target.closest("[data-sample]");
        if (!btn) return;
        const sampleKey = btn.getAttribute("data-sample");
        const bundle = SAMPLE_BUNDLES[sampleKey];
        if (!bundle) return;
        els.sampleCityControls.querySelectorAll("[data-sample]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        hideError();
        els.cityInput.value = sampleKey;
        state.currentData = bundle.current;
        state.forecastData = bundle.forecast;
        renderAll();
      });
    }

    // Recent searches
    els.recentCities.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-city]");
      if (!btn) return;
      const city = btn.getAttribute("data-city");
      els.cityInput.value = city;
      handleSearch(city);
    });

    // Interactive landing page theme preview buttons
    document.querySelectorAll(".mood-btn[data-theme]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".mood-btn[data-theme]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const themeClass = btn.getAttribute("data-theme") || "theme-default";
        applyBodyTheme(themeClass);
      });
    });
  }

  function getConfiguredApiKey() {
    if (typeof API_KEY === "undefined" || API_KEY === null) {
      return "";
    }
    return String(API_KEY).trim();
  }

  function hasValidApiKey() {
    const key = getConfiguredApiKey();
    return Boolean(key && key !== PLACEHOLDER_KEY);
  }

  // ------------------------------------------------------------------------
  // Fetch with 10s AbortController Timeout & Error Handling
  // ------------------------------------------------------------------------

  async function fetchWithTimeout(url, timeoutMs = TIMEOUT_MS) {
    const controller = new AbortController();
    const timerId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, { signal: controller.signal });
      return response;
    } catch (err) {
      if (err && err.name === "AbortError") {
        throw new Error("Request timed out after 10 seconds. Please check your internet connection.");
      }
      throw new Error("Network error: unable to connect. Please check your internet connection.");
    } finally {
      clearTimeout(timerId);
    }
  }

  function buildLocationQueryParams(rawQuery) {
    const trimmed = rawQuery.trim();
    // Match numeric ZIP / postal codes like 10001 or 10001,US
    if (/^\d{4,10}(,\s*[a-zA-Z]{2})?$/.test(trimmed)) {
      return `zip=${encodeURIComponent(trimmed.replace(/\s+/g, ""))}`;
    }
    return `q=${encodeURIComponent(trimmed)}`;
  }

  async function handleSearch(rawQuery) {
    const query = String(rawQuery || "").trim();

    if (!query) {
      showError("Please enter a city name or ZIP code before searching.");
      els.cityInput.focus();
      return;
    }

    if (!hasValidApiKey()) {
      showError(
        "OpenWeatherMap API key is missing or still set to PASTE_YOUR_KEY_HERE in config.js."
      );
      return;
    }

    hideError();
    setLoading(true, `Fetching live weather for "${query}"...`);

    const apiKey = getConfiguredApiKey();
    const locParam = buildLocationQueryParams(query);
    const currentUrl = `${OPENWEATHER_CURRENT_URL}?${locParam}&units=metric&appid=${encodeURIComponent(apiKey)}`;
    const forecastUrl = `${OPENWEATHER_FORECAST_URL}?${locParam}&units=metric&appid=${encodeURIComponent(apiKey)}`;

    try {
      const [currentResp, forecastResp] = await Promise.all([
        fetchWithTimeout(currentUrl),
        fetchWithTimeout(forecastUrl),
      ]);

      await validateOpenWeatherResponse(currentResp);
      await validateOpenWeatherResponse(forecastResp);

      const currentData = await currentResp.json();
      const forecastData = await forecastResp.json();

      state.currentData = currentData;
      state.forecastData = forecastData;

      const label = currentData.sys && currentData.sys.country
        ? `${currentData.name}, ${currentData.sys.country}`
        : currentData.name;
      saveRecentCity(label);
      renderAll();
    } catch (err) {
      showError(err.message || "An unexpected error occurred while fetching weather.");
    } finally {
      setLoading(false);
    }
  }

  async function validateOpenWeatherResponse(response) {
    if (response.ok) return;

    if (response.status === 404) {
      throw new Error("City or ZIP code not found (404). Please check the spelling and try again.");
    }
    if (response.status === 401) {
      throw new Error(
        "Invalid OpenWeatherMap API key (401). Note: new API keys can take up to 2 hours to activate."
      );
    }

    let detail = "";
    try {
      const body = await response.json();
      if (body && body.message) detail = `: ${body.message}`;
    } catch (_) {
      // ignore json parse issue on error body
    }
    throw new Error(`Weather API error (HTTP ${response.status})${detail}`);
  }

  async function handleUseMyLocation() {
    hideError();
    setLoading(true, "Detecting your approximate city via ipinfo.io...");

    try {
      const resp = await fetchWithTimeout(IPINFO_URL);
      if (!resp.ok) {
        throw new Error(`Location lookup failed (HTTP ${resp.status}). Please search manually.`);
      }
      const data = await resp.json();
      const city = (data.city || "").trim();
      const country = (data.country || "").trim();

      if (!city) {
        throw new Error("Could not determine your city from ipinfo.io. Please enter a city manually.");
      }

      const query = country ? `${city}, ${country}` : city;
      els.cityInput.value = query;
      await handleSearch(query);
    } catch (err) {
      setLoading(false);
      showError(err.message || "Unable to auto-detect location.");
    }
  }

  // ------------------------------------------------------------------------
  // Unit Toggle & Hourly Range (Zero-Refetch)
  // ------------------------------------------------------------------------

  function setUnit(newUnit) {
    if (state.unit === newUnit) return;
    state.unit = newUnit;

    els.btnUnitC.classList.toggle("active", newUnit === "C");
    els.btnUnitF.classList.toggle("active", newUnit === "F");
    els.btnUnitC.setAttribute("aria-pressed", String(newUnit === "C"));
    els.btnUnitF.setAttribute("aria-pressed", String(newUnit === "F"));

    if (state.currentData && state.forecastData) {
      renderAll();
    } else if (state.pinnedCities.length > 0) {
      renderComparisonBoard();
    }
  }

  function setHourlyMode(hours) {
    state.hourlyMode = hours;
    els.hourlyMode6.classList.toggle("active", hours === 6);
    els.hourlyMode18.classList.toggle("active", hours === 18);
    els.hourlyMode6.setAttribute("aria-pressed", String(hours === 6));
    els.hourlyMode18.setAttribute("aria-pressed", String(hours === 18));

    if (state.forecastData) {
      renderHourlyForecast();
    }
  }

  // ------------------------------------------------------------------------
  // Temperature, Time & Meteorological Helpers
  // ------------------------------------------------------------------------

  function cToF(c) {
    return (c * 9) / 5 + 32;
  }

  function formatTemp(tempC, unit = state.unit, decimals = 1) {
    const val = unit === "F" ? cToF(tempC) : tempC;
    return `${val.toFixed(decimals)}°${unit}`;
  }

  function formatLocalDateTime(unixSec, tzOffsetSec, options) {
    const date = new Date((unixSec + tzOffsetSec) * 1000);
    return new Intl.DateTimeFormat("en-US", { timeZone: "UTC", ...options }).format(date);
  }

  function getLocalDateKey(unixSec, tzOffsetSec) {
    const date = new Date((unixSec + tzOffsetSec) * 1000);
    const y = date.getUTCFullYear();
    const m = String(date.getUTCMonth() + 1).padStart(2, "0");
    const d = String(date.getUTCDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  function getCardinalDirection(deg) {
    if (typeof deg !== "number") return "—";
    const dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
    return dirs[Math.round(deg / 22.5) % 16];
  }

  function getBeaufortDescriptor(ms) {
    if (ms < 0.5) return "Calm (Force 0)";
    if (ms < 1.6) return "Light Air (Force 1)";
    if (ms < 3.4) return "Light Breeze (Force 2)";
    if (ms < 5.5) return "Gentle Breeze (Force 3)";
    if (ms < 8.0) return "Moderate Breeze (Force 4)";
    if (ms < 10.8) return "Fresh Breeze (Force 5)";
    if (ms < 13.9) return "Strong Breeze (Force 6)";
    if (ms < 17.2) return "Near Gale (Force 7)";
    return "Gale Force (Force 8+)";
  }

  function calculateDewPointC(tempC, humidity) {
    const a = 17.27;
    const b = 237.7;
    const alpha = (a * tempC) / (b + tempC) + Math.log(Math.max(humidity, 1) / 100);
    return (b * alpha) / (a - alpha);
  }

  function getComfortLabel(tempC, humidity) {
    if (tempC < 5) return "Brisk / Cold";
    if (tempC > 31 || (tempC >= 26 && humidity >= 75)) return "Warm & Muggy";
    if (humidity < 25) return "Crisp & Dry";
    if (tempC >= 16 && tempC <= 25 && humidity <= 68) return "Ideal Comfort";
    return "Moderate";
  }

  function getOutfitAdvisory(tempC, humidity, windMs, condMain) {
    const tips = [];
    const cond = (condMain || "").toLowerCase();

    if (tempC <= 5) {
      tips.push("Bundle up in a thermal coat, scarf, and gloves.");
    } else if (tempC <= 14) {
      tips.push("Layer up with a light jacket or sweater.");
    } else if (tempC <= 22) {
      tips.push("Pleasant temperatures — breathable long sleeves or light layers work well.");
    } else if (tempC <= 30) {
      tips.push("Warm outdoors — choose airy cotton or linen clothing.");
    } else {
      tips.push("High heat — wear light sun-protective fabrics and carry water.");
    }

    if (cond.includes("rain") || cond.includes("drizzle") || cond.includes("thunderstorm")) {
      tips.push("Pack a waterproof umbrella or rain shell.");
    } else if (cond.includes("snow")) {
      tips.push("Wear insulated waterproof footwear.");
    } else if (cond.includes("clear") && tempC >= 18) {
      tips.push("Sunglasses and SPF sunscreen are recommended.");
    }

    if (windMs >= 8) {
      tips.push("Expect brisk gusts — a windbreaker helps.");
    }
    if (humidity >= 80 && tempC >= 24) {
      tips.push("Elevated humidity will make outdoor exertion feel warmer.");
    }
    return tips.join(" ");
  }

  // ------------------------------------------------------------------------
  // Dynamic Atmospheric Theme & CSS Particles
  // ------------------------------------------------------------------------

  function resolveThemeFromWeather(condMain, iconCode) {
    const cond = (condMain || "").toLowerCase();
    const isNight = (iconCode || "").endsWith("n");

    if (cond.includes("thunderstorm")) return "theme-storm";
    if (cond.includes("rain") || cond.includes("drizzle")) return "theme-rain";
    if (cond.includes("snow")) return "theme-snow";
    if (cond.includes("cloud")) return "theme-clouds";
    if (cond.includes("clear")) return isNight ? "theme-storm" : "theme-clear";
    return "theme-default";
  }

  function applyBodyTheme(themeClass) {
    const allThemes = [
      "theme-default",
      "theme-clear",
      "theme-clouds",
      "theme-rain",
      "theme-storm",
      "theme-snow",
      "theme-sunset",
    ];
    document.body.classList.remove(...allThemes);
    document.body.classList.add(themeClass);
    renderWeatherParticles(themeClass);
  }

  function renderWeatherParticles(themeClass) {
    els.particles.innerHTML = "";
    if (themeClass !== "theme-rain" && themeClass !== "theme-storm" && themeClass !== "theme-snow") {
      return;
    }

    const isSnow = themeClass === "theme-snow";
    const count = isSnow ? 28 : 42;
    const frag = document.createDocumentFragment();

    for (let i = 0; i < count; i += 1) {
      const node = document.createElement("span");
      node.className = isSnow ? "snow-flake" : "rain-drop";
      node.style.left = `${(i * 100) / count + Math.random() * 2}%`;
      node.style.animationDuration = isSnow
        ? `${5 + Math.random() * 5}s`
        : `${0.75 + Math.random() * 0.65}s`;
      node.style.animationDelay = `${-Math.random() * 4}s`;
      frag.appendChild(node);
    }
    els.particles.appendChild(frag);
  }

  // ------------------------------------------------------------------------
  // Render Full Weather Dashboard
  // ------------------------------------------------------------------------

  function renderAll() {
    if (!state.currentData || !state.forecastData) return;

    els.dashboard.classList.remove("hidden");

    const current = state.currentData;
    const weather = (current.weather && current.weather[0]) || {};
    const themeClass = resolveThemeFromWeather(weather.main, weather.icon);
    applyBodyTheme(themeClass);

    renderCurrentWeather(current, weather);
    renderHourlyForecast();
    renderDailyForecast();
    renderSunArc(current);
    renderWindCompass(current);
    renderComparisonBoard();
  }

  function renderCurrentWeather(current, weather) {
    const tzOffset = current.timezone || 0;
    const cityLabel = current.sys && current.sys.country
      ? `${current.name}, ${current.sys.country}`
      : current.name;

    els.cityTitle.textContent = cityLabel;
    els.conditionDesc.textContent = weather.description || weather.main || "—";
    els.localTimeLabel.textContent = formatLocalDateTime(current.dt, tzOffset, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });

    if (current.coord) {
      els.coordsLabel.textContent = `${current.coord.lat.toFixed(2)}°, ${current.coord.lon.toFixed(2)}°`;
    }

    const tempC = current.main.temp;
    const feelsC = current.main.feels_like;
    const minC = current.main.temp_min;
    const maxC = current.main.temp_max;
    const altUnit = state.unit === "C" ? "F" : "C";

    els.primaryTemp.textContent = formatTemp(tempC, state.unit, 1);
    els.altTemp.textContent = `${formatTemp(tempC, altUnit, 1)}`;
    els.feelsLike.textContent = `Feels like ${formatTemp(feelsC, state.unit, 1)}`;
    els.minmaxToday.textContent = `Low ${formatTemp(minC, state.unit, 0)} · High ${formatTemp(maxC, state.unit, 0)}`;

    // Icon with fallback
    const iconCode = weather.icon || "01d";
    els.currentIcon.src = OPENWEATHER_ICON_URL(iconCode);
    els.currentIcon.alt = weather.description || "Weather condition icon";
    els.currentIcon.onerror = () => {
      els.currentIcon.style.display = "none";
    };
    els.currentIcon.onload = () => {
      els.currentIcon.style.display = "block";
    };

    // Metrics
    const humidity = current.main.humidity;
    const dewPointC = calculateDewPointC(tempC, humidity);
    const windMs = (current.wind && current.wind.speed) || 0;
    const windKmh = windMs * 3.6;
    const visibilityKm = (current.visibility || 0) / 1000;

    els.metricHumidity.textContent = `${humidity}%`;
    els.metricDewpoint.textContent = `Dew point ${formatTemp(dewPointC, state.unit, 1)}`;
    els.metricWind.textContent = `${windMs.toFixed(1)} m/s`;
    els.metricWindSub.textContent = `${windKmh.toFixed(0)} km/h · ${getCardinalDirection(current.wind && current.wind.deg)}`;
    els.metricPressure.textContent = `${current.main.pressure} hPa`;
    els.metricClouds.textContent = `Cloud cover ${(current.clouds && current.clouds.all) || 0}%`;
    els.metricVisibility.textContent = `${visibilityKm.toFixed(1)} km`;
    els.metricComfort.textContent = `Comfort: ${getComfortLabel(tempC, humidity)}`;

    els.advisoryText.textContent = getOutfitAdvisory(tempC, humidity, windMs, weather.main);
    updatePinButtonState();
  }

  function renderHourlyForecast() {
    const forecast = state.forecastData;
    const tzOffset = (forecast.city && forecast.city.timezone) || 0;
    const count = state.hourlyMode === 18 ? 6 : 2;
    const entries = (forecast.list || []).slice(0, count);

    els.hourlyHeading.textContent =
      state.hourlyMode === 18
        ? "Hourly Forecast — Next 18 Hours"
        : "Hourly Forecast — Next 6 Hours";
    els.hourlySub.textContent =
      state.hourlyMode === 18
        ? "Next 6 intervals (3-hour steps)"
        : "First 2 intervals (3-hour steps covering 6 hours)";

    renderHourlySparkline(entries);

    els.hourlyList.innerHTML = "";
    entries.forEach((item) => {
      const w = (item.weather && item.weather[0]) || {};
      const timeStr = formatLocalDateTime(item.dt, tzOffset, {
        hour: "numeric",
        minute: "2-digit",
      });
      const popPct = Math.round((item.pop || 0) * 100);

      const row = document.createElement("div");
      row.className = "hourly-row";
      row.innerHTML = `
        <div class="hourly-left">
          <img src="${OPENWEATHER_ICON_URL(w.icon || "01d")}" alt="${escapeHtml(w.description || "")}" referrerpolicy="no-referrer" />
          <div>
            <div class="hourly-time tabular-nums">${escapeHtml(timeStr)}</div>
            <div class="hourly-desc">${escapeHtml(w.description || "")}</div>
          </div>
        </div>
        <div class="hourly-right">
          <div class="hourly-temp tabular-nums">${formatTemp(item.main.temp, state.unit, 1)}</div>
          <div class="hourly-pop tabular-nums">Precip ${popPct}% · Feels ${formatTemp(item.main.feels_like, state.unit, 0)}</div>
        </div>
      `;
      els.hourlyList.appendChild(row);
    });
  }

  function renderHourlySparkline(entries) {
    if (!entries || entries.length < 2) {
      els.hourlySparklineWrap.innerHTML = "";
      return;
    }

    const temps = entries.map((e) => (state.unit === "F" ? cToF(e.main.temp) : e.main.temp));
    const minT = Math.min(...temps);
    const maxT = Math.max(...temps);
    const span = Math.max(maxT - minT, 1);

    const width = 360;
    const height = 56;
    const padX = 18;
    const padY = 12;

    const points = temps.map((t, idx) => {
      const x = padX + (idx * (width - padX * 2)) / (temps.length - 1);
      const y = height - padY - ((t - minT) / span) * (height - padY * 2);
      return { x, y, t };
    });

    const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
    const dots = points
      .map(
        (p) =>
          `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.5" fill="#0284c7" stroke="#ffffff" stroke-width="1.5" />`
      )
      .join("");

    els.hourlySparklineWrap.innerHTML = `
      <svg viewBox="0 0 ${width} ${height}" style="width:100%;height:56px;display:block;" aria-hidden="true">
        <path d="${pathD}" fill="none" stroke="#0284c7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
        ${dots}
      </svg>
    `;
  }

  function renderDailyForecast() {
    const forecast = state.forecastData;
    const tzOffset = (forecast.city && forecast.city.timezone) || 0;
    const todayKey = getLocalDateKey(Math.floor(Date.now() / 1000), tzOffset);

    const grouped = new Map();
    (forecast.list || []).forEach((item) => {
      const key = getLocalDateKey(item.dt, tzOffset);
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key).push(item);
    });

    const days = Array.from(grouped.entries()).slice(0, 5);
    els.dailyList.innerHTML = "";

    days.forEach(([dateKey, items]) => {
      const minC = Math.min(...items.map((x) => x.main.temp_min));
      const maxC = Math.max(...items.map((x) => x.main.temp_max));
      const maxPop = Math.round(Math.max(...items.map((x) => x.pop || 0)) * 100);

      // Pick entry closest to local noon for representative icon/condition
      let repItem = items[0];
      let bestDist = Infinity;
      items.forEach((x) => {
        const localHour = new Date((x.dt + tzOffset) * 1000).getUTCHours();
        const dist = Math.abs(localHour - 12);
        if (dist < bestDist) {
          bestDist = dist;
          repItem = x;
        }
      });

      const w = (repItem.weather && repItem.weather[0]) || {};
      const iconCode = (w.icon || "01d").replace("n", "d");
      const dayName = dateKey === todayKey
        ? "Today"
        : formatLocalDateTime(repItem.dt, tzOffset, { weekday: "short" });
      const dateStr = formatLocalDateTime(repItem.dt, tzOffset, {
        month: "short",
        day: "numeric",
      });

      const card = document.createElement("div");
      card.className = "daily-card";
      card.innerHTML = `
        <div class="daily-day">${escapeHtml(dayName)}</div>
        <div class="daily-date">${escapeHtml(dateStr)}</div>
        <img src="${OPENWEATHER_ICON_URL(iconCode)}" alt="${escapeHtml(w.description || "")}" referrerpolicy="no-referrer" />
        <div class="daily-temps tabular-nums">
          ${formatTemp(maxC, state.unit, 0)} <span class="daily-low">/ ${formatTemp(minC, state.unit, 0)}</span>
        </div>
        <div class="daily-desc">${escapeHtml(w.description || "")}</div>
        <div class="daily-pop tabular-nums">Precip ${maxPop}%</div>
      `;
      els.dailyList.appendChild(card);
    });
  }

  // ------------------------------------------------------------------------
  // Unique Feature: Interactive Sun Arc & Wind Compass SVGs
  // ------------------------------------------------------------------------

  function renderSunArc(current) {
    const sys = current.sys || {};
    const tzOffset = current.timezone || 0;
    const sunrise = sys.sunrise;
    const sunset = sys.sunset;

    if (!sunrise || !sunset || sunset <= sunrise) {
      els.sunriseTime.textContent = "—";
      els.sunsetTime.textContent = "—";
      els.daylightPct.textContent = "—";
      els.daylightDuration.textContent = "Solar telemetry unavailable";
      return;
    }

    const totalSec = sunset - sunrise;
    const hours = Math.floor(totalSec / 3600);
    const mins = Math.round((totalSec % 3600) / 60);
    const nowSec = current.dt;
    const rawProgress = (nowSec - sunrise) / totalSec;
    const clamped = Math.max(0, Math.min(1, rawProgress));
    const pct = Math.round(clamped * 100);

    els.sunriseTime.textContent = formatLocalDateTime(sunrise, tzOffset, {
      hour: "numeric",
      minute: "2-digit",
    });
    els.sunsetTime.textContent = formatLocalDateTime(sunset, tzOffset, {
      hour: "numeric",
      minute: "2-digit",
    });
    els.daylightPct.textContent = nowSec < sunrise ? "Pre-dawn (0%)" : nowSec > sunset ? "After sunset (100%)" : `${pct}%`;
    els.daylightDuration.textContent = `Daylight span: ${hours}h ${mins}m`;

    // Semi-circular arc centered at (160, 128) with radius 110
    const cx = 160;
    const cy = 128;
    const r = 110;
    const angle = Math.PI * (1 - clamped); // PI (left sunrise) -> 0 (right sunset)
    const sunX = cx + r * Math.cos(angle);
    const sunY = cy - r * Math.sin(angle);
    const isDaytime = nowSec >= sunrise && nowSec <= sunset;

    els.sunArcSvg.innerHTML = `
      <line x1="22" y1="${cy}" x2="298" y2="${cy}" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="4 4" />
      <path d="M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}" fill="none" stroke="#e2e8f0" stroke-width="6" stroke-linecap="round" />
      ${
        clamped > 0
          ? `<path d="M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${sunX.toFixed(1)} ${sunY.toFixed(1)}" fill="none" stroke="#f59e0b" stroke-width="6" stroke-linecap="round" />`
          : ""
      }
      <circle cx="${sunX.toFixed(1)}" cy="${sunY.toFixed(1)}" r="9" fill="${isDaytime ? "#f59e0b" : "#64748b"}" stroke="#ffffff" stroke-width="3" />
    `;
  }

  function renderWindCompass(current) {
    const wind = current.wind || {};
    const speedMs = wind.speed || 0;
    const gustMs = wind.gust;
    const deg = typeof wind.deg === "number" ? wind.deg : 0;
    const dir = getCardinalDirection(wind.deg);

    els.beaufortLabel.textContent = getBeaufortDescriptor(speedMs);
    els.compassDir.textContent = typeof wind.deg === "number" ? `${dir} (${deg}°)` : "Variable";
    els.compassSpeed.textContent = `${speedMs.toFixed(1)} m/s (${(speedMs * 3.6).toFixed(0)} km/h)`;
    els.compassGust.textContent = typeof gustMs === "number" ? `${gustMs.toFixed(1)} m/s` : "Calm";
    els.compassComfort.textContent = getComfortLabel(current.main.temp, current.main.humidity);

    els.windCompassSvg.innerHTML = `
      <circle cx="90" cy="90" r="76" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2" />
      <circle cx="90" cy="90" r="56" fill="none" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 3" />
      <text x="90" y="26" text-anchor="middle" font-size="12" font-weight="700" fill="#0f172a">N</text>
      <text x="156" y="94" text-anchor="middle" font-size="12" font-weight="700" fill="#64748b">E</text>
      <text x="90" y="162" text-anchor="middle" font-size="12" font-weight="700" fill="#64748b">S</text>
      <text x="24" y="94" text-anchor="middle" font-size="12" font-weight="700" fill="#64748b">W</text>
      <g transform="rotate(${deg} 90 90)">
        <polygon points="90,34 83,90 97,90" fill="#0284c7" />
        <polygon points="90,146 84,90 96,90" fill="#94a3b8" />
        <circle cx="90" cy="90" r="6" fill="#0f172a" />
      </g>
    `;
  }

  // ------------------------------------------------------------------------
  // Unique Feature: Pinned City Side-by-Side Comparison
  // ------------------------------------------------------------------------

  function handlePinCurrentCity() {
    if (!state.currentData) return;
    const c = state.currentData;
    const key = `${c.name}-${(c.sys && c.sys.country) || ""}`;
    const existingIdx = state.pinnedCities.findIndex((item) => item.key === key);

    if (existingIdx >= 0) {
      state.pinnedCities.splice(existingIdx, 1);
    } else {
      if (state.pinnedCities.length >= 3) {
        state.pinnedCities.shift();
      }
      const w = (c.weather && c.weather[0]) || {};
      state.pinnedCities.push({
        key,
        name: c.sys && c.sys.country ? `${c.name}, ${c.sys.country}` : c.name,
        tempC: c.main.temp,
        feelsC: c.main.feels_like,
        humidity: c.main.humidity,
        windMs: (c.wind && c.wind.speed) || 0,
        description: w.description || w.main || "—",
        icon: w.icon || "01d",
      });
    }

    updatePinButtonState();
    renderComparisonBoard();
  }

  function updatePinButtonState() {
    if (!state.currentData) return;
    const c = state.currentData;
    const key = `${c.name}-${(c.sys && c.sys.country) || ""}`;
    const isPinned = state.pinnedCities.some((item) => item.key === key);
    els.pinCompareBtn.textContent = isPinned ? "Pinned (Remove)" : "Pin to Compare";
  }

  function renderComparisonBoard() {
    if (state.pinnedCities.length === 0) {
      els.compareEmpty.classList.remove("hidden");
      els.compareGrid.classList.add("hidden");
      els.clearCompareBtn.classList.add("hidden");
      els.compareGrid.innerHTML = "";
      return;
    }

    els.compareEmpty.classList.add("hidden");
    els.compareGrid.classList.remove("hidden");
    els.clearCompareBtn.classList.remove("hidden");
    els.compareGrid.innerHTML = "";

    state.pinnedCities.forEach((city) => {
      const card = document.createElement("div");
      card.className = "compare-card";
      card.innerHTML = `
        <div class="compare-top">
          <div class="compare-city">${escapeHtml(city.name)}</div>
          <button type="button" class="compare-remove" data-remove="${escapeHtml(city.key)}">Remove</button>
        </div>
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <div class="compare-temp tabular-nums">${formatTemp(city.tempC, state.unit, 1)}</div>
          <img src="${OPENWEATHER_ICON_URL(city.icon)}" alt="" width="48" height="48" referrerpolicy="no-referrer" />
        </div>
        <div class="compare-meta" style="text-transform:capitalize;">${escapeHtml(city.description)}</div>
        <div class="compare-meta tabular-nums">
          Feels ${formatTemp(city.feelsC, state.unit, 0)} · Humidity ${city.humidity}% · Wind ${city.windMs.toFixed(1)} m/s
        </div>
      `;
      card.querySelector("[data-remove]").addEventListener("click", () => {
        state.pinnedCities = state.pinnedCities.filter((x) => x.key !== city.key);
        updatePinButtonState();
        renderComparisonBoard();
      });
      els.compareGrid.appendChild(card);
    });
  }

  // ------------------------------------------------------------------------
  // Recent Searches (localStorage safe under file://)
  // ------------------------------------------------------------------------

  function loadRecentCities() {
    try {
      const raw = localStorage.getItem(RECENT_STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed.slice(0, 5) : [];
    } catch (_) {
      return [];
    }
  }

  function saveRecentCity(cityLabel) {
    const filtered = state.recentCities.filter(
      (item) => item.toLowerCase() !== cityLabel.toLowerCase()
    );
    state.recentCities = [cityLabel, ...filtered].slice(0, 5);
    try {
      localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(state.recentCities));
    } catch (_) {
      // Ignore storage restrictions if blocked
    }
    renderRecentCities();
  }

  function renderRecentCities() {
    if (state.recentCities.length === 0) {
      els.recentGroup.classList.add("hidden");
      return;
    }
    els.recentGroup.classList.remove("hidden");
    els.recentCities.innerHTML = "";
    state.recentCities.forEach((city) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quick-btn";
      btn.setAttribute("data-city", city);
      btn.textContent = city;
      els.recentCities.appendChild(btn);
    });
  }

  // ------------------------------------------------------------------------
  // UI Feedback Helpers
  // ------------------------------------------------------------------------

  function showError(message) {
    els.errorMessage.textContent = message;
    els.errorBox.classList.remove("hidden");
  }

  function hideError() {
    els.errorBox.classList.add("hidden");
    els.errorMessage.textContent = "";
  }

  function setLoading(isLoading, text = "Fetching weather...") {
    els.searchBtn.disabled = isLoading;
    els.locateBtn.disabled = isLoading;
    if (isLoading) {
      els.loadingText.textContent = text;
      els.loadingBox.classList.remove("hidden");
    } else {
      els.loadingBox.classList.add("hidden");
    }
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  document.addEventListener("DOMContentLoaded", init);
})();
