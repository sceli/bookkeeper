import tkinter
from tkinter import ttk, messagebox
import sqlcommand
import vat_rates
import chart_of_accounts


class InvoiceIndexes(tkinter.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title('Invoice Indexes')
        self.resizable(False, False)

        # Invoice indexes tree Frame
        self.invoice_indexes_frame = tkinter.Frame(self)
        self.invoice_indexes_frame.grid(column=0, row=0)

        self.invoice_indexes_tree_scroll = tkinter.Scrollbar(self.invoice_indexes_frame)
        self.invoice_indexes_tree_scroll.grid(column=1, row=0, sticky='ns')

        # Options Frame
        self.options_frame = tkinter.Frame(self)
        self.options_frame.grid(column=1, row=0, sticky='n')

        self.add_inv_index_button = tkinter.Button(self.options_frame, text="Add invoice index",
                                                   command=self.add_inv_index,
                                                   pady=5, padx=5, width=20)
        self.add_inv_index_button.grid(column=0, row=0)

        self.edit_inv_index_button = tkinter.Button(self.options_frame, text="Edit invoice index",
                                                   command=self.edit_inv_index,
                                                   pady=5, padx=5, width=20)
        self.edit_inv_index_button.grid(column=0, row=1)

        self.delete_inv_index_button = tkinter.Button(self.options_frame, text="Delete invoice index",
                                                   command=self.delete_inv_index,
                                                   pady=5, padx=5, width=20)
        self.delete_inv_index_button.grid(column=0, row=2)

        # Searchbar
        self.search_entry = tkinter.Entry(self.options_frame, width=20)
        self.search_entry.bind('<Return>', self.search)
        self.search_entry.grid(column=0, row=3, pady=(50, 5))

        self.search_button = tkinter.Button(self.options_frame, text="search", command=lambda: self.search(event=None))
        self.search_button.grid(column=0, row=4)

        self.invoice_indexes_treeview()

    def invoice_indexes_treeview(self):
        """Create invoice indexes treeview"""
        # Connect with SQL database
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(f"SELECT * FROM invoice_indexes WHERE "
                                   f"inv_index_id ILIKE '%{self.search_entry.get()}%' "
                                   f"OR inv_index_description ILIKE '%{self.search_entry.get()}%' "
                                   f"OR sales_account_num LIKE '{self.search_entry.get()}%' "
                                   f"OR purchase_account_num LIKE '{self.search_entry.get()}%' "
                                   f"OR vat_id ILIKE '%{self.search_entry.get()}%' "
                                   f"ORDER BY inv_index_description")

        column_names = execute['column_names']
        self.invoice_indexes_tree = ttk.Treeview(self.invoice_indexes_frame, columns=column_names,
                                                 show='headings', height=35)
        column = 0
        for _ in column_names:
            self.invoice_indexes_tree.heading(column_names[column], text=f'{column_names[column]}')
            column += 1
        self.invoice_indexes_tree_scroll.config(command=self.invoice_indexes_tree.yview)

        # Adjust column width
        self.invoice_indexes_tree.column(column_names[0], width=170)
        self.invoice_indexes_tree.column(column_names[1], width=250)
        self.invoice_indexes_tree.column(column_names[2], width=100)
        self.invoice_indexes_tree.column(column_names[3], width=100)
        self.invoice_indexes_tree.column(column_names[4], width=120)

        self.invoice_indexes_tree.grid(column=0, row=0)

        records = execute['records']
        record = 0
        for _ in records:
            self.invoice_indexes_tree.insert('', tkinter.END, values=records[record])
            record += 1

    def search(self, event):
        try:
            self.invoice_indexes_treeview()
        except Exception:
            pass

    def selected_inv_index(self):
        """Take selected invoice index"""
        selected = self.invoice_indexes_tree.focus()
        inv_index = self.invoice_indexes_tree.item(selected).get('values')
        return inv_index

    def add_inv_index(self):
        """Open new window to add new invoice index"""
        self.add_inv_index_window = tkinter.Toplevel()
        self.add_inv_index_window.title("Add invoice index")
        self.add_inv_index_window.config(padx=5, pady=5)
        self.add_inv_index_window.grab_set()
        self.add_inv_index_window.resizable(False, False)

        # Inputs
        self.inv_index_id_label = tkinter.Label(self.add_inv_index_window, text="Invoice index ID", width=30)
        self.inv_index_id_label.grid(column=0, row=0)
        self.inv_index_id_entry = tkinter.Entry(self.add_inv_index_window, width=30)
        self.inv_index_id_entry.grid(column=1, row=0)

        self.inv_index_desc_label = tkinter.Label(self.add_inv_index_window, text="Invoice index description", width=30)
        self.inv_index_desc_label.grid(column=0, row=1)
        self.inv_index_desc_entry = tkinter.Entry(self.add_inv_index_window, width=30)
        self.inv_index_desc_entry.grid(column=1, row=1)

        self.sales_account_num_label = tkinter.Label(self.add_inv_index_window, text="Sales account number", width=30)
        self.sales_account_num_label.grid(column=0, row=2)
        self.sales_account_num_entry = tkinter.Button(self.add_inv_index_window, text='',
                                                      command=self.select_account,
                                                      width=25, highlightbackground='grey', borderwidth=1,
                                                      relief='sunken', anchor='w')
        self.sales_account_num_entry.bind('<Button-1>', self.clicked_button)
        self.sales_account_num_entry.grid(column=1, row=2)

        self.purchase_account_num_label = tkinter.Label(self.add_inv_index_window, text="Purchase account number",
                                                        width=30)
        self.purchase_account_num_label.grid(column=0, row=3)
        self.purchase_account_num_entry = tkinter.Button(self.add_inv_index_window, text='',
                                                         command=self.select_account,
                                                         width=25, highlightbackground='grey', borderwidth=1,
                                                         relief='sunken', anchor='w')
        self.purchase_account_num_entry.bind('<Button-1>', self.clicked_button)
        self.purchase_account_num_entry.grid(column=1, row=3)

        self.vat_rate_label = tkinter.Label(self.add_inv_index_window, text="Vat rate", width=30)
        self.vat_rate_label.grid(column=0, row=4)
        self.vat_rate_entry = tkinter.Button(self.add_inv_index_window, text='', command=self.select_vat, width=25,
                                             highlightbackground='grey', borderwidth=1, relief='sunken', anchor='w')
        self.vat_rate_entry.grid(column=1, row=4)

        self.add_index_button = tkinter.Button(self.add_inv_index_window,
                                               text="Add invoice index", command=self.add_inv_index_command)
        self.add_index_button.grid(column=1, row=5)

        # Right mouse click menu
        self.r_click_menu = tkinter.Menu(self, tearoff=False)
        self.r_click_menu.add_command(label="Delete", command=self.delete_choice)

        # bind name of widget with function
        self.sales_account_num_entry.bind('<Button-3>', self.clicked_right_button)
        self.purchase_account_num_entry.bind('<Button-3>', self.clicked_right_button)
        self.vat_rate_entry.bind('<Button-3>', self.clicked_right_button)

    def add_inv_index_command(self):
        """Add to invoice_indexes in sql database"""
        # Ask if add invoice index
        answer = tkinter.messagebox.askyesno(title="WARNING", message="Add invoice index?",
                                             parent=self.add_inv_index_window)
        if answer:
            sales_account_num = 'null' if self.sales_account_num_entry['text'] == '' \
                else f"'{self.sales_account_num_entry['text']}'"
            purchase_account_num = 'null' if self.purchase_account_num_entry['text'] == '' \
                else f"'{self.purchase_account_num_entry['text']}'"
            sql_command = f"INSERT INTO invoice_indexes(inv_index_id, inv_index_description, sales_account_num, " \
                          f"purchase_account_num, vat_id) " \
                          f"VALUES" \
                          f"('{self.inv_index_id_entry.get()}', '{self.inv_index_desc_entry.get()}', " \
                          f"{sales_account_num}, " \
                          f"{purchase_account_num}, " \
                          f"'{self.vat_rate_entry['text']}')"

            # Connect with SQL database
            conn = sqlcommand.SqlCommand()
            conn.sql_execute(sql_command)

            # Refresh customers tree
            self.refresh_invoice_indexes_tree()
            self.add_inv_index_window.destroy()

    def clicked_button(self, event):
        """Return clicked button"""
        self.clicked_btn = event.widget

    def clicked_right_button(self, event):
        """Return clicked right button"""
        self.clicked_right_btn = event.widget
        self.r_click_menu.tk_popup(event.x_root, event.y_root)

    def edit_inv_index(self):
        try:
            self.add_inv_index()
            self.add_inv_index_window.title("Edit invoice index")

            self.inv_index_id_entry.insert('end', self.selected_inv_index()[0])
            self.inv_index_desc_entry.insert('end', self.selected_inv_index()[1])
            if self.selected_inv_index()[2] == 'None':
                pass
            else:
                self.sales_account_num_entry.config(text=self.selected_inv_index()[2])
            if self.selected_inv_index()[3] == 'None':
                pass
            else:
                self.purchase_account_num_entry.config(text=self.selected_inv_index()[3])
            self.vat_rate_entry.config(text=self.selected_inv_index()[4])
            self.add_index_button.config(text="Save changes", command=self.save_changes)
        except:
            self.add_inv_index_window.destroy()
            tkinter.messagebox.showerror(title="ERROR", message="Select index", parent=self)

    def save_changes(self):
        """Save changes in invoice index details"""
        sales_account_num = 'null' if self.sales_account_num_entry['text'] == '' \
            else f"'{self.sales_account_num_entry['text']}'"
        purchase_account_num = 'null' if self.purchase_account_num_entry['text'] == '' \
            else f"'{self.purchase_account_num_entry['text']}'"
        sql_command = f"UPDATE invoice_indexes " \
                      f"SET " \
                      f"inv_index_id='{self.inv_index_id_entry.get()}', " \
                      f"inv_index_description='{self.inv_index_desc_entry.get()}', " \
                      f"sales_account_num={sales_account_num}, " \
                      f"purchase_account_num={purchase_account_num}, " \
                      f"vat_id='{self.vat_rate_entry['text']}' " \
                      f"WHERE inv_index_id='{self.selected_inv_index()[0]}'"

        # Connect with SQL database
        conn = sqlcommand.SqlCommand()
        conn.sql_execute(sql_command)

        # Refresh customers tree
        self.refresh_invoice_indexes_tree()
        self.add_inv_index_window.destroy()

    def delete_choice(self):
        """Delete choice from button entry widgets"""
        self.r_clicked_button = self.clicked_right_btn
        self.r_clicked_button.config(text='')

    def select_account(self):
        """Open new window with account to choose"""
        self.account_window = chart_of_accounts.ChartOfAccounts(self)
        self.account_window.grab_set()
        self.selected_account_button = self.clicked_btn
        add_account_button = tkinter.Button(self.account_window, text='Select account',
                                             command=self.select_account_command, font=30)
        add_account_button.grid(column=0, row=1, columnspan=2)

    def select_account_command(self):
        """Get selected account from account window"""
        self.acc_details = self.account_window.selected_account()
        self.acc_num = self.account_window.selected_account_num()
        self.selected_account_button.config(text=f"{self.acc_num}")
        self.account_window.destroy()

    def select_vat(self):
        """Open new window with vat rate to choose"""
        self.vat_window = vat_rates.VatRates(self)
        self.vat_window.grab_set()
        add_vat_button = tkinter.Button(self.vat_window, text='Select vat rate',
                                        command=self.select_vat_rate_command, font=30)
        add_vat_button.grid(row=1, column=0)

    def select_vat_rate_command(self):
        """Get selected vat rate from vat rate window"""
        self.vat_details = self.vat_window.selected_vat_rate()
        self.vat_rate_entry.config(text=f'{self.vat_details[0]}')
        self.vat_window.destroy()

    def delete_inv_index(self):
        """Delete customer"""
        try:
            sql_command = f"DELETE FROM invoice_indexes WHERE inv_index_id='{self.selected_inv_index()[0]}'"
            answer = tkinter.messagebox.askyesno(title="WARNING",
                                                 message=f"Delete index: '{self.selected_inv_index()[0]}'?",
                                                 parent=self)
            if answer:
                # Connect to sql database to delete index
                conn = sqlcommand.SqlCommand()
                conn.sql_execute(sql_command)

                # Refresh invoice indexes tree
                self.refresh_invoice_indexes_tree()
        except:
            tkinter.messagebox.showerror(title="ERROR", message="Select index", parent=self)

    def refresh_invoice_indexes_tree(self):
        """Refresh customer tree"""
        self.invoice_indexes_tree.delete(*self.invoice_indexes_tree.get_children())
        self.invoice_indexes_treeview()
