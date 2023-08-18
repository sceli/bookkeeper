import tkinter
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import psycopg2
import customers
import invoice_indexes
import sql_parameters
import sqlcommand
import chart_of_accounts
import re
from functools import partial
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import subprocess


# Register fonts
pdfmetrics.registerFont(TTFont("Arial", "arial.ttf", "UTF-8"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "arialbd.ttf", "UTF-8"))


class Invoice(tkinter.Toplevel):

    def __init__(self, parent, invoice_type):
        """Invoice document"""
        super().__init__(parent)

        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute("SELECT * FROM invoice_settings ORDER BY invoice_type DESC")
        self.inv_details = execute['records']

        # Specify document type
        self.invoice_type = invoice_type
        self.inv_type_short = [item for item in self.inv_details if f'{item[0]}' == self.invoice_type][0][1]
        self.cust_account = [item for item in self.inv_details if f'{item[0]}' == self.invoice_type][0][2]

        # Configure window
        self.title(self.invoice_type)
        self.config(padx=15, pady=15)
        self.resizable(False, False)

        self.inv_type_label = tkinter.Label(self, text=f'{self.invoice_type}', font=30)
        self.inv_type_label.grid(column=3, row=1, columnspan=2)

        # Entries
        self.doc_date_label = tkinter.Label(self, text="Document date")
        self.doc_date_label.grid(column=1, row=0)
        self.doc_date_entry = DateEntry(self, selectmode='day', locale='en_US', date_pattern='dd-mm-y')
        self.doc_date_entry.grid(column=1, row=1)

        self.vat_date_label = tkinter.Label(self, text="Vat date")
        self.vat_date_label.grid(column=2, row=0)
        self.vat_date_entry = DateEntry(self, selectmode='day', locale='en_US', date_pattern='dd-mm-y')
        self.vat_date_entry.grid(column=2, row=1)

        self.add_new_line_button = tkinter.Button(self, text='Add new line', command=self.add_line)
        self.add_new_line_button.grid(column=5, row=1)
        self.remove_last_line_button = tkinter.Button(self, text='Remove last line',
                                                      command=self.remove_line)
        self.remove_last_line_button.grid(column=6, row=1)

        self.customer_label = tkinter.Label(self, text="Customer")
        self.customer_label.grid(column=1, row=2)
        self.customer_entry = tkinter.Button(self, text='',
                                             command=self.select_customer, width=25, background='white',
                                             activebackground='white', borderwidth=1, relief='sunken', anchor='w')
        self.customer_entry.grid(column=2, row=2)

        self.invoice_number_label = tkinter.Label(self, text="Invoice number")
        self.invoice_number_label.grid(column=1, row=3)
        self.invoice_number_entry = tkinter.Entry(self, width=30)
        self.invoice_number_entry.grid(column=2, row=3)

        if self.invoice_type == "Cost Purchase Invoice":
            self.internal_inv_num_label = tkinter.Label(self, text="Internal inv num")
            self.internal_inv_num_label.grid(column=1, row=4)
            self.internal_inv_num_entry = tkinter.Entry(self, width=30, state='readonly')
            self.internal_inv_num_entry.grid(column=2, row=4)
        else:
            self.invoice_number_entry.config(state='readonly')

        self.space = tkinter.Canvas(self, height=10, width=0)
        self.space.grid(column=1, row=5)

        # Headers
        self.no_journal_label = tkinter.Label(self, width=3)
        self.no_journal_label.grid(column=0, row=6)
        self.index_label = tkinter.Label(self, text="Index", width=21)
        self.index_label.grid(column=1, row=6)
        self.description_label = tkinter.Label(self, text="Description", width=25)
        self.description_label.grid(column=2, row=6)
        self.account_label = tkinter.Label(self, text="Account", width=25)
        self.account_label.grid(column=3, row=6)
        self.net_value_label = tkinter.Label(self, text='NET Value', width=26)
        self.net_value_label.grid(column=4, row=6)
        self.vat_rate_label = tkinter.Label(self, text='Vat rate', width=27)
        self.vat_rate_label.grid(column=5, row=6)
        self.vat_amount_label = tkinter.Label(self, text='Vat amount', width=27)
        self.vat_amount_label.grid(column=6, row=6)

        # Set first row
        self.row = 7
        # Set first no
        self.no = 1

        # Bottom widget
        self.net_sum_value_label = tkinter.Label(self, text="Net value")
        self.net_sum_value_label.grid(column=4)
        self.net_value = tkinter.Label(self, text="0.00", anchor='e', width=16)
        self.net_value.grid(column=5)
        self.vat_sum_value_label = tkinter.Label(self, text="Vat value")
        self.vat_sum_value_label.grid(column=4)
        self.vat_value = tkinter.Label(self, text="0.00", anchor='e', width=16)
        self.vat_value.grid(column=5)
        self.gross_sum_value_label = tkinter.Label(self, text="Gross value")
        self.gross_sum_value_label.grid(column=4, pady=(0, 20))
        self.gross_value = tkinter.Label(self, text="0.00", anchor='e', width=16)
        self.gross_value.grid(column=5, pady=(0, 20))

        self.due_date_label = tkinter.Label(self, text="Due date")
        self.due_date_label.grid(column=4)
        self.due_date_entry = DateEntry(self, selectmode='day', locale='en_US', date_pattern='dd-mm-y')
        self.due_date_entry.grid(column=5)

        self.payment_method_label = tkinter.Label(self, text="Payment method")
        self.payment_method_label.grid(column=4)
        payment_methods = ('transfer', 'cash')
        self.payment_method_entry = ttk.Combobox(self, values=payment_methods, state='readonly')
        self.payment_method_entry.current(0)
        self.payment_method_entry.grid(column=5)

        self.post_button = tkinter.Button(self, text="Post in journal", command=self.post_in_journal)
        self.post_button.grid(column=6)

        # Add scrollbar
        self.frame = tkinter.Frame(self)
        self.frame.grid(column=0, row=7, columnspan=7)

        self.scrollbar = tkinter.Scrollbar(self.frame)
        self.scrollbar.grid(column=7, row=0, sticky='ns')

        self.canvas = tkinter.Canvas(self.frame, yscrollcommand=self.scrollbar.set, width=1111, height=387,
                                     highlightthickness=0, borderwidth=1, relief='groove')
        self.canvas.grid(column=0, row=0, columnspan=7)

        self.lines_frame = tkinter.Frame(self.canvas)
        self.lines_frame.grid(column=0, row=0, columnspan=7)

        self.lines_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.lines_frame, anchor='nw')

        self.canvas.config(yscrollcommand=self.scrollbar.set)

        self.scrollbar.config(command=self.canvas.yview)

        # List for all added lines
        self.no_label_list = []
        self.index_entry_list = []
        self.description_entry_list = []
        self.account_entry_list = []
        self.net_value_entry_list = []
        self.vat_rate_entry_list = []
        self.vat_amount_entry_list = []
        self.vat_rate_hidden_label_list = []

        self.list_of_str_var = []

        self.add_line()

        # Connect with SQL database
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute("SELECT * FROM vat_rates")
        self.vat_accounts = execute['records']

    def add_line(self):
        """Add new lines to post"""
        self.no_label = tkinter.Label(self.lines_frame, text=f'{self.no}', width=3)
        self.no_label.grid(column=0, row=self.row)
        self.no += 1

        self.index_entry = tkinter.Button(self.lines_frame, text='...', command=self.select_index, width=20,
                                          highlightbackground='grey', borderwidth=1, anchor='w')
        self.index_entry.grid(column=1, row=self.row)

        self.description_entry = tkinter.Entry(self.lines_frame, width=30)
        self.description_entry.grid(column=2, row=self.row)

        self.account_entry = tkinter.Entry(self.lines_frame, width=30, state='readonly', justify='right')
        self.account_entry.grid(column=3, row=self.row)

        self.amount_str_var = tkinter.StringVar()
        self.amount_str_var.set('0.00')
        self.net_value_entry = tkinter.Entry(self.lines_frame, textvariable=self.amount_str_var, width=30,
                                             justify='right')
        self.net_value_entry.grid(column=4, row=self.row)

        self.vat_rate_entry = tkinter.Entry(self.lines_frame, width=30, state='readonly', justify='right')
        self.vat_rate_entry.grid(column=5, row=self.row)

        self.vat_amount_entry = tkinter.Entry(self.lines_frame, width=30, state='readonly', justify='right')
        self.vat_amount_entry.grid(column=6, row=self.row)

        self.vat_rate_hidden_label = tkinter.Label(text='')
        self.vat_account_hidden_label = tkinter.Label(text='')

        # Set row for bottom widget
        self.net_sum_value_label.grid(row=self.row + 2)
        self.net_value.grid(row=self.row + 2)
        self.vat_sum_value_label.grid(row=self.row + 3)
        self.vat_value.grid(row=self.row + 3)
        self.gross_sum_value_label.grid(row=self.row + 4)
        self.gross_value.grid(row=self.row + 4)
        self.due_date_label.grid(row=self.row + 5)
        self.due_date_entry.grid(row=self.row + 5)
        self.payment_method_label.grid(row=self.row + 6)
        self.payment_method_entry.grid(row=self.row + 6)
        self.post_button.grid(row=self.row + 6)

        self.row += 2

        # bind name of widget with function
        self.index_entry.bind('<Button-1>', self.clicked_button)
        self.net_value_entry.bind('<FocusOut>', self.calculate_vat_value)

        # Append all created lines to list
        self.no_label_list.append(self.no_label)
        self.index_entry_list.append(self.index_entry)
        self.description_entry_list.append(self.description_entry)
        self.account_entry_list.append(self.account_entry)
        self.net_value_entry_list.append(self.net_value_entry)
        self.vat_rate_entry_list.append(self.vat_rate_entry)
        self.vat_amount_entry_list.append(self.vat_amount_entry)
        self.vat_rate_hidden_label_list.append(self.vat_rate_hidden_label)

        self.list_of_str_var.append(self.amount_str_var)

        for item in range(int(len(self.list_of_str_var))):
            self.list_of_str_var[item].trace('w', partial(self.entry_fill, self.net_value_entry_list[item]))

    def remove_line(self):
        """Remove last line to post"""
        if self.row > 10:
            self.no_label_list[-1].destroy()
            self.no_label_list.pop()
            self.index_entry_list[-1].destroy()
            self.index_entry_list.pop()
            self.description_entry_list[-1].destroy()
            self.description_entry_list.pop()
            self.account_entry_list[-1].destroy()
            self.account_entry_list.pop()
            self.net_value_entry_list[-1].destroy()
            self.net_value_entry_list.pop()
            self.vat_rate_entry_list[-1].destroy()
            self.vat_rate_entry_list.pop()
            self.vat_amount_entry_list[-1].destroy()
            self.vat_amount_entry_list.pop()
            self.vat_rate_hidden_label_list[-1].destroy()
            self.vat_rate_hidden_label_list.pop()
            self.list_of_str_var.pop()
            self.row -= 2
            self.no -= 1

    def clicked_button(self, event):
        """Return clicked button"""
        self.clicked_btn = event.widget

    def select_index(self):
        """Open new window with customer to choose"""
        self.index_window = invoice_indexes.InvoiceIndexes(self)
        self.index_window.grab_set()
        self.add_index_button = tkinter.Button(self.index_window, text='Select index',
                                               command=self.select_index_command, font=30)
        self.add_index_button.grid(column=0, row=1, columnspan=2)

    def select_index_command(self):
        """Fill row with selected index values"""
        selected = self.index_window.selected_inv_index()
        index = self.clicked_btn
        index.config(text=f'{selected[0]}')
        description = self.description_entry_list[self.index_entry_list.index(self.clicked_btn)]
        description.delete(0, 'end')
        description.insert('end', selected[1])
        account = self.account_entry_list[self.index_entry_list.index(self.clicked_btn)]
        account.config(state='normal')
        account.delete(0, 'end')
        if self.invoice_type == 'Service Sales Invoice':
            account.insert('end', selected[2])
        elif self.invoice_type == 'Cost Purchase Invoice':
            account.insert('end', selected[3])
        account.config(state='readonly')
        vat_rate = self.vat_rate_entry_list[self.index_entry_list.index(self.clicked_btn)]
        vat_rate.config(state='normal')
        vat_rate.delete(0, 'end')
        vat_rate.insert('end', selected[4])
        vat_rate.config(state='readonly')
        self.vat_rate_hidden = self.vat_rate_hidden_label_list[self.index_entry_list.index(self.clicked_btn)]
        self.vat_rate_hidden.config(text=[item for item in self.vat_accounts if item[0] == selected[4]][0][1])
        self.index_window.destroy()

    def calculate_vat_value(self, event):
        """Calculate Vat value"""
        net_entry = event.widget
        vat_label = self.vat_rate_hidden_label_list[self.net_value_entry_list.index(net_entry)]
        try:
            vat_amount = round(float(vat_label['text']) * float(net_entry.get().replace(' ', '')) / 100, 2)
            vat_amount_entry = self.vat_amount_entry_list[self.net_value_entry_list.index(net_entry)]
            vat_amount_entry.config(state='normal')
            vat_amount_entry.delete(0, 'end')
            vat_amount_entry.insert('end', '{:,.2f}'.format(vat_amount).replace(',', ' '))
            vat_amount_entry.config(state='readonly')
        except Exception:
            pass
        self.calculate_gross_value()

    def calculate_gross_value(self):
        """Calculate gross value"""
        lines = int(len(self.no_label_list))
        net_value = []
        vat_value = []

        for n in range(lines):
            net_value.append(self.net_value_entry_list[n].get())
            vat_value.append(self.vat_amount_entry_list[n].get())

        for item in range(len(net_value)):
            if net_value[item] == '':
                net_value[item] = 0
            else:
                net_value[item] = net_value[item].replace(' ', '')

        for item in range(len(vat_value)):
            if vat_value[item] == '':
                vat_value[item] = 0
            else:
                vat_value[item] = vat_value[item].replace(' ', '')
        net_sum = sum(list(map(float, net_value)))
        vat_sum = sum(list(map(float, vat_value)))
        gross_sum = net_sum + vat_sum
        self.net_value.config(text=f"{'{:,.2f}'.format(net_sum).replace(',', ' ')}")
        self.vat_value.config(text=f"{'{:,.2f}'.format(vat_sum).replace(',', ' ')}")
        self.gross_value.config(text=f"{'{:,.2f}'.format(gross_sum).replace(',', ' ')}")

    def select_customer(self):
        """Open new window with customer to choose"""
        self.customer_window = customers.Customers(self)
        self.customer_window.grab_set()
        add_customer_button = tkinter.Button(self.customer_window, text='Select customer',
                                             command=self.select_customer_command, font=30)
        add_customer_button.grid(column=0, row=1, columnspan=2)

    def select_customer_command(self):
        """Get selected customer from customer window"""
        self.cust_details = self.customer_window.selected_customer()
        self.customer_entry.config(text=f"{self.cust_details[0]} ~ {self.cust_details[1]}")
        self.customer_window.destroy()

    def entry_fill(self, entry, *args):
        """Format entry widget and returns digits with a thousand separator"""
        try:
            if len(entry.get()) >= 20:
                entry.delete(entry.index("end") - 1)
            else:
                result = re.sub(r'[^0-9]', '', entry.get())
                sep = '{:,.2f}'.format(float(result) / 100).replace(',', ' ')
                entry.delete(0, 'end')
                entry.insert('end', sep)
        except Exception:
            pass

    def post_in_journal(self):
        """Posts in journal in sql database, checks if all necessary fields are filled"""
        lines = int(len(self.no_label_list))

        # Calculate all vat rates again
        for n in range(lines):
            net_entry = self.net_value_entry_list[n]
            vat_label = self.vat_rate_hidden_label_list[self.net_value_entry_list.index(net_entry)]
            if net_entry.get() == '':
                pass
            else:
                try:
                    vat_amount = round(int(vat_label['text']) * float(str(net_entry.get()).replace(' ', '')) / 100, 2)
                    vat_amount_entry = self.vat_amount_entry_list[self.net_value_entry_list.index(net_entry)]
                    vat_amount_entry.config(state='normal')
                    vat_amount_entry.delete(0, 'end')
                    vat_amount_entry.insert('end', '{:,.2f}'.format(vat_amount).replace(',', ' '))
                    vat_amount_entry.config(state='readonly')
                except Exception:
                    pass

        cust_account = f"'{self.cust_account}'"
        doc_type = self.inv_type_short
        doc_date = self.doc_date_entry.get()
        description = []
        dt_account = []
        ct_account = []
        amount = []
        cust_id = self.customer_entry['text'][0:self.customer_entry['text'].rfind(" ~ ")]
        ext_doc_number = self.invoice_number_entry.get()
        vat_id = []
        vat_date = 'null' if self.vat_date_entry.get() == '' else f"'{self.vat_date_entry.get()}'"
        inv_index_id = []
        vat_value = []
        due_date = self.due_date_entry.get()
        payment_method = self.payment_method_entry.get()
        gross_value = self.gross_value['text'].replace(' ', '')

        for n in range(lines):
            inv_index_id.append(self.index_entry_list[n]['text'])
            description.append(self.description_entry_list[n].get())
            if self.invoice_type == 'Cost Purchase Invoice':
                dt_account.append(self.account_entry_list[n].get())
            elif self.invoice_type == 'Service Sales Invoice':
                ct_account.append(self.account_entry_list[n].get())
            amount.append(self.net_value_entry_list[n].get())
            vat_id.append(self.vat_rate_entry_list[n].get())
            vat_value.append(self.vat_amount_entry_list[n].get().replace(' ', ''))

        for item in range(len(dt_account)):
            if dt_account[item] == '':
                pass
            else:
                dt_account[item] = f"'{dt_account[item]}'"

        for item in range(len(ct_account)):
            if ct_account[item] == '':
                pass
            else:
                ct_account[item] = f"'{ct_account[item]}'"

        for item in range(len(amount)):
            if amount[item] == '':
                amount[item] = 0
            else:
                amount[item] = amount[item].replace(' ', '')

        for item in range(len(vat_id)):
            if vat_id[item] == '':
                vat_id[item] = 'null'
            else:
                vat_id[item] = f"'{vat_id[item]}'"

        empty_description = False
        empty_account = False
        empty_values = False
        for item in range(lines):
            if description[item] == '':
                empty_description = True
            if self.invoice_type == 'Service Sales Invoice':
                if ct_account[item] == '':
                    empty_account = True
            if self.invoice_type == 'Cost Purchase Invoice':
                if dt_account[item] == '':
                    empty_account = True
            if float(amount[item]) == 0:
                empty_values = True

        # Take doc number
        date_str = self.doc_date_entry.get()
        date = datetime.strptime(date_str, '%d-%m-%Y')
        month = date.strftime('%m')
        year = date.strftime('%Y')
        sql_take_number = f"SELECT doc_num FROM document_numbers WHERE " \
                          f"doc_name='{self.invoice_type}' AND doc_month={month} AND doc_year={year}"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_take_number)
        number = execute['records'][0][0]

        doc_number = f"{number}/{month}/{year}"

        # Check if everything is filled
        if self.customer_entry['text'] == '':
            tkinter.messagebox.showerror(title="ERROR", message="Missing customer", parent=self)
        elif empty_account is True:
            tkinter.messagebox.showerror(title="ERROR", message="Missing index", parent=self)
        elif empty_description is True:
            tkinter.messagebox.showerror(title="ERROR", message="Missing description", parent=self)
        elif empty_values is True:
            tkinter.messagebox.showerror(title="ERROR", message="Missing NET value", parent=self)
        else:
            if ext_doc_number == '':
                if self.invoice_type == 'Cost Purchase Invoice':
                    tkinter.messagebox.showerror(title="ERROR", message="Missing document number", parent=self)
                else:
                    ext_doc_number = doc_number

                # Update next doc number
                sql_update_number = f"UPDATE document_numbers SET " \
                                    f"doc_num = {number + 1} " \
                                    f"WHERE " \
                                    f"doc_name='{self.invoice_type}' AND doc_month={month} AND doc_year={year}"
                conn = sqlcommand.SqlCommand()
                conn.sql_execute(sql_update_number)

                # Create dictionary with vat sum for each rate
                vat_sum_dict = dict.fromkeys(vat_id, 0)
                for n in range(len(vat_id)):
                    for key in vat_sum_dict:
                        if key == vat_id[n]:
                            if vat_value[n] == '':
                                pass
                            else:
                                vat_sum_dict[vat_id[n]] += (float(vat_value[n]))

                insert_sql = f"INSERT INTO journal(doc_type, doc_date, description, dt_account_num, ct_account_num, " \
                             f"amount, cust_id, doc_number, int_doc_number, vat_id, vat_date, inv_index_id, " \
                             f"index_vat_value, inv_due_date, inv_payment_method)\n" \
                             f"VALUES\n" \
                             f"('{doc_type}', TO_DATE('{doc_date}', 'dd-mm-yyyy'), " \
                             f"'{doc_number} {self.invoice_type}', " \
                             f"{cust_account if self.invoice_type == 'Service Sales Invoice' else 'null'}, " \
                             f"{cust_account if self.invoice_type == 'Cost Purchase Invoice' else 'null'}, " \
                             f"{gross_value}, {cust_id}, '{ext_doc_number}', '{doc_number}', null, " \
                             f"TO_DATE({vat_date}, 'dd-mm-yyyy'), null, null, TO_DATE('{due_date}', 'dd-mm-yyyy')," \
                             f"'{payment_method}'), " \
                             f'\n'

                values_string = []
                for n in range(lines):
                    values_string.append(f"('{doc_type}', TO_DATE('{doc_date}', 'dd-mm-yyyy'), "
                                         f"'{description[n]}', "
                                         f"{dt_account[n] if self.invoice_type == 'Cost Purchase Invoice' else 'null'},"
                                         f"{ct_account[n] if self.invoice_type == 'Service Sales Invoice' else 'null'},"
                                         f"{amount[n]}, {cust_id}, '{ext_doc_number}', '{doc_number}', {vat_id[n]}, "
                                         f"TO_DATE({vat_date}, 'dd-mm-yyyy'), "
                                         f"'{inv_index_id[n]}', {vat_value[n]}, "
                                         f"TO_DATE('{due_date}', 'dd-mm-yyyy'), '{payment_method}'),\n")

                vat_string = []
                for key in vat_sum_dict:
                    vat_acc = [item for item in self.vat_accounts if f"'{item[0]}'" == key][0][2] \
                        if self.invoice_type == 'Service Sales Invoice' else \
                        [item for item in self.vat_accounts if f"'{item[0]}'" == key][0][3]
                    vat_account = f"'{vat_acc}'"
                    vat_string.append(f"('{doc_type}', TO_DATE('{doc_date}', 'dd-mm-yyyy'), "
                                      f"'{doc_number} {self.invoice_type}', "
                                      f"{vat_account if self.invoice_type == 'Cost Purchase Invoice' else 'null'}, "
                                      f"{vat_account if self.invoice_type == 'Service Sales Invoice' else 'null'}, "
                                      f"{'{:.2f}'.format(vat_sum_dict[key])}, "
                                      f"{cust_id}, '{ext_doc_number}', '{doc_number}', {key}, "
                                      f"TO_DATE({vat_date}, 'dd-mm-yyyy'), null, null, "
                                      f"TO_DATE('{due_date}', 'dd-mm-yyyy'), '{payment_method}'),\n")

                for values in range(lines):
                    insert_sql += values_string[values]

                for values in range(len(vat_string)):
                    insert_sql += vat_string[values]

                sql_command = f"{insert_sql[:-2]} RETURNING doc_number"

                # Connect to sql database to post data
                conn = None
                cur = None

                try:
                    conn = psycopg2.connect(
                        host=sql_parameters.hostname,
                        dbname=sql_parameters.database,
                        user=sql_parameters.username,
                        password=sql_parameters.pwd,
                        port=sql_parameters.port_id
                    )

                    conn.autocommit = True
                    cur = conn.cursor()
                    cur.execute(sql_command)
                    # Take document number
                    doc_number = cur.fetchone()[0]
                    self.invoice_number_entry.config(state='normal')
                    self.invoice_number_entry.insert('end', doc_number)
                    self.invoice_number_entry.config(state='readonly')

                except Exception as error:
                    is_correct = False
                    tkinter.messagebox.showerror(title="ERROR", message=f'{error}', parent=self)

                else:
                    is_correct = True

                finally:
                    if cur is not None:
                        cur.close()
                    if conn is not None:
                        conn.close()

                if is_correct is True:
                    answer = tkinter.messagebox.askyesno(title="Info", message="Document added. Print invoice?",
                                                         parent=self)
                    if answer:
                        self.generate_pdf()
                    self.close()

    def on_close(self, callback):
        self.callback = callback

    def close(self):
        self.callback()
        self.destroy()

    def generate_pdf(self):
        """Generate Invoice PDF file"""
        # Get company data
        sql_command = "SELECT * FROM company"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)
        company_data = execute['records'][0]

        company_name = company_data[0]
        company_tax_id_num = company_data[1]
        company_address = f"{company_data[2]} {company_data[3]}, {company_data[4]} {company_data[5]}, {company_data[6]}"
        bank_account = []
        bank_account_list = eval(company_data[8])
        for item in bank_account_list:
            if item[2] == 'True':
                bank_account.append(f"{item[0]}: {item[1]}")

        sql_command = f"SELECT * FROM customers " \
                      f"WHERE cust_id={self.customer_entry['text'][0:self.customer_entry['text'].rfind(' ~ ')]}"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)
        customer_data = execute['records'][0]

        customer_name = customer_data[1]
        customer_tax_id_num = customer_data[2]
        customer_address = f"{customer_data[3]} {customer_data[4]}, {customer_data[5]} {customer_data[6]}, " \
                           f"{customer_data[7]}"

        positions = []
        vat_dict = {}
        for n in range(len(self.no_label_list)):
            # Create positions tuples
            positions.append(tuple([self.description_entry_list[n].get(), self.net_value_entry_list[n].get(),
                                   f"{self.vat_rate_hidden_label_list[n]['text']}%",
                                    self.vat_amount_entry_list[n].get()]))
            # Create vat dictionary
            key = f"{self.vat_rate_hidden_label_list[n]['text']}%"
            value = float(self.vat_amount_entry_list[n].get().replace(' ', ''))
            if key in vat_dict:
                vat_dict[key] += value
            else:
                vat_dict[key] = value
        # Add a thousand separator in values
        for key in vat_dict:
            vat_dict[key] = '{:,.2f}'.format(vat_dict[key]).replace(',', ' ')

        # Generating an invoice in the 'temp' folder
        output_folder = os.path.join(os.getcwd(), "temp")
        pdf_filename = os.path.join(output_folder, "invoice.pdf")

        # Create a 'temp' folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        c = canvas.Canvas(pdf_filename, pagesize=A4)
        c.setFont("Arial", 10)

        # Heading
        c.setFont("Arial-Bold", 14)
        c.drawCentredString(A4[0] / 2, 780, f"Invoice {self.invoice_number_entry.get()}")
        c.setFont("Arial", 10)

        # Invoice details
        c.setFont("Arial-Bold", 10)
        c.drawString(50, 750, f"FROM:")
        c.setFont("Arial", 10)
        c.drawString(50, 730, f"{company_name}")
        c.drawString(50, 710, f"{company_tax_id_num}")
        c.drawString(50, 690, f"{company_address}")

        c.setFont("Arial-Bold", 10)
        c.drawString(50, 650, f"BILL TO:")
        c.setFont("Arial", 10)
        c.drawString(50, 630, f"{customer_name}")
        c.drawString(50, 610, f"{customer_tax_id_num}")
        c.drawString(50, 590, f"{customer_address}")

        c.drawRightString(545, 730, f"Invoice date: {self.doc_date_entry.get()}")
        c.drawRightString(545, 710, f"VAT date: {self.vat_date_entry.get()}")

        # Invoice item table
        c.setFont("Arial-Bold", 10)
        c.drawString(50, 540, "No.")
        c.drawString(70, 540, "Service description")
        c.drawRightString(385, 540, "Net amount")
        c.drawRightString(455, 540, "VAT rate")
        c.drawRightString(545, 540, "VAT amount")
        c.line(50, 535, A4[0] - 50, 535)

        c.setFont("Arial", 10)
        y = 520
        lp = 1
        for position in positions:
            service, net_amount, vat_rate, vat_amount = position
            c.drawString(50, y, str(lp))
            c.drawString(70, y, service)
            c.drawRightString(385, y, str(net_amount))
            c.drawRightString(455, y, str(vat_rate))
            c.drawRightString(545, y, str(vat_amount))
            y -= 20
            lp += 1

        # Bottom sum
        c.setFont("Arial-Bold", 10)
        c.drawString(380, y - 40, "Net sum:")
        c.drawRightString(545, y - 40, f"{self.net_value['text']}")
        n = 0
        for key in vat_dict:
            c.drawString(380, y - (60 + n), f"{key} VAT sum:")
            c.drawRightString(545, y - (60 + n), f"{vat_dict[key]}")
            n += 20
        c.drawString(380, y - (60 + n), "Gross sum:")
        c.drawRightString(545, y - (60 + n), f"{self.gross_value['text']}")

        # Due
        c.setFillColor('red')
        c.drawString(50, y - 40, f"Due date: {self.due_date_entry.get()}")
        c.setFillColor('black')
        c.drawString(50, y - 60, f"Payment method: {self.payment_method_entry.get()}")
        n = 0
        c.setFont("Arial", 9)
        for account in range(len(bank_account)):
            c.drawString(50, y - (90 + n), f"{bank_account[account]}")
            n += 15

        c.save()

        # Opening the PDF file
        subprocess.Popen([pdf_filename], shell=True)


class ViewInvoice(Invoice):

    def __init__(self, parent, invoice_type, journal_entry_date, doc_number, cust_id, cust_name):
        """Open new window with view invoice mode"""
        super().__init__(parent, invoice_type)

        self.journal_entry_date = journal_entry_date
        self.doc_number = doc_number
        self.cust_id = cust_id
        self.cust_name = cust_name

        sql_command = f"SELECT * FROM journal " \
                      f"WHERE journal_entry_date='{self.journal_entry_date}' " \
                      f"AND doc_number='{self.doc_number}' " \
                      f"AND cust_id={self.cust_id} " \
                      f"AND inv_index_id IS NOT NULL " \
                      f"ORDER BY no_journal ASC"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)
        records = execute['records']

        self.title('Invoice VIEW')
        self.doc_date_entry.set_date(records[0][3])
        self.doc_date_entry.config(state='disabled')
        self.vat_date_entry.set_date(records[0][12])
        self.vat_date_entry.config(state='disabled')
        self.due_date_entry.set_date(records[0][16])
        self.due_date_entry.config(state='disabled')
        self.payment_method_entry.set(records[0][17])
        self.add_new_line_button.configure(state='disabled')
        self.remove_last_line_button.configure(state='disabled')
        self.payment_method_entry.configure(state='disabled')
        self.customer_entry.configure(
            text=f"{self.cust_id} ~ {self.cust_name}", state='disabled', background='SystemButtonFace')
        self.invoice_number_entry.configure(state='normal')
        self.invoice_number_entry.insert('end', records[0][9])
        self.invoice_number_entry.configure(state='readonly')
        if self.invoice_type == 'Cost Purchase Invoice':
            self.internal_inv_num_entry.configure(state='normal')
            self.internal_inv_num_entry.insert('end', records[0][10])
            self.internal_inv_num_entry.configure(state='readonly')

        for n in range(len(records)):
            if n > 0:
                self.add_line()

        for n in range(len(records)):
            # Fill all lines with data from original invoice
            self.index_entry_list[n].configure(text=records[n][14], state='disabled')
            self.description_entry_list[n].insert('end', string=records[n][4])
            self.description_entry_list[n].configure(state='readonly')
            self.account_entry_list[n].configure(state='normal')
            if self.invoice_type == 'Cost Purchase Invoice':
                self.account_entry_list[n].insert('end', string=records[n][5])
            if self.invoice_type == 'Service Sales Invoice':
                self.account_entry_list[n].insert('end', string=records[n][6])
            self.account_entry_list[n].configure(state='readonly')
            self.net_value_entry_list[n].insert('end', string=records[n][7])
            self.net_value_entry_list[n].configure(state='readonly')
            self.vat_rate_entry_list[n].configure(state='normal')
            self.vat_rate_entry_list[n].insert('end', string=records[n][11])
            self.vat_rate_entry_list[n].configure(state='readonly')
            self.vat_amount_entry_list[n].configure(state='normal')
            self.vat_amount_entry_list[n].insert(
                'end', string='{:,.2f}'.format(records[n][15]).replace(',', ' '))
            self.vat_amount_entry_list[n].configure(state='readonly')
            self.vat_rate_hidden_label_list[n].config(
                text=[item for item in self.vat_accounts
                      if item[0] == self.vat_rate_entry_list[n].get()][0][1])
        self.calculate_gross_value()

        if self.invoice_type == 'Cost Purchase Invoice':
            self.post_button.configure(state='disabled')
        if self.invoice_type == 'Service Sales Invoice':
            self.post_button.configure(text='Print invoice', command=self.generate_pdf)


class EditInvoice(Invoice):

    def __init__(self, parent, invoice_type, journal_entry_date, doc_number, cust_id, cust_name):
        """Open new window with edit invoice mode"""
        super().__init__(parent, invoice_type)

        self.title('Invoice EDIT')

        self.journal_entry_date = journal_entry_date
        self.doc_number = doc_number
        self.cust_id = cust_id
        self.cust_name = cust_name

        self.sql_command = f"SELECT * FROM journal " \
                           f"WHERE journal_entry_date='{self.journal_entry_date}' " \
                           f"AND doc_number='{self.doc_number}' " \
                           f"AND cust_id={self.cust_id} " \
                           f"AND inv_index_id IS NOT NULL " \
                           f"ORDER BY no_journal ASC"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(self.sql_command)
        records = execute['records']

        self.orig_doc_date = records[0][3]
        self.orig_vat_date = records[0][12]

        self.doc_date_entry.set_date(records[0][3])
        self.vat_date_entry.set_date(records[0][12])
        self.due_date_entry.set_date(records[0][16])
        self.payment_method_entry.set(records[0][17])
        self.add_new_line_button.configure(state='disabled')
        self.remove_last_line_button.configure(state='disabled')
        self.post_button.configure(text='Save changes', command=self.save_inv_edit)
        self.customer_entry.configure(
            text=f"{self.cust_id} ~ {self.cust_name}")
        self.invoice_number_entry.configure(state='normal')
        self.invoice_number_entry.insert('end', records[0][9])
        self.invoice_number_entry.configure(state='readonly')
        if self.invoice_type == 'Cost Purchase Invoice':
            self.invoice_number_entry.configure(state='normal')
            self.internal_inv_num_entry.configure(state='normal')
            self.internal_inv_num_entry.insert('end', records[0][10])
            self.internal_inv_num_entry.configure(state='readonly')

        for n in range(len(records)):
            if n > 0:
                self.add_line()

        for n in range(len(records)):
            # Fill all lines with data from original invoice
            self.index_entry_list[n].configure(text=records[n][14], state='disabled')
            self.description_entry_list[n].insert('end', string=records[n][4])
            self.description_entry_list[n].configure(state='readonly')
            self.account_entry_list[n].configure(state='normal')
            self.account_entry_list[n].configure(state='normal')
            if self.invoice_type == 'Cost Purchase Invoice':
                self.account_entry_list[n].insert('end', string=records[n][5])
            if self.invoice_type == 'Service Sales Invoice':
                self.account_entry_list[n].insert('end', string=records[n][6])
            self.account_entry_list[n].configure(state='readonly')
            self.net_value_entry_list[n].insert('end', records[n][7])
            self.net_value_entry_list[n].configure(state='readonly')
            self.vat_rate_entry_list[n].configure(state='normal')
            self.vat_rate_entry_list[n].insert('end', string=records[n][11])
            self.vat_rate_entry_list[n].configure(state='readonly')
            self.vat_amount_entry_list[n].configure(state='normal')
            self.vat_amount_entry_list[n].insert(
                'end', string='{:,.2f}'.format(records[n][15]).replace(',', ' '))
            self.vat_amount_entry_list[n].configure(state='readonly')
            self.vat_rate_hidden_label_list[n].config(
                text=[item for item in self.vat_accounts
                      if item[0] == self.vat_rate_entry_list[n].get()][0][1])
        self.calculate_gross_value()

    def save_inv_edit(self):
        """Update changes from invoice edit mode in SQL database"""
        doc_date = self.doc_date_entry.get()
        vat_date = self.vat_date_entry.get()
        orig_doc_date = self.orig_doc_date
        orig_vat_date = self.orig_vat_date
        doc_date_obj = datetime.strptime(doc_date, "%d-%m-%Y")
        vat_date_obj = datetime.strptime(vat_date, "%d-%m-%Y")

        if int(doc_date_obj.strftime("%m")) != int(orig_doc_date.strftime("%m")) or \
                int(doc_date_obj.strftime("%Y")) != int(orig_doc_date.strftime("%Y")):
            tkinter.messagebox.showerror(title="ERROR", message="Document month date must remain the same", parent=self)
        elif int(vat_date_obj.strftime("%m")) != int(orig_vat_date.strftime("%m")) or \
                int(vat_date_obj.strftime("%Y")) != int(orig_vat_date.strftime("%Y")):
            tkinter.messagebox.showerror(title="ERROR", message="Vat month date must remain the same", parent=self)
        else:
            vat_date = 'null' if self.vat_date_entry.get() == '' \
                else f"'{self.vat_date_entry.get()}'"
            cust_id = self.customer_entry['text'][0:self.customer_entry['text'].rfind(" ~ ")]
            doc_number = self.invoice_number_entry.get()
            inv_due_date = self.due_date_entry.get()
            inv_payment_method = self.payment_method_entry.get()

            sql_command = f"UPDATE journal \n" \
                          f"SET \n" \
                          f"doc_date=TO_DATE('{doc_date}', 'dd-mm-yyyy'), " \
                          f"vat_date=TO_DATE({vat_date}, 'dd-mm-yyyy'), " \
                          f"cust_id={cust_id}, " \
                          f"doc_number='{doc_number}', " \
                          f"inv_due_date=TO_DATE('{inv_due_date}', 'dd-mm-yyyy'), " \
                          f"inv_payment_method='{inv_payment_method}' \n" \
                          f"WHERE \n" \
                          f"journal_entry_date='{self.journal_entry_date}' " \
                          f"AND doc_number='{self.doc_number}' " \
                          f"AND cust_id={self.cust_id} "

            conn = sqlcommand.SqlCommand()
            conn.sql_execute(sql_command)

            self.close()


class CorrectingInvoice(tkinter.Toplevel):

    def __init__(self, parent, invoice_type, journal_entry_date, doc_number, cust_id, cust_name,
                 orig_doc_number, mode):
        """Open new window to issue correcting invoice"""
        super().__init__(parent)

        # Connect to SQL to get data from database
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute("SELECT * FROM invoice_settings ORDER BY invoice_type DESC")
        self.inv_details = execute['records']

        # Specify document type
        self.invoice_type = invoice_type
        self.inv_type_short = [item for item in self.inv_details if f'{item[0]}' == self.invoice_type][0][1]
        self.cust_account = [item for item in self.inv_details if f'{item[0]}' == self.invoice_type][0][2]

        # Configure window
        self.title('Correcting Invoice')
        self.config(padx=15, pady=15)
        self.cor_type_label = tkinter.Label(self, text=f'CORRECTING INVOICE', foreground='red', font=30)
        self.cor_type_label.grid(column=3, row=0, columnspan=2)
        self.resizable(False, False)

        self.inv_type_label = tkinter.Label(self, text=f'{self.invoice_type}', font=30)
        self.inv_type_label.grid(column=3, row=1, columnspan=2)

        self.journal_entry_date = journal_entry_date
        self.doc_number = doc_number
        self.cust_id = cust_id
        self.cust_name = cust_name
        self.orig_doc_number = orig_doc_number
        self.mode = mode

        # Get data from SQL database
        if self.mode == 'create':
            self.sql_command_current_data = f"SELECT * FROM journal " \
                                            f"WHERE " \
                                            f"journal_entry_date='{self.journal_entry_date}' " \
                                            f"AND doc_number='{self.doc_number}' " \
                                            f"AND cust_id={self.cust_id} " \
                                            f"AND inv_index_id IS NOT NULL"
            self.order_by = ' ORDER BY no_journal ASC'
            conn = sqlcommand.SqlCommand()
            execute = conn.sql_execute(self.sql_command_current_data + self.order_by)
            self.cor_records = execute['records']

            # Get data from previous corrections
            self.sql_command_previous_data = f"SELECT * FROM journal " \
                                             f"WHERE " \
                                             f"cor_orig_entry_date='{self.journal_entry_date}' " \
                                             f"AND cor_orig_doc_number='{self.doc_number}' " \
                                             f"AND cust_id={self.cust_id} " \
                                             f"AND inv_index_id IS NOT NULL"
            conn = sqlcommand.SqlCommand()
            execute = conn.sql_execute(self.sql_command_previous_data + self.order_by)
            self.previous_cor_records = execute['records']

        elif self.mode == 'view':
            self.sql_command = f"SELECT * FROM journal " \
                               f"WHERE " \
                               f"journal_entry_date='{self.journal_entry_date}' " \
                               f"AND doc_number='{self.doc_number}' " \
                               f"AND cust_id={self.cust_id} " \
                               f"AND inv_index_id IS NOT NULL"
            self.order_by = ' ORDER BY no_journal ASC'
            conn = sqlcommand.SqlCommand()
            execute = conn.sql_execute(self.sql_command + self.order_by)
            records = execute['records']

            self.sql_command_orig = f"SELECT * FROM journal " \
                                    f"WHERE " \
                                    f"journal_entry_date='{records[0][18]}' " \
                                    f"AND doc_number='{records[0][19]}' " \
                                    f"AND cust_id={self.cust_id} " \
                                    f"AND inv_index_id IS NOT NULL"
            self.order_by = ' ORDER BY no_journal ASC'
            conn = sqlcommand.SqlCommand()
            execute = conn.sql_execute(self.sql_command_orig + self.order_by)
            self.cor_records = execute['records']
            self.previous_cor_records = []

        # Entries
        self.doc_date_label = tkinter.Label(self, text='Original document date')
        self.doc_date_label.grid(column=1, row=0)
        self.doc_date_entry = DateEntry(self, selectmode='day', locale='en_US', date_pattern='dd-mm-y')
        self.doc_date_entry.set_date(self.cor_records[0][3])
        self.doc_date_entry.config(state='disabled')
        self.doc_date_entry.grid(column=1, row=1)

        self.vat_date_label = tkinter.Label(self, text="Original vat date")
        self.vat_date_label.grid(column=2, row=0)
        self.vat_date_entry = DateEntry(self, selectmode='day', locale='en_US', date_pattern='dd-mm-y')
        self.vat_date_entry.set_date(self.cor_records[0][12])
        self.vat_date_entry.config(state='disabled')
        self.vat_date_entry.grid(column=2, row=1)

        self.customer_label = tkinter.Label(self, text="Customer")
        self.customer_label.grid(column=1, row=2)
        self.customer_entry = tkinter.Button(self, text=f"{self.cust_id} ~ {self.cust_name}", state='disabled',
                                             command=self.select_customer, width=25,
                                             highlightbackground='grey', borderwidth=1, relief='sunken', anchor='w')
        self.customer_entry.grid(column=2, row=2)

        self.invoice_number_label = tkinter.Label(self, text="Original invoice number")
        self.invoice_number_label.grid(column=1, row=3)
        self.invoice_number_entry = tkinter.Entry(self, width=30)
        self.invoice_number_entry.grid(column=2, row=3)
        if self.mode == 'view':
            self.invoice_number_entry.insert('end', string=self.orig_doc_number)
        elif self.mode == 'create':
            self.invoice_number_entry.insert('end', string=self.doc_number)
        self.invoice_number_entry.config(state='readonly')

        if self.invoice_type == "Cost Purchase Invoice":
            self.internal_inv_num_label = tkinter.Label(self, text="Internal inv num")
            self.internal_inv_num_label.grid(column=1, row=4)
            self.internal_inv_num_entry = tkinter.Entry(self, width=30, state='readonly')
            self.internal_inv_num_entry.grid(column=2, row=4)
        else:
            self.invoice_number_entry.config(state='readonly')

        self.space = tkinter.Canvas(self, height=10, width=0)
        self.space.grid(column=1, row=5)

        # Headers
        self.no_journal_label = tkinter.Label(self, width=3)
        self.no_journal_label.grid(column=0, row=6)
        self.index_label = tkinter.Label(self, text="Index", width=21)
        self.index_label.grid(column=1, row=6)
        self.description_label = tkinter.Label(self, text="Description", width=25)
        self.description_label.grid(column=2, row=6)
        self.account_label = tkinter.Label(self, text="Account", width=25)
        self.account_label.grid(column=3, row=6)
        self.net_value_label = tkinter.Label(self, text='NET Value', width=26)
        self.net_value_label.grid(column=4, row=6)
        self.vat_rate_label = tkinter.Label(self, text='Vat rate', width=27)
        self.vat_rate_label.grid(column=5, row=6)
        self.vat_amount_label = tkinter.Label(self, text='Vat amount', width=27)
        self.vat_amount_label.grid(column=6, row=6)

        # Set first row
        self.row = 7
        # Set first no
        self.no = 1

        # Bottom widget
        self.net_sum_value_label = tkinter.Label(self, text="Original net value")
        self.net_sum_value_label.grid(column=1)
        self.net_value = tkinter.Label(self, text="0.00", anchor='e', width=16)
        self.net_value.grid(column=2)
        self.vat_sum_value_label = tkinter.Label(self, text="Original vat value")
        self.vat_sum_value_label.grid(column=1)
        self.vat_value = tkinter.Label(self, text="0.00", anchor='e', width=16)
        self.vat_value.grid(column=2)
        self.gross_sum_value_label = tkinter.Label(self, text="Original gross value")
        self.gross_sum_value_label.grid(column=1, pady=(0, 20))
        self.gross_value = tkinter.Label(self, text="0.00", anchor='e', width=16)
        self.gross_value.grid(column=2, pady=(0, 20))

        self.due_date_label = tkinter.Label(self, text="Original due date")
        self.due_date_label.grid(column=1)
        self.due_date_entry = DateEntry(self, selectmode='day', locale='en_US', date_pattern='dd-mm-y')
        self.due_date_entry.set_date(self.cor_records[0][16])
        self.due_date_entry.config(state='disabled')
        self.due_date_entry.grid(column=2)

        self.payment_method_label = tkinter.Label(self, text="Original payment method")
        self.payment_method_label.grid(column=1)
        payment_methods = ('transfer', 'cash')
        self.payment_method_entry = ttk.Combobox(self, values=payment_methods, state='readonly')
        self.payment_method_entry.set(self.cor_records[0][17])
        self.payment_method_entry.config(state='disabled')
        self.payment_method_entry.grid(column=2)

        self.post_button = tkinter.Button(self, text="Post in journal", command=self.post_cor_inv_in_journal)
        self.post_button.grid(column=6)

        # Add scrollbar
        self.frame = tkinter.Frame(self)
        self.frame.grid(column=0, row=7, columnspan=7)

        self.scrollbar = tkinter.Scrollbar(self.frame)
        self.scrollbar.grid(column=7, row=0, sticky='ns')

        self.canvas = tkinter.Canvas(self.frame, yscrollcommand=self.scrollbar.set, width=1111, height=387,
                                     highlightthickness=0, borderwidth=1, relief='groove')
        self.canvas.grid(column=0, row=0, columnspan=7)

        self.lines_frame = tkinter.Frame(self.canvas)
        self.lines_frame.grid(column=0, row=0, columnspan=7)

        self.lines_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.lines_frame, anchor='nw')

        self.canvas.config(yscrollcommand=self.scrollbar.set)

        self.scrollbar.config(command=self.canvas.yview)

        # List for all added lines
        self.no_label_list = []
        self.index_entry_list = []
        self.description_entry_list = []
        self.account_entry_list = []
        self.net_value_entry_list = []
        self.vat_rate_entry_list = []
        self.vat_amount_entry_list = []
        self.vat_rate_hidden_label_list = []

        self.list_of_str_var = []

        self.add_line()

        # Connect with SQL database
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute("SELECT * FROM vat_rates")
        self.vat_accounts = execute['records']

        # New widgets
        self.correcting_inv_date_label = tkinter.Label(self, text="Correcting invoice date")
        self.correcting_inv_date_label.grid(column=5, row=0)
        self.correcting_inv_date_entry = DateEntry(self, selectmode='day', locale='en_US',
                                                   date_pattern='dd-mm-y')
        self.correcting_inv_date_entry.grid(column=5, row=1)

        self.correcting_vat_date_label = tkinter.Label(self, text="Vat date")
        self.correcting_vat_date_label.grid(column=6, row=0)
        self.correcting_vat_date_entry = DateEntry(self, selectmode='day', locale='en_US',
                                                   date_pattern='dd-mm-y')
        self.correcting_vat_date_entry.grid(column=6, row=1)

        self.correcting_inv_reason_label = tkinter.Label(self, text="Reason for correction")
        self.correcting_inv_reason_label.grid(column=5, row=2)
        self.correcting_inv_reason_entry = tkinter.Entry(self, width=30)
        self.correcting_inv_reason_entry.grid(column=6, row=2)

        self.correcting_inv_number_label = tkinter.Label(self, text="Correcting invoice number")
        self.correcting_inv_number_label.grid(column=5, row=3)
        self.correcting_inv_number_entry = tkinter.Entry(self, width=30)
        self.correcting_inv_number_entry.grid(column=6, row=3)

        if self.invoice_type == 'Cost Purchase Invoice':
            self.internal_inv_num_entry.config(state='normal')
            self.internal_inv_num_entry.insert('end', self.cor_records[0][10])
            self.internal_inv_num_entry.config(state='readonly')

            self.internal_cor_inv_number_label = tkinter.Label(self, text="Internal cor inv number")
            self.internal_cor_inv_number_label.grid(column=5, row=4)
            self.internal_cor_inv_number_entry = tkinter.Entry(self, width=30, state='readonly')
            self.internal_cor_inv_number_entry.grid(column=6, row=4)
        else:
            self.correcting_inv_number_entry.config(state='readonly')

        # Bottom new widgets
        self.cor_net_value_label = tkinter.Label(self, text="Net value")
        self.cor_net_value_label.grid(column=4)
        self.cor_net_value = tkinter.Label(self, text="0.00", anchor='e', width=16)
        self.cor_net_value.grid(column=5)
        self.cor_vat_value_label = tkinter.Label(self, text="Vat value")
        self.cor_vat_value_label.grid(column=4)
        self.cor_vat_value = tkinter.Label(self, text="0.00", anchor='e', width=16)
        self.cor_vat_value.grid(column=5)
        self.cor_gross_value_label = tkinter.Label(self, text="Gross value")
        self.cor_gross_value_label.grid(column=4, pady=(0, 20))
        self.cor_gross_value = tkinter.Label(self, text="0.00", anchor='e', width=16)
        self.cor_gross_value.grid(column=5, pady=(0, 20))

        self.cor_due_date_label = tkinter.Label(self, text="Due date")
        self.cor_due_date_label.grid(column=4)
        self.cor_due_date_entry = DateEntry(self, selectmode='day', locale='en_US', date_pattern='dd-mm-y')
        self.cor_due_date_entry.grid(column=5)

        self.cor_payment_method_label = tkinter.Label(self, text="Payment method")
        self.cor_payment_method_label.grid(column=4)
        payment_methods = ('transfer', 'cash')
        self.cor_payment_method_entry = ttk.Combobox(self, values=payment_methods, state='readonly')
        self.cor_payment_method_entry.current(0)
        self.cor_payment_method_entry.grid(column=5)

        # Create list with all check buttons variable names
        self.check_buttons = []
        # Create list with check button states
        self.positions_to_correct = []
        for n in range(len(self.cor_records)):
            if n > 0:
                # Add line to each position posted in original invoice
                self.add_line()
            # Add check buttons to each line
            self.checked_state = tkinter.IntVar()
            self.correct_position_chkbtn = ttk.Checkbutton(self.lines_frame, variable=self.checked_state)
            self.correct_position_chkbtn.grid(column=7, row=self.row - 2)
            self.positions_to_correct.append(self.checked_state)
            self.check_buttons.append(self.correct_position_chkbtn)
            self.correct_position_chkbtn.bind('<Button-1>', self.add_correcting_lines)

        # Set row for bottom widget
        self.cor_net_value_label.grid(row=self.row)
        self.cor_net_value.grid(row=self.row)
        self.cor_vat_value_label.grid(row=self.row + 1)
        self.cor_vat_value.grid(row=self.row + 1)
        self.cor_gross_value_label.grid(row=self.row + 2)
        self.cor_gross_value.grid(row=self.row + 2)
        self.cor_due_date_label.grid(row=self.row + 3)
        self.cor_due_date_entry.grid(row=self.row + 3)
        self.cor_payment_method_label.grid(row=self.row + 4)
        self.cor_payment_method_entry.grid(row=self.row + 4)

        for n in range(len(self.cor_records)):
            # Fill all lines with data from original invoice
            self.index_entry_list[n].config(text=self.cor_records[n][14], state='disabled')
            self.description_entry_list[n].insert('end', string=self.cor_records[n][4])
            self.description_entry_list[n].config(state='readonly')
            self.account_entry_list[n].config(state='normal')
            if self.invoice_type == 'Cost Purchase Invoice':
                self.account_entry_list[n].insert('end', string=self.cor_records[n][5])
            if self.invoice_type == 'Service Sales Invoice':
                self.account_entry_list[n].insert('end', string=self.cor_records[n][6])
            self.account_entry_list[n].config(state='readonly')
            self.net_value_entry_list[n].insert('end', string=self.cor_records[n][7])
            self.net_value_entry_list[n].config(state='readonly')
            self.vat_rate_entry_list[n].config(state='normal')
            self.vat_rate_entry_list[n].insert('end', string=self.cor_records[n][11])
            self.vat_rate_entry_list[n].config(state='readonly')
            self.vat_amount_entry_list[n].config(state='normal')
            self.vat_amount_entry_list[n].insert(
                'end', string='{:,.2f}'.format(self.cor_records[n][15]).replace(',', ' '))
            self.vat_amount_entry_list[n].config(state='readonly')
            self.vat_rate_hidden_label_list[n].config(
                text=[item for item in self.vat_accounts
                      if item[0] == self.vat_rate_entry_list[n].get()][0][1])

        # Check if there have been any corrections
        if self.previous_cor_records == []:
            pass
        else:
            tkinter.messagebox.showinfo(title='INFO', message="The document has already been corrected. "
                                                              "Current index values after corrections will be shown.",
                                        parent=self)
            # Update net and vat values if there have been any corrections
            for n in range(len(self.cor_records)):
                for cor_item in self.previous_cor_records:
                    if n == cor_item[21]:
                        net_before_cor = self.net_value_entry_list[n].get().replace(' ', '')
                        net_after_cor = float(net_before_cor) + float(cor_item[7])
                        self.net_value_entry_list[n].config(state='normal')
                        self.net_value_entry_list[n].delete(0, 'end')
                        self.net_value_entry_list[n].insert(
                            'end', string='{:,.2f}'.format(net_after_cor).replace(',', ' '))
                        self.net_value_entry_list[n].config(state='readonly')
                        vat_before_cor = self.vat_amount_entry_list[n].get().replace(' ', '')
                        vat_after_cor = float(vat_before_cor) + float(cor_item[15])
                        self.vat_amount_entry_list[n].config(state='normal')
                        self.vat_amount_entry_list[n].delete(0, 'end')
                        self.vat_amount_entry_list[n].insert(
                            'end', string='{:,.2f}'.format(vat_after_cor).replace(',', ' '))
                        self.vat_amount_entry_list[n].config(state='readonly')
        self.calculate_gross_value()

        # Create list with consecutive numbers of position lines
        cor_lines = []
        for line in range(len(self.check_buttons)):
            cor_lines.append(line)
        # Create dictionary with line number in key and widget list in values
        self.correct_line_dict = dict.fromkeys(cor_lines)
        for key in self.correct_line_dict:
            # Add zero values for each widget in line
            self.correct_line_dict[key] = (0, 0, 0, 0)

        self.list_of_cor_str_var = []
        self.list_of_cor_net_val = []

    def add_line(self):
        """Add new lines to post"""
        self.no_label = tkinter.Label(self.lines_frame, text=f'{self.no}', width=3)
        self.no_label.grid(column=0, row=self.row)
        self.no += 1

        self.index_entry = tkinter.Button(self.lines_frame, text='...', command=self.select_index, width=20,
                                          highlightbackground='grey', borderwidth=1, anchor='w')
        self.index_entry.grid(column=1, row=self.row)

        self.description_entry = tkinter.Entry(self.lines_frame, width=30)
        self.description_entry.grid(column=2, row=self.row)

        self.account_entry = tkinter.Entry(self.lines_frame, width=30, state='readonly', justify='right')
        self.account_entry.grid(column=3, row=self.row)

        self.amount_str_var = tkinter.StringVar()
        self.amount_str_var.set('0.00')
        self.net_value_entry = tkinter.Entry(self.lines_frame, textvariable=self.amount_str_var, width=30,
                                             justify='right')
        self.net_value_entry.grid(column=4, row=self.row)

        self.vat_rate_entry = tkinter.Entry(self.lines_frame, width=30, state='readonly', justify='right')
        self.vat_rate_entry.grid(column=5, row=self.row)

        self.vat_amount_entry = tkinter.Entry(self.lines_frame, width=30, state='readonly', justify='right')
        self.vat_amount_entry.grid(column=6, row=self.row)

        self.vat_rate_hidden_label = tkinter.Label(text='')
        self.vat_account_hidden_label = tkinter.Label(text='')

        # Set row for bottom widget
        self.net_sum_value_label.grid(row=self.row + 2)
        self.net_value.grid(row=self.row + 2)
        self.vat_sum_value_label.grid(row=self.row + 3)
        self.vat_value.grid(row=self.row + 3)
        self.gross_sum_value_label.grid(row=self.row + 4)
        self.gross_value.grid(row=self.row + 4)
        self.due_date_label.grid(row=self.row + 5)
        self.due_date_entry.grid(row=self.row + 5)
        self.payment_method_label.grid(row=self.row + 6)
        self.payment_method_entry.grid(row=self.row + 6)
        self.post_button.grid(row=self.row + 6)

        self.row += 2

        # bind name of widget with function
        self.index_entry.bind('<Button-1>', self.clicked_button)
        self.net_value_entry.bind('<FocusOut>', self.calculate_vat_value)

        # Append all created lines to list
        self.no_label_list.append(self.no_label)
        self.index_entry_list.append(self.index_entry)
        self.description_entry_list.append(self.description_entry)
        self.account_entry_list.append(self.account_entry)
        self.net_value_entry_list.append(self.net_value_entry)
        self.vat_rate_entry_list.append(self.vat_rate_entry)
        self.vat_amount_entry_list.append(self.vat_amount_entry)
        self.vat_rate_hidden_label_list.append(self.vat_rate_hidden_label)

        self.list_of_str_var.append(self.amount_str_var)

        for item in range(int(len(self.list_of_str_var))):
            self.list_of_str_var[item].trace('w', partial(self.entry_fill, self.net_value_entry_list[item]))

    def remove_line(self):
        """Remove last line to post"""
        if self.row > 10:
            self.no_label_list[-1].destroy()
            self.no_label_list.pop()
            self.index_entry_list[-1].destroy()
            self.index_entry_list.pop()
            self.description_entry_list[-1].destroy()
            self.description_entry_list.pop()
            self.account_entry_list[-1].destroy()
            self.account_entry_list.pop()
            self.net_value_entry_list[-1].destroy()
            self.net_value_entry_list.pop()
            self.vat_rate_entry_list[-1].destroy()
            self.vat_rate_entry_list.pop()
            self.vat_amount_entry_list[-1].destroy()
            self.vat_amount_entry_list.pop()
            self.vat_rate_hidden_label_list[-1].destroy()
            self.vat_rate_hidden_label_list.pop()
            self.list_of_str_var.pop()
            self.row -= 2
            self.no -= 1

    def add_correcting_lines(self, event):
        """Create or delete line with entry to correct values whenever check button is pressed"""
        if self.mode == 'view':
            pass
        elif self.mode == 'create':
            checked = event.widget
            checked_index = self.check_buttons.index(checked)
            checked_index_state = self.positions_to_correct[self.check_buttons.index(checked)].get()

            if checked_index_state == 0:
                self.correct_value_label = tkinter.Label(self.lines_frame, text="Insert correct value")
                self.correct_value_label.grid(column=3, row=8 + checked_index * 2)
                self.cor_amount_str_var = tkinter.StringVar()
                self.cor_amount_str_var.set('0.00')
                self.list_of_cor_str_var.append(self.cor_amount_str_var)
                self.correct_value_entry = tkinter.Entry(self.lines_frame, textvariable=self.cor_amount_str_var,
                                                         width=30, justify='right')
                self.correct_value_entry.grid(column=4, row=8 + checked_index * 2)
                self.correct_value_entry.bind('<FocusOut>', self.filled_entry)
                self.list_of_cor_net_val.append(self.correct_value_entry)
                self.corrected_entry = tkinter.Entry(self.lines_frame, width=30, justify='right', state='readonly',
                                                     fg='red')
                self.corrected_entry.grid(column=5, row=8 + checked_index * 2)
                self.vat_corrected_entry = tkinter.Entry(self.lines_frame, width=30, justify='right', state='readonly',
                                                         fg='red')
                self.vat_corrected_entry.grid(column=6, row=8 + checked_index * 2)
                self.correct_line_dict[checked_index] = (self.correct_value_label, self.correct_value_entry,
                                                         self.corrected_entry, self.vat_corrected_entry)

            if checked_index_state == 1:
                for widget in self.correct_line_dict[checked_index]:
                    widget.destroy()
                self.correct_line_dict[checked_index] = (0, 0, 0, 0)

        for item in range(int(len(self.list_of_cor_str_var))):
            self.list_of_cor_str_var[item].trace('w', partial(self.entry_fill, self.list_of_cor_net_val[item]))

    def filled_entry(self, event):
        """Return which entry was filled"""
        self.widget = event.widget
        # Calculate all values when entry is filled
        self.calculate_corrected_values()

    def calculate_corrected_values(self):
        """Calculate net, vat, gross values whenever new value is inserted in entry"""
        # Returns information which dictionary key refers to line which was filled
        self.dict_key = [item for item in self.correct_line_dict.items() if item[1][1] == self.widget][0][0]

        orig_net_val = self.net_value_entry_list[self.dict_key].get()
        vat_rate = self.vat_rate_hidden_label_list[self.dict_key]['text']

        try:
            correction_net_value = round(
                float(self.correct_line_dict[self.dict_key][1].get().replace(' ', '')) -
                round(float(orig_net_val.replace(' ', ''))), 2)
        except Exception:
            correction_net_value = 0

        self.correct_line_dict[self.dict_key][2].config(state='normal')
        self.correct_line_dict[self.dict_key][2].delete(0, 'end')
        self.correct_line_dict[self.dict_key][2].insert('end', '{:,.2f}'.format(correction_net_value).replace(',', ' '))
        self.correct_line_dict[self.dict_key][2].config(state='readonly')

        correction_vat_value = round(float(self.correct_line_dict[self.dict_key][2].get().replace(' ', '')) *
                                     float(vat_rate) / 100, 2)
        self.correct_line_dict[self.dict_key][3].config(state='normal')
        self.correct_line_dict[self.dict_key][3].delete(0, 'end')
        self.correct_line_dict[self.dict_key][3].insert('end', '{:,.2f}'.format(correction_vat_value).replace(',', ' '))
        self.correct_line_dict[self.dict_key][3].config(state='readonly')

        net_all_list = [item[1][2] for item in self.correct_line_dict.items()]
        vat_all_list = [item[1][3] for item in self.correct_line_dict.items()]
        for item in net_all_list:
            if item == 0:
                pass
            else:
                if net_all_list[net_all_list.index(item)].get() == '':
                    net_all_list[net_all_list.index(item)] = 0
                else:
                    net_all_list[net_all_list.index(item)] = \
                        net_all_list[net_all_list.index(item)].get().replace(' ', '')
        for item in vat_all_list:
            if item == 0:
                pass
            else:
                if vat_all_list[vat_all_list.index(item)].get() == '':
                    vat_all_list[vat_all_list.index(item)] = 0
                else:
                    vat_all_list[vat_all_list.index(item)] = \
                        vat_all_list[vat_all_list.index(item)].get().replace(' ', '')

        cor_net_sum = sum(list(map(float, net_all_list)))
        cor_vat_sum = sum(list(map(float, vat_all_list)))
        cor_gross_sum = cor_net_sum + cor_vat_sum
        self.cor_net_value.config(text=f"{'{:,.2f}'.format(cor_net_sum).replace(',', ' ')}")
        self.cor_vat_value.config(text=f"{'{:,.2f}'.format(cor_vat_sum).replace(',', ' ')}")
        self.cor_gross_value.config(text=f"{'{:,.2f}'.format(cor_gross_sum).replace(',', ' ')}")

    def calculate_gross_value(self):
        """Calculate gross value"""
        lines = int(len(self.no_label_list))
        net_value = []
        vat_value = []

        for n in range(lines):
            net_value.append(self.net_value_entry_list[n].get())
            vat_value.append(self.vat_amount_entry_list[n].get())

        for item in range(len(net_value)):
            if net_value[item] == '':
                net_value[item] = 0
            else:
                net_value[item] = net_value[item].replace(' ', '')

        for item in range(len(vat_value)):
            if vat_value[item] == '':
                vat_value[item] = 0
            else:
                vat_value[item] = vat_value[item].replace(' ', '')
        net_sum = sum(list(map(float, net_value)))
        vat_sum = sum(list(map(float, vat_value)))
        gross_sum = net_sum + vat_sum
        self.net_value.config(text=f"{'{:,.2f}'.format(net_sum).replace(',', ' ')}")
        self.vat_value.config(text=f"{'{:,.2f}'.format(vat_sum).replace(',', ' ')}")
        self.gross_value.config(text=f"{'{:,.2f}'.format(gross_sum).replace(',', ' ')}")

    def clicked_button(self, event):
        """Return clicked button"""
        self.clicked_btn = event.widget

    def select_index(self):
        """Open new window with customer to choose"""
        self.index_window = invoice_indexes.InvoiceIndexes(self)
        self.index_window.grab_set()
        self.add_index_button = tkinter.Button(self.index_window, text='Select index',
                                               command=self.select_index_command, font=30)
        self.add_index_button.grid(column=0, row=1, columnspan=2)

    def select_index_command(self):
        """Fill row with selected index values"""
        selected = self.index_window.selected_inv_index()
        index = self.clicked_btn
        index.config(text=f'{selected[0]}')
        description = self.description_entry_list[self.index_entry_list.index(self.clicked_btn)]
        description.delete(0, 'end')
        description.insert('end', selected[1])
        account = self.account_entry_list[self.index_entry_list.index(self.clicked_btn)]
        account.config(state='normal')
        account.delete(0, 'end')
        if self.invoice_type == 'Service Sales Invoice':
            account.insert('end', selected[2])
        elif self.invoice_type == 'Cost Purchase Invoice':
            account.insert('end', selected[3])
        account.config(state='readonly')
        vat_rate = self.vat_rate_entry_list[self.index_entry_list.index(self.clicked_btn)]
        vat_rate.config(state='normal')
        vat_rate.delete(0, 'end')
        vat_rate.insert('end', selected[4])
        vat_rate.config(state='readonly')
        self.vat_rate_hidden = self.vat_rate_hidden_label_list[self.index_entry_list.index(self.clicked_btn)]
        self.vat_rate_hidden.config(text=[item for item in self.vat_accounts if item[0] == selected[4]][0][1])
        self.index_window.destroy()

    def calculate_vat_value(self, event):
        """Calculate Vat value"""
        net_entry = event.widget
        vat_label = self.vat_rate_hidden_label_list[self.net_value_entry_list.index(net_entry)]
        try:
            vat_amount = round(float(vat_label['text']) * float(net_entry.get().replace(' ', '')) / 100, 2)
            vat_amount_entry = self.vat_amount_entry_list[self.net_value_entry_list.index(net_entry)]
            vat_amount_entry.config(state='normal')
            vat_amount_entry.delete(0, 'end')
            vat_amount_entry.insert('end', '{:,.2f}'.format(vat_amount).replace(',', ' '))
            vat_amount_entry.config(state='readonly')
        except Exception:
            pass
        self.calculate_gross_value()

    def select_customer(self):
        """Open new window with customer to choose"""
        self.customer_window = customers.Customers(self)
        self.customer_window.grab_set()
        add_customer_button = tkinter.Button(self.customer_window, text='Select customer',
                                             command=self.select_customer_command, font=30)
        add_customer_button.grid(column=0, row=1, columnspan=2)

    def select_customer_command(self):
        """Get selected customer from customer window"""
        self.cust_details = self.customer_window.selected_customer()
        self.customer_entry.config(text=f"{self.cust_details[0]} ~ {self.cust_details[1]}")
        self.customer_window.destroy()

    def entry_fill(self, entry, *args):
        """Format entry widget and returns digits with a thousand separator"""
        try:
            if len(entry.get()) >= 20:
                entry.delete(entry.index("end") - 1)
            else:
                result = re.sub(r'[^0-9]', '', entry.get())
                sep = '{:,.2f}'.format(float(result) / 100).replace(',', ' ')
                entry.delete(0, 'end')
                entry.insert('end', sep)
        except Exception:
            pass

    def post_cor_inv_in_journal(self):
        """Posts correcting invoice in journal in sql database, checks if all necessary fields are filled"""
        # Check if at least one position has been selected
        positions_sum = 0
        for chkbtn in self.check_buttons:
            positions_sum += self.positions_to_correct[self.check_buttons.index(chkbtn)].get()
        if positions_sum == 0:
            tkinter.messagebox.showerror(title="ERROR", message="None of the positions have been corrected",
                                         parent=self)
        else:
            # Take doc number
            date_str = self.doc_date_entry.get()
            date = datetime.strptime(date_str, '%d-%m-%Y')
            month = date.strftime('%m')
            year = date.strftime('%Y')
            sql_take_number = f"SELECT doc_num FROM document_numbers WHERE " \
                              f"doc_name='[COR] {self.invoice_type}' AND doc_month={month} AND doc_year={year}"
            conn = sqlcommand.SqlCommand()
            execute = conn.sql_execute(sql_take_number)
            number = execute['records'][0][0]

            doc_number = f"{number}/{month}/{year}"

            # Check if all fields are filled
            all_filled = True
            for item in self.correct_line_dict:
                try:
                    if float(self.correct_line_dict[item][1].get().replace(' ', '')) == 0:
                        all_filled = False
                except Exception:
                    pass
            if all_filled == False:
                tkinter.messagebox.showerror(title="ERROR", message="You left unfilled fields!", parent=self)
            elif self.correcting_inv_reason_entry.get() == '':
                tkinter.messagebox.showerror(title="ERROR", message="Missing correcting reason", parent=self)
            else:
                # Calculate all values again
                for item in self.correct_line_dict:
                    if self.correct_line_dict[item] == (0, 0, 0, 0):
                        pass
                    else:
                        orig_net_val = self.net_value_entry_list[item].get()
                        vat_rate = self.vat_rate_hidden_label_list[item]['text']
                        try:
                            correction_net_value = round(
                                float(self.correct_line_dict[item][1].get().replace(' ', '')) - round(
                                    float(orig_net_val.replace(' ', ''))), 2)
                        except Exception:
                            correction_net_value = 0

                        self.correct_line_dict[item][2].config(state='normal')
                        self.correct_line_dict[item][2].delete(0, 'end')
                        self.correct_line_dict[item][2].insert(
                            'end', '{:,.2f}'.format(correction_net_value).replace(',', ' '))
                        self.correct_line_dict[item][2].config(state='readonly')

                        vat_pos = \
                            round(float(self.correct_line_dict[item][2].get().replace(' ', '')) *
                                  float(vat_rate) / 100, 2)
                        self.correct_line_dict[item][3].config(state='normal')
                        self.correct_line_dict[item][3].delete(0, 'end')
                        self.correct_line_dict[item][3].insert('end', '{:,.2f}'.format(vat_pos).replace(',', ' '))
                        self.correct_line_dict[item][3].config(state='readonly')

                        net_all_list = [item[1][2] for item in self.correct_line_dict.items()]
                        vat_all_list = [item[1][3] for item in self.correct_line_dict.items()]
                        for item in net_all_list:
                            if item == 0:
                                pass
                            else:
                                if net_all_list[net_all_list.index(item)].get() == '':
                                    net_all_list[net_all_list.index(item)] = 0
                                else:
                                    net_all_list[net_all_list.index(item)] = \
                                        net_all_list[net_all_list.index(item)].get().replace(' ', '')
                        for item in vat_all_list:
                            if item == 0:
                                pass
                            else:
                                if vat_all_list[vat_all_list.index(item)].get() == '':
                                    vat_all_list[vat_all_list.index(item)] = 0
                                else:
                                    vat_all_list[vat_all_list.index(item)] = \
                                        vat_all_list[vat_all_list.index(item)].get().replace(' ', '')

                        cor_net_sum = sum(list(map(float, net_all_list)))
                        cor_vat_sum = sum(list(map(float, vat_all_list)))
                        cor_gross_sum = cor_net_sum + cor_vat_sum
                        self.cor_net_value.config(text=f"{'{:,.2f}'.format(cor_net_sum).replace(',', ' ')}")
                        self.cor_vat_value.config(text=f"{'{:,.2f}'.format(cor_vat_sum).replace(',', ' ')}")
                        self.cor_gross_value.config(text=f"{'{:,.2f}'.format(cor_gross_sum).replace(',', ' ')}")

                if float(self.cor_gross_value['text'].replace(' ', '')) == 0:
                    tkinter.messagebox.showerror(title="ERROR", message="None of positions have been corrected.",
                                                 parent=self)
                else:
                    # Get and prepare data to post in SQL database
                    cust_account = f"'{self.cust_account}'"
                    doc_type = f'[COR] {self.inv_type_short}'
                    doc_date = self.correcting_inv_date_entry.get()
                    description = []
                    dt_account = []
                    ct_account = []
                    amount = []
                    cust_id = self.customer_entry['text'][0:self.customer_entry['text'].rfind(" ~ ")]
                    ext_doc_number = self.correcting_inv_number_entry.get()
                    vat_id = []
                    vat_date = 'null' if self.correcting_vat_date_entry.get() == '' \
                        else f"'{self.correcting_vat_date_entry.get()}'"
                    inv_index_id = []
                    vat_value = []
                    due_date = self.cor_due_date_entry.get()
                    payment_method = self.payment_method_entry.get()
                    gross_value = self.cor_gross_value['text'].replace(' ', '')
                    cor_orig_entry_date = self.cor_records[0][1]
                    cor_orig_doc_number = self.invoice_number_entry.get()
                    cor_reason = self.correcting_inv_reason_entry.get()

                    for n in range(len(self.cor_records)):
                        # Get data from original invoice
                        inv_index_id.append(self.index_entry_list[n]['text'])
                        description.append(self.description_entry_list[n].get())
                        if doc_type == '[COR] purchase costs':
                            dt_account.append(self.account_entry_list[n].get())
                        elif doc_type == '[COR] sale service':
                            ct_account.append(self.account_entry_list[n].get())
                        vat_id.append(self.vat_rate_entry_list[n].get())

                    for item in range(len(dt_account)):
                        if dt_account[item] == '':
                            pass
                        else:
                            dt_account[item] = f"'{dt_account[item]}'"

                    for item in range(len(ct_account)):
                        if ct_account[item] == '':
                            pass
                        else:
                            ct_account[item] = f"'{ct_account[item]}'"

                    # Get data with corrected values
                    for item in self.correct_line_dict:
                        try:
                            amount.append(self.correct_line_dict[item][2].get().replace(' ', ''))
                            vat_value.append(self.correct_line_dict[item][3].get().replace(' ', ''))
                        except Exception:
                            amount.append('0.00')
                            vat_value.append('0.00')

                    if ext_doc_number == '':
                        if self.invoice_type == 'Cost Purchase Invoice':
                            tkinter.messagebox.showerror(title="ERROR", message="Missing document number", parent=self)
                        else:
                            ext_doc_number = doc_number

                    # Update next doc number
                    sql_update_number = f"UPDATE document_numbers SET " \
                                        f"doc_num = {number + 1} " \
                                        f"WHERE " \
                                        f"doc_name='[COR] {self.invoice_type}' " \
                                        f"AND doc_month={month} AND doc_year={year}"
                    conn = sqlcommand.SqlCommand()
                    conn.sql_execute(sql_update_number)

                    # Create dictionary with vat sum for each rate
                    vat_sum_dict = dict.fromkeys(vat_id, 0)
                    for n in range(len(vat_id)):
                        for key in vat_sum_dict:
                            if key == vat_id[n]:
                                if vat_value[n] == '':
                                    pass
                                else:
                                    vat_sum_dict[vat_id[n]] += float(vat_value[n])

                    for item in range(len(vat_id)):
                        if vat_id[item] == '':
                            vat_id[item] = 'null'
                        else:
                            vat_id[item] = f"'{vat_id[item]}'"

                    insert_sql = f"INSERT INTO journal(doc_type, doc_date, description, dt_account_num, " \
                                 f"ct_account_num, amount, cust_id, doc_number, int_doc_number, " \
                                 f"vat_id, vat_date, status, inv_index_id, index_vat_value, " \
                                 f"inv_due_date, inv_payment_method, cor_orig_entry_date, cor_orig_doc_number, " \
                                 f"cor_reason, cor_orig_position)\n" \
                                 f"VALUES\n" \
                                 f"('{doc_type}', TO_DATE('{doc_date}', 'dd-mm-yyyy'), " \
                                 f"'{doc_number} {self.invoice_type}', " \
                                 f"{cust_account if self.invoice_type == 'Service Sales Invoice' else 'null'}, " \
                                 f"{cust_account if self.invoice_type == 'Cost Purchase Invoice' else 'null'}, " \
                                 f"{gross_value}, " \
                                 f"{cust_id}, '{ext_doc_number}', '{doc_number}', null, " \
                                 f"TO_DATE({vat_date}, 'dd-mm-yyyy'), '[COR]', null, null, " \
                                 f"TO_DATE('{due_date}', 'dd-mm-yyyy'), '{payment_method}', " \
                                 f"'{cor_orig_entry_date}', '{cor_orig_doc_number}', '{cor_reason}', " \
                                 f"null), " \
                                 f"\n"

                    n = 0
                    values_string = []
                    for item in self.correct_line_dict:
                        if self.correct_line_dict[item] == (0, 0, 0, 0):
                            pass
                        else:
                            values_string.append(f"('{doc_type}', TO_DATE('{doc_date}', 'dd-mm-yyyy'), "
                                                 f"'{description[n]}', "
                                                 f"{dt_account[n] if doc_type == '[COR] purchase costs' else 'null'}, "
                                                 f"{ct_account[n] if doc_type == '[COR] sale service' else 'null'}, "
                                                 f"{amount[n]}, "
                                                 f"{cust_id}, '{ext_doc_number}', '{doc_number}', {vat_id[n]}, "
                                                 f"TO_DATE({vat_date}, 'dd-mm-yyyy'), '[COR]', "
                                                 f"'{inv_index_id[n]}', {vat_value[n]}, "
                                                 f"TO_DATE('{due_date}', 'dd-mm-yyyy'), '{payment_method}', "
                                                 f"'{cor_orig_entry_date}', '{cor_orig_doc_number}', "
                                                 f"'{cor_reason}', {item}), "
                                                 f"\n")
                        n += 1

                    vat_string = []
                    for key in vat_sum_dict:
                        vat_acc = [item for item in self.vat_accounts if item[0] == key][0][2] \
                            if doc_type == '[COR] sale service' else \
                            [item for item in self.vat_accounts if item[0] == key][0][3]
                        vat_account = f"'{vat_acc}'"
                        if vat_sum_dict[key] == 0:
                            pass
                        else:
                            vat_string.append(f"('{doc_type}', TO_DATE('{doc_date}', 'dd-mm-yyyy'), "
                                              f"'{doc_number} {self.invoice_type}', "
                                              f"{vat_account if doc_type == '[COR] purchase costs' else 'null'}, "
                                              f"{vat_account if doc_type == '[COR] sale service' else 'null'}, "
                                              f"{'{:.2f}'.format(vat_sum_dict[key])}, "
                                              f"{cust_id}, '{ext_doc_number}', '{doc_number}', '{key}', "
                                              f"TO_DATE({vat_date}, 'dd-mm-yyyy'), '[COR]', null, null, "
                                              f"TO_DATE('{due_date}', 'dd-mm-yyyy'), '{payment_method}', "
                                              f"'{cor_orig_entry_date}', '{cor_orig_doc_number}', "
                                              f"'{cor_reason}', null), "
                                              f"\n")

                    for item in values_string:
                        insert_sql += item
                    for item in vat_string:
                        insert_sql += item
                    sql_command = f"{insert_sql[:-3]} RETURNING doc_number"

                    # Connect to sql database to post data
                    conn = None
                    cur = None

                    try:
                        conn = psycopg2.connect(
                            host=sql_parameters.hostname,
                            dbname=sql_parameters.database,
                            user=sql_parameters.username,
                            password=sql_parameters.pwd,
                            port=sql_parameters.port_id
                        )

                        conn.autocommit = True
                        cur = conn.cursor()
                        cur.execute(sql_command)
                        # Take document number
                        cor_doc_number = cur.fetchone()[0]
                        self.correcting_inv_number_entry.config(state='normal')
                        self.correcting_inv_number_entry.insert('end', cor_doc_number)
                        self.correcting_inv_number_entry.config(state='readonly')

                    except Exception as error:
                        is_correct = False
                        tkinter.messagebox.showerror(title="ERROR", message=f'{error}', parent=self)

                    else:
                        is_correct = True

                    finally:
                        if cur is not None:
                            cur.close()
                        if conn is not None:
                            conn.close()

                    if is_correct is True:
                        sql_update = f"UPDATE journal " \
                                     f"SET " \
                                     f"status='[COR]' " \
                                     f"WHERE " \
                                     f"journal_entry_date='{cor_orig_entry_date}' " \
                                     f"AND doc_number='{cor_orig_doc_number}' " \
                                     f"AND cust_id={cust_id} "

                        conn = sqlcommand.SqlCommand()
                        conn.sql_execute(sql_update)

                        answer = tkinter.messagebox.askyesno(title="Info",
                                                             message="Document added. Print correcting invoice?",
                                                             parent=self)
                        if answer:
                            self.generate_pdf()
                        self.close()

    def on_close(self, callback):
        self.callback = callback

    def close(self):
        self.callback()
        self.destroy()

    def generate_pdf(self):
        """Generate Correcting Invoice PDF file"""
        # Get company data
        sql_command = "SELECT * FROM company"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)
        company_data = execute['records'][0]

        company_name = company_data[0]
        company_tax_id_num = company_data[1]
        company_address = f"{company_data[2]} {company_data[3]}, {company_data[4]} {company_data[5]}, {company_data[6]}"
        bank_account = []
        bank_account_list = eval(company_data[8])
        for item in bank_account_list:
            if item[2] == 'True':
                bank_account.append(f"{item[0]}: {item[1]}")

        sql_command = f"SELECT * FROM customers " \
                      f"WHERE cust_id={self.customer_entry['text'][0:self.customer_entry['text'].rfind(' ~ ')]}"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)
        customer_data = execute['records'][0]

        customer_name = customer_data[1]
        customer_tax_id_num = customer_data[2]
        customer_address = f"{customer_data[3]} {customer_data[4]}, {customer_data[5]} {customer_data[6]}, " \
                           f"{customer_data[7]}"
        before = []
        after = []
        vat_dict = {}
        for n in range(len(self.correct_line_dict)):
            if self.correct_line_dict[n] == (0, 0, 0, 0):
                pass
            else:
                # Create before tuples
                before.append(tuple([self.description_entry_list[n].get(), self.net_value_entry_list[n].get(),
                              f"{self.vat_rate_hidden_label_list[n]['text']}%", self.vat_amount_entry_list[n].get()]))
                # Create after tuples
                vat_amount = float(self.vat_amount_entry_list[n].get().replace(' ', '')) + \
                             float(self.correct_line_dict[n][3].get().replace(' ', ''))
                after.append(tuple([self.description_entry_list[n].get(), self.correct_line_dict[n][1].get(),
                             f"{self.vat_rate_hidden_label_list[n]['text']}%",
                                    '{:,.2f}'.format(vat_amount).replace(',', ' ')]))
                # Create vat dictionary
                key = f"{self.vat_rate_hidden_label_list[n]['text']}%"
                value = float(self.correct_line_dict[n][3].get().replace(' ', ''))
                if key in vat_dict:
                    vat_dict[key] += value
                else:
                    vat_dict[key] = value

        # Add a thousand separator in values
        for key in vat_dict:
            vat_dict[key] = '{:,.2f}'.format(vat_dict[key]).replace(',', ' ')

        # Generating an invoice in the 'temp' folder
        output_folder = os.path.join(os.getcwd(), "temp")
        pdf_filename = os.path.join(output_folder, "correcting_invoice.pdf")

        # Create a 'temp' folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        c = canvas.Canvas(pdf_filename, pagesize=A4)
        c.setFont("Arial", 10)

        # Heading
        c.setFont("Arial-Bold", 14)
        c.drawCentredString(A4[0] / 2, 780, f"Correcting Invoice {self.correcting_inv_number_entry.get()}")
        c.setFont("Arial", 10)

        # Invoice details
        c.setFont("Arial-Bold", 10)
        c.drawString(50, 750, f"FROM:")
        c.setFont("Arial", 10)
        c.drawString(50, 730, f"{company_name}")
        c.drawString(50, 710, f"{company_tax_id_num}")
        c.drawString(50, 690, f"{company_address}")

        c.setFont("Arial-Bold", 10)
        c.drawString(50, 650, f"BILL TO:")
        c.setFont("Arial", 10)
        c.drawString(50, 630, f"{customer_name}")
        c.drawString(50, 610, f"{customer_tax_id_num}")
        c.drawString(50, 590, f"{customer_address}")

        c.drawString(50, 550, f"Reason for correction: {self.correcting_inv_reason_entry.get()}")

        c.drawRightString(545, 730, f"Correcting Invoice date: {self.correcting_inv_date_entry.get()}")
        c.drawRightString(545, 710, f"Correcting VAT date: {self.correcting_vat_date_entry.get()}")
        c.drawRightString(545, 670, f"Original Invoice number: {self.invoice_number_entry.get()}")
        c.drawRightString(545, 650, f"Original Invoice date: {self.doc_date_entry.get()}")
        c.drawRightString(545, 630, f"Original VAT date: {self.vat_date_entry.get()}")

        # Invoice item table BEFORE
        c.setFont("Arial-Bold", 10)
        c.setFillColor('red')
        c.drawString(50, 520, "BEFORE CORRECTION")
        c.setFillColor('black')
        c.drawString(50, 500, "No.")
        c.drawString(70, 500, "Service description")
        c.drawRightString(385, 500, "Net amount")
        c.drawRightString(455, 500, "VAT rate")
        c.drawRightString(545, 500, "VAT amount")
        c.line(50, 495, A4[0] - 50, 495)

        c.setFont("Arial", 10)
        y = 480
        lp = 1
        for position in before:
            service, net_amount, vat_rate, vat_amount = position
            c.drawString(50, y, str(lp))
            c.drawString(70, y, service)
            c.drawRightString(385, y, str(net_amount))
            c.drawRightString(455, y, str(vat_rate))
            c.drawRightString(545, y, str(vat_amount))
            y -= 20
            lp += 1

        # Invoice item table AFTER
        y -= 40
        c.setFont("Arial-Bold", 10)
        c.setFillColor('red')
        c.drawString(50, (y + 20), "AFTER CORRECTION")
        c.setFillColor('black')
        c.drawString(50, y, "No.")
        c.drawString(70, y, "Service description")
        c.drawRightString(385, y, "Net amount")
        c.drawRightString(455, y, "VAT rate")
        c.drawRightString(545, y, "VAT amount")
        c.line(50, (y - 5), A4[0] - 50, (y - 5))

        c.setFont("Arial", 10)
        lp = 1
        y -= 20
        for position in after:
            service, net_amount, vat_rate, vat_amount = position
            c.drawString(50, y, str(lp))
            c.drawString(70, y, service)
            c.drawRightString(385, y, str(net_amount))
            c.drawRightString(455, y, str(vat_rate))
            c.drawRightString(545, y, str(vat_amount))
            y -= 20
            lp += 1

        # Bottom sum
        c.setFont("Arial-Bold", 10)
        c.drawString(380, y - 40, "Net sum:")
        c.drawRightString(545, y - 40, f"{self.cor_net_value['text']}")
        n = 0
        for key in vat_dict:
            c.drawString(380, y - (60 + n), f"{key} VAT sum:")
            c.drawRightString(545, y - (60 + n), f"{vat_dict[key]}")
            n += 20
        c.drawString(380, y - (60 + n), "Gross sum:")
        c.drawRightString(545, y - (60 + n), f"{self.cor_gross_value['text']}")

        # Due
        c.setFillColor('red')
        c.drawString(50, y - 40, f"Due date: {self.cor_due_date_entry.get()}")
        c.setFillColor('black')
        c.drawString(50, y - 60, f"Payment method: {self.cor_payment_method_entry.get()}")
        n = 0
        c.setFont("Arial", 9)
        for account in range(len(bank_account)):
            c.drawString(50, y - (90 + n), f"{bank_account[account]}")
            n += 15

        c.save()

        # Opening the PDF file
        subprocess.Popen([pdf_filename], shell=True)


class ViewCorrectingInvoice(CorrectingInvoice):

    def __init__(self, parent, invoice_type, journal_entry_date, doc_number, cust_id, cust_name,
                 orig_doc_number, mode):
        """Open new window with view correcting invoice mode"""
        super().__init__(parent, invoice_type, journal_entry_date, doc_number, cust_id, cust_name,
                         orig_doc_number, mode)

        self.journal_entry_date = journal_entry_date
        self.doc_number = doc_number
        self.cust_id = cust_id
        self.cust_name = cust_name

        # Get data from SQL database
        self.sql_command = f"SELECT * FROM journal " \
                           f"WHERE " \
                           f"journal_entry_date='{self.journal_entry_date}' " \
                           f"AND doc_number='{self.doc_number}' " \
                           f"AND cust_id={self.cust_id} " \
                           f"AND inv_index_id IS NOT NULL"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(self.sql_command + self.order_by)
        records = execute['records']

        self.title('Correcting Invoice VIEW')

        # Fill all lines with data from original invoice
        self.correcting_inv_date_entry.set_date(records[0][3])
        self.correcting_inv_date_entry.config(state='disabled')
        self.correcting_vat_date_entry.set_date(records[0][12])
        self.correcting_vat_date_entry.config(state='disabled')
        self.cor_due_date_entry.set_date(records[0][16])
        self.cor_due_date_entry.config(state='disabled')
        self.cor_payment_method_entry.set(records[0][17])
        self.cor_payment_method_entry.config(state='disabled')
        self.correcting_inv_reason_entry.insert('end', records[0][20])
        self.correcting_inv_reason_entry.config(state='readonly')
        self.correcting_inv_number_entry.config(state='normal')
        self.correcting_inv_number_entry.insert('end', records[0][9])
        self.correcting_inv_number_entry.config(state='readonly')
        if self.invoice_type == 'Cost Purchase Invoice':
            self.internal_cor_inv_number_entry.configure(state='normal')
            self.internal_cor_inv_number_entry.insert('end', records[0][10])
            self.internal_cor_inv_number_entry.configure(state='readonly')
        if self.invoice_type == 'Cost Purchase Invoice':
            self.post_button.config(state='disabled')
        elif self.invoice_type == 'Service Sales Invoice':
            self.post_button.config(text='Print correction', command=self.generate_pdf)

        # Mark check buttons
        for item in records:
            self.positions_to_correct[item[21]].set(1)

        # Fill with correcting positions data
        for item in records:
            self.correct_value_label = tkinter.Label(self.lines_frame, text="Insert correct value")
            self.correct_value_label.grid(column=3, row=8 + item[21] * 2)

            self.corrected_entry = tkinter.Entry(self.lines_frame, width=30, justify='right', fg='red')
            self.corrected_entry.insert('end', '{:,.2f}'.format(item[7]).replace(',', ' '))
            self.corrected_entry.config(state='readonly')
            self.corrected_entry.grid(column=5, row=8 + item[21] * 2)

            self.correct_value_entry = tkinter.Entry(self.lines_frame, width=30, justify='right')
            pos_net_correct = float(item[7]) + \
                              float(self.net_value_entry_list[int(item[21])].get().replace(' ', ''))
            self.correct_value_entry.insert('end', '{:,.2f}'.format(pos_net_correct).replace(',', ' '))
            self.correct_value_entry.config(state='readonly')
            self.correct_value_entry.grid(column=4, row=8 + item[21] * 2)

            self.vat_corrected_entry = tkinter.Entry(self.lines_frame, width=30, justify='right',
                                                     fg='red')
            self.vat_corrected_entry.insert('end', '{:,.2f}'.format(item[15]).replace(',', ' '))
            self.vat_corrected_entry.config(state='readonly')
            self.vat_corrected_entry.grid(column=6, row=8 + item[21] * 2)
            self.correct_line_dict[item[21]] = (self.correct_value_label, self.correct_value_entry,
                                                               self.corrected_entry, self.vat_corrected_entry)

            # Calculate gross value
            net_all_list = [item[1][2] for item in self.correct_line_dict.items()]
            vat_all_list = [item[1][3] for item in self.correct_line_dict.items()]
            for item in net_all_list:
                if item == 0:
                    pass
                else:
                    if net_all_list[net_all_list.index(item)].get() == '':
                        net_all_list[net_all_list.index(item)] = 0
                    else:
                        net_all_list[net_all_list.index(item)] = \
                            net_all_list[net_all_list.index(item)].get().replace(' ', '')
            for item in vat_all_list:
                if item == 0:
                    pass
                else:
                    if vat_all_list[vat_all_list.index(item)].get() == '':
                        vat_all_list[vat_all_list.index(item)] = 0
                    else:
                        vat_all_list[vat_all_list.index(item)] = \
                            vat_all_list[vat_all_list.index(item)].get().replace(' ', '')

            cor_net_sum = sum(list(map(float, net_all_list)))
            cor_vat_sum = sum(list(map(float, vat_all_list)))
            cor_gross_sum = cor_net_sum + cor_vat_sum
            self.cor_net_value.config(text=f"{'{:,.2f}'.format(cor_net_sum).replace(',', ' ')}")
            self.cor_vat_value.config(text=f"{'{:,.2f}'.format(cor_vat_sum).replace(',', ' ')}")
            self.cor_gross_value.config(text=f"{'{:,.2f}'.format(cor_gross_sum).replace(',', ' ')}")

        # Disable all check buttons
        for item in range(len(self.cor_records)):
            self.check_buttons[item].config(state='disabled')


class EditCorrectingInvoice(CorrectingInvoice):

    def __init__(self, parent, invoice_type, journal_entry_date, doc_number, cust_id, cust_name,
                 orig_doc_number, mode):
        """Open new window with view correcting invoice mode"""
        super().__init__(parent, invoice_type, journal_entry_date, doc_number, cust_id, cust_name,
                         orig_doc_number, mode)

        self.title('Correcting Invoice EDIT')

        self.journal_entry_date = journal_entry_date
        self.doc_number = doc_number
        self.cust_id = cust_id
        self.cust_name = cust_name

        # Get data from SQL database
        self.sql_command = f"SELECT * FROM journal " \
                           f"WHERE " \
                           f"journal_entry_date='{self.journal_entry_date}' " \
                           f"AND doc_number='{self.doc_number}' " \
                           f"AND cust_id={self.cust_id} " \
                           f"AND inv_index_id IS NOT NULL"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(self.sql_command + self.order_by)
        records = execute['records']

        self.orig_doc_date = records[0][3]
        self.orig_vat_date = records[0][12]

        # Fill all lines with data from original invoice
        self.correcting_inv_date_entry.set_date(records[0][3])
        self.correcting_vat_date_entry.set_date(records[0][12])
        self.cor_due_date_entry.set_date(records[0][16])
        self.cor_payment_method_entry.set(records[0][17])
        self.correcting_inv_reason_entry.insert('end', records[0][20])
        self.correcting_inv_number_entry.config(state='normal')
        self.correcting_inv_number_entry.insert('end', records[0][9])
        self.correcting_inv_number_entry.config(state='readonly')
        if self.invoice_type == 'Cost Purchase Invoice':
            self.correcting_inv_number_entry.configure(state='normal')
            self.internal_cor_inv_number_entry.configure(state='normal')
            self.internal_cor_inv_number_entry.insert('end', records[0][10])
            self.internal_cor_inv_number_entry.configure(state='readonly')
        self.post_button.config(text='Save changes', command=self.save_cor_inv_edit)

        # Mark check buttons
        for item in records:
            self.positions_to_correct[item[21]].set(1)

        # Fill with correcting positions data
        for item in records:
            self.correct_value_label = tkinter.Label(self.lines_frame, text="Insert correct value")
            self.correct_value_label.grid(column=3, row=8 + item[21] * 2)

            self.corrected_entry = tkinter.Entry(self.lines_frame, width=30, justify='right', fg='red')
            self.corrected_entry.insert('end', '{:,.2f}'.format(item[7]).replace(',', ' '))
            self.corrected_entry.config(state='readonly')
            self.corrected_entry.grid(column=5, row=8 + item[21] * 2)

            self.correct_value_entry = tkinter.Entry(self.lines_frame, width=30, justify='right')
            pos_net_correct = float(item[7]) + \
                              float(self.net_value_entry_list[int(item[21])].get().replace(' ', ''))
            self.correct_value_entry.insert('end', '{:,.2f}'.format(pos_net_correct).replace(',', ' '))
            self.correct_value_entry.config(state='readonly')
            self.correct_value_entry.grid(column=4, row=8 + item[21] * 2)

            self.vat_corrected_entry = tkinter.Entry(self.lines_frame, width=30, justify='right',
                                                     fg='red')
            self.vat_corrected_entry.insert('end', '{:,.2f}'.format(item[15]).replace(',', ' '))
            self.vat_corrected_entry.config(state='readonly')
            self.vat_corrected_entry.grid(column=6, row=8 + item[21] * 2)
            self.correct_line_dict[item[21]] = (self.correct_value_label, self.correct_value_entry,
                                                               self.corrected_entry, self.vat_corrected_entry)

            # Calculate gross value
            net_all_list = [item[1][2] for item in self.correct_line_dict.items()]
            vat_all_list = [item[1][3] for item in self.correct_line_dict.items()]
            for item in net_all_list:
                if item == 0:
                    pass
                else:
                    if net_all_list[net_all_list.index(item)].get() == '':
                        net_all_list[net_all_list.index(item)] = 0
                    else:
                        net_all_list[net_all_list.index(item)] = \
                            net_all_list[net_all_list.index(item)].get().replace(' ', '')
            for item in vat_all_list:
                if item == 0:
                    pass
                else:
                    if vat_all_list[vat_all_list.index(item)].get() == '':
                        vat_all_list[vat_all_list.index(item)] = 0
                    else:
                        vat_all_list[vat_all_list.index(item)] = \
                            vat_all_list[vat_all_list.index(item)].get().replace(' ', '')

            cor_net_sum = sum(list(map(float, net_all_list)))
            cor_vat_sum = sum(list(map(float, vat_all_list)))
            cor_gross_sum = cor_net_sum + cor_vat_sum
            self.cor_net_value.config(text=f"{'{:,.2f}'.format(cor_net_sum).replace(',', ' ')}")
            self.cor_vat_value.config(text=f"{'{:,.2f}'.format(cor_vat_sum).replace(',', ' ')}")
            self.cor_gross_value.config(text=f"{'{:,.2f}'.format(cor_gross_sum).replace(',', ' ')}")

        # Disable all check buttons
        for item in range(len(self.cor_records)):
            self.check_buttons[item].config(state='disabled')

    def save_cor_inv_edit(self):
        """Update changes from correcting invoice edit mode in SQL database"""
        doc_date = self.correcting_inv_date_entry.get()
        vat_date = self.correcting_vat_date_entry.get()
        orig_doc_date = self.orig_doc_date
        orig_vat_date = self.orig_vat_date
        doc_date_obj = datetime.strptime(doc_date, "%d-%m-%Y")
        vat_date_obj = datetime.strptime(vat_date, "%d-%m-%Y")

        if int(doc_date_obj.strftime("%m")) != int(orig_doc_date.strftime("%m")) or \
                int(doc_date_obj.strftime("%Y")) != int(orig_doc_date.strftime("%Y")):
            tkinter.messagebox.showerror(title="ERROR", message="Document month date must remain the same", parent=self)
        elif int(vat_date_obj.strftime("%m")) != int(orig_vat_date.strftime("%m")) or \
                int(vat_date_obj.strftime("%Y")) != int(orig_vat_date.strftime("%Y")):
            tkinter.messagebox.showerror(title="ERROR", message="Vat month date must remain the same", parent=self)
        else:
            cor_doc_date = self.correcting_inv_date_entry.get()
            cor_vat_date = 'null' if self.correcting_vat_date_entry.get() == '' \
                else f"'{self.correcting_vat_date_entry.get()}'"
            cor_cust_id = \
                self.customer_entry['text'][0:self.customer_entry['text'].rfind(" ~ ")]
            cor_doc_number = self.correcting_inv_number_entry.get()
            cor_inv_due_date = self.cor_due_date_entry.get()
            cor_inv_payment_method = self.cor_payment_method_entry.get()
            cor_inv_reason = self.correcting_inv_reason_entry.get()

            sql_command = f"UPDATE journal \n" \
                          f"SET \n" \
                          f"doc_date=TO_DATE('{cor_doc_date}', 'dd-mm-yyyy'), " \
                          f"vat_date=TO_DATE({cor_vat_date}, 'dd-mm-yyyy'), " \
                          f"cust_id={cor_cust_id}, " \
                          f"doc_number='{cor_doc_number}', " \
                          f"inv_due_date=TO_DATE('{cor_inv_due_date}', 'dd-mm-yyyy'), " \
                          f"inv_payment_method='{cor_inv_payment_method}'," \
                          f"cor_reason='{cor_inv_reason}' \n" \
                          f"WHERE \n" \
                          f"journal_entry_date='{self.journal_entry_date}' " \
                          f"AND doc_number='{self.doc_number}' " \
                          f"AND cust_id={self.cust_id} "

            conn = sqlcommand.SqlCommand()
            conn.sql_execute(sql_command)

            self.close()


class InvoiceRegister(tkinter.Toplevel):

    def __init__(self, parent, invoice_type):
        """Invoice register"""
        super().__init__(parent)

        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute("SELECT * FROM invoice_settings ORDER BY invoice_type DESC")
        self.inv_details = execute['records']

        # Specify document type
        self.invoice_type = invoice_type
        self.inv_type_short = [item for item in self.inv_details if f'{item[0]}' == self.invoice_type][0][1]
        self.cust_account = [item for item in self.inv_details if f'{item[0]}' == self.invoice_type][0][2]

        # Configure window
        self.title(f"Invoice register - {self.invoice_type}")
        self.resizable(False, False)

        self.invoice_reg_frame = tkinter.Frame(self)
        self.invoice_reg_frame.grid(column=0, row=0)

        self.invoice_reg_tree_scroll = tkinter.Scrollbar(self.invoice_reg_frame)
        self.invoice_reg_tree_scroll.grid(column=1, row=0, sticky='ns')

        self.invoice_register_treeview()

        # Create Options Frame
        self.invoice_reg_options = tkinter.Frame(self)
        self.invoice_reg_options.grid(column=1, row=0, sticky='n')

        self.add_document_button = tkinter.Button(self.invoice_reg_options, text="Add invoice",
                                                   command=self.add_invoice, pady=15, padx=15, width=20)
        self.add_document_button.grid(column=0, row=0)
        self.correcting_invoice_button = tkinter.Button(self.invoice_reg_options, text="Add correcting invoice",
                                                        command=self.correcting_invoice, pady=15, padx=15, width=20)
        self.correcting_invoice_button.grid(column=0, row=1)
        self.view_document_button = tkinter.Button(self.invoice_reg_options, text="View document",
                                                   command=self.view_invoice, pady=15, padx=15, width=20)
        self.view_document_button.grid(column=0, row=2)
        self.edit_document_button = tkinter.Button(self.invoice_reg_options, text="Edit document",
                                                   command=self.edit_invoice, pady=15, padx=15, width=20)
        self.edit_document_button.grid(column=0, row=3)

    def invoice_register_treeview(self):
        """Create invoice register treeview"""
        account = ''
        if self.invoice_type == 'Service Sales Invoice':
            account = 'dt_account_num'
        elif self.invoice_type == 'Cost Purchase Invoice':
            account = 'ct_account_num'
        # Connect to sql database to add account
        self.sql_command = f"SELECT no_journal, doc_date, doc_number, " \
                           f"TO_CHAR(COALESCE(CAST(amount AS DECIMAL(1000, 2)),0), 'fm999G999G999G990.00') " \
                           f"AS gross_value, " \
                           f"COALESCE(journal.cust_id, 0) AS cust_id, COALESCE(customers.cust_name,'') AS cust_name, " \
                           f"doc_type, vat_date, journal_entry_date AS created, COALESCE(status, '') AS status, " \
                           f"COALESCE(cor_orig_doc_number,'') AS orig_doc_number, int_doc_number " \
                           f"FROM journal " \
                           f"LEFT JOIN customers " \
                           f"ON journal.cust_id = customers.cust_id " \
                           f"LEFT JOIN chart_of_accounts " \
                           f"ON journal.dt_account_num = chart_of_accounts.account_num " \
                           f"WHERE doc_type='{self.inv_type_short}' AND {account} != '' " \
                           f"OR doc_type='[COR] {self.inv_type_short}' AND {account} != '' "

        self.order_by = ' ORDER BY no_journal ASC'

        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(self.sql_command + self.order_by)

        column_names = execute['column_names']

        self.invoice_reg_tree = ttk.Treeview(self.invoice_reg_frame, columns=column_names, show='headings', height=35,
                                             selectmode='browse', yscrollcommand=self.invoice_reg_tree_scroll.set)
        self.invoice_reg_tree_scroll.config(command=self.invoice_reg_tree.yview)

        column = 0
        for _ in column_names:
            self.invoice_reg_tree.heading(column_names[column], text=f'{column_names[column]}')
            column += 1

            # Adjust column width
            self.invoice_reg_tree.column(column_names[0], width=0)
            self.invoice_reg_tree.column(column_names[1], width=100)
            self.invoice_reg_tree.column(column_names[2], width=100)
            self.invoice_reg_tree.column(column_names[3], width=100, anchor='e')
            self.invoice_reg_tree.column(column_names[4], width=100, anchor='e')
            self.invoice_reg_tree.column(column_names[5], width=170)
            self.invoice_reg_tree.column(column_names[6], width=100)
            self.invoice_reg_tree.column(column_names[7], width=100)
            self.invoice_reg_tree.column(column_names[8], width=170)
            self.invoice_reg_tree.column(column_names[9], width=100)
            self.invoice_reg_tree.column(column_names[10], width=100)
            self.invoice_reg_tree.column(column_names[11], width=100)

        self.invoice_reg_tree["displaycolumns"] = (column_names[1:])

        self.invoice_reg_tree.grid(row=0, column=0)

        records = execute['records']

        record = 0
        for _ in records:
            self.invoice_reg_tree.insert('', tkinter.END, values=records[record])
            record += 1

    def selected_invoice(self):
        """Take selected document from tree"""
        selected = self.invoice_reg_tree.focus()
        self.selected_inv = self.invoice_reg_tree.item(selected).get('values')
        return self.selected_inv

    def add_invoice(self):
        """Open new window to add invoice"""
        self.inv_window = Invoice(self, self.invoice_type)
        self.inv_window.on_close(self.refresh_inv_reg_tree)

    def view_invoice(self):
        """Open new window with view invoice mode"""
        if self.selected_invoice()[6] == f'[COR] {self.inv_type_short}':
            self.view_correcting_invoice()
        else:
            journal_entry_date = self.selected_invoice()[8]
            doc_number = self.selected_invoice()[2]
            cust_id = self.selected_invoice()[4]
            cust_name = self.selected_invoice()[5]
            self.inv_window = ViewInvoice(self, self.invoice_type, journal_entry_date, doc_number, cust_id, cust_name)

    def edit_invoice(self):
        """Open new window with edit invoice mode"""
        if self.selected_invoice()[6] == f'[COR] {self.inv_type_short}':
            self.edit_correcting_invoice()
        else:
            journal_entry_date = self.selected_invoice()[8]
            doc_number = self.selected_invoice()[2]
            cust_id = self.selected_invoice()[4]
            cust_name = self.selected_invoice()[5]
            self.inv_window = EditInvoice(self, self.invoice_type, journal_entry_date, doc_number, cust_id, cust_name)
            self.inv_window.on_close(self.refresh_inv_reg_tree)

    def correcting_invoice(self):
        """Open new window to create correcting invoice"""
        # Check first if selected document is invoice
        if self.selected_invoice()[6] == f'[COR] {self.inv_type_short}':
            tkinter.messagebox.showerror(title='ERROR', message='Cannot issue correct to correcting invoice.',
                                         parent=self)
        else:
            journal_entry_date = self.selected_invoice()[8]
            doc_number = self.selected_invoice()[2]
            cust_id = self.selected_invoice()[4]
            cust_name = self.selected_invoice()[5]
            orig_doc_number = self.selected_invoice()[10]
            self.cor_inv_window = CorrectingInvoice(self, self.invoice_type, journal_entry_date, doc_number, cust_id,
                                                    cust_name, orig_doc_number, 'create')
            self.cor_inv_window.on_close(self.refresh_inv_reg_tree)

    def view_correcting_invoice(self):
        """Open new window with view correcting invoice mode"""
        journal_entry_date = self.selected_invoice()[8]
        doc_number = self.selected_invoice()[2]
        cust_id = self.selected_invoice()[4]
        cust_name = self.selected_invoice()[5]
        orig_doc_number = self.selected_invoice()[10]

        self.cor_inv_window = ViewCorrectingInvoice(self, self.invoice_type, journal_entry_date, doc_number,
                                                    cust_id, cust_name, orig_doc_number, 'view')

    def edit_correcting_invoice(self):
        """Open new window with edit correcting invoice mode"""
        journal_entry_date = self.selected_invoice()[8]
        doc_number = self.selected_invoice()[2]
        cust_id = self.selected_invoice()[4]
        cust_name = self.selected_invoice()[5]
        orig_doc_number = self.selected_invoice()[10]

        self.cor_inv_window = EditCorrectingInvoice(self, self.invoice_type, journal_entry_date, doc_number,
                                                    cust_id, cust_name, orig_doc_number, 'view')
        self.cor_inv_window.on_close(self.refresh_inv_reg_tree)

    def refresh_inv_reg_tree(self):
        """Refresh customer tree"""
        self.invoice_reg_tree.delete(*self.invoice_reg_tree.get_children())
        self.invoice_register_treeview()


class InvoiceSettings(tkinter.Toplevel):

    def __init__(self, parent):
        """Invoice settings"""
        super().__init__(parent)
        self.title('Invoice settings')
        self.config(padx=10, pady=10)
        self.resizable(False, False)

        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute("SELECT * FROM invoice_settings ORDER BY invoice_type DESC")
        self.rows = execute['records']

        header_1 = tkinter.Label(self, text='Invoice Type', width=25)
        header_1.grid(column=0, row=0)
        header_1 = tkinter.Label(self, text='Invoice Type Short', width=25)
        header_1.grid(column=1, row=0)
        header_1 = tkinter.Label(self, text='Customer account number', width=25)
        header_1.grid(column=2, row=0)

        self.accounts = []
        n = 0
        for row in self.rows:
            entry_1 = tkinter.Entry(self, width=30)
            entry_1.insert('end', string=row[0])
            entry_1.config(state='readonly')
            entry_1.grid(column=0, row=1 + n)
            entry_2 = tkinter.Entry(self, width=30)
            entry_2.insert('end', string=row[1])
            entry_2.config(state='readonly')
            entry_2.grid(column=1, row=1 + n)
            entry_3 = tkinter.Button(self, text=row[2], command=self.select_account, width=30, background='white',
                                     activebackground='white', borderwidth=1, relief='sunken', anchor='w')
            entry_3.grid(column=2, row=1 + n)
            entry_3.bind('<Button-1>', self.clicked_button)
            self.accounts.append(entry_3)
            n += 1

        save_button = tkinter.Button(self, text="Save", command=self.save, width=15)
        save_button.grid(column=2, row=1 + n)

    def save(self):
        """Save changes in Invoice settings window"""
        # Ask if change account name
        answer = tkinter.messagebox.askyesno(title="WARNING", message=f"Save changes'?", parent=self)

        if answer:
            n = 0
            for row in self.rows:
                sql_command = f"UPDATE invoice_settings SET cust_account_num='{self.accounts[0 + n]['text']}' " \
                              f"WHERE invoice_type='{row[0]}'"
                n += 1

                # Connect to sql database to delete account
                conn = sqlcommand.SqlCommand()
                conn.sql_execute(sql_command)

            self.destroy()

    def select_account(self):
        """Open new window with account to choose"""
        self.account_window = chart_of_accounts.ChartOfAccounts(self)
        self.account_window.sql_command = "SELECT * FROM chart_of_accounts " \
                                          "WHERE customer_settlement='True' ORDER BY account_num"
        self.account_window.grab_set()
        self.selected_account_button = self.clicked_btn
        add_customer_button = tkinter.Button(self.account_window, text='Select account',
                                             command=self.select_account_command, font=30)
        add_customer_button.grid(column=0, row=1, columnspan=2)

    def select_account_command(self):
        """Get selected account from account window"""
        self.acc_details = self.account_window.selected_account()
        self.acc_num = self.account_window.selected_account_num()
        self.selected_account_button.config(text=f"{self.acc_num}")
        self.account_window.destroy()

    def clicked_button(self, event):
        """Return clicked button"""
        self.clicked_btn = event.widget
