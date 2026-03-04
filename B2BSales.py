# B2BClient.py
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import sqlite3
import re
from datetime import datetime, timedelta
from tkcalendar import Calendar  # replaced DateEntry with Calendar
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch


class B2BClientClass:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1000x580+50+50")  # Further reduced window size
        self.root.title("Inventory Management System | B2B Client Dashboard")
        self.root.config(bg="#1E3A8A")
        self.root.focus_force()

        # Main container frame
        self.main_frame = Frame(self.root, bg="#1E3A8A")
        self.main_frame.pack(fill=BOTH, expand=True, padx=8, pady=8)

        # Create database and table if not exists
        self.setup_database()

        # ===========================================
        # All Variables=========
        self.var_searchby = StringVar()
        self.var_searchtxt = StringVar()
        self.var_invoice_id = StringVar()
        self.var_invoice_date = StringVar()
        self.var_due_date = StringVar()
        self.var_customer_name = StringVar()
        self.var_phone = StringVar()
        self.var_description = StringVar()
        self.var_tax_percentage = StringVar(value="9.0")  # Default tax 9%
        self.var_tax_amount = StringVar()
        self.var_total_amount = StringVar()
        self.var_final_amount = StringVar()
        self.var_advance = StringVar()
        self.var_payment_status = StringVar(value="Pending")
        
        # Payment variables
        self.var_payment_amount = StringVar()
        self.var_payment_date = StringVar()
        self.var_paid_from = StringVar()
        self.current_balance = 0

        # ===Header with Date Time and Stats====
        header_frame = Frame(self.main_frame, bg="#1E3A8A", height=35)
        header_frame.pack(fill=X, pady=(0, 5))

        # Title on left
        title_frame = Frame(header_frame, bg="#1E3A8A")
        title_frame.pack(side=LEFT, padx=5)

        title_label = Label(title_frame, text="B2B Client Dashboard", 
                           font=("bahnschrift light semicondensed", 12, "bold"),
                           bg="#1E3A8A", fg="white")
        title_label.pack(side=LEFT)

        # Live date and time
        self.datetime_label = Label(header_frame, 
                                   font=("bahnschrift light semicondensed", 8),
                                   bg="#1E3A8A", fg="white")
        self.datetime_label.pack(side=LEFT, padx=5, pady=(2, 0))
        self.update_datetime()

        # ===Sales Trackers Section====
        trackers_frame = Frame(self.main_frame, bg="#1E3A8A")
        trackers_frame.pack(fill=X, pady=(0, 5))
        
        # Create grid for trackers (2 rows, 2 columns)
        for i in range(2):
            trackers_frame.grid_rowconfigure(i, weight=1, uniform="tracker_row")
        for i in range(2):
            trackers_frame.grid_columnconfigure(i, weight=1, uniform="tracker_col")

        # Daily Sales Tracker
        self.daily_tracker = self.create_tracker_card(trackers_frame, "💰 DAILY SALES", "PKR 0.00", 
                                                     "#10B981", 0, 0)
        
        # Weekly Sales Tracker
        self.weekly_tracker = self.create_tracker_card(trackers_frame, "📈 WEEKLY SALES", "PKR 0.00", 
                                                      "#3B82F6", 0, 1)
        
        # Monthly Sales Tracker
        self.monthly_tracker = self.create_tracker_card(trackers_frame, "📊 MONTHLY SALES", "PKR 0.00", 
                                                       "#F59E0B", 1, 0)
        
        # Annual Sales Tracker
        self.annual_tracker = self.create_tracker_card(trackers_frame, "📅 ANNUAL SALES", "PKR 0.00", 
                                                      "#8B5CF6", 1, 1)

        # ===Main Content Frame (Left and Right Panels)====
        content_frame = Frame(self.main_frame, bg="#1E3A8A")
        content_frame.pack(fill=BOTH, expand=True)

        # ===Left Panel (Invoice Information)====
        left_panel = Frame(content_frame, bg="white", bd=1,
                          relief=RIDGE, highlightbackground="#1E3A8A", highlightthickness=1)
        left_panel.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5), pady=(0, 5))

        # ===Invoice Information Section====
        invoice_frame = LabelFrame(left_panel, text="Invoice Details", 
                                  font=("bahnschrift light semicondensed", 10, "bold"),
                                  bd=1, relief=GROOVE, bg="white", fg="#1E3A8A")
        invoice_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Create a frame for the form
        form_frame = Frame(invoice_frame, bg="white")
        form_frame.pack(fill=BOTH, expand=True, padx=3, pady=3)

        # ====Form Fields====
        # Configure grid for form
        for i in range(8):
            form_frame.grid_rowconfigure(i, minsize=32)
        form_frame.grid_columnconfigure(0, weight=1, minsize=90)
        form_frame.grid_columnconfigure(1, weight=2, minsize=170)
        form_frame.grid_columnconfigure(2, weight=1, minsize=90)
        form_frame.grid_columnconfigure(3, weight=2, minsize=170)

        # Row 0: Invoice ID
        Label(form_frame, text="Invoice ID:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=0, column=0, sticky="w", padx=2, pady=2)

        self.txt_invoice_id = Entry(form_frame, textvariable=self.var_invoice_id,
                                   font=("Aptos Display", 8), bg="#F9FAFB", fg="#1F2937",
                                   state='readonly', highlightthickness=1,
                                   highlightbackground="#D1D5DB", highlightcolor="#3B82F6",
                                   width=11)
        self.txt_invoice_id.grid(row=0, column=1, sticky="w", padx=2, pady=2, ipady=2)

        # Row 0: Invoice Date and Due Date in same line
        Label(form_frame, text="Invoice Date:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=0, column=2, sticky="w", padx=2, pady=2)

        self.invoice_date_frame, self.invoice_date_entry = self.create_date_entry(
            form_frame, self.var_invoice_date, row=0, col=3)

        # Row 1: Due Date
        Label(form_frame, text="Due Date:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=1, column=0, sticky="w", padx=2, pady=2)

        self.due_date_frame, self.due_date_entry = self.create_date_entry(
            form_frame, self.var_due_date, row=1, col=1)

        # Row 1: Customer Name
        Label(form_frame, text="Customer Name:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=1, column=2, sticky="w", padx=2, pady=2)

        Entry(form_frame, textvariable=self.var_customer_name,
             font=("Aptos Display", 8), bg="white", fg="#1F2937",
             highlightthickness=1, highlightbackground="#D1D5DB", 
             highlightcolor="#3B82F6", width=17).grid(
                 row=1, column=3, sticky="w", padx=2, pady=2, ipady=2)

        # Row 2: Phone
        Label(form_frame, text="Phone:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=2, column=0, sticky="w", padx=2, pady=2)

        phone_frame = Frame(form_frame, bg="white")
        phone_frame.grid(row=2, column=1, columnspan=3, sticky="w", padx=2, pady=2)

        phone_label = Label(phone_frame, text="+92", font=("Aptos Display", 8),
                           bg="#F3F4F6", fg="#6B7280", relief=SUNKEN, bd=1)
        phone_label.pack(side=LEFT, fill=Y)

        self.phone_entry = Entry(phone_frame, font=("Aptos Display", 8),
                                bg="white", fg="#1F2937", justify=LEFT,
                                highlightthickness=1, highlightbackground="#D1D5DB", 
                                highlightcolor="#3B82F6", width=17)
        self.phone_entry.pack(side=LEFT, ipady=2)
        self.phone_entry.bind('<KeyRelease>', self.validate_phone)
        self.phone_entry.bind('<FocusIn>', self.on_phone_focus)

        # Row 3: Description
        Label(form_frame, text="Description:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=3, column=0, sticky="nw", padx=2, pady=2)

        self.txt_description = Text(form_frame, font=("Aptos Display", 8),
                                   bg="white", fg="#1F2937",
                                   height=2, wrap=WORD,
                                   highlightthickness=1,
                                   highlightbackground="#D1D5DB", 
                                   highlightcolor="#3B82F6")
        self.txt_description.grid(row=3, column=1, columnspan=3, sticky="nsew", padx=2, pady=2)

        # Row 4: Total Amount (before tax)
        Label(form_frame, text="Total Amount:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=4, column=0, sticky="w", padx=2, pady=2)

        self.txt_total_amount = Entry(form_frame, textvariable=self.var_total_amount,
                                     font=("Aptos Display", 8), bg="white", fg="#1F2937",
                                     highlightthickness=1, highlightbackground="#D1D5DB", 
                                     highlightcolor="#3B82F6", width=11)
        self.txt_total_amount.grid(row=4, column=1, sticky="w", padx=2, pady=2, ipady=2)
        self.txt_total_amount.bind('<KeyRelease>', self.calculate_tax_and_final)

        # Row 4: Tax Percentage and Amount in same line
        Label(form_frame, text="Tax %:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=4, column=2, sticky="w", padx=2, pady=2)

        tax_frame = Frame(form_frame, bg="white")
        tax_frame.grid(row=4, column=3, sticky="w", padx=2, pady=2)

        Entry(tax_frame, textvariable=self.var_tax_percentage,
             font=("Aptos Display", 8), bg="white", fg="#1F2937",
             highlightthickness=1, highlightbackground="#D1D5DB", 
             highlightcolor="#3B82F6", width=5).pack(side=LEFT, padx=(0, 2))
        
        Label(tax_frame, text="%", 
              font=("Aptos Display", 8),
              bg="white", fg="#1F2937").pack(side=LEFT, padx=(0, 6))
        
        Label(tax_frame, text="Tax Amt:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937").pack(side=LEFT, padx=(0, 2))
        
        self.txt_tax_amount = Entry(tax_frame, textvariable=self.var_tax_amount,
                                   font=("Aptos Display", 8), bg="#F9FAFB", fg="#1F2937",
                                   state='readonly', highlightthickness=1,
                                   highlightbackground="#D1D5DB", highlightcolor="#3B82F6",
                                   width=9)
        self.txt_tax_amount.pack(side=LEFT)

        # Row 5: Final Amount and Advance in same line
        Label(form_frame, text="Final Amount:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=5, column=0, sticky="w", padx=2, pady=2)

        self.txt_final_amount = Entry(form_frame, textvariable=self.var_final_amount,
                                     font=("Aptos Display", 8), bg="#F9FAFB", fg="#1F2937",
                                     state='readonly', highlightthickness=1,
                                     highlightbackground="#D1D5DB", highlightcolor="#3B82F6",
                                     width=11)
        self.txt_final_amount.grid(row=5, column=1, sticky="w", padx=2, pady=2, ipady=2)

        Label(form_frame, text="Advance:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=5, column=2, sticky="w", padx=2, pady=2)

        Entry(form_frame, textvariable=self.var_advance,
             font=("Aptos Display", 8), bg="white", fg="#1F2937",
             highlightthickness=1, highlightbackground="#D1D5DB", 
             highlightcolor="#3B82F6", width=11).grid(
                 row=5, column=3, sticky="w", padx=2, pady=2, ipady=2)

        # Row 6: Payment Status
        Label(form_frame, text="Payment Status:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=6, column=0, sticky="w", padx=2, pady=2)

        status_frame = Frame(form_frame, bg="white")
        status_frame.grid(row=6, column=1, columnspan=3, sticky="w", padx=2, pady=2)

        cmb_payment_status = ttk.Combobox(status_frame, textvariable=self.var_payment_status,
                                         values=["Pending", "Paid", "Overdue"],
                                         state='readonly', font=("Aptos Display", 8),
                                         width=9)
        cmb_payment_status.pack(side=LEFT, padx=(0, 6))

        btn_check_status = Button(status_frame, text="Check Status", command=self.manual_check_status,
                                 font=("Aptos Display", 7, "bold"), bg="#F59E0B", fg="White",
                                 cursor="hand2", padx=5,
                                 activebackground="#D97706", activeforeground="white")
        btn_check_status.pack(side=LEFT)

        # ===Action Buttons Section====
        btn_frame = Frame(left_panel, bg="white")
        btn_frame.pack(fill=X, padx=5, pady=(5, 5))

        btn_save = Button(btn_frame, text="Save Invoice", command=self.save_invoice,
                         font=("Aptos Display", 8, "bold"), bg="#10B981", fg="White",
                         cursor="hand2", padx=10,
                         activebackground="#059669", activeforeground="white")
        btn_save.pack(side=LEFT, padx=2, pady=2, expand=True)

        btn_update = Button(btn_frame, text="Update Invoice", command=self.update_invoice,
                           font=("Aptos Display", 8, "bold"), bg="#3B82F6", fg="White",
                           cursor="hand2", padx=10,
                           activebackground="#2563EB", activeforeground="white")
        btn_update.pack(side=LEFT, padx=2, pady=2, expand=True)

        btn_delete = Button(btn_frame, text="Delete Invoice", command=self.delete_invoice,
                           font=("Aptos Display", 8, "bold"), bg="#DC2626", fg="White",
                           cursor="hand2", padx=10,
                           activebackground="#B91C1C", activeforeground="white")
        btn_delete.pack(side=LEFT, padx=2, pady=2, expand=True)

        btn_clear = Button(btn_frame, text="Clear All", command=self.clear_all,
                          font=("Aptos Display", 8, "bold"), bg="#6B7280", fg="White",
                          cursor="hand2", padx=10,
                          activebackground="#4B5563", activeforeground="white")
        btn_clear.pack(side=LEFT, padx=2, pady=2, expand=True)

        # ===Make a Payment Section====
        payment_frame = LabelFrame(left_panel, text="Make a Payment", 
                                  font=("bahnschrift light semicondensed", 10, "bold"),
                                  bd=1, relief=GROOVE, bg="white", fg="#1E3A8A")
        payment_frame.pack(fill=BOTH, expand=True, padx=5, pady=(0, 5))

        # Create a frame for payment form
        payment_form = Frame(payment_frame, bg="white")
        payment_form.pack(fill=BOTH, expand=True, padx=6, pady=6)

        # Configure grid for payment form
        for i in range(4):
            payment_form.grid_rowconfigure(i, minsize=30)
        payment_form.grid_columnconfigure(0, weight=1, minsize=90)
        payment_form.grid_columnconfigure(1, weight=2, minsize=170)

        # Row 0: Amount Paid
        Label(payment_form, text="Amount Paid (PKR):", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=0, column=0, sticky="w", padx=2, pady=2)

        Entry(payment_form, textvariable=self.var_payment_amount,
             font=("Aptos Display", 8), bg="white", fg="#1F2937",
             highlightthickness=1, highlightbackground="#D1D5DB", 
             highlightcolor="#3B82F6", width=17).grid(
                 row=0, column=1, sticky="w", padx=2, pady=2, ipady=2)

        # Row 1: Date Paid
        Label(payment_form, text="Date Paid:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=1, column=0, sticky="w", padx=2, pady=2)

        self.payment_date_frame, self.payment_date_entry = self.create_date_entry(
            payment_form, self.var_payment_date, row=1, col=1)

        # Row 2: Paid From (Bank)
        Label(payment_form, text="Paid From:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937", anchor="w").grid(
                  row=2, column=0, sticky="w", padx=2, pady=2)

        cmb_paid_from = ttk.Combobox(payment_form, textvariable=self.var_paid_from,
                                    values=["Meezan Bank", "Alfalah Bank", "Allied Bank", "Habib Bank"],
                                    state='readonly', font=("Aptos Display", 8),
                                    width=15)
        cmb_paid_from.grid(row=2, column=1, sticky="w", padx=2, pady=2)
        cmb_paid_from.current(0)

        # Row 3: Add Payment Button
        btn_add_payment = Button(payment_form, text="Add Payment", command=self.add_payment,
                                font=("Aptos Display", 8, "bold"), bg="#8B5CF6", fg="White",
                                cursor="hand2", padx=10,
                                activebackground="#7C3AED", activeforeground="white")
        btn_add_payment.grid(row=3, column=0, columnspan=2, pady=6, sticky="ew")

        # ===Right Panel (Table and Search)====
        right_panel = Frame(content_frame, bg="white", bd=1,
                           relief=RIDGE, highlightbackground="#1E3A8A", highlightthickness=1)
        right_panel.pack(side=RIGHT, fill=BOTH, expand=True, pady=(0, 5))

        # ===Search Frame=====
        SearchFrame = Frame(right_panel, bg="white")
        SearchFrame.pack(fill=X, padx=6, pady=6)

        Label(SearchFrame, text="Search:", 
              font=("Aptos Display", 8, "bold"),
              bg="white", fg="#1F2937").pack(side=LEFT, padx=(0, 5))

        cmb_search = ttk.Combobox(SearchFrame, textvariable=self.var_searchby,
                                 values=["Select", "Invoice ID", "Customer Name",
                                         "Phone", "Invoice Date", "Payment Status"],
                                 state='readonly', font=("Aptos Display", 8), width=9)
        cmb_search.pack(side=LEFT, padx=(0, 5))
        cmb_search.current(0)

        txt_search = Entry(SearchFrame, textvariable=self.var_searchtxt,
                          font=("Aptos Display", 8), bg="white", fg="#1F2937", width=20,
                          highlightthickness=1, highlightbackground="#D1D5DB", 
                          highlightcolor="#3B82F6")
        txt_search.pack(side=LEFT, padx=(0, 5))

        btn_search = Button(SearchFrame, text="Search", command=self.search,
                           font=("Aptos Display", 8, "bold"), bg="#3B82F6", fg="White",
                           cursor="hand2", padx=8,
                           activebackground="#2563EB", activeforeground="white")
        btn_search.pack(side=LEFT, padx=(0, 3))

        btn_show_all = Button(SearchFrame, text="Show All", command=self.show,
                             font=("Aptos Display", 8, "bold"), bg="#10B981", fg="White",
                             cursor="hand2", padx=8,
                             activebackground="#059669", activeforeground="white")
        btn_show_all.pack(side=LEFT)

        # ===PDF Buttons Frame====
        pdf_frame = Frame(right_panel, bg="white")
        pdf_frame.pack(fill=X, padx=6, pady=(0, 3))

        btn_pdf_single = Button(pdf_frame, text="📄 Selected PDF", command=self.generate_single_pdf,
                               font=("Aptos Display", 7, "bold"), bg="#8B5CF6", fg="White",
                               cursor="hand2", padx=5,
                               activebackground="#7C3AED", activeforeground="white")
        btn_pdf_single.pack(side=LEFT, padx=(0, 3))

        btn_pdf_all = Button(pdf_frame, text="📊 All PDF", command=self.generate_all_pdf,
                            font=("Aptos Display", 7, "bold"), bg="#EC4899", fg="White",
                            cursor="hand2", padx=5,
                            activebackground="#DB2777", activeforeground="white")
        btn_pdf_all.pack(side=LEFT)

        # ===B2B Client Table====
        table_container = Frame(right_panel, bg="white")
        table_container.pack(fill=BOTH, expand=True, padx=6, pady=(0, 6))

        scrollx = Scrollbar(table_container, orient=HORIZONTAL)
        scrolly = Scrollbar(table_container, orient=VERTICAL)

        # Create style for table
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                       background="white",
                       foreground="#1F2937",
                       rowheight=20,
                       fieldbackground="white",
                       bordercolor="#D1D5DB",
                       borderwidth=1)
        style.configure("Custom.Treeview.Heading",
                       background="#1E3A8A",
                       foreground="white",
                       font=("Aptos Display", 7, "bold"),
                       relief=FLAT)
        style.map('Custom.Treeview',
                 background=[('selected', '#1E40AF')],
                 foreground=[('selected', 'white')])

        # Updated columns for B2B Sales - added Bank-Rec column
        self.B2BTable = ttk.Treeview(table_container, 
                                     columns=("invoiceid", "invoicedate", "duedate", "customername", 
                                             "phone", "description", "totalamount", "finalamount", 
                                             "advance", "bankrec", "paymentstatus", "balance"),
                                     yscrollcommand=scrolly.set, xscrollcommand=scrollx.set,
                                     show="headings", style="Custom.Treeview", height=9)
        
        scrollx.pack(side=BOTTOM, fill=X)
        scrolly.pack(side=RIGHT, fill=Y)
        scrollx.config(command=self.B2BTable.xview)
        scrolly.config(command=self.B2BTable.yview)

        # Configure headings with updated columns (added Bank-Rec column)
        headings = [
            ("invoiceid", "Invoice ID", 75),
            ("invoicedate", "Invoice Date", 75),
            ("duedate", "Due Date", 75),
            ("customername", "Customer Name", 95),
            ("phone", "Phone", 85),
            ("description", "Description", 95),
            ("totalamount", "Total (PKR)", 85),
            ("finalamount", "Final (PKR)", 85),
            ("advance", "Advance (PKR)", 85),
            ("bankrec", "Bank-Rec (PKR)", 85),
            ("paymentstatus", "Status", 65),
            ("balance", "Balance (PKR)", 85)
        ]

        for col, text, width in headings:
            self.B2BTable.heading(col, text=text)
            self.B2BTable.column(col, width=width, anchor=CENTER)

        self.B2BTable.column("customername", anchor=W)
        self.B2BTable.column("description", anchor=W)
        self.B2BTable.column("totalamount", anchor=E)
        self.B2BTable.column("finalamount", anchor=E)
        self.B2BTable.column("advance", anchor=E)
        self.B2BTable.column("bankrec", anchor=E)
        self.B2BTable.column("balance", anchor=E)

        self.B2BTable.pack(fill=BOTH, expand=True)
        self.B2BTable.bind("<ButtonRelease-1>", self.get_invoice_data)

        # Initialize
        self.generate_invoice_id()
        self.show()
        self.update_stats()
        self.update_sales_trackers()
        
        # Start periodic updates for trackers
        self.periodic_tracker_update()

    # ---------- Custom Date Entry Methods ----------
    def create_date_entry(self, parent, textvariable, row, col, colspan=1):
        """Create a custom date entry with placeholder and calendar button"""
        frame = Frame(parent, bg="white", highlightthickness=1,
                      highlightbackground="#D1D5DB", highlightcolor="#3B82F6")
        frame.grid(row=row, column=col, columnspan=colspan, padx=2, pady=2, sticky='w')

        # Entry for date
        entry = Entry(frame, font=("Aptos Display", 8), bg="white", fg="#999999",
                      relief=FLAT, bd=0)
        entry.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))

        # Placeholder text
        placeholder = "DD/MM/YYYY"
        entry.insert(0, placeholder)

        # Store placeholder and variable reference
        entry.placeholder = placeholder
        entry.textvariable = textvariable

        # Bind events
        entry.bind("<FocusIn>", self.on_date_focus_in)
        entry.bind("<FocusOut>", self.on_date_focus_out)
        entry.bind("<KeyRelease>", self.on_date_key_release)

        # Calendar button
        btn_cal = Button(frame, text="📅", font=("Aptos Display", 8),
                         bg="#3B82F6", fg="white", bd=0,
                         cursor="hand2", width=3,
                         command=lambda: self.open_calendar(entry, textvariable))
        btn_cal.pack(side=RIGHT, padx=(0, 2))

        return frame, entry

    def on_date_focus_in(self, event):
        """Clear placeholder on focus in"""
        entry = event.widget
        if entry.get() == entry.placeholder:
            entry.delete(0, END)
            entry.config(fg="#1F2937")

    def on_date_focus_out(self, event):
        """Restore placeholder if empty, otherwise validate"""
        entry = event.widget
        value = entry.get().strip()
        if not value or value == entry.placeholder:
            entry.delete(0, END)
            entry.insert(0, entry.placeholder)
            entry.config(fg="#999999")
            entry.textvariable.set("")
        else:
            # Validate date format
            if not self.validate_date_string(value):
                messagebox.showerror("Invalid Date",
                                     "Please enter a valid date in DD/MM/YYYY format.",
                                     parent=self.root)
                # Revert to placeholder
                entry.delete(0, END)
                entry.insert(0, entry.placeholder)
                entry.config(fg="#999999")
                entry.textvariable.set("")
            else:
                entry.textvariable.set(value)

    def on_date_key_release(self, event):
        """Format date as user types: only digits, auto-insert slashes"""
        entry = event.widget
        # Ignore if placeholder is showing
        if entry.get() == entry.placeholder:
            return

        # Get current text and remove any non-digit characters
        current = entry.get()
        digits = ''.join(filter(str.isdigit, current))

        # Limit to 8 digits (DDMMYYYY)
        if len(digits) > 8:
            digits = digits[:8]

        # Build formatted string with slashes
        formatted = ""
        if len(digits) > 0:
            formatted = digits[:2]
        if len(digits) > 2:
            formatted += "/" + digits[2:4]
        if len(digits) > 4:
            formatted += "/" + digits[4:8]

        # Update entry and preserve cursor position
        cursor_pos = entry.index(INSERT)
        entry.delete(0, END)
        entry.insert(0, formatted)

        # Adjust cursor to skip over slashes
        new_pos = cursor_pos
        if new_pos > 2:
            new_pos += 1          # after first slash
        if new_pos > 5:
            new_pos += 1          # after second slash
        entry.icursor(min(new_pos, len(formatted)))

        # Update the StringVar with the current formatted value
        entry.textvariable.set(formatted)

    def validate_date_string(self, date_str):
        """Check if date_str is a valid date in DD/MM/YYYY format"""
        if not date_str or date_str == "DD/MM/YYYY":
            return False
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
            return True
        except ValueError:
            return False

    def open_calendar(self, entry, textvariable):
        """Open a calendar popup just below the entry field and set the selected date"""
        def set_date():
            selected = cal.selection_get()
            if selected:
                formatted = selected.strftime("%d/%m/%Y")
                entry.delete(0, END)
                entry.insert(0, formatted)
                entry.config(fg="#1F2937")
                textvariable.set(formatted)
            top.destroy()

        # Get the position of the entry widget
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height() + 5  # 5px below entry

        top = Toplevel(self.root)
        top.title("Select Date")
        top.grab_set()
        top.resizable(False, False)

        # Position the popup
        top.geometry(f"300x250+{x}+{y}")

        cal = Calendar(top, selectmode='day', date_pattern='dd/mm/yyyy')
        cal.pack(padx=10, pady=10)

        btn_ok = Button(top, text="OK", command=set_date,
                        bg="#3B82F6", fg="white", font=("Aptos Display", 8))
        btn_ok.pack(pady=5)

        # Ensure the popup stays on top
        top.transient(self.root)
        top.focus_force()
        top.grab_set()
    # ---------------------------------------------------------

    def create_tracker_card(self, parent, title, value, color, row, col):
        """Create a sales tracker card"""
        card = Frame(parent, bg="white", bd=1, relief=RAISED, 
                    highlightbackground=color, highlightthickness=1)
        card.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
        
        # Content frame
        content = Frame(card, bg="white")
        content.pack(fill=BOTH, expand=True, padx=6, pady=6)
        
        # Title with icon
        title_label = Label(content, text=title, 
                          font=("bahnschrift light semicondensed", 8, "bold"),
                          bg="white", fg="#1F2937", anchor="w")
        title_label.pack(anchor="w", pady=(0, 4))
        
        # Value
        value_label = Label(content, text=value, 
                          font=("bahnschrift light semicondensed", 11, "bold"),
                          bg="white", fg=color, anchor="w")
        value_label.pack(anchor="w")
        
        # Store reference to update later
        if "DAILY" in title:
            self.daily_sales_label = value_label
        elif "WEEKLY" in title:
            self.weekly_sales_label = value_label
        elif "MONTHLY" in title:
            self.monthly_sales_label = value_label
        elif "ANNUAL" in title:
            self.annual_sales_label = value_label
        
        return card

    def calculate_tax_and_final(self, event=None):
        """Calculate tax amount and final amount based on total amount and tax percentage"""
        try:
            total_amount_str = self.var_total_amount.get().strip()
            tax_percent_str = self.var_tax_percentage.get().strip()
            
            if total_amount_str and tax_percent_str:
                total_amount = float(total_amount_str)
                tax_percent = float(tax_percent_str)
                
                if total_amount >= 0 and tax_percent >= 0:
                    tax_amount = total_amount * (tax_percent / 100)
                    final_amount = total_amount + tax_amount
                    
                    self.var_tax_amount.set(f"{tax_amount:.2f}")
                    self.var_final_amount.set(f"{final_amount:.2f}")
                else:
                    self.var_tax_amount.set("0.00")
                    self.var_final_amount.set("0.00")
            else:
                self.var_tax_amount.set("0.00")
                self.var_final_amount.set("0.00")
        except:
            self.var_tax_amount.set("0.00")
            self.var_final_amount.set("0.00")

    def add_payment(self):
        """Add a payment to the selected invoice - ONLY INCREASE BANK-REC, NOT ADVANCE"""
        if not self.var_invoice_id.get():
            messagebox.showwarning("Warning", "Please select an invoice first", parent=self.root)
            return
        
        if not self.var_payment_amount.get():
            messagebox.showwarning("Warning", "Please enter payment amount", parent=self.root)
            return
        
        if not self.var_payment_date.get():
            messagebox.showwarning("Warning", "Please select payment date", parent=self.root)
            return
        
        if not self.var_paid_from.get():
            messagebox.showwarning("Warning", "Please select bank", parent=self.root)
            return
        
        try:
            payment_amount = float(self.var_payment_amount.get())
            
            if payment_amount <= 0:
                messagebox.showwarning("Warning", "Payment amount must be greater than 0", parent=self.root)
                return
            
            # Get current bank-rec, advance and final amount from database
            con = sqlite3.connect(database='Possystem.db')
            cur = con.cursor()
            
            # Get current advance, bank-rec and final amount
            cur.execute("SELECT Advance, BankRec, FinalAmount, PaymentStatus FROM B2B_Sales WHERE InvoiceID=?", 
                       (self.var_invoice_id.get(),))
            result = cur.fetchone()
            
            if not result:
                messagebox.showerror("Error", "Invoice not found", parent=self.root)
                return
            
            current_advance = float(result[0]) if result[0] else 0
            current_bankrec = float(result[1]) if result[1] else 0
            final_amount = float(result[2]) if result[2] else 0
            current_status = result[3]
            
            # Calculate new bank-rec (advance remains unchanged)
            new_bankrec = current_bankrec + payment_amount
            
            # Calculate total received (advance + bankrec)
            total_received = current_advance + new_bankrec
            
            # Check if total received exceeds final amount
            if total_received > final_amount:
                messagebox.showwarning("Warning", 
                    f"Total payment exceeds final amount!\n"
                    f"Final Amount: PKR {final_amount:,.2f}\n"
                    f"Current Advance: PKR {current_advance:,.2f}\n"
                    f"Current Bank-Rec: PKR {current_bankrec:,.2f}\n"
                    f"Payment of PKR {payment_amount:,.2f} would make total: PKR {total_received:,.2f}",
                    parent=self.root)
                return
            
            # Update ONLY bank-rec in B2B_Sales table (advance remains unchanged)
            cur.execute("UPDATE B2B_Sales SET BankRec = ? WHERE InvoiceID = ?", 
                       (new_bankrec, self.var_invoice_id.get()))
            
            # Save payment details to Payments table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS Payments (
                    PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
                    InvoiceID TEXT NOT NULL,
                    PaymentDate TEXT NOT NULL,
                    Amount REAL NOT NULL,
                    BankName TEXT NOT NULL,
                    FOREIGN KEY (InvoiceID) REFERENCES B2B_Sales (InvoiceID)
                )
            ''')
            
            cur.execute('''
                INSERT INTO Payments (InvoiceID, PaymentDate, Amount, BankName)
                VALUES (?, ?, ?, ?)
            ''', (
                self.var_invoice_id.get(),
                self.var_payment_date.get(),
                payment_amount,
                self.var_paid_from.get()
            ))
            
            # Check if payment status needs to be updated
            if total_received >= final_amount:
                new_status = 'Paid'
                cur.execute("UPDATE B2B_Sales SET PaymentStatus = 'Paid' WHERE InvoiceID = ?", 
                           (self.var_invoice_id.get(),))
                self.var_payment_status.set("Paid")
            else:
                new_status = current_status if current_status else 'Pending'
                # Don't change status if it was already 'Overdue'
                if current_status != 'Overdue':
                    cur.execute("UPDATE B2B_Sales SET PaymentStatus = 'Pending' WHERE InvoiceID = ?", 
                               (self.var_invoice_id.get(),))
                    self.var_payment_status.set("Pending")
            
            con.commit()
            con.close()
            
            # Update display
            self.show()
            
            # Clear payment fields
            self.var_payment_amount.set("")
            self.var_payment_date.set("")
            self.var_paid_from.set("Meezan Bank")
            self.payment_date_entry.delete(0, END)
            self.payment_date_entry.insert(0, self.payment_date_entry.placeholder)
            self.payment_date_entry.config(fg="#999999")
            
            messagebox.showinfo("Success", 
                f"Payment of PKR {payment_amount:,.2f} added successfully!\n"
                f"New Bank-Rec: PKR {new_bankrec:,.2f}\n"
                f"Total Received (Advance + Bank-Rec): PKR {total_received:,.2f}\n"
                f"Status: {new_status}", 
                parent=self.root)
            
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to add payment: {str(ex)}", parent=self.root)
            print(f"Payment error: {str(ex)}")

    def setup_database(self):
        """Create database and tables if they don't exist"""
        try:
            db_path = 'Possystem.db'
            print(f"Connecting to database at: {db_path}")

            con = sqlite3.connect(database=db_path)
            cur = con.cursor()

            # Check if B2B_Sales table exists
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='B2B_Sales'")
            if cur.fetchone():
                # Check if all columns exist
                cur.execute("PRAGMA table_info(B2B_Sales)")
                columns = [col[1] for col in cur.fetchall()]
                
                # Add new columns if they don't exist
                if 'TaxPercentage' not in columns:
                    cur.execute("ALTER TABLE B2B_Sales ADD COLUMN TaxPercentage REAL DEFAULT 9.0")
                    print("Added TaxPercentage column to B2B_Sales table")
                
                if 'TaxAmount' not in columns:
                    cur.execute("ALTER TABLE B2B_Sales ADD COLUMN TaxAmount REAL DEFAULT 0")
                    print("Added TaxAmount column to B2B_Sales table")
                
                if 'FinalAmount' not in columns:
                    cur.execute("ALTER TABLE B2B_Sales ADD COLUMN FinalAmount REAL DEFAULT 0")
                    print("Added FinalAmount column to B2B_Sales table")
                
                # Add BankRec column if it doesn't exist
                if 'BankRec' not in columns:
                    cur.execute("ALTER TABLE B2B_Sales ADD COLUMN BankRec REAL DEFAULT 0")
                    print("Added BankRec column to B2B_Sales table")
            else:
                # Create B2B_Sales table with all columns including BankRec
                cur.execute('''
                    CREATE TABLE B2B_Sales (
                        InvoiceID TEXT PRIMARY KEY,
                        InvoiceDate TEXT NOT NULL,
                        DueDate TEXT NOT NULL,
                        CustomerName TEXT NOT NULL,
                        Phone TEXT NOT NULL,
                        Description TEXT,
                        TotalAmount REAL NOT NULL,
                        TaxPercentage REAL DEFAULT 9.0,
                        TaxAmount REAL DEFAULT 0,
                        FinalAmount REAL NOT NULL,
                        Advance REAL DEFAULT 0,
                        BankRec REAL DEFAULT 0,
                        PaymentStatus TEXT DEFAULT 'Pending'
                    )
                ''')
                print("Created B2B_Sales table successfully")

            # Create Payments table if not exists
            cur.execute('''
                CREATE TABLE IF NOT EXISTS Payments (
                    PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
                    InvoiceID TEXT NOT NULL,
                    PaymentDate TEXT NOT NULL,
                    Amount REAL NOT NULL,
                    BankName TEXT NOT NULL,
                    FOREIGN KEY (InvoiceID) REFERENCES B2B_Sales (InvoiceID)
                )
            ''')
            print("Payments table created/verified")

            con.commit()
            con.close()
            print("Database setup completed successfully")
        except Exception as ex:
            print(f"Error setting up database: {str(ex)}")
            messagebox.showerror(
                "Database Error", f"Cannot setup database: {str(ex)}", parent=self.root)

    def update_datetime(self):
        """Update the live date and time display"""
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %I:%M:%S %p")
        self.datetime_label.config(text=dt_string)
        self.root.after(1000, self.update_datetime)

    def update_stats(self):
        """Update dashboard statistics"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM B2B_Sales")
            total = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM B2B_Sales WHERE PaymentStatus='Pending'")
            pending = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM B2B_Sales WHERE PaymentStatus='Paid'")
            paid = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM B2B_Sales WHERE PaymentStatus='Overdue'")
            overdue = cur.fetchone()[0]
            
        except Exception as ex:
            print(f"Error updating stats: {str(ex)}")
        finally:
            con.close()

    def generate_invoice_id(self):
        """Generate auto-incrementing invoice ID"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute(
                "SELECT InvoiceID FROM B2B_Sales ORDER BY InvoiceID DESC LIMIT 1")
            result = cur.fetchone()

            if result:
                last_invoice = result[0]
                numbers = re.findall(r'\d+', last_invoice)
                if numbers:
                    last_number = int(numbers[-1])
                    next_number = last_number + 1
                else:
                    next_number = 1
            else:
                next_number = 1

            next_invoice = f"INV{next_number:06d}"
            self.var_invoice_id.set(next_invoice)
        except Exception as ex:
            self.var_invoice_id.set("INV000001")
            print(f"Error generating invoice: {str(ex)}")
        finally:
            con.close()

    # Removed on_invoice_date_select, on_due_date_select, on_payment_date_select as they are no longer needed.

    def manual_check_status(self):
        """Manually check and update payment status based on due date"""
        if not self.var_due_date.get() or not self.var_invoice_date.get():
            messagebox.showwarning(
                "Warning", "Please select invoice date and due date first", parent=self.root)
            return

        try:
            due_date = datetime.strptime(self.var_due_date.get(), "%d/%m/%Y")
            current_date = datetime.now()

            if due_date < current_date:
                if self.var_payment_status.get() == "Paid":
                    messagebox.showinfo("Status Info",
                                        f"Due date has passed, but status is already set to 'Paid'.",
                                        parent=self.root)
                else:
                    self.var_payment_status.set("Overdue")
                    messagebox.showinfo("Status Check",
                                        "Status set to 'Overdue' (due date has passed)",
                                        parent=self.root)
            else:
                if self.var_payment_status.get() == "Paid":
                    messagebox.showinfo("Status Info",
                                        "Status is already set to 'Paid'.",
                                        parent=self.root)
                else:
                    self.var_payment_status.set("Pending")
                    messagebox.showinfo("Status Check",
                                        "Status set to 'Pending' (due date is in the future)",
                                        parent=self.root)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Invalid date format: {str(e)}", parent=self.root)

    def on_phone_focus(self, event):
        """Set cursor to the beginning of the entry when focused"""
        self.phone_entry.icursor(0)

    def validate_phone(self, event=None):
        """Validate Phone to accept exactly 10 digits"""
        current_text = self.phone_entry.get()
        if current_text:
            digits = ''.join(filter(str.isdigit, current_text))
            if len(digits) > 10:
                digits = digits[:10]

            self.phone_entry.delete(0, END)
            self.phone_entry.insert(0, digits)
            self.phone_entry.icursor(len(digits))

            # Change background color based on validation
            if len(digits) == 10:
                self.phone_entry.config(bg="#DCFCE7")
            elif len(digits) > 0:
                self.phone_entry.config(bg="white")
            else:
                self.phone_entry.config(bg="white")

    def validate_phone_format(self, phone_digits):
        """Validate that phone has exactly 10 digits"""
        if not phone_digits:
            return False, "Phone number is required"

        if len(phone_digits) != 10:
            return False, "Phone must be exactly 10 digits"

        if not phone_digits.isdigit():
            return False, "Phone must contain only digits"

        return True, f"+92{phone_digits}"

    def validate_invoice(self):
        """Validate the complete invoice"""
        errors = []

        if not self.var_invoice_id.get():
            errors.append("Invoice ID is required")

        if not self.var_invoice_date.get():
            errors.append("Invoice Date is required")

        if not self.var_due_date.get():
            errors.append("Due Date is required")

        if not self.var_customer_name.get().strip():
            errors.append("Customer Name is required")

        phone_digits = self.phone_entry.get().strip()
        if not phone_digits:
            errors.append("Phone is required")
        else:
            is_valid, msg = self.validate_phone_format(phone_digits)
            if not is_valid:
                errors.append(msg)

        # Validate total amount
        if not self.var_total_amount.get():
            errors.append("Total Amount is required")
        else:
            try:
                total_amount = float(self.var_total_amount.get())
                if total_amount <= 0:
                    errors.append("Total Amount must be greater than 0")
            except:
                errors.append("Total Amount must be a valid number")

        # Validate tax percentage
        if self.var_tax_percentage.get():
            try:
                tax_percent = float(self.var_tax_percentage.get())
                if tax_percent < 0:
                    errors.append("Tax percentage cannot be negative")
                if tax_percent > 100:
                    errors.append("Tax percentage cannot be more than 100%")
            except:
                errors.append("Tax percentage must be a valid number")

        # Validate advance amount
        advance = self.var_advance.get()
        if advance:
            try:
                advance_float = float(advance)
                if advance_float < 0:
                    errors.append("Advance amount cannot be negative")
                
                # Check if advance is greater than final amount
                final_amount = float(self.var_final_amount.get()) if self.var_final_amount.get() else 0
                if advance_float > final_amount:
                    errors.append("Advance amount cannot be greater than Final Amount")
            except:
                errors.append("Advance amount must be a valid number")

        if errors:
            messagebox.showerror("Validation Error",
                                 "\n".join(errors), parent=self.root)
            return False

        return True

    def save_invoice(self):
        """Save the invoice to database"""
        if not self.validate_invoice():
            return

        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            phone_digits = self.phone_entry.get().strip()
            is_valid, full_phone = self.validate_phone_format(phone_digits)
            if not is_valid:
                messagebox.showerror("Error", full_phone, parent=self.root)
                return

            # Calculate amounts
            total_amount = float(self.var_total_amount.get())
            tax_percentage = float(self.var_tax_percentage.get())
            tax_amount = float(self.var_tax_amount.get())
            final_amount = float(self.var_final_amount.get())
            advance_amount = float(self.var_advance.get()) if self.var_advance.get() else 0
            # Initialize bankrec with 0
            bankrec_amount = 0

            cur.execute("""
                INSERT INTO B2B_Sales(InvoiceID, InvoiceDate, DueDate, CustomerName, Phone, Description, 
                                      TotalAmount, TaxPercentage, TaxAmount, FinalAmount, Advance, BankRec, PaymentStatus)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.var_invoice_id.get(),
                self.var_invoice_date.get(),
                self.var_due_date.get(),
                self.var_customer_name.get().strip(),
                full_phone,
                self.txt_description.get('1.0', END).strip(),
                total_amount,
                tax_percentage,
                tax_amount,
                final_amount,
                advance_amount,
                bankrec_amount,
                self.var_payment_status.get()
            ))

            con.commit()
            messagebox.showinfo(
                "Success", "Invoice saved successfully", parent=self.root)
            self.show()
            self.clear_all()
            self.update_stats()
            self.update_sales_trackers()  # Update trackers after saving

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Error", "Invoice ID already exists", parent=self.root)
        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error saving invoice: {str(ex)}", parent=self.root)
            print(f"Save error: {str(ex)}")
        finally:
            con.close()

    def update_invoice(self):
        """Update an existing invoice"""
        if not self.validate_invoice():
            return

        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT * FROM B2B_Sales WHERE InvoiceID=?",
                        (self.var_invoice_id.get(),))
            if not cur.fetchone():
                messagebox.showerror(
                    "Error", "Invoice not found", parent=self.root)
                return

            phone_digits = self.phone_entry.get().strip()
            is_valid, full_phone = self.validate_phone_format(phone_digits)
            if not is_valid:
                messagebox.showerror("Error", full_phone, parent=self.root)
                return

            # Calculate amounts
            total_amount = float(self.var_total_amount.get())
            tax_percentage = float(self.var_tax_percentage.get())
            tax_amount = float(self.var_tax_amount.get())
            final_amount = float(self.var_final_amount.get())
            advance_amount = float(self.var_advance.get()) if self.var_advance.get() else 0
            
            # Get current bankrec value
            cur.execute("SELECT BankRec FROM B2B_Sales WHERE InvoiceID=?", (self.var_invoice_id.get(),))
            bankrec_result = cur.fetchone()
            bankrec_amount = float(bankrec_result[0]) if bankrec_result and bankrec_result[0] else 0

            cur.execute("""
                UPDATE B2B_Sales SET 
                InvoiceDate=?, DueDate=?, CustomerName=?, Phone=?, Description=?, 
                TotalAmount=?, TaxPercentage=?, TaxAmount=?, FinalAmount=?, Advance=?, BankRec=?, PaymentStatus=?
                WHERE InvoiceID=?
            """, (
                self.var_invoice_date.get(),
                self.var_due_date.get(),
                self.var_customer_name.get().strip(),
                full_phone,
                self.txt_description.get('1.0', END).strip(),
                total_amount,
                tax_percentage,
                tax_amount,
                final_amount,
                advance_amount,
                bankrec_amount,
                self.var_payment_status.get(),
                self.var_invoice_id.get()
            ))

            con.commit()
            messagebox.showinfo(
                "Success", "Invoice updated successfully", parent=self.root)
            self.show()
            self.update_stats()
            self.update_sales_trackers()  # Update trackers after updating

        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error updating invoice: {str(ex)}", parent=self.root)
            print(f"Update error: {str(ex)}")
        finally:
            con.close()

    def delete_invoice(self):
        """Delete an invoice"""
        if not self.var_invoice_id.get():
            messagebox.showerror(
                "Error", "Please select an invoice to delete", parent=self.root)
            return

        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT * FROM B2B_Sales WHERE InvoiceID=?",
                        (self.var_invoice_id.get(),))
            if not cur.fetchone():
                messagebox.showerror(
                    "Error", "Invoice not found", parent=self.root)
                return

            op = messagebox.askyesno(
                "Confirm", "Do you really want to delete this invoice?", parent=self.root)
            if op:
                # First delete related payments
                cur.execute("DELETE FROM Payments WHERE InvoiceID=?", (self.var_invoice_id.get(),))
                # Then delete the invoice
                cur.execute("DELETE FROM B2B_Sales WHERE InvoiceID=?",
                            (self.var_invoice_id.get(),))

                con.commit()
                messagebox.showinfo(
                    "Success", "Invoice deleted successfully", parent=self.root)
                self.clear_all()
                self.show()
                self.update_stats()
                self.update_sales_trackers()  # Update trackers after deleting

        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error deleting invoice: {str(ex)}", parent=self.root)
        finally:
            con.close()

    def clear_all(self):
        """Clear all fields and reset form"""
        self.var_invoice_date.set("")
        self.var_due_date.set("")
        self.var_customer_name.set("")
        self.phone_entry.delete(0, END)
        self.txt_description.delete('1.0', END)
        self.var_total_amount.set("")
        self.var_tax_percentage.set("9.0")
        self.var_tax_amount.set("")
        self.var_final_amount.set("")
        self.var_advance.set("")
        self.var_payment_status.set("Pending")
        
        # Clear payment fields
        self.var_payment_amount.set("")
        self.var_payment_date.set("")
        self.var_paid_from.set("Meezan Bank")

        self.var_searchtxt.set("")
        self.var_searchby.set("Select")

        self.generate_invoice_id()

        # Reset custom date entries to placeholder
        for entry in [self.invoice_date_entry, self.due_date_entry, self.payment_date_entry]:
            entry.delete(0, END)
            entry.insert(0, entry.placeholder)
            entry.config(fg="#999999")
            entry.textvariable.set("")

    def show(self):
        """Show all B2B invoices in the table with Bank-Rec column"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute(
                "SELECT InvoiceID, InvoiceDate, DueDate, CustomerName, Phone, Description, "
                "TotalAmount, TaxPercentage, TaxAmount, FinalAmount, Advance, BankRec, PaymentStatus "
                "FROM B2B_Sales ORDER BY InvoiceID DESC")
            rows = cur.fetchall()

            self.B2BTable.delete(*self.B2BTable.get_children())

            for row in rows:
                formatted_row = list(row)
                
                # Format amounts
                formatted_row[6] = f"{formatted_row[6]:,.2f}"  # Total Amount
                # Skip tax percentage (index 7) and tax amount (index 8)
                formatted_row[9] = f"{formatted_row[9]:,.2f}"  # Final Amount
                formatted_row[10] = f"{formatted_row[10]:,.2f}"  # Advance
                formatted_row[11] = f"{formatted_row[11]:,.2f}"  # Bank-Rec (new column)
                
                # Calculate balance
                advance = float(row[10]) if row[10] else 0
                final = float(row[9])
                balance = final - advance
                formatted_row.append(f"{balance:,.2f}")  # Balance
                
                # Truncate description if too long
                if len(formatted_row[5]) > 25:
                    formatted_row[5] = formatted_row[5][:22] + "..."
                
                # Color coding for payment status
                if formatted_row[12] == "Overdue":
                    formatted_row[12] = "⚠ " + formatted_row[12]
                elif formatted_row[12] == "Paid":
                    formatted_row[12] = "✓ " + formatted_row[12]

                # Create new row with Bank-Rec column
                display_row = [
                    formatted_row[0],  # InvoiceID
                    formatted_row[1],  # InvoiceDate
                    formatted_row[2],  # DueDate
                    formatted_row[3],  # CustomerName
                    formatted_row[4],  # Phone
                    formatted_row[5],  # Description
                    formatted_row[6],  # TotalAmount
                    formatted_row[9],  # FinalAmount
                    formatted_row[10], # Advance
                    formatted_row[11], # Bank-Rec (new column)
                    formatted_row[12], # PaymentStatus
                    formatted_row[13]  # Balance
                ]

                self.B2BTable.insert('', END, values=display_row)

        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error loading data: {str(ex)}", parent=self.root)
            print(f"Show error: {str(ex)}")
        finally:
            con.close()

    def get_invoice_data(self, ev):
        """Get selected invoice data for editing"""
        try:
            f = self.B2BTable.focus()
            if not f:
                return

            content = self.B2BTable.item(f)
            row = content['values']
            if not row or len(row) < 12:  # Now 12 columns with Bank-Rec
                return

            self.clear_all()

            self.var_invoice_id.set(row[0])
            self.var_invoice_date.set(row[1])
            self.var_due_date.set(row[2])
            self.var_customer_name.set(row[3])

            # Remove status symbols if present
            payment_status = row[10]  # Now index 10 instead of 11
            if payment_status.startswith("⚠ "):
                payment_status = payment_status[2:]
            elif payment_status.startswith("✓ "):
                payment_status = payment_status[2:]
            self.var_payment_status.set(payment_status)

            phone = str(row[4])
            if phone.startswith('+92'):
                phone = phone[3:]
            elif phone.startswith('92') and len(phone) == 12:
                phone = phone[2:]

            digits = ''.join(filter(str.isdigit, phone))
            if len(digits) >= 10:
                digits = digits[-10:]

            self.phone_entry.delete(0, END)
            self.phone_entry.insert(0, digits)

            # Update custom date entries
            self.invoice_date_entry.delete(0, END)
            if row[1]:
                self.invoice_date_entry.insert(0, row[1])
                self.invoice_date_entry.config(fg="#1F2937")
            else:
                self.invoice_date_entry.insert(0, self.invoice_date_entry.placeholder)
                self.invoice_date_entry.config(fg="#999999")

            self.due_date_entry.delete(0, END)
            if row[2]:
                self.due_date_entry.insert(0, row[2])
                self.due_date_entry.config(fg="#1F2937")
            else:
                self.due_date_entry.insert(0, self.due_date_entry.placeholder)
                self.due_date_entry.config(fg="#999999")

            self.txt_description.delete('1.0', END)
            self.txt_description.insert('1.0', row[5] if row[5] else "")

            self.var_total_amount.set(row[6].replace(',', ''))
            
            # Need to get tax percentage from database since it's not in display
            con = sqlite3.connect(database='Possystem.db')
            cur = con.cursor()
            cur.execute("SELECT TaxPercentage, TaxAmount FROM B2B_Sales WHERE InvoiceID=?", (row[0],))
            tax_data = cur.fetchone()
            con.close()
            
            if tax_data:
                self.var_tax_percentage.set(str(tax_data[0]))
                self.var_tax_amount.set(str(tax_data[1]))
            
            self.var_final_amount.set(row[7].replace(',', ''))
            self.var_advance.set(row[8].replace(',', ''))
            
            # Set Bank-Rec value
            if row[9] and row[9] != "N/A":
                self.var_advance.set(row[9].replace(',', ''))

            # Set current balance
            self.current_balance = float(row[11].replace(',', '')) if row[11] else 0

            # Recalculate to update tax and final amounts
            self.calculate_tax_and_final()

        except Exception as ex:
            print(f"Error getting invoice data: {str(ex)}")

    def search(self):
        """Search B2B invoices based on criteria"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            search_by = self.var_searchby.get()
            search_text = self.var_searchtxt.get().strip()

            if not search_text:
                messagebox.showerror(
                    "Error", "Please enter search text", parent=self.root)
                self.show()
                return

            if search_by == "Select":
                messagebox.showerror(
                    "Error", "Please select a search option", parent=self.root)
                return

            self.B2BTable.delete(*self.B2BTable.get_children())

            if search_by == "Invoice ID":
                if search_text.isdigit() and len(search_text) <= 6:
                    search_invoice = f"INV{int(search_text):06d}"
                elif search_text.upper().startswith('INV') and search_text[3:].isdigit() and len(search_text) <= 9:
                    search_invoice = f"INV{int(search_text[3:]):06d}"
                else:
                    search_invoice = search_text.upper()

                cur.execute(
                    "SELECT InvoiceID, InvoiceDate, DueDate, CustomerName, Phone, Description, "
                    "TotalAmount, TaxPercentage, TaxAmount, FinalAmount, Advance, BankRec, PaymentStatus "
                    "FROM B2B_Sales WHERE InvoiceID LIKE ?", (f'%{search_invoice}%',))

            elif search_by == "Customer Name":
                cur.execute(
                    "SELECT InvoiceID, InvoiceDate, DueDate, CustomerName, Phone, Description, "
                    "TotalAmount, TaxPercentage, TaxAmount, FinalAmount, Advance, BankRec, PaymentStatus "
                    "FROM B2B_Sales WHERE CustomerName LIKE ?", (f'%{search_text}%',))

            elif search_by == "Phone":
                phone_digits = ''.join(filter(str.isdigit, search_text))
                if phone_digits.startswith('92') and len(phone_digits) == 12:
                    phone_digits = phone_digits[2:]
                elif phone_digits.startswith('92') and len(phone_digits) > 12:
                    phone_digits = phone_digits[2:12]
                elif len(phone_digits) > 10:
                    phone_digits = phone_digits[:10]

                search_phone = f"+92{phone_digits}" if len(
                    phone_digits) == 10 else search_text

                cur.execute(
                    "SELECT InvoiceID, InvoiceDate, DueDate, CustomerName, Phone, Description, "
                    "TotalAmount, TaxPercentage, TaxAmount, FinalAmount, Advance, BankRec, PaymentStatus "
                    "FROM B2B_Sales WHERE Phone LIKE ?", (f'%{search_phone}%',))

            elif search_by == "Invoice Date":
                cur.execute(
                    "SELECT InvoiceID, InvoiceDate, DueDate, CustomerName, Phone, Description, "
                    "TotalAmount, TaxPercentage, TaxAmount, FinalAmount, Advance, BankRec, PaymentStatus "
                    "FROM B2B_Sales WHERE InvoiceDate LIKE ?", (f'%{search_text}%',))

            elif search_by == "Payment Status":
                cur.execute(
                    "SELECT InvoiceID, InvoiceDate, DueDate, CustomerName, Phone, Description, "
                    "TotalAmount, TaxPercentage, TaxAmount, FinalAmount, Advance, BankRec, PaymentStatus "
                    "FROM B2B_Sales WHERE PaymentStatus LIKE ?", (f'%{search_text}%',))

            rows = cur.fetchall()
            if rows:
                for row in rows:
                    formatted_row = list(row)
                    formatted_row[6] = f"{formatted_row[6]:,.2f}"
                    formatted_row[9] = f"{formatted_row[9]:,.2f}"
                    formatted_row[10] = f"{formatted_row[10]:,.2f}"
                    formatted_row[11] = f"{formatted_row[11]:,.2f}"  # Bank-Rec
                    
                    advance = float(row[10]) if row[10] else 0
                    final = float(row[9])
                    balance = final - advance
                    formatted_row.append(f"{balance:,.2f}")
                    
                    if len(formatted_row[5]) > 25:
                        formatted_row[5] = formatted_row[5][:22] + "..."
                    
                    if formatted_row[12] == "Overdue":
                        formatted_row[12] = "⚠ " + formatted_row[12]
                    elif formatted_row[12] == "Paid":
                        formatted_row[12] = "✓ " + formatted_row[12]

                    # Create display row with Bank-Rec column
                    display_row = [
                        formatted_row[0],  # InvoiceID
                        formatted_row[1],  # InvoiceDate
                        formatted_row[2],  # DueDate
                        formatted_row[3],  # CustomerName
                        formatted_row[4],  # Phone
                        formatted_row[5],  # Description
                        formatted_row[6],  # TotalAmount
                        formatted_row[9],  # FinalAmount
                        formatted_row[10], # Advance
                        formatted_row[11], # Bank-Rec (new column)
                        formatted_row[12], # PaymentStatus
                        formatted_row[13]  # Balance
                    ]

                    self.B2BTable.insert('', END, values=display_row)
            else:
                messagebox.showinfo(
                    "No Results", "No records found matching your search", parent=self.root)
                self.show()
        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error searching: {str(ex)}", parent=self.root)
        finally:
            con.close()

    def update_sales_trackers(self):
        """Update all sales trackers using SQL date functions (same as Sales.py)"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            # Get current date info
            current_date = datetime.now()
            
            # Daily Sales (today)
            today_formatted = current_date.strftime("%d/%m/%Y")
            cur.execute("""
                SELECT SUM(FinalAmount) FROM B2B_Sales 
                WHERE InvoiceDate = ?
            """, (today_formatted,))
            daily_sales = cur.fetchone()[0] or 0
            
            # Get all invoices and convert dates
            cur.execute("""
                SELECT FinalAmount, InvoiceDate FROM B2B_Sales
                WHERE InvoiceDate IS NOT NULL AND FinalAmount IS NOT NULL
            """)
            all_invoices = cur.fetchall()
            
            # Weekly Sales (last 7 days)
            week_ago = current_date - timedelta(days=7)
            weekly_sales = 0
            
            # Monthly Sales (current month)
            monthly_sales = 0
            
            # Annual Sales (current year)
            annual_sales = 0
            
            # Process each invoice
            for amount, invoice_date_str in all_invoices:
                try:
                    # Parse the dd/mm/yyyy date string
                    invoice_date = datetime.strptime(invoice_date_str, "%d/%m/%Y")
                    
                    # Check if within last 7 days (weekly)
                    if week_ago <= invoice_date <= current_date:
                        weekly_sales += amount
                    
                    # Check if in current month (monthly)
                    if invoice_date.year == current_date.year and invoice_date.month == current_date.month:
                        monthly_sales += amount
                    
                    # Check if in current year (annual)
                    if invoice_date.year == current_date.year:
                        annual_sales += amount
                        
                except Exception as e:
                    continue
            
            # Update labels
            self.daily_sales_label.config(text=f"PKR {daily_sales:,.2f}")
            self.weekly_sales_label.config(text=f"PKR {weekly_sales:,.2f}")
            self.monthly_sales_label.config(text=f"PKR {monthly_sales:,.2f}")
            self.annual_sales_label.config(text=f"PKR {annual_sales:,.2f}")
            
        except Exception as ex:
            print(f"Error updating sales trackers: {str(ex)}")
            # Set all to zero in case of error
            self.daily_sales_label.config(text=f"PKR 0.00")
            self.weekly_sales_label.config(text=f"PKR 0.00")
            self.monthly_sales_label.config(text=f"PKR 0.00")
            self.annual_sales_label.config(text=f"PKR 0.00")
        finally:
            con.close()

    def periodic_tracker_update(self):
        """Periodically update sales trackers every 30 seconds"""
        self.update_sales_trackers()
        self.root.after(30000, self.periodic_tracker_update)  # Update every 30 seconds

    def generate_single_pdf(self):
        """Generate PDF for selected invoice with company details and payment history - IMPROVED READABILITY"""
        selected_item = self.B2BTable.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an invoice to generate PDF", parent=self.root)
            return
        
        content = self.B2BTable.item(selected_item[0])
        row = content['values']
        
        if not row or len(row) < 12:  # Now 12 columns with Bank-Rec
            messagebox.showerror("Error", "Invalid invoice data", parent=self.root)
            return
        
        # Create PDF
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"B2B_Invoice_{row[0]}.pdf"
        )
        
        if not file_path:
            return
        
        try:
            # Get tax details and payment history from database
            con = sqlite3.connect(database='Possystem.db')
            cur = con.cursor()
            
            # Get tax details
            cur.execute("SELECT TaxPercentage, TaxAmount FROM B2B_Sales WHERE InvoiceID=?", (row[0],))
            tax_data = cur.fetchone()
            
            # Get payment history
            cur.execute("SELECT PaymentDate, Amount, BankName FROM Payments WHERE InvoiceID=? ORDER BY PaymentDate", 
                       (row[0],))
            payment_history = cur.fetchall()
            
            con.close()
            
            tax_percent = tax_data[0] if tax_data else 9.0
            tax_amount = tax_data[1] if tax_data else 0
            
            # Use letter orientation for better readability
            doc = SimpleDocTemplate(file_path, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
            elements = []
            
            # Styles with increased font sizes for better readability
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CompanyTitle',
                parent=styles['Title'],
                fontSize=18,  # Increased from 12
                spaceAfter=6,
                alignment=1,
                textColor=colors.HexColor('#1E3A8A')
            )
            
            subtitle_style = ParagraphStyle(
                'SubTitle',
                parent=styles['Normal'],
                fontSize=12,  # Increased from 8
                spaceAfter=12,
                alignment=1
            )
            
            heading_style = ParagraphStyle(
                'SectionHeading',
                parent=styles['Heading2'],
                fontSize=14,  # Increased from 10
                spaceAfter=8,
                textColor=colors.HexColor('#1E3A8A')
            )
            
            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=11  # Increased from 7
            )
            
            bold_style = ParagraphStyle(
                'Bold',
                parent=styles['Normal'],
                fontSize=11,  # Increased from 7
                fontName='Helvetica-Bold'
            )
            
            # Company Header
            elements.append(Paragraph("Dukes Tech Services", title_style))
            elements.append(Paragraph("SAAS- POS SYSTEM", subtitle_style))
            elements.append(Spacer(1, 12))
            
            # Document Title
            elements.append(Paragraph("INVOICE", title_style))
            elements.append(Spacer(1, 12))
            
            # Bank Details Section (Moved to top)
            elements.append(Paragraph("BANK DETAILS", heading_style))
            elements.append(Spacer(1, 6))
            
            bank_info = [
                ["Bank Name:", "Meezan Bank"],
                ["Account Name:", "Sherwani Studio"],
                ["Account Number:", "IBAN12345678910"]
            ]
            
            bank_table = Table(bank_info, colWidths=[120, 250])
            bank_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            elements.append(bank_table)
            elements.append(Spacer(1, 12))
            
            # Invoice Information in two columns with increased sizes
            invoice_data = [
                [Paragraph("<b>Invoice ID:</b>", bold_style), row[0], 
                 Paragraph("<b>Invoice Date:</b>", bold_style), row[1]],
                [Paragraph("<b>Customer Name:</b>", bold_style), row[3],
                 Paragraph("<b>Due Date:</b>", bold_style), row[2]],
                [Paragraph("<b>Phone:</b>", bold_style), row[4],
                 Paragraph("<b>Payment Status:</b>", bold_style), row[10]]
            ]
            
            invoice_table = Table(invoice_data, colWidths=[100, 120, 100, 120])
            invoice_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            elements.append(invoice_table)
            elements.append(Spacer(1, 12))
            
            # Description
            if row[5] and row[5] != "N/A":
                elements.append(Paragraph("<b>Description:</b>", bold_style))
                elements.append(Paragraph(row[5], normal_style))
                elements.append(Spacer(1, 12))
            
            # Financial Summary
            elements.append(Paragraph("FINANCIAL SUMMARY", heading_style))
            elements.append(Spacer(1, 8))
            
            # Parse amounts
            total_amount = float(row[6].replace(',', ''))
            final_amount = float(row[7].replace(',', ''))
            advance = float(row[8].replace(',', ''))
            bankrec = float(row[9].replace(',', ''))  # Bank-Rec amount
            balance = final_amount - advance - bankrec  # Updated balance calculation
            
            financial_info = [
                [Paragraph("<b>Item</b>", bold_style), Paragraph("<b>Amount (PKR)</b>", bold_style)],
                ["Subtotal (Before Tax)", f"{total_amount:,.2f}"],
                [f"Tax ({tax_percent:.1f}%)", f"{tax_amount:,.2f}"],
                ["Total Amount (After Tax)", f"{final_amount:,.2f}"],
                ["Advance Paid", f"{advance:,.2f}"],
                ["Bank Received", f"{bankrec:,.2f}"],  # Bank-Rec row
                ["Balance Due", f"{balance:,.2f}"]
            ]
            
            financial_table = Table(financial_info, colWidths=[250, 150])
            financial_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey)
            ]))
            
            elements.append(financial_table)
            elements.append(Spacer(1, 15))
            
            # Payment History Section
            if payment_history:
                elements.append(Paragraph("PAYMENT HISTORY", heading_style))
                elements.append(Spacer(1, 8))
                
                payment_data = []
                payment_data.append([Paragraph("<b>Date</b>", bold_style), 
                                   Paragraph("<b>Amount (PKR)</b>", bold_style),
                                   Paragraph("<b>Bank</b>", bold_style)])
                
                total_paid = 0
                for payment in payment_history:
                    payment_date = payment[0]
                    amount = float(payment[1])
                    bank = payment[2]
                    total_paid += amount
                    
                    payment_data.append([payment_date, f"{amount:,.2f}", bank])
                
                # Add total row
                payment_data.append([Paragraph("<b>TOTAL PAID</b>", bold_style), 
                                   Paragraph(f"<b>{total_paid:,.2f}</b>", bold_style),
                                   ""])
                
                payment_table = Table(payment_data, colWidths=[120, 120, 200])
                payment_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
                    ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
                ]))
                
                elements.append(payment_table)
                elements.append(Spacer(1, 15))
            
            # Footer function for each page with increased font
            def footer(canvas, doc):
                canvas.saveState()
                
                # Footer line
                canvas.setStrokeColor(colors.grey)
                canvas.setLineWidth(0.5)
                canvas.line(0.75*inch, 0.6*inch, doc.width + 0.75*inch, 0.6*inch)
                
                # Footer text
                footer_text = "Software developed by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363"
                
                # Set footer at bottom of page
                canvas.setFont('Helvetica', 8)  # Increased from 6
                canvas.setFillColor(colors.grey)
                canvas.drawCentredString(doc.width/2.0 + 0.75*inch, 0.35*inch, footer_text)
                
                # Page number
                canvas.drawRightString(doc.width + 0.75*inch, 0.35*inch, f"Page {doc.page}")
                
                canvas.restoreState()
            
            # Build PDF with footer
            doc.build(elements, onFirstPage=footer, onLaterPages=footer)
            
            messagebox.showinfo("Success", f"PDF generated successfully!\nSaved to: {file_path}", parent=self.root)
            
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(ex)}", parent=self.root)
            print(f"PDF Error: {str(ex)}")

    def generate_all_pdf(self):
        """Generate PDF for all invoices with company details - IMPROVED READABILITY"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute(
                "SELECT InvoiceID, InvoiceDate, DueDate, CustomerName, Phone, Description, "
                "TotalAmount, TaxPercentage, TaxAmount, FinalAmount, Advance, BankRec, PaymentStatus "
                "FROM B2B_Sales ORDER BY InvoiceID DESC")
            rows = cur.fetchall()
            
            if not rows:
                messagebox.showinfo("Info", "No invoices found to generate PDF", parent=self.root)
                return
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"All_B2B_Invoices_{datetime.now().strftime('%Y%m%d')}.pdf"
            )
            
            if not file_path:
                return
            
            # Use landscape orientation for table display
            doc = SimpleDocTemplate(file_path, pagesize=landscape(letter), topMargin=0.75*inch, bottomMargin=0.75*inch)
            elements = []
            
            # Styles with increased font sizes for better readability
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CompanyTitle',
                parent=styles['Title'],
                fontSize=18,  # Increased from 12
                spaceAfter=6,
                alignment=1,
                textColor=colors.HexColor('#1E3A8A')
            )
            
            subtitle_style = ParagraphStyle(
                'SubTitle',
                parent=styles['Normal'],
                fontSize=12,  # Increased from 8
                spaceAfter=8,
                alignment=1
            )
            
            report_title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=16,  # Increased from 12
                spaceAfter=8,
                alignment=1
            )
            
            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=9  # Increased from 6
            )
            
            bold_style = ParagraphStyle(
                'Bold',
                parent=styles['Normal'],
                fontSize=9,  # Increased from 6
                fontName='Helvetica-Bold'
            )
            
            # Company Header
            elements.append(Paragraph("Dukes Tech Services", title_style))
            elements.append(Paragraph("SAAS- POS SYSTEM", subtitle_style))
            elements.append(Spacer(1, 8))
            
            # Report Title
            elements.append(Paragraph("ALL B2B INVOICES REPORT", report_title_style))
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}", normal_style))
            elements.append(Spacer(1, 12))
            
            # Bank Details Section (Moved to top)
            elements.append(Paragraph("BANK DETAILS", bold_style))
            elements.append(Paragraph("Bank: Meezan Bank | Account: Sherwani Studio | IBAN: 12345678910", normal_style))
            elements.append(Spacer(1, 12))
            
            # Summary Section (Moved to top)
            total_invoices = len(rows)
            total_subtotal = 0
            total_final = 0
            total_advance = 0
            total_bankrec = 0
            total_balance = 0
            
            for row in rows:
                total_subtotal += float(row[6])
                total_final += float(row[9])
                total_advance += float(row[10]) if row[10] else 0
                total_bankrec += float(row[11]) if row[11] else 0
            
            elements.append(Paragraph("SUMMARY", bold_style))
            summary_text = f"Total Invoices: {total_invoices} | "
            summary_text += f"Total Subtotal: PKR {total_subtotal:,.2f} | "
            summary_text += f"Total Final: PKR {total_final:,.2f} | "
            summary_text += f"Total Advance: PKR {total_advance:,.2f} | "
            summary_text += f"Total Bank Received: PKR {total_bankrec:,.2f} | "
            summary_text += f"Total Balance: PKR {(total_final - total_advance - total_bankrec):,.2f}"
            
            elements.append(Paragraph(summary_text, normal_style))
            elements.append(Spacer(1, 15))
            
            # Prepare table data with Bank-Rec column
            table_data = []
            headers = ["Inv ID", "Date", "Customer", "Phone", "Subtotal", "Final", "Advance", "Bank-Rec", "Status"]
            table_data.append(headers)
            
            for row in rows:
                subtotal = float(row[6])
                final_amount = float(row[9])
                advance = float(row[10]) if row[10] else 0
                bankrec = float(row[11]) if row[11] else 0  # Bank-Rec value
                
                # Shorten customer name for compact display
                customer_name = row[3]
                if len(customer_name) > 12:
                    customer_name = customer_name[:11] + "..."
                
                table_data.append([
                    row[0],
                    row[1],
                    customer_name,
                    row[4],
                    f"{subtotal:,.2f}",
                    f"{final_amount:,.2f}",
                    f"{advance:,.2f}",
                    f"{bankrec:,.2f}",  # Bank-Rec column
                    row[12]
                ])
            
            # Create table with increased column widths for better readability
            table = Table(table_data, repeatRows=1, colWidths=[60, 55, 70, 70, 65, 65, 65, 65, 50])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (4, 1), (7, -1), 'RIGHT'),  # Adjusted for Bank-Rec column
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            
            elements.append(table)
            
            # Footer function with increased font
            def footer(canvas, doc):
                canvas.saveState()
                
                # Footer line
                canvas.setStrokeColor(colors.grey)
                canvas.setLineWidth(0.5)
                canvas.line(0.75*inch, 0.6*inch, doc.width + 0.75*inch, 0.6*inch)
                
                # Footer text
                footer_text = "Software developed by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363"
                
                # Set footer at bottom of page
                canvas.setFont('Helvetica', 7)  # Increased from 6
                canvas.setFillColor(colors.grey)
                canvas.drawCentredString(doc.width/2.0 + 0.75*inch, 0.35*inch, footer_text)
                
                # Page number
                canvas.drawRightString(doc.width + 0.75*inch, 0.35*inch, f"Page {doc.page}")
                
                canvas.restoreState()
            
            # Build PDF with footer
            doc.build(elements, onFirstPage=footer, onLaterPages=footer)
            
            messagebox.showinfo("Success", f"PDF generated successfully!\nSaved to: {file_path}", parent=self.root)
            
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(ex)}", parent=self.root)
            print(f"PDF generation error: {str(ex)}")
        finally:
            con.close()


if __name__ == "__main__":
    root = Tk()
    obj = B2BClientClass(root)
    root.mainloop()