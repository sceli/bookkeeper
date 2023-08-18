import tkinter
from tkinter import messagebox, ttk
import sqlcommand


class ChartOfAccounts(tkinter.Toplevel):

    def __init__(self, parent):
        """Chart of accounts main window"""
        super().__init__(parent)

        self.title("Chart of accounts")
        self.resizable(False, False)

        # Create chart of accounts Frame
        self.coa_frame = tkinter.Frame(self)
        self.coa_frame.grid(column=0, row=0)

        self.coa_tree_scroll = tkinter.Scrollbar(self.coa_frame)
        self.coa_tree_scroll.grid(column=1, row=0, sticky='ns')

        # Create options Frame
        self.coa_options = tkinter.Frame(self)
        self.coa_options.grid(column=1, row=0, sticky='n')

        # Buttons
        self.add_new_account_button = tkinter.Button(self.coa_options, text='Add new account',
                                                     command=self.add_new_account,
                                                     pady=15, padx=15, width=20)
        self.add_new_account_button.grid(column=0, row=0)

        self.edit_account_name_button = tkinter.Button(self.coa_options, text="Edit account",
                                                         command=self.edit_account,
                                                         pady=15, padx=15, width=20)
        self.edit_account_name_button.grid(column=0, row=1)

        self.delete_account_button = tkinter.Button(self.coa_options, text='Delete account',
                                                    command=self.delete_account,
                                                    pady=15, padx=15, width=20)
        self.delete_account_button.grid(column=0, row=2)

        # Searchbar
        self.search_entry = tkinter.Entry(self.coa_options, width=20)
        self.search_entry.bind('<Return>', self.search)
        self.search_entry.grid(column=0, row=3, pady=(50, 5))

        self.search_button = tkinter.Button(self.coa_options, text="search", command=lambda: self.search(event=None))
        self.search_button.grid(column=0, row=4)

        self.coa_treeview()

    def coa_treeview(self):
        """Create chart of accounts treeview"""
        self.sql_command = f"SELECT * FROM chart_of_accounts WHERE " \
                           f"account_num LIKE '{self.search_entry.get()}%' " \
                           f"OR account_name ILIKE '%{self.search_entry.get()}%' " \
                           f"ORDER BY account_num"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(self.sql_command)

        column_names = execute['column_names']
        self.coa_tree = ttk.Treeview(self.coa_frame, columns=column_names, show='headings', height=35,
                                     selectmode='browse', yscrollcommand=self.coa_tree_scroll.set)
        self.coa_tree_scroll.config(command=self.coa_tree.yview)

        column = 0
        for _ in column_names:
            self.coa_tree.heading(column_names[column], text=column_names[column])
            column += 1

        # Adjust column width
        self.coa_tree.column(column_names[0], width=100)
        self.coa_tree.column(column_names[1], width=450)
        self.coa_tree.column(column_names[2], width=80, anchor='center')
        self.coa_tree.column(column_names[3], width=80, anchor='center')
        self.coa_tree.column(column_names[4], width=80, anchor='center')

        self.coa_tree.grid(column=0, row=0)

        records = execute['records']

        # Replace True and False booleans to checkmarks
        values = []
        for item in records:
            lst = list(item)
            lst[2] = '✔' if lst[2] is True else '-'
            lst[3] = '✔' if lst[3] is True else '-'
            lst[4] = '✔' if lst[4] is True else '-'
            values.append(lst)

        # Insert records
        record = 0
        for _ in records:
            self.coa_tree.insert('', tkinter.END, values=values[record])
            record += 1

    def search(self, event):
        try:
            self.coa_treeview()
        except Exception:
            pass

    def selected_account_num(self):
        """Take selected account number"""
        selected = self.coa_tree.focus()
        self.selected_acc_num = self.coa_tree.item(selected).get('values')[0]
        if len(str(self.selected_acc_num)) == 2:
            self.selected_acc_num = '0' + str(self.selected_acc_num)
        return self.selected_acc_num

    def selected_account(self):
        """Take selected account details"""
        selected = self.coa_tree.focus()
        self.selected_acc = self.coa_tree.item(selected).get('values')
        return self.selected_acc

    def add_new_account(self):
        """Open new window to create new account"""
        self.add_new_account_window = tkinter.Toplevel()
        self.add_new_account_window.title('Add new account')
        self.add_new_account_window.grab_set()
        self.add_new_account_window.resizable(False, False)

        # Inputs
        self.account_num_label = tkinter.Label(self.add_new_account_window,
                                               text="Account number", width=20)
        self.account_num_label.grid(column=0, row=0)
        self.account_num_entry = tkinter.Entry(self.add_new_account_window, width=30)
        self.account_num_entry.grid(column=1, row=0)

        self.account_name_label = tkinter.Label(self.add_new_account_window,
                                                text="Account name", width=20)
        self.account_name_label.grid(column=0, row=1)
        self.account_name_entry = tkinter.Entry(self.add_new_account_window, width=30)
        self.account_name_entry.grid(column=1, row=1)

        self.customer_settlement_label = tkinter.Label(self.add_new_account_window,
                                                       text="Customer settlement", width=20)
        self.customer_settlement_label.grid(column=0, row=2)
        self.customer_settlement_state = tkinter.BooleanVar()
        self.customer_settlement_entry = tkinter.Checkbutton(self.add_new_account_window,
                                                             variable=self.customer_settlement_state)
        self.customer_settlement_entry.grid(column=1, row=2, sticky='w')

        self.vat_settlement_label = tkinter.Label(self.add_new_account_window,
                                                  text="Vat settlement", width=20)
        self.vat_settlement_label.grid(column=0, row=3)
        self.vat_settlement_state = tkinter.BooleanVar()
        self.vat_settlement_entry = tkinter.Checkbutton(self.add_new_account_window,
                                                        variable=self.vat_settlement_state)
        self.vat_settlement_entry.grid(column=1, row=3, sticky='w')

        self.nominal_account_label = tkinter.Label(self.add_new_account_window,
                                                  text="Nominal account", width=20)
        self.nominal_account_label.grid(column=0, row=4)
        self.nominal_account_state = tkinter.BooleanVar()
        self.nominal_account_entry = tkinter.Checkbutton(self.add_new_account_window,
                                                        variable=self.nominal_account_state)
        self.nominal_account_entry.grid(column=1, row=4, sticky='w')

        self.add_account_button = tkinter.Button(self.add_new_account_window,
                                                 text="Add account", command=self.add_account_command)
        self.add_account_button.grid(column=1, row=5)

    def add_account_command(self):
        """Connect to sql database and add account"""
        sql_command = f"INSERT INTO chart_of_accounts(account_num, account_name, " \
                      f"customer_settlement, vat_settlement, nominal_account) " \
                      f"VALUES" \
                      f"('{self.account_num_entry.get()}', '{self.account_name_entry.get()}', " \
                      f"{self.customer_settlement_state.get()}, " \
                      f"{self.vat_settlement_state.get()}, {self.nominal_account_state.get()})"

        # Connect to sql database to add account
        conn = sqlcommand.SqlCommand()
        conn.sql_execute(sql_command)

        self.add_new_account_window.destroy()

        # Refresh chart of accounts tree
        self.refresh_coa_tree()

    def edit_account(self):
        """Open new window to edit account"""
        try:
            selected = self.selected_account()
            self.add_new_account()
            self.add_new_account_window.title('Edit account')

            # Fill with data
            self.account_num_entry.insert('end', selected[0] if len(str(selected[0])) >= 3 else f"0{selected[0]}")
            self.account_name_entry.insert('end', selected[1])
            self.customer_settlement_state.set(True if selected[2] == '✔' else False)
            self.vat_settlement_state.set(True if selected[3] == '✔' else False)
            self.nominal_account_state.set(True if selected[4] == '✔' else False)
            self.add_account_button.config(text="Save changes", command=self.edit_account_command)
        except:
            self.add_new_account_window.destroy()
            tkinter.messagebox.showerror(title="ERROR", message="Select account", parent=self)

    def edit_account_command(self):
        """Connect to sql database to save account changes"""
        # Ask if save changes
        answer = tkinter.messagebox.askyesno(title="WARNING", message="Save changes?",
                                             parent=self.add_new_account_window)
        if answer:
            sql_command = f"UPDATE chart_of_accounts " \
                          f"SET " \
                          f"account_num='{self.account_num_entry.get()}', " \
                          f"account_name='{self.account_name_entry.get()}', " \
                          f"customer_settlement={self.customer_settlement_state.get()}, " \
                          f"vat_settlement={self.vat_settlement_state.get()}, " \
                          f"nominal_account={self.nominal_account_state.get()} " \
                          f"WHERE account_num='{self.selected_account_num()}'"

            # Connect to sql database to delete account
            conn = sqlcommand.SqlCommand()
            conn.sql_execute(sql_command)

            # Refresh chart of accounts tree
            self.refresh_coa_tree()
            self.add_new_account_window.destroy()

    def delete_account(self):
        """Connect to sql database and delete account"""
        try:
            self.selected_account_num()
            # Ask if delete account
            answer = tkinter.messagebox.askyesno(title="WARNING",
                                                 message=f"Delete '{self.selected_account_num()}' account?",
                                                 parent=self)
            if answer:
                sql_command = f"DELETE FROM chart_of_accounts WHERE account_num='{self.selected_account_num()}'"

                # Connect to sql database to delete account
                conn = sqlcommand.SqlCommand()
                conn.sql_execute(sql_command)

                # Refresh chart of accounts tree
                self.refresh_coa_tree()
        except:
            tkinter.messagebox.showerror(title="ERROR", message="Select account", parent=self)

    def refresh_coa_tree(self):
        """Refresh chart of accounts tree"""
        self.coa_tree.delete(*self.coa_tree.get_children())
        self.coa_treeview()
