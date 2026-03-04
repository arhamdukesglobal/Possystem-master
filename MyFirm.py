import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import tkcalendar as tkcal
import webbrowser
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER

# Database setup (same as before)
def setup_database():
    conn = sqlite3.connect('Possystem.db')
    cursor = conn.cursor()
    
    # Create firm_details table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS firm_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        firm_type TEXT,
        firm_name TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        city_town TEXT,
        post_code TEXT,
        website TEXT,
        business_start_date DATE,
        book_start_date DATE,
        year_end DATE,
        country TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create history table for tracking changes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS firm_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        firm_details_id INTEGER,
        change_type TEXT,
        change_details TEXT,
        changed_by TEXT DEFAULT 'System',
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (firm_details_id) REFERENCES firm_details(id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
setup_database()

class MyFirmDetails:
    def __init__(self, root):
        # Store the root window (Toplevel from Dashboard)
        self.root = root
        
        # Configure main window - Keep standard window controls
        self.root.title("My POS System - Firm Details")
        self.root.geometry("1100x800")  # Slightly smaller for better fit
        self.root.minsize(1000, 700)  # Set minimum size
        
        # Make window resizable
        self.root.resizable(True, True)
        
        # Remove any forced positioning
        # Center window initially, but allow free movement
        self.center_window_initially()
        
        # Enhanced Banking/Finance color scheme
        self.color_scheme = {
            'primary': '#0d47a1',      # Deep Navy Blue (Banking)
            'secondary': '#1565c0',     # Corporate Blue
            'accent': '#1976d2',        # Trust Blue
            'success': '#2e7d32',       # Financial Green
            'warning': '#f57c00',       # Gold/Orange
            'error': '#c62828',         # Alert Red
            'light': '#e3f2fd',         # Light Blue background
            'dark': '#0a1e32',          # Very Dark Blue
            'text': '#ffffff',          # White text
            'text_dark': '#263238',     # Dark text
            'bg_light': '#f8fbff',      # Very Light Blue background
            'card_bg': '#ffffff',       # White card background
            'border': '#bbdefb',        # Light Blue border
            'header_bg': '#0d47a1',     # Header background
            'datetime_bg': '#1565c0',   # DateTime background
            'section_bg': '#f0f7ff',    # Section background
            'hover_bg': '#e8f0fe',      # Hover background
        }
        
        self.root.configure(bg=self.color_scheme['bg_light'])
        self.style = ttk.Style()
        self.setup_styles()
        
        # Variables for real-time clock
        self.date_time_var = tk.StringVar()
        
        # Add drag functionality to header
        self.header_draggable = False
        
        self.create_widgets()
        self.update_clock()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Bind events for window movement
        self.bind_drag_events()
        
    def setup_styles(self):
        """Configure custom styles for the application"""
        self.style.theme_use('clam')
        
        # Button styles
        self.style.configure('Primary.TButton',
                            background=self.color_scheme['primary'],
                            foreground=self.color_scheme['text'],
                            borderwidth=0,
                            focuscolor='none',
                            font=('Segoe UI', 11, 'bold'),
                            padding=(20, 12))
        self.style.map('Primary.TButton',
                      background=[('active', self.color_scheme['accent']),
                                 ('pressed', self.color_scheme['secondary']),
                                 ('disabled', '#cccccc')])
        
        self.style.configure('Secondary.TButton',
                            background=self.color_scheme['light'],
                            foreground=self.color_scheme['primary'],
                            borderwidth=1,
                            font=('Segoe UI', 10),
                            padding=(15, 8))
        self.style.map('Secondary.TButton',
                      background=[('active', self.color_scheme['hover_bg']),
                                 ('pressed', '#bbdefb')])
        
        self.style.configure('Report.TButton',
                            background=self.color_scheme['success'],
                            foreground=self.color_scheme['text'],
                            borderwidth=0,
                            font=('Segoe UI', 11, 'bold'),
                            padding=(20, 12))
        self.style.map('Report.TButton',
                      background=[('active', '#388e3c'),
                                 ('pressed', '#1b5e20')])
        
        # Label styles
        self.style.configure('Header.TLabel',
                            background=self.color_scheme['header_bg'],
                            foreground=self.color_scheme['text'],
                            font=('Segoe UI', 20, 'bold'),
                            padding=15,
                            borderwidth=0)
        
        self.style.configure('DateTime.TLabel',
                            background=self.color_scheme['datetime_bg'],
                            foreground=self.color_scheme['text'],
                            font=('Segoe UI', 11, 'bold'),
                            padding=10)
        
        self.style.configure('Section.TLabel',
                            background=self.color_scheme['section_bg'],
                            foreground=self.color_scheme['primary'],
                            font=('Segoe UI', 14, 'bold'),
                            padding=12)
        
        self.style.configure('Field.TLabel',
                            background=self.color_scheme['card_bg'],
                            foreground=self.color_scheme['text_dark'],
                            font=('Segoe UI', 11, 'bold'))
        
        self.style.configure('Required.TLabel',
                            background=self.color_scheme['card_bg'],
                            foreground=self.color_scheme['error'],
                            font=('Segoe UI', 11, 'bold'))
        
        self.style.configure('Note.TLabel',
                            background=self.color_scheme['card_bg'],
                            foreground=self.color_scheme['warning'],
                            font=('Segoe UI', 10, 'italic'))
        
        # Entry styles
        self.style.configure('Custom.TEntry',
                            fieldbackground='white',
                            bordercolor=self.color_scheme['border'],
                            lightcolor=self.color_scheme['border'],
                            darkcolor=self.color_scheme['border'],
                            borderwidth=1,
                            relief='solid',
                            padding=8)
        self.style.map('Custom.TEntry',
                      bordercolor=[('focus', self.color_scheme['accent']),
                                   ('active', self.color_scheme['accent'])])
        
        # Frame styles
        self.style.configure('Card.TFrame',
                            background=self.color_scheme['card_bg'],
                            relief='flat',
                            borderwidth=1,
                            bordercolor=self.color_scheme['border'])
        
    def bind_drag_events(self):
        """Bind events to make window draggable from header"""
        # Bind mouse events to header for dragging
        self.header_frame.bind("<ButtonPress-1>", self.start_move)
        self.header_frame.bind("<ButtonRelease-1>", self.stop_move)
        self.header_frame.bind("<B1-Motion>", self.do_move)
        
        # Make cursor change on header hover to indicate draggable area
        self.header_frame.bind("<Enter>", lambda e: self.header_frame.config(cursor="fleur"))
        self.header_frame.bind("<Leave>", lambda e: self.header_frame.config(cursor=""))
        
    def start_move(self, event):
        """Start window movement"""
        self.x = event.x
        self.y = event.y
        self.header_draggable = True
        
    def stop_move(self, event):
        """Stop window movement"""
        self.header_draggable = False
        
    def do_move(self, event):
        """Move the window"""
        if self.header_draggable:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")
        
    def center_window_initially(self):
        """Center the window initially, but allow free movement"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        # Main container
        main_container = tk.Frame(self.root, bg=self.color_scheme['bg_light'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header Section - Make this draggable
        self.header_frame = tk.Frame(main_container, bg=self.color_scheme['header_bg'], height=80)
        self.header_frame.pack(fill='x', pady=(0, 20))
        self.header_frame.pack_propagate(False)
        
        # Title with move indicator
        title_frame = tk.Frame(self.header_frame, bg=self.color_scheme['header_bg'])
        title_frame.pack(side='left', fill='both', expand=True, padx=20)
        
        title_label = tk.Label(title_frame,
                              text="🏢 My Firm Details (Drag here to move)",
                              font=('Segoe UI', 22, 'bold'),
                              bg=self.color_scheme['header_bg'],
                              fg=self.color_scheme['text'])
        title_label.pack(side='left')
        
        # Date and Time
        datetime_frame = tk.Frame(self.header_frame, bg=self.color_scheme['header_bg'])
        datetime_frame.pack(side='right', fill='both', padx=20)
        
        datetime_label = tk.Label(datetime_frame,
                                 textvariable=self.date_time_var,
                                 font=('Segoe UI', 11, 'bold'),
                                 bg=self.color_scheme['datetime_bg'],
                                 fg=self.color_scheme['text'],
                                 padx=15,
                                 pady=8,
                                 relief='flat')
        datetime_label.pack(side='right')
        
        # Main content area with notebook for better organization
        content_frame = tk.Frame(main_container, bg=self.color_scheme['bg_light'])
        content_frame.pack(fill='both', expand=True)
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Tab 1: Basic Information
        basic_info_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(basic_info_frame, text='📝 Basic Information')
        
        # Tab 2: Dates & Location
        dates_location_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(dates_location_frame, text='📅 Dates & Location')
        
        # Tab 3: Actions
        actions_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(actions_frame, text='⚡ Actions')
        
        # Store all fields
        self.fields = {}
        
        # Create widgets for each tab
        self.create_basic_info_tab(basic_info_frame)
        self.create_dates_location_tab(dates_location_frame)
        self.create_actions_tab(actions_frame)
        
        # Status bar at bottom
        self.create_status_bar(main_container)
    
    def create_basic_info_tab(self, parent):
        """Create widgets for Basic Information tab"""
        # Create a canvas with scrollbar for this tab
        canvas_frame = tk.Frame(parent, bg=self.color_scheme['card_bg'])
        canvas_frame.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg=self.color_scheme['card_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Card.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side='left', fill='both', expand=True, padx=2, pady=2)
        scrollbar.pack(side='right', fill='y')
        
        # Configure grid for scrollable frame
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)
        
        # Section 1: Firm Details
        firm_section = ttk.LabelFrame(scrollable_frame, text=" Firm Details ", 
                                     style='Card.TFrame', padding=15)
        firm_section.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        firm_section.grid_columnconfigure(0, weight=1)
        firm_section.grid_columnconfigure(1, weight=1)
        
        # Required fields with better spacing
        row = 0
        self.fields['firm_type'] = self.create_field(firm_section, "Firm Type*", row, 0, required=True)
        self.fields['firm_name'] = self.create_field(firm_section, "Firm Name*", row, 1, required=True)
        row += 1
        
        # Section 2: Contact Information
        contact_section = ttk.LabelFrame(scrollable_frame, text=" Contact Information ", 
                                        style='Card.TFrame', padding=15)
        contact_section.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        contact_section.grid_columnconfigure(0, weight=1)
        contact_section.grid_columnconfigure(1, weight=1)
        
        row = 0
        self.fields['email'] = self.create_field(contact_section, "Email*", row, 0, required=True)
        self.fields['phone'] = self.create_field(contact_section, "Phone*", row, 1, required=True)
        row += 1
        
        self.fields['website'] = self.create_field(contact_section, "Website", row, 0)
        self.fields['country'] = self.create_field(contact_section, "Country*", row, 1, required=True)
        row += 1
        
        # Section 3: Address (full width)
        address_section = ttk.LabelFrame(scrollable_frame, text=" Address Details ", 
                                        style='Card.TFrame', padding=15)
        address_section.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        
        row = 0
        self.fields['address'] = self.create_textarea(address_section, "Address*", row, 0, required=True)
        row += 1
        
        city_post_frame = tk.Frame(address_section, bg=self.color_scheme['card_bg'])
        city_post_frame.grid(row=row, column=0, sticky='ew', pady=10)
        city_post_frame.grid_columnconfigure(0, weight=1)
        city_post_frame.grid_columnconfigure(1, weight=1)
        
        # Updated: City/Town is required, Post Code is optional (no asterisk)
        self.fields['city_town'] = self.create_field_in_frame(city_post_frame, "City/Town*", 0, 0, required=True)
        self.fields['post_code'] = self.create_field_in_frame(city_post_frame, "Post Code", 0, 1, required=False)
        
        # Required note
        note_frame = ttk.Frame(scrollable_frame, style='Card.TFrame')
        note_frame.grid(row=3, column=0, columnspan=2, pady=15, sticky='ew')
        
        note_label = tk.Label(note_frame,
                             text="* Required fields must be filled",
                             font=('Segoe UI', 10, 'italic'),
                             bg=self.color_scheme['card_bg'],
                             fg=self.color_scheme['error'])
        note_label.pack(pady=5)
        
    def create_dates_location_tab(self, parent):
        """Create widgets for Dates & Location tab"""
        # Create a canvas with scrollbar for this tab
        canvas_frame = tk.Frame(parent, bg=self.color_scheme['card_bg'])
        canvas_frame.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg=self.color_scheme['card_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Card.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side='left', fill='both', expand=True, padx=2, pady=2)
        scrollbar.pack(side='right', fill='y')
        
        # Configure grid for scrollable frame
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)
        
        # Section: Important Dates
        dates_section = ttk.LabelFrame(scrollable_frame, text=" Important Dates ", 
                                      style='Card.TFrame', padding=20)
        dates_section.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        dates_section.grid_columnconfigure(0, weight=1)
        dates_section.grid_columnconfigure(1, weight=1)
        
        row = 0
        self.fields['business_start_date'] = self.create_date_field(dates_section, "Business Start Date*", row, 0, required=True)
        self.fields['book_start_date'] = self.create_date_field(dates_section, "Book Start Date", row, 1)
        row += 1
        
        # Year End (full width)
        year_end_frame = ttk.Frame(dates_section, style='Card.TFrame')
        year_end_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=15)
        
        self.fields['year_end'] = self.create_date_field_in_frame(year_end_frame, "Year End", 0, 0)
        
        # Information section
        info_section = ttk.LabelFrame(scrollable_frame, text=" ℹ️ Information ", 
                                     style='Card.TFrame', padding=15)
        info_section.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        
        info_text = """Please ensure all required fields (*) are completed before saving.
        
Important Dates Information:
• Business Start Date: The date your business officially began operations
• Book Start Date: The starting date for your accounting records
• Year End: Your company's financial year end date
        
Note: Post Code is optional, all other fields marked with * are required."""
        
        info_label = tk.Label(info_section,
                             text=info_text,
                             font=('Segoe UI', 10),
                             bg=self.color_scheme['card_bg'],
                             fg=self.color_scheme['text_dark'],
                             justify='left',
                             anchor='w',
                             padx=10,
                             pady=10)
        info_label.pack(fill='both', expand=True)
        
    def create_actions_tab(self, parent):
        """Create widgets for Actions tab"""
        # Main container for actions
        actions_container = tk.Frame(parent, bg=self.color_scheme['card_bg'])
        actions_container.pack(fill='both', expand=True, padx=40, pady=40)
        
        # Section 1: Data Management
        data_section = ttk.LabelFrame(actions_container, text=" 📊 Data Management ", 
                                     style='Card.TFrame', padding=25)
        data_section.pack(fill='both', expand=True, pady=(0, 25))
        
        # Button grid for data actions
        button_grid = tk.Frame(data_section, bg=self.color_scheme['card_bg'])
        button_grid.pack(fill='both', expand=True)
        
        # Save Button (Primary action)
        save_btn = ttk.Button(button_grid,
                            text="💾 SAVE FIRM DETAILS",
                            style='Primary.TButton',
                            command=self.save_data)
        save_btn.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
        
        # Load Button
        load_btn = ttk.Button(button_grid,
                            text="📥 LOAD EXISTING DATA",
                            style='Secondary.TButton',
                            command=self.load_existing_data)
        load_btn.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        # Clear Button
        clear_btn = ttk.Button(button_grid,
                             text="🗑️ CLEAR ALL FIELDS",
                             style='Secondary.TButton',
                             command=self.clear_form)
        clear_btn.grid(row=1, column=0, padx=10, pady=10, sticky='ew')
        
        # Grid weights
        button_grid.grid_columnconfigure(0, weight=1)
        button_grid.grid_columnconfigure(1, weight=1)
        
        # Section 2: Reports
        report_section = ttk.LabelFrame(actions_container, text=" 📈 Reports & Documents ", 
                                       style='Card.TFrame', padding=25)
        report_section.pack(fill='both', expand=True)
        
        report_info = tk.Label(report_section,
                              text="Generate professional PDF reports of your firm details and change history.",
                              font=('Segoe UI', 11),
                              bg=self.color_scheme['card_bg'],
                              fg=self.color_scheme['text_dark'],
                              pady=15)
        report_info.pack()
        
        report_btn = ttk.Button(report_section,
                              text="📄 GENERATE HISTORICAL REPORT (PDF)",
                              style='Report.TButton',
                              command=self.generate_report)
        report_btn.pack(ipady=10, ipadx=15, pady=10)
        
    def create_status_bar(self, parent):
        """Create status bar at bottom"""
        status_bar = tk.Frame(parent, bg=self.color_scheme['dark'], height=35)
        status_bar.pack(side='bottom', fill='x', pady=(15, 0))
        status_bar.pack_propagate(False)
        
        status_text = "© 2024 POS System | Developed by Dukes Tech Services | Phone: +92 309 7671363 | Website: dukestechservices.com"
        
        status_label = tk.Label(status_bar,
                               text=status_text,
                               font=('Segoe UI', 9),
                               bg=self.color_scheme['dark'],
                               fg=self.color_scheme['light'])
        status_label.pack(expand=True)
        
    def create_field(self, parent, label_text, row, col, required=False):
        """Create a labeled input field"""
        frame = tk.Frame(parent, bg=self.color_scheme['card_bg'])
        frame.grid(row=row, column=col, sticky='ew', padx=10, pady=8)
        frame.grid_columnconfigure(0, weight=1)
        
        return self.create_field_in_frame(frame, label_text, 0, 0, required)
    
    def create_field_in_frame(self, parent, label_text, row, col, required=False):
        """Create field within an existing frame"""
        frame = tk.Frame(parent, bg=self.color_scheme['card_bg'])
        frame.grid(row=row, column=col, sticky='ew', padx=5, pady=5)
        frame.grid_columnconfigure(0, weight=1)
        
        # Label with asterisk for required fields
        label_text_with_asterisk = f"{label_text}" if not required else f"{label_text}"
        label_color = self.color_scheme['error'] if required else self.color_scheme['text_dark']
        
        label = tk.Label(frame, 
                        text=label_text_with_asterisk,
                        font=('Segoe UI', 11, 'bold'),
                        bg=self.color_scheme['card_bg'],
                        fg=label_color)
        label.grid(row=0, column=0, sticky='w', padx=(0, 5), pady=(0, 5))
        
        # Add red asterisk for required fields
        if required:
            asterisk = tk.Label(frame,
                              text="*",
                              font=('Segoe UI', 11, 'bold'),
                              bg=self.color_scheme['card_bg'],
                              fg=self.color_scheme['error'])
            asterisk.grid(row=0, column=1, sticky='w', pady=(0, 5))
        
        # Entry widget
        entry = ttk.Entry(frame, font=('Segoe UI', 11), style='Custom.TEntry')
        entry.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 5))
        
        return entry
    
    def create_textarea(self, parent, label_text, row, col, required=False):
        """Create a labeled textarea field"""
        frame = tk.Frame(parent, bg=self.color_scheme['card_bg'])
        frame.grid(row=row, column=col, sticky='ew', padx=10, pady=8)
        frame.grid_columnconfigure(0, weight=1)
        
        # Label
        label_color = self.color_scheme['error'] if required else self.color_scheme['text_dark']
        label = tk.Label(frame,
                        text=label_text,
                        font=('Segoe UI', 11, 'bold'),
                        bg=self.color_scheme['card_bg'],
                        fg=label_color)
        label.grid(row=0, column=0, sticky='w', padx=(0, 5), pady=(0, 5))
        
        if required:
            asterisk = tk.Label(frame,
                              text="*",
                              font=('Segoe UI', 11, 'bold'),
                              bg=self.color_scheme['card_bg'],
                              fg=self.color_scheme['error'])
            asterisk.grid(row=0, column=1, sticky='w', pady=(0, 5))
        
        # Text widget with scrollbar
        text_container = tk.Frame(frame, bg=self.color_scheme['card_bg'])
        text_container.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 5))
        text_container.grid_columnconfigure(0, weight=1)
        text_container.grid_rowconfigure(0, weight=1)
        
        text_widget = tk.Text(text_container,
                             height=4,
                             font=('Segoe UI', 11),
                             bg='white',
                             relief='solid',
                             borderwidth=1,
                             highlightbackground=self.color_scheme['border'],
                             highlightcolor=self.color_scheme['accent'],
                             highlightthickness=1,
                             wrap='word')
        text_widget.grid(row=0, column=0, sticky='nsew')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        return text_widget
    
    def create_date_field(self, parent, label_text, row, col, required=False):
        """Create a labeled date picker field"""
        frame = tk.Frame(parent, bg=self.color_scheme['card_bg'])
        frame.grid(row=row, column=col, sticky='ew', padx=10, pady=8)
        frame.grid_columnconfigure(0, weight=1)
        
        # Label
        label_color = self.color_scheme['error'] if required else self.color_scheme['text_dark']
        label = tk.Label(frame,
                        text=label_text,
                        font=('Segoe UI', 11, 'bold'),
                        bg=self.color_scheme['card_bg'],
                        fg=label_color)
        label.pack(anchor='w', padx=(0, 5), pady=(0, 5))
        
        # Date picker
        date_picker = tkcal.DateEntry(frame,
                                     width=20,
                                     background=self.color_scheme['primary'],
                                     foreground='white',
                                     borderwidth=1,
                                     font=('Segoe UI', 11),
                                     date_pattern='yyyy-mm-dd',
                                     selectbackground=self.color_scheme['accent'],
                                     selectforeground='white',
                                     normalbackground='white',
                                     normalforeground=self.color_scheme['text_dark'],
                                     weekendbackground='#e3f2fd',
                                     weekendforeground=self.color_scheme['text_dark'],
                                     headersbackground=self.color_scheme['primary'],
                                     headersforeground='white',
                                     bordercolor=self.color_scheme['border'],
                                     showweeknumbers=False)
        date_picker.pack(fill='x', pady=(0, 5), ipady=6)
        
        return date_picker
    
    def create_date_field_in_frame(self, parent, label_text, row, col):
        """Create date field within an existing frame"""
        frame = tk.Frame(parent, bg=self.color_scheme['card_bg'])
        frame.grid(row=row, column=col, sticky='ew', padx=5, pady=5)
        frame.grid_columnconfigure(0, weight=1)
        
        # Label
        label = tk.Label(frame,
                        text=label_text,
                        font=('Segoe UI', 11, 'bold'),
                        bg=self.color_scheme['card_bg'],
                        fg=self.color_scheme['text_dark'])
        label.grid(row=0, column=0, sticky='w', padx=(0, 5), pady=(0, 5))
        
        # Date picker
        date_picker = tkcal.DateEntry(frame,
                                     width=20,
                                     background=self.color_scheme['primary'],
                                     foreground='white',
                                     borderwidth=1,
                                     font=('Segoe UI', 11),
                                     date_pattern='yyyy-mm-dd',
                                     selectbackground=self.color_scheme['accent'],
                                     selectforeground='white',
                                     normalbackground='white',
                                     normalforeground=self.color_scheme['text_dark'],
                                     weekendbackground='#e3f2fd',
                                     weekendforeground=self.color_scheme['text_dark'],
                                     headersbackground=self.color_scheme['primary'],
                                     headersforeground='white',
                                     bordercolor=self.color_scheme['border'],
                                     showweeknumbers=False)
        date_picker.grid(row=1, column=0, sticky='ew', pady=(0, 5))
        
        return date_picker
        
    def update_clock(self):
        """Update the real-time date and time"""
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %I:%M:%S %p")
        self.date_time_var.set(current_time)
        # Update every second
        self.root.after(1000, self.update_clock)
    
    def save_data(self):
        """Save form data to database"""
        try:
            # Get all field values
            data = {}
            for key, widget in self.fields.items():
                if isinstance(widget, tk.Text):
                    data[key] = widget.get("1.0", "end-1c").strip()
                elif isinstance(widget, tkcal.DateEntry):
                    data[key] = widget.get_date().strftime('%Y-%m-%d')
                else:
                    data[key] = widget.get().strip()
            
            # Define required fields - UPDATED: post_code is NOT required
            required_fields = ['firm_type', 'firm_name', 'email', 'phone', 
                             'address', 'city_town', 'business_start_date', 'country']
            
            # Validate required fields
            missing_fields = []
            for field in required_fields:
                if not data.get(field):
                    missing_fields.append(field.replace('_', ' ').title())
                    self.highlight_field(field)
            
            if missing_fields:
                messagebox.showerror("Validation Error", 
                                    f"Please fill in the following required fields:\n\n" +
                                    "\n".join(f"• {field}" for field in missing_fields))
                return
            
            # Validate email format
            if data['email'] and '@' not in data['email']:
                messagebox.showerror("Validation Error", 
                                    "Please enter a valid email address.")
                self.highlight_field('email')
                return
            
            # Validate phone number
            if data['phone'] and not data['phone'].replace(' ', '').replace('-', '').replace('+', '').isdigit():
                messagebox.showerror("Validation Error", 
                                    "Please enter a valid phone number.")
                self.highlight_field('phone')
                return
            
            # Connect to database
            conn = sqlite3.connect('Possystem.db')
            cursor = conn.cursor()
            
            # Check if data already exists
            cursor.execute("SELECT COUNT(*) FROM firm_details")
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Update existing record
                cursor.execute('''
                UPDATE firm_details SET
                firm_type = ?,
                firm_name = ?,
                email = ?,
                phone = ?,
                address = ?,
                city_town = ?,
                post_code = ?,
                website = ?,
                business_start_date = ?,
                book_start_date = ?,
                year_end = ?,
                country = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT MIN(id) FROM firm_details)
                ''', tuple(data.values()))
                
                # Log the update in history
                cursor.execute('''
                INSERT INTO firm_history (firm_details_id, change_type, change_details)
                VALUES ((SELECT id FROM firm_details LIMIT 1), 'UPDATE', 'Firm details updated')
                ''')
                
                action = "updated"
            else:
                # Insert new record
                cursor.execute('''
                INSERT INTO firm_details 
                (firm_type, firm_name, email, phone, address, city_town, 
                 post_code, website, business_start_date, book_start_date, 
                 year_end, country)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(data.values()))
                
                # Get the inserted ID
                last_id = cursor.lastrowid
                
                # Log the creation in history
                cursor.execute('''
                INSERT INTO firm_history (firm_details_id, change_type, change_details)
                VALUES (?, 'CREATE', 'New firm details created')
                ''', (last_id,))
                
                action = "saved"
            
            conn.commit()
            conn.close()
            
            # Show success message
            messagebox.showinfo("Success", 
                              f"✓ Firm details {action} successfully!\n\n"
                              f"Data has been stored in the database.")
            
            # Ask if user wants to clear the form after saving
            clear_after_save = messagebox.askyesno("Clear Form", 
                                                  "Do you want to clear the form for new entry?")
            if clear_after_save:
                self.clear_form()
            
        except Exception as e:
            messagebox.showerror("Database Error", 
                               f"An error occurred while saving data:\n{str(e)}")
    
    def highlight_field(self, field_name):
        """Highlight a field with error color"""
        widget = self.fields.get(field_name)
        if widget:
            if isinstance(widget, tk.Text):
                widget.configure(bg='#ffebee', highlightbackground=self.color_scheme['error'])
                self.root.after(3000, lambda: widget.configure(bg='white', highlightbackground=self.color_scheme['border']))
            elif isinstance(widget, ttk.Entry):
                widget.configure(style='Custom.TEntry')
            elif isinstance(widget, tkcal.DateEntry):
                original_bg = widget.cget('background')
                widget.configure(background=self.color_scheme['error'])
                self.root.after(3000, lambda: widget.configure(background=original_bg))
    
    def clear_form(self):
        """Clear all form fields"""
        confirm = messagebox.askyesno("Clear Form", 
                                     "Are you sure you want to clear all form fields?")
        if confirm:
            for key, widget in self.fields.items():
                if isinstance(widget, tk.Text):
                    widget.delete("1.0", "end")
                elif isinstance(widget, tkcal.DateEntry):
                    # Set to current date
                    widget.set_date(datetime.now())
                else:
                    widget.delete(0, "end")
            messagebox.showinfo("Form Cleared", "All form fields have been cleared.")
    
    def load_existing_data(self):
        """Load existing firm details from database"""
        try:
            conn = sqlite3.connect('Possystem.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM firm_details ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                # Column indices
                indices = {
                    'firm_type': 1,
                    'firm_name': 2,
                    'email': 3,
                    'phone': 4,
                    'address': 5,
                    'city_town': 6,
                    'post_code': 7,
                    'website': 8,
                    'business_start_date': 9,
                    'book_start_date': 10,
                    'year_end': 11,
                    'country': 12
                }
                
                for key, idx in indices.items():
                    if key in self.fields and row[idx]:
                        widget = self.fields[key]
                        
                        if isinstance(widget, tk.Text):
                            widget.delete("1.0", "end")
                            widget.insert("1.0", row[idx])
                        elif isinstance(widget, tkcal.DateEntry):
                            try:
                                date_obj = datetime.strptime(row[idx], '%Y-%m-%d')
                                widget.set_date(date_obj)
                            except:
                                pass
                        else:
                            widget.delete(0, "end")
                            widget.insert(0, row[idx])
                
                messagebox.showinfo("Data Loaded", "✓ Existing firm details loaded successfully!")
            else:
                messagebox.showinfo("No Data", "No existing firm details found in the database.")
            
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Load Error", 
                               f"An error occurred while loading data:\n{str(e)}")
    
    def generate_report(self):
        """Generate PDF historical report"""
        try:
            # Connect to database first to check if data exists
            conn = sqlite3.connect('Possystem.db')
            cursor = conn.cursor()
            
            # Get firm details
            cursor.execute("SELECT * FROM firm_details ORDER BY id DESC LIMIT 1")
            firm_data = cursor.fetchone()
            
            if not firm_data:
                messagebox.showwarning("No Data", "No firm details found. Please save firm details first.")
                conn.close()
                return
            
            conn.close()
            
            # Ask user where to save the PDF
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Historical Report As",
                initialfile=f"Firm_Details_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not filename:
                return  # User cancelled
            
            # Get history
            conn = sqlite3.connect('Possystem.db')
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT change_type, change_details, changed_at 
            FROM firm_history 
            WHERE firm_details_id = (SELECT id FROM firm_details LIMIT 1)
            ORDER BY changed_at DESC
            ''')
            history_data = cursor.fetchall()
            
            conn.close()
            
            # Create PDF
            self.create_pdf_report(filename, firm_data, history_data)
            
            # Ask if user wants to open the PDF
            open_pdf = messagebox.askyesno("Report Generated", 
                                          "✓ Historical report has been generated successfully!\n\n"
                                          "Do you want to open the PDF file?")
            
            if open_pdf:
                webbrowser.open(filename)
                
        except Exception as e:
            messagebox.showerror("Report Error", 
                               f"An error occurred while generating the report:\n{str(e)}")
    
    def create_pdf_report(self, filename, firm_data, history_data):
        """Create PDF report with firm details and history"""
        # Create the PDF document
        doc = SimpleDocTemplate(filename, pagesize=A4, 
                               topMargin=0.5*inch, bottomMargin=0.75*inch)
        
        # Container for the flowables
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles with banking colors
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor(self.color_scheme['primary']),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor(self.color_scheme['primary']),
            spaceAfter=10
        )
        
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=5
        )
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=TA_CENTER
        )
        
        # Title
        title = Paragraph("FIRM DETAILS HISTORICAL REPORT", title_style)
        elements.append(title)
        
        # Date of report
        report_date = Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}", normal_style)
        elements.append(report_date)
        elements.append(Spacer(1, 20))
        
        # Firm Details Section
        firm_heading = Paragraph("Firm Details", heading_style)
        elements.append(firm_heading)
        
        # Prepare firm data table
        firm_table_data = [
            ["Field", "Value"],
            ["Firm Type", firm_data[1] or "Not Provided"],
            ["Firm Name", firm_data[2] or "Not Provided"],
            ["Email", firm_data[3] or "Not Provided"],
            ["Phone", firm_data[4] or "Not Provided"],
            ["Address", firm_data[5] or "Not Provided"],
            ["City/Town", firm_data[6] or "Not Provided"],
            ["Post Code", firm_data[7] or "Not Provided"],
            ["Website", firm_data[8] or "Not Provided"],
            ["Business Start Date", firm_data[9] or "Not Provided"],
            ["Book Start Date", firm_data[10] or "Not Provided"],
            ["Year End", firm_data[11] or "Not Provided"],
            ["Country", firm_data[12] or "Not Provided"],
            ["Created", firm_data[13]],
            ["Last Updated", firm_data[14] if len(firm_data) > 14 else "N/A"]
        ]
        
        firm_table = Table(firm_table_data, colWidths=[2.5*inch, 4*inch])
        firm_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.color_scheme['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(self.color_scheme['border'])),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(firm_table)
        elements.append(Spacer(1, 30))
        
        # History Section
        if history_data:
            history_heading = Paragraph("Change History", heading_style)
            elements.append(history_heading)
            
            # Prepare history table
            history_table_data = [["Change Type", "Details", "Date & Time"]]
            
            for record in history_data:
                history_table_data.append([
                    record[0],
                    record[1],
                    record[2]
                ])
            
            history_table = Table(history_table_data, colWidths=[1.5*inch, 3*inch, 2*inch])
            history_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.color_scheme['secondary'])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(self.color_scheme['border'])),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(history_table)
        else:
            no_history = Paragraph("No history available for this firm.", normal_style)
            elements.append(no_history)
        
        # Build the PDF
        doc.build(elements, onFirstPage=self.add_footer, onLaterPages=self.add_footer)
    
    def add_footer(self, canvas, doc):
        """Add footer to each page"""
        # Save the state of the canvas
        canvas.saveState()
        
        # Footer text
        footer_text = "Software produced by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363"
        
        # Set font and color
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor(self.color_scheme['text_dark']))
        
        # Draw footer text
        canvas.drawCentredString(A4[0]/2, 0.4*inch, footer_text)
        
        # Add page number
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(A4[0]/2, 0.2*inch, f"Page {page_num}")
        
        # Restore the canvas state
        canvas.restoreState()
    
    def on_closing(self):
        """Handle window closing"""
        self.root.destroy()

# For testing the module directly
if __name__ == "__main__":
    root = tk.Tk()
    app = MyFirmDetails(root)
    root.mainloop()