"""
bmi_calculator.py
Advanced BMI Calculator Desktop Application (tkinter + SQLite + matplotlib).
Oasis Infobyte Python Programming Internship - Task 2.

Colorful & Interactive Features:
- Deep teal header banner and dynamic color-coded result cards
- Interactive Height Unit toggle (meters 'm' or centimeters 'cm')
- Clickable BMI Category Reference buttons for instant guidance & sample preview
- Healthy Weight Target Range (18.5–24.9 BMI) and exact kg delta
- Shaded BMI zone bands + per-point category-colored markers on matplotlib chart
- Customizable Goal BMI line and one-click CSV export
"""

import csv
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional, Tuple

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from database import BMIDatabase, DatabaseError


# Validation bounds as specified (in kg and meters)
MIN_WEIGHT_KG = 10.0
MAX_WEIGHT_KG = 300.0
MIN_HEIGHT_M = 0.5
MAX_HEIGHT_M = 2.5

# Theme palette
HEADER_BG = "#0F766E"
CANVAS_BG = "#F0FDFA"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#CCFBF1"

# Category thresholds and color mapping
CATEGORY_STYLES = {
    "Underweight": {
        "color": "#2563EB",
        "bg": "#EFF6FF",
        "range": "< 18.5",
        "tip": "Consider nutrient-dense meals and strength training to reach the 18.5–24.9 corridor.",
        "sample_bmi": 17.2,
    },
    "Normal": {
        "color": "#16A34A",
        "bg": "#ECFDF5",
        "range": "18.5 – 24.9",
        "tip": "Great balance. Maintain consistent nutrition, sleep, and weekly activity.",
        "sample_bmi": 22.0,
    },
    "Overweight": {
        "color": "#EA580C",
        "bg": "#FFF7ED",
        "range": "25.0 – 29.9",
        "tip": "Moderate cardio and a steady calorie deficit can guide you toward the Normal corridor.",
        "sample_bmi": 27.2,
    },
    "Obese": {
        "color": "#DC2626",
        "bg": "#FEF2F2",
        "range": ">= 30.0",
        "tip": "Consider consulting a healthcare provider for a safe, gradual nutrition and movement plan.",
        "sample_bmi": 32.5,
    },
}


def classify_bmi(bmi: float) -> Tuple[str, str, str]:
    """
    Classify a BMI value into its standard category and return
    (category_name, text_hex_color, card_bg_hex_color).
    """
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25.0:
        category = "Normal"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obese"

    style = CATEGORY_STYLES[category]
    return category, style["color"], style["bg"]


def compute_healthy_weight_guidance(weight: float, height: float) -> Tuple[float, float, str]:
    """
    Calculate the Normal BMI (18.5 - 24.9) healthy weight corridor for the given height
    and return (min_healthy_kg, max_healthy_kg, guidance_message).
    """
    min_healthy = round(18.5 * (height * height), 1)
    max_healthy = round(24.9 * (height * height), 1)

    if weight < min_healthy:
        delta = round(min_healthy - weight, 1)
        msg = f"Healthy range: {min_healthy:.1f}–{max_healthy:.1f} kg  |  Gain ~{delta:.1f} kg to reach Normal"
    elif weight > max_healthy:
        delta = round(weight - max_healthy, 1)
        msg = f"Healthy range: {min_healthy:.1f}–{max_healthy:.1f} kg  |  Lose ~{delta:.1f} kg to reach Normal"
    else:
        msg = f"Healthy range: {min_healthy:.1f}–{max_healthy:.1f} kg  |  Within healthy weight target"

    return min_healthy, max_healthy, msg


def validate_inputs(
    username_raw: str,
    weight_raw: str,
    height_raw: str,
    height_unit: str = "m",
) -> Tuple[Optional[str], Optional[float], Optional[float], Optional[str]]:
    """
    Validate user inputs for username, weight (kg), and height (m or cm).
    Converts height to meters if height_unit == 'cm'.
    Returns (username, weight_kg, height_m, error_message).
    """
    username = username_raw.strip()
    if not username:
        return None, None, None, "Please enter a username before calculating."

    if not weight_raw.strip() or not height_raw.strip():
        return None, None, None, "Weight and Height fields cannot be empty."

    try:
        weight = float(weight_raw.strip())
        height_val = float(height_raw.strip())
    except ValueError:
        return (
            None,
            None,
            None,
            "Weight and Height must be valid numeric values (e.g., 68.5 and 1.72).",
        )

    if not (math.isfinite(weight) and math.isfinite(height_val)):
        return None, None, None, "Weight and Height must be finite numbers."

    if weight <= 0 or height_val <= 0:
        return None, None, None, "Weight and Height must be greater than zero."

    height = height_val / 100.0 if height_unit == "cm" else height_val

    if not (MIN_WEIGHT_KG <= weight <= MAX_WEIGHT_KG):
        return (
            None,
            None,
            None,
            f"Please enter a realistic weight between {MIN_WEIGHT_KG:.0f} kg and {MAX_WEIGHT_KG:.0f} kg.",
        )

    if not (MIN_HEIGHT_M <= height <= MAX_HEIGHT_M):
        if height_unit == "cm":
            return (
                None,
                None,
                None,
                f"Please enter a realistic height between {MIN_HEIGHT_M * 100:.0f} cm and {MAX_HEIGHT_M * 100:.0f} cm.",
            )
        return (
            None,
            None,
            None,
            f"Please enter a realistic height between {MIN_HEIGHT_M:.1f} m and {MAX_HEIGHT_M:.1f} m.",
        )

    return username, weight, round(height, 4), None


class BMICalculatorApp:
    """Main tkinter GUI application for the Advanced BMI Calculator."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("BMI Studio — Oasis Infobyte")
        self.root.geometry("610x730")
        self.root.minsize(560, 680)
        self.root.configure(bg=CANVAS_BG)

        # Initialize SQLite database safely and seed multi-user dummy data on first run
        self.db: Optional[BMIDatabase] = None
        try:
            self.db = BMIDatabase()
            self.db.seed_sample_data()
        except DatabaseError as exc:
            messagebox.showerror("Database Error", str(exc))

        self.height_unit_var = tk.StringVar(value="m")
        self._configure_styles()
        self._build_ui()
        self._refresh_user_dropdown()
        if not self.username_var.get() and self.username_combo["values"]:
            self.username_var.set(self.username_combo["values"][0])

    def _configure_styles(self) -> None:
        """Configure ttk widget styles for a clean colorful appearance."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        """Construct all GUI widgets and layout."""
        # Top Colored Banner
        header_banner = tk.Frame(self.root, bg=HEADER_BG, padx=28, pady=18)
        header_banner.pack(fill="x")

        tk.Label(
            header_banner,
            text="BMI Studio",
            font=("Segoe UI", 20, "bold"),
            fg="#FFFFFF",
            bg=HEADER_BG,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            header_banner,
            text="Interactive multi-user BMI calculator, healthy weight corridor & visual trends.",
            font=("Segoe UI", 10),
            fg="#CCFBF1",
            bg=HEADER_BG,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        container = tk.Frame(self.root, bg=CANVAS_BG, padx=26, pady=18)
        container.pack(fill="both", expand=True)

        # Input Card
        input_card = tk.Frame(
            container,
            bg=CARD_BG,
            highlightbackground="#99F6E4",
            highlightthickness=1,
            padx=20,
            pady=16,
        )
        input_card.pack(fill="x")
        input_card.columnconfigure(1, weight=1)

        label_opts = {"font": ("Segoe UI", 10, "bold"), "fg": "#0F172A", "bg": CARD_BG, "anchor": "w"}
        entry_opts = {
            "font": ("Segoe UI", 11),
            "fg": "#0F172A",
            "bg": "#F8FAFC",
            "relief": "solid",
            "bd": 1,
        }

        # Username Field (Combobox)
        tk.Label(input_card, text="Username", **label_opts).grid(
            row=0, column=0, sticky="w", pady=(0, 10), padx=(0, 16)
        )
        self.username_var = tk.StringVar()
        self.username_combo = ttk.Combobox(
            input_card,
            textvariable=self.username_var,
            font=("Segoe UI", 11),
        )
        self.username_combo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=(0, 10), ipady=3)

        # Weight Field
        tk.Label(input_card, text="Weight (kg)", **label_opts).grid(
            row=1, column=0, sticky="w", pady=(0, 10), padx=(0, 16)
        )
        self.weight_var = tk.StringVar()
        self.weight_entry = tk.Entry(input_card, textvariable=self.weight_var, **entry_opts)
        self.weight_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(0, 10), ipady=5)

        # Height Field + Interactive m / cm Unit Toggle
        self.height_label = tk.Label(input_card, text="Height (m)", **label_opts)
        self.height_label.grid(row=2, column=0, sticky="w", pady=(0, 10), padx=(0, 16))
        self.height_var = tk.StringVar()
        self.height_entry = tk.Entry(input_card, textvariable=self.height_var, **entry_opts)
        self.height_entry.grid(row=2, column=1, sticky="ew", pady=(0, 10), ipady=5)

        unit_frame = tk.Frame(input_card, bg=CARD_BG)
        unit_frame.grid(row=2, column=2, sticky="e", padx=(8, 0), pady=(0, 10))
        tk.Radiobutton(
            unit_frame,
            text="m",
            variable=self.height_unit_var,
            value="m",
            command=self._on_unit_change,
            bg=CARD_BG,
            fg="#0F766E",
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        ).pack(side="left")
        tk.Radiobutton(
            unit_frame,
            text="cm",
            variable=self.height_unit_var,
            value="cm",
            command=self._on_unit_change,
            bg=CARD_BG,
            fg="#0F766E",
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        ).pack(side="left")

        # Goal BMI Field
        tk.Label(input_card, text="Goal BMI", **label_opts).grid(
            row=3, column=0, sticky="w", pady=(0, 2), padx=(0, 16)
        )
        self.goal_bmi_var = tk.StringVar(value="22.0")
        self.goal_bmi_entry = tk.Entry(input_card, textvariable=self.goal_bmi_var, **entry_opts)
        self.goal_bmi_entry.grid(row=3, column=1, columnspan=2, sticky="ew", pady=(0, 2), ipady=5)

        # Primary & Clear Buttons Row
        action_row = tk.Frame(container, bg=CANVAS_BG)
        action_row.pack(fill="x", pady=(12, 12))

        self.calc_btn = tk.Button(
            action_row,
            text="Calculate BMI",
            command=self.handle_calculate,
            font=("Segoe UI", 10, "bold"),
            fg="#FFFFFF",
            bg="#0F766E",
            activebackground="#115E59",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=9,
        )
        self.calc_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.clear_btn = tk.Button(
            action_row,
            text="Clear",
            command=self.handle_clear,
            font=("Segoe UI", 10, "bold"),
            fg="#1E293B",
            bg="#E2E8F0",
            activebackground="#CBD5E1",
            activeforeground="#0F172A",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=9,
        )
        self.clear_btn.pack(side="left")

        # Dynamic Color-Coded Result Card
        self.result_card = tk.Frame(
            container,
            bg=CARD_BG,
            highlightbackground="#CBD5E1",
            highlightthickness=2,
            padx=20,
            pady=14,
        )
        self.result_card.pack(fill="x", pady=(0, 12))

        self.result_title_label = tk.Label(
            self.result_card,
            text="Your BMI Result",
            font=("Segoe UI", 10, "bold"),
            fg="#64748B",
            bg=CARD_BG,
        )
        self.result_title_label.pack(anchor="w")

        self.bmi_value_label = tk.Label(
            self.result_card,
            text="--",
            font=("Segoe UI", 32, "bold"),
            fg="#0F172A",
            bg=CARD_BG,
        )
        self.bmi_value_label.pack(anchor="w", pady=(2, 2))

        self.category_label = tk.Label(
            self.result_card,
            text="Enter your details above or click a category below to explore.",
            font=("Segoe UI", 11, "bold"),
            fg="#475569",
            bg=CARD_BG,
        )
        self.category_label.pack(anchor="w")

        self.guidance_label = tk.Label(
            self.result_card,
            text="Healthy weight corridor and target delta will appear here.",
            font=("Segoe UI", 9),
            fg="#64748B",
            bg=CARD_BG,
            wraplength=510,
            justify="left",
        )
        self.guidance_label.pack(anchor="w", pady=(5, 0))

        # History, Graph, Export CSV, and Delete Buttons Row
        secondary_row = tk.Frame(container, bg=CANVAS_BG)
        secondary_row.pack(fill="x", pady=(0, 12))

        self.history_btn = tk.Button(
            secondary_row,
            text="View History",
            command=self.handle_view_history,
            font=("Segoe UI", 9, "bold"),
            fg="#1D4ED8",
            bg="#EFF6FF",
            activebackground="#DBEAFE",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=10,
            pady=8,
        )
        self.history_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.graph_btn = tk.Button(
            secondary_row,
            text="Show Graph",
            command=self.handle_show_graph,
            font=("Segoe UI", 9, "bold"),
            fg="#0F766E",
            bg="#F0FDFA",
            activebackground="#CCFBF1",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=10,
            pady=8,
        )
        self.graph_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.export_btn = tk.Button(
            secondary_row,
            text="Export CSV",
            command=self.handle_export_csv,
            font=("Segoe UI", 9, "bold"),
            fg="#15803D",
            bg="#ECFDF5",
            activebackground="#D1FAE5",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=10,
            pady=8,
        )
        self.export_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.delete_btn = tk.Button(
            secondary_row,
            text="Delete my records",
            command=self.handle_delete_records,
            font=("Segoe UI", 9, "bold"),
            fg="#DC2626",
            bg="#FEF2F2",
            activebackground="#FEE2E2",
            activeforeground="#B91C1C",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=10,
            pady=8,
        )
        self.delete_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.sample_btn = tk.Button(
            secondary_row,
            text="Load Sample",
            command=self.handle_load_sample_data,
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#F1F5F9",
            activebackground="#E2E8F0",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=10,
            pady=8,
        )
        self.sample_btn.pack(side="left", fill="x", expand=True)

        # Interactive Color-Coded Category Explorer
        legend_frame = tk.Frame(
            container,
            bg=CARD_BG,
            highlightbackground="#99F6E4",
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        legend_frame.pack(fill="x")

        tk.Label(
            legend_frame,
            text="Interactive Category Explorer (click any category to preview)",
            font=("Segoe UI", 9, "bold"),
            fg="#334155",
            bg=CARD_BG,
        ).pack(anchor="w", pady=(0, 6))

        legend_row = tk.Frame(legend_frame, bg=CARD_BG)
        legend_row.pack(fill="x")
        for idx, (cat_name, info) in enumerate(CATEGORY_STYLES.items()):
            legend_row.columnconfigure(idx, weight=1)
            btn = tk.Button(
                legend_row,
                text=f"{cat_name}\n{info['range']}",
                command=lambda c=cat_name: self._preview_category(c),
                font=("Segoe UI", 8, "bold"),
                fg=info["color"],
                bg=info["bg"],
                activebackground=info["bg"],
                relief="solid",
                bd=1,
                cursor="hand2",
                pady=5,
            )
            btn.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 4, 0))

        self.root.bind("<Return>", lambda _event: self.handle_calculate())

    def _on_unit_change(self) -> None:
        """Update height label and convert existing numeric value between m and cm."""
        unit = self.height_unit_var.get()
        self.height_label.configure(text=f"Height ({unit})")
        raw = self.height_var.get().strip()
        if not raw:
            return
        try:
            val = float(raw)
            if unit == "cm" and val <= 3.0:
                self.height_var.set(f"{val * 100:.0f}")
            elif unit == "m" and val > 10.0:
                self.height_var.set(f"{val / 100:.2f}")
        except ValueError:
            pass

    def _preview_category(self, category: str) -> None:
        """Interactive preview when clicking a category button in the legend."""
        info = CATEGORY_STYLES[category]
        sample_bmi = info["sample_bmi"]
        self.result_card.configure(bg=info["bg"], highlightbackground=info["color"])
        self.result_title_label.configure(
            text=f"Category Preview: {category}", bg=info["bg"], fg="#334155"
        )
        self.bmi_value_label.configure(text=f"{sample_bmi:.1f}", fg=info["color"], bg=info["bg"])
        self.category_label.configure(
            text=f"Range: {info['range']} kg/m²", fg=info["color"], bg=info["bg"]
        )
        self.guidance_label.configure(text=info["tip"], fg="#334155", bg=info["bg"])

    def _refresh_user_dropdown(self) -> None:
        """Populate the Username combobox with saved users from SQLite."""
        if self.db is None:
            return
        try:
            users = self.db.get_all_usernames()
            self.username_combo["values"] = users
        except DatabaseError:
            pass

    def _update_result_card(
        self, bmi: float, category: str, color: str, bg: str, username: str, guidance: str
    ) -> None:
        """Update the result display with color-coded BMI feedback and target guidance."""
        self.result_card.configure(bg=bg, highlightbackground=color)
        self.result_title_label.configure(
            text=f"Result for {username}", bg=bg, fg="#334155"
        )
        self.bmi_value_label.configure(text=f"{bmi:.2f}", fg=color, bg=bg)
        self.category_label.configure(
            text=f"Category: {category} ({CATEGORY_STYLES[category]['range']})",
            fg=color,
            bg=bg,
        )
        self.guidance_label.configure(text=guidance, fg="#334155", bg=bg)

    def _reset_result_card(self) -> None:
        """Restore the result card to its initial neutral state."""
        self.result_card.configure(bg=CARD_BG, highlightbackground="#CBD5E1")
        self.result_title_label.configure(text="Your BMI Result", bg=CARD_BG, fg="#64748B")
        self.bmi_value_label.configure(text="--", fg="#0F172A", bg=CARD_BG)
        self.category_label.configure(
            text="Enter your details above or click a category below to explore.",
            fg="#475569",
            bg=CARD_BG,
        )
        self.guidance_label.configure(
            text="Healthy weight corridor and target delta will appear here.",
            fg="#64748B",
            bg=CARD_BG,
        )

    def _require_db(self) -> bool:
        """Ensure the database connection is available, or attempt recovery."""
        if self.db is not None:
            return True
        try:
            self.db = BMIDatabase()
            return True
        except DatabaseError as exc:
            messagebox.showerror("Database Error", str(exc))
            return False

    def handle_calculate(self) -> None:
        """Validate input, compute BMI, display result, and persist to SQLite."""
        username, weight, height, error = validate_inputs(
            self.username_var.get(),
            self.weight_var.get(),
            self.height_var.get(),
            self.height_unit_var.get(),
        )
        if error:
            messagebox.showwarning("Invalid Input", error)
            return

        assert username is not None and weight is not None and height is not None
        bmi = round(weight / (height * height), 2)
        category, color, bg = classify_bmi(bmi)
        _, _, guidance = compute_healthy_weight_guidance(weight, height)

        self._update_result_card(bmi, category, color, bg, username, guidance)

        if not self._require_db():
            return

        try:
            assert self.db is not None
            self.db.insert_record(username, weight, height, bmi, category)
            self._refresh_user_dropdown()
        except DatabaseError as exc:
            messagebox.showerror(
                "Database Save Error",
                f"Your BMI was calculated, but could not be saved:\n{exc}",
            )

    def handle_clear(self) -> None:
        """Clear all input fields and reset the result card after confirmation."""
        if not (
            self.username_var.get().strip()
            or self.weight_var.get().strip()
            or self.height_var.get().strip()
        ):
            self._reset_result_card()
            return

        confirmed = messagebox.askyesno(
            "Confirm Clear",
            "Are you sure you want to clear all input fields?",
        )
        if confirmed:
            self.username_var.set("")
            self.weight_var.set("")
            self.height_var.set("")
            self._reset_result_card()
            self.username_combo.focus_set()

    def handle_view_history(self) -> None:
        """Open a window displaying the current user's BMI records in a ttk.Treeview."""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning(
                "Username Required",
                "Please enter a username to view their BMI history.",
            )
            return

        if not self._require_db():
            return

        try:
            assert self.db is not None
            records = self.db.get_user_records(username)
        except DatabaseError as exc:
            messagebox.showerror("Database Read Error", str(exc))
            return

        if not records:
            messagebox.showinfo(
                "No Records Found",
                f"No saved BMI records found for '{username}'.",
            )
            return

        history_win = tk.Toplevel(self.root)
        history_win.title(f"BMI History — {username}")
        history_win.geometry("760x380")
        history_win.minsize(640, 300)
        history_win.configure(bg=CANVAS_BG)

        tk.Label(
            history_win,
            text=f"Saved BMI Records for {username} ({len(records)} entries)",
            font=("Segoe UI", 13, "bold"),
            fg="#0F766E",
            bg=CANVAS_BG,
            padx=16,
            pady=12,
        ).pack(anchor="w")

        table_frame = tk.Frame(history_win, bg=CANVAS_BG, padx=16, pady=4)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "username", "weight", "height", "bmi", "category", "date_time")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        headings = {
            "id": ("ID", 50, "center"),
            "username": ("Username", 110, "w"),
            "weight": ("Weight (kg)", 95, "e"),
            "height": ("Height (m)", 90, "e"),
            "bmi": ("BMI", 80, "e"),
            "category": ("Category", 110, "w"),
            "date_time": ("Date & Time", 160, "w"),
        }

        for col, (title, width, anchor) in headings.items():
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row in records:
            rec_id, rec_user, w, h, b, cat, dt = row
            tree.insert("", "end", values=(rec_id, rec_user, f"{w:.1f}", f"{h:.2f}", f"{b:.2f}", cat, dt))

    def handle_show_graph(self) -> None:
        """Display a colorful matplotlib line chart with shaded BMI zones and category markers."""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning(
                "Username Required",
                "Please enter a username to display their BMI graph.",
            )
            return

        if not self._require_db():
            return

        try:
            assert self.db is not None
            records = self.db.get_user_records(username)
        except DatabaseError as exc:
            messagebox.showerror("Database Read Error", str(exc))
            return

        if not records:
            messagebox.showinfo(
                "No Data to Plot",
                f"No saved BMI records found for '{username}'. Calculate a BMI first.",
            )
            return

        goal_bmi: Optional[float] = None
        try:
            parsed_goal = float(self.goal_bmi_var.get().strip())
            if 10.0 <= parsed_goal <= 50.0:
                goal_bmi = parsed_goal
        except ValueError:
            goal_bmi = None

        dates = [row[6] for row in records]
        bmis = [row[4] for row in records]
        point_colors = [classify_bmi(b)[1] for b in bmis]

        graph_win = tk.Toplevel(self.root)
        graph_win.title(f"BMI Trend Graph — {username}")
        graph_win.geometry("780x500")
        graph_win.minsize(620, 420)
        graph_win.configure(bg="#FFFFFF")

        fig = Figure(figsize=(7.4, 4.6), dpi=100)
        ax = fig.add_subplot(111)

        # Shaded background bands for BMI zones
        y_min = min(14.0, min(bmis) - 3.0)
        y_max = max(36.0, max(bmis) + 3.0)
        ax.axhspan(y_min, 18.5, color="#DBEAFE", alpha=0.35, label="Underweight (<18.5)")
        ax.axhspan(18.5, 25.0, color="#D1FAE5", alpha=0.45, label="Normal (18.5–24.9)")
        ax.axhspan(25.0, 30.0, color="#FFEDD5", alpha=0.40, label="Overweight (25–29.9)")
        ax.axhspan(30.0, y_max, color="#FEE2E2", alpha=0.35, label="Obese (>=30)")

        x_indices = list(range(len(dates)))
        ax.plot(x_indices, bmis, color="#0F766E", linewidth=2.4, zorder=3)
        ax.scatter(
            x_indices,
            bmis,
            c=point_colors,
            s=75,
            edgecolors="#FFFFFF",
            linewidths=1.8,
            zorder=4,
            label="Recorded BMI",
        )

        for x_val, y_val in zip(x_indices, bmis):
            ax.annotate(
                f"{y_val:.2f}",
                (x_val, y_val),
                textcoords="offset points",
                xytext=(0, 9),
                ha="center",
                fontsize=8,
                fontweight="bold",
                color="#0F172A",
            )

        if goal_bmi is not None:
            ax.axhline(
                goal_bmi,
                color="#0F766E",
                linestyle="-.",
                linewidth=1.5,
                label=f"Goal BMI ({goal_bmi:.1f})",
            )

        ax.set_ylim(y_min, y_max)
        ax.set_title(f"BMI Trend Over Time — {username}", fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Date & Time", fontsize=10, labelpad=8)
        ax.set_ylabel("BMI (kg/m²)", fontsize=10, labelpad=8)
        ax.set_xticks(x_indices)
        ax.set_xticklabels(dates, rotation=25, ha="right", fontsize=8)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend(loc="best", fontsize=8, ncol=2)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=graph_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def handle_export_csv(self) -> None:
        """Export the current user's BMI records to a CSV file."""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning(
                "Username Required",
                "Please enter a username to export their BMI history.",
            )
            return

        if not self._require_db():
            return

        try:
            assert self.db is not None
            records = self.db.get_user_records(username)
        except DatabaseError as exc:
            messagebox.showerror("Database Read Error", str(exc))
            return

        if not records:
            messagebox.showinfo(
                "No Records Found",
                f"There are no saved records for '{username}' to export.",
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=f"{username.lower().replace(' ', '_')}_bmi_history.csv",
            title=f"Export BMI History — {username}",
        )
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["ID", "Username", "Weight (kg)", "Height (m)", "BMI", "Category", "Date & Time"])
                writer.writerows(records)
            messagebox.showinfo("Export Successful", f"Exported {len(records)} record(s) to:\n{file_path}")
        except OSError as exc:
            messagebox.showerror("Export Error", f"Could not write CSV file:\n{exc}")

    def handle_delete_records(self) -> None:
        """Delete all saved BMI records for the entered username after confirmation."""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning(
                "Username Required",
                "Please enter a username whose records you want to delete.",
            )
            return

        if not self._require_db():
            return

        try:
            assert self.db is not None
            records = self.db.get_user_records(username)
        except DatabaseError as exc:
            messagebox.showerror("Database Read Error", str(exc))
            return

        if not records:
            messagebox.showinfo(
                "No Records Found",
                f"There are no saved records for '{username}' to delete.",
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to permanently delete all {len(records)} BMI record(s) for '{username}'?",
        )
        if not confirmed:
            return

        try:
            assert self.db is not None
            deleted_count = self.db.delete_user_records(username)
            self._refresh_user_dropdown()
            messagebox.showinfo(
                "Records Deleted",
                f"Successfully deleted {deleted_count} record(s) for '{username}'.",
            )
        except DatabaseError as exc:
            messagebox.showerror("Database Delete Error", str(exc))

    def handle_load_sample_data(self) -> None:
        """Insert sample multi-user dummy records into SQLite on user request."""
        if not self._require_db():
            return
        try:
            assert self.db is not None
            count = self.db.seed_sample_data(force=True)
            self._refresh_user_dropdown()
            if self.username_combo["values"]:
                self.username_var.set(self.username_combo["values"][0])
            messagebox.showinfo(
                "Sample Data Loaded",
                f"Loaded {count} sample BMI records for Ayesha, Rahul, and Priya.",
            )
        except DatabaseError as exc:
            messagebox.showerror("Database Seed Error", str(exc))


def main() -> None:
    """Launch the BMI Calculator tkinter application."""
    root = tk.Tk()
    BMICalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
