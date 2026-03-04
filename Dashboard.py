from datetime import datetime
import tkinter
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from Employee import EmployeeClass
from PurchaseEntry import PurchasesClass
from Category import CategoryClass
from SaleSummary import SalesClass
from MyAdmin import IMS
from Product import IntegratedInventorySystem as ProductClass
from InvoiceNew import Invoice_Class
from BankAmountTracker import BankAmountTracker
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
        
        # Updated color scheme with bright, vibrant colors
        self.colors = {
            'primary': '#f0f2f5',          # Very light gray background
            'secondary': '#ffffff',         # White for cards
            'accent': "#fff000",            # Bright coral
            'highlight': '#000000',         # Bright turquoise
            'success': '#2ecc71',            # Emerald green
            'warning': '#f39c12',            # Orange
            'danger': '#F02117',              # Red
            'light': '#b0c4de',                # Light steel blue
            'dark': '#debc69',                 # Dark blue-gray (header background)
            'white': '#ffffff',
            'black': '#000000',                # Sidebar background
            'card_bg': '#ffffff',
            'sidebar': "#fff000",               # Slightly lighter than before (used for dashboard card)
            'text_dark': "#000000",
            "dark_green" :"#006400",
            'text_light': '#ffffff',
            'sidebar_bg': '#000000'  ,
            'menu_bk':'#1E1E1E'           # New: pure black for sidebar
        }
        
        self.root.config(bg=self.colors['primary'])
        
        # Hide main window initially
        self.root.withdraw()
        
        # User data file
        self.user_data_file = "user_data.json"
        self.current_user = None
        self.is_guest = False
        self.is_admin = False
        
        # Show login screen first
        self.show_login_screen()
    
    def on_app_close(self):
        self.app_running = False
        self.root.destroy()

    def center_window(self, window, width, height):
        """Center any window on screen"""
        x = (self.screen_width // 2) - (width // 2)
        y = (self.screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def init_main_window(self):
        """Initialize the main window after login"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Show the window
        self.root.deiconify()
        
        # Configure styles
        self.configure_styles()
        
        # Title bar frame (modern header) - fixed height, expands horizontally
        title_frame = Frame(self.root, bg=self.colors['dark'], height=80)
        title_frame.pack(side=TOP, fill=X)
        title_frame.pack_propagate(False)
        
        # Left: Logo and Title
        title_left = Frame(title_frame, bg=self.colors['dark'])
        title_left.pack(side=LEFT, fill=Y, padx=20)
        
        title = Label(
            title_left,
            text="POS SYSTEM",
            font=("Segoe UI", 24, "bold"),
            bg=self.colors['dark'],
            fg=self.colors['black'],
            anchor="w"
        )
        title.pack(side=LEFT)
        
        subtitle = Label(
            title_left,
            text="Professional Point of Sale",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['dark'],
            fg=self.colors['black'],
            anchor="w"
        )
        subtitle.pack(side=LEFT, padx=(10, 0))
        
        # Center: Clock (Expands to push right content to the edge)
        self.lbl_clock = Label(
            title_frame,
            text="",
            font=("Segoe UI", 11,  "bold"),
            bg=self.colors['dark'],
            fg=self.colors['black']
        )
        self.lbl_clock.pack(side=LEFT, expand=True)
        
        # Right: User info and logout
        title_right = Frame(title_frame, bg=self.colors['dark'])
        title_right.pack(side=RIGHT, fill=Y, padx=20)
        
        if self.is_admin:
            user_type = "Administrator"
            user_icon = "👑"
        elif self.is_guest:
            user_type = "Guest"
            user_icon = "👤"
        else:
            user_type = "User"
            user_icon = "👤"
            
        self.user_label = Label(
            title_right,
            text=f"{user_icon} {self.current_user} ({user_type})",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['dark'],
            fg=self.colors['black']
        )
        self.user_label.pack(side=LEFT, padx=(0, 20))
        
        logout_text = "🚪 Logout" if not self.is_guest else "🚪 Exit Guest"
        logout_btn = Button(
            title_right,
            text=logout_text,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['black'],
            fg=self.colors['white'],
            cursor="hand2",
            command=self.logout,
            bd=0,
            padx=15,
            pady=5,
            relief=FLAT
        )
        logout_btn.pack(side=LEFT)
        
        # Main container for responsive body layout
        main_container = Frame(self.root, bg=self.colors['primary'])
        main_container.pack(fill=BOTH, expand=True)
        
        # Sidebar - fixed width, fully expands vertically
        sidebar = Frame(main_container, bg=self.colors['menu_bk'], width=220)
        sidebar.pack(side=LEFT, fill=Y)
        sidebar.pack_propagate(False)
        
        # Sidebar header
        sidebar_header = Frame(sidebar, bg=self.colors['black'], height=100)
        sidebar_header.pack(fill=X, pady=(0, 20))
        sidebar_header.pack_propagate(False)
        
        Label(
            sidebar_header,
            text="HOME",
            font=("Segoe UI", 26, "bold"),
            bg=self.colors['black'],
            fg=self.colors['sidebar']
        ).pack(expand=True)
        
        # Navigation buttons container
        nav_frame = Frame(sidebar, bg=self.colors['menu_bk'])
        nav_frame.pack(fill=BOTH, expand=True, padx=15, pady=10)
        
        # Define navigation items based on user type
        if self.is_admin:
            nav_items = [
                ("👑 ADMIN", self.Admin),
                ("👥 EMPLOYEE", self.Employee),
                ("📦 PURCHASES", self.Supplier),
                ("📊 INVENTORY", self.Product),
                ("💰 SALES", self.Invoice),
                ("🏦 BANK", self.Bank),
                ("🚪 EXIT", self.on_app_close)
            ]
        elif self.is_guest:
            nav_items = [
                ("📦 PURCHASES", self.Supplier),
                ("📊 INVENTORY", self.Product),
                ("💰 SALES", self.Invoice),
                ("🚪 Exit", self.on_app_close)
            ]
        else:
            nav_items = [
                ("👥 Employee", self.Employee),
                ("📦 PURCHASES", self.Supplier),
                ("📊 INVENTORY", self.Product),
                ("💰 SALES", self.Invoice),
                ("🏦 BANK", self.Bank),
                ("🚪 Exit", self.on_app_close)
            ]
        
        bright_colors = [
            "#3498DB", "#2ECC71", "#E67E22", "#9B59B6", "#E74C3C", 
            "#F1C40F", "#C0392B", "#F02117", "#FF69B4", "#2006B4",
            "#FDDD0A", "#0074D9", "#3D9970", "#2ECC40"
        ]
        
        for i, (text, command) in enumerate(nav_items):
            btn_color = bright_colors[i % len(bright_colors)]
            r = int(btn_color[1:3], 16)
            g = int(btn_color[3:5], 16)
            b = int(btn_color[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            text_color = '#000000' if brightness > 128 else '#ffffff'
            
            btn = Button(
                nav_frame,
                text=text,
                font=("Segoe UI", 12, "bold"),
                bg=btn_color,
                fg=text_color,
                command=command,
                bd=0,
                anchor="w",
                padx=20,
                pady=12,
                cursor="hand2",
                relief=FLAT,
                activebackground=btn_color,
                activeforeground=text_color
            )
            btn.pack(fill=X, pady=5)
        
        # Responsive Dashboard Area - expands to fill remaining space
        dashboard = Frame(main_container, bg=self.colors['black'])
        dashboard.pack(side=LEFT, fill=BOTH, expand=True, padx=20, pady=20)
        
        # Main dashboard content
        content_frame = Frame(dashboard, bg=self.colors['black'])
        content_frame.pack(fill=BOTH, expand=True)

        # Company info card
        company_card = Frame(
            content_frame,
            bg=self.colors['white'],
            relief=FLAT,
            bd=1,
            highlightbackground=self.colors['light'],
            highlightthickness=1
        )
        company_card.pack(fill=BOTH, expand=True)
        
        # Responsive Inner Frame with reduced padding
        inner_frame = Frame(company_card, bg=self.colors['white'], padx=20, pady=20)
        inner_frame.pack(fill=BOTH, expand=True)
        
        # Compact Title Section (Removed extra space)
        title_group = Frame(inner_frame, bg=self.colors['white'])
        title_group.pack(fill=X, pady=0)
        
        Label(
            title_group,
            text="POS SYSTEM",
            font=("Segoe UI", 28, "bold"),
            bg=self.colors['white'],
            fg=self.colors['text_dark']
        ).pack(pady=0)
        
        Label(
            title_group,
            text="Produced By Dukes Tech Services",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors['white'],
            fg=self.colors['black']
        ).pack(pady=0)
        
        # Line Divider
        Frame(inner_frame, bg=self.colors['black'], height=2).pack(fill=X, pady=(10, 5))
        
        # Compact Contact Information Section
        contact_line = Frame(inner_frame, bg=self.colors['white'])
        contact_line.pack(pady=0)
        
        Label(contact_line, text="🌐 dukestechservices.com", font=("Segoe UI", 11),
              bg=self.colors['white'], fg=self.colors['highlight'], cursor="hand2").pack(side=LEFT, padx=(0, 10))
        Label(contact_line, text="|", font=("Segoe UI", 11, "bold"), bg=self.colors['white'], fg=self.colors['text_dark']).pack(side=LEFT, padx=5)
        
        Label(contact_line, text="📞 +92 309 7671363", font=("Segoe UI", 11),
              bg=self.colors['white'], fg=self.colors['text_dark']).pack(side=LEFT, padx=10)
        Label(contact_line, text="|", font=("Segoe UI", 11, "bold"), bg=self.colors['white'], fg=self.colors['text_dark']).pack(side=LEFT, padx=5)
        
        Label(contact_line, text="📧 info@dukestechservices.com", font=("Segoe UI", 11),
              bg=self.colors['white'], fg=self.colors['highlight'], cursor="hand2").pack(side=LEFT, padx=(10, 0))
        
        # Line Divider
        Frame(inner_frame, bg=self.colors['black'], height=1).pack(fill=X, pady=(5, 10))
        
        # Expandable Company description
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
        
        text_frame = Frame(inner_frame, bg=self.colors['white'])
        text_frame.pack(fill=BOTH, expand=True) # Text frame absorbs remaining space for responsiveness
        
        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        description_label = Text(
            text_frame,
            font=("Segoe UI", 11),
            bg=self.colors['white'],
            fg=self.colors['text_dark'],
            wrap=WORD,
            yscrollcommand=scrollbar.set,
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=5
        )
        description_label.pack(side=LEFT, fill=BOTH, expand=True)
        description_label.insert(END, description_text)
        description_label.config(state=DISABLED)
        scrollbar.config(command=description_label.yview)

        # Compact SYSTEM NOTICE
        notice_frame = Frame(inner_frame, bg='#fff3cd', bd=1, relief=SOLID, highlightbackground='#ffeeba')
        notice_frame.pack(fill=X, pady=(15, 0))

        Label(notice_frame, text="📢", font=("Segoe UI", 16), bg='#fff3cd', fg='#856404').pack(side=LEFT, padx=(10,5), pady=5)

        notice_text = "System Notice / Reporting Guidelines: To ensure accurate financial reporting and system consistency, all users are required to strictly follow the defined color scheme and reporting structure within the POS system."
        Label(notice_frame, text=notice_text, font=("Segoe UI", 10), bg='#fff3cd', fg='#856404', justify=LEFT, wraplength=1000).pack(side=LEFT, padx=(0,10), pady=10, fill=X, expand=True)
        
        # Footer - fixed height, expands horizontally
        footer = Frame(self.root, bg=self.colors['dark'], height=40)
        footer.pack(side=BOTTOM, fill=X)
        footer.pack_propagate(False)
        
        if self.is_admin:
            footer_text = "POS System | Administrator Mode | Developed by Dukes Tech Services"
        elif self.is_guest:
            footer_text = "POS System | Guest Mode (Limited Access)"
        else:
            footer_text = "POS System | Professional Edition | Developed by Dukes Tech Services"
        
        Label(
            footer,
            text=footer_text,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['dark'],
            fg=self.colors['highlight']
        ).pack(expand=True)
        
        if not self.is_guest:
            self.update_content()

    def configure_styles(self):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        style.configure('Primary.TButton', font=('Segoe UI', 11), padding=10, relief='flat')
        style.configure('Success.TButton', font=('Segoe UI', 11), padding=10, relief='flat')
        style.configure('Modern.TEntry', fieldbackground=self.colors['card_bg'],
                       foreground=self.colors['text_dark'], padding=10, relief='flat')

    def show_login_screen(self):
        """Display modern login/signup screen with bright colors and credit"""
        login_window = Toplevel(self.root)
        login_window.title("Login - POS System")
        # Added minsize for responsive safety on small screens
        login_window.minsize(900, 600)
        login_window.geometry("1000x650") 
        self.center_window(login_window, 1000, 650)
        
        login_colors = {
            'bg': "#000000",
            'card': '#ffffff',
            'card1':'#debc69',   
            'accent': '#FFD700',
            'text': '#000000',
            'light': '#ffffff',
            'input_bg': '#ecf0f1',
            'danger':'#F02117'
        }
        
        login_window.config(bg=login_colors['bg'])
        login_window.resizable(True, True) # Responsive
        
        login_window.grab_set()
        login_window.protocol("WM_DELETE_WINDOW", lambda: self.on_login_close(login_window))
        
        main_container = Frame(login_window, bg=login_colors['bg'])
        main_container.pack(fill=BOTH, expand=True, padx=40, pady=40)
        
        left_frame = Frame(main_container, bg=login_colors['bg'])
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 40))
        
        Label(left_frame, text="Welcome to", font=("Segoe UI", 16,"bold"), bg=login_colors['bg'], fg='#ffffff').pack(anchor="w", pady=(20, 0))
        Label(left_frame, text="POS SYSTEM", font=("Segoe UI", 40, "bold"), bg=login_colors['bg'], fg="#debc69").pack(anchor="w", pady=(0, 10))
        Label(left_frame, text="Professional Point of Sale Solutions", font=("Segoe UI", 14, "bold"), bg=login_colors['bg'], fg='#ffffff').pack(anchor="w", pady=(0, 40))
        
        features = [
            ("✓ Professional Dashboard", '#debc69'),
            ("✓ Inventory Management", '#debc69'),
            ("✓ Sales & Invoicing", '#debc69'),
            ("✓ Employee Management", '#debc69'),
            ("✓ Real-time Analytics", "#debc69"),
            ("✓ Bank Amount Tracking", '#debc69')
        ]
        
        for feature, color in features:
            feature_frame = Frame(left_frame, bg=login_colors['bg'])
            feature_frame.pack(fill=X, pady=5)
            Label(feature_frame, text=feature, font=("Segoe UI", 12, "bold"), bg=login_colors['bg'], fg=color, anchor="w").pack(side=LEFT)
        
        credit_frame = Frame(left_frame, bg=login_colors['bg'])
        credit_frame.pack(side=BOTTOM, anchor="sw", pady=(40, 0))
        Label(credit_frame, text="Software produced by", font=("Segoe UI", 12, "bold"), bg=login_colors['bg'], fg='#ffffff').pack(anchor="w")
        Label(credit_frame, text="Dukes Tech Services", font=("Segoe UI", 16, "bold"), bg=login_colors['bg'], fg='#debc69').pack(anchor="w")
        
        right_frame = Frame(main_container, bg=login_colors['card1'], relief=FLAT)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        style = ttk.Style()
        style.configure('TNotebook', background=login_colors['card1'])
        style.configure('TNotebook.Tab', background=login_colors['card1'], foreground=login_colors['text'], padding=[20, 10])
        style.map('TNotebook.Tab', background=[('selected', login_colors['accent'])], foreground=[('selected', '#000000')])
        
        login_frame = Frame(notebook, bg=login_colors['card1'])
        notebook.add(login_frame, text="Login")
        self.create_login_tab(login_frame, login_window, login_colors)
        
        guest_frame = Frame(notebook, bg=login_colors['card1'])
        notebook.add(guest_frame, text="Guest Access")
        self.create_guest_tab(guest_frame, login_window, login_colors)

    def create_login_tab(self, parent, login_window, colors):
        """Create modern login tab with bright colors"""
        Label(parent, text="Login to Your Account", font=("Segoe UI", 18, "bold"), bg=colors['card1'], fg='#000000').pack(pady=(20, 30))
        
        input_frame = Frame(parent, bg=colors['card1'])
        input_frame.pack(fill=X, padx=40, pady=10)
        Label(input_frame, text="Username", font=("Segoe UI", 11), bg=colors['card1'], fg=colors['text']).pack(anchor="w")
        self.login_username = Entry(input_frame, font=("Segoe UI", 12), bd=0, bg=colors['input_bg'], fg=colors['text'], insertbackground=colors['text'], relief=FLAT)
        self.login_username.pack(fill=X, pady=(5, 0), ipady=8)
        
        input_frame = Frame(parent, bg=colors['card1'])
        input_frame.pack(fill=X, padx=40, pady=10)
        Label(input_frame, text="Password", font=("Segoe UI", 11), bg=colors['card1'], fg=colors['text']).pack(anchor="w")
        self.login_password = Entry(input_frame, font=("Segoe UI", 12), bd=0, bg=colors['input_bg'], fg=colors['text'], insertbackground=colors['text'], relief=FLAT, show="•")
        self.login_password.pack(fill=X, pady=(5, 0), ipady=8)
        
        info_frame = Frame(parent, bg=colors['card1'])
        info_frame.pack(fill=X, padx=40, pady=(10, 0))
        Label(info_frame, text="Demo Admin: Username='Admin' Password='123456'", font=("Segoe UI", 9, "italic"), bg=colors['card1'], fg='#000000').pack(anchor="w")
        
        btn_frame = Frame(parent, bg=colors['card1'])
        btn_frame.pack(fill=X, padx=40, pady=(30, 20))
        Button(btn_frame, text="Login", font=("Segoe UI", 12, "bold"), bg='#000000', fg='#ffffff', cursor="hand2", command=lambda: self.attempt_login(login_window), bd=0, relief=FLAT, padx=30, pady=12).pack(fill=X)

    def create_guest_tab(self, parent, login_window, colors):
        """Create modern guest access tab with bright colors"""
        Label(parent, text="Guest Access", font=("Segoe UI", 18, "bold"), bg=colors['card1'], fg=colors['text']).pack(pady=(40, 20))
        Label(parent, text="Try the system in demo mode", font=("Segoe UI", 12), bg=colors['card1'], fg=colors['text']).pack(pady=(0, 30))
        
        features = [
            ("• Access to Purchases only", '#000000'),
            ("• Access to Inventory only", '#000000'),
            ("• Access to Sales only", '#000000'),
            ("• Access to Bank Tracking", '#000000'),
            ("• Employee and Admin features locked", '#000000'),
            ("• Perfect for testing basic features", '#000000')
        ]
        
        for feature, color in features:
            feature_frame = Frame(parent, bg=colors['card1'])
            feature_frame.pack(fill=X, padx=60, pady=5)
            Label(feature_frame, text=feature, font=("Segoe UI", 11, "bold"), bg=colors['card1'], fg=color, anchor="w").pack(anchor="w")
        
        btn_frame = Frame(parent, bg=colors['card1'])
        btn_frame.pack(fill=X, padx=60, pady=(40, 20))
        Button(btn_frame, text="Enter as Guest", font=("Segoe UI", 12, "bold"), bg='#000000', fg='#ffffff', cursor="hand2", command=lambda: self.enter_as_guest(login_window), bd=0, relief=FLAT, padx=30, pady=12).pack(fill=X)

    def attempt_login(self, login_window):
        """Handle login attempt"""
        username = self.login_username.get()
        password = self.login_password.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password", parent=login_window)
            return
        
        if username == "Admin" and password == "123456":
            self.current_user = username
            self.is_guest = False
            self.is_admin = True
            login_window.destroy()
            self.init_main_window()
            messagebox.showinfo("Welcome", f"Welcome Administrator!", parent=self.root)
            return
        
        if self.authenticate_user(username, password):
            self.current_user = username
            self.is_guest = False
            self.is_admin = False
            login_window.destroy()
            self.init_main_window()
            messagebox.showinfo("Welcome", f"Welcome back, {username}!", parent=self.root)
        else:
            messagebox.showerror("Error", "Invalid username or password", parent=login_window)

    def enter_as_guest(self, login_window):
        """Enter as guest user"""
        self.current_user = "Guest"
        self.is_guest = True
        self.is_admin = False
        login_window.destroy()
        self.init_main_window()
        messagebox.showinfo("Guest Mode", "You are now in guest mode with limited functionality.\n\nAccessible features:\n• Purchases\n• Inventory\n• Sales\n• Bank Tracking", parent=self.root)

    def user_exists(self, username):
        """Check if user exists"""
        if not os.path.exists(self.user_data_file):
            return False
        try:
            with open(self.user_data_file, 'r') as f:
                users = json.load(f)
                return username in users
        except:
            return False

    def create_user(self, username, password):
        """Create new user account"""
        users = {}
        if os.path.exists(self.user_data_file):
            try:
                with open(self.user_data_file, 'r') as f:
                    users = json.load(f)
            except:
                users = {}
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        users[username] = {
            'password_hash': password_hash,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        try:
            with open(self.user_data_file, 'w') as f:
                json.dump(users, f, indent=2)
            return True
        except:
            return False

    def authenticate_user(self, username, password):
        """Authenticate user"""
        if not os.path.exists(self.user_data_file):
            return False
        try:
            with open(self.user_data_file, 'r') as f:
                users = json.load(f)
                
            if username in users:
                stored_hash = users[username]['password_hash']
                input_hash = hashlib.sha256(password.encode()).hexdigest()
                return stored_hash == input_hash
        except:
            return False
        return False

    def on_login_close(self, login_window):
        """Handle login window close"""
        if messagebox.askyesno("Exit", "Close the application?", parent=login_window):
            login_window.destroy()
            self.app_running = False
            self.root.destroy()
        else:
            login_window.grab_set()

    def logout(self):
        """Logout from current session"""
        if messagebox.askyesno("Confirm", "Logout from system?", parent=self.root):
            self.app_running = False
            self.root.withdraw()
            self.current_user = None
            self.is_guest = False
            self.is_admin = False
            self.show_login_screen()

    # Window openers with access control
    def Employee(self):
        if self.is_guest:
            messagebox.showinfo("Guest Mode", "Employee module is disabled in guest mode. Please login as Admin for full access.", parent=self.root)
            return
        self.new_win = Toplevel(self.root)
        self.new_obj = EmployeeClass(self.new_win)

    def Supplier(self):
        self.new_win = Toplevel(self.root)
        self.new_obj = PurchasesClass(self.new_win)

    def Category(self):
        if self.is_guest:
            messagebox.showinfo("Guest Mode", "Category module is disabled in guest mode. Please login as Admin for full access.", parent=self.root)
            return
        self.new_win = Toplevel(self.root)
        self.new_obj = CategoryClass(self.new_win)

    def Product(self):
        self.new_win = Toplevel(self.root)
        self.new_obj = ProductClass(self.new_win)

    def Invoice(self):
        self.new_win = Toplevel(self.root)
        self.new_obj = Invoice_Class(self.new_win)

    def Bank(self):
        self.new_win = Toplevel(self.root)
        self.new_obj = BankAmountTracker(self.new_win)

    def Admin(self):
        if not self.is_admin:
            if self.is_guest:
                messagebox.showinfo("Guest Mode", "Admin dashboard is disabled in guest mode. Please login as Admin for full access.", parent=self.root)
            else:
                messagebox.showinfo("Access Denied", "Admin dashboard is only accessible to administrators.", parent=self.root)
            return
        try:
            from MyAdmin import IMS
            self.new_win = Toplevel(self.root)
            self.new_obj = IMS(self.new_win)
        except ImportError as e:
            messagebox.showerror("Error", f"Admin module not available: {e}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Admin dashboard: {e}", parent=self.root)

    def update_content(self):
        """Update dashboard content for logged-in users"""
        if self.is_guest:
            return
            
        now = datetime.datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%I:%M:%S %p")
        self.lbl_clock.config(text=f"Date: {date_str} | Time: {time_str}")

        if self.app_running:
            self.root.after(3000, self.update_content)

if __name__ == "__main__":
    root = Tk()
    obj = IMS(root)
    root.protocol("WM_DELETE_WINDOW", obj.on_app_close)
    root.mainloop()