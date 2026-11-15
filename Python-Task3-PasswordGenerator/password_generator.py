"""
Random Password Generator (Advanced Tier) - Python tkinter Version
Oasis Infobyte Internship - Task 3

Uses Python's cryptographically secure `secrets` module (never `random`)
and `pyperclip` for clipboard integration. Passwords exist in memory only
for the current session and are never written to disk.
"""

import secrets
import string
import tkinter as tk
from tkinter import messagebox
import pyperclip

# Character pools
UPPERCASE_CHARS = string.ascii_uppercase
LOWERCASE_CHARS = string.ascii_lowercase
NUMBER_CHARS = string.digits
SYMBOL_CHARS = "!@#$%^&*()-_=+[]{};:,.<>?/\\|~"

# Ambiguous characters that look visually similar in many fonts
AMBIGUOUS_CHARS = set("0Oo1lI")

MIN_LENGTH = 8
MAX_LENGTH = 64
DEFAULT_LENGTH = 12
MAX_HISTORY = 5


def evaluate_password_strength(password: str) -> tuple[str, str, int]:
    """
    Evaluate password strength based on length and character diversity.

    Scoring Breakdown (max 7 points):
      1. Length score:
         - 16+ characters : +3 points
         - 12-15 characters: +2 points
         - 8-11 characters : +1 point
      2. Character diversity score (+1 for each category present):
         - Uppercase letter (A-Z)
         - Lowercase letter (a-z)
         - Numeric digit (0-9)
         - Symbol character

    Classification:
      - Weak   : total score <= 3, or length < 10, or fewer than 2 categories
      - Medium : total score 4 or 5
      - Strong : total score >= 6

    Returns:
        tuple[str, str, int]: (label, hex_color, bar_percentage)
    """
    if not password:
        return ("None", "#CBD5E1", 0)

    length = len(password)

    # 1. Score password length
    if length >= 16:
        length_score = 3
    elif length >= 12:
        length_score = 2
    elif length >= 8:
        length_score = 1
    else:
        length_score = 0

    # 2. Score character category diversity
    has_upper = any(ch.isupper() for ch in password)
    has_lower = any(ch.islower() for ch in password)
    has_digit = any(ch.isdigit() for ch in password)
    has_symbol = any(not ch.isalnum() for ch in password)

    diversity_score = sum([has_upper, has_lower, has_digit, has_symbol])
    total_score = length_score + diversity_score

    # 3. Map combined score to Weak / Medium / Strong with colour and fill %
    if length < 10 or diversity_score < 2 or total_score <= 3:
        return ("Weak", "#DC2626", 33)
    if total_score <= 5:
        return ("Medium", "#D97706", 66)
    return ("Strong", "#16A34A", 100)


def build_character_pools(
    use_upper: bool,
    use_lower: bool,
    use_numbers: bool,
    use_symbols: bool,
    exclude_ambiguous: bool,
) -> list[str]:
    """Build non-empty character pools for each selected character category."""
    raw_pools: list[str] = []
    if use_upper:
        raw_pools.append(UPPERCASE_CHARS)
    if use_lower:
        raw_pools.append(LOWERCASE_CHARS)
    if use_numbers:
        raw_pools.append(NUMBER_CHARS)
    if use_symbols:
        raw_pools.append(SYMBOL_CHARS)

    if exclude_ambiguous:
        filtered_pools = [
            "".join(ch for ch in pool if ch not in AMBIGUOUS_CHARS)
            for pool in raw_pools
        ]
        return [pool for pool in filtered_pools if pool]

    return raw_pools


def generate_secure_password(
    length: int,
    use_upper: bool,
    use_lower: bool,
    use_numbers: bool,
    use_symbols: bool,
    exclude_ambiguous: bool,
) -> str:
    """
    Generate a cryptographically secure password using `secrets`.

    Guarantees at least one character from every selected pool, fills the
    remaining slots from the combined pool, and shuffles with
    `secrets.SystemRandom().shuffle()`.
    """
    if not isinstance(length, int) or length < MIN_LENGTH or length > MAX_LENGTH:
        raise ValueError(
            f"Password length must be a whole number between {MIN_LENGTH} and {MAX_LENGTH}."
        )

    selected_count = sum([use_upper, use_lower, use_numbers, use_symbols])
    if selected_count < 2:
        raise ValueError("Please select at least 2 character types.")

    pools = build_character_pools(
        use_upper, use_lower, use_numbers, use_symbols, exclude_ambiguous
    )
    if len(pools) < 2:
        raise ValueError("At least 2 non-empty character pools are required.")

    # Guarantee at least one character from each selected character type
    password_chars = [secrets.choice(pool) for pool in pools]

    # Fill the remaining length from the combined character pool
    combined_pool = "".join(pools)
    remaining = length - len(password_chars)
    for _ in range(remaining):
        password_chars.append(secrets.choice(combined_pool))

    # Cryptographically secure shuffle
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


class PasswordGeneratorApp:
    """tkinter GUI for the Random Password Generator."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Random Password Generator")
        self.root.geometry("540x680")
        self.root.minsize(480, 640)
        self.root.configure(bg="#F8FAFC")

        # In-memory session history only (never written to disk)
        self.session_history: list[str] = []
        self.is_password_visible = True

        # Tk state variables
        self.length_var = tk.StringVar(value=str(DEFAULT_LENGTH))
        self.slider_var = tk.IntVar(value=DEFAULT_LENGTH)
        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.numbers_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.exclude_ambiguous_var = tk.BooleanVar(value=False)
        self.password_var = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg="#F8FAFC", padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # Header
        tk.Label(
            container,
            text="Random Password Generator",
            font=("Segoe UI", 18, "bold"),
            fg="#0F172A",
            bg="#F8FAFC",
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            container,
            text="Cryptographically secure generation using Python secrets. Passwords stay in memory only.",
            font=("Segoe UI", 9),
            fg="#475569",
            bg="#F8FAFC",
            anchor="w",
        ).pack(fill="x", pady=(2, 16))

        # Main configuration card
        card = tk.Frame(
            container,
            bg="#FFFFFF",
            highlightbackground="#E2E8F0",
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        card.pack(fill="x")

        # Length row (Slider + Spinbox)
        length_header = tk.Frame(card, bg="#FFFFFF")
        length_header.pack(fill="x", pady=(0, 6))

        tk.Label(
            length_header,
            text="Password Length (8–64)",
            font=("Segoe UI", 10, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        ).pack(side="left")

        self.length_spinbox = tk.Spinbox(
            length_header,
            from_=MIN_LENGTH,
            to=MAX_LENGTH,
            textvariable=self.length_var,
            width=5,
            font=("Consolas", 11, "bold"),
            justify="center",
            command=self._on_spinbox_change,
            relief="solid",
            bd=1,
        )
        self.length_spinbox.pack(side="right")
        self.length_spinbox.bind("<KeyRelease>", lambda _e: self._on_spinbox_typing())

        self.length_slider = tk.Scale(
            card,
            from_=MIN_LENGTH,
            to=MAX_LENGTH,
            orient="horizontal",
            variable=self.slider_var,
            command=self._on_slider_move,
            showvalue=False,
            bg="#FFFFFF",
            troughcolor="#E2E8F0",
            activebackground="#1D4ED8",
            highlightthickness=0,
        )
        self.length_slider.pack(fill="x", pady=(0, 14))

        # Character types
        tk.Label(
            card,
            text="Character Types (select at least 2)",
            font=("Segoe UI", 10, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        checks_grid = tk.Frame(card, bg="#FFFFFF")
        checks_grid.pack(fill="x", pady=(0, 10))
        checks_grid.columnconfigure(0, weight=1)
        checks_grid.columnconfigure(1, weight=1)

        options = [
            ("Uppercase (A–Z)", self.upper_var, 0, 0),
            ("Lowercase (a–z)", self.lower_var, 0, 1),
            ("Numbers (0–9)", self.numbers_var, 1, 0),
            ("Symbols (!@#$...)", self.symbols_var, 1, 1),
        ]
        for label, var, row, col in options:
            tk.Checkbutton(
                checks_grid,
                text=label,
                variable=var,
                font=("Segoe UI", 10),
                fg="#1E293B",
                bg="#FFFFFF",
                activebackground="#FFFFFF",
                anchor="w",
                selectcolor="#FFFFFF",
            ).grid(row=row, column=col, sticky="w", pady=3)

        # Exclude ambiguous checkbox
        tk.Checkbutton(
            card,
            text="Exclude ambiguous characters (0, O, o, l, 1, I)",
            variable=self.exclude_ambiguous_var,
            font=("Segoe UI", 9),
            fg="#334155",
            bg="#FFFFFF",
            activebackground="#FFFFFF",
            anchor="w",
            selectcolor="#FFFFFF",
        ).pack(fill="x", pady=(4, 14))

        # Primary & secondary action buttons
        btn_row = tk.Frame(card, bg="#FFFFFF")
        btn_row.pack(fill="x")

        self.generate_btn = tk.Button(
            btn_row,
            text="Generate Password",
            command=self.handle_generate,
            font=("Segoe UI", 10, "bold"),
            bg="#0F172A",
            fg="#FFFFFF",
            activebackground="#1E293B",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=16,
            pady=9,
            cursor="hand2",
        )
        self.generate_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.copy_btn = tk.Button(
            btn_row,
            text="Copy",
            command=self.handle_copy_current,
            font=("Segoe UI", 10, "bold"),
            bg="#F1F5F9",
            fg="#0F172A",
            activebackground="#E2E8F0",
            relief="flat",
            padx=16,
            pady=9,
            cursor="hand2",
        )
        self.copy_btn.pack(side="right")

        # Output field + Show/Hide toggle
        output_frame = tk.Frame(card, bg="#FFFFFF")
        output_frame.pack(fill="x", pady=(14, 6))

        self.password_entry = tk.Entry(
            output_frame,
            textvariable=self.password_var,
            font=("Consolas", 12, "bold"),
            state="readonly",
            readonlybackground="#F8FAFC",
            fg="#0F172A",
            relief="solid",
            bd=1,
        )
        self.password_entry.pack(side="left", fill="x", expand=True, ipady=6)

        self.toggle_btn = tk.Button(
            output_frame,
            text="Hide",
            command=self.toggle_visibility,
            font=("Segoe UI", 9, "bold"),
            bg="#F1F5F9",
            fg="#334155",
            activebackground="#E2E8F0",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
        )
        self.toggle_btn.pack(side="right", padx=(8, 0))

        # Status / error feedback label
        self.status_label = tk.Label(
            card,
            text="Click Generate Password to create a secure password.",
            font=("Segoe UI", 9),
            fg="#64748B",
            bg="#FFFFFF",
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(2, 10))

        # Strength meter
        strength_header = tk.Frame(card, bg="#FFFFFF")
        strength_header.pack(fill="x")

        tk.Label(
            strength_header,
            text="Strength:",
            font=("Segoe UI", 9, "bold"),
            fg="#334155",
            bg="#FFFFFF",
        ).pack(side="left")

        self.strength_text_label = tk.Label(
            strength_header,
            text="—",
            font=("Segoe UI", 9, "bold"),
            fg="#64748B",
            bg="#FFFFFF",
        )
        self.strength_text_label.pack(side="left", padx=(6, 0))

        self.strength_canvas = tk.Canvas(
            card,
            height=8,
            bg="#E2E8F0",
            highlightthickness=0,
        )
        self.strength_canvas.pack(fill="x", pady=(6, 0))
        self.strength_canvas.bind("<Configure>", lambda _e: self._redraw_strength_bar())
        self._current_strength = ("None", "#CBD5E1", 0)

        # Session history card
        history_card = tk.Frame(
            container,
            bg="#FFFFFF",
            highlightbackground="#E2E8F0",
            highlightthickness=1,
            padx=18,
            pady=14,
        )
        history_card.pack(fill="both", expand=True, pady=(14, 0))

        history_top = tk.Frame(history_card, bg="#FFFFFF")
        history_top.pack(fill="x", pady=(0, 6))

        tk.Label(
            history_top,
            text="Recent Passwords (Last 5 · Session Only)",
            font=("Segoe UI", 10, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        ).pack(side="left")

        tk.Label(
            history_top,
            text="Double-click to copy",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="#FFFFFF",
        ).pack(side="right")

        self.history_listbox = tk.Listbox(
            history_card,
            height=5,
            font=("Consolas", 10),
            bg="#F8FAFC",
            fg="#0F172A",
            selectbackground="#DBEAFE",
            selectforeground="#0F172A",
            relief="solid",
            bd=1,
            activestyle="none",
        )
        self.history_listbox.pack(fill="both", expand=True)
        self.history_listbox.bind("<Double-Button-1>", self._on_history_double_click)

    def _on_slider_move(self, value: str) -> None:
        self.length_var.set(str(int(float(value))))

    def _on_spinbox_change(self) -> None:
        try:
            val = int(self.length_var.get())
            if MIN_LENGTH <= val <= MAX_LENGTH:
                self.slider_var.set(val)
        except ValueError:
            pass

    def _on_spinbox_typing(self) -> None:
        try:
            val = int(self.length_var.get())
            if MIN_LENGTH <= val <= MAX_LENGTH:
                self.slider_var.set(val)
        except ValueError:
            pass

    def _parse_and_validate_length(self) -> int:
        raw = self.length_var.get().strip()
        try:
            length = int(raw)
        except ValueError:
            raise ValueError(
                f"Invalid length '{raw}'. Enter a whole number from {MIN_LENGTH} to {MAX_LENGTH}."
            )

        if length < MIN_LENGTH:
            raise ValueError(
                f"Password length must be at least {MIN_LENGTH} characters."
            )
        if length > MAX_LENGTH:
            raise ValueError(
                f"Password length cannot exceed {MAX_LENGTH} characters."
            )

        self.slider_var.set(length)
        return length

    def _set_status(self, message: str, color: str) -> None:
        self.status_label.config(text=message, fg=color)

    def _copy_to_clipboard(self, text: str) -> bool:
        try:
            pyperclip.copy(text)
            return True
        except Exception as exc:
            self._set_status(
                "Generated password, but clipboard copy failed.", "#D97706"
            )
            messagebox.showwarning(
                "Clipboard Error",
                f"Could not copy password to clipboard automatically.\n\nDetails: {exc}",
            )
            return False

    def _redraw_strength_bar(self) -> None:
        label, color, pct = self._current_strength
        width = self.strength_canvas.winfo_width()
        height = self.strength_canvas.winfo_height()
        self.strength_canvas.delete("all")
        if pct > 0 and width > 1:
            fill_width = max(4, int((pct / 100.0) * width))
            self.strength_canvas.create_rectangle(
                0, 0, fill_width, height, fill=color, outline=""
            )
        if label == "None":
            self.strength_text_label.config(text="—", fg="#64748B")
        else:
            self.strength_text_label.config(text=label, fg=color)

    def _update_history(self, password: str) -> None:
        self.session_history.insert(0, password)
        if len(self.session_history) > MAX_HISTORY:
            self.session_history = self.session_history[:MAX_HISTORY]

        self.history_listbox.delete(0, tk.END)
        for idx, item in enumerate(self.session_history, start=1):
            self.history_listbox.insert(tk.END, f"{idx}.  {item}")

    def toggle_visibility(self) -> None:
        self.is_password_visible = not self.is_password_visible
        if self.is_password_visible:
            self.password_entry.config(show="")
            self.toggle_btn.config(text="Hide")
        else:
            self.password_entry.config(show="*")
            self.toggle_btn.config(text="Show")

    def handle_generate(self) -> None:
        try:
            length = self._parse_and_validate_length()
            password = generate_secure_password(
                length=length,
                use_upper=self.upper_var.get(),
                use_lower=self.lower_var.get(),
                use_numbers=self.numbers_var.get(),
                use_symbols=self.symbols_var.get(),
                exclude_ambiguous=self.exclude_ambiguous_var.get(),
            )
        except ValueError as err:
            self._set_status(str(err), "#DC2626")
            messagebox.showerror("Validation Error", str(err))
            return

        self.password_var.set(password)
        self._current_strength = evaluate_password_strength(password)
        self._redraw_strength_bar()
        self._update_history(password)

        if self._copy_to_clipboard(password):
            self._set_status("Copied to clipboard!", "#16A34A")

    def handle_copy_current(self) -> None:
        password = self.password_var.get()
        if not password:
            msg = "Generate a password first before copying."
            self._set_status(msg, "#DC2626")
            messagebox.showerror("Nothing to Copy", msg)
            return

        if self._copy_to_clipboard(password):
            self._set_status("Copied to clipboard!", "#16A34A")

    def _on_history_double_click(self, _event: tk.Event) -> None:
        selection = self.history_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if 0 <= index < len(self.session_history):
            chosen = self.session_history[index]
            if self._copy_to_clipboard(chosen):
                self._set_status("Copied selected history password to clipboard!", "#16A34A")


if __name__ == "__main__":
    main_window = tk.Tk()
    app = PasswordGeneratorApp(main_window)
    main_window.mainloop()
