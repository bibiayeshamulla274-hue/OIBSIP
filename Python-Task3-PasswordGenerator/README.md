# Random Password Generator (Advanced Tier)

**Oasis Infobyte Internship — Python Programming Task 3**

A dual-implementation **Random Password Generator** built in both **Python (`tkinter`)** and **Web (`HTML / CSS / Vanilla JS`)**. Both versions use cryptographically secure random number generation, guarantee character-type diversity, evaluate password strength in real time, copy passwords automatically to the clipboard, and keep a temporary in-memory history of the last 5 passwords.

---

## Features

- **Interactive Landing Page & Dual Modes (Web)**: Switch seamlessly between **Random Password** (8–64 chars) and **Memorable Passphrase** (3–8 diceware-style words with customizable separators, capitalization, and trailing digit).
- **Quick Presets & Custom Character Exclusions**: Apply one-click presets (`Standard`, `Vault`, `No Ambiguous`, `Max Key`), exclude ambiguous characters (`0, O, o, l, 1, I`), or exclude custom characters.
- **Color-Coded Character Anatomy**: Inspect generated passwords character-by-character with distinct color tokens for Uppercase, Lowercase, Numbers, and Symbols.
- **Live Entropy & Crack-Time Estimator + Strength Lab**: Calculates bit entropy and offline brute-force resistance, plus an interactive Strength Lab to audit any password in volatile memory.
- **Customizable Length (8–64 characters)**: Enforces a minimum of 8 characters (default 12) via synchronized slider and numeric/spinbox controls.
- **Character Type Rules**: Independently toggle Uppercase (`A–Z`), Lowercase (`a–z`), Numbers (`0–9`), and Symbols (`!@#$...`). Enforces selecting at least 2 character types.
- **Guaranteed Inclusion & Secure Shuffling**: Guarantees at least one character from every selected category, fills remaining slots from the combined pool, and shuffles securely (`secrets.SystemRandom()` in Python, Fisher-Yates with `crypto.getRandomValues()` in JS).
- **Live Strength Indicator**: Classifies generated passwords as **Weak**, **Medium**, or **Strong** with a color-coded progress bar based on length and character diversity.
- **Clipboard Integration**: Automatically copies newly generated passwords to the clipboard (`pyperclip` in Python with `try/except`; `navigator.clipboard.writeText` with `document.execCommand('copy')` fallback in Web) plus a manual Copy button.
- **Show / Hide Toggle**: Mask or reveal the generated password on demand.
- **Session-Only History (Last 5)**: Displays the 5 most recently generated passwords for the current session only.

---

## Tech Stack

- **Python Version**: Python 3, `tkinter`, `secrets`, `string`, `pyperclip`
- **Web Version**: Semantic HTML5, Modern CSS3 (Grid/Flexbox), Vanilla JavaScript (ES5/ES6, `window.crypto.getRandomValues()`)

---

## How to Run Each Version

### 1. Python Desktop Version (`tkinter`)

1. Navigate to the project folder:
   ```bash
   cd OIBSIP/Python-Task3-PasswordGenerator
   ```
2. Install the required dependency (`pyperclip`):
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python password_generator.py
   ```
   *(On Linux/macOS, use `python3 password_generator.py` and ensure your Python installation includes `tkinter`, e.g. `sudo apt install python3-tk` on Debian/Ubuntu.)*

### 2. Web Version (Zero Build / Zero Server)

1. Open `OIBSIP/Python-Task3-PasswordGenerator/` in your file explorer.
2. **Double-click `index.html`** to open it directly in any modern browser (`Chrome`, `Edge`, `Firefox`, `Safari`).
3. No terminal, server, `npm`, or build step is required.

---

## Why `secrets` / `crypto.getRandomValues()` Is Better Than `random` / `Math.random()`

Standard pseudo-random number generators (Python's `random` and JavaScript's `Math.random()`) are designed for speed and simulations, **not** security. Their internal state can be predicted or reconstructed by an attacker after observing a small sequence of outputs.

- **Python `secrets` module**: Uses the operating system's cryptographically secure source of randomness (`os.urandom()`), making generated passwords unpredictable.
- **Browser `crypto.getRandomValues()`**: Uses the browser's CSPRNG backed by OS entropy, combined with rejection sampling in `script.js` to prevent modulo bias.

---

## Security Note (In-Memory Only)

Generated passwords are **never** written to disk, logs, databases, cookies, `localStorage`, or `sessionStorage`. Both the current password and the last-5 password history live strictly in volatile memory (a Python `list` in `password_generator.py` and a local JavaScript array inside an IIFE in `script.js`) and are wiped immediately when you close the window or refresh the page.

---

## Screenshots

> Add screenshots of your local runs here before submitting your internship repository:

- `screenshots/python-gui.png` — Python `tkinter` desktop window showing length controls, strength bar, and session Listbox.
- `screenshots/web-desktop.png` — Standalone `index.html` opened in browser on desktop.
- `screenshots/web-mobile.png` — Responsive mobile view of `index.html`.

---

## Folder Structure

```text
OIBSIP/
└── Python-Task3-PasswordGenerator/
    ├── password_generator.py   # Python tkinter CSPRNG password generator
    ├── requirements.txt        # Python dependencies (pyperclip)
    ├── index.html              # Standalone web UI (double-click to open)
    ├── style.css               # Responsive clean stylesheet
    ├── script.js               # Vanilla JS using crypto.getRandomValues()
    └── README.md               # Project documentation
```
