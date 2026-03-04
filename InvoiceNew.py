import tkinter
from tkinter import *
from PIL import Image, ImageTk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import time
import datetime
import re
import os
import csv
from tkinter import font as tkfont

# Try to import fpdf for PDF generation. Fallback if not installed.
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

class Invoice_Class:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1350x700+0+0")
        self.root.title("Smart POS & Billing System | Developed by Dukes Tech Services")
        self.root.config(bg="#FDF5F5") 
        
        self.root.minsize(800, 600)
        self.root.state('zoomed') 
        
        # Initialize database tables & alter if necessary for new exchange/barcode features
        self.create_invoice_tables()
        self.upgrade_returns_table()
        self.upgrade_product_table()
        
        self.root.bind("<Configure>", self.on_window_resize)
        
        self.initial_window_width = 1350
        self.initial_window_height = 700
        self.current_window_width = self.initial_window_width
        self.current_window_height = self.initial_window_height
        
        self.cart_list = []
        self.bill_generated = False 
        
        self.bill_amnt = 0
        self.net_pay = 0
        self.discount = 0
        self.suggestion_window = None
        self.tax_rate = 8  
        self.tax_amount = 0
        self.invoice_date = datetime.datetime.now()

        try:
            self.icon_title = PhotoImage(file="IMAGES/shopcartfinal.png")
        except:
            self.icon_title = None

        self.main_container = Frame(self.root, bg="#FDF5F5")
        self.main_container.pack(fill=BOTH, expand=1)
        
        title_frame = Frame(self.main_container, bg="#E74C3C", height=70)
        title_frame.pack(side=TOP, fill=X)
        title_frame.pack_propagate(False)
        
        title = Label(title_frame, text="Smart POS & Billing System", image=self.icon_title, compound=LEFT,
                      font=("bahnschrift light semicondensed", self.scale_font_size(35), "bold"),
                      bg="#E74C3C", fg="white", anchor="w", padx=20)
        title.pack(side=LEFT, fill=Y)
        
        Button(title_frame, text="Exit", font=("Arial", self.scale_font_size(15), "bold"),
               bg="#fff000", fg="#000000", activebackground="#F34B4B", activeforeground="white",
               cursor="hand2", command=self.logout).pack(side=RIGHT, padx=20, pady=10)

        Button(title_frame, text="Returns & Exchanges", font=("Arial", self.scale_font_size(15), "bold"),
               bg="#2ECC71", fg="white", activebackground="#27AE60", activeforeground="white",
               cursor="hand2", command=self.open_return_dashboard).pack(side=RIGHT, padx=10, pady=10)

        self.lbl_clock = Label(self.main_container, text="Welcome to Smart POS & Billing System",
                               font=("bahnschrift light semicondensed", self.scale_font_size(15)),
                               bg="#C0392B", fg="white")
        self.lbl_clock.pack(side=TOP, fill=X, ipady=5)
        self.update_clock() 

        # Main content area
        self.content_frame = Frame(self.main_container, bg="#FDF5F5")
        self.content_frame.pack(fill=BOTH, expand=1, padx=10, pady=10)
        
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=2)
        self.content_frame.columnconfigure(2, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        #===========Product Frame===========
        self.var_search = StringVar()
        self.var_search_id = StringVar()
        self.var_search_barcode = StringVar()
        
        Product_Frame1 = Frame(self.content_frame, bd=4, relief=RIDGE, bg="white")
        Product_Frame1.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        Product_Frame1.columnconfigure(0, weight=1)
        Product_Frame1.rowconfigure(1, weight=0)
        Product_Frame1.rowconfigure(2, weight=1)

        Label(Product_Frame1, text="All Products", 
              font=("bahnschrift light semicondensed", self.scale_font_size(20), "bold"), 
              bg="#E74C3C", fg="white").grid(row=0, column=0, sticky="ew", ipady=5)

        Search_Frame = Frame(Product_Frame1, bd=2, relief=RIDGE, bg="#FFF5F5")
        Search_Frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        Search_Frame.columnconfigure(1, weight=1)

        lbl_search = Label(Search_Frame, text="Search Product By Name", 
                           font=("Aptos Display", self.scale_font_size(11), "bold"), bg="#FFF5F5", fg="#C0392B")
        lbl_search.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        txt_search = Entry(Search_Frame, textvariable=self.var_search, 
                           font=("Aptos Display", self.scale_font_size(11)), bg="white", fg="#C0392B", 
                           highlightthickness=1, highlightbackground="#E74C3C", highlightcolor="#E74C3C")
        txt_search.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        txt_search.bind('<KeyRelease>', self.show_suggestions)
        
        lbl_search_id = Label(Search_Frame, text="Search Product By ID", 
                              font=("Aptos Display", self.scale_font_size(11), "bold"), bg="#FFF5F5", fg="#C0392B")
        lbl_search_id.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        txt_search_id = Entry(Search_Frame, textvariable=self.var_search_id, 
                              font=("Aptos Display", self.scale_font_size(11)), bg="white", fg="#C0392B", 
                              highlightthickness=1, highlightbackground="#E74C3C", highlightcolor="#E74C3C")
        txt_search_id.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        lbl_search_barcode = Label(Search_Frame, text="Search Product By Barcode", 
                                   font=("Aptos Display", self.scale_font_size(11), "bold"), bg="#FFF5F5", fg="#C0392B")
        lbl_search_barcode.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        txt_search_barcode = Entry(Search_Frame, textvariable=self.var_search_barcode, 
                                   font=("Aptos Display", self.scale_font_size(11)), bg="white", fg="#C0392B", 
                                   highlightthickness=1, highlightbackground="#E74C3C", highlightcolor="#E74C3C")
        txt_search_barcode.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        button_frame = Frame(Search_Frame, bg="#FFF5F5")
        button_frame.grid(row=0, column=2, rowspan=3, sticky="nsew", padx=5, pady=2)
        
        Button(button_frame, text="Search by Name", command=self.search_by_name, font=("Aptos Display", 9, "bold"), 
               bg="#2ECC71", fg="white", cursor="hand2").pack(side=TOP, fill=X, pady=(0, 2))
        Button(button_frame, text="Search by ID", command=self.search_by_id, font=("Aptos Display", 9, "bold"), 
               bg="#3498DB", fg="white", cursor="hand2").pack(side=TOP, fill=X, pady=2)
        Button(button_frame, text="Search by Barcode", command=self.search_by_barcode, font=("Aptos Display", 9, "bold"), 
               bg="#9B59B6", fg="white", cursor="hand2").pack(side=TOP, fill=X, pady=2)
        Button(button_frame, text="Show All", command=self.show, font=("Aptos Display", 9, "bold"), 
               bg="#E91E63", fg="white", cursor="hand2").pack(side=TOP, fill=X, pady=(2, 0))

        #==============Product Details Frame=============
        Product_Frame3 = Frame(Product_Frame1, bd=3, relief=RIDGE, bg="white")
        Product_Frame3.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))

        scrolly = Scrollbar(Product_Frame3, orient=VERTICAL)
        scrollx = Scrollbar(Product_Frame3, orient=HORIZONTAL)

        self.ProductTable = ttk.Treeview(Product_Frame3, columns=("pid", "Name", "retailprice", "Quantity", "Status"), 
                                         yscrollcommand=scrolly.set, xscrollcommand=scrollx.set, height=10)
        
        scrollx.pack(side=BOTTOM, fill=X)
        scrolly.pack(side=RIGHT, fill=Y)
        scrollx.config(command=self.ProductTable.xview)
        scrolly.config(command=self.ProductTable.yview)
        
        self.ProductTable.pack(fill=BOTH, expand=1)
        
        self.ProductTable.heading("pid", text="ID")
        self.ProductTable.heading("Name", text="Name")
        self.ProductTable.heading("retailprice", text="Price")
        self.ProductTable.heading("Quantity", text="Qty")
        self.ProductTable.heading("Status", text="Status")
        self.ProductTable["show"] = "headings"

        self.ProductTable.column("pid", width=50, anchor="center")
        self.ProductTable.column("Name", width=150, anchor="w")
        self.ProductTable.column("retailprice", width=80, anchor="e")
        self.ProductTable.column("Quantity", width=60, anchor="center")
        self.ProductTable.column("Status", width=80, anchor="center")

        self.ProductTable.bind("<ButtonRelease-1>", self.get_data)

        #===========Customer & Cart Area===========
        middle_frame = Frame(self.content_frame, bg="#FDF5F5")
        middle_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.rowconfigure(0, weight=0)
        middle_frame.rowconfigure(1, weight=1)
        middle_frame.rowconfigure(2, weight=0)
        middle_frame.rowconfigure(3, weight=0)

        self.var_cname = StringVar()
        self.var_contact = StringVar()
        Customer_Frame = Frame(middle_frame, bd=4, relief=RIDGE, bg="white")
        Customer_Frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        Customer_Frame.columnconfigure(1, weight=1)
        Customer_Frame.columnconfigure(3, weight=1)

        Label(Customer_Frame, text="Customer Details", font=("bahnschrift light semicondensed", self.scale_font_size(14), "bold"), 
              bg="#E74C3C", fg="white").grid(row=0, column=0, columnspan=4, sticky="ew", ipady=3)
        
        Label(Customer_Frame, text="Name", font=("Aptos Display", self.scale_font_size(12), "bold"), bg="white", fg="#E74C3C").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        txt_name = Entry(Customer_Frame, textvariable=self.var_cname, font=("Aptos Display", self.scale_font_size(12)), 
                         bg="white", fg="#C0392B", highlightthickness=1, highlightbackground="#E74C3C")
        txt_name.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        Label(Customer_Frame, text="Contact (Optional)", font=("Aptos Display", self.scale_font_size(12), "bold"), 
              bg="white", fg="#C0392B").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        contact_frame = Frame(Customer_Frame, bg="white")
        contact_frame.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
        Label(contact_frame, text="+92", font=("Aptos Display", self.scale_font_size(12), "bold"), 
              bg="#FFF5F5", fg="#C0392B", relief=SUNKEN, bd=1).pack(side=LEFT, fill=Y)
        
        self.contact_entry = Entry(contact_frame, textvariable=self.var_contact, font=("Aptos Display", self.scale_font_size(12)), 
                                   bg="white", fg="#C0392B", highlightthickness=1, highlightbackground="#E74C3C")
        self.contact_entry.pack(side=LEFT, fill=BOTH, expand=True)
        self.contact_entry.bind('<KeyRelease>', self.validate_contact)
        self.var_contact.trace('w', self.format_contact)

        #========Cart Frame========
        Cart_Frame = Frame(middle_frame, bd=4, relief=RIDGE, bg="white")
        Cart_Frame.grid(row=1, column=0, sticky="nsew", pady=(0, 5))
        Cart_Frame.columnconfigure(0, weight=1)
        Cart_Frame.rowconfigure(1, weight=1)

        self.CartTitle = Label(Cart_Frame, text="Cart \t Total Products: [0]", font=("bahnschrift light semicondensed", self.scale_font_size(14), "bold"), bg="#E74C3C", fg="white")
        self.CartTitle.grid(row=0, column=0, sticky="ew", ipady=3)

        scrolly = Scrollbar(Cart_Frame, orient=VERTICAL)
        scrollx = Scrollbar(Cart_Frame, orient=HORIZONTAL)

        # Updated Cart columns
        self.CartTable = ttk.Treeview(Cart_Frame, columns=("pid", "barcode", "Name", "Price", "Quantity"), 
                                      yscrollcommand=scrolly.set, xscrollcommand=scrollx.set, height=10)
        scrollx.grid(row=2, column=0, sticky="ew")
        scrolly.grid(row=1, column=1, sticky="ns")
        scrollx.config(command=self.CartTable.xview)
        scrolly.config(command=self.CartTable.yview)
        self.CartTable.grid(row=1, column=0, sticky="nsew")
        
        self.CartTable.heading("pid", text="ID")
        self.CartTable.heading("barcode", text="Barcode")
        self.CartTable.heading("Name", text="Product Name")
        self.CartTable.heading("Price", text="Price")
        self.CartTable.heading("Quantity", text="Qty")
        self.CartTable["show"] = "headings"
        self.CartTable.column("pid", width=40, anchor="center")
        self.CartTable.column("barcode", width=80, anchor="center")
        self.CartTable.column("Name", width=140, anchor="w")
        self.CartTable.column("Price", width=70, anchor="e")
        self.CartTable.column("Quantity", width=50, anchor="center")
        self.CartTable.bind("<ButtonRelease-1>", self.get_data_cart)

        #======== NEW Quick Add to Cart Frame ========
        self.var_quick_search = StringVar()
        self.var_quick_barcode = StringVar()
        self.var_quick_name = StringVar()
        self.var_quick_price = StringVar()
        self.var_quick_qty = StringVar()
        self.var_quick_pid = StringVar()
        self.var_quick_stock = StringVar()

        QuickAdd_Frame = Frame(middle_frame, bd=4, relief=RIDGE, bg="white")
        QuickAdd_Frame.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        QuickAdd_Frame.columnconfigure(0, weight=1)
        QuickAdd_Frame.columnconfigure(1, weight=2)
        QuickAdd_Frame.columnconfigure(2, weight=1)
        QuickAdd_Frame.columnconfigure(3, weight=1)

        # Labels
        Label(QuickAdd_Frame, text="Search ID / Barcode (Press Enter)", font=("Aptos Display", 9, "bold"), bg="white", fg="#2980B9").grid(row=0, column=0, sticky="w", padx=5)
        Label(QuickAdd_Frame, text="Product Name", font=("Aptos Display", 9, "bold"), bg="white", fg="#7F8C8D").grid(row=0, column=1, sticky="w", padx=5)
        Label(QuickAdd_Frame, text="Price", font=("Aptos Display", 9, "bold"), bg="white", fg="#7F8C8D").grid(row=0, column=2, sticky="w", padx=5)
        Label(QuickAdd_Frame, text="Qty (Press Enter to Add)", font=("Aptos Display", 9, "bold"), bg="white", fg="#27AE60").grid(row=0, column=3, sticky="w", padx=5)

        # Entries
        self.entry_quick_search = Entry(QuickAdd_Frame, textvariable=self.var_quick_search, font=("Aptos Display", 11), bg="#EBF5FB", highlightthickness=1, highlightbackground="#3498DB")
        self.entry_quick_search.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.entry_quick_search.bind("<Return>", self.fetch_product_for_cart)

        Entry(QuickAdd_Frame, textvariable=self.var_quick_name, state='readonly', font=("Aptos Display", 11), bg="#F2F4F4", highlightthickness=1).grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 5))
        Entry(QuickAdd_Frame, textvariable=self.var_quick_price, state='readonly', font=("Aptos Display", 11), bg="#F2F4F4", highlightthickness=1).grid(row=1, column=2, sticky="ew", padx=5, pady=(0, 5))
        
        self.entry_quick_qty = Entry(QuickAdd_Frame, textvariable=self.var_quick_qty, font=("Aptos Display", 11, "bold"), bg="#EAFAF1", fg="#27AE60", highlightthickness=1, highlightbackground="#27AE60")
        self.entry_quick_qty.grid(row=1, column=3, sticky="ew", padx=5, pady=(0, 5))
        self.entry_quick_qty.bind("<Return>", self.add_to_cart_from_quick)

        # Info line under entries
        self.lbl_inStock = Label(QuickAdd_Frame, text="In Stock: N/A", font=("Aptos Display", 9, "bold"), bg="white", fg="#E74C3C")
        self.lbl_inStock.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        Label(QuickAdd_Frame, text="Note: Enter '0' Quantity to remove an item", font=("Aptos Display", 9, "italic"), bg="white", fg="gray").grid(row=2, column=2, columnspan=2, sticky="e", padx=5, pady=2)

        #======== Counter Price Calculator (Moved below cart) ========
        Calculator_Frame = Frame(middle_frame, bd=4, relief=RIDGE, bg="#FFF5F5")
        Calculator_Frame.grid(row=3, column=0, sticky="ew")
        Calculator_Frame.columnconfigure(0, weight=1)
        Calculator_Frame.columnconfigure(1, weight=1)
        Calculator_Frame.columnconfigure(2, weight=1)

        self.lbl_amnt = Label(Calculator_Frame, text="Subtotal\nRs. 0.00", font=("Aptos Display", 13, "bold"), bg="#34495E", fg="white", relief=FLAT)
        self.lbl_amnt.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0, ipady=5)

        self.lbl_tax = Label(Calculator_Frame, text=f"Tax ({self.tax_rate}%)\nRs. 0.00", font=("Aptos Display", 13, "bold"), bg="#E67E22", fg="white", relief=FLAT)
        self.lbl_tax.grid(row=0, column=1, sticky="nsew", padx=2, pady=0, ipady=5)

        self.lbl_net_pay = Label(Calculator_Frame, text="Total Amount\nRs. 0.00", font=("Aptos Display", 14, "bold"), bg="#C0392B", fg="white", relief=FLAT)
        self.lbl_net_pay.grid(row=0, column=2, sticky="nsew", padx=(2, 0), pady=0, ipady=5)


        #=================Billing Area===============
        billFrame = Frame(self.content_frame, bd=2, relief=RIDGE, bg='white')
        billFrame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=5)
        billFrame.columnconfigure(0, weight=1)
        billFrame.rowconfigure(1, weight=1)

        Label(billFrame, text="Customer Bill Area", font=("bahnschrift light semicondensed", self.scale_font_size(18), "bold"), bg="#E74C3C", fg="white").grid(row=0, column=0, sticky="ew", ipady=5)

        scrolly = Scrollbar(billFrame, orient=VERTICAL)
        self.txt_bill_area = Text(billFrame, yscrollcommand=scrolly.set, font=("Courier", self.scale_font_size(10)), wrap=WORD, bg="white", fg="#000000", highlightthickness=1, highlightbackground="#E74C3C")
        self.txt_bill_area.grid(row=1, column=0, sticky="nsew")
        scrolly.grid(row=1, column=1, sticky="ns")
        scrolly.config(command=self.txt_bill_area.yview)

        #=================Billing Buttons Frame===============
        billMenuFrame = Frame(billFrame, bg='white')
        billMenuFrame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        billMenuFrame.columnconfigure(0, weight=1)
        billMenuFrame.columnconfigure(1, weight=1)
        billMenuFrame.columnconfigure(2, weight=1)

        Button(billMenuFrame, text="Print Invoice", command=self.print_bill, cursor="hand2", font=("Aptos Display", 11, "bold"), bg="#3498DB", fg="white", pady=5).grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=2)
        Button(billMenuFrame, text="Clear All", command=self.clear_all, cursor="hand2", font=("Aptos Display", 11, "bold"), bg="#E91E63", fg="white", pady=5).grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        Button(billMenuFrame, text="Generate Bill", command=self.generate_bill, cursor="hand2", font=("Aptos Display", 11, "bold"), bg="#F39C12", fg="white", pady=5).grid(row=0, column=2, sticky="nsew", padx=(2, 0), pady=2)

        # ========= Payment Frame =========
        payment_frame = Frame(billFrame, bg='white', bd=1, relief=SOLID)
        payment_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        payment_frame.columnconfigure(1, weight=1)
        payment_frame.columnconfigure(3, weight=1)

        Label(payment_frame, text="Cash (Rs):", font=("Aptos Display", self.scale_font_size(11), "bold"), bg="white", fg="#C0392B").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.var_cash = StringVar()
        self.var_cash.trace('w', self.calculate_change)
        Entry(payment_frame, textvariable=self.var_cash, font=("Aptos Display", self.scale_font_size(11), "bold"), bg="white", fg="#27AE60", highlightthickness=1, highlightbackground="#E74C3C").grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        Label(payment_frame, text="Change Due:", font=("Aptos Display", self.scale_font_size(11), "bold"), bg="white", fg="#C0392B").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.var_change = StringVar()
        self.var_change.set("0.00")
        Entry(payment_frame, textvariable=self.var_change, font=("Aptos Display", self.scale_font_size(11), "bold"), bg="#FFF5F5", fg="#C0392B", state='readonly', highlightthickness=1, highlightbackground="#E74C3C").grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        # Footer 
        footer = Frame(self.main_container, bg="#E74C3C", height=40)
        footer.pack(side=BOTTOM, fill=X)
        footer.pack_propagate(False) 
        Label(footer, text="Software Produced by Dukes Tech Services | Website: dukestechservices.com | Phone: +923097671363", font=("bahnschrift light semicondensed", self.scale_font_size(11)), bg="#E74C3C", fg="white", justify=CENTER).pack(expand=True, fill=BOTH, pady=10)

        self.show()
        self.update_table_column_widths()
        self.entry_quick_search.focus()

    # ============== DATABASE & CORE FUNCTIONS ==============
    def create_invoice_tables(self):
        try:
            con = sqlite3.connect(database=r'Possystem.db')
            cur = con.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS invoices (invoice_id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_no TEXT UNIQUE NOT NULL, total_amount REAL NOT NULL, tax_amount REAL NOT NULL, subtotal_amount REAL NOT NULL, customer_name TEXT NOT NULL, customer_contact TEXT, invoice_date DATE NOT NULL, invoice_time TIME NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS invoice_items (item_id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER NOT NULL, product_id INTEGER NOT NULL, product_name TEXT NOT NULL, quantity INTEGER NOT NULL, price REAL NOT NULL, total REAL NOT NULL, FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id) ON DELETE CASCADE)''')
            cur.execute('''CREATE INDEX IF NOT EXISTS idx_invoice_date ON invoices(invoice_date)''')

            # Initialize Returns Table
            cur.execute('''CREATE TABLE IF NOT EXISTS returns (
                return_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                qty_returned INTEGER NOT NULL,
                refund_amount REAL NOT NULL,
                reason TEXT,
                return_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            con.commit()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to create tables: {str(e)}")
        finally:
            if 'con' in locals():
                con.close()

    def upgrade_returns_table(self):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("ALTER TABLE returns ADD COLUMN exchange_pid INTEGER")
            cur.execute("ALTER TABLE returns ADD COLUMN exchange_pname TEXT")
            cur.execute("ALTER TABLE returns ADD COLUMN exchange_qty INTEGER")
            cur.execute("ALTER TABLE returns ADD COLUMN exchange_price REAL")
            cur.execute("ALTER TABLE returns ADD COLUMN net_amount REAL")
            con.commit()
        except sqlite3.OperationalError:
            pass 
        finally:
            con.close()
            
    def upgrade_product_table(self):
        """Adds barcode column to product table if missing to prevent crashes"""
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("ALTER TABLE product ADD COLUMN barcode TEXT")
            con.commit()
        except sqlite3.OperationalError:
            pass # Column likely already exists
        finally:
            con.close()

    def generate_unique_invoice_no(self):
        try:
            now = datetime.datetime.now()
            import random
            return f"INV-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{random.randint(100, 999)}"
        except:
            return f"INV-{int(time.time())}"

    def get_current_datetime_parts(self):
        now = datetime.datetime.now()
        return {'date': now.strftime("%Y-%m-%d"), 'time': now.strftime("%H:%M:%S"), 'datetime': now, 'display_date': now.strftime("%d/%m/%Y"), 'display_time': now.strftime("%I:%M:%S %p")}

    def scale_font_size(self, base_size):
        return max(int(base_size * min(self.current_window_width / self.initial_window_width, 1.5) * 0.8), 8) 

    def on_window_resize(self, event):
        if event.widget == self.root:
            self.current_window_width = event.width
            self.current_window_height = event.height
            self.update_table_column_widths()

    def update_table_column_widths(self):
        if hasattr(self, 'ProductTable'):
            scale_factor = self.current_window_width / self.initial_window_width
            for col, width in [("pid", 50), ("Name", 150), ("retailprice", 80), ("Quantity", 60), ("Status", 80)]:
                self.ProductTable.column(col, width=int(width * scale_factor))
            if hasattr(self, 'CartTable'):
                for col, width in [("pid", 40), ("barcode", 70), ("Name", 140), ("Price", 70), ("Quantity", 50)]:
                    self.CartTable.column(col, width=int(width * scale_factor))

    # ================= QUICK ADD / BARCODE LOGIC =================
    def fetch_product_for_cart(self, event=None):
        search_val = self.var_quick_search.get().strip()
        if not search_val: return
        
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            # Search by pid OR barcode
            cur.execute("SELECT pid, barcode, Name, retailprice, Quantity FROM product WHERE (pid=? OR barcode=?) AND Status='Active'", (search_val, search_val))
            row = cur.fetchone()
            if row:
                self.var_quick_pid.set(row[0])
                self.var_quick_barcode.set(row[1] if row[1] else 'N/A')
                self.var_quick_name.set(row[2])
                self.var_quick_price.set(row[3])
                self.var_quick_stock.set(row[4])
                self.lbl_inStock.config(text=f"In Stock: {row[4]}")
                
                # Pre-fill quantity with 1 and focus so user can type and hit enter
                self.var_quick_qty.set("1")
                self.entry_quick_qty.focus()
                self.entry_quick_qty.selection_range(0, END)
            else:
                messagebox.showerror("Not Found", "Product not found or is currently inactive/out of stock", parent=self.root)
                self.clear_quick_add()
        except Exception as ex:
            messagebox.showerror("Error", f"Error querying database: {str(ex)}", parent=self.root)
        finally:
            con.close()

    def add_to_cart_from_quick(self, event=None):
        if self.var_quick_pid.get() == '':
            messagebox.showerror("Error", "Please fetch a valid product first by typing ID/Barcode and pressing Enter", parent=self.root)
            return
            
        try:
            qty = int(self.var_quick_qty.get())
            stock = int(self.var_quick_stock.get())
            price = float(self.var_quick_price.get())
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a valid number", parent=self.root)
            return

        pid = self.var_quick_pid.get()
        barcode = self.var_quick_barcode.get()
        pname = self.var_quick_name.get()
        total_price = price * qty

        # Check if item is already in the cart
        present = False
        index_ = 0
        old_qty = 0
        # cart_list structure: [pid, barcode, pname, price, qty, total_price, stock]
        for i, row in enumerate(self.cart_list):
            if pid == str(row[0]):
                present = True
                index_ = i
                old_qty = int(row[4])
                break

        if present:
            if qty == 0:
                self.cart_list.pop(index_)
                if not self.bill_generated:
                    self.update_product_quantity_in_db(pid, old_qty, "add")
            elif qty < 0:
                messagebox.showerror("Error", "Quantity cannot be negative", parent=self.root)
                return
            else:
                qty_diff = qty - old_qty
                if qty_diff > 0 and qty_diff > stock:
                    messagebox.showerror("Error", f"Not enough stock. Only {stock} available.", parent=self.root)
                    return
                self.cart_list[index_][4] = str(qty)
                self.cart_list[index_][5] = str(total_price)
                if not self.bill_generated:
                    if qty_diff > 0:
                        self.update_product_quantity_in_db(pid, qty_diff, "subtract")
                    elif qty_diff < 0:
                        self.update_product_quantity_in_db(pid, abs(qty_diff), "add")
        else:
            if qty <= 0:
                messagebox.showerror("Error", "Quantity must be > 0", parent=self.root)
                return
            if qty > stock:
                messagebox.showerror("Error", f"Not enough stock. Only {stock} available.", parent=self.root)
                return
            
            cart_data = [pid, barcode, pname, str(price), str(qty), str(total_price), str(stock)]
            self.cart_list.append(cart_data)
            if not self.bill_generated:
                self.update_product_quantity_in_db(pid, qty, "subtract")

        self.clear_quick_add()
        self.show_cart()
        self.show() # Refresh product table to show new stock visually
        
    def clear_quick_add(self):
        self.var_quick_search.set("")
        self.var_quick_barcode.set("")
        self.var_quick_name.set("")
        self.var_quick_price.set("")
        self.var_quick_qty.set("")
        self.var_quick_pid.set("")
        self.var_quick_stock.set("")
        self.lbl_inStock.config(text="In Stock: N/A")
        self.entry_quick_search.focus()

    #================ GREEN RETURN DASHBOARD FUNCTIONS ================
    def open_return_dashboard(self):
        # [Content unchanged. Retaining Return dashboard functionality]
        self.return_win = Toplevel(self.root)
        self.return_win.geometry("1200x750")
        self.return_win.title("Return & Exchange Dashboard")
        self.return_win.config(bg="#E8F5E9") 
        self.return_win.focus_force()

        self.var_search_invoice = StringVar()
        self.var_return_pid = StringVar()
        self.var_return_pname = StringVar()
        self.var_return_purchased_qty = StringVar()
        self.var_return_price = StringVar()
        self.var_return_qty = StringVar()
        
        self.var_exc_search = StringVar() 
        self.var_exc_pid = StringVar()
        self.var_exc_pname = StringVar()
        self.var_exc_price = StringVar()
        self.var_exc_qty = StringVar()
        self.var_exc_stock = StringVar()
        
        self.var_net_amount = StringVar(value="0.00")
        self.var_return_reason = StringVar()

        header_frame = Frame(self.return_win, bg="#2E7D32")
        header_frame.pack(side=TOP, fill=X)
        Label(header_frame, text="Returns & Exchanges", font=("bahnschrift light semicondensed", 20, "bold"), bg="#2E7D32", fg="white", pady=10).pack(side=LEFT, padx=20)
        
        self.lbl_return_clock = Label(header_frame, font=("Aptos Display", 12, "bold"), bg="#2E7D32", fg="#A5D6A7")
        self.lbl_return_clock.pack(side=RIGHT, padx=20)
        self.update_return_clock()

        body_frame = Frame(self.return_win, bg="#E8F5E9")
        body_frame.pack(fill=BOTH, expand=1, padx=10, pady=10)

        top_frame = Frame(body_frame, bg="#E8F5E9")
        top_frame.pack(fill=X, pady=(0, 10))
        
        search_frame = LabelFrame(top_frame, text="1. Select Invoice", font=("Aptos Display", 11, "bold"), bg="white", fg="#1B5E20", bd=2)
        search_frame.pack(side=LEFT, fill=X, expand=1, padx=(0, 5))
        Label(search_frame, text="Disclaimer: Only valid invoices mapped to existing records can be searched.", font=("Aptos Display", 9, "italic"), bg="white", fg="gray").pack(anchor=W, padx=5, pady=(2, 5))
        
        sf_inner = Frame(search_frame, bg="white")
        sf_inner.pack(fill=X, padx=5, pady=5)
        self.combo_invoice = ttk.Combobox(sf_inner, textvariable=self.var_search_invoice, font=("Aptos Display", 11), state='normal')
        self.combo_invoice.pack(side=LEFT, fill=X, expand=1, padx=(0, 10))
        self.fetch_all_invoices()
        Button(sf_inner, text="Load Invoice Items", command=self.search_invoice_for_return, font=("Aptos Display", 10, "bold"), bg="#4CAF50", fg="white", cursor="hand2").pack(side=LEFT)

        tracker_frame = Frame(top_frame, bg="#E8F5E9")
        tracker_frame.pack(side=RIGHT, fill=Y)
        
        self.lbl_total_returns = Label(tracker_frame, text="Total Returns:\n0", font=("Aptos Display", 12, "bold"), bg="#1B5E20", fg="white", relief=RAISED, width=15)
        self.lbl_total_returns.pack(side=LEFT, fill=Y, padx=(5,0))
        self.lbl_total_refunds = Label(tracker_frame, text="Total Cash Given Back:\nRs. 0.00", font=("Aptos Display", 12, "bold"), bg="#388E3C", fg="white", relief=RAISED, width=20)
        self.lbl_total_refunds.pack(side=LEFT, fill=Y, padx=(5,0))
        self.lbl_total_collected = Label(tracker_frame, text="Total Cash Collected:\nRs. 0.00", font=("Aptos Display", 12, "bold"), bg="#D35400", fg="white", relief=RAISED, width=20)
        self.lbl_total_collected.pack(side=LEFT, fill=Y, padx=(5,0))

        mid_frame = Frame(body_frame, bg="#E8F5E9")
        mid_frame.pack(fill=BOTH, expand=1, pady=(0, 10))
        mid_frame.columnconfigure(0, weight=1)
        mid_frame.columnconfigure(1, weight=1)
        mid_frame.columnconfigure(2, weight=1)

        inv_table_frame = LabelFrame(mid_frame, text="2. Select Item to Return", font=("Aptos Display", 11, "bold"), bg="white", fg="#1B5E20")
        inv_table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        scroll_y_inv = Scrollbar(inv_table_frame, orient=VERTICAL)
        self.InvoiceItemTable = ttk.Treeview(inv_table_frame, columns=("pid", "name", "qty", "price"), yscrollcommand=scroll_y_inv.set)
        scroll_y_inv.pack(side=RIGHT, fill=Y)
        scroll_y_inv.config(command=self.InvoiceItemTable.yview)
        
        self.InvoiceItemTable.heading("pid", text="ID")
        self.InvoiceItemTable.heading("name", text="Product Name")
        self.InvoiceItemTable.heading("qty", text="Qty")
        self.InvoiceItemTable.heading("price", text="Price")
        self.InvoiceItemTable["show"] = "headings"
        self.InvoiceItemTable.column("pid", width=40)
        self.InvoiceItemTable.column("name", width=120)
        self.InvoiceItemTable.column("qty", width=40)
        self.InvoiceItemTable.column("price", width=60)
        self.InvoiceItemTable.pack(fill=BOTH, expand=1, padx=5, pady=5)
        self.InvoiceItemTable.bind("<ButtonRelease-1>", self.select_return_item)

        ret_form_frame = LabelFrame(mid_frame, text="Return Details", font=("Aptos Display", 11, "bold"), bg="white", fg="#C0392B")
        ret_form_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        Label(ret_form_frame, text="Returning:", bg="white", font=("Aptos Display", 10)).grid(row=0, column=0, sticky=W, padx=5, pady=5)
        Entry(ret_form_frame, textvariable=self.var_return_pname, state='readonly', bg="#F2F4F4").grid(row=0, column=1, sticky=EW, padx=5)
        Label(ret_form_frame, text="Bought / Price:", bg="white", font=("Aptos Display", 10)).grid(row=1, column=0, sticky=W, padx=5, pady=5)
        Frame1 = Frame(ret_form_frame, bg="white")
        Frame1.grid(row=1, column=1, sticky=EW)
        Entry(Frame1, textvariable=self.var_return_purchased_qty, state='readonly', bg="#F2F4F4", width=5).pack(side=LEFT, padx=(5,2))
        Entry(Frame1, textvariable=self.var_return_price, state='readonly', bg="#F2F4F4", width=8).pack(side=LEFT)
        Label(ret_form_frame, text="Return Qty:", bg="white", font=("Aptos Display", 10, "bold")).grid(row=2, column=0, sticky=W, padx=5, pady=5)
        Entry(ret_form_frame, textvariable=self.var_return_qty, bg="white", highlightthickness=1).grid(row=2, column=1, sticky=EW, padx=5)
        self.var_return_qty.trace('w', self.calculate_net_amount)
        Label(ret_form_frame, text="Reason:", bg="white", font=("Aptos Display", 10)).grid(row=3, column=0, sticky=W, padx=5, pady=5)
        ttk.Combobox(ret_form_frame, textvariable=self.var_return_reason, values=("Defective", "Wrong Item", "Changed Mind", "Other")).grid(row=3, column=1, sticky=EW, padx=5)

        exc_form_frame = LabelFrame(mid_frame, text="3. Exchange Product (Optional)", font=("Aptos Display", 11, "bold"), bg="white", fg="#2980B9")
        exc_form_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        Label(exc_form_frame, text="Search (ID/Name/Barcode):", bg="white", font=("Aptos Display", 10)).grid(row=0, column=0, sticky=W, padx=5, pady=5)
        search_frm = Frame(exc_form_frame, bg="white")
        search_frm.grid(row=0, column=1, sticky=EW, padx=5)
        Entry(search_frm, textvariable=self.var_exc_search, font=("Aptos Display", 10), width=15).pack(side=LEFT, fill=X, expand=1, padx=(0,2))
        Button(search_frm, text="Find", command=self.find_exchange_product, bg="#3498DB", fg="white", cursor="hand2", font=("Aptos Display", 9)).pack(side=LEFT)

        Label(exc_form_frame, text="Select Product:", bg="white", font=("Aptos Display", 10)).grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.combo_exchange = ttk.Combobox(exc_form_frame, font=("Aptos Display", 10))
        self.combo_exchange.grid(row=1, column=1, sticky=EW, padx=5)
        self.fetch_exchange_products()
        self.combo_exchange.bind("<<ComboboxSelected>>", self.select_exchange_product)

        Label(exc_form_frame, text="Price / Stock:", bg="white", font=("Aptos Display", 10)).grid(row=2, column=0, sticky=W, padx=5, pady=5)
        Frame2 = Frame(exc_form_frame, bg="white")
        Frame2.grid(row=2, column=1, sticky=EW)
        Entry(Frame2, textvariable=self.var_exc_price, state='readonly', bg="#F2F4F4", width=8).pack(side=LEFT, padx=(5,2))
        Entry(Frame2, textvariable=self.var_exc_stock, state='readonly', bg="#F2F4F4", width=5).pack(side=LEFT)

        Label(exc_form_frame, text="Exchange Qty:", bg="white", font=("Aptos Display", 10, "bold")).grid(row=3, column=0, sticky=W, padx=5, pady=5)
        Entry(exc_form_frame, textvariable=self.var_exc_qty, bg="white", highlightthickness=1).grid(row=3, column=1, sticky=EW, padx=5)
        self.var_exc_qty.trace('w', self.calculate_net_amount)

        action_frame = Frame(exc_form_frame, bg="#E8F5E9", bd=1, relief=SOLID)
        action_frame.grid(row=4, column=0, columnspan=2, sticky=EW, pady=10, padx=5)
        
        Button(action_frame, text="Clear Form", command=self.clear_return_form, font=("Aptos Display", 9, "bold"), bg="#F39C12", fg="white", cursor="hand2").pack(side=LEFT, padx=5, pady=5)
        Label(action_frame, text="Payment / Refund:", bg="#E8F5E9", font=("Aptos Display", 10, "bold")).pack(side=LEFT, padx=5)
        self.lbl_net_display = Label(action_frame, text="Rs. 0.00", bg="#E8F5E9", fg="#27AE60", font=("Aptos Display", 12, "bold"))
        self.lbl_net_display.pack(side=RIGHT, padx=5, pady=5)

        Button(exc_form_frame, text="Process Return & Exchange", command=self.process_return_action, font=("Aptos Display", 11, "bold"), bg="#16A085", fg="white", cursor="hand2").grid(row=5, column=0, columnspan=2, pady=5, sticky=EW, padx=5)

        bot_frame = LabelFrame(body_frame, text="Returns & Exchanges History", font=("Aptos Display", 11, "bold"), bg="white", fg="#1B5E20")
        bot_frame.pack(fill=BOTH, expand=1)

        btn_frame = Frame(bot_frame, bg="white")
        btn_frame.pack(fill=X, padx=5, pady=5)
        Button(btn_frame, text="Download Excel (CSV)", command=self.export_excel, font=("Aptos Display", 9, "bold"), bg="#27AE60", fg="white", cursor="hand2").pack(side=RIGHT, padx=5)
        Button(btn_frame, text="Download PDF", command=self.export_pdf, font=("Aptos Display", 9, "bold"), bg="#E74C3C", fg="white", cursor="hand2").pack(side=RIGHT, padx=5)

        scroll_y_ret = Scrollbar(bot_frame, orient=VERTICAL)
        self.ReturnTrackerTable = ttk.Treeview(bot_frame, columns=("ret_id", "inv_no", "ret_pname", "ret_qty", "exc_pname", "exc_qty", "net_amt", "date"), yscrollcommand=scroll_y_ret.set)
        scroll_y_ret.pack(side=RIGHT, fill=Y)
        scroll_y_ret.config(command=self.ReturnTrackerTable.yview)

        self.ReturnTrackerTable.heading("ret_id", text="ID")
        self.ReturnTrackerTable.heading("inv_no", text="Invoice")
        self.ReturnTrackerTable.heading("ret_pname", text="Returned Product")
        self.ReturnTrackerTable.heading("ret_qty", text="Ret Qty")
        self.ReturnTrackerTable.heading("exc_pname", text="Exchanged Product")
        self.ReturnTrackerTable.heading("exc_qty", text="Exc Qty")
        self.ReturnTrackerTable.heading("net_amt", text="Cash Difference")
        self.ReturnTrackerTable.heading("date", text="Date")
        self.ReturnTrackerTable["show"] = "headings"
        self.ReturnTrackerTable.column("ret_id", width=30)
        self.ReturnTrackerTable.column("ret_qty", width=50)
        self.ReturnTrackerTable.column("exc_qty", width=50)
        self.ReturnTrackerTable.column("net_amt", width=120)
        self.ReturnTrackerTable.pack(fill=BOTH, expand=1, padx=5, pady=(0, 5))

        self.fetch_returns_history()

    def update_return_clock(self):
        if hasattr(self, 'return_win') and self.return_win.winfo_exists():
            now = datetime.datetime.now()
            self.lbl_return_clock.config(text=now.strftime("Date: %d/%m/%Y   Time: %I:%M:%S %p"))
            self.return_win.after(1000, self.update_return_clock)

    def fetch_all_invoices(self):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT invoice_no FROM invoices ORDER BY invoice_id DESC")
            rows = cur.fetchall()
            self.combo_invoice['values'] = [r[0] for r in rows]
        except: pass
        finally: con.close()

    def fetch_exchange_products(self):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT pid, Name FROM product WHERE Status='Active' AND Quantity > 0")
            rows = cur.fetchall()
            self.combo_exchange['values'] = [f"{r[0]} | {r[1]}" for r in rows]
        except: pass
        finally: con.close()

    def find_exchange_product(self):
        search_val = self.var_exc_search.get().strip()
        if not search_val: 
            return messagebox.showerror("Error", "Enter Barcode, ID, or Name to search", parent=self.return_win)
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT pid, Name FROM product WHERE (barcode=? OR pid=? OR Name LIKE ?) AND Status='Active' AND Quantity > 0", (search_val, search_val, f"%{search_val}%"))
            rows = cur.fetchall()
            if rows:
                self.combo_exchange['values'] = [f"{r[0]} | {r[1]}" for r in rows]
                self.combo_exchange.current(0)
                self.select_exchange_product(None)
            else:
                messagebox.showinfo("Not Found", "No active product matching that ID, Name, or Barcode was found in stock.", parent=self.return_win)
        except Exception as ex:
            messagebox.showerror("Error", f"Error querying database: {str(ex)}", parent=self.return_win)
        finally: 
            con.close()

    def search_invoice_for_return(self):
        invoice_no = self.var_search_invoice.get().strip()
        if not invoice_no: return messagebox.showerror("Error", "Please select or enter an Invoice Number.", parent=self.return_win)
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT invoice_id FROM invoices WHERE invoice_no=?", (invoice_no,))
            inv_record = cur.fetchone()
            if not inv_record: return messagebox.showerror("Error", "Invoice not found.", parent=self.return_win)
            inv_id = inv_record[0]
            cur.execute("SELECT product_id, product_name, quantity, price FROM invoice_items WHERE invoice_id=?", (inv_id,))
            rows = cur.fetchall()
            self.InvoiceItemTable.delete(*self.InvoiceItemTable.get_children())
            for row in rows: self.InvoiceItemTable.insert('', END, values=row)
        except Exception as ex: messagebox.showerror("Error", f"Error: {str(ex)}", parent=self.return_win)
        finally: con.close()

    def select_return_item(self, ev):
        f = self.InvoiceItemTable.focus()
        content = self.InvoiceItemTable.item(f)
        row = content['values']
        if row:
            self.var_return_pid.set(row[0])
            self.var_return_pname.set(row[1])
            self.var_return_purchased_qty.set(row[2])
            self.var_return_price.set(row[3])
            self.var_return_qty.set("1")
            self.calculate_net_amount()

    def select_exchange_product(self, ev):
        selection = self.combo_exchange.get()
        if not selection: return
        pid = selection.split(" | ")[0]
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT Name, retailprice, Quantity FROM product WHERE pid=?", (pid,))
            row = cur.fetchone()
            if row:
                self.var_exc_pid.set(pid)
                self.var_exc_pname.set(row[0])
                self.var_exc_price.set(row[1])
                self.var_exc_stock.set(row[2])
                self.var_exc_qty.set("1")
                self.calculate_net_amount()
        except: pass
        finally: con.close()

    def calculate_net_amount(self, *args):
        try:
            ret_qty = int(self.var_return_qty.get()) if self.var_return_qty.get() else 0
            ret_price = float(self.var_return_price.get()) if self.var_return_price.get() else 0.0
            ret_total = ret_qty * ret_price
            
            exc_qty = int(self.var_exc_qty.get()) if self.var_exc_qty.get() else 0
            exc_price = float(self.var_exc_price.get()) if self.var_exc_price.get() else 0.0
            exc_total = exc_qty * exc_price
            
            net = ret_total - exc_total
            self.var_net_amount.set(str(net))
            
            if net > 0: self.lbl_net_display.config(text=f"Give Customer: Rs. {abs(net):.2f}", fg="#27AE60")
            elif net < 0: self.lbl_net_display.config(text=f"Customer Pays Store: Rs. {abs(net):.2f}", fg="#C0392B")
            else: self.lbl_net_display.config(text="No Cash Exchange Needed", fg="gray")
        except: pass

    def clear_return_form(self):
        self.var_search_invoice.set("")
        self.var_return_pid.set("")
        self.var_return_pname.set("")
        self.var_return_purchased_qty.set("")
        self.var_return_price.set("")
        self.var_return_qty.set("")
        self.var_return_reason.set("")
        self.var_exc_search.set("")
        self.var_exc_pid.set("")
        self.var_exc_pname.set("")
        self.var_exc_price.set("")
        self.var_exc_qty.set("")
        self.var_exc_stock.set("")
        self.var_net_amount.set("0.00")
        self.combo_exchange.set("")
        self.lbl_net_display.config(text="Rs. 0.00", fg="#27AE60")
        self.InvoiceItemTable.delete(*self.InvoiceItemTable.get_children())

    def process_return_action(self):
        if not self.var_return_pid.get(): return messagebox.showerror("Error", "Please select a product from the invoice list.", parent=self.return_win)
        try:
            ret_qty = int(self.var_return_qty.get())
            purchased_qty = int(self.var_return_purchased_qty.get())
            if ret_qty <= 0 or ret_qty > purchased_qty: return messagebox.showerror("Error", "Invalid return quantity.", parent=self.return_win)
            exc_qty = int(self.var_exc_qty.get()) if self.var_exc_qty.get() else 0
            exc_stock = int(self.var_exc_stock.get()) if self.var_exc_stock.get() else 0
            if exc_qty > exc_stock: return messagebox.showerror("Error", "Not enough stock for exchange item.", parent=self.return_win)
        except ValueError: return messagebox.showerror("Error", "Quantities must be valid numbers.", parent=self.return_win)

        invoice_no = self.var_search_invoice.get()
        r_pid, r_pname, r_price = self.var_return_pid.get(), self.var_return_pname.get(), float(self.var_return_price.get())
        e_pid = self.var_exc_pid.get() if exc_qty > 0 else None
        e_pname = self.var_exc_pname.get() if exc_qty > 0 else "N/A"
        e_price = float(self.var_exc_price.get()) if exc_qty > 0 else 0.0
        reason = self.var_return_reason.get()
        net_amt = (r_price * ret_qty) - (e_price * exc_qty)

        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("UPDATE product SET Quantity = Quantity + ?, Status='Active' WHERE pid = ?", (ret_qty, r_pid))
            if e_pid and exc_qty > 0:
                cur.execute("UPDATE product SET Quantity = Quantity - ? WHERE pid = ?", (exc_qty, e_pid))
                cur.execute("SELECT Quantity FROM product WHERE pid=?", (e_pid,))
                if cur.fetchone()[0] <= 0: cur.execute("UPDATE product SET Status='Inactive' WHERE pid=?", (e_pid,))
            cur.execute('''INSERT INTO returns (invoice_no, product_id, product_name, qty_returned, refund_amount, exchange_pid, exchange_pname, exchange_qty, exchange_price, net_amount, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (invoice_no, r_pid, r_pname, ret_qty, (r_price*ret_qty), e_pid, e_pname, exc_qty, e_price, net_amt, reason))
            con.commit()
            
            msg = f"Processed Successfully!\nSettlement: "
            if net_amt > 0: msg += f"Give Customer Rs. {abs(net_amt):.2f}"
            elif net_amt < 0: msg += f"Collect Rs. {abs(net_amt):.2f} from Customer"
            else: msg += "No Cash Exchange Needed"

            messagebox.showinfo("Success", msg, parent=self.return_win)
            self.clear_return_form() 
            self.fetch_returns_history()
            self.show() 
        except Exception as ex:
            con.rollback()
            messagebox.showerror("Error", f"Failed to process: {str(ex)}", parent=self.return_win)
        finally: con.close()

    def fetch_returns_history(self):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT return_id, invoice_no, product_name, qty_returned, exchange_pname, exchange_qty, net_amount, date(return_date) FROM returns ORDER BY return_id DESC")
            rows = cur.fetchall()
            self.ReturnTrackerTable.delete(*self.ReturnTrackerTable.get_children())
            total_returns = len(rows)
            total_given_back = 0.0
            total_collected = 0.0
            
            for row in rows:
                formatted_row = list(row)
                net = float(row[6]) if row[6] else 0.0
                if net > 0: 
                    total_given_back += net 
                    formatted_row[6] = f"Give: Rs. {net:.2f}"
                elif net < 0:
                    total_collected += abs(net)
                    formatted_row[6] = f"Collect: Rs. {abs(net):.2f}"
                else:
                    formatted_row[6] = "Even (Rs. 0.00)"
                self.ReturnTrackerTable.insert('', END, values=formatted_row)
                
            self.lbl_total_returns.config(text=f"Total Returns:\n{total_returns}")
            self.lbl_total_refunds.config(text=f"Total Cash Given Back:\nRs. {total_given_back:.2f}")
            self.lbl_total_collected.config(text=f"Total Cash Collected:\nRs. {total_collected:.2f}")
        except Exception as ex: pass
        finally: con.close()

    def export_excel(self):
        try:
            rows = self.ReturnTrackerTable.get_children()
            if len(rows) == 0: return messagebox.showerror("Error", "No records to export.", parent=self.return_win)
            filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], title="Save returns to Excel(CSV)")
            if filepath:
                with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["ID", "Invoice", "Returned Product", "Ret Qty", "Exchanged Product", "Exc Qty", "Cash Difference", "Date"])
                    for row_id in rows: writer.writerow(self.ReturnTrackerTable.item(row_id)['values'])
                messagebox.showinfo("Success", f"Data exported successfully to\n{filepath}", parent=self.return_win)
        except Exception as ex: messagebox.showerror("Error", f"Failed to export: {str(ex)}", parent=self.return_win)

    def export_pdf(self):
        if not HAS_FPDF: return messagebox.showwarning("Missing Library", "PDF Export requires the 'fpdf' library.\nPlease open your terminal/command prompt and run:\n\npip install fpdf", parent=self.return_win)
        try:
            rows = self.ReturnTrackerTable.get_children()
            if len(rows) == 0: return messagebox.showerror("Error", "No records to export.", parent=self.return_win)
            filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], title="Save returns to PDF")
            if filepath:
                pdf = FPDF(orientation='L', unit='mm', format='A4') 
                pdf.add_page()
                pdf.set_font("Arial", size=16, style="B")
                pdf.cell(0, 10, "Returns and Exchanges History Report", ln=True, align="C")
                pdf.set_font("Arial", size=10)
                pdf.cell(0, 10, f"Generated on: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align="C")
                pdf.ln(5)
                pdf.set_font("Arial", size=10, style="B")
                pdf.cell(15, 10, "ID", border=1)
                pdf.cell(45, 10, "Invoice No", border=1)
                pdf.cell(60, 10, "Returned Product", border=1)
                pdf.cell(20, 10, "Ret Qty", border=1)
                pdf.cell(60, 10, "Exchange Product", border=1)
                pdf.cell(20, 10, "Exc Qty", border=1)
                pdf.cell(35, 10, "Cash Diff", border=1)
                pdf.ln()
                pdf.set_font("Arial", size=9)
                for row_id in rows:
                    row_data = self.ReturnTrackerTable.item(row_id)['values']
                    pdf.cell(15, 10, str(row_data[0]), border=1)
                    pdf.cell(45, 10, str(row_data[1]), border=1)
                    pdf.cell(60, 10, str(row_data[2])[:30], border=1) 
                    pdf.cell(20, 10, str(row_data[3]), border=1)
                    pdf.cell(60, 10, str(row_data[4])[:30] if row_data[4] != 'None' else "N/A", border=1)
                    pdf.cell(20, 10, str(row_data[5]) if row_data[5] != 'None' else "0", border=1)
                    pdf.cell(35, 10, str(row_data[6]), border=1)
                    pdf.ln()
                pdf.output(filepath)
                messagebox.showinfo("Success", f"PDF saved successfully to\n{filepath}", parent=self.return_win)
        except Exception as ex: messagebox.showerror("Error", f"Failed to generate PDF: {str(ex)}", parent=self.return_win)

    #================All Other Functions================
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to Exit?", parent=self.root):
            self.root.destroy()

    def update_clock(self):
        now = datetime.datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%I:%M:%S")
        self.lbl_clock.config(text=f"Welcome to Smart POS & Billing System     Date: {date_str}     Time: {time_str}")
        self.root.after(1000, self.update_clock)

    def validate_contact(self, event=None):
        current_text = self.var_contact.get()
        digits_only = re.sub(r'\D', '', current_text)
        if len(digits_only) > 10: digits_only = digits_only[:10]
        self.var_contact.set(digits_only)
        if len(digits_only) == 10: self.contact_entry.config(bg="#DCFCE7") 
        else: self.contact_entry.config(bg="white")
        return True

    def format_contact(self, *args):
        current_value = self.var_contact.get()
        if len(current_value) == 10 and current_value.isdigit(): return "+92" + current_value
        return current_value

    def get_contact_for_bill(self):
        contact = self.var_contact.get().strip()
        if len(contact) == 10 and contact.isdigit(): return "+92" + contact
        elif contact: return contact
        return "N/A" 

    def show_suggestions(self, event):
        search_text = self.var_search.get()
        if self.suggestion_window: self.suggestion_window.destroy()
        if not search_text: return
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT Name FROM product WHERE Name LIKE ? AND Status='Active' LIMIT 5", (f'%{search_text}%',))
            suggestions = cur.fetchall()
            if suggestions:
                self.suggestion_window = Toplevel(self.root)
                self.suggestion_window.wm_overrideredirect(True)
                x = event.widget.winfo_rootx()
                y = event.widget.winfo_rooty() + event.widget.winfo_height()
                self.suggestion_window.geometry(f"+{x}+{y}")
                self.suggestion_window.configure(bg='white', bd=1, relief=SOLID)
                for i, suggestion in enumerate(suggestions):
                    suggestion_text = suggestion[0]
                    lbl = Label(self.suggestion_window, text=suggestion_text, font=("Aptos Display", 10), bg='white', anchor='w', padx=5, pady=2)
                    lbl.pack(fill=X)
                    lbl.bind('<Button-1>', lambda e, text=suggestion_text: self.set_search_text(text))
                    lbl.bind('<Enter>', lambda e, lbl=lbl: lbl.config(bg='#FFF5F5')) 
                    lbl.bind('<Leave>', lambda e, lbl=lbl: lbl.config(bg='white'))
        except Exception: pass
        finally: con.close()

    def set_search_text(self, text):
        self.var_search.set(text)
        if self.suggestion_window:
            self.suggestion_window.destroy()
            self.suggestion_window = None
        self.search_by_name()

    def show(self):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT pid, Name, retailprice, Quantity, Status FROM product WHERE Status='Active'")
            rows = cur.fetchall()
            self.ProductTable.delete(*self.ProductTable.get_children())
            for row in rows: self.ProductTable.insert('', END, values=row)
        except Exception as ex: messagebox.showerror("Error", f"Error due to {str(ex)}", parent=self.root)
        finally: con.close()

    def search_by_name(self):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            if self.var_search.get() == "": messagebox.showerror("Error", "Please enter product name to search", parent=self.root)
            else:
                cur.execute("SELECT pid, Name, retailprice, Quantity, Status FROM product WHERE Name LIKE ? AND Status='Active'", (f'%{self.var_search.get()}%',))
                rows = cur.fetchall()
                if len(rows) != 0:
                    self.ProductTable.delete(*self.ProductTable.get_children())
                    for row in rows: self.ProductTable.insert('', END, values=row)
                else: messagebox.showerror("Error", "No record found!!!", parent=self.root)
        except Exception as ex: messagebox.showerror("Error", f"Error due to {str(ex)}", parent=self.root)
        finally: con.close()

    def search_by_id(self):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            if self.var_search_id.get() == "": messagebox.showerror("Error", "Please enter product ID to search", parent=self.root)
            else:
                cur.execute("SELECT pid, Name, retailprice, Quantity, Status FROM product WHERE pid=? AND Status='Active'", (self.var_search_id.get(),))
                rows = cur.fetchall()
                if len(rows) != 0:
                    self.ProductTable.delete(*self.ProductTable.get_children())
                    for row in rows: self.ProductTable.insert('', END, values=row)
                else: messagebox.showerror("Error", "No record found!!!", parent=self.root)
        except Exception as ex: messagebox.showerror("Error", f"Error due to {str(ex)}", parent=self.root)
        finally: con.close()

    def search_by_barcode(self):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            if self.var_search_barcode.get() == "": messagebox.showerror("Error", "Please enter product barcode to search", parent=self.root)
            else:
                cur.execute("SELECT pid, Name, retailprice, Quantity, Status FROM product WHERE barcode=? AND Status='Active'", (self.var_search_barcode.get(),))
                rows = cur.fetchall()
                if len(rows) != 0:
                    self.ProductTable.delete(*self.ProductTable.get_children())
                    for row in rows: self.ProductTable.insert('', END, values=row)
                else: messagebox.showerror("Error", "No record found!!!", parent=self.root)
        except Exception as ex: messagebox.showerror("Error", f"Error querying database: {str(ex)}", parent=self.root)
        finally: con.close()

    def get_data(self, ev):
        """Clicking left table fills quick-add input line"""
        f = self.ProductTable.focus()
        content = self.ProductTable.item(f)
        row = content['values']
        if row:
            self.var_quick_pid.set(row[0])
            self.var_quick_name.set(row[1])
            self.var_quick_price.set(row[2])
            self.var_quick_stock.set(row[3])
            self.lbl_inStock.config(text=f"In Stock: {row[3]}")
            self.var_quick_qty.set('1')
            self.var_quick_search.set(row[0]) # Put ID in search box
            
            con = sqlite3.connect(database=r'Possystem.db')
            cur = con.cursor()
            try:
                cur.execute("SELECT barcode FROM product WHERE pid=?", (row[0],))
                res = cur.fetchone()
                self.var_quick_barcode.set(res[0] if res and res[0] else 'N/A')
            except:
                self.var_quick_barcode.set('N/A')
            finally:
                con.close()
                
            self.entry_quick_qty.focus()
            self.entry_quick_qty.selection_range(0, END)

    def get_data_cart(self, ev):
        """Clicking cart table fills quick-add input line so you can update qty"""
        f = self.CartTable.focus()
        content = self.CartTable.item(f)
        row = content['values']
        if row:
            self.var_quick_pid.set(row[0])
            self.var_quick_barcode.set(row[1])
            self.var_quick_name.set(row[2])
            price_str = row[3].replace('Rs.', '').strip()
            self.var_quick_price.set(price_str)
            self.var_quick_qty.set(row[4])
            self.var_quick_search.set(row[0])
            for cart_item in self.cart_list:
                if str(cart_item[0]) == str(row[0]):
                    self.var_quick_stock.set(cart_item[6]) # Stock is index 6
                    self.lbl_inStock.config(text=f"In Stock: {cart_item[6]}")
                    break
            self.entry_quick_qty.focus()
            self.entry_quick_qty.selection_range(0, END)

    def update_product_quantity_in_db(self, pid, qty, operation):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            if operation == "subtract": cur.execute("UPDATE product SET Quantity = Quantity - ? WHERE pid = ?", (qty, pid))
            elif operation == "add": cur.execute("UPDATE product SET Quantity = Quantity + ? WHERE pid = ?", (qty, pid))
            
            cur.execute("SELECT Quantity FROM product WHERE pid=?", (pid,))
            result = cur.fetchone()
            if result:
                new_qty = result[0]
                if new_qty <= 0: cur.execute("UPDATE product SET Status='Inactive' WHERE pid=?", (pid,))
                elif new_qty > 0: cur.execute("UPDATE product SET Status='Active' WHERE pid=?", (pid,))
            con.commit()
        except Exception as ex:
            messagebox.showerror("Error", f"Error updating database: {str(ex)}", parent=self.root)
            con.rollback()
        finally: con.close()

    def bill_updates(self):
        self.bill_amnt = 0 
        self.net_pay = 0 
        self.tax_amount = 0
        for row in self.cart_list:
            try: self.bill_amnt += float(row[5]) # index 5 is total_price
            except: continue

        self.tax_amount = (self.bill_amnt * self.tax_rate) / 100
        self.net_pay = self.bill_amnt + self.tax_amount
        
        self.lbl_amnt.config(text=f'Subtotal\nRs. {self.bill_amnt:.2f}')
        self.lbl_tax.config(text=f'Tax ({self.tax_rate}%)\nRs. {self.tax_amount:.2f}')
        self.lbl_net_pay.config(text=f'Total Amount\nRs. {self.net_pay:.2f}')
        self.CartTitle.config(text=f"Cart \t Total Products: [{len(self.cart_list)}]")
        self.calculate_change()

    def show_cart(self):
        try:
            self.CartTable.delete(*self.CartTable.get_children())
            for row in self.cart_list:
                # cart_list = [pid, barcode, pname, price, qty, total_price, stock]
                self.CartTable.insert('', END, values=(row[0], row[1], row[2], f"Rs.{float(row[3]):.2f}", row[4]))
            self.bill_updates()
        except Exception as ex: messagebox.showerror("Error", f"Error due to {str(ex)}", parent=self.root)

    def calculate_change(self, *args):
        try:
            cash_str = self.var_cash.get().strip()
            cash = float(cash_str) if cash_str else 0.0
            total = self.net_pay if hasattr(self, 'net_pay') else 0.0
            change = cash - total
            self.var_change.set(f"{change:.2f}")
        except: self.var_change.set("0.00")

    def generate_bill(self):
        self.bill_generated = True
        customer_name = self.var_cname.get().strip() or "Guest"
        contact = self.var_contact.get().strip()
        if contact and (len(contact) != 10 or not contact.isdigit()):
            messagebox.showerror("Error", "Contact number must be exactly 10 digits\nExample: 3001234567\nOr leave it empty", parent=self.root)
            self.contact_entry.focus()
            self.bill_generated = False
            return
        if len(self.cart_list) == 0:
            messagebox.showerror("Error", "Please add product to the cart", parent=self.root)
            self.bill_generated = False
            return

        cash_str = self.var_cash.get().strip()
        try: cash = float(cash_str) if cash_str else 0.0
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid cash amount", parent=self.root)
            self.bill_generated = False
            return

        total = self.net_pay
        if cash < total:
            messagebox.showerror("Error", f"Cash amount (Rs.{cash:.2f}) is less than total (Rs.{total:.2f})\nPlease enter sufficient cash.", parent=self.root)
            self.bill_generated = False
            return

        try:
            invoice_no = self.generate_unique_invoice_no()
            datetime_parts = self.get_current_datetime_parts()
            formatted_contact = self.get_contact_for_bill()

            if self.save_invoice_to_db(invoice_no, customer_name, formatted_contact, datetime_parts):
                self.bill_updates() 
                self.display_bill(invoice_no, customer_name, formatted_contact, datetime_parts, cash)
                msg = f"Bill generated successfully\nInvoice No.: {invoice_no}\nCustomer: {customer_name}\n"
                if contact: msg += f"Contact: {formatted_contact}\n"
                msg += f"Date: {datetime_parts['display_date']}\nTime: {datetime_parts['display_time']}\nCash: Rs.{cash:.2f}\nChange: Rs.{cash - total:.2f}\nSaved to database"
                messagebox.showinfo("Success", msg, parent=self.root)
            else:
                messagebox.showerror("Error", "Failed to save invoice to database", parent=self.root)
                self.bill_generated = False

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate bill: {str(e)}", parent=self.root)
            self.bill_generated = False

    def save_invoice_to_db(self, invoice_no, customer_name, customer_contact, datetime_parts):
        try:
            con = sqlite3.connect(database=r'Possystem.db')
            cur = con.cursor()
            cur.execute('''INSERT INTO invoices (invoice_no, total_amount, tax_amount, subtotal_amount, customer_name, customer_contact, invoice_date, invoice_time, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (invoice_no, self.net_pay, self.tax_amount, self.bill_amnt, customer_name, customer_contact if customer_contact != "N/A" else None, datetime_parts['date'], datetime_parts['time'], datetime_parts['datetime']))
            invoice_id = cur.lastrowid
            
            for item in self.cart_list:
                # item format: [pid, barcode, pname, price, qty, total_price, stock]
                total_price = float(item[5])
                qty = int(item[4])
                price_per_item = float(item[3])
                cur.execute('''INSERT INTO invoice_items (invoice_id, product_id, product_name, quantity, price, total) VALUES (?, ?, ?, ?, ?, ?)''', (invoice_id, item[0], item[2], qty, price_per_item, total_price))
            con.commit()
            return True
        except Exception:
            if 'con' in locals(): con.rollback()
            return False
        finally:
            if 'con' in locals(): con.close()

    def display_bill(self, invoice_no, customer_name, customer_contact, datetime_parts, cash):
        self.txt_bill_area.delete('1.0', END)
        bill_header = f"""
{'='*60}
{'INVOICE'.center(60)}
{'='*60}
Customer Name  : {customer_name if customer_name else 'Guest'}
Contact No.    : {customer_contact}
Invoice No.    : {invoice_no}
Date           : {datetime_parts['display_date']}
Time           : {datetime_parts['display_time']}
{'='*60}
{'PRODUCT NAME'.ljust(30)}{'QTY'.rjust(8)}{'PRICE'.rjust(12)}{'TOTAL'.rjust(12)}
{'='*60}
"""
        self.txt_bill_area.insert(END, bill_header)
        for item in self.cart_list:
            pname = item[2][:22] + "..." if len(item[2]) > 25 else item[2]
            qty, total_price = int(item[4]), float(item[5])
            price_per_item = float(item[3])
            self.txt_bill_area.insert(END, f"{pname.ljust(30)}{str(qty).rjust(8)}Rs.{price_per_item:>9.2f}Rs.{total_price:>10.2f}\n")

        change = cash - self.net_pay
        
        # Address moved to the absolute bottom as requested
        bill_footer = f"""
{'-'*60}
{'SUBTOTAL:'.ljust(50)}Rs.{self.bill_amnt:>8.2f}
{'TAX (8%):'.ljust(50)}Rs.{self.tax_amount:>8.2f}
{'='*60}
{'TOTAL AMOUNT:'.ljust(50)}Rs.{self.net_pay:>8.2f}
{'-'*60}
{'CASH RECEIVED:'.ljust(50)}Rs.{cash:>8.2f}
{'CHANGE DUE:'.ljust(50)}Rs.{change:>8.2f}
{'='*60}
{'TERMS & CONDITIONS:'.center(60)}
• Amount is non-refundable
• Only replacement available with original bill
• Replacement within 7 days of purchase
• Goods once sold will not be taken back

{'Thank you for your business!'.center(60)}
{'Please visit again!'.center(60)}
{'='*60}
{'Dukes Tech Services'.center(60)}
{'Phone: +923097671363'.center(60)}
{'Address: Lahore-54000'.center(60)}
{'='*60}
"""
        self.txt_bill_area.insert(END, bill_footer)

    def clear_all(self):
        if not self.cart_list and not self.var_contact.get() and not self.var_cname.get() and not self.var_cash.get(): return messagebox.showinfo("Info", "Already cleared", parent=self.root)
        if messagebox.askyesno("Confirm", "Clear all data?", parent=self.root):
            if not self.bill_generated:
                for item in self.cart_list: self.update_product_quantity_in_db(item[0], int(item[4]), "add")
            self.cart_list.clear()
            self.var_cname.set('')
            self.var_contact.set('')
            self.var_search.set('')
            self.var_search_id.set('')
            self.var_search_barcode.set('')
            self.var_cash.set('')
            self.var_change.set('0.00')
            self.contact_entry.config(bg="white") 
            self.clear_quick_add()
            self.show_cart()
            self.txt_bill_area.delete('1.0', END)
            self.bill_updates()
            self.show() 
            self.bill_generated = False
            messagebox.showinfo("Success", f"All data cleared{' and stock restored' if not self.bill_generated else ''}", parent=self.root)

    def print_bill(self):
        if len(self.cart_list) == 0: return messagebox.showerror("Error", "No bill to print. Please generate bill first.", parent=self.root)
        bill_text = self.txt_bill_area.get('1.0', END).strip()
        if not bill_text: return messagebox.showerror("Error", "Please generate bill first", parent=self.root)
        
        invoice_match = re.search(r'Invoice No\.\s*:\s*([A-Z0-9\-]+)', bill_text)
        invoice_num = invoice_match.group(1) if invoice_match else self.generate_unique_invoice_no()
        date_match = re.search(r'Date\s*:\s*([\d/]+)', bill_text)
        time_match = re.search(r'Time\s*:\s*([\d:]+ [APM]+)', bill_text)
        date_str = date_match.group(1) if date_match else datetime.datetime.now().strftime("%d/%m/%Y")
        time_str = time_match.group(1) if time_match else datetime.datetime.now().strftime("%I:%M:%S %p")
        
        try:
            if not os.path.exists('bills'): os.makedirs('bills')
            file_name = f'bills/{invoice_num}.txt'
            with open(file_name, 'w', encoding='utf-8') as fp: fp.write(self.txt_bill_area.get('1.0', END))
            messagebox.showinfo("Saved & Print", f"Invoice Details:\n----------------\nInvoice No. : {invoice_num}\nDate        : {date_str}\nTime        : {time_str}\n\n1. Saved to: {file_name}\n2. Sent to printer\n3. Saved to database", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save/print bill: {str(e)}", parent=self.root)

if __name__ == "__main__":
    root = Tk()
    obj = Invoice_Class(root)
    root.mainloop()