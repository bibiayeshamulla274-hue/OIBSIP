"""
Configuration & API Service Layer for Weather App (Python Version).

Handles environment variable / .env loading, OpenWeatherMap API calls,
ipinfo.io geolocation, icon fetching, and forecast data normalization.
Completely decoupled from tkinter GUI logic.
"""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # Fallback if python-dotenv is not yet installed
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

OPENWEATHER_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
OPENWEATHER_ICON_URL = "https://openweathermap.org/img/wn/{icon}@2x.png"
IPINFO_URL = "https://ipinfo.io/json"

REQUEST_TIMEOUT = 10  # seconds
PLACEHOLDER_KEY = "PASTE_YOUR_KEY_HERE"


class WeatherAPIError(Exception):
    """Domain-specific exception raised for all Weather API / input errors."""

    def __init__(self, message: str, error_type: str = "unknown") -> None:
        super().__init__(message)
        self.message = message
        self.error_type = error_type


def _load_env_fallback(env_file: Path) -> None:
    """Lightweight .env reader if python-dotenv is unavailable."""
    if not env_file.is_file():
        return
    try:
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


def get_api_key() -> str:
    """Read OPENWEATHER_API_KEY from environment or local .env file."""
    if load_dotenv is not None and ENV_PATH.is_file():
        load_dotenv(dotenv_path=ENV_PATH, override=False)
    else:
        _load_env_fallback(ENV_PATH)

    return os.environ.get("OPENWEATHER_API_KEY", "").strip()


def validate_api_key(api_key: str) -> None:
    """Raise WeatherAPIError if the API key is missing or still a placeholder."""
    if not api_key or api_key == PLACEHOLDER_KEY:
        raise WeatherAPIError(
            "OpenWeatherMap API key is missing. Copy .env.example to .env and "
            "set OPENWEATHER_API_KEY=your_actual_key.",
            error_type="missing_key",
        )


def c_to_f(temp_c: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (temp_c * 9.0 / 5.0) + 32.0


def format_temp(temp_c: float, unit: str = "C", precision: int = 1) -> str:
    """Format a Celsius value into °C or °F."""
    if unit.upper() == "F":
        val = c_to_f(temp_c)
        return f"{val:.{precision}f}°F"
    return f"{temp_c:.{precision}f}°C"


def get_wind_direction(deg: float | int | None) -> str:
    """Convert meteorological wind degrees to cardinal compass label."""
    if deg is None:
        return "—"
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((float(deg) / 22.5) + 0.5) % 16
    return directions[idx]


def format_local_time(unix_ts: int, tz_offset_sec: int, fmt: str = "%I:%M %p") -> str:
    """Format a UTC unix timestamp into the city's local time."""
    tz = timezone(timedelta(seconds=tz_offset_sec))
    return datetime.fromtimestamp(unix_ts, tz=tz).strftime(fmt).lstrip("0")


def get_outfit_advisory(
    temp_c: float,
    humidity: int,
    wind_ms: float,
    condition_main: str,
) -> str:
    """Generate practical clothing and outdoor guidance from live weather."""
    tips: list[str] = []
    cond = condition_main.lower()

    if temp_c <= 5:
        tips.append("Bundle up with a heavy thermal coat, scarf, and gloves.")
    elif temp_c <= 14:
        tips.append("Wear a warm jacket or layered knitwear.")
    elif temp_c <= 22:
        tips.append("Comfortable conditions—light layers or a long-sleeve top.")
    elif temp_c <= 30:
        tips.append("Warm day—breathable cotton or linen clothing recommended.")
    else:
        tips.append("High heat—wear light UV-protective fabrics and stay hydrated.")

    if "rain" in cond or "drizzle" in cond or "thunderstorm" in cond:
        tips.append("Carry a waterproof umbrella or rain shell.")
    elif "snow" in cond:
        tips.append("Wear insulated waterproof boots with good traction.")
    elif "clear" in cond and temp_c >= 18:
        tips.append("Sunglasses and SPF sunscreen are ideal outdoors.")

    if wind_ms >= 8.0:
        tips.append("Breezy gusts—opt for a windproof outer layer.")
    if humidity >= 80 and temp_c >= 24:
        tips.append("High humidity may make it feel warmer than the thermometer reads.")

    return " ".join(tips)


def get_weather_theme(condition_main: str, icon_code: str = "01d") -> dict[str, str]:
    """Return a rich, high-contrast color palette tailored to the weather condition."""
    cond = (condition_main or "").lower()
    is_night = icon_code.endswith("n")

    if "thunderstorm" in cond:
        return {
            "name": "Midnight Storm",
            "bg": "#1E1B4B",
            "surface": "#2E296E",
            "card": "#FFFFFF",
            "card_muted": "#EEF2FF",
            "accent": "#F59E0B",
            "accent_hover": "#D97706",
            "hero_text": "#FFFFFF",
            "hero_sub": "#C7D2FE",
            "text": "#0F172A",
            "muted": "#475569",
            "border": "#CBD5E1",
        }
    if "rain" in cond or "drizzle" in cond:
        return {
            "name": "Coastal Rain",
            "bg": "#0F3D5E",
            "surface": "#164E75",
            "card": "#FFFFFF",
            "card_muted": "#EFF6FF",
            "accent": "#0284C7",
            "accent_hover": "#0369A1",
            "hero_text": "#FFFFFF",
            "hero_sub": "#BAE6FD",
            "text": "#0F172A",
            "muted": "#475569",
            "border": "#CBD5E1",
        }
    if "snow" in cond:
        return {
            "name": "Alpine Frost",
            "bg": "#1E3A5F",
            "surface": "#284B78",
            "card": "#FFFFFF",
            "card_muted": "#F0F9FF",
            "accent": "#0EA5E9",
            "accent_hover": "#0284C7",
            "hero_text": "#FFFFFF",
            "hero_sub": "#E0F2FE",
            "text": "#0F172A",
            "muted": "#475569",
            "border": "#CBD5E1",
        }
    if "cloud" in cond:
        return {
            "name": "Misty Overcast",
            "bg": "#334155",
            "surface": "#475569",
            "card": "#FFFFFF",
            "card_muted": "#F8FAFC",
            "accent": "#2563EB",
            "accent_hover": "#1D4ED8",
            "hero_text": "#FFFFFF",
            "hero_sub": "#CBD5E1",
            "text": "#0F172A",
            "muted": "#475569",
            "border": "#CBD5E1",
        }
    if "clear" in cond and not is_night:
        return {
            "name": "Sunlit Sky",
            "bg": "#0369A1",
            "surface": "#0284C7",
            "card": "#FFFFFF",
            "card_muted": "#FFFBEB",
            "accent": "#EA580C",
            "accent_hover": "#C2410C",
            "hero_text": "#FFFFFF",
            "hero_sub": "#E0F2FE",
            "text": "#0F172A",
            "muted": "#475569",
            "border": "#CBD5E1",
        }
    if is_night:
        return {
            "name": "Starlight Night",
            "bg": "#0F172A",
            "surface": "#1E293B",
            "card": "#FFFFFF",
            "card_muted": "#F1F5F9",
            "accent": "#4F46E5",
            "accent_hover": "#4338CA",
            "hero_text": "#FFFFFF",
            "hero_sub": "#CBD5E1",
            "text": "#0F172A",
            "muted": "#475569",
            "border": "#CBD5E1",
        }

    # Default vibrant atmospheric palette
    return {
        "name": "Atmosphere Azure",
        "bg": "#1D4ED8",
        "surface": "#1E40AF",
        "card": "#FFFFFF",
        "card_muted": "#F8FAFC",
        "accent": "#0EA5E9",
        "accent_hover": "#0284C7",
        "hero_text": "#FFFFFF",
        "hero_sub": "#DBEAFE",
        "text": "#0F172A",
        "muted": "#475569",
        "border": "#CBD5E1",
    }


def extract_next_6h_hourly(forecast_json: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract the next 6 hours from OpenWeatherMap /forecast (3-hour intervals).
    The first 2 entries cover +3h and +6h from the forecast start.
    """
    tz_offset = int(forecast_json.get("city", {}).get("timezone", 0))
    entries = forecast_json.get("list", [])[:2]
    results: list[dict[str, Any]] = []

    for item in entries:
        weather_info = (item.get("weather") or [{}])[0]
        results.append(
            {
                "dt": int(item["dt"]),
                "time_label": format_local_time(int(item["dt"]), tz_offset, "%I:%M %p"),
                "temp_c": float(item["main"]["temp"]),
                "feels_like_c": float(item["main"]["feels_like"]),
                "humidity": int(item["main"]["humidity"]),
                "pop_pct": int(round(float(item.get("pop", 0.0)) * 100)),
                "description": str(weather_info.get("description", "")).title(),
                "icon": str(weather_info.get("icon", "01d")),
            }
        )
    return results


def extract_5day_forecast(forecast_json: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Group OpenWeatherMap 3-hour /forecast entries by local calendar date
    and compute daily min/max temperatures and representative icon/condition.
    Returns up to 5 days.
    """
    tz_offset = int(forecast_json.get("city", {}).get("timezone", 0))
    tz = timezone(timedelta(seconds=tz_offset))
    today_str = datetime.now(tz=tz).strftime("%Y-%m-%d")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in forecast_json.get("list", []):
        local_dt = datetime.fromtimestamp(int(item["dt"]), tz=tz)
        grouped[local_dt.strftime("%Y-%m-%d")].append(item)

    daily_cards: list[dict[str, Any]] = []
    for date_str in sorted(grouped.keys()):
        day_items = grouped[date_str]
        local_date = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = "Today" if date_str == today_str else local_date.strftime("%a")
        date_label = local_date.strftime("%b %d").replace(" 0", " ")

        min_c = min(float(x["main"]["temp_min"]) for x in day_items)
        max_c = max(float(x["main"]["temp_max"]) for x in day_items)
        avg_pop = int(round(max(float(x.get("pop", 0.0)) for x in day_items) * 100))

        # Prefer midday (12:00) entry icon, otherwise most frequent daytime icon
        midday_item = min(
            day_items,
            key=lambda x: abs(datetime.fromtimestamp(int(x["dt"]), tz=tz).hour - 12),
        )
        icons = [
            str((x.get("weather") or [{}])[0].get("icon", "01d")).replace("n", "d")
            for x in day_items
        ]
        rep_icon = str((midday_item.get("weather") or [{}])[0].get("icon", ""))
        if not rep_icon:
            rep_icon = Counter(icons).most_common(1)[0][0]
        else:
            rep_icon = rep_icon.replace("n", "d")

        rep_desc = str((midday_item.get("weather") or [{}])[0].get("description", "")).title()

        daily_cards.append(
            {
                "date_str": date_str,
                "day_name": day_name,
                "date_label": date_label,
                "min_c": min_c,
                "max_c": max_c,
                "pop_pct": avg_pop,
                "description": rep_desc,
                "icon": rep_icon,
            }
        )
        if len(daily_cards) >= 5:
            break

    return daily_cards


class WeatherService:
    """Stateless API client for OpenWeatherMap and ipinfo.io."""

    def __init__(self, api_key: str | None = None, timeout: int = REQUEST_TIMEOUT) -> None:
        self.api_key = (api_key if api_key is not None else get_api_key()).strip()
        self.timeout = timeout

    def refresh_api_key(self) -> None:
        self.api_key = get_api_key()

    @staticmethod
    def _build_query_params(location_query: str) -> dict[str, str]:
        cleaned = location_query.strip()
        if not cleaned:
            raise WeatherAPIError(
                "Please enter a city name or ZIP code before searching.",
                error_type="empty_input",
            )
        # Detect numeric ZIP code (e.g. '10001' or '10001,US')
        if re.fullmatch(r"\d{4,10}(,\s*[A-Za-z]{2})?", cleaned):
            return {"zip": re.sub(r"\s+", "", cleaned)}
        return {"q": cleaned}

    def _get_json(self, url: str, params: dict[str, str]) -> dict[str, Any]:
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            raise WeatherAPIError(
                f"Request timed out after {self.timeout}s. Please check your internet connection.",
                error_type="timeout",
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise WeatherAPIError(
                "No internet connection or network unreachable. Please reconnect and try again.",
                error_type="network",
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise WeatherAPIError(
                f"Network error while contacting weather service: {exc}",
                error_type="network",
            ) from exc

        if response.status_code == 401:
            raise WeatherAPIError(
                "Invalid OpenWeatherMap API key (401). Note: newly created keys can take up to 2 hours to activate.",
                error_type="unauthorized",
            )
        if response.status_code == 404:
            raise WeatherAPIError(
                "City or ZIP code not found (404). Please check the spelling and try again.",
                error_type="not_found",
            )
        if not response.ok:
            detail = ""
            try:
                detail = str(response.json().get("message", ""))
            except ValueError:
                pass
            raise WeatherAPIError(
                f"Weather service returned HTTP {response.status_code}"
                + (f": {detail}" if detail else "."),
                error_type="http_error",
            )

        try:
            return response.json()
        except ValueError as exc:
            raise WeatherAPIError(
                "Received malformed JSON from weather service.",
                error_type="parse_error",
            ) from exc

    def fetch_icon_bytes(self, icon_code: str) -> bytes | None:
        """Download raw PNG bytes for an OpenWeatherMap icon."""
        if not icon_code:
            return None
        url = OPENWEATHER_ICON_URL.format(icon=icon_code)
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.ok:
                return resp.content
        except requests.exceptions.RequestException:
            return None
        return None

    def fetch_weather_bundle(self, location_query: str) -> dict[str, Any]:
        """
        Fetch current weather, 5-day/3-hour forecast, and weather icon bytes
        for the given city or ZIP code.
        """
        self.refresh_api_key()
        validate_api_key(self.api_key)

        loc_params = self._build_query_params(location_query)
        common_params = {**loc_params, "units": "metric", "appid": self.api_key}

        current_json = self._get_json(OPENWEATHER_WEATHER_URL, common_params)
        forecast_json = self._get_json(OPENWEATHER_FORECAST_URL, common_params)

        hourly_6h = extract_next_6h_hourly(forecast_json)
        daily_5d = extract_5day_forecast(forecast_json)

        current_icon = str((current_json.get("weather") or [{}])[0].get("icon", "01d"))
        icon_codes = {current_icon}
        for h in hourly_6h:
            icon_codes.add(h["icon"])
        for d in daily_5d:
            icon_codes.add(d["icon"])

        icons_bytes: dict[str, bytes | None] = {}
        for code in icon_codes:
            icons_bytes[code] = self.fetch_icon_bytes(code)

        return {
            "current": current_json,
            "forecast": forecast_json,
            "hourly_6h": hourly_6h,
            "daily_5d": daily_5d,
            "icons_bytes": icons_bytes,
        }

    def detect_location_city(self) -> str:
        """Detect the user's approximate city using ipinfo.io."""
        try:
            resp = requests.get(IPINFO_URL, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            raise WeatherAPIError(
                f"Location lookup timed out after {self.timeout}s. Please enter a city manually.",
                error_type="timeout",
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise WeatherAPIError(
                "Could not detect location (network error). Please enter a city manually.",
                error_type="network",
            ) from exc

        if not resp.ok:
            raise WeatherAPIError(
                f"Location lookup failed (HTTP {resp.status_code}). Please enter a city manually.",
                error_type="network",
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise WeatherAPIError(
                "Invalid response from ipinfo.io. Please enter a city manually.",
                error_type="parse_error",
            ) from exc

        city = str(data.get("city", "")).strip()
        country = str(data.get("country", "")).strip()
        if not city:
            raise WeatherAPIError(
                "ipinfo.io did not return a city name. Please enter a city manually.",
                error_type="not_found",
            )
        return f"{city},{country}" if country else city
