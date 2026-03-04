from datetime import datetime
import tkinter
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from SaleSummary import SalesClass
from Tracker import TrackerClass
from MyFirm import MyFirmDetails
from PurchaseSummary import PurchasesDashboard
from InvoiceNew import Invoice_Class
from B2BSales import B2BClientClass  # Added import for B2B Sales
import sqlite3
from tkinter import messagebox
import time
import os
import datetime
import json
import hashlib
import os.path

class IMS:
    def __init__(self, root):
        self.root = root
        self.app_running = True
        
        # Set initial size, minimum constraints for responsiveness, and center
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Make the window responsive but prevent it from getting too small and breaking layout
        self.root.minsize(900, 600)
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.root.title("POS System | Developed by Dukes Tech Services")
        
        # Define color scheme early - Updated with lighter background for black text
        self.colors = {
            'primary': '#f8f9fa',  # Light background for better contrast
            'secondary': '#e9ecef',
            'accent': '#0f4c75',
            'highlight': '#3282b8',
            'success': '#00b894',
            'warning': '#fdcb6e',
            'danger': '#d63031',
            'light': '#6c757d',
            'dark': '#343a40',
            'white': '#ffffff',
            'card_bg': '#ffffff',
            'sidebar': '#2c3e50',
            'text_dark': '#212529',  # Dark text for better readability
            'text_light': '#f8f9fa'  , # Light text for dark backgrounds
            'black':"#000000"
        }
        
        self.root.config(bg=self.colors['primary'])
        
        # Initialize main window directly (removed login functionality)
        self.current_user = "Administrator"
        self.is_guest = False
        self.init_main_window()
    
    def on_app_close(self):
        self.app_running = False
        self.root.destroy()

    def center_window(self, window, width, height):
        """Center any window on screen"""
        x = (self.screen_width // 2) - (width // 2)
        y = (self.screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def init_main_window(self):
        """Initialize the main window"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Show the window
        self.root.deiconify()
        
        # Configure styles
        self.configure_styles()
        
        # Title bar frame (modern header)
        title_frame = Frame(self.root, bg=self.colors['sidebar'], height=80)
        title_frame.pack(side=TOP, fill=X, padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        # Left: Logo and Title
        title_left = Frame(title_frame, bg=self.colors['sidebar'])
        title_left.pack(side=LEFT, fill=Y, padx=20)
        
        # Title label
        title = Label(
            title_left,
            text="POS System",
            font=("Segoe UI", 24, "bold"),
            bg=self.colors['sidebar'],
            fg=self.colors['white'],  # Light text on dark sidebar
            anchor="w"
        )
        title.pack(side=LEFT)
        
        # Subtitle
        subtitle = Label(
            title_left,
            text="Professional Point of Sale",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['sidebar'],
            fg=self.colors['white'],
            anchor="w"
        )
        subtitle.pack(side=LEFT, padx=(10, 0))
        
        # Center: Clock (Expands to push right content to the edge)
        self.lbl_clock = Label(
            title_frame,
            text="",
            font=("Segoe UI", 11,"bold"),
            bg=self.colors['sidebar'],
            fg=self.colors['white']  # Light text on dark sidebar
        )
        self.lbl_clock.pack(side=LEFT, expand=True)
        
        # Right: User info and logout
        title_right = Frame(title_frame, bg=self.colors['sidebar'])
        title_right.pack(side=RIGHT, fill=Y, padx=20)
        
        user_type = "Administrator"
        self.user_label = Label(
            title_right,
            text=f"👤 {self.current_user}",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['sidebar'],
            fg=self.colors['white']  # Light text on dark sidebar
        )
        self.user_label.pack(side=LEFT, padx=(0, 20))
        
        logout_btn = Button(
            title_right,
            text="🚪 Exit",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['danger'],
            fg=self.colors['white'],
            cursor="hand2",
            command=self.on_app_close,
            bd=0,
            padx=15,
            pady=5,
            relief=FLAT
        )
        logout_btn.pack(side=LEFT)
        
        # Main container
        main_container = Frame(self.root, bg=self.colors['primary'])
        main_container.pack(fill=BOTH, expand=True)
        
        # Sidebar
        sidebar = Frame(main_container, bg=self.colors['sidebar'], width=220)
        sidebar.pack(side=LEFT, fill=Y, padx=0, pady=0)
        sidebar.pack_propagate(False)
        
        # Sidebar content
        sidebar_header = Frame(sidebar, bg=self.colors['accent'], height=100)
        sidebar_header.pack(fill=X, pady=(0, 20))
        sidebar_header.pack_propagate(False)
        
        Label(
            sidebar_header,
            text="HOME",
            font=("Segoe UI", 26, "bold"),
            bg=self.colors['accent'],
            fg=self.colors['white']
        ).pack(expand=True)
        
        # Navigation buttons
        nav_frame = Frame(sidebar, bg=self.colors['sidebar'])
        nav_frame.pack(fill=BOTH, expand=True, padx=15, pady=10)
        
        # Navigation buttons with B2B Sales added after Clients
        nav_items = [
            ("🏢 MY FIRM", self.MyFirm),
            ("👥 CLIENTS", self.Clients),
            ("🏢 B2B SALES", self.B2BSales),  # Added B2B Sales button
            ("📦 SUPPLIERS", self.Suppliers),
            ("📊 TRACKER", self.Tracker),
            ("🚪 EXIT", self.on_app_close)
        ]
        
        for text, command in nav_items:
            btn = Button(
                nav_frame,
                text=text,
                font=("Segoe UI", 12, "bold"),
                bg=self.colors['card_bg'],
                fg=self.colors['text_dark'],  # Dark text on light cards
                command=command,
                bd=0,
                anchor="w",
                padx=20,
                pady=12,
                cursor="hand2",
                relief=FLAT
            )
            btn.pack(fill=X, pady=5)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colors['highlight'], fg=self.colors['white']))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.colors['card_bg'], fg=self.colors['text_dark']))
        
        # Dashboard area with Scrollbar for smaller screens
        dashboard_container = Frame(main_container, bg=self.colors['primary'])
        dashboard_container.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Create a Canvas for scrolling
        canvas = Canvas(dashboard_container, bg=self.colors['primary'], highlightthickness=0)
        scrollbar = Scrollbar(dashboard_container, orient="vertical", command=canvas.yview)
        
        # Dashboard frame inside canvas
        dashboard = Frame(canvas, bg=self.colors['primary'])
        
        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=20, pady=20)
        
        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=dashboard, anchor="nw")
        
        # Function to configure scrolling and responsiveness
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Update the canvas window width dynamically to keep components expanding
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        dashboard.bind("<Configure>", configure_scroll)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # ========== NEW DASHBOARD CONTENT ==========
        
        # Main dashboard content container
        content_frame = Frame(dashboard, bg=self.colors['primary'])
        content_frame.pack(fill=BOTH, expand=True)

        # Company info card (white)
        company_card = Frame(
            content_frame,
            bg='#ffffff',
            relief=FLAT,
            bd=1,
            highlightbackground='#b0c4de',  # light steel blue
            highlightthickness=1
        )
        company_card.pack(fill=BOTH, expand=True)

        # Padding inside card - reduced to 20 for compactness
        inner_frame = Frame(company_card, bg='#ffffff', padx=20, pady=20)
        inner_frame.pack(fill=BOTH, expand=True)

        # Compact Title Section (Removed extra space)
        title_group = Frame(inner_frame, bg='#ffffff')
        title_group.pack(fill=X, pady=0)
        
        Label(
            title_group,
            text="POS SYSTEM",
            font=("Segoe UI", 28, "bold"),
            bg='#ffffff',
            fg='#000000'
        ).pack(pady=0)
        
        Label(
            title_group,
            text="Produced By Dukes Tech Services",
            font=("Segoe UI", 16, "bold"),
            bg='#ffffff',
            fg='#000000'
        ).pack(pady=0)
        
        # Horizontal line
        Frame(inner_frame, bg='#000000', height=2).pack(fill=X, pady=(10, 5))

        # Compact Contact section
        contact_line = Frame(inner_frame, bg='#ffffff')
        contact_line.pack(pady=0)

        # Website
        lbl_web = Label(
            contact_line,
            text="🌐 dukestechservices.com",
            font=("Segoe UI", 11),
            bg='#ffffff',
            fg='#000000',
            cursor="hand2"
        )
        lbl_web.pack(side=LEFT, padx=(0, 10))
        lbl_web.bind("<Button-1>", lambda e: self.open_website("https://dukestechservices.com"))

        # Separator
        Label(contact_line, text="|", font=("Segoe UI", 11, "bold"), bg='#ffffff', fg='#212529').pack(side=LEFT, padx=5)

        # Phone
        lbl_phone = Label(contact_line, text="📞 +92 309 7671363", font=("Segoe UI", 11), bg='#ffffff', fg='#212529')
        lbl_phone.pack(side=LEFT, padx=10)

        # Separator
        Label(contact_line, text="|", font=("Segoe UI", 11, "bold"), bg='#ffffff', fg='#212529').pack(side=LEFT, padx=5)

        # Email
        lbl_email = Label(
            contact_line,
            text="📧 info@dukestechservices.com",
            font=("Segoe UI", 11),
            bg='#ffffff',
            fg='#000000',
            cursor="hand2"
        )
        lbl_email.pack(side=LEFT, padx=(10, 0))
        lbl_email.bind("<Button-1>", lambda e: self.open_website("mailto:info@dukestechservices.com"))

        # Divider
        Frame(inner_frame, bg='#000000', height=1).pack(fill=X, pady=(5, 10))

        # Company description text (scrollable and expansive)
        description_text = """Dukes Tech Services is a leading provider of innovative business solutions specializing in Point of Sale systems. Our mission is to empower businesses with reliable, efficient, and user-friendly software that drives growth and enhances operational excellence.

Our POS System offers:
• Comprehensive inventory management
• Real-time sales tracking and analytics
• Employee performance monitoring
• Customer relationship management
• Secure data handling and backup
• 24/7 technical support and maintenance

With years of experience in software development and business consulting, we deliver solutions that are tailored to your specific needs, ensuring seamless integration with your existing workflows.

Choose Dukes Tech Services for:
✓ Professional implementation
✓ Ongoing support and updates
✓ Scalable solutions that grow with your business
✓ Training and documentation
✓ Competitive pricing with no hidden costs

Transform your business operations today with our cutting-edge POS solution!"""

        text_frame = Frame(inner_frame, bg='#ffffff')
        text_frame.pack(fill=BOTH, expand=True)

        scrollbar_desc = Scrollbar(text_frame)
        scrollbar_desc.pack(side=RIGHT, fill=Y)

        description_label = Text(
            text_frame,
            font=("Segoe UI", 11),
            bg='#ffffff',
            fg='#212529',
            wrap=WORD,
            yscrollcommand=scrollbar_desc.set,
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=5
        )
        description_label.pack(side=LEFT, fill=BOTH, expand=True)
        description_label.insert(END, description_text)
        description_label.config(state=DISABLED)

        scrollbar_desc.config(command=description_label.yview)

        # Compact SYSTEM NOTICE moved below the description
        notice_frame = Frame(inner_frame, bg='#fff3cd', bd=1, relief=SOLID, highlightbackground='#ffeeba')
        notice_frame.pack(fill=X, pady=(15, 0))

        Label(notice_frame, text="📢", font=("Segoe UI", 16), bg='#fff3cd', fg='#856404').pack(side=LEFT, padx=(10,5), pady=5)

        notice_text = "System Notice / Reporting Guidelines: To ensure accurate financial reporting and system consistency, all users are required to strictly follow the defined color scheme and reporting structure within the POS system."
        Label(notice_frame, text=notice_text, font=("Segoe UI", 10), bg='#fff3cd', fg='#856404', justify=LEFT, wraplength=1000).pack(side=LEFT, padx=(0,10), pady=10, fill=X, expand=True)

        # Add some space at bottom
        Frame(dashboard, bg=self.colors['primary'], height=20).pack(fill=X)
        # ========== END OF NEW DASHBOARD CONTENT ==========
        
        # Footer
        footer = Frame(self.root, bg=self.colors['accent'], height=40)
        footer.pack(side=BOTTOM, fill=X, padx=0, pady=0)
        footer.pack_propagate(False)
        
        footer_text = "© 2025 POS System | Developed by Dukes Tech Services | +92 309 7671363 | dukestechservices.com"
        
        Label(
            footer,
            text=footer_text,
            font=("Segoe UI", 10),
            bg=self.colors['accent'],
            fg=self.colors['white']
        ).pack(expand=True)
        
        self.update_content()
    
    def get_feature_command(self, feature_title):
        """Get command for feature click (kept for compatibility but not used in new dashboard)"""
        feature_commands = {
            "🏢 MY FIRM": self.MyFirm,
            "👥 CLIENTS": self.Clients,
            "🏢 B2B SALES": self.B2BSales,
            "📦 SUPPLIERS": self.Suppliers,
            "📊 TRACKER": self.Tracker,
            "💰 INVOICES": self.Invoices
        }
        return feature_commands.get(feature_title, lambda: None)

    def configure_styles(self):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        
        # Configure button styles
        style.configure(
            'Primary.TButton',
            font=('Segoe UI', 11),
            padding=10,
            relief='flat'
        )
        
        style.configure(
            'Success.TButton',
            font=('Segoe UI', 11),
            padding=10,
            relief='flat'
        )
        
        # Configure entry styles
        style.configure(
            'Modern.TEntry',
            fieldbackground=self.colors['card_bg'],
            foreground=self.colors['text_dark'],
            padding=10,
            relief='flat'
        )

    def open_website(self, url):
        """Open website in browser"""
        import webbrowser
        webbrowser.open(url)

    def Invoices(self):
        """Open Invoice Management"""
        self.new_win = Toplevel(self.root)
        self.new_obj = Invoice_Class(self.new_win)

    # Renamed window openers
    def MyFirm(self):
        """Open MyFirm Management"""
        # Create a new Toplevel window
        self.new_win = Toplevel(self.root)
    
        # Set the geometry and title for the Toplevel window
        self.new_win.title("My POS System - Firm Details")
        self.new_win.geometry("1000x800")
    
        # Create an instance of MyFirmDetails with the Toplevel window as master
        self.new_obj = MyFirmDetails(self.new_win)
    
        # Make sure the window appears on top
        self.new_win.transient(self.root)
        self.new_win.grab_set()

    def Clients(self):
        """Open Clients Management (formerly Purchases)"""
        self.new_win = Toplevel(self.root)
        self.new_obj = SalesClass(self.new_win)

    def B2BSales(self):
        """Open B2B Sales Management"""
        try:
            self.new_win = Toplevel(self.root)
            self.new_obj = B2BClientClass(self.new_win)
        except ImportError as e:
            messagebox.showerror("Error", f"B2BSales module not available: {e}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open B2B Sales: {e}", parent=self.root)

    def Suppliers(self):
        """Open Suppliers Management (formerly Inventory)"""
        self.new_win = Toplevel(self.root)
        self.new_obj = PurchasesDashboard(self.new_win)

    def Tracker(self):
        """Open Tracker (formerly Admin)"""
        try:
            from Tracker import TrackerClass
            self.new_win = Toplevel(self.root)
            self.new_obj = TrackerClass(self.new_win)
        except ImportError as e:
            messagebox.showerror("Error", f"Tracker module not available: {e}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Tracker: {e}", parent=self.root)

    def update_content(self):
        """Update dashboard content"""
        # Update clock
        now = datetime.datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%I:%M:%S %p")
        self.lbl_clock.config(
            text=f"Date: {date_str} | Time: {time_str}"
        )

        if self.app_running:
            self.root.after(1000, self.update_content)

if __name__ == "__main__":
    root = Tk()
    obj = IMS(root)
    root.protocol("WM_DELETE_WINDOW", obj.on_app_close)
    root.mainloop()