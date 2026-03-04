# Sales.py
from tkinter import *
from tkinter import ttk, messagebox
import sqlite3
import datetime
from datetime import date, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus.flowables import Flowable
import os
from tkinter import filedialog
import warnings
import time
import traceback
warnings.filterwarnings('ignore')

class FooterCanvas(Flowable):
    """Custom footer for PDF pages"""
    def __init__(self, width):
        Flowable.__init__(self)
        self.width = width
    
    def draw(self):
        self.canv.saveState()
        
        # Set font and size
        self.canv.setFont("Helvetica", 8)
        self.canv.setFillColor(colors.HexColor("#666666"))
        
        # Draw footer text
        footer_text = "Software produced by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363"
        self.canv.drawCentredString(self.width / 2.0, 0.25 * inch, footer_text)
        
        self.canv.restoreState()

class SalesClass:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1300x700+200+100")
        self.root.title("Sales Analytics Dashboard | Inventory Management System")
        self.root.config(bg="#f0f0f0")
        self.root.focus_force()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set minimum window size
        self.root.minsize(1200, 700)
        
        # =========== Variables ==========
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.selected_invoice_id = None
        self.report_data = []
        self.sort_directions = {}
        self.radio_buttons = []  # Store radio button references for hover effects
        self.after_ids = []  # Track after callbacks
        self.is_closing = False  # Flag to prevent callbacks during close
        
        # Database connection
        self.db_path = r'Possystem.db'
        self.conn = None
        self.cursor = None
        
        # Professional Color Scheme
        self.bg_color = "#f8f9fa"
        self.card_bg = "#ffffff"
        self.accent_color = "#2c3e50"
        self.success_color = "#27ae60"
        self.warning_color = "#f39c12"
        self.danger_color = "#e74c3c"
        self.info_color = "#3498db"
        self.text_color = "#2c3e50"
        self.subtext_color = "#7f8c8d"
        self.border_color = "#d5dbdb"
        self.header_bg = "#34495e"
        self.hover_color = "#e3f2fd"  # Light blue hover color
        
        # Configure root background
        self.root.config(bg=self.bg_color)
        
        # =========== Main Container ==========
        self.main_container = Frame(self.root, bg=self.bg_color)
        self.main_container.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # =========== Header with Date/Time ==========
        header_frame = Frame(self.main_container, bg=self.header_bg, height=80)
        header_frame.pack(fill=X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Title
        title_frame = Frame(header_frame, bg=self.header_bg)
        title_frame.pack(side=LEFT, fill=Y, padx=20)
        
        Label(title_frame, text="📊 SALES ANALYTICS DASHBOARD", 
              font=("Segoe UI", 22, "bold"), bg=self.header_bg, 
              fg="white").pack(pady=20)
        
        # Live Date and Time
        time_frame = Frame(header_frame, bg=self.header_bg)
        time_frame.pack(side=RIGHT, fill=Y, padx=20)
        
        self.date_time_label = Label(time_frame, text="", 
                                    font=("Segoe UI", 11), 
                                    bg=self.header_bg, fg="white")
        self.date_time_label.pack(pady=20)
        
        # =========== Quick Stats Cards ==========
        self.stats_container = Frame(self.main_container, bg=self.bg_color)
        self.stats_container.pack(fill=X, pady=(0, 20))
        
        # Create stats grid
        for i in range(4):
            self.stats_container.grid_columnconfigure(i, weight=1, uniform="stats")
        
        # Today's Sales Card
        self.today_card = self.create_stat_card(self.stats_container, "💰 TODAY'S SALES", "PKR 0.00", 
                                              self.success_color)
        self.today_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Weekly Sales Card
        self.weekly_card = self.create_stat_card(self.stats_container, "📈 WEEKLY SALES", "PKR 0.00", 
                                               self.info_color)
        self.weekly_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Monthly Sales Card
        self.monthly_card = self.create_stat_card(self.stats_container, "📊 MONTHLY SALES", "PKR 0.00", 
                                                self.warning_color)
        self.monthly_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        # Total Invoices Card
        self.invoices_card = self.create_stat_card(self.stats_container, "📋 TOTAL INVOICES", "0", 
                                                 self.accent_color)
        self.invoices_card.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        
        # =========== Main Content Area ==========
        self.content_frame = Frame(self.main_container, bg=self.bg_color)
        self.content_frame.pack(fill=BOTH, expand=True)
        
        # Configure grid for content area
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=2)
        
        # =========== Left Panel - Daily Invoices ==========
        self.left_panel = Frame(self.content_frame, bg=self.card_bg, bd=1, relief="solid",
                          highlightbackground=self.border_color, highlightthickness=1)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Header for Daily Invoices
        invoice_header = Frame(self.left_panel, bg=self.accent_color, height=50)
        invoice_header.pack(fill=X)
        invoice_header.pack_propagate(False)
        
        Label(invoice_header, text="📋 DAILY INVOICES", font=("Segoe UI", 14, "bold"), 
              bg=self.accent_color, fg="white").pack(pady=13)
        
        # Date selection and Search
        search_frame = Frame(self.left_panel, bg=self.card_bg)
        search_frame.pack(fill=X, padx=15, pady=15)
        
        # Date selection
        date_frame = Frame(search_frame, bg=self.card_bg)
        date_frame.pack(fill=X, pady=(0, 10))
        
        Label(date_frame, text="Select Date:", font=("Segoe UI", 11), 
              bg=self.card_bg, fg=self.text_color).pack(side=LEFT, padx=(0, 10))
        
        self.date_var = StringVar(value=self.current_date)
        self.date_entry = Entry(date_frame, textvariable=self.date_var, 
                               font=("Segoe UI", 10), width=15,
                               relief="solid", bd=1)
        self.date_entry.pack(side=LEFT, padx=(0, 10))
        
        Button(date_frame, text="📅 Today", command=self.set_today_date,
               font=("Segoe UI", 9), bg=self.info_color, fg="white",
               cursor="hand2", relief="flat", padx=12, pady=4).pack(side=LEFT)
        
        Button(date_frame, text="🔍 Load", command=self.load_daily_invoices,
               font=("Segoe UI", 9), bg=self.success_color, fg="white",
               cursor="hand2", relief="flat", padx=12, pady=4).pack(side=LEFT, padx=(5, 0))
        
        # Search section
        search_input_frame = Frame(search_frame, bg=self.card_bg)
        search_input_frame.pack(fill=X, pady=(10, 0))
        
        Label(search_input_frame, text="Search:", font=("Segoe UI", 11), 
              bg=self.card_bg, fg=self.text_color).pack(side=LEFT, padx=(0, 10))
        
        self.search_var = StringVar()
        self.search_entry = Entry(search_input_frame, textvariable=self.search_var,
                                 font=("Segoe UI", 10), width=25,
                                 relief="solid", bd=1)
        self.search_entry.pack(side=LEFT, padx=(0, 10))
        
        # Bind search events
        self.search_entry.bind("<KeyRelease>", self.search_invoices)
        
        # Search button
        Button(search_input_frame, text="🔍 Search", command=self.search_invoices,
               font=("Segoe UI", 9), bg=self.accent_color, fg="white",
               cursor="hand2", relief="flat", padx=12, pady=4).pack(side=LEFT)
        
        # Invoice list container
        list_container = Frame(self.left_panel, bg=self.card_bg)
        list_container.pack(fill=BOTH, expand=True, padx=15, pady=(0, 10))
        
        # Treeview for invoices
        tree_frame = Frame(list_container, bg=self.card_bg)
        tree_frame.pack(fill=BOTH, expand=True)
        
        # Create scrollbars
        scroll_y = Scrollbar(tree_frame, orient=VERTICAL)
        scroll_x = Scrollbar(tree_frame, orient=HORIZONTAL)
        
        # Create Treeview with sortable columns
        self.invoice_tree = ttk.Treeview(tree_frame, 
                                         columns=("Invoice", "Amount", "Customer", "Time"), 
                                         show="headings", 
                                         yscrollcommand=scroll_y.set,
                                         xscrollcommand=scroll_x.set,
                                         height=8)
        
        # Configure scrollbars
        scroll_y.config(command=self.invoice_tree.yview)
        scroll_x.config(command=self.invoice_tree.xview)
        
        # Define columns with sort functionality
        columns = [
            ("Invoice", "Invoice No.", 100, self.sort_invoice_tree),
            ("Amount", "Amount (PKR)", 100, self.sort_invoice_tree),
            ("Customer", "Customer", 120, self.sort_invoice_tree),
            ("Time", "Time", 80, self.sort_invoice_tree)
        ]
        
        for col_id, heading, width, sort_func in columns:
            self.invoice_tree.heading(col_id, text=heading, command=lambda c=col_id: sort_func(c))
            self.invoice_tree.column(col_id, width=width, minwidth=70)
            self.sort_directions[col_id] = False
        
        # Pack treeview and scrollbars
        self.invoice_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)
        scroll_x.pack(side=BOTTOM, fill=X)
        
        # Bind selection event
        self.invoice_tree.bind('<<TreeviewSelect>>', self.on_invoice_select)
        
        # Action buttons frame
        self.action_frame = Frame(self.left_panel, bg=self.card_bg)
        self.action_frame.pack(fill=X, padx=15, pady=(0, 15))
        
        Button(self.action_frame, text="📄 View Details", command=self.view_invoice_details,
               font=("Segoe UI", 10), bg=self.accent_color, fg="white",
               cursor="hand2", relief="flat", padx=15, pady=6).pack(side=LEFT, padx=(0, 10))
        
        Button(self.action_frame, text="🖨️ Print Invoice", command=self.print_invoice,
               font=("Segoe UI", 10), bg=self.warning_color, fg="white",
               cursor="hand2", relief="flat", padx=15, pady=6).pack(side=LEFT)
        
        # =========== Right Panel - Reports ==========
        self.right_panel = Frame(self.content_frame, bg=self.card_bg, bd=1, relief="solid",
                           highlightbackground=self.border_color, highlightthickness=1)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Report controls
        control_frame = Frame(self.right_panel, bg=self.card_bg)
        control_frame.pack(fill=X, padx=20, pady=20)
        
        Label(control_frame, text="📊 REPORT GENERATOR", font=("Segoe UI", 14, "bold"),
              bg=self.card_bg, fg=self.text_color).pack(anchor="w", pady=(0, 15))
        
        # Report type selection
        type_frame = Frame(control_frame, bg=self.card_bg)
        type_frame.pack(fill=X, pady=(0, 15))
        
        Label(type_frame, text="Report Type:", font=("Segoe UI", 11),
              bg=self.card_bg, fg=self.text_color).pack(side=LEFT, padx=(0, 15))
        
        self.report_type = StringVar(value="daily")
        report_options = [
            ("Daily", "daily"),
            ("Weekly", "weekly"), 
            ("Monthly", "monthly"),
            ("Custom Range", "custom")
        ]
        
        for text, value in report_options:
            # Create a frame for each radio button to enable hover effect
            rb_frame = Frame(type_frame, bg=self.card_bg)
            rb_frame.pack(side=LEFT, padx=(0, 15))
            
            # Create the radio button
            rb = Radiobutton(rb_frame, text=text, variable=self.report_type,
                           value=value, font=("Segoe UI", 10),
                           bg=self.card_bg, fg=self.text_color, 
                           activebackground=self.card_bg,
                           activeforeground=self.accent_color,
                           selectcolor=self.accent_color,
                           command=self.on_report_type_change)
            rb.pack()
            
            # Add hover effects
            rb.bind("<Enter>", lambda e, f=rb_frame: self.on_radio_hover(e, f))
            rb.bind("<Leave>", lambda e, f=rb_frame: self.on_radio_leave(e, f))
            
            # Also bind to the frame for better hover area
            rb_frame.bind("<Enter>", lambda e, f=rb_frame: self.on_radio_hover(e, f))
            rb_frame.bind("<Leave>", lambda e, f=rb_frame: self.on_radio_leave(e, f))
            
            # Store reference for hover effects
            self.radio_buttons.append((rb, rb_frame))
        
        # Date range for custom reports
        self.custom_frame = Frame(control_frame, bg=self.card_bg)
        
        Label(self.custom_frame, text="From:", font=("Segoe UI", 10),
              bg=self.card_bg, fg=self.text_color).pack(side=LEFT, padx=(0, 5))
        
        self.start_date = Entry(self.custom_frame, font=("Segoe UI", 10), 
                               width=12, relief="solid", bd=1)
        self.start_date.insert(0, self.current_date)
        self.start_date.pack(side=LEFT, padx=(0, 15))
        
        Label(self.custom_frame, text="To:", font=("Segoe UI", 10),
              bg=self.card_bg, fg=self.text_color).pack(side=LEFT, padx=(0, 5))
        
        self.end_date = Entry(self.custom_frame, font=("Segoe UI", 10), 
                             width=12, relief="solid", bd=1)
        self.end_date.insert(0, self.current_date)
        self.end_date.pack(side=LEFT)
        
        self.custom_frame.pack_forget()
        
        # Action buttons for reports
        button_frame = Frame(control_frame, bg=self.card_bg)
        button_frame.pack(fill=X, pady=(10, 0))
        
        Button(button_frame, text="📊 Generate Report", command=self.generate_report,
               font=("Segoe UI", 10), bg=self.success_color, fg="white",
               cursor="hand2", relief="flat", padx=15, pady=6).pack(side=LEFT, padx=(0, 10))
        
        Button(button_frame, text="📈 Export to Excel", command=self.export_to_excel,
               font=("Segoe UI", 10), bg="#217346", fg="white",
               cursor="hand2", relief="flat", padx=15, pady=6).pack(side=LEFT, padx=(0, 10))
        
        Button(button_frame, text="📄 Export to PDF", command=self.export_to_pdf,
               font=("Segoe UI", 10), bg="#d32f2f", fg="white",
               cursor="hand2", relief="flat", padx=15, pady=6).pack(side=LEFT, padx=(0, 10))
        
        # NEW: Clients button
        Button(button_frame, text="👥 Clients", command=self.export_clients_pdf,
               font=("Segoe UI", 10), bg="#6c5ce7", fg="white",
               cursor="hand2", relief="flat", padx=15, pady=6).pack(side=LEFT)
        
        # =========== Report Display Area - ONLY TABLE VIEW ==========
        self.display_frame = Frame(self.right_panel, bg=self.card_bg)
        self.display_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Simple label for report view
        report_label_frame = Frame(self.display_frame, bg=self.card_bg)
        report_label_frame.pack(fill=X, pady=(0, 10))
        
        Label(report_label_frame, text="📋 REPORT DATA", font=("Segoe UI", 12, "bold"),
              bg=self.card_bg, fg=self.text_color).pack(anchor="w")
        
        # Treeview for report data
        report_tree_frame = Frame(self.display_frame, bg=self.card_bg)
        report_tree_frame.pack(fill=BOTH, expand=True)
        
        # Create scrollbars for report tree
        scroll_y2 = Scrollbar(report_tree_frame, orient=VERTICAL)
        scroll_x2 = Scrollbar(report_tree_frame, orient=HORIZONTAL)
        
        self.report_tree = ttk.Treeview(report_tree_frame, 
                                        columns=("Date", "Invoice", "Amount", "Items", "Customer", "Time"), 
                                        show="headings", 
                                        yscrollcommand=scroll_y2.set,
                                        xscrollcommand=scroll_x2.set,
                                        height=6)
        
        scroll_y2.config(command=self.report_tree.yview)
        scroll_x2.config(command=self.report_tree.xview)
        
        # Define columns for report with sort functionality
        report_columns = [
            ("Date", "📅 Date", 100, self.sort_report_tree),
            ("Invoice", "📄 Invoice No.", 120, self.sort_report_tree),
            ("Amount", "💰 Amount (PKR)", 120, self.sort_report_tree),
            ("Items", "🛒 Items", 80, self.sort_report_tree),
            ("Customer", "👤 Customer", 150, self.sort_report_tree),
            ("Time", "⏰ Time", 100, self.sort_report_tree)
        ]
        
        for col_id, heading, width, sort_func in report_columns:
            self.report_tree.heading(col_id, text=heading, command=lambda c=col_id: sort_func(c))
            self.report_tree.column(col_id, width=width, minwidth=80)
            self.sort_directions[f"report_{col_id}"] = False
        
        # Pack report treeview and scrollbars
        self.report_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y2.pack(side=RIGHT, fill=Y)
        scroll_x2.pack(side=BOTTOM, fill=X)
        
        # =========== Footer ==========
        self.footer_frame = Frame(self.main_container, bg=self.accent_color, height=40)
        self.footer_frame.pack(side=BOTTOM, fill=X, pady=(10, 0))
        self.footer_frame.pack_propagate(False)
        
        self.status_label = Label(self.footer_frame, text="Ready", font=("Segoe UI", 9),
                                 bg=self.accent_color, fg="white")
        self.status_label.pack(side=LEFT, padx=20, pady=10)
        
        self.time_label = Label(self.footer_frame, text="", font=("Segoe UI", 9),
                               bg=self.accent_color, fg="white")
        self.time_label.pack(side=RIGHT, padx=20, pady=10)
        
        # =========== Initialize ==========
        self.load_daily_invoices()
        self.update_quick_stats()
        self.safe_after(100, self.update_date_time)
        self.safe_after(100, self.update_time)
    
    # =========== UTILITY METHODS ===========
    
    def safe_after(self, delay_ms, callback, *args):
        """Safely schedule an after callback"""
        if self.is_closing:
            return None
            
        def safe_callback():
            if not self.is_closing and self.root.winfo_exists():
                try:
                    callback(*args)
                except Exception as e:
                    print(f"Callback error: {e}")
        
        after_id = self.root.after(delay_ms, safe_callback)
        self.after_ids.append(after_id)
        return after_id
    
    def on_close(self):
        """Handle window close event"""
        self.is_closing = True
        self.cleanup()
        self.root.destroy()
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up resources...")
        
        # Cancel all after callbacks
        for after_id in self.after_ids:
            try:
                self.root.after_cancel(after_id)
            except:
                pass
        
        # Close database connection
        if self.conn:
            try:
                self.conn.close()
                print("Database connection closed")
            except:
                pass
        
        print("Cleanup complete")
    
    def get_db_connection(self):
        """Get database connection with error handling"""
        try:
            if self.conn is None:
                self.conn = sqlite3.connect(self.db_path)
                self.cursor = self.conn.cursor()
            return self.conn, self.cursor
        except Exception as e:
            messagebox.showerror("Database Error", 
                                f"Cannot connect to database:\n{str(e)}")
            return None, None
    
    def validate_date(self, date_text):
        """Validate date format"""
        try:
            datetime.datetime.strptime(date_text, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    def sanitize_input(self, text):
        """Sanitize user input for SQL queries"""
        dangerous_patterns = ["--", ";", "/*", "*/", "'", '"', "DROP", "DELETE", "INSERT", "UPDATE"]
        for pattern in dangerous_patterns:
            text = text.replace(pattern, "")
        return text.strip()
    
    # =========== UI COMPONENT METHODS ===========
    
    def on_radio_hover(self, event, frame):
        """Handle mouse hover on radio button"""
        frame.config(bg=self.hover_color)
        for widget in frame.winfo_children():
            if isinstance(widget, Radiobutton):
                widget.config(bg=self.hover_color)
    
    def on_radio_leave(self, event, frame):
        """Handle mouse leave from radio button"""
        frame.config(bg=self.card_bg)
        for widget in frame.winfo_children():
            if isinstance(widget, Radiobutton):
                widget.config(bg=self.card_bg)
    
    def create_stat_card(self, parent, title, value, color):
        """Create a professional statistics card"""
        card = Frame(parent, bg=self.card_bg, bd=0, highlightbackground=self.border_color,
                    highlightthickness=1, relief="solid")
        
        # Content frame
        content = Frame(card, bg=self.card_bg)
        content.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # Title
        Label(content, text=title, font=("Segoe UI", 10), 
              bg=self.card_bg, fg=self.subtext_color, anchor="w").pack(anchor="w", pady=(0, 8))
        
        # Value
        value_label = Label(content, text=value, font=("Segoe UI", 18, "bold"),
                           bg=self.card_bg, fg=self.text_color, anchor="w")
        value_label.pack(anchor="w")
        
        # Colored accent bar at bottom
        accent_bar = Frame(card, bg=color, height=4)
        accent_bar.pack(side=BOTTOM, fill=X)
        
        # Store reference to update later
        if "today" in title.lower():
            self.today_sales_label = value_label
        elif "weekly" in title.lower():
            self.weekly_sales_label = value_label
        elif "monthly" in title.lower():
            self.monthly_sales_label = value_label
        elif "invoice" in title.lower():
            self.total_invoices_label = value_label
        
        return card
    
    # =========== SORTING METHODS ===========
    
    def sort_invoice_tree(self, column):
        """Sort invoice treeview by column"""
        try:
            items = [(self.invoice_tree.set(item, column), item) for item in self.invoice_tree.get_children('')]
            
            if column == "Amount":
                items.sort(key=lambda x: float(x[0].replace('PKR ', '').replace(',', '')) if 'PKR' in x[0] else 0, 
                          reverse=self.sort_directions[column])
            elif column == "Invoice":
                items.sort(key=lambda x: int(''.join(filter(str.isdigit, x[0]))) if any(c.isdigit() for c in x[0]) else 0,
                          reverse=self.sort_directions[column])
            else:
                items.sort(key=lambda x: x[0].lower(), reverse=self.sort_directions[column])
            
            for index, (_, item) in enumerate(items):
                self.invoice_tree.move(item, '', index)
            
            self.sort_directions[column] = not self.sort_directions[column]
        except Exception as e:
            print(f"Error sorting invoice tree: {e}")
    
    def sort_report_tree(self, column):
        """Sort report treeview by column"""
        try:
            all_items = list(self.report_tree.get_children(''))
            
            regular_items = []
            total_item = None
            
            for item in all_items:
                values = self.report_tree.item(item)['values']
                if values and values[0] == "TOTAL":
                    total_item = item
                else:
                    regular_items.append(item)
            
            items_data = [(self.report_tree.set(item, column), item) for item in regular_items]
            
            if column == "Amount":
                items_data.sort(key=lambda x: float(x[0].replace('PKR ', '').replace(',', '')) if 'PKR' in x[0] else 0,
                              reverse=self.sort_directions[f"report_{column}"])
            elif column == "Date":
                items_data.sort(key=lambda x: x[0], reverse=self.sort_directions[f"report_{column}"])
            elif column == "Invoice":
                items_data.sort(key=lambda x: int(''.join(filter(str.isdigit, x[0]))) if any(c.isdigit() for c in x[0]) else 0,
                              reverse=self.sort_directions[f"report_{column}"])
            else:
                items_data.sort(key=lambda x: x[0].lower(), reverse=self.sort_directions[f"report_{column}"])
            
            for index, (_, item) in enumerate(items_data):
                self.report_tree.move(item, '', index)
            
            if total_item:
                self.report_tree.move(total_item, '', len(regular_items))
            
            self.sort_directions[f"report_{column}"] = not self.sort_directions[f"report_{column}"]
        except Exception as e:
            print(f"Error sorting report tree: {e}")
    
    # =========== INVOICE METHODS ===========
    
    def search_invoices(self, event=None):
        """Search invoices by invoice number"""
        search_text = self.search_var.get().strip()
        
        if not search_text:
            self.load_daily_invoices()
            return
        
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Clear existing items
            self.invoice_tree.delete(*self.invoice_tree.get_children())
            
            # Search by invoice number
            cur.execute('''
                SELECT invoice_no, total_amount, customer_name, 
                       strftime('%H:%M', created_at) as time
                FROM invoices 
                WHERE invoice_no LIKE ? 
                ORDER BY created_at DESC
            ''', (f'%{search_text}%',))
            
            invoices = cur.fetchall()
            
            if invoices:
                total_amount = 0
                for invoice in invoices:
                    invoice_no, amount, customer, time = invoice
                    total_amount += amount if amount else 0
                    
                    self.invoice_tree.insert("", END, values=(
                        invoice_no,
                        f"PKR {amount:,.2f}" if amount else "PKR 0.00",
                        customer or "Walk-in Customer",
                        time
                    ))
                
                self.status_label.config(text=f"Found {len(invoices)} invoices | Total: PKR {total_amount:,.2f}")
            else:
                self.status_label.config(text=f"No invoices found for '{search_text}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search invoices: {str(e)}")
            self.status_label.config(text="Error searching invoices")
    
    def set_today_date(self):
        """Set date to today"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.date_var.set(today)
        self.load_daily_invoices()
    
    def load_daily_invoices(self):
        """Load invoices for selected date"""
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            selected_date = self.date_var.get()
            
            # Clear existing items
            self.invoice_tree.delete(*self.invoice_tree.get_children())
            
            # Query for invoices on selected date
            cur.execute('''
                SELECT invoice_no, total_amount, customer_name, 
                       strftime('%H:%M', created_at) as time
                FROM invoices 
                WHERE DATE(created_at) = ?
                ORDER BY created_at DESC
            ''', (selected_date,))
            
            invoices = cur.fetchall()
            
            if invoices:
                total_amount = 0
                for invoice in invoices:
                    invoice_no, amount, customer, time = invoice
                    total_amount += amount if amount else 0
                    
                    self.invoice_tree.insert("", END, values=(
                        invoice_no,
                        f"PKR {amount:,.2f}" if amount else "PKR 0.00",
                        customer or "Walk-in Customer",
                        time
                    ))
                
                self.status_label.config(text=f"Loaded {len(invoices)} invoices | Total: PKR {total_amount:,.2f}")
            else:
                self.status_label.config(text=f"No invoices found for {selected_date}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load invoices: {str(e)}")
            self.status_label.config(text="Error loading invoices")
    
    def on_invoice_select(self, event):
        """Handle invoice selection"""
        selection = self.invoice_tree.selection()
        if selection:
            values = self.invoice_tree.item(selection[0])['values']
            if values:
                self.selected_invoice_id = values[0]  # Invoice number
    
    def view_invoice_details(self):
        """View detailed invoice information"""
        if not self.selected_invoice_id:
            messagebox.showinfo("Info", "Please select an invoice first")
            return
        
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Get all invoice details
            cur.execute('''
                SELECT invoice_id, invoice_no, total_amount, tax_amount, 
                       subtotal_amount, customer_name, customer_contact,
                       invoice_date, invoice_time, created_at
                FROM invoices 
                WHERE invoice_no = ?
            ''', (self.selected_invoice_id,))
            
            invoice_data = cur.fetchone()
            
            if not invoice_data:
                messagebox.showerror("Error", "Invoice not found")
                return
            
            # Get invoice items
            cur.execute('''
                SELECT product_name, quantity, price, total
                FROM invoice_items
                WHERE invoice_id = ?
            ''', (invoice_data[0],))
            
            items_data = cur.fetchall()
            
            # Create detail window
            detail_win = Toplevel(self.root)
            detail_win.title(f"Invoice Details - #{self.selected_invoice_id}")
            detail_win.geometry("900x700")
            detail_win.config(bg=self.card_bg)
            detail_win.resizable(True, True)
            
            # Make window modal
            detail_win.transient(self.root)
            detail_win.grab_set()
            
            # Create main container
            main_container = Frame(detail_win, bg=self.card_bg)
            main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            # Header
            header = Frame(main_container, bg=self.accent_color, height=60)
            header.pack(fill=X, pady=(0, 20))
            header.pack_propagate(False)
            
            Label(header, text=f"INVOICE DETAILS - #{self.selected_invoice_id}", 
                  font=("Segoe UI", 16, "bold"), bg=self.accent_color, fg="white").pack(pady=15)
            
            # Create content frame with scrollbar
            content_container = Frame(main_container, bg=self.card_bg)
            content_container.pack(fill=BOTH, expand=True)
            
            # Create canvas and scrollbar
            canvas = Canvas(content_container, bg=self.card_bg, highlightthickness=0)
            scrollbar = Scrollbar(content_container, orient=VERTICAL, command=canvas.yview)
            scrollable_frame = Frame(canvas, bg=self.card_bg)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # Content area
            content = Frame(scrollable_frame, bg=self.card_bg)
            content.pack(fill=BOTH, expand=True, padx=30, pady=20)
            
            # Invoice Details Section
            details_frame = Frame(content, bg=self.card_bg, relief="solid", bd=1)
            details_frame.pack(fill=X, pady=(0, 20))
            
            Label(details_frame, text="📋 INVOICE INFORMATION", 
                  font=("Segoe UI", 14, "bold"), bg=self.accent_color, fg="white").pack(fill=X, pady=10)
            
            # Create details grid
            details_grid = Frame(details_frame, bg=self.card_bg)
            details_grid.pack(fill=X, padx=20, pady=15)
            
            # Invoice details in two columns
            invoice_details = [
                ("Invoice No:", invoice_data[1]),
                ("Customer Name:", invoice_data[5] or "Walk-in Customer"),
                ("Customer Contact:", invoice_data[6] or "N/A"),
                ("Invoice Date:", invoice_data[7]),
                ("Invoice Time:", invoice_data[8]),
                ("Created At:", invoice_data[9]),
                ("Subtotal:", f"PKR {invoice_data[4]:,.2f}" if invoice_data[4] else "PKR 0.00"),
                ("Tax Amount:", f"PKR {invoice_data[3]:,.2f}" if invoice_data[3] else "PKR 0.00"),
                ("Total Amount:", f"PKR {invoice_data[2]:,.2f}" if invoice_data[2] else "PKR 0.00")
            ]
            
            # Display in two columns
            for i, (label, value) in enumerate(invoice_details):
                row = i // 2
                col = i % 2
                
                if col == 0:
                    frame = Frame(details_grid, bg=self.card_bg)
                    frame.grid(row=row, column=0, sticky="w", padx=(0, 20), pady=5)
                else:
                    frame = Frame(details_grid, bg=self.card_bg)
                    frame.grid(row=row, column=1, sticky="w", padx=(20, 0), pady=5)
                
                Label(frame, text=label, font=("Segoe UI", 11, "bold"), 
                      bg=self.card_bg, fg=self.subtext_color, width=15, anchor="w").pack(side=LEFT)
                Label(frame, text=value, font=("Segoe UI", 11), 
                      bg=self.card_bg, fg=self.text_color, width=25, anchor="w").pack(side=LEFT)
            
            # Items Section
            items_label_frame = Frame(content, bg=self.card_bg)
            items_label_frame.pack(fill=X, pady=(0, 10))
            
            Label(items_label_frame, text="🛒 ITEMS PURCHASED", font=("Segoe UI", 14, "bold"),
                  bg=self.card_bg, fg=self.text_color).pack(anchor="w")
            
            # Create items container
            items_container = Frame(content, bg=self.card_bg, height=200)
            items_container.pack(fill=BOTH, expand=True, pady=(0, 20))
            items_container.pack_propagate(False)
            
            # Create treeview for items
            item_tree = ttk.Treeview(items_container, columns=("Product", "Qty", "Price", "Total"), 
                                   show="headings", height=8)
            
            item_tree.heading("Product", text="Product")
            item_tree.heading("Qty", text="Qty")
            item_tree.heading("Price", text="Price (PKR)")
            item_tree.heading("Total", text="Total (PKR)")
            
            item_tree.column("Product", width=400, minwidth=200)
            item_tree.column("Qty", width=80, anchor="center")
            item_tree.column("Price", width=120, anchor="e")
            item_tree.column("Total", width=150, anchor="e")
            
            # Add scrollbar
            item_scroll = Scrollbar(items_container, orient=VERTICAL, command=item_tree.yview)
            item_tree.configure(yscrollcommand=item_scroll.set)
            
            item_tree.pack(side=LEFT, fill=BOTH, expand=True)
            item_scroll.pack(side=RIGHT, fill=Y)
            
            # Insert items
            total_items = 0
            total_quantity = 0
            for item in items_data:
                product_name, quantity, price, total = item
                item_tree.insert("", END, values=(
                    product_name,
                    quantity,
                    f"PKR {price:,.2f}",
                    f"PKR {total:,.2f}"
                ))
                total_items += 1
                total_quantity += quantity
            
            # Summary Section
            summary_frame = Frame(content, bg="#f8f9fa", relief="solid", bd=1)
            summary_frame.pack(fill=X, pady=(0, 20))
            
            summary_text = f"Summary: {total_items} items, {total_quantity} units purchased"
            Label(summary_frame, text=summary_text, font=("Segoe UI", 11), 
                  bg="#f8f9fa", fg=self.subtext_color, pady=10).pack()
            
            # Close button at bottom
            close_frame = Frame(content, bg=self.card_bg)
            close_frame.pack(fill=X, pady=(10, 0))
            
            Button(close_frame, text="Close", command=detail_win.destroy,
                   font=("Segoe UI", 10), bg=self.accent_color, fg="white",
                   cursor="hand2", relief="flat", padx=30, pady=8).pack()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load invoice details: {str(e)}")
            print(f"Error details: {e}")
    
    def print_invoice(self):
        """Print selected invoice as PDF"""
        if not self.selected_invoice_id:
            messagebox.showinfo("Info", "Please select an invoice first")
            return
        
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Get invoice details
            cur.execute('''
                SELECT invoice_id, invoice_no, total_amount, tax_amount, 
                       subtotal_amount, customer_name, customer_contact,
                       invoice_date, invoice_time
                FROM invoices 
                WHERE invoice_no = ?
            ''', (self.selected_invoice_id,))
            
            invoice = cur.fetchone()
            
            if not invoice:
                messagebox.showerror("Error", "Invoice not found")
                return
            
            # Get invoice items
            cur.execute('''
                SELECT product_name, quantity, price, total
                FROM invoice_items
                WHERE invoice_id = ?
            ''', (invoice[0],))
            
            items = cur.fetchall()
            
            # Create PDF
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Invoice as PDF",
                initialfile=f"Invoice_{self.selected_invoice_id}.pdf"
            )
            
            if not file_path:
                return
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor(self.accent_color),
                alignment=1,
                spaceAfter=15
            )
            
            elements.append(Paragraph(f"INVOICE #{self.selected_invoice_id}", title_style))
            
            # Invoice details
            details_style = ParagraphStyle(
                'Details',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=5
            )
            
            customer_name = invoice[5] or "Walk-in Customer"
            customer_contact = invoice[6] or "N/A"
            
            details = [
                f"Customer Name: {customer_name}",
                f"Customer Contact: {customer_contact}",
                f"Invoice Date: {invoice[7]}",
                f"Invoice Time: {invoice[8]}",
                ""
            ]
            
            for detail in details:
                elements.append(Paragraph(detail, details_style))
            
            elements.append(Spacer(1, 15))
            
            # Items table
            table_data = [['Product', 'Qty', 'Price (PKR)', 'Total (PKR)']]
            
            for item in items:
                table_data.append([
                    item[0],
                    str(item[1]),
                    f"{item[2]:,.2f}",
                    f"{item[3]:,.2f}"
                ])
            
            # Add totals
            subtotal = invoice[4] or 0
            tax = invoice[3] or 0
            total = invoice[2] or 0
            
            table_data.append(['', '', 'Subtotal:', f"PKR {subtotal:,.2f}"])
            table_data.append(['', '', 'Tax:', f"PKR {tax:,.2f}"])
            table_data.append(['', '', 'Total:', f"PKR {total:,.2f}"])
            
            items_table = Table(table_data, colWidths=[250, 50, 80, 80])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.accent_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -3), colors.white),
                ('GRID', (0, 0), (-1, -4), 0.5, colors.HexColor('#dddddd')),
                ('FONTNAME', (-2, -3), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (-2, -3), (-1, -1), 'RIGHT'),
                ('LINEABOVE', (-2, -1), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(items_table)
            elements.append(Spacer(1, 20))
            
            # Footer
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#666666'),
                alignment=1
            )
            
            elements.append(Paragraph(f"Customer: {customer_name} | Contact: {customer_contact}", footer_style))
            elements.append(Paragraph(f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
            # Add custom footer with company info
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("Software produced by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363", 
                                    footer_style))
            
            # Build PDF
            doc.build(elements)
            
            self.status_label.config(text=f"Invoice #{self.selected_invoice_id} saved as PDF")
            messagebox.showinfo("Success", f"Invoice saved as PDF:\n{file_path}")
            
            # Open the PDF
            os.startfile(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print invoice: {str(e)}")
    
    # =========== REPORT METHODS ===========
    
    def on_report_type_change(self):
        """Handle report type change"""
        report_type = self.report_type.get()
        if report_type == "custom":
            self.custom_frame.pack(fill=X, pady=(10, 0))
        else:
            self.custom_frame.pack_forget()
    
    def generate_report(self):
        """Generate sales report based on selected type"""
        report_type = self.report_type.get()
        
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            query_params = []
            query = '''
                SELECT DATE(created_at) as date,
                       invoice_no,
                       total_amount,
                       (SELECT COUNT(*) FROM invoice_items WHERE invoice_id = invoices.invoice_id) as items,
                       customer_name,
                       TIME(created_at) as time
                FROM invoices
                WHERE 1=1
            '''
            
            if report_type == "daily":
                query += " AND DATE(created_at) = ?"
                query_params.append(self.current_date)
                
            elif report_type == "weekly":
                start_date = (datetime.datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                query += " AND DATE(created_at) >= ?"
                query_params.append(start_date)
                
            elif report_type == "monthly":
                month_start = datetime.datetime.now().replace(day=1).strftime("%Y-%m-%d")
                query += " AND DATE(created_at) >= ?"
                query_params.append(month_start)
                
            elif report_type == "custom":
                start_date = self.start_date.get()
                end_date = self.end_date.get()
                
                if not start_date or not end_date:
                    messagebox.showerror("Error", "Please select both start and end dates")
                    return
                
                query += " AND DATE(created_at) BETWEEN ? AND ?"
                query_params.extend([start_date, end_date])
            
            query += " ORDER BY created_at DESC"
            
            cur.execute(query, query_params)
            self.report_data = cur.fetchall()
            
            # Update report display only
            self.update_report_display()
            
            self.status_label.config(text=f"Generated {report_type} report with {len(self.report_data)} records")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
            self.status_label.config(text="Error generating report")
    
    def update_report_display(self):
        """Update the report treeview with data"""
        self.report_tree.delete(*self.report_tree.get_children())
        
        if not self.report_data:
            return
        
        total_amount = 0
        total_items = 0
        for row in self.report_data:
            date_str, invoice_no, amount, items, customer, time = row
            formatted_amount = f"PKR {amount:,.2f}" if amount else "PKR 0.00"
            total_amount += amount if amount else 0
            total_items += items if items else 0
            
            self.report_tree.insert("", END, values=(
                date_str,
                invoice_no,
                formatted_amount,
                items or 0,
                customer or "Walk-in Customer",
                time
            ))
        
        # Add total row
        self.report_tree.insert("", END, values=(
            "TOTAL", "", f"PKR {total_amount:,.2f}", total_items, "", ""
        ), tags=('total',))
        
        self.report_tree.tag_configure('total', background='#e8f5e9', font=('Segoe UI', 10, 'bold'))
    
    # =========== STATISTICS METHODS ===========
    
    def update_quick_stats(self):
        """Update quick statistics cards"""
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Today's sales
            cur.execute("SELECT SUM(total_amount) FROM invoices WHERE DATE(created_at) = ?", 
                       (self.current_date,))
            today_sales = cur.fetchone()[0] or 0
            self.today_sales_label.config(text=f"PKR {today_sales:,.2f}")
            
            # Weekly sales (last 7 days)
            start_date = (datetime.datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            cur.execute("SELECT SUM(total_amount) FROM invoices WHERE DATE(created_at) >= ?",
                       (start_date,))
            weekly_sales = cur.fetchone()[0] or 0
            self.weekly_sales_label.config(text=f"PKR {weekly_sales:,.2f}")
            
            # Monthly sales (current month)
            current_month = datetime.datetime.now().strftime("%Y-%m")
            cur.execute("SELECT SUM(total_amount) FROM invoices WHERE strftime('%Y-%m', created_at) = ?",
                       (current_month,))
            monthly_sales = cur.fetchone()[0] or 0
            self.monthly_sales_label.config(text=f"PKR {monthly_sales:,.2f}")
            
            # Total invoices
            cur.execute("SELECT COUNT(*) FROM invoices")
            total_invoices = cur.fetchone()[0] or 0
            self.total_invoices_label.config(text=f"{total_invoices:,}")
            
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    # =========== EXPORT METHODS ===========
    
    def export_to_excel(self):
        """Export COMPLETE invoice details to Excel"""
        try:
            if not self.report_data:
                messagebox.showinfo("Info", "No data to export. Please generate a report first.")
                return
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Complete Invoice Report",
                initialfile=f"complete_invoice_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not file_path:
                return
            
            conn, cur = self.get_db_connection()
            if not conn:
                return
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Sheet 1: Invoice Summary
                summary_data = []
                for row in self.report_data:
                    date_str, invoice_no, amount, items, customer, time = row
                    summary_data.append({
                        'Date': date_str,
                        'Invoice No': invoice_no,
                        'Total Amount': amount or 0,
                        'Items Count': items or 0,
                        'Customer Name': customer or "Walk-in Customer",
                        'Time': time
                    })
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Invoice Summary', index=False)
                
                # Sheet 2: Detailed Invoice Information
                detailed_data = []
                for row in self.report_data:
                    invoice_no = row[1]
                    
                    cur.execute('''
                        SELECT invoice_no, total_amount, tax_amount, 
                               subtotal_amount, customer_name, customer_contact,
                               invoice_date, invoice_time, created_at
                        FROM invoices 
                        WHERE invoice_no = ?
                    ''', (invoice_no,))
                    
                    invoice_details = cur.fetchone()
                    
                    if invoice_details:
                        detailed_data.append({
                            'Invoice No': invoice_details[0],
                            'Total Amount': invoice_details[1] or 0,
                            'Tax Amount': invoice_details[2] or 0,
                            'Subtotal Amount': invoice_details[3] or 0,
                            'Customer Name': invoice_details[4] or "Walk-in Customer",
                            'Customer Contact': invoice_details[5] or "N/A",
                            'Invoice Date': invoice_details[6],
                            'Invoice Time': invoice_details[7],
                            'Created At': invoice_details[8]
                        })
                
                df_detailed = pd.DataFrame(detailed_data)
                df_detailed.to_excel(writer, sheet_name='Invoice Details', index=False)
                
                # Sheet 3: Invoice Items
                items_data = []
                for row in self.report_data:
                    invoice_no = row[1]
                    
                    cur.execute('SELECT invoice_id FROM invoices WHERE invoice_no = ?', (invoice_no,))
                    invoice_id_result = cur.fetchone()
                    
                    if invoice_id_result:
                        invoice_id = invoice_id_result[0]
                        
                        cur.execute('''
                            SELECT product_name, quantity, price, total
                            FROM invoice_items
                            WHERE invoice_id = ?
                        ''', (invoice_id,))
                        
                        invoice_items = cur.fetchall()
                        
                        for item in invoice_items:
                            items_data.append({
                                'Invoice No': invoice_no,
                                'Product Name': item[0],
                                'Quantity': item[1],
                                'Price': item[2],
                                'Total': item[3]
                            })
                
                df_items = pd.DataFrame(items_data)
                df_items.to_excel(writer, sheet_name='Invoice Items', index=False)
                
                # Sheet 4: Summary Statistics
                amounts = [row[2] for row in self.report_data if row[2]]
                
                if amounts:
                    total_sales = sum(amounts)
                    avg_sale = total_sales / len(amounts) if len(amounts) > 0 else 0
                    highest_sale = max(amounts) if amounts else 0
                    lowest_sale = min(amounts) if amounts else 0
                    total_items = sum(row[3] for row in self.report_data if row[3])
                    transactions = len(self.report_data)
                    
                    summary_stats = {
                        'Metric': ['Total Sales', 'Average Sale', 'Highest Sale', 'Lowest Sale', 'Total Items', 'Transactions'],
                        'Value': [
                            f"PKR {total_sales:,.2f}",
                            f"PKR {avg_sale:,.2f}",
                            f"PKR {highest_sale:,.2f}",
                            f"PKR {lowest_sale:,.2f}",
                            f"{total_items:,}",
                            f"{transactions:,}"
                        ]
                    }
                    
                    df_stats = pd.DataFrame(summary_stats)
                    df_stats.to_excel(writer, sheet_name='Summary Statistics', index=False)
            
            self.status_label.config(text=f"Complete report exported to {os.path.basename(file_path)}")
            messagebox.showinfo("Success", f"Complete invoice report exported successfully!\n\nSaved to:\n{file_path}")
            
            # Open the Excel file
            os.startfile(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export to Excel: {str(e)}")
    
    def export_to_pdf(self):
        """Export COMPLETE invoice details to PDF with footer and improved table formatting"""
        try:
            if not self.report_data:
                messagebox.showinfo("Info", "No data to export. Please generate a report first.")
                return
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Complete Invoice Report",
                initialfile=f"complete_invoice_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not file_path:
                return
            
            conn, cur = self.get_db_connection()
            if not conn:
                return
            
            # Custom PDF template with footer
            class CustomDocTemplate(SimpleDocTemplate):
                def __init__(self, filename, **kwargs):
                    SimpleDocTemplate.__init__(self, filename, **kwargs)
                
                def afterFlowable(self, flowable):
                    # Add footer after each flowable (page)
                    if isinstance(flowable, PageBreak):
                        self.canv.saveState()
                        self.canv.setFont('Helvetica', 8)
                        self.canv.setFillColor(colors.HexColor("#666666"))
                        footer_text = "Software produced by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363"
                        self.canv.drawCentredString(self.width/2.0, 0.5*inch, footer_text)
                        self.canv.restoreState()
                
                def build(self, flowables, **kw):
                    # Add footer to all pages
                    SimpleDocTemplate.build(self, flowables, **kw)
                    # Add footer to last page
                    self.canv.saveState()
                    self.canv.setFont('Helvetica', 8)
                    self.canv.setFillColor(colors.HexColor("#666666"))
                    footer_text = "Software produced by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363"
                    self.canv.drawCentredString(self.width/2.0, 0.5*inch, footer_text)
                    self.canv.restoreState()
            
            # Create PDF document with custom template
            doc = CustomDocTemplate(file_path, pagesize=landscape(letter))
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor(self.accent_color),
                alignment=1,
                spaceAfter=15
            )
            
            report_type = self.report_type.get().upper()
            title = Paragraph(f"COMPLETE INVOICE REPORT - {report_type}", title_style)
            elements.append(title)
            
            # Date range
            date_style = ParagraphStyle(
                'DateStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#666666'),
                alignment=1,
                spaceAfter=15
            )
            
            date_range = self.get_date_range_text()
            elements.append(Paragraph(date_range, date_style))
            
            # Summary Statistics
            summary_style = ParagraphStyle(
                'Summary',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor(self.accent_color),
                alignment=0,
                spaceAfter=10
            )
            
            elements.append(Paragraph("SUMMARY STATISTICS", summary_style))
            
            # Calculate summary statistics
            amounts = [row[2] for row in self.report_data if row[2]]
            total_sales = sum(amounts) if amounts else 0
            avg_sale = total_sales / len(amounts) if len(amounts) > 0 else 0
            highest_sale = max(amounts) if amounts else 0
            lowest_sale = min(amounts) if amounts else 0
            total_items = sum(row[3] for row in self.report_data if row[3])
            transactions = len(self.report_data)
            
            summary_data = [
                ['Total Sales:', f"PKR {total_sales:,.2f}"],
                ['Average Sale:', f"PKR {avg_sale:,.2f}"],
                ['Highest Sale:', f"PKR {highest_sale:,.2f}"],
                ['Lowest Sale:', f"PKR {lowest_sale:,.2f}"],
                ['Total Items:', f"{total_items:,}"],
                ['Total Transactions:', f"{transactions:,}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[200, 200])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 20))
            
            # Detailed Invoice List
            invoice_title = Paragraph("DETAILED INVOICE LIST", summary_style)
            elements.append(invoice_title)
            elements.append(Spacer(1, 10))
            
            # Create table for all invoices - ADJUSTED COLUMN WIDTHS for better readability
            # Increased width for invoice_no column and adjusted others
            table_data = [['Date', 'Invoice No', 'Customer', 'Amount (PKR)', 'Items', 'Time']]
            
            for row in self.report_data:
                date_str, invoice_no, amount, items, customer, time = row
                # Format customer name to prevent overflow
                formatted_customer = (customer or "Walk-in Customer")[:25] + "..." if len(customer or "") > 25 else (customer or "Walk-in Customer")
                table_data.append([
                    date_str,
                    invoice_no,  # Invoice number may be long
                    formatted_customer,
                    f"{amount:,.2f}" if amount else "0.00",
                    str(items or 0),
                    time
                ])
            
            # Add total row
            table_data.append(['', '', 'TOTAL:', f"{total_sales:,.2f}", str(total_items), ''])
            
            # Create table with improved column widths - SPECIFICALLY INCREASED INVOICE NO COLUMN WIDTH
            # Format: [Date, Invoice No, Customer, Amount, Items, Time]
            invoice_table = Table(table_data, colWidths=[70, 120, 150, 80, 40, 60])  # Increased Invoice No from 80 to 120
            invoice_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.accent_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#cccccc')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e9')),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                # Word wrap for long invoice numbers
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))
            
            elements.append(invoice_table)
            elements.append(Spacer(1, 20))
            
            # Process each invoice for detailed view
            for idx, row in enumerate(self.report_data):
                date_str, invoice_no, amount, items, customer, time = row
                
                # Add page break for each new invoice
                elements.append(PageBreak())
                
                # Invoice Header
                invoice_title_style = ParagraphStyle(
                    'InvoiceTitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.HexColor(self.accent_color),
                    alignment=0,
                    spaceAfter=10
                )
                
                elements.append(Paragraph(f"INVOICE #{invoice_no}", invoice_title_style))
                
                # Get complete invoice details
                cur.execute('''
                    SELECT invoice_no, total_amount, tax_amount, 
                           subtotal_amount, customer_name, customer_contact,
                           invoice_date, invoice_time, created_at
                    FROM invoices 
                    WHERE invoice_no = ?
                ''', (invoice_no,))
                
                invoice_details = cur.fetchone()
                
                if invoice_details:
                    # Invoice Information Table
                    info_data = [
                        ['Field', 'Value'],
                        ['Invoice No:', invoice_details[0]],
                        ['Customer Name:', invoice_details[4] or "Walk-in Customer"],
                        ['Customer Contact:', invoice_details[5] or "N/A"],
                        ['Invoice Date:', invoice_details[6]],
                        ['Invoice Time:', invoice_details[7]],
                        ['Created At:', invoice_details[8]],
                        ['Subtotal Amount:', f"PKR {invoice_details[3]:,.2f}"],
                        ['Tax Amount:', f"PKR {invoice_details[2]:,.2f}"],
                        ['Total Amount:', f"PKR {invoice_details[1]:,.2f}"]
                    ]
                    
                    info_table = Table(info_data, colWidths=[200, 300])
                    info_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                    ]))
                    
                    elements.append(info_table)
                    elements.append(Spacer(1, 20))
                    
                    # Get invoice items
                    cur.execute('SELECT invoice_id FROM invoices WHERE invoice_no = ?', (invoice_no,))
                    invoice_id_result = cur.fetchone()
                    
                    if invoice_id_result:
                        invoice_id = invoice_id_result[0]
                        
                        cur.execute('''
                            SELECT product_name, quantity, price, total
                            FROM invoice_items
                            WHERE invoice_id = ?
                        ''', (invoice_id,))
                        
                        invoice_items = cur.fetchall()
                        
                        if invoice_items:
                            # Items Table
                            items_title = Paragraph("Items Purchased:", styles['Heading3'])
                            elements.append(items_title)
                            elements.append(Spacer(1, 10))
                            
                            items_data = [['Product', 'Qty', 'Price (PKR)', 'Total (PKR)']]
                            
                            for item in invoice_items:
                                # Truncate product name if too long
                                product_name = item[0][:35] + "..." if len(item[0]) > 35 else item[0]
                                items_data.append([
                                    product_name,
                                    str(item[1]),
                                    f"{item[2]:,.2f}",
                                    f"{item[3]:,.2f}"
                                ])
                            
                            # Calculate totals
                            total_qty = sum(item[1] for item in invoice_items)
                            total_amount = sum(item[3] for item in invoice_items)
                            
                            items_data.append(['', '', 'Total Items:', str(len(invoice_items))])
                            items_data.append(['', '', 'Total Quantity:', str(total_qty)])
                            items_data.append(['', '', 'Total Amount:', f"PKR {total_amount:,.2f}"])
                            
                            items_table = Table(items_data, colWidths=[300, 60, 100, 100])
                            items_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 10),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                                ('BACKGROUND', (0, 1), (-1, -4), colors.white),
                                ('BACKGROUND', (-2, -3), (-1, -1), colors.HexColor('#f8f9fa')),
                                ('FONTNAME', (-2, -3), (-1, -1), 'Helvetica-Bold'),
                                ('GRID', (0, 0), (-1, -4), 0.5, colors.HexColor('#cccccc')),
                                ('LINEABOVE', (-2, -1), (-1, -1), 1, colors.black),
                            ]))
                            
                            elements.append(items_table)
                            elements.append(Spacer(1, 20))
                
                # Add separator
                elements.append(Spacer(1, 30))
            
            # Footer info
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#666666'),
                alignment=1
            )
            
            elements.append(Paragraph(f"Report includes complete invoice details for {len(self.report_data)} invoices", footer_style))
            elements.append(Paragraph(f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
            
            # Build PDF
            doc.build(elements)
            
            self.status_label.config(text="Complete invoice report exported to PDF")
            messagebox.showinfo("Success", f"Complete invoice PDF report generated successfully!\n\nSaved to:\n{file_path}")
            
            # Open the PDF
            os.startfile(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export to PDF: {str(e)}")
    
    def get_date_range_text(self):
        """Get date range text for report"""
        report_type = self.report_type.get()
        
        if report_type == "daily":
            return f"Date: {self.current_date}"
        elif report_type == "weekly":
            start_date = (datetime.datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            return f"Week: {start_date} to {self.current_date}"
        elif report_type == "monthly":
            month_name = datetime.datetime.now().strftime("%B %Y")
            return f"Month: {month_name}"
        elif report_type == "custom":
            return f"From {self.start_date.get()} to {self.end_date.get()}"
        
        return ""
    
    # =========== UPDATED: CLIENTS PDF EXPORT METHOD WITH SUMMARY AT TOP ===========
    
    def export_clients_pdf(self):
        """Export CLIENT LIST from invoices table in a detailed PDF format WITHOUT Invoice Time and Created At columns"""
        try:
            conn, cur = self.get_db_connection()
            if not conn:
                return
            
            # Get ALL invoices from database with ALL columns
            cur.execute('''
                SELECT 
                    rowid,
                    invoice_no,
                    customer_name,
                    customer_contact,
                    total_amount,
                    tax_amount,
                    subtotal_amount,
                    invoice_date,
                    invoice_time,
                    created_at
                FROM invoices 
                ORDER BY rowid
            ''')
            
            all_invoices = cur.fetchall()
            
            if not all_invoices:
                messagebox.showinfo("Info", "No invoices found in the database.")
                return
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Client List Report",
                initialfile=f"client_list_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not file_path:
                return
            
            # Custom PDF template with footer on EVERY page
            class ClientDocTemplate(SimpleDocTemplate):
                def __init__(self, filename, **kwargs):
                    SimpleDocTemplate.__init__(self, filename, **kwargs)
                
                def afterFlowable(self, flowable):
                    # Add footer after EACH flowable (every page)
                    if isinstance(flowable, Flowable):
                        # Add footer with company info at bottom of every page
                        self.canv.saveState()
                        self.canv.setFont('Helvetica', 8)
                        self.canv.setFillColor(colors.HexColor("#666666"))
                        footer_text = "Software produced by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363"
                        self.canv.drawCentredString(self.width/2.0, 0.5*inch, footer_text)
                        
                        # Add page number
                        page_num = f"Page {self.page}"
                        self.canv.drawRightString(self.width - 0.5*inch, 0.5*inch, page_num)
                        self.canv.restoreState()
            
            # Create PDF document
            doc = ClientDocTemplate(file_path, pagesize=landscape(letter))
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'ClientTitle',
                parent=styles['Heading1'],
                fontSize=22,
                textColor=colors.HexColor(self.accent_color),
                alignment=1,
                spaceAfter=10
            )
            
            elements.append(Paragraph("👥 CLIENT LIST REPORT", title_style))
            
            # Subtitle
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#666666'),
                alignment=1,
                spaceAfter=20
            )
            
            elements.append(Paragraph("Complete Customer Invoices Database", subtitle_style))
            
            # Report Information
            info_style = ParagraphStyle(
                'Info',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#444444'),
                alignment=1,
                spaceAfter=15
            )
            
            elements.append(Paragraph(f"Total Records: {len(all_invoices):,} | Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
            
            # Calculate summary statistics
            total_amount_all = 0
            total_tax_all = 0
            total_subtotal_all = 0
            unique_customers = set()
            
            for invoice in all_invoices:
                (
                    rowid,
                    invoice_no,
                    customer_name,
                    customer_contact,
                    total_amount,
                    tax_amount,
                    subtotal_amount,
                    invoice_date,
                    invoice_time,
                    created_at
                ) = invoice
                
                if customer_name:
                    unique_customers.add(customer_name)
                
                total_amount_all += total_amount if total_amount else 0
                total_tax_all += tax_amount if tax_amount else 0
                total_subtotal_all += subtotal_amount if subtotal_amount else 0
            
            avg_invoice_amount = total_amount_all / len(all_invoices) if len(all_invoices) > 0 else 0
            
            # ===== SUMMARY STATISTICS AT THE TOP =====
            summary_style = ParagraphStyle(
                'Summary',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor(self.accent_color),
                alignment=0,
                spaceAfter=10
            )
            
            elements.append(Paragraph("SUMMARY STATISTICS", summary_style))
            
            summary_data = [
                ['Total Invoices:', f"{len(all_invoices):,}"],
                ['Unique Customers:', f"{len(unique_customers):,}"],
                ['Total Revenue:', f"PKR {total_amount_all:,.2f}"],
                ['Total Tax:', f"PKR {total_tax_all:,.2f}"],
                ['Total Subtotal:', f"PKR {total_subtotal_all:,.2f}"],
                ['Average Invoice:', f"PKR {avg_invoice_amount:,.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[150, 200])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 20))
            
            # ===== MAIN DATA TABLE =====
            data_style = ParagraphStyle(
                'Data',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor(self.accent_color),
                alignment=0,
                spaceAfter=10
            )
            
            elements.append(Paragraph("DETAILED INVOICE DATA", data_style))
            
            # Create main data table WITHOUT "Invoice Time" and "Created At" columns
            table_data = []
            
            # Table headers (SKIPPING Invoice Time and Created At columns)
            headers = [
                '#', 'Invoice No', 'Customer Name', 'Customer Contact',
                'Total Amount (PKR)', 'Tax Amount (PKR)', 'Subtotal Amount (PKR)',
                'Invoice Date'  # Removed: 'Invoice Time' and 'Created At'
            ]
            table_data.append(headers)
            
            # Add data rows (SKIPPING Invoice Time and Created At columns)
            for invoice in all_invoices:
                (
                    rowid,
                    invoice_no,
                    customer_name,
                    customer_contact,
                    total_amount,
                    tax_amount,
                    subtotal_amount,
                    invoice_date,
                    invoice_time,  # This will be SKIPPED
                    created_at     # This will be SKIPPED
                ) = invoice
                
                # Format amounts
                formatted_total = f"{total_amount:,.2f}" if total_amount else "0.00"
                formatted_tax = f"{tax_amount:,.2f}" if tax_amount else "0.00"
                formatted_subtotal = f"{subtotal_amount:,.2f}" if subtotal_amount else "0.00"
                
                # Format invoice date only (SKIPPING invoice_time and created_at)
                formatted_invoice_date = invoice_date if invoice_date else "N/A"
                
                # Format customer name and contact for better display
                formatted_customer = (customer_name or "Walk-in Customer")[:25] + "..." if len(customer_name or "") > 25 else (customer_name or "Walk-in Customer")
                formatted_contact = (customer_contact or "N/A")[:20] + "..." if len(customer_contact or "") > 20 else (customer_contact or "N/A")
                
                # Add row WITHOUT Invoice Time and Created At columns
                table_data.append([
                    str(rowid),
                    invoice_no,
                    formatted_customer,
                    formatted_contact,
                    formatted_total,
                    formatted_tax,
                    formatted_subtotal,
                    formatted_invoice_date  # Only invoice date, no time
                ])
            
            # Add summary row (adjusted for fewer columns)
            table_data.append([
                'TOTAL', '', '', '',
                f"{total_amount_all:,.2f}",
                f"{total_tax_all:,.2f}",
                f"{total_subtotal_all:,.2f}",
                ''
            ])
            
            # Calculate column widths for landscape mode (8 columns now instead of 10)
            # INCREASED Invoice No column width from 80 to 120
            col_widths = [30, 120, 120, 100, 80, 70, 80, 90]  # Increased Invoice No column width
            
            # Create and style the table
            main_table = Table(table_data, colWidths=col_widths)
            
            # Style for the table
            main_table.setStyle(TableStyle([
                # Header style
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.accent_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                
                # Data rows style
                ('ALIGN', (0, 1), (-1, -2), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 8),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#cccccc')),
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
                
                # Amount columns alignment (columns 4, 5, 6)
                ('ALIGN', (4, 1), (6, -2), 'RIGHT'),
                
                # Summary row style
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e9')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 9),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('ALIGN', (4, -1), (6, -1), 'RIGHT'),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
                
                # Word wrap for long invoice numbers
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))
            
            elements.append(main_table)
            elements.append(Spacer(1, 20))
            
            # Add information about skipped columns
            note_style = ParagraphStyle(
                'Note',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#666666'),
                alignment=0,
                spaceAfter=10
            )
            
            elements.append(Paragraph(
                "<i>Note: This report shows invoice date only. Invoice time and created timestamp columns have been excluded for clarity.</i>",
                note_style
            ))
            
            # Add footer text with company info
            footer_style = ParagraphStyle(
                'FooterText',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#666666'),
                alignment=1
            )
            
            elements.append(Paragraph(
                "This report contains all customer invoices from the database. "
                "For any queries or support, please contact:",
                footer_style
            ))
            
            elements.append(Spacer(1, 5))
            
            company_info = Paragraph(
                "<b>Dukes Tech Services</b><br/>"
                "Phone: +923097671363 | Website: dukestechservices.com",
                ParagraphStyle(
                    'CompanyInfo',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor(self.accent_color),
                    alignment=1
                )
            )
            
            elements.append(company_info)
            elements.append(Spacer(1, 10))
            
            # Build PDF (footer will be added automatically on every page by the custom template)
            doc.build(elements)
            
            # Update status and show success message
            self.status_label.config(text=f"Client list ({len(all_invoices)} records) exported to PDF")
            messagebox.showinfo("Success", 
                f"Client List PDF report generated successfully!\n\n"
                f"• Total Records: {len(all_invoices):,}\n"
                f"• Total Revenue: PKR {total_amount_all:,.2f}\n"
                f"• Unique Customers: {len(unique_customers):,}\n"
                f"• Saved to: {file_path}\n\n"
                f"Note: Invoice Time and Created At columns have been excluded from the report.")
            
            # Open the PDF
            os.startfile(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export client list: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
    
    # =========== TIME UPDATE METHODS ===========
    
    def update_date_time(self):
        """Update live date and time in header"""
        try:
            # Check if we should continue
            if self.is_closing or not self.root.winfo_exists():
                return
            
            # Check if widget exists
            if hasattr(self, 'date_time_label') and self.date_time_label.winfo_exists():
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                self.date_time_label.config(text=current_time)
            
            # Schedule next update
            if not self.is_closing:
                self.safe_after(1000, self.update_date_time)
                
        except Exception as e:
            print(f"Error in update_date_time: {e}")
            if not self.is_closing:
                self.safe_after(1000, self.update_date_time)
    
    def update_time(self):
        """Update time display in footer"""
        try:
            # Check if we should continue
            if self.is_closing or not self.root.winfo_exists():
                return
            
            # Check if widget exists
            if hasattr(self, 'time_label') and self.time_label.winfo_exists():
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.time_label.config(text=f"Last Updated: {current_time}")
            
            # Schedule next update
            if not self.is_closing:
                self.safe_after(1000, self.update_time)
                
        except Exception as e:
            print(f"Error in update_time: {e}")
            if not self.is_closing:
                self.safe_after(1000, self.update_time)


def main():
    """Main entry point with proper cleanup"""
    root = None
    app = None
    
    try:
        root = Tk()
        app = SalesClass(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure cleanup
        if app and hasattr(app, 'cleanup'):
            try:
                app.cleanup()
            except:
                pass
        if root:
            try:
                root.destroy()
            except:
                pass
        print("Application terminated")


if __name__ == "__main__":
    main()