from tkinter import *
from PIL import Image, ImageTk
from tkinter import messagebox, ttk
import sqlite3

class CategoryClass:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1100x500+220+130")
        self.root.title("Inventory Management System | Developed by Dukes Tech Services")
        self.root.config(bg="white")
        self.root.focus_force()
        
        ########Variables===========
        self.var_CatID = StringVar()
        self.var_Name = StringVar()

        #===============title================
        lbl_title = Label(self.root, text="Manage Product Category", font=("goudy old style", 30), bg="#184a45", fg="white", bd=3, relief=RIDGE).pack(side=TOP, fill=X, padx=10, pady=20)

        lbl_name = Label(self.root, text="Enter Category Name", font=("goudy old style", 30), bg="white").place(x=50, y=100)
        txt_name = Entry(self.root, textvariable=self.var_Name, font=("goudy old style", 18), bg="lightyellow").place(x=50, y=170, width=300)

        btn_add = Button(self.root, text="ADD", command=self.add, font=("goudy old style", 15), bg="#4caf50", fg="white", cursor="hand2").place(x=360, y=170, width=150, height=30)
        btn_delete = Button(self.root, text="DELETE", command=self.delete, font=("goudy old style", 15), bg="red", fg="white", cursor="hand2").place(x=520, y=170, width=150, height=30)

        #========Category Details===========
        cat_frame = Frame(self.root, bd=3, relief=RIDGE)
        cat_frame.place(x=700, y=100, width=500, height=700)

        scrolly = Scrollbar(cat_frame, orient=VERTICAL)
        scrollx = Scrollbar(cat_frame, orient=HORIZONTAL)

        self.Category_Table = ttk.Treeview(cat_frame, columns=("CID", "Name"), yscrollcommand=scrolly.set, xscrollcommand=scrollx.set)
        scrollx.pack(side=BOTTOM, fill=X)
        scrolly.pack(side=RIGHT, fill=Y)
        scrollx.config(command=self.Category_Table.xview)
        scrolly.config(command=self.Category_Table.yview)

        self.Category_Table.heading("CID", text="Category ID")
        self.Category_Table.heading("Name", text="Name")
        self.Category_Table["show"] = "headings"
        self.Category_Table.column("CID", width=90)
        self.Category_Table.column("Name", width=100)
        self.Category_Table.pack(fill=BOTH, expand=1)
        self.Category_Table.bind("<ButtonRelease-1>", self.get_data)

        self.show()

    def get_next_id(self):
        """Get the next available ID starting from 1"""
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            # Get all existing IDs
            cur.execute("SELECT CID FROM Category ORDER BY CID")
            rows = cur.fetchall()
            
            if not rows:
                return 1
            
            # Convert to list of integers
            ids = [row[0] for row in rows]
            
            # Find the first gap in sequence
            for i in range(1, len(ids) + 2):
                if i not in ids:
                    return i
                    
            return len(ids) + 1
        finally:
            con.close()

    def add(self):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            if self.var_Name.get() == "":
                messagebox.showerror("Error", "Category Name must be required", parent=self.root)
            else:
                cur.execute("SELECT * FROM Category WHERE Name=?", (self.var_Name.get(),))
                row = cur.fetchone()
                if row is not None:
                    messagebox.showerror("Error", "Category already present, try different", parent=self.root)
                else:
                    # Get the next available ID
                    next_id = self.get_next_id()
                    
                    # Insert with calculated ID
                    cur.execute("INSERT INTO Category (CID, Name) VALUES(?, ?)", (next_id, self.var_Name.get()))
                    con.commit()
                    messagebox.showinfo("Success", "Category added successfully", parent=self.root)
                    self.show()
                    self.var_Name.set("")  # Clear the entry field
        except Exception as ex:
            messagebox.showerror("Error", f"Error due to: {str(ex)}", parent=self.root)
        finally:
            con.close()

    def show(self):
        con = sqlite3.connect(database=r'Possystem.db')
        cur = con.cursor()
        try:
            cur.execute("SELECT * FROM Category ORDER BY CID")
            rows = cur.fetchall()
            self.Category_Table.delete(*self.Category_Table.get_children())
            for row in rows:
                self.Category_Table.insert('', END, values=row)
        except Exception as ex:
            messagebox.showerror("Error", f"Error loading data: {str(ex)}", parent=self.root)
        finally:
            con.close()

    def get_data(self, ev):
        try:
            selected_item = self.Category_Table.selection()[0]
            row = self.Category_Table.item(selected_item, 'values')
            if row:
                self.var_CatID.set(row[0])
                self.var_Name.set(row[1])
        except IndexError:
            pass

    def delete(self):
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            if not self.var_CatID.get():
                messagebox.showerror("Error", "Please select a Category to delete", parent=self.root)
            else:
                cur.execute("SELECT * FROM Category WHERE CID=?", (self.var_CatID.get(),))
                row = cur.fetchone()
                if row is None:
                    messagebox.showerror("Error", "Category not found in database", parent=self.root)
                else:
                    op = messagebox.askyesno("Confirm", "Do you really want to delete this Category?", parent=self.root)
                    if op:
                        # Get the ID being deleted
                        delete_id = int(self.var_CatID.get())
                        
                        # Delete the record
                        cur.execute("DELETE FROM Category WHERE CID=?", (delete_id,))
                        
                        # Get all records with higher IDs
                        cur.execute("SELECT CID FROM Category WHERE CID > ? ORDER BY CID", (delete_id,))
                        higher_ids = cur.fetchall()
                        
                        # Decrement all higher IDs by 1
                        for old_id in higher_ids:
                            new_id = old_id[0] - 1
                            cur.execute("UPDATE Category SET CID = ? WHERE CID = ?", (new_id, old_id[0]))
                        
                        con.commit()
                        messagebox.showinfo("Delete", "Category deleted successfully", parent=self.root)
                        self.show()
                        self.var_CatID.set("")
                        self.var_Name.set("")
        except Exception as ex:
            messagebox.showerror("Error", f"Error due to: {str(ex)}", parent=self.root)
        finally:
            con.close()

    def reorganize_ids(self):
        """Optional: Reorganize all IDs to be sequential (can be called periodically)"""
        con = sqlite3.connect(database='Possystem.db')
        cur = con.cursor()
        try:
            # Get all categories ordered by current ID
            cur.execute("SELECT Name FROM Category ORDER BY CID")
            categories = cur.fetchall()
            
            # Delete and reinsert with sequential IDs
            cur.execute("DELETE FROM Category")
            
            for i, category in enumerate(categories, 1):
                cur.execute("INSERT INTO Category (CID, Name) VALUES(?, ?)", (i, category[0]))
            
            con.commit()
            messagebox.showinfo("Success", "IDs reorganized successfully", parent=self.root)
            self.show()
        except Exception as ex:
            messagebox.showerror("Error", f"Error due to: {str(ex)}", parent=self.root)
        finally:
            con.close()


if __name__ == "__main__":
    root = Tk()
    obj = CategoryClass(root)
    root.mainloop()