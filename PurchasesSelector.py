import tkinter as tk
from tkinter import ttk, messagebox
import datetime

from PurchaseEntry import PurchasesClass
from PurchaseSummary import PurchasesDashboard


class POSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Purchases Control Panel")

        self.WIDTH = 420
        self.HEIGHT = 620

        self.center_window()
        self.setup_styles()
        self.create_dashboard()

    # ---------------- WINDOW ---------------- #

    def center_window(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw // 2) - (self.WIDTH // 2)
        y = (sh // 2) - (self.HEIGHT // 2)
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        self.root.resizable(False, False)

    # ---------------- STYLES ---------------- #

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Banking/Finance color scheme (Light Mode)
        self.bg = "#f5f7fa"  # Light grayish-blue background
        self.card = "#ffffff"  # White cards
        self.primary = "#1e3a8a"  # Deep blue (traditional banking color)
        self.primary_hover = "#1e40af"  # Slightly darker blue on hover
        self.text = "#1f2937"  # Dark gray/black for text
        self.muted = "#6b7280"  # Medium gray for secondary text
        self.accent = "#059669"  # Emerald green for finance (money color)
        self.danger = "#dc2626"  # Red for close/danger actions
        self.border = "#d1d5db"  # Light gray for borders

        self.root.configure(bg=self.bg)

        self.style.configure(
            "Title.TLabel",
            background=self.bg,
            foreground=self.primary,
            font=("Segoe UI", 22, "bold"),
        )

        self.style.configure(
            "Info.TLabel",
            background=self.bg,
            foreground=self.muted,
            font=("Segoe UI", 12),
        )

        self.style.configure(
            "Main.TButton",
            background=self.primary,
            foreground="white",
            font=("Segoe UI", 14, "bold"),
            padding=18,
            borderwidth=0,
            focuscolor="none",
        )

        self.style.map(
            "Main.TButton",
            background=[("active", self.primary_hover)],
            foreground=[("active", "white")],
        )

        self.style.configure(
            "Close.TButton",
            background=self.danger,
            foreground="white",
            font=("Segoe UI", 11, "bold"),
            padding=10,
            borderwidth=0,
        )

        self.style.map(
            "Close.TButton",
            background=[("active", "#b91c1c")],  # Darker red on hover
            foreground=[("active", "white")],
        )

        # Configure frame style
        self.style.configure(
            "Card.TFrame",
            background=self.card,
            relief="solid",
            borderwidth=1,
        )

    # ---------------- UI ---------------- #

    def create_dashboard(self):
        self.frame = tk.Frame(self.root, bg=self.bg)
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        ttk.Label(
            self.frame,
            text="Purchases Dashboard",
            style="Title.TLabel",
        ).pack(pady=(30, 10))

        self.datetime_label = ttk.Label(
            self.frame, style="Info.TLabel"
        )
        self.datetime_label.pack(pady=(0, 40))

        self.update_datetime()

        # Main action buttons
        ttk.Button(
            self.frame,
            text="1. Bill Entry",
            style="Main.TButton",
            command=self.open_purchases,
        ).pack(fill="x", pady=12)

        ttk.Button(
            self.frame,
            text="2. Bill Summary",
            style="Main.TButton",
            command=self.open_summary,
        ).pack(fill="x", pady=12)

        # Separator
        separator = ttk.Separator(self.frame, orient='horizontal')
        separator.pack(fill='x', pady=30)

        # Close button
        ttk.Button(
            self.frame,
            text="Close Application",
            style="Close.TButton",
            command=self.close_app,
        ).pack(side="bottom", fill="x", pady=20)

    # ---------------- ACTIONS ---------------- #

    def open_purchases(self):
        """Open Supplier.py without hiding dashboard"""
        win = tk.Toplevel(self.root)
        PurchasesClass(win)

    def open_summary(self):
        """Open Sale1.py without hiding dashboard"""
        win = tk.Toplevel(self.root)
        PurchasesDashboard(win)

    def update_datetime(self):
        now = datetime.datetime.now()
        self.datetime_label.config(
            text=now.strftime("%A, %d %B %Y\n%I:%M:%S %p")
        )
        self.root.after(1000, self.update_datetime)

    def close_app(self):
        if messagebox.askyesno("Exit", "Close application?"):
            self.root.destroy()


def main():
    root = tk.Tk()
    POSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()