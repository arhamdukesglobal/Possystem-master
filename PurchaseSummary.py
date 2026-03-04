# PurchaseDashboard.py
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
from datetime import date, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import warnings
import re
import time
warnings.filterwarnings('ignore')

class PurchasesDashboard:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1300x700+200+100")
        self.root.title("Purchases Analytics Dashboard | Inventory Management System")
        self.root.config(bg="#f0f0f0")
        self.root.focus_force()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set minimum window size
        self.root.minsize(1200, 700)
        
        # =========== Variables ==========
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.selected_bill_no = None
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
        self.accent_color = "#0f4d7d"  # Changed to match Purchases color
        self.success_color = "#27ae60"
        self.warning_color = "#f39c12"
        self.danger_color = "#e74c3c"
        self.info_color = "#3498db"
        self.text_color = "#2c3e50"
        self.subtext_color = "#7f8c8d"
        self.border_color = "#d5dbdb"
        self.header_bg = "#0f4d7d"  # Updated to match Purchases color
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
        
        Label(title_frame, text="📦 PURCHASES ANALYTICS DASHBOARD", 
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
        
        # Today's Purchases Card
        self.today_card = self.create_stat_card(self.stats_container, "💰 TODAY'S PURCHASES", "PKR 0.00", 
                                              self.success_color)
        self.today_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Weekly Purchases Card
        self.weekly_card = self.create_stat_card(self.stats_container, "📈 WEEKLY PURCHASES", "PKR 0.00", 
                                               self.info_color)
        self.weekly_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Monthly Purchases Card
        self.monthly_card = self.create_stat_card(self.stats_container, "📊 MONTHLY PURCHASES", "PKR 0.00", 
                                                self.warning_color)
        self.monthly_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        # Total Bills Card
        self.bills_card = self.create_stat_card(self.stats_container, "📋 TOTAL BILLS", "0", 
                                               self.accent_color)
        self.bills_card.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        
        # =========== Main Content Area ==========
        self.content_frame = Frame(self.main_container, bg=self.bg_color)
        self.content_frame.pack(fill=BOTH, expand=True)
        
        # Configure grid for content area
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=2)
        
        # =========== Left Panel - Daily Bills ==========
        self.left_panel = Frame(self.content_frame, bg=self.card_bg, bd=1, relief="solid",
                          highlightbackground=self.border_color, highlightthickness=1)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Header for Daily Bills
        bill_header = Frame(self.left_panel, bg=self.accent_color, height=50)
        bill_header.pack(fill=X)
        bill_header.pack_propagate(False)
        
        Label(bill_header, text="📋 DAILY PURCHASE BILLS", font=("Segoe UI", 14, "bold"), 
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
        
        Button(date_frame, text="🔍 Load", command=self.load_daily_bills,
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
        self.search_entry.bind("<KeyRelease>", self.search_bills)
        
        # Search button
        Button(search_input_frame, text="🔍 Search", command=self.search_bills,
               font=("Segoe UI", 9), bg=self.accent_color, fg="white",
               cursor="hand2", relief="flat", padx=12, pady=4).pack(side=LEFT)
        
        # Debug button (temporary for troubleshooting)
        Button(search_input_frame, text="🐛 Debug DB", command=self.debug_database,
               font=("Segoe UI", 9), bg="#9b59b6", fg="white",
               cursor="hand2", relief="flat", padx=12, pady=4).pack(side=LEFT, padx=(10, 0))
        
        # Bill list container
        list_container = Frame(self.left_panel, bg=self.card_bg)
        list_container.pack(fill=BOTH, expand=True, padx=15, pady=(0, 10))
        
        # Treeview for bills
        tree_frame = Frame(list_container, bg=self.card_bg)
        tree_frame.pack(fill=BOTH, expand=True)
        
        # Create scrollbars
        scroll_y = Scrollbar(tree_frame, orient=VERTICAL)
        scroll_x = Scrollbar(tree_frame, orient=HORIZONTAL)
        
        # Create Treeview with sortable columns
        self.bill_tree = ttk.Treeview(tree_frame, 
                                      columns=("BillNo", "Amount", "Supplier", "Status", "DueDate"), 
                                      show="headings", 
                                      yscrollcommand=scroll_y.set,
                                      xscrollcommand=scroll_x.set,
                                      height=8)
        
        # Configure scrollbars
        scroll_y.config(command=self.bill_tree.yview)
        scroll_x.config(command=self.bill_tree.xview)
        
        # Define columns with sort functionality
        columns = [
            ("BillNo", "Bill No.", 100, self.sort_bill_tree),
            ("Amount", "Amount (PKR)", 100, self.sort_bill_tree),
            ("Supplier", "Supplier", 120, self.sort_bill_tree),
            ("Status", "Status", 80, self.sort_bill_tree),
            ("DueDate", "Due Date", 90, self.sort_bill_tree)
        ]
        
        for col_id, heading, width, sort_func in columns:
            self.bill_tree.heading(col_id, text=heading, command=lambda c=col_id: sort_func(c))
            self.bill_tree.column(col_id, width=width, minwidth=70)
            self.sort_directions[col_id] = False
        
        # Pack treeview and scrollbars
        self.bill_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)
        scroll_x.pack(side=BOTTOM, fill=X)
        
        # Bind selection event
        self.bill_tree.bind('<<TreeviewSelect>>', self.on_bill_select)
        
        # Action buttons frame
        self.action_frame = Frame(self.left_panel, bg=self.card_bg)
        self.action_frame.pack(fill=X, padx=15, pady=(0, 15))
        
        Button(self.action_frame, text="📄 View Details", command=self.view_bill_details,
               font=("Segoe UI", 10), bg=self.accent_color, fg="white",
               cursor="hand2", relief="flat", padx=15, pady=6).pack(side=LEFT, padx=(0, 10))
        
        Button(self.action_frame, text="🖨️ Print Bill", command=self.print_bill,
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
        
        # =========== Suppliers Button ===========
        Button(button_frame, text="🏢 Suppliers Report", command=self.generate_suppliers_pdf,
               font=("Segoe UI", 10), bg="#8e44ad", fg="white",
               cursor="hand2", relief="flat", padx=15, pady=6).pack(side=LEFT)
        
        # =========== Report Display Area (Table Only) ==========
        self.display_frame = Frame(self.right_panel, bg=self.card_bg)
        self.display_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview for report data
        report_tree_frame = Frame(self.display_frame, bg=self.card_bg)
        report_tree_frame.pack(fill=BOTH, expand=True)
        
        # Create scrollbars for report tree
        scroll_y2 = Scrollbar(report_tree_frame, orient=VERTICAL)
        scroll_x2 = Scrollbar(report_tree_frame, orient=HORIZONTAL)
        
        self.report_tree = ttk.Treeview(report_tree_frame, 
                                        columns=("Date", "BillNo", "Amount", "Items", "Supplier", "Status", "DueDate"), 
                                        show="headings", 
                                        yscrollcommand=scroll_y2.set,
                                        xscrollcommand=scroll_x2.set,
                                        height=12)
        
        scroll_y2.config(command=self.report_tree.yview)
        scroll_x2.config(command=self.report_tree.xview)
        
        # Define columns for report with sort functionality
        report_columns = [
            ("Date", "📅 Bill Date", 100, self.sort_report_tree),
            ("BillNo", "📄 Bill No.", 120, self.sort_report_tree),
            ("Amount", "💰 Amount (PKR)", 120, self.sort_report_tree),
            ("Items", "🛒 Items", 80, self.sort_report_tree),
            ("Supplier", "🏢 Supplier", 150, self.sort_report_tree),
            ("Status", "✅ Status", 100, self.sort_report_tree),
            ("DueDate", "📅 Due Date", 100, self.sort_report_tree)
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
        self.load_daily_bills()
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
                # Enable foreign keys and set date format
                self.cursor.execute("PRAGMA foreign_keys = ON")
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
    
    def debug_database(self):
        """Debug method to check database contents"""
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Check Purchases table
            cur.execute("SELECT COUNT(*) FROM Purchases")
            count = cur.fetchone()[0]
            print(f"\n=== DATABASE DEBUG INFO ===")
            print(f"Total purchases in database: {count}")
            
            # Check column names
            cur.execute("PRAGMA table_info(Purchases)")
            columns = cur.fetchall()
            print("\nPurchases table columns:")
            for col in columns:
                print(f"  {col}")
            
            # Check a few sample records
            cur.execute("SELECT BillNo, BillDate, TotalAmount, Supplier FROM Purchases LIMIT 5")
            samples = cur.fetchall()
            print("\nSample purchases (first 5):")
            for sample in samples:
                print(f"  {sample}")
            
            # Check date formats
            cur.execute("SELECT DISTINCT BillDate FROM Purchases LIMIT 5")
            dates = cur.fetchall()
            print("\nSample date formats:")
            for date_sample in dates:
                print(f"  {date_sample}")
                
            print("=" * 40)
            
        except Exception as e:
            print(f"Debug error: {e}")
            import traceback
            traceback.print_exc()
    
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
            self.today_purchases_label = value_label
        elif "weekly" in title.lower():
            self.weekly_purchases_label = value_label
        elif "monthly" in title.lower():
            self.monthly_purchases_label = value_label
        elif "bill" in title.lower():
            self.total_bills_label = value_label
        
        return card
    
    # =========== SORTING METHODS ===========
    
    def sort_bill_tree(self, column):
        """Sort bill treeview by column"""
        try:
            items = [(self.bill_tree.set(item, column), item) for item in self.bill_tree.get_children('')]
            
            if column == "Amount":
                items.sort(key=lambda x: float(x[0].replace('PKR ', '').replace(',', '')) if 'PKR' in x[0] else 0, 
                          reverse=self.sort_directions[column])
            elif column == "BillNo":
                items.sort(key=lambda x: int(''.join(filter(str.isdigit, x[0]))) if any(c.isdigit() for c in x[0]) else 0,
                          reverse=self.sort_directions[column])
            elif column == "DueDate":
                try:
                    items.sort(key=lambda x: datetime.datetime.strptime(x[0], "%d/%m/%Y") if x[0] and x[0] != "N/A" else datetime.datetime.min,
                              reverse=self.sort_directions[column])
                except:
                    items.sort(key=lambda x: x[0].lower(), reverse=self.sort_directions[column])
            else:
                items.sort(key=lambda x: x[0].lower(), reverse=self.sort_directions[column])
            
            for index, (_, item) in enumerate(items):
                self.bill_tree.move(item, '', index)
            
            self.sort_directions[column] = not self.sort_directions[column]
        except Exception as e:
            print(f"Error sorting bill tree: {e}")
    
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
            elif column == "Date" or column == "DueDate":
                try:
                    items_data.sort(key=lambda x: datetime.datetime.strptime(x[0], "%d/%m/%Y") if x[0] and x[0] != "N/A" else datetime.datetime.min,
                                  reverse=self.sort_directions[f"report_{column}"])
                except:
                    items_data.sort(key=lambda x: x[0].lower(), reverse=self.sort_directions[f"report_{column}"])
            elif column == "BillNo":
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
    
    # =========== BILL METHODS ===========
    
    def search_bills(self, event=None):
        """Search bills by bill number or supplier"""
        search_text = self.search_var.get().strip()
        
        if not search_text:
            self.load_daily_bills()
            return
        
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Clear existing items
            self.bill_tree.delete(*self.bill_tree.get_children())
            
            # Search by bill number or supplier
            cur.execute('''
                SELECT BillNo, TotalAmount, Supplier, PaymentStatus, DueDate
                FROM Purchases 
                WHERE (BillNo LIKE ? OR Supplier LIKE ?)
                ORDER BY BillDate DESC
            ''', (f'%{search_text}%', f'%{search_text}%'))
            
            bills = cur.fetchall()
            
            if bills:
                total_amount = 0
                for bill in bills:
                    bill_no, amount, supplier, status, due_date = bill
                    total_amount += amount if amount else 0
                    
                    # Format status with symbols
                    display_status = status or "Pending"
                    if status == "Overdue":
                        display_status = "⚠ " + status
                    elif status == "Paid":
                        display_status = "✓ " + status
                    
                    # Format due date
                    formatted_due_date = due_date or "N/A"
                    if due_date:
                        try:
                            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                                try:
                                    parsed_date = datetime.datetime.strptime(due_date, fmt)
                                    formatted_due_date = parsed_date.strftime("%d/%m/%Y")
                                    break
                                except:
                                    continue
                        except:
                            pass
                    
                    self.bill_tree.insert("", END, values=(
                        bill_no,
                        f"PKR {amount:,.2f}" if amount else "PKR 0.00",
                        supplier or "Unknown Supplier",
                        display_status,
                        formatted_due_date
                    ))
                
                self.status_label.config(text=f"Found {len(bills)} bills | Total: PKR {total_amount:,.2f}")
            else:
                self.status_label.config(text=f"No bills found for '{search_text}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search bills: {str(e)}")
            self.status_label.config(text="Error searching bills")
    
    def set_today_date(self):
        """Set date to today"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.date_var.set(today)
        self.load_daily_bills()
    
    def load_daily_bills(self):
        """Load bills for selected date with flexible date matching"""
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            selected_date = self.date_var.get()
            
            # Clear existing items
            self.bill_tree.delete(*self.bill_tree.get_children())
            
            # Get ALL bills first
            cur.execute('''
                SELECT BillNo, BillDate, TotalAmount, Supplier, PaymentStatus, DueDate
                FROM Purchases 
                ORDER BY BillDate DESC
            ''')
            
            all_bills = cur.fetchall()
            
            # Filter by selected date (flexible matching)
            matching_bills = []
            for bill in all_bills:
                bill_no, bill_date, amount, supplier, status, due_date = bill
                
                # Try different matching strategies
                if bill_date:
                    # Direct match
                    if selected_date == bill_date:
                        matching_bills.append(bill)
                    # Contains match
                    elif selected_date in bill_date:
                        matching_bills.append(bill)
                    # Try parsing and comparing
                    else:
                        try:
                            # Try different date formats
                            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                                try:
                                    parsed_date = datetime.datetime.strptime(bill_date, fmt)
                                    if selected_date == parsed_date.strftime("%Y-%m-%d"):
                                        matching_bills.append(bill)
                                    break
                                except:
                                    continue
                        except:
                            continue
            
            if matching_bills:
                total_amount = 0
                for bill in matching_bills:
                    bill_no, bill_date, amount, supplier, status, due_date = bill
                    total_amount += amount if amount else 0
                    
                    # Format status
                    display_status = status or "Pending"
                    if status == "Overdue":
                        display_status = "⚠ " + status
                    elif status == "Paid":
                        display_status = "✓ " + status
                    
                    # Format due date
                    formatted_due_date = due_date or "N/A"
                    if due_date:
                        try:
                            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                                try:
                                    parsed_date = datetime.datetime.strptime(due_date, fmt)
                                    formatted_due_date = parsed_date.strftime("%d/%m/%Y")
                                    break
                                except:
                                    continue
                        except:
                            pass
                    
                    self.bill_tree.insert("", END, values=(
                        bill_no,
                        f"PKR {amount:,.2f}" if amount else "PKR 0.00",
                        supplier or "Unknown Supplier",
                        display_status,
                        formatted_due_date
                    ))
                
                self.status_label.config(text=f"Loaded {len(matching_bills)} bills | Total: PKR {total_amount:,.2f}")
            else:
                self.status_label.config(text=f"No bills found for {selected_date}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load bills: {str(e)}")
            self.status_label.config(text="Error loading bills")
    
    def on_bill_select(self, event):
        """Handle bill selection"""
        selection = self.bill_tree.selection()
        if selection:
            values = self.bill_tree.item(selection[0])['values']
            if values:
                self.selected_bill_no = values[0]  # Bill number
    
    def view_bill_details(self):
        """View detailed bill information"""
        if not self.selected_bill_no:
            messagebox.showinfo("Info", "Please select a bill first")
            return
        
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Get all bill details
            cur.execute('''
                SELECT BillNo, BillDate, DueDate, Supplier, Contact, Address, 
                       TotalAmount, TotalItems, PaymentStatus
                FROM Purchases 
                WHERE BillNo = ?
            ''', (self.selected_bill_no,))
            
            bill_data = cur.fetchone()
            
            if not bill_data:
                messagebox.showerror("Error", "Bill not found")
                return
            
            # Get bill items
            cur.execute('''
                SELECT ReferenceNo, Description, Quantity, UnitPrice, TaxRate, Amount
                FROM PurchaseItems
                WHERE BillNo = ?
                ORDER BY ID
            ''', (self.selected_bill_no,))
            
            items_data = cur.fetchall()
            
            # Create detail window
            detail_win = Toplevel(self.root)
            detail_win.title(f"Purchase Bill Details - #{self.selected_bill_no}")
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
            
            Label(header, text=f"PURCHASE BILL DETAILS - #{self.selected_bill_no}", 
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
            
            # Bill Details Section
            details_frame = Frame(content, bg=self.card_bg, relief="solid", bd=1)
            details_frame.pack(fill=X, pady=(0, 20))
            
            Label(details_frame, text="📋 BILL INFORMATION", 
                  font=("Segoe UI", 14, "bold"), bg=self.accent_color, fg="white").pack(fill=X, pady=10)
            
            # Create details grid
            details_grid = Frame(details_frame, bg=self.card_bg)
            details_grid.pack(fill=X, padx=20, pady=15)
            
            # Bill details in two columns
            bill_details = [
                ("Bill No:", bill_data[0]),
                ("Supplier:", bill_data[3]),
                ("Contact:", bill_data[4]),
                ("Address:", bill_data[5]),
                ("Bill Date:", bill_data[1]),
                ("Due Date:", bill_data[2]),
                ("Payment Status:", bill_data[8]),
                ("Total Items:", str(bill_data[7])),
                ("Total Amount:", f"PKR {bill_data[6]:,.2f}" if bill_data[6] else "PKR 0.00")
            ]
            
            # Display in two columns
            for i, (label, value) in enumerate(bill_details):
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
            
            Label(items_label_frame, text="🛒 PURCHASE ITEMS", font=("Segoe UI", 14, "bold"),
                  bg=self.card_bg, fg=self.text_color).pack(anchor="w")
            
            # Create items container
            items_container = Frame(content, bg=self.card_bg, height=200)
            items_container.pack(fill=BOTH, expand=True, pady=(0, 20))
            items_container.pack_propagate(False)
            
            # Create treeview for items
            item_tree = ttk.Treeview(items_container, columns=("Reference", "Description", "Qty", "Unit Price", "Tax", "Amount"), 
                                   show="headings", height=8)
            
            item_tree.heading("Reference", text="Reference")
            item_tree.heading("Description", text="Description")
            item_tree.heading("Qty", text="Qty")
            item_tree.heading("Unit Price", text="Unit Price (PKR)")
            item_tree.heading("Tax", text="Tax %")
            item_tree.heading("Amount", text="Amount (PKR)")
            
            item_tree.column("Reference", width=100, anchor="w")
            item_tree.column("Description", width=200, anchor="w")
            item_tree.column("Qty", width=60, anchor="center")
            item_tree.column("Unit Price", width=100, anchor="e")
            item_tree.column("Tax", width=80, anchor="center")
            item_tree.column("Amount", width=120, anchor="e")
            
            # Add scrollbar
            item_scroll = Scrollbar(items_container, orient=VERTICAL, command=item_tree.yview)
            item_tree.configure(yscrollcommand=item_scroll.set)
            
            item_tree.pack(side=LEFT, fill=BOTH, expand=True)
            item_scroll.pack(side=RIGHT, fill=Y)
            
            # Insert items
            total_items = 0
            total_quantity = 0
            for item in items_data:
                reference, description, quantity, unit_price, tax_rate, amount = item
                item_tree.insert("", END, values=(
                    reference,
                    description,
                    quantity,
                    f"PKR {unit_price:,.2f}",
                    f"{tax_rate:.2f}%",
                    f"PKR {amount:,.2f}"
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
            messagebox.showerror("Error", f"Failed to load bill details: {str(e)}")
            print(f"Error details: {e}")
    
    def print_bill(self):
        """Print selected bill as PDF"""
        if not self.selected_bill_no:
            messagebox.showinfo("Info", "Please select a bill first")
            return
        
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Get bill details
            cur.execute('''
                SELECT BillNo, BillDate, DueDate, Supplier, Contact, Address, 
                       TotalAmount, TotalItems, PaymentStatus
                FROM Purchases 
                WHERE BillNo = ?
            ''', (self.selected_bill_no,))
            
            bill = cur.fetchone()
            
            if not bill:
                messagebox.showerror("Error", "Bill not found")
                return
            
            # Get bill items
            cur.execute('''
                SELECT ReferenceNo, Description, Quantity, UnitPrice, TaxRate, Amount
                FROM PurchaseItems
                WHERE BillNo = ?
                ORDER BY ID
            ''', (bill[0],))
            
            items = cur.fetchall()
            
            # Create PDF
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Purchase Bill as PDF",
                initialfile=f"Purchase_Bill_{self.selected_bill_no}.pdf"
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
            
            elements.append(Paragraph(f"PURCHASE BILL #{self.selected_bill_no}", title_style))
            
            # Bill details
            details_style = ParagraphStyle(
                'Details',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=5
            )
            
            supplier = bill[3] or "Unknown Supplier"
            contact = bill[4] or "N/A"
            address = bill[5] or "N/A"
            
            details = [
                f"Supplier: {supplier}",
                f"Contact: {contact}",
                f"Address: {address}",
                f"Bill Date: {bill[1]}",
                f"Due Date: {bill[2]}",
                f"Payment Status: {bill[8]}",
                f"Total Items: {bill[7]}",
                ""
            ]
            
            for detail in details:
                elements.append(Paragraph(detail, details_style))
            
            elements.append(Spacer(1, 15))
            
            # Items table
            table_data = [['Reference', 'Description', 'Qty', 'Unit Price', 'Tax %', 'Amount (PKR)']]
            
            for item in items:
                table_data.append([
                    item[0],
                    item[1],
                    str(item[2]),
                    f"{item[3]:,.2f}",
                    f"{item[4]:.2f}",
                    f"{item[5]:,.2f}"
                ])
            
            # Add totals
            total_amount = bill[6] or 0
            
            table_data.append(['', '', '', '', 'Total:', f"PKR {total_amount:,.2f}"])
            
            items_table = Table(table_data, colWidths=[80, 150, 40, 70, 50, 80])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.accent_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#dddddd')),
                ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'),
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
            
            elements.append(Paragraph(f"Supplier: {supplier} | Contact: {contact}", footer_style))
            elements.append(Paragraph(f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
            
            # Build PDF
            doc.build(elements)
            
            self.status_label.config(text=f"Purchase Bill #{self.selected_bill_no} saved as PDF")
            messagebox.showinfo("Success", f"Purchase bill saved as PDF:\n{file_path}")
            
            # Open the PDF
            os.startfile(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print bill: {str(e)}")
    
    # =========== UPDATED SUPPLIERS PDF METHOD ===========
    def generate_suppliers_pdf(self):
        """Generate a PDF report of all suppliers purchase data from Purchases table"""
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Get all purchase records from Purchases table with all columns
            cur.execute('''
                SELECT BillNo, BillDate, DueDate, Supplier, Contact, Address,
                       TotalItems, TotalAmount, PaymentStatus
                FROM Purchases 
                ORDER BY BillDate DESC
            ''')
            
            all_purchases = cur.fetchall()
            
            if not all_purchases:
                messagebox.showinfo("Info", "No purchase records found in the database.")
                return
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Suppliers Purchase Report",
                initialfile=f"Suppliers_Purchase_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not file_path:
                return
            
            # Create PDF document with landscape orientation
            doc = SimpleDocTemplate(
                file_path, 
                pagesize=landscape(A4),
                topMargin=0.75*inch,
                bottomMargin=1.0*inch,  # Increased bottom margin for footer
                leftMargin=0.5*inch,
                rightMargin=0.5*inch
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # =========== SUPPLIER SUMMARY SECTION (AT THE TOP) ===========
            summary_title_style = ParagraphStyle(
                'SummaryTitle',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#0f4d7d'),
                alignment=0,
                spaceAfter=15,
                spaceBefore=20
            )
            
            elements.append(Paragraph("SUPPLIER PURCHASE SUMMARY", summary_title_style))
            
            # Calculate summary statistics
            total_bills = len(all_purchases)
            total_amount = sum(purchase[7] or 0 for purchase in all_purchases)
            total_items = sum(purchase[6] or 0 for purchase in all_purchases)
            
            # Count payment statuses
            status_counts = {'Pending': 0, 'Paid': 0, 'Overdue': 0}
            for purchase in all_purchases:
                status = purchase[8] or 'Pending'
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts['Pending'] += 1
            
            # Group purchases by supplier for supplier summary
            supplier_data = {}
            for purchase in all_purchases:
                supplier = purchase[3] or "Unknown Supplier"
                amount = purchase[7] or 0
                items = purchase[6] or 0
                
                if supplier not in supplier_data:
                    supplier_data[supplier] = {
                        'total_amount': 0,
                        'total_items': 0,
                        'bill_count': 0,
                        'pending': 0,
                        'paid': 0,
                        'overdue': 0
                    }
                
                supplier_data[supplier]['total_amount'] += amount
                supplier_data[supplier]['total_items'] += items
                supplier_data[supplier]['bill_count'] += 1
                
                # Count statuses
                status = purchase[8] or 'Pending'
                if status == 'Pending':
                    supplier_data[supplier]['pending'] += 1
                elif status == 'Paid':
                    supplier_data[supplier]['paid'] += 1
                elif status == 'Overdue':
                    supplier_data[supplier]['overdue'] += 1
                else:
                    supplier_data[supplier]['pending'] += 1
            
            # Create supplier summary table
            supplier_table_data = [['Supplier', 'Bills', 'Items', 'Amount', 'Pending', 'Paid', 'Overdue', 'Avg/Bill']]
            
            for supplier, data in sorted(supplier_data.items(), 
                                        key=lambda x: x[1]['total_amount'], 
                                        reverse=True):
                avg_amount = data['total_amount'] / data['bill_count'] if data['bill_count'] > 0 else 0
                supplier_table_data.append([
                    supplier[:30],  # Limit supplier name length
                    str(data['bill_count']),
                    str(data['total_items']),
                    f"PKR {data['total_amount']:,.2f}",
                    str(data['pending']),
                    str(data['paid']),
                    str(data['overdue']),
                    f"PKR {avg_amount:,.2f}"
                ])
            
            # Add totals row
            supplier_table_data.append([
                'TOTAL',
                str(total_bills),
                str(total_items),
                f"PKR {total_amount:,.2f}",
                str(status_counts['Pending']),
                str(status_counts['Paid']),
                str(status_counts['Overdue']),
                f"PKR {(total_amount/total_bills if total_bills > 0 else 0):,.2f}"
            ])
            
            supplier_table = Table(supplier_table_data, 
                                  colWidths=[2.0*inch, 0.6*inch, 0.6*inch, 1.2*inch, 
                                             0.6*inch, 0.6*inch, 0.6*inch, 1.0*inch])
            
            supplier_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f4d7d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#dddddd')),
                
                # Total row
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e9')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),  # Amount column
                ('ALIGN', (7, 1), (7, -1), 'RIGHT'),  # Average column
            ]))
            
            elements.append(supplier_table)
            
            # Add separator
            elements.append(Spacer(1, 20))
            
            # Summary statistics text
            stats_style = ParagraphStyle(
                'StatsStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#666666'),
                alignment=0,
                spaceAfter=10
            )
            
            elements.append(Paragraph(f"Overall Summary: {total_bills} bills, {total_items} items, Total Amount: PKR {total_amount:,.2f}", stats_style))
            elements.append(Paragraph(f"Payment Status: Pending: {status_counts['Pending']}, Paid: {status_counts['Paid']}, Overdue: {status_counts['Overdue']}", stats_style))
            
            # Add page break before detailed table
            elements.append(PageBreak())
            
            # =========== TITLE FOR DETAILED TABLE ===========
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=22,
                textColor=colors.HexColor('#0f4d7d'),
                alignment=1,
                spaceAfter=15,
                spaceBefore=10
            )
            
            title = Paragraph("PURCHASES TABLE REPORT", title_style)
            elements.append(title)
            
            # Report date
            date_style = ParagraphStyle(
                'ReportDate',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#666666'),
                alignment=1,
                spaceAfter=20
            )
            
            report_date = f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            elements.append(Paragraph(report_date, date_style))
            
            # =========== MAIN DATA TABLE ===========
            table_data = [[
                'Bill No', 'Bill Date', 'Due Date', 'Supplier', 'Contact', 
                'Address', 'Items', 'Amount (PKR)', 'Status'
            ]]
            
            for purchase in all_purchases:
                bill_no, bill_date, due_date, supplier, contact, address, items, amount, status = purchase
                
                # Format empty values
                bill_no = bill_no or "N/A"
                bill_date = bill_date or "N/A"
                due_date = due_date or "N/A"
                supplier = supplier or "Unknown Supplier"
                contact = contact or "N/A"
                address = address or "N/A"
                items = items or 0
                amount = amount or 0
                status = status or "Pending"
                
                # Format amount with currency
                formatted_amount = f"PKR {amount:,.2f}"
                
                table_data.append([
                    bill_no,
                    bill_date,
                    due_date,
                    supplier,
                    contact,
                    address,
                    str(items),
                    formatted_amount,
                    status
                ])
            
            # Create table with adjusted column widths for landscape
            col_widths = [
                1.0*inch,  # Bill No
                1.0*inch,  # Bill Date
                1.0*inch,  # Due Date
                1.5*inch,  # Supplier
                1.2*inch,  # Contact
                1.5*inch,  # Address
                0.6*inch,  # Items
                1.2*inch,  # Amount
                0.8*inch   # Status
            ]
            
            main_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Style for the main table
            table_style = TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f4d7d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                
                # Grid lines
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
                
                # Zebra striping
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                
                # Column alignment
                ('ALIGN', (6, 1), (6, -1), 'CENTER'),  # Items column
                ('ALIGN', (7, 1), (7, -1), 'RIGHT'),   # Amount column
                
                # Status color highlighting
                ('TEXTCOLOR', (8, 1), (8, -1), self.get_status_color),
                
                # Highlight important columns
                ('FONTNAME', (7, 1), (7, -1), 'Helvetica-Bold'),
            ])
            
            main_table.setStyle(table_style)
            elements.append(main_table)
            
            elements.append(Spacer(1, 30))
            
            # Status color legend
            legend_style = ParagraphStyle(
                'Legend',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#666666'),
                alignment=0,
                spaceAfter=10
            )
            
            elements.append(Paragraph("Status Color Legend:", legend_style))
            elements.append(Paragraph("• Pending: Black", legend_style))
            elements.append(Paragraph("• Paid: Green", legend_style))
            elements.append(Paragraph("• Overdue: Red", legend_style))
            
            # Build PDF with footer on every page
            doc.build(elements, onFirstPage=self.add_footer, onLaterPages=self.add_footer)
            
            self.status_label.config(text="Suppliers purchase report generated successfully")
            messagebox.showinfo("Success", 
                              f"Purchases Table Report generated successfully!\n\n"
                              f"Total records: {total_bills}\n"
                              f"Total amount: PKR {total_amount:,.2f}\n\n"
                              f"Saved to:\n{file_path}")
            
            # Open the PDF
            os.startfile(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate suppliers report: {str(e)}")
            print(f"Error details: {e}")
            import traceback
            traceback.print_exc()
    
    def get_status_color(self, data, col, row):
        """Get color for status column based on value"""
        if data[col][row] == 'Paid':
            return colors.green
        elif data[col][row] == 'Overdue':
            return colors.red
        else:
            return colors.black
    
    def add_footer(self, canvas, doc):
        """Add footer to every page of the PDF"""
        # Save the current state of the canvas
        canvas.saveState()
        
        # Set font for footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#666666'))
        
        # Get page dimensions
        page_width = doc.pagesize[0]
        page_height = doc.pagesize[1]
        
        # Footer text - Left aligned
        left_text = "Software produced by Dukes Tech Services"
        
        # Footer text - Center
        center_text = "www.dukestechservices.com"
        
        # Footer text - Right aligned
        right_text = "Phone: +923097671363"
        
        # Draw footer at bottom of page
        footer_y = 0.4 * inch
        
        # Left aligned text
        canvas.drawString(0.5 * inch, footer_y, left_text)
        
        # Center text
        canvas.drawCentredString(page_width / 2, footer_y, center_text)
        
        # Right aligned text
        canvas.drawRightString(page_width - 0.5 * inch, footer_y, right_text)
        
        # Add page number (centered at bottom)
        page_num = f"Page {doc.page}"
        canvas.drawCentredString(page_width / 2, 0.2 * inch, page_num)
        
        # Restore the canvas state
        canvas.restoreState()
    
    # =========== REPORT METHODS ===========
    
    def on_report_type_change(self):
        """Handle report type change"""
        report_type = self.report_type.get()
        if report_type == "custom":
            self.custom_frame.pack(fill=X, pady=(10, 0))
        else:
            self.custom_frame.pack_forget()
    
    def generate_report(self):
        """Generate purchases report with flexible date handling"""
        report_type = self.report_type.get()
        
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Get all bills from database
            cur.execute('''
                SELECT BillDate, BillNo, TotalAmount, TotalItems, Supplier, PaymentStatus, DueDate
                FROM Purchases 
                ORDER BY BillDate DESC
            ''')
            all_bills = cur.fetchall()
            
            self.report_data = []
            
            if report_type == "daily":
                # Filter for today
                for bill in all_bills:
                    bill_date = bill[0]
                    if bill_date:
                        try:
                            # Try different date formats
                            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                                try:
                                    parsed_date = datetime.datetime.strptime(bill_date, fmt)
                                    if parsed_date.strftime("%Y-%m-%d") == self.current_date:
                                        self.report_data.append(bill)
                                    break
                                except:
                                    continue
                        except:
                            # Simple string comparison as fallback
                            if self.current_date in str(bill_date):
                                self.report_data.append(bill)
                                
            elif report_type == "weekly":
                # Filter for last 7 days
                for bill in all_bills:
                    bill_date = bill[0]
                    if bill_date:
                        try:
                            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                                try:
                                    parsed_date = datetime.datetime.strptime(bill_date, fmt)
                                    days_diff = (datetime.datetime.now() - parsed_date).days
                                    if 0 <= days_diff < 7:
                                        self.report_data.append(bill)
                                    break
                                except:
                                    continue
                        except:
                            pass
                            
            elif report_type == "monthly":
                # Filter for current month
                current_month = datetime.datetime.now().strftime("%Y-%m")
                for bill in all_bills:
                    bill_date = bill[0]
                    if bill_date and current_month in bill_date:
                        self.report_data.append(bill)
                        
            elif report_type == "custom":
                start_date = self.start_date.get()
                end_date = self.end_date.get()
                
                if not start_date or not end_date:
                    messagebox.showerror("Error", "Please select both start and end dates")
                    return
                
                # Filter by custom range
                for bill in all_bills:
                    bill_date = bill[0]
                    if bill_date:
                        try:
                            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                                try:
                                    parsed_date = datetime.datetime.strptime(bill_date, fmt)
                                    parsed_start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                                    parsed_end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                                    if parsed_start <= parsed_date <= parsed_end:
                                        self.report_data.append(bill)
                                    break
                                except:
                                    continue
                        except:
                            pass
            
            print(f"Generated {report_type} report with {len(self.report_data)} bills")
            
            # Update report display
            self.update_report_display()
            
            self.status_label.config(text=f"Generated {report_type} report with {len(self.report_data)} bills")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
            print(f"Error details: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.config(text="Error generating report")
    
    def update_report_display(self):
        """Update the report treeview with data"""
        self.report_tree.delete(*self.report_tree.get_children())
        
        if not self.report_data:
            # Clear any existing labels in the treeview frame
            for widget in self.report_tree.winfo_children():
                if isinstance(widget, Label):
                    widget.destroy()
            return
        
        total_amount = 0
        total_items = 0
        for row in self.report_data:
            bill_date, bill_no, amount, items, supplier, status, due_date = row
            
            # Format bill date
            formatted_date = bill_date or "N/A"
            if bill_date:
                try:
                    # Try different date formats
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                        try:
                            parsed_date = datetime.datetime.strptime(bill_date, fmt)
                            formatted_date = parsed_date.strftime("%d/%m/%Y")
                            break
                        except:
                            continue
                except:
                    pass
            
            formatted_amount = f"PKR {amount:,.2f}" if amount else "PKR 0.00"
            total_amount += amount if amount else 0
            total_items += items if items else 0
            
            # Format status with symbols
            display_status = status or "Pending"
            if status == "Overdue":
                display_status = "⚠ " + status
            elif status == "Paid":
                display_status = "✓ " + status
            elif not status:
                display_status = "Pending"
            
            # Format due date
            formatted_due_date = due_date or "N/A"
            if due_date:
                try:
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                        try:
                            parsed_due = datetime.datetime.strptime(due_date, fmt)
                            formatted_due_date = parsed_due.strftime("%d/%m/%Y")
                            break
                        except:
                            continue
                except:
                    pass
            
            self.report_tree.insert("", END, values=(
                formatted_date,
                bill_no,
                formatted_amount,
                items or 0,
                supplier or "Unknown Supplier",
                display_status,
                formatted_due_date
            ))
        
        # Add total row if there's data
        if self.report_data:
            self.report_tree.insert("", END, values=(
                "TOTAL", "", f"PKR {total_amount:,.2f}", total_items, "", "", ""
            ), tags=('total',))
            self.report_tree.tag_configure('total', background='#e8f5e9', font=('Segoe UI', 10, 'bold'))
    
    # =========== STATISTICS METHODS ===========
    
    def update_quick_stats(self):
        """Update quick statistics cards with proper date handling"""
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            today_str = self.current_date
            
            # Get all bills for calculations
            cur.execute('''
                SELECT BillDate, TotalAmount FROM Purchases
            ''')
            all_bills = cur.fetchall()
            
            # TODAY'S PURCHASES - Fixed
            today_purchases = 0
            for bill_date, amount in all_bills:
                if bill_date:
                    try:
                        # Try different date formats
                        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                            try:
                                parsed_date = datetime.datetime.strptime(bill_date, fmt)
                                if parsed_date.strftime("%Y-%m-%d") == today_str:
                                    today_purchases += amount if amount else 0
                                break
                            except:
                                continue
                    except:
                        # Simple string comparison as fallback
                        if today_str in str(bill_date):
                            today_purchases += amount if amount else 0
            
            self.today_purchases_label.config(text=f"PKR {today_purchases:,.2f}")
            
            # WEEKLY PURCHASES (last 7 days)
            weekly_purchases = 0
            for bill_date, amount in all_bills:
                if bill_date:
                    try:
                        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                            try:
                                parsed_date = datetime.datetime.strptime(bill_date, fmt)
                                days_diff = (datetime.datetime.now() - parsed_date).days
                                if 0 <= days_diff < 7:
                                    weekly_purchases += amount if amount else 0
                                break
                            except:
                                continue
                    except:
                        pass
            
            self.weekly_purchases_label.config(text=f"PKR {weekly_purchases:,.2f}")
            
            # MONTHLY PURCHASES (current month) - Fixed
            monthly_purchases = 0
            current_month = datetime.datetime.now().strftime("%Y-%m")
            for bill_date, amount in all_bills:
                if bill_date:
                    # Try to parse and compare month
                    try:
                        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
                            try:
                                parsed_date = datetime.datetime.strptime(bill_date, fmt)
                                if parsed_date.strftime("%Y-%m") == current_month:
                                    monthly_purchases += amount if amount else 0
                                break
                            except:
                                continue
                    except:
                        # Simple string comparison as fallback
                        if current_month in str(bill_date):
                            monthly_purchases += amount if amount else 0
            
            self.monthly_purchases_label.config(text=f"PKR {monthly_purchases:,.2f}")
            
            # TOTAL BILLS
            total_bills = len(all_bills)
            self.total_bills_label.config(text=f"{total_bills:,}")
            
            print(f"Stats updated: Today={today_purchases}, Weekly={weekly_purchases}, Monthly={monthly_purchases}, Total={total_bills}")
            
        except Exception as e:
            print(f"Error updating stats: {e}")
            import traceback
            traceback.print_exc()
    
    # =========== EXPORT METHODS ===========
    
    def export_to_excel(self):
        """Export COMPLETE bill details to Excel"""
        try:
            if not self.report_data:
                messagebox.showinfo("Info", "No data to export. Please generate a report first.")
                return
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Complete Purchase Report",
                initialfile=f"complete_purchase_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not file_path:
                return
            
            conn, cur = self.get_db_connection()
            if not conn:
                return
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Sheet 1: Bill Summary
                summary_data = []
                for row in self.report_data:
                    bill_date, bill_no, amount, items, supplier, status, due_date = row
                    summary_data.append({
                        'Bill Date': bill_date,
                        'Bill No': bill_no,
                        'Total Amount': amount or 0,
                        'Items Count': items or 0,
                        'Supplier': supplier or "Unknown Supplier",
                        'Payment Status': status,
                        'Due Date': due_date or "N/A"
                    })
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Bill Summary', index=False)
                
                # Sheet 2: Detailed Bill Information
                detailed_data = []
                for row in self.report_data:
                    bill_no = row[1]
                    
                    cur.execute('''
                        SELECT BillNo, BillDate, DueDate, Supplier, Contact, Address, 
                               TotalAmount, TotalItems, PaymentStatus
                        FROM Purchases 
                        WHERE BillNo = ?
                    ''', (bill_no,))
                    
                    bill_details = cur.fetchone()
                    
                    if bill_details:
                        detailed_data.append({
                            'Bill No': bill_details[0],
                            'Bill Date': bill_details[1],
                            'Due Date': bill_details[2],
                            'Supplier': bill_details[3] or "Unknown Supplier",
                            'Contact': bill_details[4] or "N/A",
                            'Address': bill_details[5] or "N/A",
                            'Total Amount': bill_details[6] or 0,
                            'Total Items': bill_details[7] or 0,
                            'Payment Status': bill_details[8]
                        })
                
                df_detailed = pd.DataFrame(detailed_data)
                df_detailed.to_excel(writer, sheet_name='Bill Details', index=False)
                
                # Sheet 3: Bill Items
                items_data = []
                for row in self.report_data:
                    bill_no = row[1]
                    
                    cur.execute('''
                        SELECT ReferenceNo, Description, Quantity, UnitPrice, TaxRate, Amount
                        FROM PurchaseItems
                        WHERE BillNo = ?
                        ORDER BY ID
                    ''', (bill_no,))
                    
                    bill_items = cur.fetchall()
                    
                    for item in bill_items:
                        items_data.append({
                            'Bill No': bill_no,
                            'Reference No': item[0],
                            'Description': item[1],
                            'Quantity': item[2],
                            'Unit Price': item[3],
                            'Tax Rate': item[4],
                            'Amount': item[5]
                        })
                
                df_items = pd.DataFrame(items_data)
                df_items.to_excel(writer, sheet_name='Bill Items', index=False)
                
                # Sheet 4: Summary Statistics
                amounts = [row[2] for row in self.report_data if row[2]]
                
                if amounts:
                    total_purchases = sum(amounts)
                    avg_purchase = total_purchases / len(amounts) if len(amounts) > 0 else 0
                    highest_purchase = max(amounts) if amounts else 0
                    lowest_purchase = min(amounts) if amounts else 0
                    total_items = sum(row[3] for row in self.report_data if row[3])
                    bills = len(self.report_data)
                    
                    # Count payment statuses
                    pending_count = sum(1 for row in self.report_data if row[5] == "Pending" or not row[5])
                    paid_count = sum(1 for row in self.report_data if row[5] == "Paid")
                    overdue_count = sum(1 for row in self.report_data if row[5] == "Overdue")
                    
                    summary_stats = {
                        'Metric': ['Total Purchases', 'Average Purchase', 'Highest Purchase', 'Lowest Purchase', 
                                  'Total Items', 'Total Bills', 'Pending Bills', 'Paid Bills', 'Overdue Bills'],
                        'Value': [
                            f"PKR {total_purchases:,.2f}",
                            f"PKR {avg_purchase:,.2f}",
                            f"PKR {highest_purchase:,.2f}",
                            f"PKR {lowest_purchase:,.2f}",
                            f"{total_items:,}",
                            f"{bills:,}",
                            f"{pending_count:,}",
                            f"{paid_count:,}",
                            f"{overdue_count:,}"
                        ]
                    }
                    
                    df_stats = pd.DataFrame(summary_stats)
                    df_stats.to_excel(writer, sheet_name='Summary Statistics', index=False)
            
            self.status_label.config(text=f"Complete report exported to {os.path.basename(file_path)}")
            messagebox.showinfo("Success", f"Complete purchase report exported successfully!\n\nSaved to:\n{file_path}")
            
            # Open the Excel file
            os.startfile(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export to Excel: {str(e)}")
    
    def export_to_pdf(self):
        """Export COMPLETE bill details to PDF with footer on every page"""
        try:
            if not self.report_data:
                messagebox.showinfo("Info", "No data to export. Please generate a report first.")
                return
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Complete Purchase Report",
                initialfile=f"complete_purchase_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not file_path:
                return
            
            conn, cur = self.get_db_connection()
            if not conn:
                return
            
            # Create PDF document
            doc = SimpleDocTemplate(
                file_path, 
                pagesize=landscape(letter),
                topMargin=0.75*inch,
                bottomMargin=1.0*inch,  # Increased bottom margin for footer
                leftMargin=0.5*inch,
                rightMargin=0.5*inch
            )
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
            title = Paragraph(f"COMPLETE PURCHASE REPORT - {report_type}", title_style)
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
            
            # ==========================================
            # NEW: SUMMARY STATISTICS & MASTER BILL LIST
            # ==========================================
            
            summary_style = ParagraphStyle(
                'Summary',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor(self.accent_color),
                alignment=0,
                spaceAfter=10
            )
            
            elements.append(Paragraph("SUMMARY STATISTICS", summary_style))
            
            # Calculate summary statistics based on report_data structure:
            # bill_date, bill_no, amount, items, supplier, status, due_date
            amounts = [row[2] for row in self.report_data if row[2]]
            total_purchases = sum(amounts) if amounts else 0
            avg_purchase = total_purchases / len(amounts) if len(amounts) > 0 else 0
            highest_purchase = max(amounts) if amounts else 0
            lowest_purchase = min(amounts) if amounts else 0
            total_items = sum(row[3] for row in self.report_data if row[3])
            transactions = len(self.report_data)
            
            summary_data = [
                ['Total Purchases:', f"PKR {total_purchases:,.2f}"],
                ['Average Purchase:', f"PKR {avg_purchase:,.2f}"],
                ['Highest Purchase:', f"PKR {highest_purchase:,.2f}"],
                ['Lowest Purchase:', f"PKR {lowest_purchase:,.2f}"],
                ['Total Items:', f"{total_items:,}"],
                ['Total Bills:', f"{transactions:,}"]
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
            
            # Detailed Master Bill List
            invoice_title = Paragraph("DETAILED BILL LIST", summary_style)
            elements.append(invoice_title)
            elements.append(Spacer(1, 10))
            
            # Create master table with column widths adapted for landscape 
            table_data = [['Date', 'Bill No', 'Supplier', 'Amount (PKR)', 'Items', 'Status', 'Due Date']]
            
            for row in self.report_data:
                bill_date, bill_no, amount, items, supplier, status, due_date = row
                
                # Format supplier name to prevent overflow
                formatted_supplier = (supplier or "Unknown Supplier")[:25] + "..." if len(supplier or "") > 25 else (supplier or "Unknown Supplier")
                
                table_data.append([
                    bill_date or "N/A",
                    bill_no or "N/A",  
                    formatted_supplier,
                    f"{amount:,.2f}" if amount else "0.00",
                    str(items or 0),
                    status or "Pending",
                    due_date or "N/A"
                ])
            
            # Add total row to the master list
            table_data.append(['', '', 'TOTAL:', f"{total_purchases:,.2f}", str(total_items), '', ''])
            
            # Configure table structure
            list_table = Table(table_data, colWidths=[70, 120, 150, 90, 40, 70, 70]) 
            list_table.setStyle(TableStyle([
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
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))
            
            elements.append(list_table)
            elements.append(Spacer(1, 20))
            
            # ==========================================
            # END OF NEW SUMMARY SECTION
            # ==========================================
            
            # Process each individual bill for detailed breakdown
            for idx, row in enumerate(self.report_data):
                bill_date, bill_no, amount, items, supplier, status, due_date = row
                
                # Add page break before EVERY individual bill so they are kept isolated
                elements.append(PageBreak())
                
                # Bill Header
                bill_title_style = ParagraphStyle(
                    'BillTitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.HexColor(self.accent_color),
                    alignment=0,
                    spaceAfter=10
                )
                
                elements.append(Paragraph(f"PURCHASE BILL #{bill_no}", bill_title_style))
                
                # Get complete bill details
                cur.execute('''
                    SELECT BillNo, BillDate, DueDate, Supplier, Contact, Address, 
                           TotalAmount, TotalItems, PaymentStatus
                    FROM Purchases 
                    WHERE BillNo = ?
                ''', (bill_no,))
                
                bill_details = cur.fetchone()
                
                if bill_details:
                    # Bill Information Table
                    info_data = [
                        ['Field', 'Value'],
                        ['Bill No:', bill_details[0]],
                        ['Supplier:', bill_details[3] or "Unknown Supplier"],
                        ['Contact:', bill_details[4] or "N/A"],
                        ['Address:', bill_details[5] or "N/A"],
                        ['Bill Date:', bill_details[1]],
                        ['Due Date:', bill_details[2]],
                        ['Payment Status:', bill_details[8]],
                        ['Total Items:', str(bill_details[7])],
                        ['Total Amount:', f"PKR {bill_details[6]:,.2f}"]
                    ]
                    
                    info_table = Table(info_data, colWidths=[200, 300])
                    info_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f4d7d')),
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
                    
                    # Get bill items
                    cur.execute('''
                        SELECT ReferenceNo, Description, Quantity, UnitPrice, TaxRate, Amount
                        FROM PurchaseItems
                        WHERE BillNo = ?
                        ORDER BY ID
                    ''', (bill_no,))
                    
                    bill_items = cur.fetchall()
                    
                    if bill_items:
                        # Items Table
                        items_title = Paragraph("Purchase Items:", styles['Heading3'])
                        elements.append(items_title)
                        elements.append(Spacer(1, 10))
                        
                        items_data = [['Reference', 'Description', 'Qty', 'Unit Price', 'Tax %', 'Amount (PKR)']]
                        
                        for item in bill_items:
                            items_data.append([
                                item[0],
                                item[1],
                                str(item[2]),
                                f"{item[3]:,.2f}",
                                f"{item[4]:.2f}",
                                f"{item[5]:,.2f}"
                            ])
                        
                        # Calculate totals
                        total_qty = sum(item[2] for item in bill_items)
                        total_amount = sum(item[5] for item in bill_items)
                        
                        items_data.append(['', '', '', '', 'Total Items:', str(len(bill_items))])
                        items_data.append(['', '', '', '', 'Total Quantity:', str(total_qty)])
                        items_data.append(['', '', '', '', 'Total Amount:', f"PKR {total_amount:,.2f}"])
                        
                        items_table = Table(items_data, colWidths=[80, 150, 40, 70, 50, 80])
                        items_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f4d7d')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
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
            
            # Footer summary
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#666666'),
                alignment=1
            )
            
            elements.append(Paragraph(f"Report includes complete purchase details for {len(self.report_data)} bills", footer_style))
            elements.append(Paragraph(f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
            
            # Build PDF with footer on every page
            doc.build(elements, onFirstPage=self.add_footer, onLaterPages=self.add_footer)
            
            self.status_label.config(text="Complete purchase report exported to PDF")
            messagebox.showinfo("Success", f"Complete purchase PDF report generated successfully!\n\nSaved to:\n{file_path}")
            
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
        app = PurchasesDashboard(root)
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