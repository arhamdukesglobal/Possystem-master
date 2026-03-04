# Sales.py
from tkinter import *
from tkinter import ttk, messagebox
import sqlite3
import datetime
from datetime import date, timedelta
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, BaseDocTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus.flowables import Flowable
import os
from tkinter import filedialog
import warnings
import time
import traceback
import json
import webbrowser

warnings.filterwarnings('ignore')

class FooterCanvas:
    """Canvas class that adds footer to every page"""
    def __init__(self):
        pass
    
    @staticmethod
    def add_footer(canvas, doc):
        """Add footer to the canvas"""
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        footer_text = "Software produced by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363"
        canvas.drawCentredString(doc.width / 2.0 + doc.leftMargin, 0.3 * inch, footer_text)
        canvas.restoreState()

class TrackerClass:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1300x750+50+50")  # Reduced size
        self.root.title("Order Tracking System | Inventory Management")
        self.root.config(bg="#f0f0f0")
        self.root.focus_force()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set minimum window size
        self.root.minsize(1100, 650)  # Reduced minimum size
        
        # =========== Variables ==========
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.selected_invoice_id = None
        self.selected_order_id = None
        self.report_data = []
        self.sort_directions = {}
        self.after_ids = []
        self.is_closing = False
        
        # Order tracking variables - UPDATED: 9 stages
        self.orders = []
        self.current_order_id = 1
        self.stages = [
            "Order Confirmation", 
            "Shop Manager", 
            "Cutting Processes", 
            "Handwork Embroidery Unit", 
            "Stitching Unit", 
            "Quality Control", 
            "Final Pressing & Packing", 
            "Back to Shop", 
            "Delivery"
        ]
        # Alternative stage names mapping (to handle variations)
        self.stage_aliases = {
            "Order Confirmed": "Order Confirmation",
            "Order Confirm": "Order Confirmation",
            "Confirmed": "Order Confirmation",
            "Shop Mgr": "Shop Manager",
            "Manager": "Shop Manager",
            "Cutting": "Cutting Processes",
            "Handwork": "Handwork Embroidery Unit",
            "Embroidery": "Handwork Embroidery Unit",
            "Stitching": "Stitching Unit",
            "QC": "Quality Control",
            "Quality": "Quality Control",
            "Pressing": "Final Pressing & Packing",
            "Packing": "Final Pressing & Packing",
            "Back": "Back to Shop",
            "Delivered": "Delivery"
        }
        self.stage_buttons = []
        self.current_selected_stage = None  # Track currently selected stage
        
        # Database connection
        self.db_path = r'Possystem.db'
        self.conn = None
        self.cursor = None
        
        # Load existing order data
        self.load_order_data()
        
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
        self.hover_color = "#e3f2fd"
        
        # Configure root background
        self.root.config(bg=self.bg_color)
        
        # =========== Main Container ==========
        self.main_container = Frame(self.root, bg=self.bg_color)
        self.main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)  # Reduced padding
        
        # =========== Header ==========
        header_frame = Frame(self.main_container, bg=self.header_bg, height=60)  # Reduced height
        header_frame.pack(fill=X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Title
        title_frame = Frame(header_frame, bg=self.header_bg)
        title_frame.pack(side=LEFT, fill=Y, padx=15)
        
        Label(title_frame, text="📦 ORDER TRACKING", 
              font=("Segoe UI", 16, "bold"), bg=self.header_bg,  # Smaller font
              fg="white").pack(pady=15)
        
        # Live Date and Time
        time_frame = Frame(header_frame, bg=self.header_bg)
        time_frame.pack(side=RIGHT, fill=Y, padx=15)
        
        self.date_time_label = Label(time_frame, text="", 
                                    font=("Segoe UI", 10),  # Smaller font
                                    bg=self.header_bg, fg="white")
        self.date_time_label.pack(pady=15)
        
        # =========== Main Content Area ==========
        self.content_frame = Frame(self.main_container, bg=self.bg_color)
        self.content_frame.pack(fill=BOTH, expand=True)
        
        # Configure grid for content area - ADJUSTED RATIO
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=4)  # Left panel (Active Orders) - 40%
        self.content_frame.grid_columnconfigure(1, weight=6)  # Right panel (Tracker) - 60%
        
        # =========== Left Panel - Active Orders ==========
        self.left_panel = Frame(self.content_frame, bg=self.card_bg, bd=1, relief="solid",
                          highlightbackground=self.border_color, highlightthickness=1)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Header for Active Orders
        order_header = Frame(self.left_panel, bg=self.accent_color, height=35)  # Reduced height
        order_header.pack(fill=X)
        order_header.pack_propagate(False)
        
        Label(order_header, text="📋 ACTIVE ORDERS", font=("Segoe UI", 11, "bold"),  # Smaller font
              bg=self.accent_color, fg="white").pack(pady=8)
        
        # Search and filter controls
        control_frame = Frame(self.left_panel, bg=self.card_bg)
        control_frame.pack(fill=X, padx=8, pady=8)  # Reduced padding
        
        # Search section - COMPACT
        search_frame = Frame(control_frame, bg=self.card_bg)
        search_frame.pack(fill=X)
        
        Label(search_frame, text="Search:", font=("Segoe UI", 9),  # Smaller font
              bg=self.card_bg, fg=self.text_color).pack(side=LEFT, padx=(0, 5))
        
        self.search_var = StringVar()
        self.search_entry = Entry(search_frame, textvariable=self.search_var,
                                 font=("Segoe UI", 9), width=15,  # Smaller width
                                 relief="solid", bd=1)
        self.search_entry.pack(side=LEFT, padx=(0, 5))
        self.search_entry.bind('<Return>', self.search_orders)
        
        Button(search_frame, text="🔍", command=self.search_orders,  # Icon only
               font=("Segoe UI", 8), bg=self.accent_color, fg="white",
               cursor="hand2", relief="flat", width=2, height=1).pack(side=LEFT, padx=(0, 2))
        
        Button(search_frame, text="🔄", command=self.refresh_orders,  # Icon only
               font=("Segoe UI", 8), bg=self.info_color, fg="white",
               cursor="hand2", relief="flat", width=2, height=1).pack(side=LEFT)
        
        # Filter by status - COMPACT
        filter_frame = Frame(control_frame, bg=self.card_bg)
        filter_frame.pack(fill=X, pady=(5, 0))
        
        Label(filter_frame, text="Status:", font=("Segoe UI", 9),  # Smaller font
              bg=self.card_bg, fg=self.text_color).pack(side=LEFT, padx=(0, 5))
        
        self.status_filter = StringVar(value="All")
        status_options = ["All"] + self.stages
        
        status_menu = ttk.Combobox(filter_frame, textvariable=self.status_filter,
                                  values=status_options, state="readonly",
                                  font=("Segoe UI", 8), width=12)  # Smaller
        status_menu.pack(side=LEFT, padx=(0, 5))
        status_menu.bind("<<ComboboxSelected>>", self.filter_orders)
        
        # Stats display - SHOW ACTIVE AND DELIVERED COUNTS
        self.stats_label = Label(filter_frame, text="", font=("Segoe UI", 8),
                               bg=self.card_bg, fg=self.success_color)
        self.stats_label.pack(side=RIGHT)
        
        # Orders list container
        list_container = Frame(self.left_panel, bg=self.card_bg)
        list_container.pack(fill=BOTH, expand=True, padx=8, pady=(0, 5))
        
        # Treeview for orders
        tree_frame = Frame(list_container, bg=self.card_bg)
        tree_frame.pack(fill=BOTH, expand=True)
        
        # Create scrollbars
        scroll_y = Scrollbar(tree_frame, orient=VERTICAL)
        scroll_x = Scrollbar(tree_frame, orient=HORIZONTAL)
        
        # Create Treeview for orders
        self.orders_tree = ttk.Treeview(tree_frame, 
                                         columns=("Invoice", "Amount", "Customer", "Date", "Status", "Days"), 
                                         show="headings", 
                                         yscrollcommand=scroll_y.set,
                                         xscrollcommand=scroll_x.set,
                                         height=12)  # Reduced height
        
        # Configure scrollbars
        scroll_y.config(command=self.orders_tree.yview)
        scroll_x.config(command=self.orders_tree.xview)
        
        # Define columns - COMPACT
        columns = [
            ("Invoice", "Invoice", 80),
            ("Amount", "Amount", 85),
            ("Customer", "Customer", 100),
            ("Date", "Date", 70),
            ("Status", "Status", 110),
            ("Days", "Days", 45)
        ]
        
        for col_id, heading, width in columns:
            self.orders_tree.heading(col_id, text=heading)
            self.orders_tree.column(col_id, width=width, minwidth=40)
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                       background=self.card_bg,
                       foreground=self.text_color,
                       rowheight=22,  # Reduced row height
                       fieldbackground=self.card_bg,
                       font=("Segoe UI", 8))  # Smaller font
        style.map('Treeview', background=[('selected', self.hover_color)])
        
        # Pack treeview and scrollbars
        self.orders_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)
        scroll_x.pack(side=BOTTOM, fill=X)
        
        # Bind selection event
        self.orders_tree.bind('<<TreeviewSelect>>', self.on_order_select)
        
        # Action buttons frame
        self.action_frame = Frame(self.left_panel, bg=self.card_bg)
        self.action_frame.pack(fill=X, padx=8, pady=(0, 8))
        
        # Buttons in a row
        btn_frame = Frame(self.action_frame, bg=self.card_bg)
        btn_frame.pack(fill=X)
        
        Button(btn_frame, text="📄 Details", command=self.view_order_details,
               font=("Segoe UI", 8), bg=self.accent_color, fg="white",
               cursor="hand2", relief="flat", padx=5, pady=2).pack(side=LEFT, padx=(0, 2))
        
        Button(btn_frame, text="🖨️ Print", command=self.print_invoice,
               font=("Segoe UI", 8), bg=self.warning_color, fg="white",
               cursor="hand2", relief="flat", padx=5, pady=2).pack(side=LEFT, padx=2)
        
        Button(btn_frame, text="📊 Load", command=self.load_from_sales,
               font=("Segoe UI", 8), bg=self.success_color, fg="white",
               cursor="hand2", relief="flat", padx=5, pady=2).pack(side=LEFT, padx=2)
        
        # =========== Right Panel - Order Tracker ==========
        self.right_panel = Frame(self.content_frame, bg=self.card_bg, bd=1, relief="solid",
                           highlightbackground=self.border_color, highlightthickness=1)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Order Tracker Header
        tracker_header = Frame(self.right_panel, bg=self.accent_color, height=35)
        tracker_header.pack(fill=X)
        tracker_header.pack_propagate(False)
        
        Label(tracker_header, text="📊 ORDER TRACKER", font=("Segoe UI", 11, "bold"),
              bg=self.accent_color, fg="white").pack(pady=8)
        
        # Selected Order Info - COMPACT
        self.selected_info_frame = Frame(self.right_panel, bg="#f8f9fa", height=35)
        self.selected_info_frame.pack(fill=X, padx=8, pady=5)
        self.selected_info_frame.pack_propagate(False)
        
        self.selected_label = Label(self.selected_info_frame, text="No order selected", 
                                   font=("Segoe UI", 9), bg="#f8f9fa", fg=self.subtext_color)
        self.selected_label.pack(side=LEFT, padx=5, pady=8)
        
        # ===== NEW REDESIGNED PRODUCTION STAGES SECTION =====
        # Create a notebook (tabbed interface) for better organization
        self.tracker_notebook = ttk.Notebook(self.right_panel)
        self.tracker_notebook.pack(fill=BOTH, expand=True, padx=8, pady=(0, 5))
        
        # Style the notebook
        style.configure("TNotebook", background=self.card_bg)
        style.configure("TNotebook.Tab", padding=[5, 2], font=('Segoe UI', 8))
        
        # Tab 1: Production Stages (Grid View)
        self.stages_tab = Frame(self.tracker_notebook, bg=self.card_bg)
        self.tracker_notebook.add(self.stages_tab, text="📋 Stages")
        
        # Tab 2: Progress View (Timeline)
        self.progress_tab = Frame(self.tracker_notebook, bg=self.card_bg)
        self.tracker_notebook.add(self.progress_tab, text="📈 Progress")
        
        # Tab 3: History View
        self.history_tab = Frame(self.tracker_notebook, bg=self.card_bg)
        self.tracker_notebook.add(self.history_tab, text="📜 History")
        
        # === STAGES TAB - REDESIGNED (3x3 Compact Grid) ===
        stages_container = Frame(self.stages_tab, bg=self.card_bg)
        stages_container.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Title
        Label(stages_container, text="Production Stages", font=("Segoe UI", 10, "bold"),
              bg=self.card_bg, fg=self.text_color).pack(anchor="w", pady=(0, 5))
        
        # Create a frame for stage buttons with fixed size
        self.stages_grid = Frame(stages_container, bg=self.card_bg)
        self.stages_grid.pack(expand=True, fill=BOTH)
        
        # Configure grid weights
        for i in range(3):
            self.stages_grid.grid_columnconfigure(i, weight=1)
        for i in range(3):
            self.stages_grid.grid_rowconfigure(i, weight=1)
        
        # Create stage buttons (9 buttons in 3x3 grid)
        self.stage_buttons = []
        self.stage_button_map = {}  # Map button to stage name
        for i, stage in enumerate(self.stages):
            # Create abbreviated text for button
            display_text = stage
            if stage == "Handwork Embroidery Unit":
                display_text = "Handwork\nEmbroidery"
            elif stage == "Final Pressing & Packing":
                display_text = "Final\nPressing"
            elif stage == "Quality Control":
                display_text = "Quality\nControl"
            elif stage == "Stitching Unit":
                display_text = "Stitching"
            elif stage == "Back to Shop":
                display_text = "Back to\nShop"
            elif stage == "Order Confirmation":
                display_text = "Order\nConf."
            elif stage == "Cutting Processes":
                display_text = "Cutting"
            elif stage == "Shop Manager":
                display_text = "Shop\nManager"
            elif stage == "Delivery":
                display_text = "Delivery"
            
            btn = Button(self.stages_grid,
                        text=display_text,
                        command=lambda s=stage: self.select_stage(s),
                        font=("Segoe UI", 8, "bold"),
                        bg='#e0e0e0',
                        fg='#2c3e50',
                        relief=RAISED,
                        bd=1,
                        cursor="hand2",
                        height=2,
                        width=12)
            btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky="nsew")
            self.stage_buttons.append(btn)
            self.stage_button_map[btn] = stage  # Map button to stage
        
        # === PROGRESS TAB - REDESIGNED (Visual Timeline) ===
        progress_container = Frame(self.progress_tab, bg=self.card_bg)
        progress_container.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        Label(progress_container, text="Progress Timeline", font=("Segoe UI", 10, "bold"),
              bg=self.card_bg, fg=self.text_color).pack(anchor="w", pady=(0, 5))
        
        # Progress canvas with fixed height
        self.progress_canvas = Canvas(progress_container, height=180, bg='white', 
                                     highlightthickness=1, highlightbackground=self.border_color)
        self.progress_canvas.pack(fill=X, pady=(0, 10))
        
        # Progress percentage and status
        self.progress_info = Frame(progress_container, bg=self.card_bg)
        self.progress_info.pack(fill=X, pady=(0, 5))
        
        self.progress_percent_label = Label(self.progress_info, text="Progress: 0%", 
                                          font=("Segoe UI", 9, "bold"),
                                          bg=self.card_bg, fg=self.success_color)
        self.progress_percent_label.pack(side=LEFT)
        
        self.current_stage_label = Label(self.progress_info, text="Current: None",
                                        font=("Segoe UI", 9),
                                        bg=self.card_bg, fg=self.text_color)
        self.current_stage_label.pack(side=RIGHT)
        
        # Add a mini stage indicator
        self.stage_indicator_frame = Frame(progress_container, bg=self.card_bg)
        self.stage_indicator_frame.pack(fill=X, pady=(0, 5))
        
        # === HISTORY TAB - NEW ===
        history_container = Frame(self.history_tab, bg=self.card_bg)
        history_container.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        Label(history_container, text="Stage History", font=("Segoe UI", 10, "bold"),
              bg=self.card_bg, fg=self.text_color).pack(anchor="w", pady=(0, 5))
        
        # History listbox with scrollbar
        history_list_frame = Frame(history_container, bg=self.card_bg)
        history_list_frame.pack(fill=BOTH, expand=True)
        
        scroll_history = Scrollbar(history_list_frame)
        scroll_history.pack(side=RIGHT, fill=Y)
        
        self.history_listbox = Listbox(history_list_frame, 
                                      yscrollcommand=scroll_history.set,
                                      font=("Segoe UI", 9),
                                      bg='white',
                                      relief="solid",
                                      bd=1,
                                      height=8)
        self.history_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        
        scroll_history.config(command=self.history_listbox.yview)
        
        # ===== ACTION BUTTONS - ENLARGED =====
        action_buttons_frame = Frame(self.right_panel, bg=self.card_bg)
        action_buttons_frame.pack(fill=X, padx=8, pady=(0, 8))
        
        # Create a grid for action buttons (2x2)
        action_grid = Frame(action_buttons_frame, bg=self.card_bg)
        action_grid.pack(fill=X)
        
        # Configure grid
        for i in range(4):
            action_grid.grid_columnconfigure(i, weight=1)
        
        # Action buttons - LARGER SIZE
        btn_update = Button(action_grid, text="🔄 UPDATE STAGE", 
                          command=self.update_stage,
                          font=("Segoe UI", 9, "bold"),
                          bg=self.info_color,
                          fg='white',
                          relief=RAISED,
                          bd=1,
                          cursor="hand2",
                          height=2)  # Increased height
        btn_update.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        btn_delete = Button(action_grid, text="🗑️ DELETE ORDER", 
                          command=self.delete_order,
                          font=("Segoe UI", 9, "bold"),
                          bg=self.danger_color,
                          fg='white',
                          relief=RAISED,
                          bd=1,
                          cursor="hand2",
                          height=2)  # Increased height
        btn_delete.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        btn_single = Button(action_grid, text="📄 SINGLE PDF", 
                          command=self.generate_single_pdf,
                          font=("Segoe UI", 9, "bold"),
                          bg="#9b59b6",
                          fg='white',
                          relief=RAISED,
                          bd=1,
                          cursor="hand2",
                          height=2)  # Increased height
        btn_single.grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        
        btn_all = Button(action_grid, text="📊 ALL PDF", 
                       command=self.generate_all_pdfs,
                       font=("Segoe UI", 9, "bold"),
                       bg="#e67e22",
                       fg='white',
                       relief=RAISED,
                       bd=1,
                       cursor="hand2",
                       height=2)  # Increased height
        btn_all.grid(row=0, column=3, padx=2, pady=2, sticky="ew")
        
        # Add hover effects
        for btn in [btn_update, btn_delete, btn_single, btn_all]:
            btn.bind("<Enter>", lambda e, b=btn, c=btn.cget('bg'): self.on_button_hover(e, b, c))
            btn.bind("<Leave>", lambda e, b=btn, c=btn.cget('bg'): self.on_button_leave(e, b, c))
        
        # =========== Footer ==========
        self.footer_frame = Frame(self.main_container, bg=self.accent_color, height=25)
        self.footer_frame.pack(side=BOTTOM, fill=X, pady=(5, 0))
        self.footer_frame.pack_propagate(False)
        
        self.status_label = Label(self.footer_frame, text="Ready", font=("Segoe UI", 8),
                                 bg=self.accent_color, fg="white")
        self.status_label.pack(side=LEFT, padx=10, pady=4)
        
        self.time_label = Label(self.footer_frame, text="", font=("Segoe UI", 8),
                               bg=self.accent_color, fg="white")
        self.time_label.pack(side=RIGHT, padx=10, pady=4)
        
        # =========== Initialize ==========
        self.refresh_orders()
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
        self.save_order_data()
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
    
    def darken_color(self, hex_color, factor=0.8):
        """Darken a hex color"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darker = tuple(int(c * factor) for c in rgb)
        return f'#{darker[0]:02x}{darker[1]:02x}{darker[2]:02x}'
    
    def on_button_hover(self, event, button, color):
        """Handle button hover"""
        button.configure(bg=self.darken_color(color))
    
    def on_button_leave(self, event, button, color):
        """Handle button leave"""
        button.configure(bg=color)
    
    # =========== ORDER DATA MANAGEMENT ===========
    
    def load_order_data(self):
        """Load order data from JSON file"""
        try:
            if os.path.exists('order_tracking_data.json'):
                with open('order_tracking_data.json', 'r') as f:
                    data = json.load(f)
                    self.orders = data.get('orders', [])
                    self.current_order_id = data.get('current_order_id', 1)
                    print(f"Loaded {len(self.orders)} orders from save file")
        except Exception as e:
            print(f"Error loading order data: {e}")
            self.orders = []
            self.current_order_id = 1
    
    def save_order_data(self):
        """Save order data to JSON file"""
        try:
            data = {
                'orders': self.orders,
                'current_order_id': self.current_order_id,
                'last_saved': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open('order_tracking_data.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving order data: {e}")
    
    # =========== ORDER MANAGEMENT METHODS ===========
    
    def normalize_stage(self, stage):
        """Convert stage name to standard format"""
        if not stage:
            return "Order Confirmation"
        
        # If already in stages list, return as is
        if stage in self.stages:
            return stage
        
        # Check aliases
        for alias, standard in self.stage_aliases.items():
            if alias.lower() in stage.lower() or stage.lower() in alias.lower():
                return standard
        
        # Default fallback
        return "Order Confirmation"
    
    def get_stage_index(self, stage):
        """Get index of stage, handling variations"""
        normalized_stage = self.normalize_stage(stage)
        try:
            return self.stages.index(normalized_stage)
        except ValueError:
            return 0
    
    def calculate_days_in_progress(self, order_date):
        """Calculate days since order was placed"""
        try:
            if not order_date:
                return 0
            order_dt = datetime.datetime.strptime(order_date, "%Y-%m-%d")
            current_dt = datetime.datetime.now()
            return (current_dt - order_dt).days
        except:
            return 0
    
    def refresh_orders(self):
        """Refresh the orders list from database and tracking data"""
        try:
            # Clear existing items
            self.orders_tree.delete(*self.orders_tree.get_children())
            
            # Filter out delivered orders from active tracking for display
            active_orders = [o for o in self.orders if o.get('status') != 'Delivery']
            
            # Load from database for new orders
            self.load_orders_from_database()
            
            # Add orders from tracking data (non-delivered)
            for order in active_orders:
                # Calculate days in progress
                days_in_progress = self.calculate_days_in_progress(order.get('date'))
                status = self.normalize_stage(order.get('status', 'Order Confirmation'))
                
                self.orders_tree.insert("", END, values=(
                    order.get('invoice_no', 'N/A'),
                    f"PKR {order.get('amount', 0):,.0f}",  # No decimals
                    order.get('customer', 'N/A')[:15] + "..." if len(order.get('customer', '')) > 15 else order.get('customer', 'N/A'),
                    order.get('date', 'N/A'),
                    status[:12] + "..." if len(status) > 12 else status,
                    f"{days_in_progress}d"
                ))
            
            # Update stats - SHOW ACTIVE AND DELIVERED COUNTS
            total_active = len(active_orders)
            delivered_count = len([o for o in self.orders if o.get('status') == 'Delivery'])
            self.stats_label.config(text=f"Active: {total_active} | Delivered: {delivered_count}")
            self.status_label.config(text=f"Loaded {total_active} active orders, {delivered_count} delivered")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh orders: {str(e)}")
            self.status_label.config(text="Error loading orders")
    
    def load_orders_from_database(self):
        """Load orders from the database"""
        conn, cur = self.get_db_connection()
        if not conn:
            return
        
        try:
            # Query for invoices from the last 60 days
            sixty_days_ago = (datetime.datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            
            cur.execute('''
                SELECT invoice_no, total_amount, customer_name, 
                       DATE(created_at) as date
                FROM invoices 
                WHERE DATE(created_at) >= ?
                ORDER BY created_at DESC
                LIMIT 150
            ''', (sixty_days_ago,))
            
            invoices = cur.fetchall()
            
            for invoice in invoices:
                invoice_no, amount, customer, date_str = invoice
                
                # Check if this invoice is already in our tracking system
                existing_order = next((o for o in self.orders if o.get('invoice_no') == invoice_no), None)
                
                if existing_order:
                    # Skip if delivered
                    if existing_order.get('status') == 'Delivery':
                        continue
                    status = self.normalize_stage(existing_order.get('status', 'Order Confirmation'))
                else:
                    status = 'Order Confirmation'
                
                # Calculate days in progress
                days_in_progress = self.calculate_days_in_progress(date_str)
                
                self.orders_tree.insert("", END, values=(
                    invoice_no,
                    f"PKR {amount:,.0f}" if amount else "PKR 0",
                    (customer or "Walk-in")[:12] + "..." if len(customer or "") > 12 else (customer or "Walk-in"),
                    date_str,
                    status[:12] + "..." if len(status) > 12 else status,
                    f"{days_in_progress}d"
                ))
                
        except Exception as e:
            print(f"Error loading from database: {e}")
    
    def search_orders(self, event=None):
        """Search orders by invoice number or customer name"""
        search_text = self.search_var.get().strip().lower()
        
        if not search_text:
            self.refresh_orders()
            return
        
        # Show all items first
        for item in self.orders_tree.get_children():
            self.orders_tree.item(item, tags=())
        
        # Then filter
        for item in self.orders_tree.get_children():
            values = self.orders_tree.item(item)['values']
            if values:
                invoice_no = str(values[0]).lower()
                customer = str(values[2]).lower()
                
                if search_text not in invoice_no and search_text not in customer:
                    self.orders_tree.item(item, tags=('hidden',))
        
        # Hide filtered items
        self.orders_tree.tag_configure('hidden', foreground='gray')
    
    def filter_orders(self, event=None):
        """Filter orders by status"""
        status_filter = self.status_filter.get()
        
        if status_filter == "All":
            # Show all items
            for item in self.orders_tree.get_children():
                self.orders_tree.item(item, tags=())
        else:
            # Filter by status
            for item in self.orders_tree.get_children():
                values = self.orders_tree.item(item)['values']
                if values and values[4] == status_filter[:12] + "..." if len(status_filter) > 12 else values[4] == status_filter:
                    self.orders_tree.item(item, tags=())
                else:
                    self.orders_tree.item(item, tags=('hidden',))
        
        # Apply tag configuration
        self.orders_tree.tag_configure('hidden', foreground='gray')
    
    def on_order_select(self, event):
        """Handle order selection"""
        selection = self.orders_tree.selection()
        if selection:
            values = self.orders_tree.item(selection[0])['values']
            if values:
                self.selected_invoice_id = values[0]  # Invoice number
                self.display_order_details(values[0])
                # Update selected order info
                self.selected_label.config(text=f"Invoice: {self.selected_invoice_id}")
    
    def display_order_details(self, invoice_no):
        """Display details of selected order"""
        # First check if order exists in tracking data
        order = next((o for o in self.orders if o.get('invoice_no') == invoice_no), None)
        
        if not order:
            # Try to load from database and create tracking entry
            conn, cur = self.get_db_connection()
            if conn:
                try:
                    cur.execute('''
                        SELECT invoice_no, total_amount, customer_name, 
                               customer_contact, invoice_date
                        FROM invoices 
                        WHERE invoice_no = ?
                    ''', (invoice_no,))
                    
                    invoice_data = cur.fetchone()
                    
                    if invoice_data:
                        # Create new tracking order
                        order = {
                            'id': self.current_order_id,
                            'invoice_no': invoice_data[0],
                            'amount': invoice_data[1] or 0,
                            'customer': invoice_data[2] or "Walk-in Customer",
                            'contact': invoice_data[3] or "N/A",
                            'date': invoice_data[4] or self.current_date,
                            'status': 'Order Confirmation',
                            'created_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'last_updated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'history': [{
                                'stage': 'Order Confirmation',
                                'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'updated_by': 'System'
                            }]
                        }
                        
                        self.orders.append(order)
                        self.current_order_id += 1
                        self.save_order_data()
                except Exception as e:
                    print(f"Error loading invoice details: {e}")
        
        if order:
            self.selected_order_id = order['id']
            
            # Normalize status before displaying
            order['status'] = self.normalize_stage(order.get('status', 'Order Confirmation'))
            
            # Update stage selection
            self.select_stage(order['status'])
            
            # Draw progress
            self.draw_progress(order)
            
            # Update history
            self.update_history_display(order)
    
    def select_stage(self, stage):
        """Select a production stage - FIXED: Now all stages are selectable"""
        self.current_selected_stage = stage
        
        # Update button colors based on stage
        for btn in self.stage_buttons:
            # Get the stage for this button from the map
            btn_stage = self.stage_button_map.get(btn, "")
            
            # Check if this button's stage matches the selected stage
            if btn_stage == stage:
                btn.configure(bg=self.success_color, fg='white', relief=SUNKEN)
            else:
                btn.configure(bg='#e0e0e0', fg='#2c3e50', relief=RAISED)
    
    def draw_progress(self, order):
        """Draw progress visualization - UPDATED for 9 stages"""
        self.progress_canvas.delete("all")
        
        width = self.progress_canvas.winfo_width()
        if width < 100:
            width = 500
        
        current_stage_index = self.get_stage_index(order['status'])
        
        # Calculate progress percentage
        progress_percent = int(((current_stage_index + 1) / len(self.stages)) * 100)
        self.progress_percent_label.config(text=f"Progress: {progress_percent}%")
        self.current_stage_label.config(text=f"Current: {order['status']}")
        
        height = 160
        
        # Draw timeline track
        self.progress_canvas.create_rectangle(30, height-35, width-30, height-25, 
                                             fill='#ecf0f1', outline='#bdc3c7', width=1)
        
        # Draw progress fill
        progress_width = ((current_stage_index + 1) / len(self.stages)) * (width - 60)
        self.progress_canvas.create_rectangle(30, height-35, 30 + progress_width, height-25, 
                                             fill='#27ae60', outline='#27ae60', width=0)
        
        # Draw stage markers and labels
        stage_width = (width - 60) / len(self.stages)
        
        for i, stage in enumerate(self.stages):
            x = 30 + i * stage_width + (stage_width / 2)
            
            # Marker
            radius = 10 if i == current_stage_index else 8 if i < current_stage_index else 6
            color = '#27ae60' if i <= current_stage_index else '#95a5a6'
            outline = '#2c3e50' if i == current_stage_index else color
            width_border = 2 if i == current_stage_index else 1
            
            self.progress_canvas.create_oval(x-radius, height-45-radius, x+radius, height-45+radius, 
                                           fill=color, outline=outline, width=width_border)
            
            # Stage number
            self.progress_canvas.create_text(x, height-45, text=str(i+1), 
                                           font=("Arial", 8, "bold"),
                                           fill='white')
            
            # Stage label - shortened
            short_stage = stage
            if stage == "Handwork Embroidery Unit":
                short_stage = "Handwork"
            elif stage == "Final Pressing & Packing":
                short_stage = "Pressing"
            elif stage == "Quality Control":
                short_stage = "QC"
            elif stage == "Stitching Unit":
                short_stage = "Stitch"
            elif stage == "Back to Shop":
                short_stage = "Back"
            elif stage == "Order Confirmation":
                short_stage = "Order"
            elif stage == "Shop Manager":
                short_stage = "Manager"
            elif stage == "Cutting Processes":
                short_stage = "Cutting"
            
            self.progress_canvas.create_text(x, height-60, text=short_stage, 
                                           font=("Arial", 7),
                                           fill='#2c3e50')
        
        # Create stage indicator in the progress tab
        self.create_stage_indicator(order)
    
    def create_stage_indicator(self, order):
        """Create a mini stage indicator"""
        # Clear previous
        for widget in self.stage_indicator_frame.winfo_children():
            widget.destroy()
        
        current_index = self.get_stage_index(order['status'])
        
        # Create mini stage indicators
        for i, stage in enumerate(self.stages):
            if i < 3:  # First 3 stages
                color = self.success_color if i <= current_index else '#e0e0e0'
                text = "●" if i <= current_index else "○"
            elif i < 6:  # Middle 3 stages
                color = self.warning_color if i <= current_index else '#e0e0e0'
                text = "●" if i <= current_index else "○"
            else:  # Last 3 stages
                color = self.info_color if i <= current_index else '#e0e0e0'
                text = "●" if i <= current_index else "○"
            
            lbl = Label(self.stage_indicator_frame, text=text, font=("Arial", 14),
                      fg=color, bg=self.card_bg)
            lbl.pack(side=LEFT, padx=1)
    
    def update_history_display(self, order):
        """Update the history listbox"""
        self.history_listbox.delete(0, END)
        
        history = order.get('history', [])
        if history:
            for entry in reversed(history[-10:]):  # Show last 10 entries
                if isinstance(entry, dict):
                    stage = self.normalize_stage(entry.get('stage', 'N/A'))
                    date_str = entry.get('date', 'N/A')[:16]  # Truncate
                    self.history_listbox.insert(END, f"{date_str} - {stage}")
        else:
            self.history_listbox.insert(END, "No history available")
    
    def update_stage(self):
        """Update the stage of selected order"""
        if not self.selected_order_id or not self.selected_invoice_id:
            messagebox.showwarning("Warning", "Please select an order first!")
            return
        
        # Get current stage from selection
        if not self.current_selected_stage:
            messagebox.showwarning("Warning", "Please select a production stage!")
            return
        
        current_stage = self.current_selected_stage
        
        # Find and update order
        for order in self.orders:
            if order['id'] == self.selected_order_id:
                # Normalize current status
                order['status'] = self.normalize_stage(order.get('status', 'Order Confirmation'))
                
                if order['status'] == current_stage:
                    messagebox.showinfo("Info", "Order is already at this stage!")
                    return
                
                old_status = order['status']
                order['status'] = current_stage
                order['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Add to history
                if 'history' not in order:
                    order['history'] = []
                
                order['history'].append({
                    'stage': current_stage,
                    'date': order['last_updated'],
                    'updated_by': 'User'
                })
                
                # If order is delivered, remove from active orders display
                if current_stage == 'Delivery':
                    messagebox.showinfo("Order Delivered", 
                                      f"Order #{order['invoice_no']} marked as delivered!")
                    
                    # Update treeview to remove delivered order
                    for item in self.orders_tree.get_children():
                        values = self.orders_tree.item(item)['values']
                        if values and values[0] == order['invoice_no']:
                            self.orders_tree.delete(item)
                            break
                    
                    # Clear progress display
                    self.progress_canvas.delete("all")
                    self.history_listbox.delete(0, END)
                    self.selected_order_id = None
                    self.selected_invoice_id = None
                    self.selected_label.config(text="No order selected")
                    self.progress_percent_label.config(text="Progress: 0%")
                    self.current_stage_label.config(text="Current: None")
                    
                    # Reset stage buttons
                    for btn in self.stage_buttons:
                        btn.configure(bg='#e0e0e0', fg='#2c3e50', relief=RAISED)
                    self.current_selected_stage = None
                else:
                    # Update treeview
                    days_in_progress = self.calculate_days_in_progress(order.get('date'))
                    for item in self.orders_tree.get_children():
                        values = self.orders_tree.item(item)['values']
                        if values and values[0] == order['invoice_no']:
                            self.orders_tree.item(item, values=(
                                order['invoice_no'],
                                f"PKR {order['amount']:,.0f}",
                                order['customer'][:12] + "..." if len(order['customer']) > 12 else order['customer'],
                                order['date'],
                                order['status'][:12] + "..." if len(order['status']) > 12 else order['status'],
                                f"{days_in_progress}d"
                            ))
                            break
                    
                    # Refresh display
                    self.display_order_details(order['invoice_no'])
                
                self.save_order_data()
                self.refresh_orders()  # Refresh to update counts
                
                if current_stage != 'Delivery':
                    messagebox.showinfo("Success", f"Order updated to '{current_stage}'!")
                return
        
        messagebox.showerror("Error", "Order not found in tracking system!")
    
    def delete_order(self):
        """Delete selected order from tracking system"""
        if not self.selected_order_id:
            messagebox.showwarning("Warning", "Please select an order to delete!")
            return
        
        confirm = messagebox.askyesno("Confirm Delete", 
                                     "Are you sure you want to delete this order from tracking?")
        
        if confirm:
            # Remove from tracking data
            self.orders = [o for o in self.orders if o['id'] != self.selected_order_id]
            
            # Remove from treeview
            for item in self.orders_tree.get_children():
                values = self.orders_tree.item(item)['values']
                if values and values[0] == self.selected_invoice_id:
                    self.orders_tree.delete(item)
                    break
            
            # Clear progress and selection
            self.progress_canvas.delete("all")
            self.history_listbox.delete(0, END)
            self.selected_order_id = None
            self.selected_invoice_id = None
            self.selected_label.config(text="No order selected")
            self.progress_percent_label.config(text="Progress: 0%")
            self.current_stage_label.config(text="Current: None")
            
            # Reset stage buttons
            for btn in self.stage_buttons:
                btn.configure(bg='#e0e0e0', fg='#2c3e50', relief=RAISED)
            self.current_selected_stage = None
            
            self.save_order_data()
            self.refresh_orders()  # Refresh to update counts
            
            messagebox.showinfo("Deleted", "Order removed from tracking system!")
    
    def view_order_details(self):
        """View detailed order information - FIXED: Larger window with better sizing"""
        if not self.selected_invoice_id:
            messagebox.showinfo("Info", "Please select an order first")
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
            
            # Create detail window - LARGER SIZE
            detail_win = Toplevel(self.root)
            detail_win.title(f"Order Details - Invoice #{self.selected_invoice_id}")
            detail_win.geometry("900x700+200+100")  # Increased size
            detail_win.config(bg=self.card_bg)
            detail_win.resizable(True, True)
            
            # Make window modal
            detail_win.transient(self.root)
            detail_win.grab_set()
            
            # Create main container
            main_container = Frame(detail_win, bg=self.card_bg)
            main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            # Header
            header = Frame(main_container, bg=self.accent_color, height=50)
            header.pack(fill=X, pady=(0, 10))
            header.pack_propagate(False)
            
            Label(header, text=f"INVOICE #{self.selected_invoice_id}", 
                  font=("Segoe UI", 14, "bold"), bg=self.accent_color, fg="white").pack(pady=12)
            
            # Content area with scrollbar
            canvas = Canvas(main_container, bg=self.card_bg, highlightthickness=0)
            scrollbar = Scrollbar(main_container, orient=VERTICAL, command=canvas.yview)
            scrollable_frame = Frame(canvas, bg=self.card_bg)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # Content
            content = Frame(scrollable_frame, bg=self.card_bg)
            content.pack(fill=BOTH, expand=True, padx=10, pady=5)
            
            # Order Details
            details_frame = Frame(content, bg="#f8f9fa", relief="solid", bd=1)
            details_frame.pack(fill=X, pady=(0, 10))
            
            Label(details_frame, text="ORDER INFORMATION", font=("Segoe UI", 12, "bold"),
                  bg=self.accent_color, fg="white").pack(fill=X)
            
            # Create simple grid with better layout
            details_inner = Frame(details_frame, bg="#f8f9fa")
            details_inner.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            # Create two columns for details
            left_details = Frame(details_inner, bg="#f8f9fa")
            left_details.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
            
            right_details = Frame(details_inner, bg="#f8f9fa")
            right_details.pack(side=LEFT, fill=BOTH, expand=True)
            
            details_left = [
                ("Customer:", invoice_data[5] or "Walk-in"),
                ("Contact:", invoice_data[6] or "N/A"),
                ("Date:", invoice_data[7]),
            ]
            
            details_right = [
                ("Time:", invoice_data[8]),
                ("Subtotal:", f"PKR {invoice_data[4]:,.0f}" if invoice_data[4] else "PKR 0"),
                ("Tax:", f"PKR {invoice_data[3]:,.0f}" if invoice_data[3] else "PKR 0"),
            ]
            
            # Add total at the bottom
            total_frame = Frame(details_frame, bg="#f8f9fa")
            total_frame.pack(fill=X, padx=10, pady=(0, 10))
            
            Label(total_frame, text="Total:", font=("Segoe UI", 11, "bold"), 
                  bg="#f8f9fa", fg=self.accent_color).pack(side=LEFT)
            Label(total_frame, text=f"PKR {invoice_data[2]:,.0f}" if invoice_data[2] else "PKR 0", 
                  font=("Segoe UI", 11, "bold"), bg="#f8f9fa", fg=self.success_color).pack(side=LEFT, padx=(10, 0))
            
            # Display left details
            for label, value in details_left:
                row_frame = Frame(left_details, bg="#f8f9fa")
                row_frame.pack(fill=X, pady=5)
                Label(row_frame, text=label, font=("Segoe UI", 10, "bold"), 
                      bg="#f8f9fa", width=10, anchor="w").pack(side=LEFT)
                Label(row_frame, text=value, font=("Segoe UI", 10), 
                      bg="#f8f9fa", anchor="w").pack(side=LEFT, padx=(5, 0))
            
            # Display right details
            for label, value in details_right:
                row_frame = Frame(right_details, bg="#f8f9fa")
                row_frame.pack(fill=X, pady=5)
                Label(row_frame, text=label, font=("Segoe UI", 10, "bold"), 
                      bg="#f8f9fa", width=10, anchor="w").pack(side=LEFT)
                Label(row_frame, text=value, font=("Segoe UI", 10), 
                      bg="#f8f9fa", anchor="w").pack(side=LEFT, padx=(5, 0))
            
            # Items section
            items_frame = Frame(content, bg="#f8f9fa", relief="solid", bd=1)
            items_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
            
            Label(items_frame, text="ITEMS", font=("Segoe UI", 12, "bold"),
                  bg=self.accent_color, fg="white").pack(fill=X)
            
            # Create a frame for items list with better formatting
            items_container = Frame(items_frame, bg="#f8f9fa")
            items_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            # Headers
            headers_frame = Frame(items_container, bg="#e9ecef")
            headers_frame.pack(fill=X, pady=(0, 5))
            
            headers = ["Product", "Qty", "Price", "Total"]
            widths = [400, 50, 100, 100]
            
            for i, (header, width) in enumerate(zip(headers, widths)):
                Label(headers_frame, text=header, font=("Segoe UI", 10, "bold"),
                      bg="#e9ecef", width=width//10, anchor="w").pack(side=LEFT, padx=2)
            
            # Items with alternating colors
            for idx, item in enumerate(items_data):
                item_frame = Frame(items_container, bg="#f8f9fa" if idx % 2 == 0 else "#ffffff")
                item_frame.pack(fill=X, pady=1)
                
                # Product name
                product_name = item[0]
                if len(product_name) > 40:
                    product_name = product_name[:40] + "..."
                
                Label(item_frame, text=product_name, font=("Segoe UI", 9),
                      bg=item_frame.cget('bg'), width=40, anchor="w").pack(side=LEFT, padx=2)
                Label(item_frame, text=str(item[1]), font=("Segoe UI", 9),
                      bg=item_frame.cget('bg'), width=5, anchor="w").pack(side=LEFT)
                Label(item_frame, text=f"PKR {item[2]:,.0f}", font=("Segoe UI", 9),
                      bg=item_frame.cget('bg'), width=10, anchor="w").pack(side=LEFT)
                Label(item_frame, text=f"PKR {item[3]:,.0f}", font=("Segoe UI", 9, "bold"),
                      bg=item_frame.cget('bg'), width=10, anchor="w").pack(side=LEFT)
            
            # Close button
            button_frame = Frame(content, bg=self.card_bg)
            button_frame.pack(fill=X, pady=10)
            
            Button(button_frame, text="Close", command=detail_win.destroy,
                   font=("Segoe UI", 10), bg=self.accent_color, fg="white",
                   cursor="hand2", relief="flat", padx=30, pady=5).pack()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load order details: {str(e)}")
            traceback.print_exc()
    
    def print_invoice(self):
        """Print selected invoice as PDF"""
        if not self.selected_invoice_id:
            messagebox.showinfo("Info", "Please select an order first")
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
                filetypes=[("PDF files", "*.pdf")],
                title="Save Invoice as PDF",
                initialfile=f"Invoice_{self.selected_invoice_id}.pdf"
            )
            
            if not file_path:
                return
            
            # Create PDF document with footer on every page
            doc = SimpleDocTemplate(file_path, pagesize=letter,
                                   leftMargin=0.5*inch,
                                   rightMargin=0.5*inch,
                                   topMargin=0.5*inch,
                                   bottomMargin=0.75*inch)  # Extra space for footer
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=16,
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
            
            elements.append(Spacer(1, 10))
            
            # Items table
            table_data = [['Product', 'Qty', 'Price (PKR)', 'Total (PKR)']]
            
            for item in items:
                table_data.append([
                    item[0][:30] + "..." if len(item[0]) > 30 else item[0],
                    str(item[1]),
                    f"{item[2]:,.0f}",
                    f"{item[3]:,.0f}"
                ])
            
            # Add totals
            subtotal = invoice[4] or 0
            tax = invoice[3] or 0
            total = invoice[2] or 0
            
            table_data.append(['', '', 'Subtotal:', f"PKR {subtotal:,.0f}"])
            table_data.append(['', '', 'Tax:', f"PKR {tax:,.0f}"])
            table_data.append(['', '', 'Total:', f"PKR {total:,.0f}"])
            
            items_table = Table(table_data, colWidths=[250, 50, 100, 100])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.accent_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -3), 0.5, colors.HexColor('#dddddd')),
                ('FONTNAME', (-2, -3), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (-2, -3), (-1, -1), colors.HexColor('#f8f9fa')),
                ('ALIGN', (-2, -3), (-1, -1), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(items_table)
            
            # Add spacer before footer
            elements.append(Spacer(1, 20))
            
            # Build PDF with footer on every page
            doc.build(elements, onFirstPage=FooterCanvas.add_footer, onLaterPages=FooterCanvas.add_footer)
            
            self.status_label.config(text=f"Invoice #{self.selected_invoice_id} saved")
            messagebox.showinfo("Success", f"Invoice saved as PDF")
            
            # Open the PDF
            os.startfile(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print invoice: {str(e)}")
            traceback.print_exc()
    
    def load_from_sales(self):
        """Load recent invoices from sales database"""
        self.refresh_orders()
        messagebox.showinfo("Success", "Orders loaded from sales database!")
    
    # =========== PDF GENERATION METHODS ===========
    
    def generate_single_pdf(self):
        """Generate PDF report for selected order"""
        if not self.selected_order_id or not self.selected_invoice_id:
            messagebox.showwarning("Warning", "Please select an order first!")
            return
        
        # Find the order
        order = next((o for o in self.orders if o['id'] == self.selected_order_id), None)
        if not order:
            messagebox.showerror("Error", "Order not found in tracking system!")
            return
        
        # Normalize status
        order['status'] = self.normalize_stage(order.get('status', 'Order Confirmation'))
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Order_{order['invoice_no']}_Report.pdf"
        )
        
        if not file_path:
            return
        
        try:
            # Create PDF document with footer on every page
            doc = SimpleDocTemplate(file_path, pagesize=letter,
                                  leftMargin=0.5*inch,
                                  rightMargin=0.5*inch,
                                  topMargin=0.5*inch,
                                  bottomMargin=0.75*inch)  # Extra space for footer
            elements = []
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Header
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#2c3e50'),
                alignment=1,
                spaceAfter=10
            )
            
            elements.append(Paragraph("ORDER TRACKING REPORT", title_style))
            elements.append(Paragraph(f"Invoice: {order['invoice_no']}", styles['Normal']))
            elements.append(Spacer(1, 10))
            
            # Order Details
            elements.append(Paragraph("Order Details", styles['Heading2']))
            
            details_data = [
                ["Order ID:", f"#{order['id']}"],
                ["Customer:", order['customer']],
                ["Amount:", f"PKR {order['amount']:,.0f}"],
                ["Status:", order['status']],
                ["Order Date:", order['date']],
                ["Last Updated:", order.get('last_updated', 'N/A')[:16]]
            ]
            
            table = Table(details_data, colWidths=[100, 350])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 15))
            
            # Production Stages
            elements.append(Paragraph("Production Stages", styles['Heading2']))
            
            stages_data = [["Stage", "Status"]]
            current_index = self.get_stage_index(order['status'])
            
            for i, stage in enumerate(self.stages):
                if current_index > i:
                    status = "✓ COMPLETED"
                elif current_index == i:
                    status = "✓ CURRENT"
                else:
                    status = "○ PENDING"
                stages_data.append([stage, status])
            
            stages_table = Table(stages_data, colWidths=[300, 100])
            stages_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(stages_table)
            
            # Add spacer before footer
            elements.append(Spacer(1, 20))
            
            # Build PDF with footer on every page
            doc.build(elements, onFirstPage=FooterCanvas.add_footer, onLaterPages=FooterCanvas.add_footer)
            
            messagebox.showinfo("Success", f"PDF report generated!")
            webbrowser.open(file_path)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")
            traceback.print_exc()
    
    def generate_all_pdfs(self):
        """Generate PDF report for all tracked orders"""
        if not self.orders:
            messagebox.showwarning("Warning", "No tracked orders found!")
            return
    
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"All_Tracked_Orders.pdf"
        )
    
        if not file_path:
            return
    
        try:
            # Create PDF document with footer on every page
            doc = SimpleDocTemplate(file_path, pagesize=landscape(letter),
                                  leftMargin=0.5*inch,
                                  rightMargin=0.5*inch,
                                  topMargin=0.5*inch,
                                  bottomMargin=0.75*inch)  # Extra space for footer
            elements = []
        
            # Get styles
            styles = getSampleStyleSheet()
        
        # Title
            elements.append(Paragraph("ALL TRACKED ORDERS", styles['Heading1']))
            elements.append(Paragraph(f"Report Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                                styles['Normal']))
            elements.append(Spacer(1, 10))
        
        # Summary
            total_orders = len(self.orders)
            delivered_count = sum(1 for o in self.orders if o.get('status') == 'Delivery')
            active_count = total_orders - delivered_count
        
            summary = f"Total Orders: {total_orders} | Active: {active_count} | Delivered: {delivered_count}"
            elements.append(Paragraph(summary, styles['Normal']))
            elements.append(Spacer(1, 10))
        
        # Create table with adjusted column widths for long invoice numbers
            table_data = [["ID", "Invoice No.", "Customer", "Amount (PKR)", "Status", "Date"]]
        
        # Sort orders by ID
            for order in sorted(self.orders, key=lambda x: x['id']):
            # Normalize status
                status = self.normalize_stage(order.get('status', 'Order Confirmation'))
            
            # Highlight delivered orders
                status_display = status
                if status == 'Delivery':
                    status_display = "✓ DELIVERED"
            
            # Truncate invoice number if too long
                invoice_no = order['invoice_no']
                if len(invoice_no) > 30:
                    invoice_no = invoice_no[:30] + "..."
            
            # Truncate customer name if too long
                customer_name = order['customer']
                if len(customer_name) > 25:
                    customer_name = customer_name[:25] + "..."
            
                table_data.append([
                    str(order['id']),
                    invoice_no,
                    customer_name,
                    f"{order['amount']:,.0f}",
                    status_display,
                    order['date']
                ])
        
            # Create table with adjusted column widths
            table = Table(table_data, colWidths=[30, 140, 100, 85, 100, 75])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Left align invoice numbers
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),  # Left align customer names
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('FONTSIZE', (0, 0), (-1, 0), 10),  # Header font slightly larger
                ('PADDING', (0, 0), (-1, -1), 5),
                ('WORDWRAP', (1, 1), (2, -1), True),  # Enable word wrap for invoice and customer columns
            ]))
        
            elements.append(table)
        
        # Add spacer before footer
            elements.append(Spacer(1, 20))
        
        # Build PDF with footer on every page
            doc.build(elements, onFirstPage=FooterCanvas.add_footer, onLaterPages=FooterCanvas.add_footer)
        
            messagebox.showinfo("Success", f"Complete order report generated!")
            webbrowser.open(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")
        traceback.print_exc()
    # =========== TIME UPDATE METHODS ===========
    
    def update_date_time(self):
        """Update live date and time in header"""
        try:
            if self.is_closing or not self.root.winfo_exists():
                return
            
            if hasattr(self, 'date_time_label') and self.date_time_label.winfo_exists():
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.date_time_label.config(text=current_time)
            
            if not self.is_closing:
                self.safe_after(1000, self.update_date_time)
                
        except Exception as e:
            print(f"Error in update_date_time: {e}")
            if not self.is_closing:
                self.safe_after(1000, self.update_date_time)
    
    def update_time(self):
        """Update time display in footer"""
        try:
            if self.is_closing or not self.root.winfo_exists():
                return
            
            if hasattr(self, 'time_label') and self.time_label.winfo_exists():
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                self.time_label.config(text=f"Updated: {current_time}")
            
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
        app = TrackerClass(root)
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