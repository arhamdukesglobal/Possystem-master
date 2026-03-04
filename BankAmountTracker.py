import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

class BankAmountTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Bank Amount Tracking System")
        self.root.geometry("1200x550+150+50")
        self.root.config(bg="#F5F7FA")
        
        # Define new color scheme
        self.top_bar_color = "#F1C40F"        # Yellow/gold for top bar
        self.purchase_color = "#E67E22"        # Orange for purchases
        self.sales_color = "#E74C3C"            # Red for sales
        
        # ========== TOP BAR WITH DATE/TIME ==========
        top_bar = tk.Frame(self.root, bg=self.top_bar_color, height=35)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        # Title
        title = tk.Label(top_bar, text="Bank Amount Tracking System", 
                        font=("bahnschrift light semicondensed", 16, "bold"), 
                        bg=self.top_bar_color, fg="#000000")
        title.pack(side=tk.LEFT, padx=15)
        
        # Real-time Date and Time
        self.date_time_var = tk.StringVar()
        date_time_label = tk.Label(top_bar, textvariable=self.date_time_var,
                                  font=("Aptos Display", 9), 
                                  bg=self.top_bar_color, fg="#000000")
        date_time_label.pack(side=tk.RIGHT, padx=15)
        
        # Update date/time initially and set up periodic updates
        self.update_datetime()
        
        # ========== SEARCH FRAME ==========
        search_frame = tk.Frame(self.root, bg="#F5F7FA")
        search_frame.pack(fill=tk.X, padx=10, pady=(8, 3))
        
        # Search for Purchases
        tk.Label(search_frame, text="Search Purchase:", font=("Aptos Display", 8, "bold"),
                bg="#F5F7FA", fg="#1F2937").grid(row=0, column=0, sticky="w", padx=(0, 3))
        
        self.purchase_search_var = tk.StringVar()
        purchase_search_entry = tk.Entry(search_frame, textvariable=self.purchase_search_var,
                                        font=("Aptos Display", 8), width=18,
                                        highlightthickness=1, highlightbackground="#D1D5DB")
        purchase_search_entry.grid(row=0, column=1, padx=3, pady=1)
        purchase_search_entry.bind('<KeyRelease>', lambda e: self.search_purchases())
        
        # Search for Sales
        tk.Label(search_frame, text="Search Sales:", font=("Aptos Display", 8, "bold"),
                bg="#F5F7FA", fg="#1F2937").grid(row=0, column=2, sticky="w", padx=(10, 3))
        
        self.sales_search_var = tk.StringVar()
        sales_search_entry = tk.Entry(search_frame, textvariable=self.sales_search_var,
                                     font=("Aptos Display", 8), width=18,
                                     highlightthickness=1, highlightbackground="#D1D5DB")
        sales_search_entry.grid(row=0, column=3, padx=3, pady=1)
        sales_search_entry.bind('<KeyRelease>', lambda e: self.search_sales())
        
        # Clear buttons
        tk.Button(search_frame, text="Clear Purchase", command=self.clear_purchase_search,
                 font=("Aptos Display", 7), bg="#6B7280", fg="white",
                 cursor="hand2", padx=4).grid(row=0, column=4, padx=1)
        
        tk.Button(search_frame, text="Clear Sales", command=self.clear_sales_search,
                 font=("Aptos Display", 7), bg="#6B7280", fg="white",
                 cursor="hand2", padx=4).grid(row=0, column=5, padx=1)
        
        # ========== MAIN CONTAINER ==========
        main_container = tk.Frame(self.root, bg="#F5F7FA")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=3)
        
        # Configure grid for two equal columns
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(0, weight=1)
        
        # ========== LEFT SIDE: PURCHASE AMOUNT TRACKER ==========
        purchase_frame = tk.LabelFrame(main_container, text="Purchase Amount Tracker (Outgoing Payments)", 
                                      font=("bahnschrift light semicondensed", 10, "bold"),
                                      bg="white", fg=self.purchase_color,  # set label frame text color
                                      bd=2, relief=tk.RIDGE)
        purchase_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        purchase_frame.columnconfigure(0, weight=1)
        purchase_frame.rowconfigure(0, weight=1)
        
        # Purchase Treeview Frame
        purchase_tree_frame = tk.Frame(purchase_frame, bg="white")
        purchase_tree_frame.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        purchase_tree_frame.columnconfigure(0, weight=1)
        purchase_tree_frame.rowconfigure(0, weight=1)
        
        # Scrollbars for purchases
        purchase_scroll_y = tk.Scrollbar(purchase_tree_frame, orient=tk.VERTICAL)
        purchase_scroll_x = tk.Scrollbar(purchase_tree_frame, orient=tk.HORIZONTAL)
        
        # Create custom style for purchase treeview heading
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Purchase.Treeview.Heading", 
                       background=self.purchase_color, 
                       foreground="white", 
                       fieldbackground=self.purchase_color,
                       font=("Aptos Display", 8, "bold"))
        style.map("Purchase.Treeview.Heading", 
                 background=[("active", self.purchase_color)])
        
        # Configure selection colors for purchase treeview
        style.map("Purchase.Treeview",
                 background=[("selected", "yellow")],
                 foreground=[("selected", "black")])
        
        # Purchase Treeview with added Advance and Remaining columns
        self.purchase_tree = ttk.Treeview(purchase_tree_frame, 
                                         columns=("billno", "billdate", "supplier", "contact", 
                                                 "total_amount", "advance", "remaining", "payment_status"),
                                         yscrollcommand=purchase_scroll_y.set,
                                         xscrollcommand=purchase_scroll_x.set,
                                         height=10,
                                         show="headings",
                                         style="Purchase.Treeview")
        
        purchase_scroll_y.config(command=self.purchase_tree.yview)
        purchase_scroll_x.config(command=self.purchase_tree.xview)
        
        # Define headings for purchases with sort functionality
        columns_purchase = [
            ("billno", "Bill No", 70, "center"),
            ("billdate", "Bill Date", 75, "center"),
            ("supplier", "Supplier", 110, "w"),
            ("contact", "Contact", 80, "center"),
            ("total_amount", "Total Amount", 85, "e"),
            ("advance", "Advance", 75, "e"),
            ("remaining", "Remaining", 75, "e"),
            ("payment_status", "Status", 75, "center")
        ]
        
        for col_id, heading, width, anchor in columns_purchase:
            self.purchase_tree.heading(col_id, text=heading, 
                                      command=lambda c=col_id: self.sort_treeview(self.purchase_tree, c, False))
            self.purchase_tree.column(col_id, width=width, anchor=anchor)
        
        # Configure tag colors for payment status
        self.purchase_tree.tag_configure('Paid', background='#DCFCE7')  # Green
        self.purchase_tree.tag_configure('Pending', background='#FEF3C7')  # Yellow
        self.purchase_tree.tag_configure('Overdue', background='#FEE2E2')  # Red
        
        self.purchase_tree.grid(row=0, column=0, sticky="nsew")
        purchase_scroll_y.grid(row=0, column=1, sticky="ns")
        purchase_scroll_x.grid(row=1, column=0, sticky="ew")
        
        # PDF Button for Purchases (with purchase color)
        purchase_pdf_frame = tk.Frame(purchase_frame, bg="white", height=30)
        purchase_pdf_frame.grid(row=1, column=0, sticky="ew", padx=3, pady=(0, 3))
        purchase_pdf_frame.pack_propagate(False)
        
        tk.Button(purchase_pdf_frame, text="Download PDF", command=self.generate_purchase_pdf,
                 font=("Aptos Display", 8, "bold"), bg=self.purchase_color, fg="white",
                 cursor="hand2", padx=10, pady=2).pack(side=tk.RIGHT, padx=5)
        
        # Purchase Summary (text color purchase color)
        self.purchase_summary_var = tk.StringVar(value="Total: Rs.0.00 | Advance: Rs.0.00 | Pending: Rs.0.00 | Overdue: Rs.0.00")
        tk.Label(purchase_pdf_frame, textvariable=self.purchase_summary_var,
                font=("Aptos Display", 8, "bold"), bg="white", fg=self.purchase_color).pack(side=tk.LEFT, padx=5)
        
        # ========== RIGHT SIDE: SALES AMOUNT TRACKER ==========
        sales_frame = tk.LabelFrame(main_container, text="Sales Amount Tracker (Incoming Payments)", 
                                   font=("bahnschrift light semicondensed", 10, "bold"),
                                   bg="white", fg=self.sales_color,  # set label frame text color
                                   bd=2, relief=tk.RIDGE)
        sales_frame.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
        sales_frame.columnconfigure(0, weight=1)
        sales_frame.rowconfigure(0, weight=1)
        
        # Sales Treeview Frame
        sales_tree_frame = tk.Frame(sales_frame, bg="white")
        sales_tree_frame.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        sales_tree_frame.columnconfigure(0, weight=1)
        sales_tree_frame.rowconfigure(0, weight=1)
        
        # Scrollbars for sales
        sales_scroll_y = tk.Scrollbar(sales_tree_frame, orient=tk.VERTICAL)
        sales_scroll_x = tk.Scrollbar(sales_tree_frame, orient=tk.HORIZONTAL)
        
        # Create custom style for sales treeview heading
        style.configure("Sales.Treeview.Heading", 
                       background=self.sales_color, 
                       foreground="white", 
                       fieldbackground=self.sales_color,
                       font=("Aptos Display", 8, "bold"))
        style.map("Sales.Treeview.Heading", 
                 background=[("active", self.sales_color)])
        
        # Configure selection colors for sales treeview
        style.map("Sales.Treeview",
                 background=[("selected", "yellow")],
                 foreground=[("selected", "black")])
        
        # Sales Treeview with BankRec column
        self.sales_tree = ttk.Treeview(sales_tree_frame,
                                      columns=("invoice_no", "date", "customer_name", "customer_contact",
                                              "total_amount", "advance", "bankrec", "remaining", "status", "type"),
                                      yscrollcommand=sales_scroll_y.set,
                                      xscrollcommand=sales_scroll_x.set,
                                      height=10,
                                      show="headings",
                                      style="Sales.Treeview")
        
        sales_scroll_y.config(command=self.sales_tree.yview)
        sales_scroll_x.config(command=self.sales_tree.xview)
        
        # Define headings for sales with sort functionality
        columns_sales = [
            ("invoice_no", "Invoice No", 85, "center"),
            ("date", "Date", 75, "center"),
            ("customer_name", "Customer Name", 110, "w"),
            ("customer_contact", "Contact", 85, "center"),
            ("total_amount", "Total Amount", 85, "e"),
            ("advance", "Advance", 75, "e"),
            ("bankrec", "Bank Rec", 75, "e"),
            ("remaining", "Remaining", 75, "e"),
            ("status", "Status", 65, "center"),
            ("type", "Type", 60, "center")
        ]
        
        for col_id, heading, width, anchor in columns_sales:
            self.sales_tree.heading(col_id, text=heading, 
                                   command=lambda c=col_id: self.sort_treeview(self.sales_tree, c, False))
            self.sales_tree.column(col_id, width=width, anchor=anchor)
        
        # Configure tag colors for payment status
        self.sales_tree.tag_configure('Paid', background='#DCFCE7')  # Green
        self.sales_tree.tag_configure('Pending', background='#FEF3C7')  # Yellow
        self.sales_tree.tag_configure('Overdue', background='#FEE2E2')  # Red
        
        self.sales_tree.grid(row=0, column=0, sticky="nsew")
        sales_scroll_y.grid(row=0, column=1, sticky="ns")
        sales_scroll_x.grid(row=1, column=0, sticky="ew")
        
        # PDF Button for Sales (with sales color)
        sales_pdf_frame = tk.Frame(sales_frame, bg="white", height=30)
        sales_pdf_frame.grid(row=1, column=0, sticky="ew", padx=3, pady=(0, 3))
        sales_pdf_frame.pack_propagate(False)
        
        tk.Button(sales_pdf_frame, text="Download PDF", command=self.generate_sales_pdf,
                 font=("Aptos Display", 8, "bold"), bg=self.sales_color, fg="white",
                 cursor="hand2", padx=10, pady=2).pack(side=tk.RIGHT, padx=5)
        
        # Sales Summary (text color sales color)
        self.sales_summary_var = tk.StringVar(value="Total: Rs.0.00 | Received: Rs.0.00 | Pending: Rs.0.00 | Overdue: Rs.0.00")
        tk.Label(sales_pdf_frame, textvariable=self.sales_summary_var,
                font=("Aptos Display", 8, "bold"), bg="white", fg=self.sales_color).pack(side=tk.LEFT, padx=5)
        
        # ========== BOTTOM BUTTONS FRAME ==========
        button_frame = tk.Frame(self.root, bg="#F5F7FA")
        button_frame.pack(fill=tk.X, padx=10, pady=(3, 8))
        
        # Button configuration
        btn_config = {
            "font": ("Aptos Display", 8, "bold"),
            "cursor": "hand2",
            "width": 11,
            "padx": 4,
            "pady": 2
        }
        
        tk.Button(button_frame, text="Refresh All", command=self.load_all_data,
                 bg="#3B82F6", fg="white", **btn_config).pack(side=tk.LEFT, padx=1)
        
        tk.Button(button_frame, text="Paid", command=self.show_paid_only,
                 bg="#10B981", fg="white", **btn_config).pack(side=tk.LEFT, padx=1)
        
        tk.Button(button_frame, text="Pending", command=self.show_pending_only,
                 bg="#F59E0B", fg="white", **btn_config).pack(side=tk.LEFT, padx=1)
        
        tk.Button(button_frame, text="Overdue", command=self.show_overdue_only,
                 bg="#EF4444", fg="white", **btn_config).pack(side=tk.LEFT, padx=1)
        
        tk.Button(button_frame, text="Show All", command=self.show_all,
                 bg="#6B7280", fg="white", **btn_config).pack(side=tk.LEFT, padx=1)
        
        # Store sort states
        self.sort_states = {
            'purchase': {},
            'sales': {}
        }
        
        # Load initial data
        self.load_purchases()
        self.load_sales()
    
    def update_datetime(self):
        """Update the date and time display"""
        now = datetime.now()
        self.date_time_var.set(now.strftime("%d-%m-%Y %I:%M:%S %p"))
        self.root.after(1000, self.update_datetime)
    
    def sort_treeview(self, tree, col, reverse):
        """Sort treeview column when clicked"""
        items = [(tree.set(item, col), item) for item in tree.get_children('')]
        try:
            items.sort(key=lambda x: float(x[0].replace('Rs.', '').replace(',', '').strip()), reverse=reverse)
        except:
            items.sort(key=lambda x: x[0], reverse=reverse)
        for index, (val, item) in enumerate(items):
            tree.move(item, '', index)
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))
    
    def load_purchases(self):
        """Load purchase data from Purchases table with advance and remaining amounts"""
        try:
            for item in self.purchase_tree.get_children():
                self.purchase_tree.delete(item)
            
            con = sqlite3.connect('Possystem.db')
            cur = con.cursor()
            
            cur.execute("PRAGMA table_info(Purchases)")
            columns = [col[1] for col in cur.fetchall()]
            
            has_given_amount = 'GivenAmount' in columns
            
            if 'Advance' in columns and has_given_amount:
                cur.execute('''
                    SELECT 
                        BillNo,
                        BillDate,
                        Supplier,
                        Contact,
                        TotalAmount,
                        COALESCE(Advance, 0) as Advance,
                        (TotalAmount - COALESCE(GivenAmount, 0)) as Remaining,
                        PaymentStatus
                    FROM Purchases 
                    ORDER BY BillDate DESC
                ''')
            elif has_given_amount:
                cur.execute('''
                    SELECT 
                        BillNo,
                        BillDate,
                        Supplier,
                        Contact,
                        TotalAmount,
                        COALESCE(GivenAmount, 0) as Advance,
                        (TotalAmount - COALESCE(GivenAmount, 0)) as Remaining,
                        PaymentStatus
                    FROM Purchases 
                    ORDER BY BillDate DESC
                ''')
            elif 'Advance' in columns:
                cur.execute('''
                    SELECT 
                        BillNo,
                        BillDate,
                        Supplier,
                        Contact,
                        TotalAmount,
                        COALESCE(Advance, 0) as Advance,
                        TotalAmount as Remaining,
                        PaymentStatus
                    FROM Purchases 
                    ORDER BY BillDate DESC
                ''')
            else:
                cur.execute('''
                    SELECT 
                        BillNo,
                        BillDate,
                        Supplier,
                        Contact,
                        TotalAmount,
                        0 as Advance,
                        TotalAmount as Remaining,
                        PaymentStatus
                    FROM Purchases 
                    ORDER BY BillDate DESC
                ''')
            
            rows = cur.fetchall()
            total_amount = 0
            total_advance = 0
            total_pending = 0
            total_overdue = 0
            
            for row in rows:
                billno, billdate, supplier, contact, total, advance, remaining, status = row
                total_amount += total
                total_advance += advance
                
                if status == 'Overdue':
                    total_overdue += remaining
                elif status == 'Pending' or (advance > 0 and remaining > 0):
                    total_pending += remaining
                elif status == 'Paid':
                    remaining = 0
                
                formatted_total = f"Rs.{total:,.2f}"
                formatted_advance = f"Rs.{advance:,.2f}"
                formatted_remaining = f"Rs.{remaining:,.2f}"
                
                if status == 'Paid':
                    tag = 'Paid'
                elif status == 'Overdue':
                    tag = 'Overdue'
                else:
                    tag = 'Pending'
                
                display_status = 'Pending' if (advance > 0 and remaining > 0) else status
                
                self.purchase_tree.insert('', 'end', values=(
                    billno, billdate, supplier, contact, 
                    formatted_total, formatted_advance, formatted_remaining, display_status
                ), tags=(tag,))
            
            self.purchase_summary_var.set(
                f"Total: Rs.{total_amount:,.2f} | "
                f"Advance: Rs.{total_advance:,.2f} | "
                f"Pending: Rs.{total_pending:,.2f} | "
                f"Overdue: Rs.{total_overdue:,.2f}"
            )
            
            con.close()
            
        except Exception as ex:
            print(f"Error loading purchases: {str(ex)}")
            # If there's an issue loading (like a missing table), gracefully ignore for UI consistency
            pass
    
    def load_sales(self):
        """Load sales data from invoices and B2B_Sales tables with BankRec column"""
        try:
            for item in self.sales_tree.get_children():
                self.sales_tree.delete(item)
            
            con = sqlite3.connect('Possystem.db')
            cur = con.cursor()
            
            total_amount = 0
            total_received = 0
            total_bankrec = 0
            total_pending = 0
            total_overdue = 0
            
            # Load INVOICES (B2C)
            cur.execute("PRAGMA table_info(invoices)")
            columns = [col[1] for col in cur.fetchall()]
            
            has_due_date = 'due_date' in columns
            advance_columns = ['advance_payment', 'advance_amount', 'advance', 'advance_paid', 'GivenAmount']
            found_advance_col = None
            for col in advance_columns:
                if col in columns:
                    found_advance_col = col
                    break
            
            if found_advance_col and has_due_date:
                query = f'''
                    SELECT 
                        invoice_no,
                        invoice_date,
                        customer_name,
                        customer_contact,
                        total_amount,
                        COALESCE({found_advance_col}, 0) as advance,
                        due_date
                    FROM invoices 
                    ORDER BY invoice_date DESC
                '''
            elif found_advance_col:
                query = f'''
                    SELECT 
                        invoice_no,
                        invoice_date,
                        customer_name,
                        customer_contact,
                        total_amount,
                        COALESCE({found_advance_col}, 0) as advance,
                        NULL as due_date
                    FROM invoices 
                    ORDER BY invoice_date DESC
                '''
            elif has_due_date:
                query = '''
                    SELECT 
                        invoice_no,
                        invoice_date,
                        customer_name,
                        customer_contact,
                        total_amount,
                        0 as advance,
                        due_date
                    FROM invoices 
                    ORDER BY invoice_date DESC
                '''
            else:
                query = '''
                    SELECT 
                        invoice_no,
                        invoice_date,
                        customer_name,
                        customer_contact,
                        total_amount,
                        0 as advance,
                        NULL as due_date
                    FROM invoices 
                    ORDER BY invoice_date DESC
                '''
            
            cur.execute(query)
            invoice_rows = cur.fetchall()
            
            for row in invoice_rows:
                invoice_no, date, customer_name, contact, total, advance, due_date = row
                total_amount += total
                total_received += advance
                
                remaining = total - advance
                status = "Paid"
                bankrec = 0
                
                if status == 'Paid':
                    total_received += remaining
                    remaining = 0
                
                formatted_total = f"Rs.{total:,.2f}"
                formatted_advance = f"Rs.{advance:,.2f}"
                formatted_bankrec = f"Rs.{bankrec:,.2f}"
                formatted_remaining = f"Rs.{remaining:,.2f}"
                
                tag = 'Paid'
                self.sales_tree.insert('', 'end', values=(
                    invoice_no, date, customer_name, contact,
                    formatted_total, formatted_advance, formatted_bankrec, formatted_remaining, status, "B2C"
                ), tags=(tag,))
            
            # Load B2B_Sales
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='B2B_Sales'")
            if cur.fetchone():
                cur.execute("PRAGMA table_info(B2B_Sales)")
                b2b_columns = [col[1] for col in cur.fetchall()]
                
                has_final_amount = 'FinalAmount' in b2b_columns
                has_advance_col = 'Advance' in b2b_columns
                has_bankrec_col = 'BankRec' in b2b_columns
                
                if has_final_amount and has_advance_col and has_bankrec_col:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            FinalAmount,
                            COALESCE(Advance, 0) as advance,
                            COALESCE(BankRec, 0) as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        ORDER BY InvoiceDate DESC
                    '''
                elif has_final_amount and has_advance_col:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            FinalAmount,
                            COALESCE(Advance, 0) as advance,
                            0 as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        ORDER BY InvoiceDate DESC
                    '''
                elif has_final_amount:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            FinalAmount,
                            0 as advance,
                            0 as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        ORDER BY InvoiceDate DESC
                    '''
                elif has_advance_col and has_bankrec_col:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            TotalAmount,
                            COALESCE(Advance, 0) as advance,
                            COALESCE(BankRec, 0) as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        ORDER BY InvoiceDate DESC
                    '''
                elif has_advance_col:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            TotalAmount,
                            COALESCE(Advance, 0) as advance,
                            0 as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        ORDER BY InvoiceDate DESC
                    '''
                else:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            TotalAmount,
                            0 as advance,
                            0 as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        ORDER BY InvoiceDate DESC
                    '''
                
                cur.execute(b2b_query)
                b2b_rows = cur.fetchall()
                
                for row in b2b_rows:
                    if len(row) >= 8:
                        invoice_no, date, customer_name, contact, total, advance, bankrec, status = row[:8]
                        total_amount += total
                        total_received += advance
                        total_bankrec += bankrec
                        
                        remaining = total - advance
                        
                        if status == 'Paid':
                            total_received = total_received - advance + total
                            remaining = 0
                        elif status == 'Overdue':
                            total_overdue += remaining
                            total_pending += remaining
                        elif status == 'Pending':
                            total_pending += remaining
                        
                        formatted_total = f"Rs.{total:,.2f}"
                        formatted_advance = f"Rs.{advance:,.2f}"
                        formatted_bankrec = f"Rs.{bankrec:,.2f}"
                        formatted_remaining = f"Rs.{remaining:,.2f}"
                        
                        if status == 'Paid':
                            tag = 'Paid'
                        elif status == 'Overdue':
                            tag = 'Overdue'
                        else:
                            tag = 'Pending'
                        
                        self.sales_tree.insert('', 'end', values=(
                            invoice_no, date, customer_name, contact,
                            formatted_total, formatted_advance, formatted_bankrec, formatted_remaining, status, "B2B"
                        ), tags=(tag,))
            
            self.sales_summary_var.set(
                f"Total: Rs.{total_amount:,.2f} | "
                f"Received: Rs.{total_received:,.2f} | "
                f"Bank Rec: Rs.{total_bankrec:,.2f} | "
                f"Pending: Rs.{total_pending:,.2f} | "
                f"Overdue: Rs.{total_overdue:,.2f}"
            )
            
            con.close()
            
        except Exception as ex:
            print(f"Error loading sales: {str(ex)}")
            pass
    
    def search_purchases(self):
        search_text = self.purchase_search_var.get().strip().lower()
        if not search_text:
            self.load_purchases()
            return
        try:
            for item in self.purchase_tree.get_children():
                self.purchase_tree.delete(item)
            
            con = sqlite3.connect('Possystem.db')
            cur = con.cursor()
            
            cur.execute("PRAGMA table_info(Purchases)")
            columns = [col[1] for col in cur.fetchall()]
            has_given_amount = 'GivenAmount' in columns
            
            if 'Advance' in columns and has_given_amount:
                query = '''
                    SELECT 
                        BillNo,
                        BillDate,
                        Supplier,
                        Contact,
                        TotalAmount,
                        COALESCE(Advance, 0) as Advance,
                        (TotalAmount - COALESCE(GivenAmount, 0)) as Remaining,
                        PaymentStatus
                    FROM Purchases 
                    WHERE LOWER(BillNo) LIKE ? OR 
                          LOWER(Supplier) LIKE ? OR 
                          LOWER(Contact) LIKE ? OR
                          LOWER(PaymentStatus) LIKE ?
                    ORDER BY BillDate DESC
                '''
            elif has_given_amount:
                query = '''
                    SELECT 
                        BillNo,
                        BillDate,
                        Supplier,
                        Contact,
                        TotalAmount,
                        COALESCE(GivenAmount, 0) as Advance,
                        (TotalAmount - COALESCE(GivenAmount, 0)) as Remaining,
                        PaymentStatus
                    FROM Purchases 
                    WHERE LOWER(BillNo) LIKE ? OR 
                          LOWER(Supplier) LIKE ? OR 
                          LOWER(Contact) LIKE ? OR
                          LOWER(PaymentStatus) LIKE ?
                    ORDER BY BillDate DESC
                '''
            elif 'Advance' in columns:
                query = '''
                    SELECT 
                        BillNo,
                        BillDate,
                        Supplier,
                        Contact,
                        TotalAmount,
                        COALESCE(Advance, 0) as Advance,
                        TotalAmount as Remaining,
                        PaymentStatus
                    FROM Purchases 
                    WHERE LOWER(BillNo) LIKE ? OR 
                          LOWER(Supplier) LIKE ? OR 
                          LOWER(Contact) LIKE ? OR
                          LOWER(PaymentStatus) LIKE ?
                    ORDER BY BillDate DESC
                '''
            else:
                query = '''
                    SELECT 
                        BillNo,
                        BillDate,
                        Supplier,
                        Contact,
                        TotalAmount,
                        0 as Advance,
                        TotalAmount as Remaining,
                        PaymentStatus
                    FROM Purchases 
                    WHERE LOWER(BillNo) LIKE ? OR 
                          LOWER(Supplier) LIKE ? OR 
                          LOWER(Contact) LIKE ? OR
                          LOWER(PaymentStatus) LIKE ?
                    ORDER BY BillDate DESC
                '''
            
            search_pattern = f'%{search_text}%'
            cur.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
            
            rows = cur.fetchall()
            for row in rows:
                billno, billdate, supplier, contact, total, advance, remaining, status = row
                formatted_total = f"Rs.{total:,.2f}"
                formatted_advance = f"Rs.{advance:,.2f}"
                formatted_remaining = f"Rs.{remaining:,.2f}"
                
                if status == 'Paid':
                    tag = 'Paid'
                elif status == 'Overdue':
                    tag = 'Overdue'
                else:
                    tag = 'Pending'
                
                display_status = 'Pending' if (advance > 0 and remaining > 0) else status
                
                self.purchase_tree.insert('', 'end', values=(
                    billno, billdate, supplier, contact, 
                    formatted_total, formatted_advance, formatted_remaining, display_status
                ), tags=(tag,))
            
            con.close()
            
        except Exception as ex:
            print(f"Error searching purchases: {str(ex)}")
    
    def search_sales(self):
        search_text = self.sales_search_var.get().strip().lower()
        if not search_text:
            self.load_sales()
            return
        try:
            for item in self.sales_tree.get_children():
                self.sales_tree.delete(item)
            
            con = sqlite3.connect('Possystem.db')
            cur = con.cursor()
            
            total_amount = 0
            total_received = 0
            total_bankrec = 0
            total_pending = 0
            total_overdue = 0
            
            # Search invoices
            cur.execute("PRAGMA table_info(invoices)")
            columns = [col[1] for col in cur.fetchall()]
            has_due_date = 'due_date' in columns
            advance_columns = ['advance_payment', 'advance_amount', 'advance', 'advance_paid', 'GivenAmount']
            found_advance_col = None
            for col in advance_columns:
                if col in columns:
                    found_advance_col = col
                    break
            
            if found_advance_col and has_due_date:
                query = f'''
                    SELECT 
                        invoice_no,
                        invoice_date,
                        customer_name,
                        customer_contact,
                        total_amount,
                        COALESCE({found_advance_col}, 0) as advance,
                        due_date
                    FROM invoices 
                    WHERE LOWER(invoice_no) LIKE ? OR 
                          LOWER(customer_name) LIKE ? OR 
                          LOWER(customer_contact) LIKE ?
                    ORDER BY invoice_date DESC
                '''
            elif found_advance_col:
                query = f'''
                    SELECT 
                        invoice_no,
                        invoice_date,
                        customer_name,
                        customer_contact,
                        total_amount,
                        COALESCE({found_advance_col}, 0) as advance,
                        NULL as due_date
                    FROM invoices 
                    WHERE LOWER(invoice_no) LIKE ? OR 
                          LOWER(customer_name) LIKE ? OR 
                          LOWER(customer_contact) LIKE ?
                    ORDER BY invoice_date DESC
                '''
            elif has_due_date:
                query = '''
                    SELECT 
                        invoice_no,
                        invoice_date,
                        customer_name,
                        customer_contact,
                        total_amount,
                        0 as advance,
                        due_date
                    FROM invoices 
                    WHERE LOWER(invoice_no) LIKE ? OR 
                          LOWER(customer_name) LIKE ? OR 
                          LOWER(customer_contact) LIKE ?
                    ORDER BY invoice_date DESC
                '''
            else:
                query = '''
                    SELECT 
                        invoice_no,
                        invoice_date,
                        customer_name,
                        customer_contact,
                        total_amount,
                        0 as advance,
                        NULL as due_date
                    FROM invoices 
                    WHERE LOWER(invoice_no) LIKE ? OR 
                          LOWER(customer_name) LIKE ? OR 
                          LOWER(customer_contact) LIKE ?
                    ORDER BY invoice_date DESC
                '''
            
            search_pattern = f'%{search_text}%'
            cur.execute(query, (search_pattern, search_pattern, search_pattern))
            invoice_rows = cur.fetchall()
            
            for row in invoice_rows:
                invoice_no, date, customer_name, contact, total, advance, due_date = row
                total_amount += total
                total_received += advance
                remaining = total - advance
                status = "Paid"
                bankrec = 0
                if status == 'Paid':
                    total_received += remaining
                    remaining = 0
                formatted_total = f"Rs.{total:,.2f}"
                formatted_advance = f"Rs.{advance:,.2f}"
                formatted_bankrec = f"Rs.{bankrec:,.2f}"
                formatted_remaining = f"Rs.{remaining:,.2f}"
                tag = 'Paid'
                self.sales_tree.insert('', 'end', values=(
                    invoice_no, date, customer_name, contact,
                    formatted_total, formatted_advance, formatted_bankrec, formatted_remaining, status, "B2C"
                ), tags=(tag,))
            
            # Search B2B
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='B2B_Sales'")
            if cur.fetchone():
                cur.execute("PRAGMA table_info(B2B_Sales)")
                b2b_columns = [col[1] for col in cur.fetchall()]
                has_final_amount = 'FinalAmount' in b2b_columns
                has_advance_col = 'Advance' in b2b_columns
                has_bankrec_col = 'BankRec' in b2b_columns
                
                if has_final_amount and has_advance_col and has_bankrec_col:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            FinalAmount,
                            COALESCE(Advance, 0) as advance,
                            COALESCE(BankRec, 0) as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        WHERE LOWER(InvoiceID) LIKE ? OR 
                              LOWER(CustomerName) LIKE ? OR 
                              LOWER(Phone) LIKE ?
                        ORDER BY InvoiceDate DESC
                    '''
                elif has_final_amount and has_advance_col:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            FinalAmount,
                            COALESCE(Advance, 0) as advance,
                            0 as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        WHERE LOWER(InvoiceID) LIKE ? OR 
                              LOWER(CustomerName) LIKE ? OR 
                              LOWER(Phone) LIKE ?
                        ORDER BY InvoiceDate DESC
                    '''
                elif has_final_amount:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            FinalAmount,
                            0 as advance,
                            0 as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        WHERE LOWER(InvoiceID) LIKE ? OR 
                              LOWER(CustomerName) LIKE ? OR 
                              LOWER(Phone) LIKE ?
                        ORDER BY InvoiceDate DESC
                    '''
                elif has_advance_col and has_bankrec_col:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            TotalAmount,
                            COALESCE(Advance, 0) as advance,
                            COALESCE(BankRec, 0) as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        WHERE LOWER(InvoiceID) LIKE ? OR 
                              LOWER(CustomerName) LIKE ? OR 
                              LOWER(Phone) LIKE ?
                        ORDER BY InvoiceDate DESC
                    '''
                elif has_advance_col:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            TotalAmount,
                            COALESCE(Advance, 0) as advance,
                            0 as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        WHERE LOWER(InvoiceID) LIKE ? OR 
                              LOWER(CustomerName) LIKE ? OR 
                              LOWER(Phone) LIKE ?
                        ORDER BY InvoiceDate DESC
                    '''
                else:
                    b2b_query = '''
                        SELECT 
                            InvoiceID,
                            InvoiceDate,
                            CustomerName,
                            Phone,
                            TotalAmount,
                            0 as advance,
                            0 as bankrec,
                            PaymentStatus
                        FROM B2B_Sales 
                        WHERE LOWER(InvoiceID) LIKE ? OR 
                              LOWER(CustomerName) LIKE ? OR 
                              LOWER(Phone) LIKE ?
                        ORDER BY InvoiceDate DESC
                    '''
                
                cur.execute(b2b_query, (search_pattern, search_pattern, search_pattern))
                b2b_rows = cur.fetchall()
                
                for row in b2b_rows:
                    if len(row) >= 8:
                        invoice_no, date, customer_name, contact, total, advance, bankrec, status = row[:8]
                        total_amount += total
                        total_received += advance
                        total_bankrec += bankrec
                        remaining = total - advance
                        if status == 'Paid':
                            total_received = total_received - advance + total
                            remaining = 0
                        elif status == 'Overdue':
                            total_overdue += remaining
                            total_pending += remaining
                        elif status == 'Pending':
                            total_pending += remaining
                        formatted_total = f"Rs.{total:,.2f}"
                        formatted_advance = f"Rs.{advance:,.2f}"
                        formatted_bankrec = f"Rs.{bankrec:,.2f}"
                        formatted_remaining = f"Rs.{remaining:,.2f}"
                        if status == 'Paid':
                            tag = 'Paid'
                        elif status == 'Overdue':
                            tag = 'Overdue'
                        else:
                            tag = 'Pending'
                        self.sales_tree.insert('', 'end', values=(
                            invoice_no, date, customer_name, contact,
                            formatted_total, formatted_advance, formatted_bankrec, formatted_remaining, status, "B2B"
                        ), tags=(tag,))
            
            con.close()
            
        except Exception as ex:
            print(f"Error searching sales: {str(ex)}")
    
    def clear_purchase_search(self):
        self.purchase_search_var.set("")
        self.load_purchases()
    
    def clear_sales_search(self):
        self.sales_search_var.set("")
        self.load_sales()
    
    def load_all_data(self):
        self.load_purchases()
        self.load_sales()
        messagebox.showinfo("Refreshed", "All data has been refreshed", parent=self.root)
    
    def show_paid_only(self):
        for item in self.purchase_tree.get_children():
            tags = self.purchase_tree.item(item)['tags']
            if tags and 'Paid' in tags:
                self.purchase_tree.reattach(item, '', 'end')
            else:
                self.purchase_tree.detach(item)
        for item in self.sales_tree.get_children():
            tags = self.sales_tree.item(item)['tags']
            if tags and 'Paid' in tags:
                self.sales_tree.reattach(item, '', 'end')
            else:
                self.sales_tree.detach(item)
    
    def show_pending_only(self):
        for item in self.purchase_tree.get_children():
            tags = self.purchase_tree.item(item)['tags']
            if tags and 'Pending' in tags:
                self.purchase_tree.reattach(item, '', 'end')
            else:
                self.purchase_tree.detach(item)
        for item in self.sales_tree.get_children():
            tags = self.sales_tree.item(item)['tags']
            if tags and 'Pending' in tags:
                self.sales_tree.reattach(item, '', 'end')
            else:
                self.sales_tree.detach(item)
    
    def show_overdue_only(self):
        for item in self.purchase_tree.get_children():
            tags = self.purchase_tree.item(item)['tags']
            if tags and 'Overdue' in tags:
                self.purchase_tree.reattach(item, '', 'end')
            else:
                self.purchase_tree.detach(item)
        for item in self.sales_tree.get_children():
            tags = self.sales_tree.item(item)['tags']
            if tags and 'Overdue' in tags:
                self.sales_tree.reattach(item, '', 'end')
            else:
                self.sales_tree.detach(item)
    
    def show_all(self):
        self.load_purchases()
        self.load_sales()
    
    def generate_purchase_pdf(self):
        try:
            items = []
            for item in self.purchase_tree.get_children():
                values = self.purchase_tree.item(item)['values']
                items.append(values)
            
            if not items:
                messagebox.showwarning("No Data", "No purchase data to export to PDF", parent=self.root)
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"Purchase_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                title="Save Purchase Report As"
            )
            
            if not filename:
                return
            
            doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
            styles = getSampleStyleSheet()
            
            # Custom title style with purchase color
            title_style = ParagraphStyle(
                'PurchaseTitle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=TA_CENTER,
                textColor=colors.HexColor(self.purchase_color),
                spaceAfter=20
            )
            
            # Custom summary style - Updated to be Black and Bold
            summary_style = ParagraphStyle(
                'PurchaseSummary',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=20,
                alignment=TA_LEFT
            )
            
            def footer(canvas, doc):
                canvas.saveState()
                footer_text = "Software produced by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363"
                canvas.setFont('Helvetica', 8)
                canvas.drawCentredString(doc.width/2.0 + doc.leftMargin, 0.5*inch, footer_text)
                page_num = f"Page {doc.page}"
                canvas.drawRightString(doc.width + doc.leftMargin, 0.5*inch, page_num)
                canvas.restoreState()
            
            story = []
            title = Paragraph("Purchase Amount Tracker Report", title_style)
            story.append(title)
            date_str = Paragraph(f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M:%S %p')}", styles['Normal'])
            story.append(date_str)
            story.append(Spacer(1, 20))
            
            # Use HTML <b> tags to make the entire summary bold using the black styling
            summary_text = self.purchase_summary_var.get()
            summary = Paragraph(f"<b>Summary: {summary_text}</b>", summary_style)
            story.append(summary)
            story.append(Spacer(1, 20))
            
            table_data = []
            headers = ["Bill No", "Bill Date", "Supplier", "Contact", "Total Amount", "Advance", "Remaining", "Status"]
            table_data.append(headers)
            for item in items:
                table_data.append(item)
            
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.purchase_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (4, 1), (6, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            for i, row in enumerate(table_data[1:], 1):
                status = row[7] if len(row) > 7 else ''
                if status == 'Paid':
                    table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#DCFCE7'))]))
                elif status == 'Pending':
                    table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FEF3C7'))]))
                elif status == 'Overdue':
                    table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FEE2E2'))]))
            
            story.append(table)
            doc.build(story, onFirstPage=footer, onLaterPages=footer)
            messagebox.showinfo("PDF Generated", f"Purchase report saved successfully!\n\nLocation: {filename}", parent=self.root)
            
        except Exception as ex:
            print(f"Error generating purchase PDF: {str(ex)}")
            messagebox.showerror("Error", f"Error generating PDF: {str(ex)}", parent=self.root)
    
    def generate_sales_pdf(self):
        try:
            items = []
            for item in self.sales_tree.get_children():
                values = self.sales_tree.item(item)['values']
                items.append(values)
            
            if not items:
                messagebox.showwarning("No Data", "No sales data to export to PDF", parent=self.root)
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"Sales_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                title="Save Sales Report As"
            )
            
            if not filename:
                return
            
            doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
            styles = getSampleStyleSheet()
            
            # Custom title style with sales color
            title_style = ParagraphStyle(
                'SalesTitle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=TA_CENTER,
                textColor=colors.HexColor(self.sales_color),
                spaceAfter=20
            )
            
            # Custom summary style - Updated to be Black and Bold
            summary_style = ParagraphStyle(
                'SalesSummary',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=20,
                alignment=TA_LEFT
            )
            
            def footer(canvas, doc):
                canvas.saveState()
                footer_text = "Software produced by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363"
                canvas.setFont('Helvetica', 8)
                canvas.drawCentredString(doc.width/2.0 + doc.leftMargin, 0.5*inch, footer_text)
                page_num = f"Page {doc.page}"
                canvas.drawRightString(doc.width + doc.leftMargin, 0.5*inch, page_num)
                canvas.restoreState()
            
            story = []
            title = Paragraph("Sales Amount Tracker Report", title_style)
            story.append(title)
            date_str = Paragraph(f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M:%S %p')}", styles['Normal'])
            story.append(date_str)
            story.append(Spacer(1, 20))
            
            # Use HTML <b> tags to make the entire summary bold using the black styling
            summary_text = self.sales_summary_var.get()
            summary = Paragraph(f"<b>Summary: {summary_text}</b>", summary_style)
            story.append(summary)
            story.append(Spacer(1, 20))
            
            table_data = []
            headers = ["Invoice No", "Date", "Customer Name", "Contact", "Total Amount", "Advance", "Bank Rec", "Remaining", "Status", "Type"]
            table_data.append(headers)
            for item in items:
                table_data.append(item)
            
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.sales_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (4, 1), (7, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            for i, row in enumerate(table_data[1:], 1):
                status = row[8] if len(row) > 8 else ''
                if status == 'Paid':
                    table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#DCFCE7'))]))
                elif status == 'Pending':
                    table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FEF3C7'))]))
                elif status == 'Overdue':
                    table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FEE2E2'))]))
            
            story.append(table)
            doc.build(story, onFirstPage=footer, onLaterPages=footer)
            messagebox.showinfo("PDF Generated", f"Sales report saved successfully!\n\nLocation: {filename}", parent=self.root)
            
        except Exception as ex:
            print(f"Error generating sales PDF: {str(ex)}")
            messagebox.showerror("Error", f"Error generating PDF: {str(ex)}", parent=self.root)


def main():
    root = tk.Tk()
    app = BankAmountTracker(root)
    root.mainloop()


if __name__ == "__main__":
    main()