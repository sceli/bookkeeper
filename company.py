import tkinter
from tkinter import ttk, messagebox
from create_company import CreateCompany
import csv
import sql_parameters
import main_window
import sqlcommand
import os


class Company(tkinter.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Company")
        self.config(padx=20, pady=20)
        self.resizable(False, False)

        self.company_listbox = tkinter.Listbox(self, width=30)
        self.company_listbox.grid(column=0, row=0)

        companies_file = 'companies.csv'

        if not os.path.exists(companies_file):
            # Create an empty CSV file if it doesn't exist
            with open(companies_file, 'w', newline=''):
                pass

        with open('companies.csv', 'r') as csv_file:
            csv_reader = csv.reader(csv_file)

            companies = []

            for line in csv_reader:
                companies.append(line[0])

            for _ in companies:
                self.company_listbox.insert("end", _)

        self.select_company_button = tkinter.Button(self, text="SELECT COMPANY", command=self.select_company,
                                                    width=20, padx=5, pady=5)
        self.select_company_button.grid(column=0, row=1)
        self.add_new_company_button = tkinter.Button(self, text="ADD NEW COMPANY", command=self.add_new_company,
                                                     width=20, padx=5, pady=5)
        self.add_new_company_button.grid(column=0, row=2)

    def select_company(self):
        if self.company_listbox.get("anchor") == '':
            tkinter.messagebox.showerror(title="ERROR", message="PLEASE SELECT A COMPANY")
        else:
            sql_parameters.database = self.company_listbox.get("anchor")
            self.master.destroy()
            window = main_window.MainWindow()
            window.mainloop()

    def add_new_company(self):
        CreateCompany(self)


class EditCompany(tkinter.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)

        sql_command = "SELECT * FROM company"

        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)
        records = execute['records']

        self.title('Edit company')
        self.config(padx=10, pady=10)
        self.resizable(False, False)
        self.grab_set()

        self.company_name_label = tkinter.Label(self, text='Company name', width=20)
        self.company_name_label.grid(column=0, row=0)
        self.company_name_entry = tkinter.Entry(self, width=60)
        self.company_name_entry.grid(column=1, row=0)
        self.company_name_entry.insert('end', records[0][0])

        self.tax_id_num_label = tkinter.Label(self, text='Tax ID number')
        self.tax_id_num_label.grid(column=0, row=1)
        self.tax_id_num_entry = tkinter.Entry(self, width=60)
        self.tax_id_num_entry.grid(column=1, row=1)
        self.tax_id_num_entry.insert('end', records[0][1])

        self.street_name_label = tkinter.Label(self, text='Street name')
        self.street_name_label.grid(column=0, row=2)
        self.street_name_entry = tkinter.Entry(self, width=60)
        self.street_name_entry.grid(column=1, row=2)
        self.street_name_entry.insert('end', records[0][2])

        self.street_number_label = tkinter.Label(self, text='Street number')
        self.street_number_label.grid(column=0, row=3)
        self.street_number_entry = tkinter.Entry(self, width=60)
        self.street_number_entry.grid(column=1, row=3)
        self.street_number_entry.insert('end', records[0][3])

        self.zip_code_label = tkinter.Label(self, text='ZIP code')
        self.zip_code_label.grid(column=0, row=4)
        self.zip_code_entry = tkinter.Entry(self, width=60)
        self.zip_code_entry.grid(column=1, row=4)
        self.zip_code_entry.insert('end', records[0][4])

        self.city_label = tkinter.Label(self, text='City')
        self.city_label.grid(column=0, row=5)
        self.city_entry = tkinter.Entry(self, width=60)
        self.city_entry.grid(column=1, row=5)
        self.city_entry.insert('end', records[0][5])

        self.country_label = tkinter.Label(self, text='Country')
        self.country_label.grid(column=0, row=6)
        self.country_entry = tkinter.Entry(self, width=60)
        self.country_entry.grid(column=1, row=6)
        self.country_entry.insert('end', records[0][6])

        self.country_code_label = tkinter.Label(self, text='Country code')
        self.country_code_label.grid(column=0, row=7)
        self.country_code_entry = tkinter.Entry(self, width=60)
        self.country_code_entry.grid(column=1, row=7)
        self.country_code_entry.insert('end', records[0][7])

        # Bank accounts tree
        column_names = ['bank_account_name', 'bank_account', 'show_on_invoice']
        self.bank_accounts_tree = ttk.Treeview(self, columns=column_names, show='headings', height=5,
                                               selectmode='browse')
        column = 0
        for _ in column_names:
            self.bank_accounts_tree.heading(column_names[column], text=f'{column_names[column]}')
            column += 1

        if records[0][8] is None:
            pass
        else:
            self.bank_accounts = eval(execute['records'][0][8])
            record = 0
            for _ in self.bank_accounts:
                self.bank_accounts_tree.insert('', tkinter.END, values=self.bank_accounts[record])
                record += 1

        # Adjust column width
        self.bank_accounts_tree.column(column_names[0], width=120)
        self.bank_accounts_tree.column(column_names[1], width=250)
        self.bank_accounts_tree.column(column_names[2], width=120)

        self.bank_accounts_tree.grid(column=1, row=8, columnspan=2, rowspan=3)

        self.add_account_button = tkinter.Button(self, text='Add account',
                                                 command=self.add_account_button_command, width=15)
        self.add_account_button.grid(column=0, row=8)
        self.edit_account_button = tkinter.Button(self, text='Edit account',
                                                  command=self.edit_account_button_command, width=15)
        self.edit_account_button.grid(column=0, row=9)
        self.delete_account_button = tkinter.Button(self, text='Delete account',
                                                    command=self.delete_account_button_command, width=15)
        self.delete_account_button.grid(column=0, row=10)

        self.save_button = tkinter.Button(self, text="Save changes", command=self.save_changes)
        self.save_button.grid(column=2, row=11)

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

        self.show_on_invoice_label = tkinter.Label(self.add_bank_account_win, text='Show on invoice')
        self.show_on_invoice_label.grid(column=0, row=2)
        self.checked_state = tkinter.BooleanVar()
        self.show_on_invoice_checkbutton = ttk.Checkbutton(self.add_bank_account_win, variable=self.checked_state)
        self.show_on_invoice_checkbutton.grid(column=1, row=2, sticky='w')

        self.add_bank_account_button = tkinter.Button(self.add_bank_account_win, text='Save',
                                                      command=self.add_bank_account_command)
        self.add_bank_account_button.grid(column=1, row=3)

    def add_bank_account_command(self):
        """Add bank account to treeview"""
        bank_acc_name = self.bank_account_name_entry.get()
        bank_acc_number = self.bank_account_number_entry.get()
        show_on_invoice = self.checked_state.get()

        if bank_acc_name == '' or bank_acc_number == '':
            tkinter.messagebox.showerror(title="ERROR", message="Fill all entries")
        else:
            values = [bank_acc_name, bank_acc_number, show_on_invoice]
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
            self.checked_state.set(selected[2])
            self.add_bank_account_button.config(command=self.update_bank_account)

    def update_bank_account(self):
        """Update bank account"""
        selected = self.bank_accounts_tree.focus()
        self.bank_accounts_tree.set(selected, column="bank_account_name", value=self.bank_account_name_entry.get())
        self.bank_accounts_tree.set(selected, column="bank_account", value=self.bank_account_number_entry.get())
        self.bank_accounts_tree.set(selected, column="show_on_invoice",
                                    value='True' if self.checked_state.get() == 1 else 'False')
        self.add_bank_account_win.destroy()

    def delete_account_button_command(self):
        """Delete bank account"""
        if self.selected_bank_account() == '':
            pass
        else:
            answer = tkinter.messagebox.askyesno(title="WARNING", message="Delete bank account?",
                                                 parent=self)
            if answer:
                selected = self.bank_accounts_tree.focus()
                self.bank_accounts_tree.delete(selected)

    def save_changes(self):
        """Saves company changes"""
        # Get bank accounts from treeview, replace ' to "
        bank_accounts_list = []
        for item in self.bank_accounts_tree.get_children():
            values = self.bank_accounts_tree.item(item)["values"]
            bank_accounts_list.append(str(tuple(values)).replace("'", '"'))
        bank_accounts = str(bank_accounts_list).replace("'", '')

        sql_command = f"UPDATE company " \
                      f"SET " \
                      f"company_name='{self.company_name_entry.get()}', " \
                      f"tax_id_num='{self.tax_id_num_entry.get()}', " \
                      f"street='{self.street_name_entry.get()}', " \
                      f"street_num='{self.street_number_entry.get()}', " \
                      f"zip_code='{self.zip_code_entry.get()}', " \
                      f"city='{self.city_entry.get()}', " \
                      f"country='{self.country_entry.get()}', " \
                      f"country_code='{self.country_code_entry.get()}', " \
                      f"bank_accounts='{bank_accounts}' "

        # Connect with SQL database
        conn = sqlcommand.SqlCommand()
        conn.sql_execute(sql_command)

        # Refresh customers tree
        self.destroy()

        tkinter.messagebox.showinfo(title="INFO", message="Updated successfully")
