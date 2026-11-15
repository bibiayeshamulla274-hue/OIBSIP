"""
Weather App (Advanced Tier) — Python Tkinter Desktop GUI.

Uses config.py for OpenWeatherMap & ipinfo.io API calls, runs all network
operations in background threads to keep the GUI responsive, and supports
dynamic themes, °C/°F unit toggling without refetching, next 6h hourly
forecast, 5-day forecast, and outfit advisories.
"""

from __future__ import annotations

import io
import threading
import tkinter as tk
from tkinter import ttk
from typing import Any

from PIL import Image, ImageTk

from config import (
    WeatherAPIError,
    WeatherService,
    c_to_f,
    format_local_time,
    format_temp,
    get_api_key,
    get_outfit_advisory,
    get_weather_theme,
    get_wind_direction,
)


QUICK_CITIES = ["London", "Tokyo", "New York", "Mumbai", "Reykjavik", "Paris"]


class WeatherAppGUI:
    """Tkinter desktop interface for the OpenWeatherMap Weather App."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Atmosphere — Weather Studio (OIBSIP Task 4)")
        self.root.geometry("980x780")
        self.root.minsize(820, 660)

        self.service = WeatherService()
        self.unit: str = "C"  # "C" or "F"
        self.is_loading: bool = False
        self.weather_bundle: dict[str, Any] | None = None
        self.icon_refs: list[ImageTk.PhotoImage] = []  # prevent GC of PhotoImages
        self.theme = get_weather_theme("Default", "01d")

        self._build_styles()
        self._build_layout()
        self._check_initial_key_notice()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_styles(self) -> None:
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Loading.Horizontal.TProgressbar", thickness=5)

    def _build_layout(self) -> None:
        self.root.configure(bg=self.theme["bg"])

        # Top header bar
        self.header_frame = tk.Frame(self.root, bg=self.theme["bg"], padx=24, pady=16)
        self.header_frame.pack(fill="x")

        title_col = tk.Frame(self.header_frame, bg=self.theme["bg"])
        title_col.pack(side="left")

        self.brand_label = tk.Label(
            title_col,
            text="Atmosphere Weather Studio",
            font=("Segoe UI", 20, "bold"),
            fg=self.theme["hero_text"],
            bg=self.theme["bg"],
        )
        self.brand_label.pack(anchor="w")

        self.subtitle_label = tk.Label(
            title_col,
            text="Live forecasts, 6-hour outlook, 5-day trends & smart advisories",
            font=("Segoe UI", 10),
            fg=self.theme["hero_sub"],
            bg=self.theme["bg"],
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # Unit toggle button (°C / °F)
        controls_col = tk.Frame(self.header_frame, bg=self.theme["bg"])
        controls_col.pack(side="right", anchor="center")

        self.unit_btn = tk.Button(
            controls_col,
            text="Unit: °C  (Switch to °F)",
            command=self.toggle_unit,
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#0F172A",
            activebackground="#E2E8F0",
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
        )
        self.unit_btn.pack()

        # Search & Quick Actions Panel
        self.search_card = tk.Frame(
            self.root,
            bg="#FFFFFF",
            padx=20,
            pady=16,
            highlightthickness=1,
            highlightbackground="#CBD5E1",
        )
        self.search_card.pack(fill="x", padx=24, pady=(0, 12))

        search_row = tk.Frame(self.search_card, bg="#FFFFFF")
        search_row.pack(fill="x")

        self.city_var = tk.StringVar()
        self.city_entry = tk.Entry(
            search_row,
            textvariable=self.city_var,
            font=("Segoe UI", 12),
            bg="#F8FAFC",
            fg="#0F172A",
            relief="solid",
            bd=1,
            insertbackground="#0F172A",
        )
        self.city_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 10))
        self.city_entry.bind("<Return>", lambda _event: self.handle_search())
        self.city_entry.focus_set()

        self.search_btn = tk.Button(
            search_row,
            text="Get Weather",
            command=self.handle_search,
            font=("Segoe UI", 10, "bold"),
            bg=self.theme["accent"],
            fg="#FFFFFF",
            activebackground=self.theme["accent_hover"],
            activeforeground="#FFFFFF",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
        )
        self.search_btn.pack(side="left", padx=(0, 8))

        self.locate_btn = tk.Button(
            search_row,
            text="Auto-detect my location",
            command=self.handle_auto_locate,
            font=("Segoe UI", 10, "bold"),
            bg="#F1F5F9",
            fg="#0F172A",
            activebackground="#E2E8F0",
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
        )
        self.locate_btn.pack(side="left")

        # Quick-pick destinations row
        quick_row = tk.Frame(self.search_card, bg="#FFFFFF")
        quick_row.pack(fill="x", pady=(10, 0))

        tk.Label(
            quick_row,
            text="Quick explore:",
            font=("Segoe UI", 9, "bold"),
            fg="#64748B",
            bg="#FFFFFF",
        ).pack(side="left", padx=(0, 8))

        for city_name in QUICK_CITIES:
            btn = tk.Button(
                quick_row,
                text=city_name,
                command=lambda c=city_name: self.search_preset(c),
                font=("Segoe UI", 9),
                bg="#EFF6FF",
                fg="#1D4ED8",
                activebackground="#DBEAFE",
                relief="flat",
                padx=10,
                pady=3,
                cursor="hand2",
            )
            btn.pack(side="left", padx=3)

        # Inline Error Banner (hidden by default)
        self.error_frame = tk.Frame(
            self.root,
            bg="#FEE2E2",
            padx=16,
            pady=10,
            highlightthickness=1,
            highlightbackground="#EF4444",
        )
        self.error_label = tk.Label(
            self.error_frame,
            text="",
            font=("Segoe UI", 10, "bold"),
            fg="#B91C1C",
            bg="#FEE2E2",
            wraplength=880,
            justify="left",
        )
        self.error_label.pack(side="left", fill="x", expand=True)

        self.dismiss_err_btn = tk.Button(
            self.error_frame,
            text="Dismiss",
            command=self.clear_error,
            font=("Segoe UI", 9, "bold"),
            bg="#FECACA",
            fg="#991B1B",
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
        )
        self.dismiss_err_btn.pack(side="right", padx=(10, 0))

        # Loading status bar
        self.loading_frame = tk.Frame(self.root, bg=self.theme["bg"], padx=24)
        self.loading_label = tk.Label(
            self.loading_frame,
            text="Fetching live weather data...",
            font=("Segoe UI", 10),
            fg=self.theme["hero_text"],
            bg=self.theme["bg"],
        )
        self.loading_label.pack(side="left", padx=(0, 12))
        self.progress = ttk.Progressbar(
            self.loading_frame,
            mode="indeterminate",
            style="Loading.Horizontal.TProgressbar",
            length=220,
        )
        self.progress.pack(side="left")

        # Scrollable main results viewport
        self.canvas_container = tk.Frame(self.root, bg=self.theme["bg"])
        self.canvas_container.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        self.canvas = tk.Canvas(
            self.canvas_container,
            bg=self.theme["bg"],
            highlightthickness=0,
        )
        self.scrollbar = ttk.Scrollbar(
            self.canvas_container,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.results_frame = tk.Frame(self.canvas, bg=self.theme["bg"])

        self.results_frame.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.results_frame, anchor="nw"
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda _e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda _e: self.canvas.yview_scroll(1, "units"))

        self._render_landing_welcome()

    def _on_mousewheel(self, event: tk.Event) -> None:
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _check_initial_key_notice(self) -> None:
        key = get_api_key()
        if not key or key == "PASTE_YOUR_KEY_HERE":
            self.show_error(
                "API key not configured yet. Copy .env.example to .env and set "
                "OPENWEATHER_API_KEY=your_key before searching."
            )

    # ------------------------------------------------------------------
    # Theme & State Helpers
    # ------------------------------------------------------------------

    def _apply_theme(self, theme: dict[str, str]) -> None:
        self.theme = theme
        self.root.configure(bg=theme["bg"])
        self.header_frame.configure(bg=theme["bg"])
        for child in self.header_frame.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=theme["bg"])
        self.brand_label.configure(bg=theme["bg"], fg=theme["hero_text"])
        self.subtitle_label.configure(bg=theme["bg"], fg=theme["hero_sub"])
        self.search_btn.configure(bg=theme["accent"], activebackground=theme["accent_hover"])
        self.loading_frame.configure(bg=theme["bg"])
        self.loading_label.configure(bg=theme["bg"], fg=theme["hero_text"])
        self.canvas_container.configure(bg=theme["bg"])
        self.canvas.configure(bg=theme["bg"])
        self.results_frame.configure(bg=theme["bg"])

    def show_error(self, message: str) -> None:
        self.error_label.configure(text=f"Error: {message}")
        self.error_frame.pack(fill="x", padx=24, pady=(0, 10), before=self.canvas_container)

    def clear_error(self) -> None:
        self.error_frame.pack_forget()

    def set_loading(self, loading: bool, message: str = "Fetching live weather data...") -> None:
        self.is_loading = loading
        state = "disabled" if loading else "normal"
        self.search_btn.configure(state=state)
        self.locate_btn.configure(state=state)
        if loading:
            self.loading_label.configure(text=message)
            self.loading_frame.pack(fill="x", pady=(0, 8), before=self.canvas_container)
            self.progress.start(12)
        else:
            self.progress.stop()
            self.loading_frame.pack_forget()

    def _clear_results_frame(self) -> None:
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.icon_refs.clear()

    def _make_photo_image(self, raw_bytes: bytes | None, size: tuple[int, int]) -> ImageTk.PhotoImage | None:
        if not raw_bytes:
            return None
        try:
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
            img = img.resize(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.icon_refs.append(photo)
            return photo
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Actions & Threading
    # ------------------------------------------------------------------

    def search_preset(self, city: str) -> None:
        self.city_var.set(city)
        self.handle_search()

    def handle_search(self) -> None:
        if self.is_loading:
            return
        query = self.city_var.get().strip()
        if not query:
            self.show_error("Please enter a city name or ZIP code.")
            return

        self.clear_error()
        self.set_loading(True, f"Fetching weather for '{query}'...")

        thread = threading.Thread(
            target=self._worker_fetch_weather,
            args=(query,),
            daemon=True,
        )
        thread.start()

    def handle_auto_locate(self) -> None:
        if self.is_loading:
            return
        self.clear_error()
        self.set_loading(True, "Detecting your city via ipinfo.io...")

        thread = threading.Thread(
            target=self._worker_auto_locate,
            daemon=True,
        )
        thread.start()

    def _worker_fetch_weather(self, query: str) -> None:
        try:
            bundle = self.service.fetch_weather_bundle(query)
            self.root.after(0, self._on_fetch_success, bundle)
        except WeatherAPIError as exc:
            self.root.after(0, self._on_fetch_error, exc.message)
        except Exception as exc:
            self.root.after(0, self._on_fetch_error, f"Unexpected error: {exc}")

    def _worker_auto_locate(self) -> None:
        try:
            detected_city = self.service.detect_location_city()
            self.root.after(0, lambda: self.city_var.set(detected_city))
            bundle = self.service.fetch_weather_bundle(detected_city)
            self.root.after(0, self._on_fetch_success, bundle)
        except WeatherAPIError as exc:
            self.root.after(0, self._on_fetch_error, exc.message)
        except Exception as exc:
            self.root.after(0, self._on_fetch_error, f"Unexpected error: {exc}")

    def _on_fetch_success(self, bundle: dict[str, Any]) -> None:
        self.set_loading(False)
        self.weather_bundle = bundle
        current = bundle["current"]
        cond_main = str((current.get("weather") or [{}])[0].get("main", "Default"))
        icon_code = str((current.get("weather") or [{}])[0].get("icon", "01d"))
        self._apply_theme(get_weather_theme(cond_main, icon_code))
        self.render_weather()

    def _on_fetch_error(self, message: str) -> None:
        self.set_loading(False)
        self.show_error(message)

    def toggle_unit(self) -> None:
        """Switch between °C and °F and re-render all panels from stored data."""
        self.unit = "F" if self.unit == "C" else "C"
        next_label = "°C" if self.unit == "F" else "°F"
        self.unit_btn.configure(text=f"Unit: °{self.unit}  (Switch to {next_label})")
        if self.weather_bundle is not None:
            self.render_weather()

    # ------------------------------------------------------------------
    # Rendering Views
    # ------------------------------------------------------------------

    def _render_landing_welcome(self) -> None:
        self._clear_results_frame()

        hero = tk.Frame(
            self.results_frame,
            bg="#FFFFFF",
            padx=28,
            pady=26,
            highlightthickness=1,
            highlightbackground="#CBD5E1",
        )
        hero.pack(fill="x", pady=(6, 14))

        tk.Label(
            hero,
            text="Explore Global Weather in Real Time",
            font=("Segoe UI", 18, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        ).pack(anchor="w")

        tk.Label(
            hero,
            text=(
                "Search any city or ZIP code above, click a quick destination, or use "
                "Auto-detect my location to load live conditions, next 6-hour intervals, "
                "5-day trends, and smart outfit advisories."
            ),
            font=("Segoe UI", 10),
            fg="#475569",
            bg="#FFFFFF",
            wraplength=840,
            justify="left",
        ).pack(anchor="w", pady=(6, 16))

        # Interactive atmosphere theme preview strip
        tk.Label(
            hero,
            text="Interactive Atmosphere Preview — test dynamic condition color themes:",
            font=("Segoe UI", 9, "bold"),
            fg="#334155",
            bg="#FFFFFF",
        ).pack(anchor="w", pady=(0, 8))

        preview_row = tk.Frame(hero, bg="#FFFFFF")
        preview_row.pack(fill="x")

        moods = [
            ("Sunlit Sky", "Clear", "01d", "#0369A1"),
            ("Coastal Rain", "Rain", "10d", "#0F3D5E"),
            ("Midnight Storm", "Thunderstorm", "11d", "#1E1B4B"),
            ("Alpine Frost", "Snow", "13d", "#1E3A5F"),
            ("Misty Overcast", "Clouds", "04d", "#334155"),
        ]
        for label, cond, icon, swatch in moods:
            tk.Button(
                preview_row,
                text=label,
                command=lambda c=cond, ic=icon: self._apply_theme(get_weather_theme(c, ic)),
                font=("Segoe UI", 9, "bold"),
                bg=swatch,
                fg="#FFFFFF",
                activebackground=swatch,
                activeforeground="#FFFFFF",
                relief="flat",
                padx=12,
                pady=6,
                cursor="hand2",
            ).pack(side="left", padx=(0, 8))

        # Feature highlight grid
        features_row = tk.Frame(self.results_frame, bg=self.theme["bg"])
        features_row.pack(fill="x")

        cards = [
            (
                "Dual-Scale Precision",
                "View simultaneous °C and °F values and toggle every panel instantly from cached data.",
            ),
            (
                "6-Hour & 5-Day Forecasts",
                "Inspect upcoming 3-hour intervals alongside grouped 5-day min/max outlooks.",
            ),
            (
                "Non-Blocking Threads",
                "Background threading + 10s timeouts keep the desktop interface fluid on slow networks.",
            ),
        ]
        for idx, (title, desc) in enumerate(cards):
            card = tk.Frame(
                features_row,
                bg="#FFFFFF",
                padx=18,
                pady=16,
                highlightthickness=1,
                highlightbackground="#CBD5E1",
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 8, 0))
            features_row.columnconfigure(idx, weight=1)
            tk.Label(
                card,
                text=title,
                font=("Segoe UI", 11, "bold"),
                fg="#0F172A",
                bg="#FFFFFF",
            ).pack(anchor="w")
            tk.Label(
                card,
                text=desc,
                font=("Segoe UI", 9),
                fg="#475569",
                bg="#FFFFFF",
                wraplength=250,
                justify="left",
            ).pack(anchor="w", pady=(6, 0))

    def render_weather(self) -> None:
        if not self.weather_bundle:
            return
        self._clear_results_frame()

        current = self.weather_bundle["current"]
        hourly_6h = self.weather_bundle["hourly_6h"]
        daily_5d = self.weather_bundle["daily_5d"]
        icons_bytes = self.weather_bundle["icons_bytes"]

        city_name = current.get("name", "Unknown")
        country = current.get("sys", {}).get("country", "")
        tz_offset = int(current.get("timezone", 0))
        weather_obj = (current.get("weather") or [{}])[0]
        cond_main = str(weather_obj.get("main", ""))
        cond_desc = str(weather_obj.get("description", "")).title()
        icon_code = str(weather_obj.get("icon", "01d"))

        temp_c = float(current["main"]["temp"])
        feels_c = float(current["main"]["feels_like"])
        temp_min_c = float(current["main"]["temp_min"])
        temp_max_c = float(current["main"]["temp_max"])
        humidity = int(current["main"]["humidity"])
        pressure = int(current["main"].get("pressure", 0))
        visibility_km = float(current.get("visibility", 0)) / 1000.0
        wind_ms = float(current.get("wind", {}).get("speed", 0.0))
        wind_kmh = wind_ms * 3.6
        wind_dir = get_wind_direction(current.get("wind", {}).get("deg"))

        sunrise = current.get("sys", {}).get("sunrise")
        sunset = current.get("sys", {}).get("sunset")
        sunrise_str = format_local_time(int(sunrise), tz_offset) if sunrise else "—"
        sunset_str = format_local_time(int(sunset), tz_offset) if sunset else "—"

        # 1. Current Weather Card
        curr_card = tk.Frame(
            self.results_frame,
            bg="#FFFFFF",
            padx=24,
            pady=20,
            highlightthickness=1,
            highlightbackground="#CBD5E1",
        )
        curr_card.pack(fill="x", pady=(4, 12))

        top_row = tk.Frame(curr_card, bg="#FFFFFF")
        top_row.pack(fill="x")

        left_info = tk.Frame(top_row, bg="#FFFFFF")
        left_info.pack(side="left", anchor="nw")

        location_title = f"{city_name}, {country}" if country else city_name
        tk.Label(
            left_info,
            text=location_title,
            font=("Segoe UI", 22, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        ).pack(anchor="w")

        local_now = format_local_time(int(current["dt"]), tz_offset, "%a, %b %d · %I:%M %p")
        tk.Label(
            left_info,
            text=f"Local observation: {local_now}  ·  {cond_desc}",
            font=("Segoe UI", 10),
            fg="#475569",
            bg="#FFFFFF",
        ).pack(anchor="w", pady=(2, 10))

        temp_row = tk.Frame(left_info, bg="#FFFFFF")
        temp_row.pack(anchor="w")

        primary_temp = format_temp(temp_c, self.unit, precision=1)
        alt_unit = "F" if self.unit == "C" else "C"
        secondary_temp = format_temp(temp_c, alt_unit, precision=1)

        tk.Label(
            temp_row,
            text=primary_temp,
            font=("Segoe UI", 36, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        ).pack(side="left")

        tk.Label(
            temp_row,
            text=f"  ({secondary_temp})   ·   Feels like {format_temp(feels_c, self.unit)}",
            font=("Segoe UI", 11),
            fg="#475569",
            bg="#FFFFFF",
        ).pack(side="left", anchor="s", pady=(0, 8))

        tk.Label(
            left_info,
            text=f"Day Range: Low {format_temp(temp_min_c, self.unit)}  /  High {format_temp(temp_max_c, self.unit)}",
            font=("Segoe UI", 9, "bold"),
            fg="#334155",
            bg="#FFFFFF",
        ).pack(anchor="w", pady=(4, 0))

        # Right side icon
        right_icon = tk.Frame(top_row, bg=self.theme["card_muted"], padx=14, pady=8)
        right_icon.pack(side="right", anchor="ne")

        photo = self._make_photo_image(icons_bytes.get(icon_code), (96, 96))
        if photo is not None:
            tk.Label(right_icon, image=photo, bg=self.theme["card_muted"]).pack()
        else:
            tk.Label(
                right_icon,
                text=cond_main or "Weather",
                font=("Segoe UI", 12, "bold"),
                fg="#0F172A",
                bg=self.theme["card_muted"],
                width=10,
                height=4,
            ).pack()
        tk.Label(
            right_icon,
            text=cond_desc,
            font=("Segoe UI", 9, "bold"),
            fg="#334155",
            bg=self.theme["card_muted"],
        ).pack()

        # Metrics Grid (Humidity, Wind, Pressure/Visibility, Sunrise/Sunset)
        metrics_row = tk.Frame(curr_card, bg="#FFFFFF")
        metrics_row.pack(fill="x", pady=(16, 12))

        metric_items = [
            ("Humidity", f"{humidity}%", "Relative moisture"),
            ("Wind", f"{wind_ms:.1f} m/s ({wind_kmh:.0f} km/h)", f"Direction: {wind_dir}"),
            ("Pressure & Visibility", f"{pressure} hPa", f"Visibility: {visibility_km:.1f} km"),
            ("Daylight Window", f"↑ {sunrise_str}", f"↓ Sunset {sunset_str}"),
        ]
        for idx, (m_title, m_val, m_sub) in enumerate(metric_items):
            tile = tk.Frame(
                metrics_row,
                bg="#F8FAFC",
                padx=12,
                pady=10,
                highlightthickness=1,
                highlightbackground="#E2E8F0",
            )
            tile.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 8, 0))
            metrics_row.columnconfigure(idx, weight=1)
            tk.Label(tile, text=m_title, font=("Segoe UI", 9, "bold"), fg="#64748B", bg="#F8FAFC").pack(anchor="w")
            tk.Label(tile, text=m_val, font=("Segoe UI", 12, "bold"), fg="#0F172A", bg="#F8FAFC").pack(anchor="w", pady=(3, 1))
            tk.Label(tile, text=m_sub, font=("Segoe UI", 8), fg="#475569", bg="#F8FAFC").pack(anchor="w")

        # Unique Feature: Smart Outfit & Activity Advisory
        advisory_text = get_outfit_advisory(temp_c, humidity, wind_ms, cond_main)
        advisory_box = tk.Frame(
            curr_card,
            bg="#EFF6FF",
            padx=14,
            pady=10,
            highlightthickness=1,
            highlightbackground="#BFDBFE",
        )
        advisory_box.pack(fill="x")
        tk.Label(
            advisory_box,
            text=f"Smart Outfit & Activity Advisory:  {advisory_text}",
            font=("Segoe UI", 9, "bold"),
            fg="#1E3A8A",
            bg="#EFF6FF",
            wraplength=850,
            justify="left",
        ).pack(anchor="w")

        # 2. Next 6 Hours Hourly Forecast Panel
        hourly_card = tk.Frame(
            self.results_frame,
            bg="#FFFFFF",
            padx=20,
            pady=16,
            highlightthickness=1,
            highlightbackground="#CBD5E1",
        )
        hourly_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            hourly_card,
            text="Hourly Forecast — Next 6 Hours (3-Hour Intervals)",
            font=("Segoe UI", 13, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        ).pack(anchor="w", pady=(0, 10))

        hourly_grid = tk.Frame(hourly_card, bg="#FFFFFF")
        hourly_grid.pack(fill="x")

        if hourly_6h:
            for idx, entry in enumerate(hourly_6h):
                h_tile = tk.Frame(
                    hourly_grid,
                    bg="#F8FAFC",
                    padx=16,
                    pady=12,
                    highlightthickness=1,
                    highlightbackground="#E2E8F0",
                )
                h_tile.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 10, 0))
                hourly_grid.columnconfigure(idx, weight=1)

                left_h = tk.Frame(h_tile, bg="#F8FAFC")
                left_h.pack(side="left", fill="y")
                tk.Label(
                    left_h,
                    text=entry["time_label"],
                    font=("Segoe UI", 11, "bold"),
                    fg="#0F172A",
                    bg="#F8FAFC",
                ).pack(anchor="w")
                tk.Label(
                    left_h,
                    text=f"{format_temp(entry['temp_c'], self.unit)}  (Feels {format_temp(entry['feels_like_c'], self.unit)})",
                    font=("Segoe UI", 12, "bold"),
                    fg=self.theme["accent"],
                    bg="#F8FAFC",
                ).pack(anchor="w", pady=(3, 2))
                tk.Label(
                    left_h,
                    text=f"{entry['description']}  ·  Humidity {entry['humidity']}%  ·  Rain {entry['pop_pct']}%",
                    font=("Segoe UI", 9),
                    fg="#475569",
                    bg="#F8FAFC",
                ).pack(anchor="w")

                h_photo = self._make_photo_image(icons_bytes.get(entry["icon"]), (56, 56))
                if h_photo is not None:
                    tk.Label(h_tile, image=h_photo, bg="#F8FAFC").pack(side="right")

        # 3. 5-Day Forecast Panel
        daily_card = tk.Frame(
            self.results_frame,
            bg="#FFFFFF",
            padx=20,
            pady=16,
            highlightthickness=1,
            highlightbackground="#CBD5E1",
        )
        daily_card.pack(fill="x", pady=(0, 8))

        tk.Label(
            daily_card,
            text="5-Day Forecast (Grouped by Date)",
            font=("Segoe UI", 13, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        ).pack(anchor="w", pady=(0, 10))

        daily_grid = tk.Frame(daily_card, bg="#FFFFFF")
        daily_grid.pack(fill="x")

        for idx, day in enumerate(daily_5d):
            d_tile = tk.Frame(
                daily_grid,
                bg="#F8FAFC",
                padx=12,
                pady=12,
                highlightthickness=1,
                highlightbackground="#E2E8F0",
            )
            d_tile.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 8, 0))
            daily_grid.columnconfigure(idx, weight=1)

            tk.Label(
                d_tile,
                text=f"{day['day_name']} · {day['date_label']}",
                font=("Segoe UI", 10, "bold"),
                fg="#0F172A",
                bg="#F8FAFC",
            ).pack()

            d_photo = self._make_photo_image(icons_bytes.get(day["icon"]), (54, 54))
            if d_photo is not None:
                tk.Label(d_tile, image=d_photo, bg="#F8FAFC").pack(pady=4)

            max_str = format_temp(day["max_c"], self.unit, precision=0)
            min_str = format_temp(day["min_c"], self.unit, precision=0)
            tk.Label(
                d_tile,
                text=f"High {max_str} / Low {min_str}",
                font=("Segoe UI", 10, "bold"),
                fg="#0F172A",
                bg="#F8FAFC",
            ).pack()

            tk.Label(
                d_tile,
                text=day["description"],
                font=("Segoe UI", 8),
                fg="#475569",
                bg="#F8FAFC",
                wraplength=140,
                justify="center",
            ).pack(pady=(3, 0))

            tk.Label(
                d_tile,
                text=f"Precip {day['pop_pct']}%",
                font=("Segoe UI", 8, "bold"),
                fg="#0284C7",
                bg="#F8FAFC",
            ).pack(pady=(2, 0))


def main() -> None:
    root = tk.Tk()
    WeatherAppGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
