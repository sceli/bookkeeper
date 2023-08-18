import tkinter
from tkinter import ttk, messagebox
import sqlcommand
import chart_of_accounts


class VatRates(tkinter.Toplevel):

    def __init__(self, parent):
        """Vat rates main window"""
        super().__init__(parent)

        self.title("Vat rates")
        self.resizable(False, False)

        # Create vat rates Frame
        self.vat_rates_frame = tkinter.Frame(self)
        self.vat_rates_frame.grid(column=0, row=0)

        self.vat_rates_treeview()

        # Create options Frame
        self.vat_rates_options = tkinter.Frame(self)
        self.vat_rates_options.grid(column=1, row=0, sticky='n')

        self.add_vat_rate_button = tkinter.Button(self.vat_rates_options, text="Add vat rate",
                                                  command=self.add_vat_rate,
                                                  pady=5, padx=5, width=20)
        self.add_vat_rate_button.grid(column=0, row=0)

        self.delete_vat_rate_button = tkinter.Button(self.vat_rates_options, text="Delete vat rate",
                                                     command=self.delete_vat_rate,
                                                     pady=5, padx=5, width=20)
        self.delete_vat_rate_button.grid(column=0, row=1)

    def vat_rates_treeview(self):
        """Create vat rates treeview"""
        # Connect to sql database to add vat rates
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute('''SELECT * FROM vat_rates ORDER BY vat_rate DESC''')

        column_names = execute['column_names']
        self.vat_rates_tree = ttk.Treeview(self.vat_rates_frame, columns=column_names, show='headings', height=10)
        column = 0
        for _ in column_names:
            self.vat_rates_tree.heading(column_names[column], text=f'{column_names[column]}')
            column += 1
        # Adjust column width
        self.vat_rates_tree.column(column_names[0], width=120)
        self.vat_rates_tree.column(column_names[1], width=100)
        self.vat_rates_tree.column(column_names[2], width=100)
        self.vat_rates_tree.column(column_names[3], width=100)

        self.vat_rates_tree.grid(column=0, row=0)

        records = execute['records']
        record = 0
        for _ in records:
            self.vat_rates_tree.insert('', tkinter.END, values=records[record])
            record += 1

    def selected_vat_rate(self):
        selected = self.vat_rates_tree.focus()
        vr = self.vat_rates_tree.item(selected).get('values')
        return vr

    def clicked_button(self, event):
        """Return clicked button"""
        self.clicked_btn = event.widget

    def clicked_right_button(self, event):
        """Return clicked right button"""
        self.clicked_right_btn = event.widget
        self.r_click_menu.tk_popup(event.x_root, event.y_root)

    def add_vat_rate(self):
        """Open new window to add vat rate"""
        self.add_vat_rate_window = tkinter.Toplevel()
        self.add_vat_rate_window.title("Add vat rate")
        self.add_vat_rate_window.grab_set()
        self.add_vat_rate_window.resizable(False, False)

        # Inputs
        self.vat_id_label = tkinter.Label(self.add_vat_rate_window, text="VAT ID", width=25)
        self.vat_id_label.grid(column=0, row=0)
        self.vat_id_entry = tkinter.Entry(self.add_vat_rate_window, width=20)
        self.vat_id_entry.grid(column=1, row=0)

        self.vat_rate_label = tkinter.Label(self.add_vat_rate_window, text="VAT rate", width=25)
        self.vat_rate_label.grid(column=0, row=1)
        self.vat_rate_entry = tkinter.Entry(self.add_vat_rate_window, width=20)
        self.vat_rate_entry.grid(column=1, row=1)

        self.sales_account_num_label = tkinter.Label(self.add_vat_rate_window, text="Sales account number", width=25)
        self.sales_account_num_label.grid(column=0, row=2)
        self.sales_account_num_entry = tkinter.Button(self.add_vat_rate_window, text='',
                                                      command=self.select_account,
                                                      width=25, highlightbackground='grey', borderwidth=1,
                                                      relief='sunken', anchor='w')
        self.sales_account_num_entry.bind('<Button-1>', self.clicked_button)
        self.sales_account_num_entry.grid(column=1, row=2)

        self.purchase_account_num_label = tkinter.Label(self.add_vat_rate_window, text="Purchase account number", width=25)
        self.purchase_account_num_label.grid(column=0, row=3)
        self.purchase_account_num_entry = tkinter.Button(self.add_vat_rate_window, text='',
                                                         command=self.select_account,
                                                         width=25, highlightbackground='grey', borderwidth=1,
                                                         relief='sunken', anchor='w')
        self.purchase_account_num_entry.bind('<Button-1>', self.clicked_button)
        self.purchase_account_num_entry.grid(column=1, row=3)



        self.add_rate_button = tkinter.Button(self.add_vat_rate_window,
                                              text="Add vat rate", command=self.add_vat_rate_command)
        self.add_rate_button.grid(column=1, row=4)

        # Right mouse click menu
        self.r_click_menu = tkinter.Menu(self, tearoff=False)
        self.r_click_menu.add_command(label="Delete", command=self.delete_choice)

        # bind name of widget with function
        self.sales_account_num_entry.bind('<Button-3>', self.clicked_right_button)
        self.purchase_account_num_entry.bind('<Button-3>', self.clicked_right_button)
        self.vat_rate_entry.bind('<Button-3>', self.clicked_right_button)

    def add_vat_rate_command(self):
        """Connect to sql database and add vat rate"""
        try:
            int(self.vat_rate_entry.get())
            sql_command = f"INSERT INTO vat_rates(vat_id, vat_rate, sales_account_num, purchase_account_num) " \
                          f"VALUES" \
                          f"('{self.vat_id_entry.get()}', '{self.vat_rate_entry.get()}'," \
                          f"'{self.sales_account_num_entry['text']}', '{self.purchase_account_num_entry['text']}')"

            # Connect to sql database to add account
            conn = sqlcommand.SqlCommand()
            conn.sql_execute(sql_command)

            self.add_vat_rate_window.destroy()

            # Refresh chart of accounts tree
            self.refresh_vat_rates_tree()
        except ValueError:
            tkinter.messagebox.showerror(title="ERROR", message="Input integer in VAT rate entry",
                                         parent=self.add_vat_rate_window)

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

    def delete_choice(self):
        """Delete choice from button entry widgets"""
        self.r_clicked_button = self.clicked_right_btn
        self.r_clicked_button.config(text='')

    def delete_vat_rate(self):
        """Delete vat rate"""
        try:
            sql_command = f"DELETE FROM vat_rates WHERE vat_id='{self.selected_vat_rate()[0]}'"
            answer = tkinter.messagebox.askyesno(title="WARNING", message=f"Delete {self.selected_vat_rate()[0]}?",
                                                 parent=self)

            if answer:
                deleted_vat_rate = self.selected_vat_rate()[0]
                # Connect to sql database to delete account
                conn = sqlcommand.SqlCommand()
                conn.sql_execute(sql_command)

                # Refresh customers tree
                self.refresh_vat_rates_tree()
                tkinter.messagebox.showinfo(title="INFO", message=f"{deleted_vat_rate} deleted successfully",
                                            parent=self)

        except:
            tkinter.messagebox.showerror(title="ERROR", message="Select vat rate", parent=self)

    def refresh_vat_rates_tree(self):
        """Refresh customer tree"""
        self.vat_rates_tree.delete(*self.vat_rates_tree.get_children())
        self.vat_rates_treeview()
