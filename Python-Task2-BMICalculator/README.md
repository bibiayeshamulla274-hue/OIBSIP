# BMI Calculator (Advanced Tier) — Oasis Infobyte Internship

A complete **Body Mass Index (BMI) Calculator** built for **Oasis Infobyte Python Programming Internship (Task 2)** in **two standalone versions**, enhanced with an **interactive landing page**, **healthy weight corridor guidance**, **goal BMI tracking**, and **CSV export**:

1. **Python Desktop App (`tkinter` + `sqlite3` + `matplotlib`)** — Native GUI with SQLite persistence (`bmi_data.db`), quick-select user combobox, healthy weight target delta, `ttk.Treeview` history, `matplotlib` trend chart with a customizable Goal BMI line, and one-click CSV export.
2. **Standalone Web App (`HTML` + `CSS` + `Vanilla JS`)** — Opens directly by double-clicking `index.html` in your file explorer (zero server, zero build step). Includes an interactive landing page with a **Live BMI Spectrum Simulator**, `localStorage` multi-user tracking, `Chart.js` Goal-line progression chart, and offline CSV export.

---

## Features

- **Interactive Landing Page & Live BMI Spectrum Simulator (Web)**: Real-time Weight and Height sliders animate a 4-zone BMI spectrum gauge, compute the Normal weight corridor, and pre-fill the tracker on click.
- **Healthy Weight Corridor & Delta (Python & Web)**: Computes the Normal BMI (`18.5 – 24.9`) weight range for the user's height (`18.5 * h²` to `24.9 * h²`) and shows how many kilograms to gain or lose to enter the healthy range.
- **Instant Color-Coded BMI Results**:
  - **Blue**: Underweight (`< 18.5`)
  - **Green**: Normal (`18.5 – 24.9`)
  - **Orange**: Overweight (`25.0 – 29.9`)
  - **Red**: Obese (`>= 30.0`)
- **Strict Input Validation**: Rejects empty fields, non-numeric entries, zero/negative numbers, and unrealistic measurements (Weight: `10–300 kg`, Height: `0.5–2.5 m`).
- **Multi-User Persistence & Quick Switching**:
  - Python: SQLite (`bmi_data.db`) + saved username dropdown (`ttk.Combobox`).
  - Web: Browser `localStorage` + user dropdown filter + session stats strip (Latest BMI, Change Since First, Average BMI).
- **Goal BMI Reference Line & CSV Export**: Plot a personal Goal BMI target line on the trend chart and export any user's history to `.csv`.
- **Safe Error Handling & Confirmation**: `try/except` around every SQLite operation, `try/catch` around every `localStorage` read/write, and `"Are you sure?"` confirmation before deleting records.

---

## Tech Stack

| Component | Python Desktop Version | Standalone Web Version |
| :--- | :--- | :--- |
| **Language** | Python 3 | HTML5, CSS3, Vanilla JavaScript (no modules) |
| **GUI / UI** | `tkinter` & `tkinter.ttk` | Responsive CSS Grid + Interactive Landing Page |
| **Storage** | `sqlite3` (`bmi_data.db`) | Browser `localStorage` |
| **Charting** | `matplotlib` (`FigureCanvasTkAgg`) | `Chart.js` (jsDelivr CDN with offline fallback) |
| **Export** | Python `csv` + `filedialog` | Browser `Blob` CSV download |

---

## How to Run

### 1. Python Desktop Version

1. Open a terminal inside `OIBSIP/Python-Task2-BMICalculator/`.
2. Install the required dependency:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python bmi_calculator.py
   ```

### 2. Standalone Web Version

1. Open your file explorer and navigate to `OIBSIP/Python-Task2-BMICalculator/`.
2. **Double-click `index.html`** to open it directly in any modern browser.
   - No server, no `npm`, no Flask, and no terminal commands required.

---

## BMI Category Reference Table

| BMI Range (kg/m²) | Category | Color Indicator |
| :--- | :--- | :--- |
| `< 18.5` | Underweight | Blue |
| `18.5 – 24.9` | Normal | Green |
| `25.0 – 29.9` | Overweight | Orange |
| `>= 30.0` | Obese | Red |

---

## Screenshots

- **Interactive Landing & Simulator**: Real-time sliders, 4-zone BMI spectrum gauge, and healthy weight corridor preview.
- **Python Desktop GUI**: Main `tkinter` window with user combobox, color-coded result & target guidance, `ttk.Treeview` history modal, and `matplotlib` trend chart with Goal BMI line.
- **Web Tracker Workspace**: Multi-user selector, stats summary strip, `Chart.js` progression chart, CSV export, and saved history table.

---

## Folder Structure

```text
OIBSIP/
└── Python-Task2-BMICalculator/
    ├── bmi_calculator.py   # Main Python tkinter GUI application
    ├── database.py         # SQLite database helper (bmi_data.db)
    ├── requirements.txt    # Python dependencies (matplotlib)
    ├── index.html          # Interactive landing page + standalone web tracker
    ├── style.css           # Responsive stylesheet for landing & tracker
    ├── script.js           # Simulator, validation, localStorage, Chart.js & CSV export
    └── README.md           # Project documentation
```
