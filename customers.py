import tkinter
from tkinter import ttk, messagebox
import sqlcommand


class Customers(tkinter.Toplevel):

    def __init__(self, parent):
        """Customers main window"""
        super().__init__(parent)

        self.title("Customers")
        self.resizable(False, False)

        # Customers tree Frame
        self.customers_frame = tkinter.Frame(self)
        self.customers_frame.grid(column=0, row=0)

        self.cust_tree_scroll = tkinter.Scrollbar(self.customers_frame)
        self.cust_tree_scroll.grid(column=1, row=0, sticky='ns')

        # Options Frame
        self.options_frame = tkinter.Frame(self)
        self.options_frame.grid(column=1, row=0, sticky='n')

        self.view_details_button = tkinter.Button(self.options_frame, text="View details",
                                                  command=self.view_details,
                                                  pady=15, padx=15, width=20)
        self.view_details_button.grid(column=0, row=0)

        self.edit_customer_button = tkinter.Button(self.options_frame, text="Edit customer",
                                                   command=self.edit_customer,
                                                   pady=15, padx=15, width=20)
        self.edit_customer_button.grid(column=0, row=1)

        self.add_new_customer_button = tkinter.Button(self.options_frame, text='Add new customer',
                                                      command=self.add_new_customer,
                                                      pady=15, padx=15, width=20)
        self.add_new_customer_button.grid(column=0, row=2)

        self.delete_customer_button = tkinter.Button(self.options_frame, text='Delete customer',
                                                     command=self.delete_customer,
                                                     pady=15, padx=15, width=20)
        self.delete_customer_button.grid(column=0, row=3)

        # Searchbar
        self.search_entry = tkinter.Entry(self.options_frame, width=20)
        self.search_entry.bind('<Return>', self.search)
        self.search_entry.grid(column=0, row=4, pady=(50, 5))

        self.search_button = tkinter.Button(self.options_frame, text="search", command=lambda: self.search(event=None))
        self.search_button.grid(column=0, row=5)

        self.customers_treeview()

    def customers_treeview(self):
        """Create customers treeview"""
        # Connect with SQL database
        sql_command = f"SELECT cust_id, cust_name, tax_id_num FROM customers WHERE " \
                      f"cust_name ILIKE '%{self.search_entry.get()}%' " \
                      f"OR tax_id_num LIKE '{self.search_entry.get()}%' " \
                      f"OR REPLACE(tax_id_num, '-','') LIKE '{self.search_entry.get()}%' " \
                      f"OR cust_id={int(self.search_entry.get()) if self.search_entry.get().isdigit() else 'Null'} " \
                      f"ORDER BY cust_name"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)

        column_names = execute['column_names']
        self.customer_tree = ttk.Treeview(self.customers_frame, columns=column_names, show='headings', height=35,
                                          yscrollcommand=self.cust_tree_scroll.set)
        self.cust_tree_scroll.config(command=self.customer_tree.yview)

        column = 0
        for _ in column_names:
            self.customer_tree.heading(column_names[column], text=f'{column_names[column]}')
            column += 1

        # Adjust column width
        self.customer_tree.column(column_names[0], width=100)
        self.customer_tree.column(column_names[1], width=450)
        self.customer_tree.column(column_names[2], width=150)

        self.customer_tree.grid(column=0, row=0)

        records = execute['records']

        record = 0
        for _ in records:
            self.customer_tree.insert('', tkinter.END, values=records[record])
            record += 1

    def search(self, event):
        try:
            self.customers_treeview()
        except Exception:
            pass

    def selected_customer(self):
        """Take selected customer"""
        selected = self.customer_tree.focus()
        cust = self.customer_tree.item(selected).get('values')
        return cust

    def customer_window(self):
        """Customer default window"""
        self.customer_win = tkinter.Toplevel(padx=10, pady=10)
        self.customer_win.grab_set()
        self.customer_win.resizable(False, False)

        self.cust_id_label = tkinter.Label(self.customer_win, text="Customer ID", width=20)
        self.cust_id_label.grid(column=0, row=0)
        self.cust_id_entry = tkinter.Entry(self.customer_win, width=60)
        self.cust_id_entry.grid(column=1, row=0, columnspan=2)

        self.cust_name_label = tkinter.Label(self.customer_win, text="Customer Name")
        self.cust_name_label.grid(column=0, row=1)
        self.cust_name_entry = tkinter.Entry(self.customer_win, width=60)
        self.cust_name_entry.grid(column=1, row=1, columnspan=2)

        self.tax_id_num_label = tkinter.Label(self.customer_win, text="Tax ID Number")
        self.tax_id_num_label.grid(column=0, row=2)
        self.tax_id_num_entry = tkinter.Entry(self.customer_win, width=60)
        self.tax_id_num_entry.grid(column=1, row=2, columnspan=2)

        self.street_label = tkinter.Label(self.customer_win, text="Street name")
        self.street_label.grid(column=0, row=3)
        self.street_entry = tkinter.Entry(self.customer_win, width=60)
        self.street_entry.grid(column=1, row=3, columnspan=2)

        self.street_num_label = tkinter.Label(self.customer_win, text="Street number")
        self.street_num_label.grid(column=0, row=4)
        self.street_num_entry = tkinter.Entry(self.customer_win, width=60)
        self.street_num_entry.grid(column=1, row=4, columnspan=2)

        self.zip_code_label = tkinter.Label(self.customer_win, text="ZIP code")
        self.zip_code_label.grid(column=0, row=5)
        self.zip_code_entry = tkinter.Entry(self.customer_win, width=60)
        self.zip_code_entry.grid(column=1, row=5, columnspan=2)

        self.city_label = tkinter.Label(self.customer_win, text="City")
        self.city_label.grid(column=0, row=6)
        self.city_entry = tkinter.Entry(self.customer_win, width=60)
        self.city_entry.grid(column=1, row=6, columnspan=2)

        self.country_label = tkinter.Label(self.customer_win, text="Country")
        self.country_label.grid(column=0, row=7)
        self.country_entry = tkinter.Entry(self.customer_win, width=60)
        self.country_entry.grid(column=1, row=7, columnspan=2)

        self.country_code_label = tkinter.Label(self.customer_win, text="Country code")
        self.country_code_label.grid(column=0, row=8)
        self.country_code_entry = tkinter.Entry(self.customer_win, width=60)
        self.country_code_entry.grid(column=1, row=8, columnspan=2)

        self.email_label = tkinter.Label(self.customer_win, text="E-mail")
        self.email_label.grid(column=0, row=9)
        self.email_entry = tkinter.Entry(self.customer_win, width=60)
        self.email_entry.grid(column=1, row=9, columnspan=2)

        self.phone_label = tkinter.Label(self.customer_win, text="Phone")
        self.phone_label.grid(column=0, row=10)
        self.phone_entry = tkinter.Entry(self.customer_win, width=60)
        self.phone_entry.grid(column=1, row=10, columnspan=2)

        # Bank accounts tree
        column_names = ['bank_account_name', 'bank_account']
        self.bank_accounts_tree = ttk.Treeview(self.customer_win, columns=column_names, show='headings', height=5,
                                               selectmode='browse')
        column = 0
        for _ in column_names:
            self.bank_accounts_tree.heading(column_names[column], text=f'{column_names[column]}')
            column += 1

        # Adjust column width
        self.bank_accounts_tree.column(column_names[0], width=120)
        self.bank_accounts_tree.column(column_names[1], width=250)

        self.bank_accounts_tree.grid(column=1, row=11, columnspan=2, rowspan=3)

        self.add_account_button = tkinter.Button(self.customer_win, text='Add account',
                                                 command=self.add_account_button_command, width=15)
        self.add_account_button.grid(column=0, row=11)
        self.edit_account_button = tkinter.Button(self.customer_win, text='Edit account',
                                                  command=self.edit_account_button_command, width=15)
        self.edit_account_button.grid(column=0, row=12)
        self.delete_account_button = tkinter.Button(self.customer_win, text='Delete account',
                                                    command=self.delete_account_button_command,width=15)
        self.delete_account_button.grid(column=0, row=13)

    def selected_bank_account(self):
        """Take selected bank account from tree"""
        selected = self.bank_accounts_tree.focus()
        self.selected_bank_acc = self.bank_accounts_tree.item(selected).get('values')
        return self.selected_bank_acc

    def add_account_button_command(self):
        """Open new window to add new bank account"""
        self.add_bank_account_win = tkinter.Toplevel(padx=10, pady=10)
        self.add_bank_account_win.title('Add new bank account')
        self.add_bank_account_win.grab_set()
        self.add_bank_account_win.resizable(False, False)

        # Inputs
        self.bank_account_name_label = tkinter.Label(self.add_bank_account_win, text='Bank account name')
        self.bank_account_name_label.grid(column=0, row=0)
        self.bank_account_name_entry = tkinter.Entry(self.add_bank_account_win, width=40)
        self.bank_account_name_entry.grid(column=1, row=0)

        self.bank_account_number_label = tkinter.Label(self.add_bank_account_win, text='Bank account number')
        self.bank_account_number_label.grid(column=0, row=1)
        self.bank_account_number_entry = tkinter.Entry(self.add_bank_account_win, width=40)
        self.bank_account_number_entry.grid(column=1, row=1)

        self.add_bank_account_button = tkinter.Button(self.add_bank_account_win, text='Save',
                                                      command=self.add_bank_account_command)
        self.add_bank_account_button.grid(column=1, row=2)

    def add_bank_account_command(self):
        """Add bank account to treeview"""
        bank_acc_name = self.bank_account_name_entry.get()
        bank_acc_number = self.bank_account_number_entry.get()

        if bank_acc_name == '' or bank_acc_number == '':
            tkinter.messagebox.showerror(title="ERROR", message="Fill all entries")
        else:
            values = [bank_acc_name, bank_acc_number]
            self.bank_accounts_tree.insert('', tkinter.END, values=values)
        self.add_bank_account_win.destroy()

    def edit_account_button_command(self):
        """Edit bank account"""
        if self.selected_bank_account() == '':
            pass
        else:
            selected = self.selected_bank_account()
            self.add_account_button_command()
            self.bank_account_name_entry.insert('end', selected[0])
            self.bank_account_number_entry.insert('end', selected[1])
            self.add_bank_account_button.config(command=self.update_bank_account)

    def update_bank_account(self):
        """Update bank account"""
        selected = self.bank_accounts_tree.focus()
        self.bank_accounts_tree.set(selected, column="bank_account_name", value=self.bank_account_name_entry.get())
        self.bank_accounts_tree.set(selected, column="bank_account", value=self.bank_account_number_entry.get())
        self.add_bank_account_win.destroy()

    def delete_account_button_command(self):
        """Delete bank account"""
        if self.selected_bank_account() == '':
            pass
        else:
            answer = tkinter.messagebox.askyesno(title="WARNING", message="Delete bank account?",
                                                 parent=self.customer_win)
            if answer:
                selected = self.bank_accounts_tree.focus()
                self.bank_accounts_tree.delete(selected)

    def view_details(self):
        """Open new window to view customer details"""
        if self.selected_customer() == '':
            pass
        else:
            # Connect with SQL database
            conn = sqlcommand.SqlCommand()
            execute = conn.sql_execute(f'SELECT * FROM customers WHERE cust_id={self.selected_customer()[0]}')

            # Open customer window
            self.customer_window()
            self.customer_win.title("Customer view")

            # Insert customer data
            self.cust_id_entry.insert('end', execute['records'][0][0])
            self.cust_name_entry.insert('end', execute['records'][0][1])
            self.tax_id_num_entry.insert('end', execute['records'][0][2])
            self.street_entry.insert('end', execute['records'][0][3])
            self.street_num_entry.insert('end', execute['records'][0][4])
            self.zip_code_entry.insert('end', execute['records'][0][5])
            self.city_entry.insert('end', execute['records'][0][6])
            self.country_entry.insert('end', execute['records'][0][7])
            self.country_code_entry.insert('end', execute['records'][0][8])
            self.email_entry.insert('end', execute['records'][0][9])
            self.phone_entry.insert('end', execute['records'][0][10])

            # Set to readonly state
            self.cust_id_entry.config(state='readonly')
            self.cust_name_entry.config(state='readonly')
            self.tax_id_num_entry.config(state='readonly')
            self.street_entry.config(state='readonly')
            self.street_num_entry.config(state='readonly')
            self.zip_code_entry.config(state='readonly')
            self.city_entry.config(state='readonly')
            self.country_entry.config(state='readonly')
            self.country_code_entry.config(state='readonly')
            self.email_entry.config(state='readonly')
            self.phone_entry.config(state='readonly')
            self.add_account_button.config(state='disabled')
            self.edit_account_button.config(state='disabled')
            self.delete_account_button.config(state='disabled')

            if execute['records'][0][11] is None:
                pass
            else:
                self.bank_accounts = eval(execute['records'][0][11])
                record = 0
                for _ in self.bank_accounts:
                    self.bank_accounts_tree.insert('', tkinter.END, values=self.bank_accounts[record])
                    record += 1

    def edit_customer(self):
        """Open new window to edit customer details"""
        if self.selected_customer() == '':
            pass
        else:
            # Connect with SQL database
            conn = sqlcommand.SqlCommand()
            execute = conn.sql_execute(f'SELECT * FROM customers WHERE cust_id={self.selected_customer()[0]}')

            # Open customer window
            self.customer_window()
            self.customer_win.title("Customer edit")

            # Insert customer data
            self.cust_id_entry.insert('end', execute['records'][0][0])
            self.cust_name_entry.insert('end', execute['records'][0][1])
            self.tax_id_num_entry.insert('end', execute['records'][0][2])
            self.street_entry.insert('end', execute['records'][0][3])
            self.street_num_entry.insert('end', execute['records'][0][4])
            self.zip_code_entry.insert('end', execute['records'][0][5])
            self.city_entry.insert('end', execute['records'][0][6])
            self.country_entry.insert('end', execute['records'][0][7])
            self.country_code_entry.insert('end', execute['records'][0][8])
            self.email_entry.insert('end', execute['records'][0][9])
            self.phone_entry.insert('end', execute['records'][0][10])

            if execute['records'][0][11] is None:
                pass
            else:
                self.bank_accounts = eval(execute['records'][0][11])
                record = 0
                for _ in self.bank_accounts:
                    self.bank_accounts_tree.insert('', tkinter.END, values=self.bank_accounts[record])
                    record += 1

            # Set to readonly state
            self.cust_id_entry.config(state='readonly')

            # Add Save button
            self.save_button = tkinter.Button(self.customer_win, text="Save changes", command=self.save_changes)
            self.save_button.grid(column=2, row=14)

    def save_changes(self):
        """Save changes in customer details"""
        # Get bank accounts from treeview, replace ' to "
        bank_accounts_list = []
        for item in self.bank_accounts_tree.get_children():
            values = self.bank_accounts_tree.item(item)["values"]
            bank_accounts_list.append(str(tuple(values)).replace("'", '"'))
        bank_accounts = str(bank_accounts_list).replace("'", '')

        sql_command = f"UPDATE customers " \
                      f"SET " \
                      f"cust_name='{self.cust_name_entry.get()}', " \
                      f"tax_id_num='{self.tax_id_num_entry.get()}', " \
                      f"street='{self.street_entry.get()}', " \
                      f"street_num='{self.street_num_entry.get()}', " \
                      f"zip_code='{self.zip_code_entry.get()}', " \
                      f"city='{self.city_entry.get()}', " \
                      f"country='{self.country_entry.get()}', " \
                      f"country_code='{self.country_code_entry.get()}', " \
                      f"email='{self.email_entry.get()}', " \
                      f"phone='{self.phone_entry.get()}', " \
                      f"bank_accounts='{bank_accounts}' " \
                      f"WHERE cust_id={self.selected_customer()[0]}"

        # Connect with SQL database
        conn = sqlcommand.SqlCommand()
        conn.sql_execute(sql_command)

        # Refresh customers tree
        self.refresh_customer_tree()
        self.customer_win.destroy()

        tkinter.messagebox.showinfo(title="INFO", message="Updated successfully",
                                    parent=self)

    def add_new_customer(self):
        """Open new window to add new customer"""
        self.customer_window()
        self.customer_win.title("Add new customer")

        # Set to readonly state
        self.cust_id_entry.configure(state='readonly')

        self.add_customer_button = tkinter.Button(self.customer_win, text="Add customer", command=self.add_customer)
        self.add_customer_button.grid(column=2, row=14)

    def add_customer(self):
        """Add new customer"""
        # Ask if add customer
        answer = tkinter.messagebox.askyesno(title="WARNING", message="Add customer?", parent=self.customer_win)
        if answer:
            # Get bank accounts from treeview, replace ' to "
            bank_accounts_list = []
            for item in self.bank_accounts_tree.get_children():
                values = self.bank_accounts_tree.item(item)["values"]
                bank_accounts_list.append(str(tuple(values)).replace("'", '"'))
            bank_accounts = str(bank_accounts_list).replace("'", '')

            sql_command = f"INSERT INTO customers(cust_name, tax_id_num, street, street_num, zip_code, city, " \
                          f"country, country_code, email, phone, bank_accounts) " \
                          f"VALUES" \
                          f"('{self.cust_name_entry.get()}', '{self.tax_id_num_entry.get()}', " \
                          f"'{self.street_entry.get()}', '{self.street_num_entry.get()}', " \
                          f"'{self.zip_code_entry.get()}', '{self.city_entry.get()}', " \
                          f"'{self.country_entry.get()}', '{self.country_code_entry.get()}', " \
                          f"'{self.email_entry.get()}', '{self.phone_entry.get()}', '{bank_accounts}')"

            # Connect with SQL database
            conn = sqlcommand.SqlCommand()
            conn.sql_execute(sql_command)

            # Refresh customers tree
            self.refresh_customer_tree()
            self.customer_win.destroy()

    def delete_customer(self):
        """Delete customer"""
        if self.selected_customer() == '':
            pass
        else:
            sql_command = f"DELETE FROM customers WHERE cust_id='{self.selected_customer()[0]}'"
            answer = tkinter.messagebox.askyesno(title="WARNING", message=f"Delete {self.selected_customer()[1]}?",
                                                 parent=self)
            if answer:
                # Connect to sql database to delete account
                conn = sqlcommand.SqlCommand()
                conn.sql_execute(sql_command)

                # Refresh customers tree
                self.refresh_customer_tree()

    def refresh_customer_tree(self):
        """Refresh customer tree"""
        self.customer_tree.delete(*self.customer_tree.get_children())
        self.customers_treeview()
