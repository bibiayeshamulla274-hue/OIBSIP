# Atmosphere — Weather App (Advanced Tier)

**Oasis Infobyte Internship (OIBSIP) — Python Programming Task 4**

A full-featured **Weather App** built in **two independent versions** powered by the free **OpenWeatherMap API** and **ipinfo.io** geolocation:

1. **Python Desktop Version (`tkinter` + `Pillow` + `requests`)** — Threaded, non-blocking desktop GUI with clean API/UI separation.
2. **Standalone Web Version (`HTML5` + `CSS3` + `Vanilla JavaScript`)** — Opens directly by double-clicking `index.html` (`file://`), requiring zero server, npm, or build step.

---

## Features

### Core & Advanced Capabilities (Both Versions)
- **City & ZIP Code Search**: Search by city name (`Tokyo`, `London,GB`) or postal/ZIP code (`10001`, `10001,US`) with `Enter`-key support.
- **Current Weather Telemetry**: Displays temperature in both **°C and °F**, feels-like temperature, humidity %, wind speed (`m/s` & `km/h`) + direction, pressure, visibility, condition description, and official OpenWeatherMap weather icons (`@2x.png`).
- **Hourly Forecast (Next 6 Hours)**: Displays the next 6 hours using the 3-hour interval entries from `/forecast` (plus an optional **Next 18 Hours** view + SVG sparkline in the Web version).
- **5-Day Forecast**: Groups `/forecast` intervals by local calendar date and calculates daily min/max temperatures, precipitation chance, and representative icons.
- **Instant `°C / °F` Unit Toggle**: Re-renders every panel (current, feels-like, hourly, 5-day, comparison) immediately from cached data **without making a new API call**.
- **Auto-Detect My Location**: Uses `https://ipinfo.io/json` to detect your approximate city and load its live forecast automatically.
- **Comprehensive In-UI Error Handling**: Shows clear red on-screen error banners (never `alert()` or silent console logs) for:
  - Empty input
  - Missing or placeholder API key
  - City/ZIP not found (`404`)
  - Invalid/inactive API key (`401`)
  - Network failure or 10-second timeout (`timeout=10` / `AbortController`)

### Unique Interactive Features
- **Interactive Landing Page & Dynamic Sky Themes**: Background colors, gradients, and CSS atmospheric particles (raindrops / snowflakes) shift dynamically with live weather conditions — or can be previewed interactively on the landing page.
- **Smart Outfit & Activity Advisory**: Context-aware clothing, umbrella, SPF, and windproof layer tips generated from live temperature, humidity, wind, and weather conditions.
- **Interactive Solar Arc & Daylight Tracker** *(Web)*: Real-time SVG arc tracking sunrise, sunset, and daylight progress in the searched city's local timezone.
- **Wind Compass & Thermal Comfort Gauge** *(Web)*: Rotating SVG compass needle, Beaufort scale rating, and dew-point calculation.
- **Side-by-Side City Comparison Pinboard** *(Web)*: Pin up to 3 cities to compare temperature, humidity, and wind side by side.

---

## Tech Stack

| Version | Technologies |
| :--- | :--- |
| **Python Desktop** | Python 3.10+, `tkinter` / `ttk`, `requests`, `Pillow`, `python-dotenv`, `threading` |
| **Standalone Web** | HTML5, CSS3 (Custom Properties + Grid + Flexbox), Vanilla JavaScript (ES6+, `fetch`, `AbortController`) |
| **APIs** | OpenWeatherMap (`/data/2.5/weather`, `/data/2.5/forecast`, `/img/wn/@2x.png`), `ipinfo.io/json` |

---

## Getting a Free OpenWeatherMap API Key

1. Visit [https://openweathermap.org/](https://openweathermap.org/) and click **Sign In** → **Create an Account**.
2. Verify your email address after registering.
3. Navigate to your profile menu → **My API keys** (or `https://home.openweathermap.org/api_keys`).
4. Copy the default API key (or generate a new one).

> **Important Activation Note:** Newly created OpenWeatherMap API keys can take **up to a couple of hours (typically 10 minutes – 2 hours)** to activate on their servers. During that window, requests may temporarily return HTTP `401 Unauthorized`.

---

## Setup & Installation

### 1. Python Desktop Version (`.env`)

1. Open a terminal inside `OIBSIP/Python-Task4-WeatherApp/`.
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   *(On Windows Command Prompt: `copy .env.example .env`)*
3. Open `.env` and paste your OpenWeatherMap API key:
   ```env
   OPENWEATHER_API_KEY=your_actual_api_key_here
   ```
4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the desktop application:
   ```bash
   python weather_app.py
   ```

### 2. Standalone Web Version (`config.js`)

1. Navigate to `OIBSIP/Python-Task4-WeatherApp/`.
2. Copy `config.example.js` to `config.js` (if `config.js` doesn't already exist):
   ```bash
   cp config.example.js config.js
   ```
3. Open `config.js` in any text editor and paste your OpenWeatherMap API key:
   ```javascript
   const API_KEY = "your_actual_api_key_here";
   ```
4. **Double-click `index.html`** to open it directly in Chrome, Edge, Firefox, or Safari. No local server, `npm`, or build step is required.

> **Security Note:** Both `.env` and `config.js` are listed in `.gitignore` so your real API key is never committed to Git.

---

## Screenshots

*(Add screenshots of your local run here before submitting your internship repository)*

- **Web Landing Page & Interactive Sky Preview**: `screenshots/web-landing.png`
- **Web Live Weather Dashboard (Current + 6h/18h + 5-Day + Sun Arc & Compass)**: `screenshots/web-dashboard.png`
- **Python Tkinter Desktop GUI**: `screenshots/python-gui.png`

---

## Folder Structure

```text
OIBSIP/
└── Python-Task4-WeatherApp/
    ├── weather_app.py      # Python tkinter desktop GUI (threaded, Pillow icons)
    ├── config.py           # Python .env loader, API client, & data helpers
    ├── requirements.txt    # Python dependencies (requests, Pillow, python-dotenv)
    ├── index.html          # Standalone Web landing page & weather dashboard
    ├── style.css           # Dynamic weather themes, atmospheric particles & layout
    ├── script.js           # Vanilla JS fetch, 10s AbortController, unit toggle & SVGs
    ├── config.js           # Local Web API key (ignored by .gitignore)
    ├── config.example.js   # Committed template for config.js
    ├── .env.example        # Committed template for Python .env
    ├── .gitignore          # Ignores .env, config.js, and Python cache artifacts
    └── README.md           # Documentation, setup guide, and project structure
```
