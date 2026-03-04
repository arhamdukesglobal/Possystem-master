# Purchases.py
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import re
from datetime import datetime, date
from tkcalendar import Calendar  # Replaced DateEntry with Calendar
from PIL import Image, ImageTk
import io
import base64
import webbrowser
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import tempfile


class PurchasesClass:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1100x600+150+50")
        self.root.title(
            "Inventory Management System | Purchases Dashboard | Developed by Dukes Tech Services")
        self.root.config(bg="#FDF2E9")
        self.root.focus_force()

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.main_frame = Frame(self.root, bg="#FDF2E9")
        self.main_frame.pack(fill=BOTH, expand=True)

        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=2)
        for i in range(3):
            self.main_frame.grid_columnconfigure(i, weight=1)

        self.setup_database()

        # Variables
        self.var_searchby = StringVar()
        self.var_searchtxt = StringVar()
        self.var_billno = StringVar()
        self.var_billdate = StringVar()
        self.var_duedate = StringVar()
        self.var_supplier = StringVar()
        self.var_contact = StringVar()
        self.var_address = StringVar()
        self.var_payment_status = StringVar(value="Pending")
        
        self.var_total_amount = StringVar(value="0.00")
        self.var_advance_amount = StringVar(value="0.00")
        self.var_remaining_amount = StringVar(value="0.00")

        self.var_reference = StringVar()
        self.var_description = StringVar()
        self.var_quantity = StringVar()
        self.var_unitprice = StringVar()
        self.var_tax = StringVar(value="9")
        self.var_amount = StringVar()

        self.invoice_image = None
        self.invoice_image_data = None
        self.bill_items = []

        # ===Header with Date Time====
        header_frame = Frame(self.main_frame, bg="#E67E22", height=30)
        header_frame.grid(row=0, column=0, columnspan=3,
                          sticky="ew", padx=5, pady=3)
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = Label(header_frame, text="Purchases Dashboard", font=("Segoe UI", 14, "bold"),
                            bg="#E67E22", fg="white")
        title_label.grid(row=0, column=0, sticky="w", padx=5)

        self.datetime_label = Label(header_frame, font=("Segoe UI", 11),
                                    bg="#E67E22", fg="white")
        self.datetime_label.grid(row=0, column=1, sticky="e", padx=5)
        self.update_datetime()

        # ===searchFrame=====
        SearchFrame = LabelFrame(self.main_frame, text="Search Purchase", font=("Segoe UI", 11, "bold"),
                                 bd=1, relief=RIDGE, bg="white")
        SearchFrame.grid(row=1, column=0, columnspan=3,
                         sticky="ew", padx=5, pady=3, ipady=2)
        SearchFrame.grid_columnconfigure(1, weight=1)

        cmb_search = ttk.Combobox(SearchFrame, textvariable=self.var_searchby,
                                  values=["Select", "Bill No", "Supplier",
                                          "Reference No", "Bill Date", "Payment Status"],
                                  state='readonly', font=("Segoe UI", 10), width=15)
        cmb_search.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        cmb_search.current(0)

        txt_search = Entry(SearchFrame, textvariable=self.var_searchtxt,
                           font=("Segoe UI", 10), bg="white", fg="#1F2937",
                           highlightthickness=1, highlightbackground="#D1D5DB", highlightcolor="#E67E22")
        txt_search.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        btn_search = Button(SearchFrame, text="Search", command=self.search,
                            font=("Segoe UI", 10, "bold"), bg="#E67E22", fg="White", cursor="hand2",
                            activebackground="#D35400", activeforeground="white", bd=0, width=10)
        btn_search.grid(row=0, column=2, padx=2, pady=2, sticky="w")

        btn_show_all = Button(SearchFrame, text="Show All", command=self.show,
                              font=("Segoe UI", 10, "bold"), bg="#10B981", fg="White", cursor="hand2",
                              activebackground="#059669", activeforeground="white", bd=0, width=10)
        btn_show_all.grid(row=0, column=3, padx=2, pady=2, sticky="w")

        # ===Left Panel (Bill Information)====
        left_panel = Frame(self.main_frame, bg="#FDF2E9")
        left_panel.grid(row=2, column=0, rowspan=2,
                        sticky="nsew", padx=(5, 2), pady=2)
        left_panel.grid_rowconfigure(1, weight=0)
        left_panel.grid_rowconfigure(2, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # ===Bill Information Section====
        bill_frame = LabelFrame(left_panel, text="Bill Information", font=("Segoe UI", 11, "bold"),
                                bd=2, relief=RIDGE, bg="white")
        bill_frame.grid(row=0, column=0, sticky="nsew",
                        padx=0, pady=(0, 2), ipady=2)

        # Configure columns for consistent alignment
        # col0: labels left, col1: field1, col2: labels, col3: field2, col4: buttons, col5: field3/status
        bill_frame.grid_columnconfigure(0, weight=0, minsize=80)
        bill_frame.grid_columnconfigure(1, weight=1, uniform='fields')
        bill_frame.grid_columnconfigure(2, weight=0, minsize=70)
        bill_frame.grid_columnconfigure(3, weight=1, uniform='fields')
        bill_frame.grid_columnconfigure(4, weight=0)
        bill_frame.grid_columnconfigure(5, weight=1, uniform='fields')

        # ====row1====
        lbl_billno = Label(bill_frame, text="Bill No", font=("Segoe UI", 10), bg="white", fg="#1F2937")
        lbl_billno.grid(row=0, column=0, sticky="w", padx=2, pady=1)

        self.txt_billno = Entry(bill_frame, textvariable=self.var_billno,
                                font=("Segoe UI", 10), bg="#F9FAFB", fg="#1F2937",
                                state='readonly', highlightthickness=1,
                                highlightbackground="#D1D5DB", width=15)
        self.txt_billno.grid(row=0, column=1, padx=2, pady=1, sticky="ew")

        lbl_billdate = Label(bill_frame, text="Bill Date", font=("Segoe UI", 10), bg="white", fg="#1F2937")
        lbl_billdate.grid(row=0, column=2, sticky="w", padx=2, pady=1)

        # Create custom date entry for Bill Date
        self.billdate_frame, self.billdate_entry = self.create_date_entry(
            bill_frame, self.var_billdate, row=0, col=3, colspan=1)

        # ====row2=====
        lbl_duedate = Label(bill_frame, text="Due Date", font=("Segoe UI", 10), bg="white", fg="#1F2937")
        lbl_duedate.grid(row=1, column=0, sticky="w", padx=2, pady=1)

        # Create custom date entry for Due Date
        self.duedate_frame, self.duedate_entry = self.create_date_entry(
            bill_frame, self.var_duedate, row=1, col=1, colspan=1)

        lbl_payment_status = Label(bill_frame, text="Payment Status", font=("Segoe UI", 10), bg="white", fg="#1F2937")
        lbl_payment_status.grid(row=1, column=2, sticky="w", padx=2, pady=1)

        cmb_payment_status = ttk.Combobox(bill_frame, textvariable=self.var_payment_status,
                                          values=["Pending", "Paid", "Overdue"],
                                          state='readonly', font=("Segoe UI", 9), width=15)
        cmb_payment_status.grid(row=1, column=3, padx=2, pady=1, sticky="ew")

        btn_check_status = Button(bill_frame, text="Check", command=self.manual_check_status,
                                  font=("Segoe UI", 9, "bold"), bg="#F39C12", fg="White", cursor="hand2",
                                  activebackground="#E67E22", activeforeground="white", width=8, bd=0)
        btn_check_status.grid(row=1, column=4, padx=1, pady=1, sticky="w")

        # ====row3=====
        lbl_supplier = Label(bill_frame, text="Supplier", font=("Segoe UI", 10), bg="white", fg="#1F2937")
        lbl_supplier.grid(row=2, column=0, sticky="w", padx=2, pady=1)

        txt_supplier = Entry(bill_frame, textvariable=self.var_supplier,
                             font=("Segoe UI", 10), bg="white", fg="#1F2937",
                             highlightthickness=1, highlightbackground="#D1D5DB", highlightcolor="#E67E22")
        txt_supplier.grid(row=2, column=1, columnspan=5, padx=2, pady=1, sticky="ew")

        # ====row4=====
        lbl_contact = Label(bill_frame, text="Contact", font=("Segoe UI", 10), bg="white", fg="#1F2937")
        lbl_contact.grid(row=3, column=0, sticky="w", padx=2, pady=1)

        contact_frame = Frame(bill_frame, bg="white")
        contact_frame.grid(row=3, column=1, columnspan=5, sticky="ew", padx=2, pady=1)
        contact_frame.grid_columnconfigure(1, weight=1)

        contact_label = Label(contact_frame, text="+92", font=("Segoe UI", 10),
                              bg="#F3F4F6", fg="#6B7280", relief=SUNKEN, bd=1, width=4)
        contact_label.pack(side=LEFT, padx=(0,2), fill=Y)

        self.contact_entry = Entry(contact_frame, font=("Segoe UI", 10),
                                   bg="white", fg="#1F2937", justify=LEFT,
                                   highlightthickness=1, highlightbackground="#D1D5DB", highlightcolor="#E67E22")
        self.contact_entry.pack(side=LEFT, fill=BOTH, expand=True)
        self.contact_entry.bind('<KeyRelease>', self.validate_contact)
        self.contact_entry.bind('<FocusIn>', self.on_contact_focus)

        # ====row5 - Address=====
        lbl_address = Label(bill_frame, text="Address", font=("Segoe UI", 10), bg="white", fg="#1F2937")
        lbl_address.grid(row=4, column=0, sticky="nw", padx=2, pady=1)

        self.txt_address = Text(bill_frame, font=("Segoe UI", 9), bg="white", fg="#1F2937",
                                height=1, highlightthickness=1,
                                highlightbackground="#D1D5DB", highlightcolor="#E67E22")
        self.txt_address.grid(row=4, column=1, columnspan=5, sticky="ew", padx=2, pady=1)

        # ====row6 - Amount Fields=====
        lbl_total_amount = Label(bill_frame, text="Total (PKR)", font=("Segoe UI", 9, "bold"), bg="white", fg="#1F2937")
        lbl_total_amount.grid(row=5, column=0, sticky="w", padx=2, pady=1)

        self.txt_total_amount = Entry(bill_frame, textvariable=self.var_total_amount,
                                      font=("Segoe UI", 9, "bold"), bg="#F9FAFB", fg="#DC2626",
                                      state='disabled', highlightthickness=1,
                                      highlightbackground="#D1D5DB", justify=RIGHT, width=15)
        self.txt_total_amount.grid(row=5, column=1, padx=2, pady=1, sticky="ew")

        lbl_advance = Label(bill_frame, text="Advance", font=("Segoe UI", 9), bg="white", fg="#1F2937")
        lbl_advance.grid(row=5, column=2, sticky="w", padx=2, pady=1)

        self.txt_advance = Entry(bill_frame, textvariable=self.var_advance_amount,
                                 font=("Segoe UI", 9), bg="#F9FAFB", fg="#1F2937",
                                 state='disabled', highlightthickness=1,
                                 highlightbackground="#D1D5DB", highlightcolor="#E67E22", justify=RIGHT, width=15)
        self.txt_advance.grid(row=5, column=3, padx=2, pady=1, sticky="ew")
        self.txt_advance.bind('<KeyRelease>', self.calculate_remaining)

        lbl_remaining = Label(bill_frame, text="Remaining", font=("Segoe UI", 9, "bold"), bg="white", fg="#1F2937")
        lbl_remaining.grid(row=5, column=4, sticky="w", padx=2, pady=1)

        self.txt_remaining = Entry(bill_frame, textvariable=self.var_remaining_amount,
                                   font=("Segoe UI", 9, "bold"), bg="#F9FAFB", fg="#DC2626",
                                   state='disabled', highlightthickness=1,
                                   highlightbackground="#D1D5DB", justify=RIGHT, width=15)
        self.txt_remaining.grid(row=5, column=5, padx=2, pady=1, sticky="ew")

        # ====row7 - Invoice=====
        lbl_invoice = Label(bill_frame, text="Invoice", font=("Segoe UI", 9), bg="white", fg="#1F2937")
        lbl_invoice.grid(row=6, column=2, sticky="w", padx=2, pady=1)

        btn_browse = Button(bill_frame, text="Browse", command=self.browse_invoice,
                            font=("Segoe UI", 9, "bold"), bg="#E67E22", fg="White", cursor="hand2",
                            activebackground="#D35400", activeforeground="white", width=8, bd=0)
        btn_browse.grid(row=6, column=3, padx=2, pady=1, sticky="w")

        btn_view = Button(bill_frame, text="View", command=self.view_invoice,
                          font=("Segoe UI", 9, "bold"), bg="#10B981", fg="White", cursor="hand2",
                          activebackground="#059669", activeforeground="white", width=8, bd=0)
        btn_view.grid(row=6, column=4, padx=2, pady=1, sticky="w")

        self.lbl_invoice_status = Label(bill_frame, text="No invoice",
                                        font=("Segoe UI", 8), bg="white", fg="#6B7280")
        self.lbl_invoice_status.grid(row=6, column=5, sticky="w", padx=2, pady=1)

        # ===Main Buttons Section====
        btn_frame = LabelFrame(left_panel, text="Actions", font=("Segoe UI", 11, "bold"),
                               bd=2, relief=RIDGE, bg="white")
        btn_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=2)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)

        btn_save = Button(btn_frame, text="Save", command=self.save_bill,
                          font=("Segoe UI", 11, "bold"),
                          bg="#00C853", activebackground="#00B248",
                          fg="white", activeforeground="white",
                          cursor="hand2", bd=0, height=1)
        btn_save.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

        btn_update = Button(btn_frame, text="Edit/Update", command=self.update_bill,
                            font=("Segoe UI", 11, "bold"),
                            bg="#2962FF", activebackground="#1E4ED8",
                            fg="white", activeforeground="white",
                            cursor="hand2", bd=0, height=1)
        btn_update.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")

        btn_delete = Button(btn_frame, text="Delete", command=self.delete_bill,
                            font=("Segoe UI", 11, "bold"),
                            bg="#FF1744", activebackground="#D50000",
                            fg="white", activeforeground="white",
                            cursor="hand2", bd=0, height=1)
        btn_delete.grid(row=0, column=2, padx=2, pady=2, sticky="nsew")

        btn_clear = Button(btn_frame, text="Clear All", command=self.clear_all,
                           font=("Segoe UI", 11, "bold"),
                           bg="#FF9100", activebackground="#FF6D00",
                           fg="white", activeforeground="white",
                           cursor="hand2", bd=0, height=1)
        btn_clear.grid(row=1, column=0, columnspan=3,
                       padx=3, pady=3, sticky="nsew")

        # ===Bill Items Section====
        items_frame = LabelFrame(self.main_frame, text="Bill Items", font=("Segoe UI", 11, "bold"),
                                 bd=2, relief=RIDGE, bg="white")
        items_frame.grid(row=2, column=1, columnspan=2,
                         sticky="nsew", padx=(2, 5), pady=2)

        # Configure columns for items frame
        items_frame.grid_columnconfigure(1, weight=1, uniform='items')
        items_frame.grid_columnconfigure(3, weight=1, uniform='items')
        items_frame.grid_columnconfigure(5, weight=0)
        for i in [0,2,4]:
            items_frame.grid_columnconfigure(i, weight=0)

        # ====row1====
        lbl_reference = Label(items_frame, text="Ref No", font=("Segoe UI", 9), bg="white", fg="#1F2937")
        lbl_reference.grid(row=0, column=0, sticky="w", padx=2, pady=1)

        txt_reference = Entry(items_frame, textvariable=self.var_reference,
                              font=("Segoe UI", 9), bg="white", fg="#1F2937",
                              highlightthickness=1, highlightbackground="#D1D5DB", highlightcolor="#E67E22", width=15)
        txt_reference.grid(row=0, column=1, sticky="ew", padx=2, pady=1)

        lbl_description = Label(items_frame, text="Description", font=("Segoe UI", 9), bg="white", fg="#1F2937")
        lbl_description.grid(row=0, column=2, sticky="w", padx=2, pady=1)

        txt_description = Entry(items_frame, textvariable=self.var_description,
                                font=("Segoe UI", 9), bg="white", fg="#1F2937",
                                highlightthickness=1, highlightbackground="#D1D5DB", highlightcolor="#E67E22")
        txt_description.grid(row=0, column=3, columnspan=3, sticky="ew", padx=2, pady=1)

        # ====row2=====
        lbl_quantity = Label(items_frame, text="Qty", font=("Segoe UI", 9), bg="white", fg="#1F2937")
        lbl_quantity.grid(row=1, column=0, sticky="w", padx=2, pady=1)

        txt_quantity = Entry(items_frame, textvariable=self.var_quantity,
                             font=("Segoe UI", 9), bg="white", fg="#1F2937",
                             highlightthickness=1, highlightbackground="#D1D5DB", highlightcolor="#E67E22", width=15)
        txt_quantity.grid(row=1, column=1, sticky="ew", padx=2, pady=1)
        txt_quantity.bind('<KeyRelease>', self.calculate_amount)

        lbl_unitprice = Label(items_frame, text="Unit Price", font=("Segoe UI", 9), bg="white", fg="#1F2937")
        lbl_unitprice.grid(row=1, column=2, sticky="w", padx=2, pady=1)

        txt_unitprice = Entry(items_frame, textvariable=self.var_unitprice,
                              font=("Segoe UI", 9), bg="white", fg="#1F2937",
                              highlightthickness=1, highlightbackground="#D1D5DB", highlightcolor="#E67E22", width=15)
        txt_unitprice.grid(row=1, column=3, sticky="ew", padx=2, pady=1)
        txt_unitprice.bind('<KeyRelease>', self.calculate_amount)

        lbl_tax = Label(items_frame, text="Tax %", font=("Segoe UI", 9), bg="white", fg="#1F2937")
        lbl_tax.grid(row=1, column=4, sticky="w", padx=2, pady=1)

        txt_tax = Entry(items_frame, textvariable=self.var_tax,
                        font=("Segoe UI", 9), bg="white", fg="#1F2937",
                        highlightthickness=1, highlightbackground="#D1D5DB", highlightcolor="#E67E22", width=8)
        txt_tax.grid(row=1, column=5, sticky="w", padx=2, pady=1)
        txt_tax.bind('<KeyRelease>', self.calculate_amount)

        # ====row3=====
        lbl_amount = Label(items_frame, text="Amount", font=("Segoe UI", 9), bg="white", fg="#1F2937")
        lbl_amount.grid(row=2, column=0, sticky="w", padx=2, pady=1)

        txt_amount = Entry(items_frame, textvariable=self.var_amount,
                           font=("Segoe UI", 9, "bold"), bg="#F9FAFB", fg="#DC2626",
                           state='readonly', highlightthickness=1, highlightbackground="#D1D5DB", width=15)
        txt_amount.grid(row=2, column=1, sticky="ew", padx=2, pady=1)

        total_frame = Frame(items_frame, bg="white", bd=1, relief=RIDGE)
        total_frame.grid(row=2, column=3, columnspan=3, sticky="e", padx=2, pady=1)

        lbl_total = Label(total_frame, text="Total:", font=("Segoe UI", 9, "bold"), bg="white", fg="#1F2937")
        lbl_total.pack(side=LEFT, padx=2)

        self.var_total = StringVar(value="0.00")
        lbl_total_amount = Label(total_frame, textvariable=self.var_total,
                                 font=("Segoe UI", 9, "bold"), bg="white", fg="#DC2626")
        lbl_total_amount.pack(side=LEFT)

        # ====row4 - Bill Items Buttons====
        btn_frame_items = Frame(items_frame, bg="white")
        btn_frame_items.grid(row=3, column=0, columnspan=6, sticky="ew", pady=2)
        btn_frame_items.grid_columnconfigure(0, weight=1)
        btn_frame_items.grid_columnconfigure(1, weight=1)
        btn_frame_items.grid_columnconfigure(2, weight=1)
        btn_frame_items.grid_columnconfigure(3, weight=1)

        btn_add_item = Button(btn_frame_items, text="Add", command=self.add_item,
                              font=("Segoe UI", 10, "bold"),
                              bg="#00C853", activebackground="#00B248",
                              fg="white", activeforeground="white",
                              cursor="hand2", bd=0, height=1)
        btn_add_item.grid(row=0, column=0, padx=1, pady=1, sticky="nsew")

        btn_update_item = Button(btn_frame_items, text="Edit", command=self.update_item,
                                 font=("Segoe UI", 10, "bold"),
                                 bg="#2962FF", activebackground="#1E4ED8",
                                 fg="white", activeforeground="white",
                                 cursor="hand2", bd=0, height=1)
        btn_update_item.grid(row=0, column=1, padx=1, pady=1, sticky="nsew")

        btn_clear_item = Button(btn_frame_items, text="Clear", command=self.clear_item,
                                font=("Segoe UI", 10, "bold"),
                                bg="#FF9100", activebackground="#FF6D00",
                                fg="white", activeforeground="white",
                                cursor="hand2", bd=0, height=1)
        btn_clear_item.grid(row=0, column=2, padx=1, pady=1, sticky="nsew")

        btn_remove_item = Button(btn_frame_items, text="Remove", command=self.remove_item,
                                 font=("Segoe UI", 10, "bold"),
                                 bg="#FF1744", activebackground="#D50000",
                                 fg="white", activeforeground="white",
                                 cursor="hand2", bd=0, height=1)
        btn_remove_item.grid(row=0, column=3, padx=1, pady=1, sticky="nsew")

        # ===Bill Items Table====
        items_table_frame = Frame(self.main_frame, bd=2, relief=RIDGE, bg="white")
        items_table_frame.grid(row=3, column=1, columnspan=2,
                               sticky="nsew", padx=(2, 5), pady=2)
        items_table_frame.grid_rowconfigure(0, weight=1)
        items_table_frame.grid_columnconfigure(0, weight=1)

        scrollx = Scrollbar(items_table_frame, orient=HORIZONTAL)
        scrolly = Scrollbar(items_table_frame, orient=VERTICAL)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview",
                        background="white",
                        foreground="#1F2937",
                        rowheight=24,
                        fieldbackground="white",
                        font=("Segoe UI", 9))
        style.configure("Custom.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background="#E67E22",
                        foreground="white")
        style.map('Custom.Treeview', background=[
                  ('selected', '#E67E22')], foreground=[('selected', 'white')])

        self.ItemsTable = ttk.Treeview(items_table_frame, columns=("sr", "reference", "description", "quantity", "unitprice", "tax", "amount"),
                                       yscrollcommand=scrolly.set, xscrollcommand=scrollx.set, height=4,
                                       show="headings", style="Custom.Treeview")
        scrollx.pack(side=BOTTOM, fill=X)
        scrolly.pack(side=RIGHT, fill=Y)
        scrollx.config(command=self.ItemsTable.xview)
        scrolly.config(command=self.ItemsTable.yview)

        self.ItemsTable.heading("sr", text="SR#")
        self.ItemsTable.heading("reference", text="Ref No")
        self.ItemsTable.heading("description", text="Description")
        self.ItemsTable.heading("quantity", text="Qty")
        self.ItemsTable.heading("unitprice", text="Unit Price")
        self.ItemsTable.heading("tax", text="Tax %")
        self.ItemsTable.heading("amount", text="Amount")

        self.ItemsTable.column("sr", width=40, anchor=CENTER, minwidth=40)
        self.ItemsTable.column("reference", width=80, anchor=CENTER, minwidth=80)
        self.ItemsTable.column("description", width=140, anchor=W, minwidth=140)
        self.ItemsTable.column("quantity", width=60, anchor=CENTER, minwidth=60)
        self.ItemsTable.column("unitprice", width=80, anchor=CENTER, minwidth=80)
        self.ItemsTable.column("tax", width=50, anchor=CENTER, minwidth=50)
        self.ItemsTable.column("amount", width=90, anchor=E, minwidth=90)

        self.ItemsTable.pack(fill=BOTH, expand=True)
        self.ItemsTable.bind("<ButtonRelease-1>", self.get_item_data)

        # ===Purchase History Table====
        history_frame = Frame(self.main_frame, bd=2, relief=RIDGE, bg="white")
        history_frame.grid(row=4, column=0, columnspan=3,
                           sticky="nsew", padx=5, pady=2)
        history_frame.grid_rowconfigure(0, weight=1)
        history_frame.grid_columnconfigure(0, weight=1)

        scrollx = Scrollbar(history_frame, orient=HORIZONTAL)
        scrolly = Scrollbar(history_frame, orient=VERTICAL)

        style2 = ttk.Style()
        style2.configure("History.Treeview",
                         background="white",
                         foreground="#1F2937",
                         rowheight=24,
                         fieldbackground="white",
                         font=("Segoe UI", 9))
        style2.configure("History.Treeview.Heading",
                         font=("Segoe UI", 9, "bold"),
                         background="#E67E22",
                         foreground="white")
        style2.map('History.Treeview', background=[
                   ('selected', '#E67E22')], foreground=[('selected', 'white')])

        self.PurchasesTable = ttk.Treeview(history_frame, columns=("billno", "billdate", "duedate", "supplier", "contact", "totalitems", "totalamount", "advance", "remaining", "paymentstatus"),
                                           yscrollcommand=scrolly.set, xscrollcommand=scrollx.set, height=5,
                                           show="headings", style="History.Treeview")
        scrollx.pack(side=BOTTOM, fill=X)
        scrolly.pack(side=RIGHT, fill=Y)
        scrollx.config(command=self.PurchasesTable.xview)
        scrolly.config(command=self.PurchasesTable.yview)

        self.PurchasesTable.heading("billno", text="Bill No")
        self.PurchasesTable.heading("billdate", text="Bill Date")
        self.PurchasesTable.heading("duedate", text="Due Date")
        self.PurchasesTable.heading("supplier", text="Supplier")
        self.PurchasesTable.heading("contact", text="Contact")
        self.PurchasesTable.heading("totalitems", text="Items")
        self.PurchasesTable.heading("totalamount", text="Total")
        self.PurchasesTable.heading("advance", text="Advance")
        self.PurchasesTable.heading("remaining", text="Remaining")
        self.PurchasesTable.heading("paymentstatus", text="Payment Status")

        self.PurchasesTable.column("billno", width=80, anchor=CENTER, minwidth=80)
        self.PurchasesTable.column("billdate", width=80, anchor=CENTER, minwidth=80)
        self.PurchasesTable.column("duedate", width=80, anchor=CENTER, minwidth=80)
        self.PurchasesTable.column("supplier", width=140, anchor=W, minwidth=140)
        self.PurchasesTable.column("contact", width=90, anchor=CENTER, minwidth=90)
        self.PurchasesTable.column("totalitems", width=50, anchor=CENTER, minwidth=50)
        self.PurchasesTable.column("totalamount", width=90, anchor=E, minwidth=90)
        self.PurchasesTable.column("advance", width=80, anchor=E, minwidth=80)
        self.PurchasesTable.column("remaining", width=80, anchor=E, minwidth=80)
        self.PurchasesTable.column("paymentstatus", width=100, anchor=CENTER, minwidth=100)

        self.PurchasesTable.pack(fill=BOTH, expand=True)
        self.PurchasesTable.bind("<ButtonRelease-1>", self.get_bill_data)

        # Initialize
        self.generate_bill_no()
        self.show()
        self.update_total()

    # ---------- Custom Date Entry Methods ----------
    def create_date_entry(self, parent, textvariable, row, col, colspan=1):
        """Create a custom date entry with placeholder and calendar button"""
        frame = Frame(parent, bg="white", highlightthickness=1,
                      highlightbackground="#D1D5DB", highlightcolor="#E67E22")
        frame.grid(row=row, column=col, columnspan=colspan, padx=2, pady=1, sticky='ew')

        # Entry for date
        entry = Entry(frame, font=("Segoe UI", 9), bg="white", fg="#999999",
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
        btn_cal = Button(frame, text="📅", font=("Segoe UI", 9),
                         bg="#E67E22", fg="white", bd=0,
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
                        bg="#E67E22", fg="white", font=("Segoe UI", 9))
        btn_ok.pack(pady=5)

        # Ensure the popup stays on top
        top.transient(self.root)
        top.focus_force()
        top.grab_set()
    # ---------------------------------------------------------

    # ... (all other existing methods unchanged) ...

    # The following methods are exactly as in the original code.
    # They are included here for completeness, but unchanged.

    def setup_database(self):
        """Create database and tables if they don't exist"""
        try:
            db_path = 'Possystem.db'
            print(f"Connecting to database at: {os.path.abspath(db_path)}")

            con = sqlite3.connect(database=db_path)
            cur = con.cursor()

            # First check if table exists
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Purchases'")
            table_exists = cur.fetchone()
            
            if not table_exists:
                # Create table with all columns
                cur.execute('''
                    CREATE TABLE Purchases (
                        BillNo TEXT PRIMARY KEY,
                        BillDate TEXT NOT NULL,
                        DueDate TEXT NOT NULL,
                        Supplier TEXT NOT NULL,
                        Contact TEXT NOT NULL,
                        Address TEXT,
                        TotalItems INTEGER,
                        TotalAmount REAL,
                        Advance REAL DEFAULT 0,
                        Remaining REAL,
                        PaymentStatus TEXT DEFAULT 'Pending',
                        InvoicePicture BLOB
                    )
                ''')
                print("Created Purchases table with all columns")
            else:
                # Check and add missing columns if table exists
                cur.execute("PRAGMA table_info(Purchases)")
                columns = [col[1] for col in cur.fetchall()]
                
                if 'Advance' not in columns:
                    try:
                        cur.execute("ALTER TABLE Purchases ADD COLUMN Advance REAL DEFAULT 0")
                        print("Added Advance column to Purchases table")
                    except Exception as e:
                        print(f"Error adding Advance column: {e}")
                
                if 'Remaining' not in columns:
                    try:
                        cur.execute("ALTER TABLE Purchases ADD COLUMN Remaining REAL")
                        print("Added Remaining column to Purchases table")
                    except Exception as e:
                        print(f"Error adding Remaining column: {e}")
                
                if 'PaymentStatus' not in columns:
                    try:
                        cur.execute("ALTER TABLE Purchases ADD COLUMN PaymentStatus TEXT DEFAULT 'Pending'")
                        print("Added PaymentStatus column to Purchases table")
                    except Exception as e:
                        print(f"Error adding PaymentStatus column: {e}")
                
                if 'InvoicePicture' not in columns:
                    try:
                        cur.execute("ALTER TABLE Purchases ADD COLUMN InvoicePicture BLOB")
                        print("Added InvoicePicture column to Purchases table")
                    except Exception as e:
                        print(f"Error adding InvoicePicture column: {e}")

            # Create PurchaseItems table if not exists
            cur.execute('''
                CREATE TABLE IF NOT EXISTS PurchaseItems (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    BillNo TEXT NOT NULL,
                    ReferenceNo TEXT,
                    Description TEXT NOT NULL,
                    Quantity INTEGER NOT NULL,
                    UnitPrice REAL NOT NULL,
                    TaxRate REAL,
                    Amount REAL NOT NULL,
                    FOREIGN KEY (BillNo) REFERENCES Purchases(BillNo)
                )
            ''')

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

    def generate_bill_no(self):
        """Generate auto-incrementing bill number"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute(
                "SELECT BillNo FROM Purchases ORDER BY BillNo DESC LIMIT 1")
            result = cur.fetchone()

            if result:
                last_bill = result[0]
                numbers = re.findall(r'\d+', last_bill)
                if numbers:
                    last_number = int(numbers[-1])
                    next_number = last_number + 1
                else:
                    next_number = 1
            else:
                next_number = 1

            next_bill = f"BILL{next_number:06d}"
            self.var_billno.set(next_bill)
        except Exception as ex:
            self.var_billno.set("BILL000001")
            print(f"Error generating bill: {str(ex)}")
        finally:
            con.close()

    # Removed on_billdate_select and on_duedate_select as they are no longer needed.
    # The custom entry handles date setting via validation and calendar.

    def manual_check_status(self):
        """Manually check and update payment status based on due date"""
        if not self.var_duedate.get() or not self.var_billdate.get():
            messagebox.showwarning(
                "Warning", "Please select bill date and due date first", parent=self.root)
            return

        try:
            due_date = datetime.strptime(self.var_duedate.get(), "%d/%m/%Y")
            current_date = datetime.now()

            if due_date < current_date:
                if self.var_payment_status.get() == "Paid":
                    messagebox.showinfo("Status Info",
                                        f"Due date has passed, but status is already set to 'Paid'.\n"
                                        f"If payment was not made, please change status to 'Overdue' manually.",
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

    def on_contact_focus(self, event):
        """Set cursor to the beginning of the entry when focused"""
        self.contact_entry.icursor(0)

    def validate_contact(self, event=None):
        """Validate Contact to accept exactly 10 digits"""
        current_text = self.contact_entry.get()
        if current_text:
            digits = ''.join(filter(str.isdigit, current_text))
            if len(digits) > 10:
                digits = digits[:10]

            self.contact_entry.delete(0, END)
            self.contact_entry.insert(0, digits)
            self.contact_entry.icursor(len(digits))

            if len(digits) == 10:
                self.contact_entry.config(bg="#DCFCE7")
            elif len(digits) > 0:
                self.contact_entry.config(bg="white")
            else:
                self.contact_entry.config(bg="white")

    def validate_contact_format(self, contact_digits):
        """Validate that contact has exactly 10 digits"""
        if not contact_digits:
            return False, "Contact number is required"

        if len(contact_digits) != 10:
            return False, "Contact must be exactly 10 digits"

        if not contact_digits.isdigit():
            return False, "Contact must contain only digits"

        return True, f"+92{contact_digits}"

    def browse_invoice(self):
        """Browse and select invoice picture"""
        file_path = filedialog.askopenfilename(
            title="Select Invoice Picture",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All Files", "*.*")]
        )

        if file_path:
            try:
                img = Image.open(file_path)
                img.thumbnail((800, 800))

                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                self.invoice_image_data = img_byte_arr.getvalue()

                self.invoice_image = ImageTk.PhotoImage(img)

                file_name = os.path.basename(file_path)
                self.lbl_invoice_status.config(
                    text=f"✓ {file_name}", fg="#10B981")
                messagebox.showinfo(
                    "Success", "Invoice picture loaded successfully!", parent=self.root)

            except Exception as ex:
                messagebox.showerror(
                    "Error", f"Failed to load image: {str(ex)}", parent=self.root)
                self.invoice_image = None
                self.invoice_image_data = None
                self.lbl_invoice_status.config(text="No invoice", fg="#6B7280")

    def view_invoice(self):
        """View the attached invoice picture"""
        if self.invoice_image is None:
            messagebox.showinfo(
                "Info", "No invoice picture attached", parent=self.root)
            return

        view_window = Toplevel(self.root)
        view_window.title("View Invoice Picture")
        view_window.geometry("700x550")
        view_window.config(bg="white")

        view_window.grid_rowconfigure(0, weight=1)
        view_window.grid_columnconfigure(0, weight=1)

        main_container = Frame(view_window, bg="white")
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)

        title_label = Label(main_container, text="Invoice Picture",
                            font=("Segoe UI", 14, "bold"), bg="white", fg="#E67E22")
        title_label.pack(pady=(0, 10))

        img_frame = Frame(main_container, bg="white")
        img_frame.pack(fill=BOTH, expand=True, pady=5)

        canvas_frame = Frame(img_frame, bg="white")
        canvas_frame.pack(fill=BOTH, expand=True)

        canvas = Canvas(canvas_frame, bg="white")
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        v_scrollbar = Scrollbar(
            canvas_frame, orient=VERTICAL, command=canvas.yview)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar = Scrollbar(
            img_frame, orient=HORIZONTAL, command=canvas.xview)
        h_scrollbar.pack(side=BOTTOM, fill=X)

        canvas.configure(yscrollcommand=v_scrollbar.set,
                         xscrollcommand=h_scrollbar.set)

        canvas.create_image(0, 0, anchor=NW, image=self.invoice_image)
        canvas.config(scrollregion=canvas.bbox("all"))

        info_frame = Frame(main_container, bg="white")
        info_frame.pack(pady=10)

        Label(info_frame, text=f"Bill No: {self.var_billno.get()}",
              font=("Segoe UI", 10), bg="white", fg="#1F2937").pack()
        Label(info_frame, text=f"Supplier: {self.var_supplier.get()}",
              font=("Segoe UI", 10), bg="white", fg="#1F2937").pack(pady=2)

        btn_close = Button(main_container, text="Close", command=view_window.destroy,
                           font=("Segoe UI", 10, "bold"), bg="#6B7280", fg="White", cursor="hand2",
                           activebackground="#4B5563", activeforeground="white",
                           width=15, height=1, bd=0)
        btn_close.pack(pady=10)

    def calculate_amount(self, event=None):
        """Calculate amount based on quantity, unit price and tax"""
        try:
            quantity = float(self.var_quantity.get()
                             ) if self.var_quantity.get() else 0
            unit_price = float(self.var_unitprice.get()
                               ) if self.var_unitprice.get() else 0
            tax_rate = float(self.var_tax.get()) if self.var_tax.get() else 0

            subtotal = quantity * unit_price
            tax_amount = (subtotal * tax_rate) / 100
            total_amount = subtotal + tax_amount

            self.var_amount.set(f"{total_amount:.2f}")
        except:
            self.var_amount.set("0.00")

    def calculate_remaining(self, event=None):
        """Calculate remaining amount based on total and advance"""
        try:
            total = float(self.var_total_amount.get().replace(',', '')) if self.var_total_amount.get() else 0
            advance = float(self.var_advance_amount.get().replace(',', '')) if self.var_advance_amount.get() else 0
            
            if advance > total:
                messagebox.showwarning("Warning", "Advance amount cannot exceed total amount!", parent=self.root)
                self.var_advance_amount.set(f"{total:.2f}")
                advance = total
            
            remaining = total - advance
            self.var_remaining_amount.set(f"{remaining:.2f}")
            
            if remaining == 0:
                self.var_payment_status.set("Paid")
            elif advance > 0 and remaining > 0:
                self.var_payment_status.set("Pending")
            else:
                self.var_payment_status.set("Pending")
                
        except ValueError:
            self.var_remaining_amount.set("0.00")

    def add_item(self):
        """Add item to the bill items list"""
        try:
            if not self.var_reference.get().strip():
                messagebox.showerror(
                    "Error", "Reference No is required", parent=self.root)
                return
            if not self.var_description.get().strip():
                messagebox.showerror(
                    "Error", "Description is required", parent=self.root)
                return
            if not self.var_quantity.get() or float(self.var_quantity.get()) <= 0:
                messagebox.showerror(
                    "Error", "Valid quantity is required", parent=self.root)
                return
            if not self.var_unitprice.get() or float(self.var_unitprice.get()) <= 0:
                messagebox.showerror(
                    "Error", "Valid unit price is required", parent=self.root)
                return

            reference = self.var_reference.get().strip()
            description = self.var_description.get().strip()
            quantity = float(self.var_quantity.get())
            unit_price = float(self.var_unitprice.get())
            tax_rate = float(self.var_tax.get())
            amount = float(self.var_amount.get())

            item = {
                'reference': reference,
                'description': description,
                'quantity': quantity,
                'unit_price': unit_price,
                'tax_rate': tax_rate,
                'amount': amount
            }

            self.bill_items.append(item)
            self.update_items_table()
            self.clear_item()
            self.update_total()
            
            if self.bill_items:
                self.enable_amount_fields()

        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error adding item: {str(ex)}", parent=self.root)

    def enable_amount_fields(self):
        """Enable the amount fields when bill items are finalized"""
        self.txt_total_amount.config(state='normal')
        self.txt_advance.config(state='normal')
        self.txt_remaining.config(state='normal')

    def disable_amount_fields(self):
        """Disable the amount fields when no items"""
        self.txt_total_amount.config(state='disabled')
        self.txt_advance.config(state='disabled')
        self.txt_remaining.config(state='disabled')

    def update_item(self):
        """Update selected item in the bill items list"""
        try:
            selected_item = self.ItemsTable.selection()
            if not selected_item:
                messagebox.showerror(
                    "Error", "Please select an item to update", parent=self.root)
                return

            if not self.var_reference.get().strip():
                messagebox.showerror(
                    "Error", "Reference No is required", parent=self.root)
                return
            if not self.var_description.get().strip():
                messagebox.showerror(
                    "Error", "Description is required", parent=self.root)
                return
            if not self.var_quantity.get() or float(self.var_quantity.get()) <= 0:
                messagebox.showerror(
                    "Error", "Valid quantity is required", parent=self.root)
                return
            if not self.var_unitprice.get() or float(self.var_unitprice.get()) <= 0:
                messagebox.showerror(
                    "Error", "Valid unit price is required", parent=self.root)
                return

            item_index = self.ItemsTable.index(selected_item[0])

            self.bill_items[item_index] = {
                'reference': self.var_reference.get().strip(),
                'description': self.var_description.get().strip(),
                'quantity': float(self.var_quantity.get()),
                'unit_price': float(self.var_unitprice.get()),
                'tax_rate': float(self.var_tax.get()),
                'amount': float(self.var_amount.get())
            }

            self.update_items_table()
            self.clear_item()
            self.update_total()

        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error updating item: {str(ex)}", parent=self.root)

    def remove_item(self):
        """Remove selected item from the bill items list"""
        try:
            selected_item = self.ItemsTable.selection()
            if not selected_item:
                messagebox.showerror(
                    "Error", "Please select an item to remove", parent=self.root)
                return

            item_index = self.ItemsTable.index(selected_item[0])
            self.bill_items.pop(item_index)
            self.update_items_table()
            self.clear_item()
            self.update_total()
            
            if not self.bill_items:
                self.disable_amount_fields()

        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error removing item: {str(ex)}", parent=self.root)

    def clear_item(self):
        """Clear item entry fields"""
        self.var_reference.set("")
        self.var_description.set("")
        self.var_quantity.set("")
        self.var_unitprice.set("")
        self.var_tax.set("9")
        self.var_amount.set("")

    def get_item_data(self, ev):
        """Get selected item data for editing"""
        try:
            f = self.ItemsTable.focus()
            if not f:
                return

            content = self.ItemsTable.item(f)
            row = content['values']
            if not row or len(row) < 7:
                return

            self.var_reference.set(row[1])
            self.var_description.set(row[2])
            self.var_quantity.set(row[3])
            self.var_unitprice.set(row[4])
            self.var_tax.set(row[5])
            self.var_amount.set(row[6])

        except Exception as ex:
            print(f"Error getting item data: {str(ex)}")

    def update_items_table(self):
        """Update the bill items table display"""
        self.ItemsTable.delete(*self.ItemsTable.get_children())

        for i, item in enumerate(self.bill_items, 1):
            self.ItemsTable.insert('', END, values=(
                i,
                item['reference'],
                item['description'],
                f"{item['quantity']:.2f}",
                f"{item['unit_price']:.2f}",
                f"{item['tax_rate']:.2f}",
                f"{item['amount']:.2f}"
            ))

    def update_total(self):
        """Update the total amount display"""
        total = sum(item['amount'] for item in self.bill_items)
        self.var_total.set(f"{total:.2f}")
        self.var_total_amount.set(f"{total:,.2f}")
        
        try:
            advance = float(self.var_advance_amount.get().replace(',', '')) if self.var_advance_amount.get() else 0
            if advance > total:
                self.var_advance_amount.set(f"{total:,.2f}")
                advance = total
            remaining = total - advance
            self.var_remaining_amount.set(f"{remaining:,.2f}")
        except:
            self.var_remaining_amount.set(f"{total:,.2f}")

    def validate_bill(self):
        """Validate the complete bill"""
        errors = []

        if not self.var_billno.get():
            errors.append("Bill No is required")

        if not self.var_billdate.get():
            errors.append("Bill Date is required")

        if not self.var_duedate.get():
            errors.append("Due Date is required")

        if not self.var_supplier.get().strip():
            errors.append("Supplier Name is required")

        contact_digits = self.contact_entry.get().strip()
        if not contact_digits:
            errors.append("Contact is required")
        else:
            is_valid, msg = self.validate_contact_format(contact_digits)
            if not is_valid:
                errors.append(msg)

        if not self.txt_address.get('1.0', END).strip():
            errors.append("Address is required")

        if not self.bill_items:
            errors.append("At least one bill item is required")

        try:
            total = float(self.var_total_amount.get().replace(',', '')) if self.var_total_amount.get() else 0
            advance = float(self.var_advance_amount.get().replace(',', '')) if self.var_advance_amount.get() else 0
            remaining = float(self.var_remaining_amount.get().replace(',', '')) if self.var_remaining_amount.get() else 0
            
            if total <= 0:
                errors.append("Total amount must be greater than 0")
            if advance < 0:
                errors.append("Advance amount cannot be negative")
            if advance > total:
                errors.append("Advance amount cannot exceed total amount")
            if abs(total - (advance + remaining)) > 0.01:
                errors.append("Total amount must equal advance + remaining")
                
        except ValueError:
            errors.append("Invalid amount values")

        if errors:
            messagebox.showerror("Validation Error",
                                 "\n".join(errors), parent=self.root)
            return False

        return True

    def save_bill(self):
        """Save the complete bill to database"""
        if not self.validate_bill():
            return

        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            contact_digits = self.contact_entry.get().strip()
            is_valid, full_contact = self.validate_contact_format(
                contact_digits)
            if not is_valid:
                messagebox.showerror("Error", full_contact, parent=self.root)
                return

            total_amount = sum(item['amount'] for item in self.bill_items)
            total_items = len(self.bill_items)
            
            total_from_field = float(self.var_total_amount.get().replace(',', ''))
            advance = float(self.var_advance_amount.get().replace(',', ''))
            remaining = float(self.var_remaining_amount.get().replace(',', ''))

            if self.invoice_image_data:
                cur.execute("""
                    INSERT INTO Purchases(BillNo, BillDate, DueDate, Supplier, Contact, Address, TotalItems, TotalAmount, Advance, Remaining, PaymentStatus, InvoicePicture)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.var_billno.get(),
                    self.var_billdate.get(),
                    self.var_duedate.get(),
                    self.var_supplier.get().strip(),
                    full_contact,
                    self.txt_address.get('1.0', END).strip(),
                    total_items,
                    total_from_field,
                    advance,
                    remaining,
                    self.var_payment_status.get(),
                    self.invoice_image_data
                ))
            else:
                cur.execute("""
                    INSERT INTO Purchases(BillNo, BillDate, DueDate, Supplier, Contact, Address, TotalItems, TotalAmount, Advance, Remaining, PaymentStatus)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.var_billno.get(),
                    self.var_billdate.get(),
                    self.var_duedate.get(),
                    self.var_supplier.get().strip(),
                    full_contact,
                    self.txt_address.get('1.0', END).strip(),
                    total_items,
                    total_from_field,
                    advance,
                    remaining,
                    self.var_payment_status.get()
                ))

            for item in self.bill_items:
                cur.execute("""
                    INSERT INTO PurchaseItems(BillNo, ReferenceNo, Description, Quantity, UnitPrice, TaxRate, Amount)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.var_billno.get(),
                    item['reference'],
                    item['description'],
                    item['quantity'],
                    item['unit_price'],
                    item['tax_rate'],
                    item['amount']
                ))

            con.commit()
            messagebox.showinfo(
                "Success", "Bill saved successfully", parent=self.root)
            self.show()
            self.clear_all()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Error", "Bill number already exists", parent=self.root)
        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error saving bill: {str(ex)}", parent=self.root)
            print(f"Save error: {str(ex)}")
        finally:
            con.close()

    def update_bill(self):
        """Update an existing bill"""
        if not self.validate_bill():
            return

        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT * FROM Purchases WHERE BillNo=?",
                        (self.var_billno.get(),))
            if not cur.fetchone():
                messagebox.showerror(
                    "Error", "Bill not found", parent=self.root)
                return

            contact_digits = self.contact_entry.get().strip()
            is_valid, full_contact = self.validate_contact_format(
                contact_digits)
            if not is_valid:
                messagebox.showerror("Error", full_contact, parent=self.root)
                return

            total_amount = sum(item['amount'] for item in self.bill_items)
            total_items = len(self.bill_items)
            
            total_from_field = float(self.var_total_amount.get().replace(',', ''))
            advance = float(self.var_advance_amount.get().replace(',', ''))
            remaining = float(self.var_remaining_amount.get().replace(',', ''))

            if self.invoice_image_data:
                cur.execute("""
                    UPDATE Purchases SET 
                    BillDate=?, DueDate=?, Supplier=?, Contact=?, Address=?, TotalItems=?, TotalAmount=?, Advance=?, Remaining=?, PaymentStatus=?, InvoicePicture=?
                    WHERE BillNo=?
                """, (
                    self.var_billdate.get(),
                    self.var_duedate.get(),
                    self.var_supplier.get().strip(),
                    full_contact,
                    self.txt_address.get('1.0', END).strip(),
                    total_items,
                    total_from_field,
                    advance,
                    remaining,
                    self.var_payment_status.get(),
                    self.invoice_image_data,
                    self.var_billno.get()
                ))
            else:
                cur.execute("""
                    UPDATE Purchases SET 
                    BillDate=?, DueDate=?, Supplier=?, Contact=?, Address=?, TotalItems=?, TotalAmount=?, Advance=?, Remaining=?, PaymentStatus=?
                    WHERE BillNo=?
                """, (
                    self.var_billdate.get(),
                    self.var_duedate.get(),
                    self.var_supplier.get().strip(),
                    full_contact,
                    self.txt_address.get('1.0', END).strip(),
                    total_items,
                    total_from_field,
                    advance,
                    remaining,
                    self.var_payment_status.get(),
                    self.var_billno.get()
                ))

            cur.execute("DELETE FROM PurchaseItems WHERE BillNo=?",
                        (self.var_billno.get(),))

            for item in self.bill_items:
                cur.execute("""
                    INSERT INTO PurchaseItems(BillNo, ReferenceNo, Description, Quantity, UnitPrice, TaxRate, Amount)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.var_billno.get(),
                    item['reference'],
                    item['description'],
                    item['quantity'],
                    item['unit_price'],
                    item['tax_rate'],
                    item['amount']
                ))

            con.commit()
            messagebox.showinfo(
                "Success", "Bill updated successfully", parent=self.root)
            self.show()

        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error updating bill: {str(ex)}", parent=self.root)
            print(f"Update error: {str(ex)}")
        finally:
            con.close()

    def delete_bill(self):
        """Delete a bill"""
        if not self.var_billno.get():
            messagebox.showerror(
                "Error", "Please select a bill to delete", parent=self.root)
            return

        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT * FROM Purchases WHERE BillNo=?",
                        (self.var_billno.get(),))
            if not cur.fetchone():
                messagebox.showerror(
                    "Error", "Bill not found", parent=self.root)
                return

            op = messagebox.askyesno(
                "Confirm", "Do you really want to delete this bill?", parent=self.root)
            if op:
                cur.execute("DELETE FROM PurchaseItems WHERE BillNo=?",
                            (self.var_billno.get(),))
                cur.execute("DELETE FROM Purchases WHERE BillNo=?",
                            (self.var_billno.get(),))

                con.commit()
                messagebox.showinfo(
                    "Success", "Bill deleted successfully", parent=self.root)
                self.clear_all()
                self.show()

        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error deleting bill: {str(ex)}", parent=self.root)
        finally:
            con.close()

    def clear_all(self):
        """Clear all fields and reset form"""
        self.var_billdate.set("")
        self.var_duedate.set("")
        self.var_supplier.set("")
        self.contact_entry.delete(0, END)
        self.txt_address.delete('1.0', END)
        self.var_payment_status.set("Pending")
        
        self.var_total_amount.set("0.00")
        self.var_advance_amount.set("0.00")
        self.var_remaining_amount.set("0.00")
        self.disable_amount_fields()

        self.bill_items = []
        self.update_items_table()
        self.clear_item()
        self.update_total()

        self.invoice_image = None
        self.invoice_image_data = None
        self.lbl_invoice_status.config(text="No invoice", fg="#6B7280")

        self.var_searchtxt.set("")
        self.var_searchby.set("Select")

        self.generate_bill_no()

        # Reset custom date entries to placeholder
        for entry in [self.billdate_entry, self.duedate_entry]:
            entry.delete(0, END)
            entry.insert(0, entry.placeholder)
            entry.config(fg="#999999")
            entry.textvariable.set("")

    def show(self):
        """Show all purchases in the table"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute(
                "SELECT BillNo, BillDate, DueDate, Supplier, Contact, TotalItems, TotalAmount, Advance, Remaining, PaymentStatus FROM Purchases ORDER BY BillNo DESC")
            rows = cur.fetchall()

            self.PurchasesTable.delete(*self.PurchasesTable.get_children())

            for row in rows:
                formatted_row = list(row)
                formatted_row[6] = f"{formatted_row[6] or 0:,.2f}"
                formatted_row[7] = f"{formatted_row[7] or 0:,.2f}"
                formatted_row[8] = f"{formatted_row[8] or 0:,.2f}"

                if formatted_row[9] is None:
                    formatted_row[9] = "Pending"
                
                if formatted_row[9] == "Overdue":
                    formatted_row[9] = "⚠ " + formatted_row[9]
                elif formatted_row[9] == "Paid":
                    formatted_row[9] = "✓ " + formatted_row[9]

                self.PurchasesTable.insert('', END, values=formatted_row)

        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error loading data: {str(ex)}", parent=self.root)
            print(f"Show error: {str(ex)}")
        finally:
            con.close()

    def get_bill_data(self, ev):
        """Get selected bill data for editing"""
        try:
            f = self.PurchasesTable.focus()
            if not f:
                return

            content = self.PurchasesTable.item(f)
            row = content['values']
            if not row or len(row) < 10:
                return

            self.clear_all()

            self.var_billno.set(row[0])
            self.var_billdate.set(row[1])
            self.var_duedate.set(row[2])
            self.var_supplier.set(row[3])

            payment_status = row[9]
            if payment_status.startswith("⚠ "):
                payment_status = payment_status[2:]
            elif payment_status.startswith("✓ "):
                payment_status = payment_status[2:]
            self.var_payment_status.set(payment_status)

            contact = str(row[4])
            if contact.startswith('+92'):
                contact = contact[3:]
            elif contact.startswith('92') and len(contact) == 12:
                contact = contact[2:]

            digits = ''.join(filter(str.isdigit, contact))
            if len(digits) >= 10:
                digits = digits[-10:]

            self.contact_entry.delete(0, END)
            self.contact_entry.insert(0, digits)

            total_amount = row[6] if row[6] else "0.00"
            advance_amount = row[7] if row[7] else "0.00"
            remaining_amount = row[8] if row[8] else "0.00"
            
            self.var_total_amount.set(total_amount)
            self.var_advance_amount.set(advance_amount)
            self.var_remaining_amount.set(remaining_amount)
            self.enable_amount_fields()

            # Update custom date entries
            self.billdate_entry.delete(0, END)
            if row[1]:
                self.billdate_entry.insert(0, row[1])
                self.billdate_entry.config(fg="#1F2937")
            else:
                self.billdate_entry.insert(0, self.billdate_entry.placeholder)
                self.billdate_entry.config(fg="#999999")

            self.duedate_entry.delete(0, END)
            if row[2]:
                self.duedate_entry.insert(0, row[2])
                self.duedate_entry.config(fg="#1F2937")
            else:
                self.duedate_entry.insert(0, self.duedate_entry.placeholder)
                self.duedate_entry.config(fg="#999999")

            self.load_address_from_db(row[0])
            self.load_invoice_picture(row[0])
            self.load_bill_items(row[0])

        except Exception as ex:
            print(f"Error getting bill data: {str(ex)}")

    def load_address_from_db(self, bill_no):
        """Load address from database for selected bill"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute(
                "SELECT Address FROM Purchases WHERE BillNo=?", (bill_no,))
            result = cur.fetchone()

            if result and result[0]:
                self.txt_address.delete('1.0', END)
                self.txt_address.insert('1.0', result[0])
            else:
                self.txt_address.delete('1.0', END)

        except Exception as ex:
            print(f"Error loading address: {str(ex)}")
        finally:
            con.close()

    def load_invoice_picture(self, bill_no):
        """Load invoice picture from database"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute(
                "SELECT InvoicePicture FROM Purchases WHERE BillNo=?", (bill_no,))
            result = cur.fetchone()

            if result and result[0]:
                img_data = result[0]
                img = Image.open(io.BytesIO(img_data))
                img.thumbnail((800, 800))

                self.invoice_image = ImageTk.PhotoImage(img)
                self.invoice_image_data = img_data
                self.lbl_invoice_status.config(
                    text="✓ Invoice attached", fg="#10B981")
            else:
                self.invoice_image = None
                self.invoice_image_data = None
                self.lbl_invoice_status.config(text="No invoice", fg="#6B7280")

        except Exception as ex:
            print(f"Error loading invoice picture: {str(ex)}")
        finally:
            con.close()

    def load_bill_items(self, bill_no):
        """Load bill items for the selected bill"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT ReferenceNo, Description, Quantity, UnitPrice, TaxRate, Amount 
                FROM PurchaseItems 
                WHERE BillNo=? 
                ORDER BY ID
            """, (bill_no,))

            rows = cur.fetchall()
            self.bill_items = []

            for row in rows:
                item = {
                    'reference': row[0],
                    'description': row[1],
                    'quantity': row[2],
                    'unit_price': row[3],
                    'tax_rate': row[4],
                    'amount': row[5]
                }
                self.bill_items.append(item)

            self.update_items_table()
            self.update_total()

        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error loading bill items: {str(ex)}", parent=self.root)
        finally:
            con.close()

    def search(self):
        """Search purchases based on criteria"""
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

            self.PurchasesTable.delete(*self.PurchasesTable.get_children())

            if search_by == "Bill No":
                if search_text.isdigit() and len(search_text) <= 6:
                    search_bill = f"BILL{int(search_text):06d}"
                elif search_text.upper().startswith('BILL') and search_text[4:].isdigit() and len(search_text) <= 10:
                    search_bill = f"BILL{int(search_text[4:]):06d}"
                else:
                    search_bill = search_text.upper()

                cur.execute(
                    "SELECT BillNo, BillDate, DueDate, Supplier, Contact, TotalItems, TotalAmount, Advance, Remaining, PaymentStatus FROM Purchases WHERE BillNo LIKE ?", (f'%{search_bill}%',))

            elif search_by == "Supplier":
                cur.execute(
                    "SELECT BillNo, BillDate, DueDate, Supplier, Contact, TotalItems, TotalAmount, Advance, Remaining, PaymentStatus FROM Purchases WHERE Supplier LIKE ?", (f'%{search_text}%',))

            elif search_by == "Reference No":
                cur.execute("""
                    SELECT p.BillNo, p.BillDate, p.DueDate, p.Supplier, p.Contact, p.TotalItems, p.TotalAmount, p.Advance, p.Remaining, p.PaymentStatus
                    FROM Purchases p
                    JOIN PurchaseItems pi ON p.BillNo = pi.BillNo
                    WHERE pi.ReferenceNo LIKE ?
                    GROUP BY p.BillNo
                """, (f'%{search_text}%',))

            elif search_by == "Bill Date":
                cur.execute(
                    "SELECT BillNo, BillDate, DueDate, Supplier, Contact, TotalItems, TotalAmount, Advance, Remaining, PaymentStatus FROM Purchases WHERE BillDate LIKE ?", (f'%{search_text}%',))

            elif search_by == "Payment Status":
                cur.execute(
                    "SELECT BillNo, BillDate, DueDate, Supplier, Contact, TotalItems, TotalAmount, Advance, Remaining, PaymentStatus FROM Purchases WHERE PaymentStatus LIKE ?", (f'%{search_text}%',))

            rows = cur.fetchall()
            if rows:
                for row in rows:
                    formatted_row = list(row)
                    formatted_row[6] = f"{formatted_row[6] or 0:,.2f}"
                    formatted_row[7] = f"{formatted_row[7] or 0:,.2f}"
                    formatted_row[8] = f"{formatted_row[8] or 0:,.2f}"

                    if formatted_row[9] is None:
                        formatted_row[9] = "Pending"
                    
                    if formatted_row[9] == "Overdue":
                        formatted_row[9] = "⚠ " + formatted_row[9]
                    elif formatted_row[9] == "Paid":
                        formatted_row[9] = "✓ " + formatted_row[9]

                    self.PurchasesTable.insert('', END, values=formatted_row)
            else:
                messagebox.showinfo(
                    "No Results", "No records found matching your search", parent=self.root)
                self.show()
        except Exception as ex:
            messagebox.showerror(
                "Error", f"Error searching: {str(ex)}", parent=self.root)
        finally:
            con.close()


if __name__ == "__main__":
    try:
        db_path = 'Possystem.db'
        print(f"Initializing database at: {os.path.abspath(db_path)}")
        
        con = sqlite3.connect(db_path)
        cur = con.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Purchases (
                BillNo TEXT PRIMARY KEY,
                BillDate TEXT NOT NULL,
                DueDate TEXT NOT NULL,
                Supplier TEXT NOT NULL,
                Contact TEXT NOT NULL,
                Address TEXT,
                TotalItems INTEGER,
                TotalAmount REAL,
                Advance REAL DEFAULT 0,
                Remaining REAL,
                PaymentStatus TEXT DEFAULT 'Pending',
                InvoicePicture BLOB
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS PurchaseItems (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                BillNo TEXT NOT NULL,
                ReferenceNo TEXT,
                Description TEXT NOT NULL,
                Quantity INTEGER NOT NULL,
                UnitPrice REAL NOT NULL,
                TaxRate REAL,
                Amount REAL NOT NULL,
                FOREIGN KEY (BillNo) REFERENCES Purchases(BillNo)
            )
        ''')

        con.commit()
        con.close()
        print("Database tables created/updated successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

    root = Tk()
    obj = PurchasesClass(root)
    root.mainloop()