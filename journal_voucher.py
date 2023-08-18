import datetime
import tkinter
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import psycopg2
import chart_of_accounts
import customers
import sqlcommand
import sql_parameters
import vat_rates
import re
from functools import partial
from datetime import datetime


class JournalVoucher(tkinter.Toplevel):

    def __init__(self, parent, journal_type):
        """Journal voucher main window"""
        super().__init__(parent)

        self.journal_type = journal_type

        self.title(self.journal_type)
        self.config(padx=15, pady=15)
        self.resizable(False, False)

        self.journal_type_label = tkinter.Label(self, text=f'{self.journal_type}', font=30)
        self.journal_type_label.grid(column=3, row=1, columnspan=3)

        # Entries
        self.doc_date_label = tkinter.Label(self, text="Document date")
        self.doc_date_label.grid(column=1, row=0)
        self.doc_date_entry = DateEntry(self, selectmode='day', locale='en_US', date_pattern='dd-mm-y')
        self.doc_date_entry.grid(column=1, row=1)

        self.vat_date_label = tkinter.Label(self, text="Vat date")
        self.vat_date_label.grid(column=2, row=0)
        self.vat_date_entry = DateEntry(self, selectmode='day', locale='en_US', date_pattern='dd-mm-y')
        self.vat_date_entry.delete(0, 'end')
        self.vat_date_entry.grid(column=2, row=1)

        self.add_new_line_button = tkinter.Button(self, text='Add new line',
                                                  command=self.add_line)
        self.add_new_line_button.grid(column=6, row=1)
        self.remove_last_line_button = tkinter.Button(self, text='Remove last line',
                                                      command=self.remove_line)
        self.remove_last_line_button.grid(column=7, row=1)

        self.document_number_label = tkinter.Label(self, text="Document number")
        self.document_number_label.grid(column=1, row=3)
        self.document_number_entry = tkinter.Entry(self, width=30, state='readonly')
        self.document_number_entry.grid(column=2, row=3)

        self.space = tkinter.Canvas(self, height=10, width=0)
        self.space.grid(column=1, row=4)

        self.headers_frame = tkinter.Frame(self)
        self.headers_frame.grid(column=0, row=5, columnspan=8)

        # Headers
        self.no_journal_label = tkinter.Label(self, width=7)
        self.no_journal_label.grid(column=0, row=5)
        self.description_label = tkinter.Label(self, text="Description", width=28)
        self.description_label.grid(column=1, row=5, columnspan=2)
        self.account_dt_label = tkinter.Label(self, text="Account DT", width=28)
        self.account_dt_label.grid(column=3, row=5)
        self.account_ct_label = tkinter.Label(self, text='Account CT', width=28)
        self.account_ct_label.grid(column=4, row=5)
        self.value_label = tkinter.Label(self, text='Value', width=28)
        self.value_label.grid(column=5, row=5)
        self.customer_label = tkinter.Label(self, text="Customer", width=28)
        self.customer_label.grid(column=6, row=5)
        self.vat_rate_label = tkinter.Label(self, text='Vat rate', width=28)
        self.vat_rate_label.grid(column=7, row=5)

        # Set first row
        self.row = 1

        # Bottom widget
        self.dt_sum_label = tkinter.Label(self, text='DT:  0.00')
        self.dt_sum_label.grid(column=3, row=8)
        self.ct_sum_label = tkinter.Label(self, text='CT:  0.00')
        self.ct_sum_label.grid(column=4, row=8)
        self.balance_label = tkinter.Label(self, text='Balance:  0.00', fg='red')
        self.balance_label.grid(column=5, row=8)
        self.post_button = tkinter.Button(self, text="Post in journal", command=self.post_in_journal)
        self.post_button.grid(column=7, row=9)

        # Add scrollbar
        self.frame = tkinter.Frame(self)
        self.frame.grid(column=0, row=7, columnspan=8)

        self.scrollbar = tkinter.Scrollbar(self.frame)
        self.scrollbar.grid(column=8, row=0, sticky='ns')

        self.canvas = tkinter.Canvas(self.frame, yscrollcommand=self.scrollbar.set, width=1330, height=482,
                                     highlightthickness=0, borderwidth=1, relief='groove')
        self.canvas.grid(column=0, row=0, columnspan=8)

        self.lines_frame = tkinter.Frame(self.canvas)
        self.lines_frame.grid(column=0, row=0, columnspan=8)

        self.lines_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.lines_frame, anchor='nw')

        self.canvas.config(yscrollcommand=self.scrollbar.set)

        self.scrollbar.config(command=self.canvas.yview)

        # Lists for all added lines
        self.no_label_list = []
        self.description_entry_list = []
        self.account_dt_entry_list = []
        self.account_ct_entry_list = []
        self.amount_entry_list = []
        self.customer_entry_list = []
        self.vat_rate_entry_list = []

        self.list_of_str_var = []
        self.list_of_dt_account_cust_set_type = []
        self.list_of_ct_account_cust_set_type = []

        self.add_line()

        # Right mouse click menu
        self.r_click_menu = tkinter.Menu(self, tearoff=False)
        self.r_click_menu.add_command(label="Delete", command=self.delete_choice)

    def add_line(self):
        """Add new lines to post"""
        # Create entries for each line
        self.no_label = tkinter.Label(self.lines_frame, text=f'{self.row}', width=3)
        self.no_label.grid(column=0, row=self.row)

        self.description_entry = tkinter.Entry(self.lines_frame, width=50)
        self.description_entry.grid(column=1, row=self.row, columnspan=2)

        self.account_dt_entry = tkinter.Button(self.lines_frame, text='', command=self.select_account_dt, width=30,
                                               background='white', activebackground='white',
                                               borderwidth=1, relief='sunken', anchor='w')
        self.account_dt_entry.grid(column=3, row=self.row)

        self.account_ct_entry = tkinter.Button(self.lines_frame, text='', command=self.select_account_ct, width=30,
                                               background='white', activebackground='white',
                                               borderwidth=1, relief='sunken', anchor='w')
        self.account_ct_entry.grid(column=4, row=self.row)

        self.amount_str_var = tkinter.StringVar()
        self.amount_str_var.set('0.00')
        self.amount_entry = tkinter.Entry(self.lines_frame, textvariable=self.amount_str_var, width=30, justify='right')
        self.amount_entry.grid(column=5, row=self.row)

        self.customer_entry = tkinter.Button(self.lines_frame, text="", command=self.select_customer, width=30,
                                             background='white', activebackground='white',
                                             borderwidth=1, relief='sunken', anchor='w')
        self.customer_entry.grid(column=6, row=self.row)

        self.vat_rate_entry = tkinter.Button(self.lines_frame, text='', command=self.select_vat, width=20,
                                             background='white', activebackground='white',
                                             borderwidth=1, relief='sunken', anchor='w')
        self.vat_rate_entry.grid(column=7, row=self.row)

        self.row += 1

        # bind name of widget with function
        self.account_dt_entry.bind('<Button-1>', self.clicked_button)
        self.account_ct_entry.bind('<Button-1>', self.clicked_button)
        self.customer_entry.bind('<Button-1>', self.clicked_button)
        self.vat_rate_entry.bind('<Button-1>', self.clicked_button)
        self.account_dt_entry.bind('<Button-3>', self.clicked_right_button)
        self.account_ct_entry.bind('<Button-3>', self.clicked_right_button)
        self.customer_entry.bind('<Button-3>', self.clicked_right_button)
        self.vat_rate_entry.bind('<Button-3>', self.clicked_right_button)
        self.amount_entry.bind('<FocusOut>', self.calculate_balance)

        # Append all created widgets to list
        self.no_label_list.append(self.no_label)
        self.description_entry_list.append(self.description_entry)
        self.account_dt_entry_list.append(self.account_dt_entry)
        self.account_ct_entry_list.append(self.account_ct_entry)
        self.amount_entry_list.append(self.amount_entry)
        self.customer_entry_list.append(self.customer_entry)
        self.vat_rate_entry_list.append(self.vat_rate_entry)

        self.list_of_str_var.append(self.amount_str_var)
        self.list_of_dt_account_cust_set_type.append(False)
        self.list_of_ct_account_cust_set_type.append(False)

        for item in range(int(len(self.list_of_str_var))):
            self.list_of_str_var[item].trace('w', partial(self.entry_fill, self.amount_entry_list[item]))

    def remove_line(self):
        """Remove last line to post"""
        if self.row > 2:
            self.no_label_list[-1].destroy()
            self.no_label_list.pop()
            self.description_entry_list[-1].destroy()
            self.description_entry_list.pop()
            self.account_dt_entry_list[-1].destroy()
            self.account_dt_entry_list.pop()
            self.account_ct_entry_list[-1].destroy()
            self.account_ct_entry_list.pop()
            self.amount_entry_list[-1].destroy()
            self.amount_entry_list.pop()
            self.customer_entry_list[-1].destroy()
            self.customer_entry_list.pop()
            self.vat_rate_entry_list[-1].destroy()
            self.vat_rate_entry_list.pop()
            self.list_of_str_var.pop()
            self.row -= 1

    def clicked_button(self, event):
        """Return clicked button"""
        self.clicked_btn = event.widget

    def clicked_right_button(self, event):
        """Return clicked right button"""
        self.clicked_right_btn = event.widget
        self.r_click_menu.tk_popup(event.x_root, event.y_root)

    def delete_choice(self):
        """Delete choice from button entry widgets"""
        self.r_clicked_button = self.clicked_right_btn
        self.r_clicked_button.config(text='')
        # Set False values in account customer settlement type list
        if self.r_clicked_button in self.account_dt_entry_list:
            index = self.account_dt_entry_list.index(self.r_clicked_button)
            self.list_of_dt_account_cust_set_type[index] = False
        elif self.r_clicked_button in self.account_ct_entry_list:
            index = self.account_ct_entry_list.index(self.r_clicked_button)
            self.list_of_ct_account_cust_set_type[index] = False

    def select_customer(self):
        """Open new window with customer to choose"""
        self.customer_window = customers.Customers(self)
        self.customer_window.grab_set()
        add_customer_button = tkinter.Button(self.customer_window, text='Select customer',
                                             command=self.select_customer_command, font=30)
        add_customer_button.grid(column=0, row=1, columnspan=2)

    def select_customer_command(self):
        """Get selected customer from customer window"""
        cust_details = self.customer_window.selected_customer()
        self.actual_cust_button = self.clicked_btn
        self.actual_cust_button.config(text=f"{cust_details[0]} ~ {cust_details[1]}")
        self.customer_window.destroy()

    def select_account_dt(self):
        """Open new window with account to choose"""
        self.account_window = chart_of_accounts.ChartOfAccounts(self)
        self.account_window.grab_set()
        self.selected_account_button = self.clicked_btn
        add_customer_button = tkinter.Button(
            self.account_window, text='Select account', command=self.select_dt_account_command, font=30)
        add_customer_button.grid(column=0, row=1, columnspan=2)

    def select_account_ct(self):
        """Open new window with account to choose"""
        self.account_window = chart_of_accounts.ChartOfAccounts(self)
        self.account_window.grab_set()
        self.selected_account_button = self.clicked_btn
        add_customer_button = tkinter.Button(
            self.account_window, text='Select account', command=self.select_ct_account_command, font=30)
        add_customer_button.grid(column=0, row=1, columnspan=2)

    def select_dt_account_command(self):
        """Get selected account from account window"""
        position = self.account_dt_entry_list.index(self.clicked_btn)
        self.acc_details = self.account_window.selected_account()
        self.acc_num = self.account_window.selected_account_num()

        if self.acc_details[2] == "✔":
            # Check if there is customer settlements account already
            if self.list_of_ct_account_cust_set_type[position] == False:
                self.list_of_dt_account_cust_set_type[position] = True
                self.select_customer()
                self.clicked_btn = self.customer_entry_list[position]

                self.selected_account_button.config(text=f"{self.acc_num} ~ {self.acc_details[1]}")
                self.account_window.destroy()
                self.calculate_balance(event=None)
            else:
                tkinter.messagebox.showerror(title="ERROR", message="It's not possible to add two customer settlements "
                                                                    "accounts in one line", parent=self.account_window)
        elif self.acc_details[3] == "✔":
            self.list_of_dt_account_cust_set_type[position] = False
            self.select_vat()
            self.clicked_btn = self.vat_rate_entry_list[position]

            self.selected_account_button.config(text=f"{self.acc_num} ~ {self.acc_details[1]}")
            self.account_window.destroy()
            self.calculate_balance(event=None)
        else:
            self.list_of_dt_account_cust_set_type[position] = False
            self.selected_account_button.config(text=f"{self.acc_num} ~ {self.acc_details[1]}")
            self.account_window.destroy()
            self.calculate_balance(event=None)

    def select_ct_account_command(self):
        """Get selected account from account window"""
        position = self.account_ct_entry_list.index(self.clicked_btn)
        self.acc_details = self.account_window.selected_account()
        self.acc_num = self.account_window.selected_account_num()

        if self.acc_details[2] == "✔":
            # Check if there is customer settlements account already
            if self.list_of_dt_account_cust_set_type[position] == False:
                self.list_of_ct_account_cust_set_type[position] = True
                self.select_customer()
                self.clicked_btn = self.customer_entry_list[position]

                self.selected_account_button.config(text=f"{self.acc_num} ~ {self.acc_details[1]}")
                self.account_window.destroy()
                self.calculate_balance(event=None)
            else:
                tkinter.messagebox.showerror(title="ERROR", message="It's not possible to add two customer settlements "
                                                                    "accounts in one line", parent=self.account_window)
        elif self.acc_details[3] == "✔":
            self.list_of_ct_account_cust_set_type[position] = False
            self.select_vat()
            self.clicked_btn = self.vat_rate_entry_list[position]

            self.selected_account_button.config(text=f"{self.acc_num} ~ {self.acc_details[1]}")
            self.account_window.destroy()
            self.calculate_balance(event=None)
        else:
            self.list_of_ct_account_cust_set_type[position] = False
            self.selected_account_button.config(text=f"{self.acc_num} ~ {self.acc_details[1]}")
            self.account_window.destroy()
            self.calculate_balance(event=None)

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
        self.actual_vat_button = self.clicked_btn
        self.actual_vat_button.config(text=f'{self.vat_details[0]}')
        self.vat_window.destroy()

    def calculate_balance(self, event):
        """Calculate and update widgets from bottom line: dt sum, ct sum and balance"""
        lines = int(len(self.no_label_list))
        dt_sum = 0
        ct_sum = 0
        for n in range(lines):
            if self.amount_entry_list[n].get() == '':
                pass
            else:
                if self.account_dt_entry_list[n]['text'] == '':
                    pass
                else:
                    dt_sum += float(self.amount_entry_list[n].get().replace(' ', ''))
                if self.account_ct_entry_list[n]['text'] == '':
                    pass
                else:
                    ct_sum += float(self.amount_entry_list[n].get().replace(' ', ''))

            self.dt_sum_label.config(text=f"DT:  {'{:,.2f}'.format(dt_sum).replace(',', ' ')}")
            self.ct_sum_label.config(text=f"CT:  {'{:,.2f}'.format(ct_sum).replace(',', ' ')}")

        self.balance = dt_sum - ct_sum
        self.balance_label.config(text=f"Balance:  {'{:,.2f}'.format(self.balance).replace(',', ' ')}")

    def entry_fill(self, entry, *args):
        """Format entry widget and returns digits with a thousand separator"""
        try:
            if len(entry.get()) >= 20:
                entry.delete(entry.index("end") - 1)
            else:
                result = re.sub(r'[^0-9-]', '', entry.get())
                sep = '{:,.2f}'.format(float(result) / 100).replace(',', ' ')
                entry.delete(0, 'end')
                entry.insert('end', sep)
        except Exception:
            pass

    def post_in_journal(self):
        """Posts in journal in sql database, checks if all necessary fields are filled"""
        self.calculate_balance(event=None)
        insert_sql = f'INSERT INTO journal(doc_type, doc_date, description, dt_account_num, ct_account_num, amount,' \
                     f'cust_id, doc_number, int_doc_number, vat_id, vat_date) ' \
                     f'VALUES\n'

        doc_type = self.journal_type
        doc_date = self.doc_date_entry.get()
        description = []
        dt_account = []
        ct_account = []
        amount = []
        cust_id = []
        vat_id = []
        vat_date = 'null' if self.vat_date_entry.get() == '' else f"'{self.vat_date_entry.get()}'"

        lines = int(len(self.no_label_list))
        for n in range(lines):
            description.append(self.description_entry_list[n].get())
            dt_account.append(self.account_dt_entry_list[n]['text'])
            ct_account.append(self.account_ct_entry_list[n]['text'])
            amount.append(self.amount_entry_list[n].get())
            cust_id.append(self.customer_entry_list[n]['text'])
            vat_id.append(self.vat_rate_entry_list[n]['text'])

        for item in range(len(dt_account)):
            dt_account[item] = dt_account[item][0:dt_account[item].rfind(" ~ ")]
            if dt_account[item] == '':
                dt_account[item] = 'null'
            else:
                dt_account[item] = f"'{dt_account[item]}'"

        for item in range(len(ct_account)):
            ct_account[item] = ct_account[item][0:ct_account[item].rfind(" ~ ")]
            if ct_account[item] == '':
                ct_account[item] = 'null'
            else:
                ct_account[item] = f"'{ct_account[item]}'"

        for item in range(len(amount)):
            if amount[item] == '':
                amount[item] = 0
            else:
                amount[item] = amount[item].replace(' ', '')

        for item in range(len(cust_id)):
            if cust_id[item] == '':
                cust_id[item] = 'null'
            else:
                cust_id[item] = cust_id[item][0:cust_id[item].rfind(" ~ ")]

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
            if dt_account[item] == 'null' and ct_account[item] == 'null':
                empty_account = True
            if float(amount[item]) == 0:
                empty_values = True

        # Check if everything is filled
        if empty_description is True:
            tkinter.messagebox.showerror(title="ERROR", message="Missing description", parent=self)
        elif empty_account is True:
            tkinter.messagebox.showerror(title="ERROR", message="Missing account", parent=self)
        elif empty_values is True:
            tkinter.messagebox.showerror(title="ERROR", message="Missing value column", parent=self)
        elif float(self.balance) != 0:
            tkinter.messagebox.showerror(title="ERROR", message="Document is not balanced", parent=self)
        else:
            # Take doc number
            date_str = self.doc_date_entry.get()
            date = datetime.datetime.strptime(date_str, '%d-%m-%Y')
            month = date.strftime('%m')
            year = date.strftime('%Y')
            sql_take_number = f"SELECT doc_num FROM document_numbers WHERE " \
                              f"doc_name='Journal voucher' AND doc_month={month} AND doc_year={year}"
            conn = sqlcommand.SqlCommand()
            execute = conn.sql_execute(sql_take_number)
            if execute['records'] == []:
                tkinter.messagebox.showerror(title="ERROR", message=f"{year} year is not opened", parent=self)
            else:
                number = execute['records'][0][0]
                sql_update_number = f"UPDATE document_numbers SET " \
                                    f"doc_num = {number + 1} " \
                                    f"WHERE " \
                                    f"doc_name='Journal voucher' AND doc_month={month} AND doc_year={year}"
                conn = sqlcommand.SqlCommand()
                conn.sql_execute(sql_update_number)

                doc_number = f"{number}/{month}/{year}"

                # Create insert lines
                values_string = []
                for n in range(lines):
                    values_string.append(f"('{doc_type}', TO_DATE('{doc_date}', 'dd-mm-yyyy'), "
                                         f"'{description[n]}', {dt_account[n]}, "
                                         f"{ct_account[n]}, {amount[n]}, {cust_id[n]}, "
                                         f"'{doc_number}', '{doc_number}', {vat_id[n]}, "
                                         f"TO_DATE({vat_date}, 'dd-mm-yyyy')),\n")

                for values in range(lines):
                    insert_sql += values_string[values]

                sql_command = insert_sql[:-2]

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
                    self.close()
                    tkinter.messagebox.showinfo(title="Info", message="Posted in journal")

    def on_close(self, callback):
        self.callback = callback

    def close(self):
        self.callback()
        self.destroy()


class ViewJournalVoucher(JournalVoucher):

    def __init__(self, parent, journal_type, doc_type, doc_date, int_doc_number):
        """Open window of journal document to view"""
        super().__init__(parent, journal_type)

        self.journal_type = journal_type

        self.doc_type = doc_type
        self.doc_date = doc_date
        self.int_doc_number = int_doc_number
        self.title("Journal voucher - VIEW")

        # Get document data from SQL base
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(f"""
                            SELECT no_journal, journal_entry_date, doc_type, doc_date, description,
                            COALESCE(journal.dt_account_num, '') AS dt_account_num,
                            COALESCE(dt.account_name, '') AS dt_account_name,
                            COALESCE(journal.ct_account_num, '') AS ct_account_num,
                            COALESCE(ct.account_name, '') AS ct_account_name,
                            COALESCE(CAST(amount AS DECIMAL(1000, 2)),0) amount,
                            COALESCE(journal.cust_id, 0) AS cust_id, COALESCE(customers.cust_name,'') AS customer_name,
                            doc_number, int_doc_number, COALESCE(vat_id,'') AS vat_id, vat_date, 
                            COALESCE(status, '') AS status
                            FROM journal
                            LEFT JOIN customers
                            ON journal.cust_id = customers.cust_id
                            LEFT JOIN chart_of_accounts AS dt
                            ON journal.dt_account_num = dt.account_num
                            LEFT JOIN chart_of_accounts AS ct
                            ON journal.ct_account_num = ct.account_num 
                            WHERE doc_type='{doc_type}' 
                            AND doc_date='{self.doc_date}' 
                            AND int_doc_number='{self.int_doc_number}'  
                            ORDER BY no_journal ASC
                            """)

        records = execute['records']
        lines = len(records)

        # Insert data to window
        self.doc_date_entry.set_date(records[0][3])
        if records[0][15] is None:
            pass
        else:
            self.vat_date_entry.set_date(records[0][15])

        self.document_number_entry.config(state='normal')
        self.document_number_entry.insert('end', string=records[0][12])
        self.document_number_entry.config(state='readonly')

        for _ in range(lines - 1):
            self.add_line()

        self.no_journal = []
        for item in range(lines):
            self.no_journal.append(records[item][0])
            self.description_entry_list[item].insert('end', string=records[item][4])
            self.description_entry_list[item].configure(state='readonly')
            if records[item][5] == '':
                self.account_dt_entry_list[item].configure(state='disabled', background='SystemButtonFace')
            else:
                self.account_dt_entry_list[item].configure(
                    text=f'{records[item][5]} ~ {records[item][6]}', state='disabled', background='SystemButtonFace')
            if records[item][7] == '':
                self.account_ct_entry_list[item].configure(state='disabled', background='SystemButtonFace')
            else:
                self.account_ct_entry_list[item].configure(
                    text=f'{records[item][7]} ~ {records[item][8]}', state='disabled', background='SystemButtonFace')
            self.amount_entry_list[item].delete(0, 'end')
            self.amount_entry_list[item].insert('end', string=records[item][9])
            self.amount_entry_list[item].configure(state='readonly')
            if records[item][11] == '':
                self.customer_entry_list[item].configure(state='disabled', background='SystemButtonFace')
            else:
                self.customer_entry_list[item].configure(
                    text=f'{records[item][10]} ~ {records[item][11]}', state='disabled', background='SystemButtonFace')
            self.vat_rate_entry_list[item].configure(text=records[item][14], state='disabled',
                                                     background='SystemButtonFace')

        # Disable rest of widgets
        self.document_number_entry.configure(state='readonly')
        self.add_new_line_button.configure(state='disabled')
        self.remove_last_line_button.configure(state='disabled')
        self.post_button.configure(state='disabled')
        self.doc_date_entry.configure(state='disabled')
        self.vat_date_entry.configure(state='disabled')

        # Calculate balance
        self.calculate_balance(event=None)


class EditJournalVoucher(JournalVoucher):

    def __init__(self, parent, journal_type, doc_type, doc_date, int_doc_number):
        """Open window of journal document to edit"""
        super().__init__(parent, journal_type)

        self.journal_type = journal_type

        self.doc_type = doc_type
        self.doc_date = doc_date
        self.int_doc_number = int_doc_number
        self.title("Journal voucher - VIEW")

        # Get document data from SQL base
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(f"""
                        SELECT no_journal, journal_entry_date, doc_type, doc_date, description,
                        COALESCE(journal.dt_account_num, '') AS dt_account_num,
                        COALESCE(dt.account_name, '') AS dt_account_name,
                        COALESCE(journal.ct_account_num, '') AS ct_account_num,
                        COALESCE(ct.account_name, '') AS ct_account_name,
                        COALESCE(CAST(amount AS DECIMAL(1000, 2)),0) amount,
                        COALESCE(journal.cust_id, 0) AS cust_id, COALESCE(customers.cust_name,'') AS customer_name,
                        doc_number, int_doc_number, COALESCE(vat_id,'') AS vat_id, vat_date, 
                        COALESCE(status, '') AS status
                        FROM journal
                        LEFT JOIN customers
                        ON journal.cust_id = customers.cust_id
                        LEFT JOIN chart_of_accounts AS dt
                        ON journal.dt_account_num = dt.account_num
                        LEFT JOIN chart_of_accounts AS ct
                        ON journal.ct_account_num = ct.account_num 
                        WHERE doc_type='{doc_type}' 
                        AND doc_date='{self.doc_date}' 
                        AND int_doc_number='{self.int_doc_number}'  
                        ORDER BY no_journal ASC
                        """)

        records = execute['records']

        self.orig_doc_date = records[0][3]
        self.orig_vat_date = records[0][15]

        # Insert data to window
        self.doc_date_entry.set_date(records[0][3])
        if records[0][15] is None:
            pass
        else:
            self.vat_date_entry.set_date(records[0][15])

        self.document_number_entry.config(state='normal')
        self.document_number_entry.insert('end', string=records[0][12])
        self.document_number_entry.config(state='readonly')

        lines = len(records)
        for _ in range(lines - 1):
            self.add_line()

        self.no_journal_list = []
        for item in range(lines):
            self.no_journal_list.append(records[item][0])
            self.description_entry_list[item].insert('end', string=records[item][4])
            if records[item][5] == '':
                pass
            else:
                self.account_dt_entry_list[item].configure(
                    text=f'{records[item][5]} ~ {records[item][6]}')
            if records[item][7] == '':
                pass
            else:
                self.account_ct_entry_list[item].configure(
                    text=f'{records[item][7]} ~ {records[item][8]}')
            self.amount_entry_list[item].delete(0, 'end')
            self.amount_entry_list[item].insert('end', string=records[item][9])
            if records[item][11] == '':
                pass
            else:
                self.customer_entry_list[item].configure(
                    text=f'{records[item][10]} ~ {records[item][11]}')
            self.vat_rate_entry_list[item].configure(text=records[item][14])
        self.post_button.configure(text='Save changes', command=self.save_changes)

        # Calculate balance
        self.calculate_balance(event=None)

    def save_changes(self):
        """Connect to SQL base to update data"""
        doc_date = self.doc_date_entry.get()
        vat_date = self.doc_date_entry.get() if self.vat_date_entry.get() == '' else self.vat_date_entry.get()
        orig_doc_date = self.orig_doc_date
        orig_vat_date = self.orig_doc_date if self.orig_vat_date is None else self.orig_vat_date
        doc_date_obj = datetime.strptime(doc_date, "%d-%m-%Y")
        vat_date_obj = datetime.strptime(vat_date, "%d-%m-%Y")

        if int(doc_date_obj.strftime("%m")) != int(orig_doc_date.strftime("%m")) or \
                int(doc_date_obj.strftime("%Y")) != int(orig_doc_date.strftime("%Y")):
            tkinter.messagebox.showerror(title="ERROR", message="Document month date must remain the same", parent=self)
        elif int(vat_date_obj.strftime("%m")) != int(orig_vat_date.strftime("%m")) or \
                int(vat_date_obj.strftime("%Y")) != int(orig_vat_date.strftime("%Y")):
            tkinter.messagebox.showerror(title="ERROR", message="Vat month date must remain the same", parent=self)
        else:
            doc_type = self.doc_type
            doc_number = self.document_number_entry.get()
            int_doc_number = self.int_doc_number
            doc_date = self.doc_date_entry.get()
            description = []
            dt_account = []
            ct_account = []
            amount = []
            cust_id = []
            vat_id = []
            vat_date = 'null' if self.vat_date_entry.get() == '' \
                else f"'{self.vat_date_entry.get()}'"

            lines = int(len(self.no_label_list))
            for item in range(lines):
                description.append(self.description_entry_list[item].get())
                dt_account.append(self.account_dt_entry_list[item]['text'])
                ct_account.append(self.account_ct_entry_list[item]['text'])
                amount.append(self.amount_entry_list[item].get())
                cust_id.append(self.customer_entry_list[item]['text'])
                vat_id.append(self.vat_rate_entry_list[item]['text'])

            for item in range(len(dt_account)):
                dt_account[item] = dt_account[item][0:dt_account[item].rfind(" ~ ")]
                if dt_account[item] == '':
                    dt_account[item] = 'null'
                else:
                    dt_account[item] = f"'{dt_account[item]}'"

            for item in range(len(ct_account)):
                ct_account[item] = ct_account[item][0:ct_account[item].rfind(" ~ ")]
                if ct_account[item] == '':
                    ct_account[item] = 'null'
                else:
                    ct_account[item] = f"'{ct_account[item]}'"

            for item in range(len(amount)):
                if amount[item] == '':
                    amount[item] = 0
                else:
                    amount[item] = amount[item].replace(' ', '')

            for item in range(len(cust_id)):
                if cust_id[item] == '':
                    cust_id[item] = 'null'
                else:
                    cust_id[item] = cust_id[item][0:cust_id[item].rfind(" ~ ")]

            for item in range(len(vat_id)):
                if vat_id[item] == '':
                    vat_id[item] = 'null'
                else:
                    vat_id[item] = f"'{vat_id[item]}'"

            sql_command = []
            for item in range(len(self.no_journal_list)):
                sql_command.append(f"UPDATE journal "
                                   f"SET "
                                   f"doc_date=TO_DATE('{doc_date}', 'dd-mm-yyyy'), "
                                   f"description='{description[item]}', "
                                   f"dt_account_num={dt_account[item]}, "
                                   f"ct_account_num={ct_account[item]}, "
                                   f"amount={amount[item]}, "
                                   f"cust_id={cust_id[item]}, "
                                   f"vat_id={vat_id[item]}, "
                                   f"vat_date=TO_DATE({vat_date}, 'dd-mm-yyyy') "
                                   f"WHERE no_journal={self.no_journal_list[item]} ")

            insert_sql = f'INSERT INTO journal(doc_type, doc_date, description, dt_account_num, ct_account_num, amount,' \
                         f'cust_id, doc_number, int_doc_number, vat_id, vat_date) ' \
                         f'VALUES\n'

            # Check if new lines were added
            new_lines_added = False
            values_string = []
            for index, value in enumerate(self.no_label_list):
                if index >= len(self.no_journal_list):
                    new_lines_added = True
                    # Create insert lines
                    values_string.append(f"('{doc_type}', TO_DATE('{doc_date}', 'dd-mm-yyyy'), "
                                         f"'{description[index]}', {dt_account[index]}, "
                                         f"{ct_account[index]}, {amount[index]}, {cust_id[index]}, "
                                         f"'{doc_number}', '{int_doc_number}', {vat_id[index]}, "
                                         f"TO_DATE({vat_date}, 'dd-mm-yyyy')),\n")
                else:
                    pass

            sql_command_insert = ''
            if new_lines_added == True:
                for values in range(len(values_string)):
                    insert_sql += values_string[values]

                sql_command_insert = insert_sql[:-2]

            empty_description = False
            empty_account = False
            empty_values = False
            for item in range(lines):
                if description[item] == '':
                    empty_description = True
                if dt_account[item] == 'null' and ct_account[item] == 'null':
                    empty_account = True
                if float(amount[item]) == 0:
                    empty_values = True

            # Check if everything is filled
            if empty_description is True:
                tkinter.messagebox.showerror(title="ERROR", message="Missing description", parent=self)
            elif empty_account is True:
                tkinter.messagebox.showerror(title="ERROR", message="Missing account", parent=self)
            elif empty_values is True:
                tkinter.messagebox.showerror(title="ERROR", message="Missing values in DT or CT column", parent=self)
            elif float(self.balance) != 0:
                tkinter.messagebox.showerror(title="ERROR", message="Document is not balanced", parent=self)
            else:
                for command in range(len(sql_command)):
                    # Connect to sql database to update data
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
                        cur.execute(sql_command[command])

                    except Exception as error:
                        tkinter.messagebox.showerror(title="ERROR", message=f'{error}', parent=self)

                    finally:
                        if cur is not None:
                            cur.close()
                        if conn is not None:
                            conn.close()

                if new_lines_added == True:
                    # Connect to sql database to add new data
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
                        cur.execute(sql_command_insert)

                    except Exception as error:
                        tkinter.messagebox.showerror(title="ERROR", message=f'{error}', parent=self)

                    finally:
                        if cur is not None:
                            cur.close()
                        if conn is not None:
                            conn.close()

                self.close()


class Vouchers(tkinter.Toplevel):

    def __init__(self, parent):
        """Sales invoice main window"""
        super().__init__(parent)

        self.title("Vouchers")
        self.resizable(False, False)

        # Vouchers list frame
        self.vouchers_list_frame = tkinter.Frame(self)
        self.vouchers_list_frame.grid(column=0, row=0)

        self.vouchers_tree_scroll = tkinter.Scrollbar(self.vouchers_list_frame)
        self.vouchers_tree_scroll.grid(column=1, row=0, sticky='ns')

        self.vouchers_treeview()

        # Create Options Frame
        self.vouchers_options = tkinter.Frame(self)
        self.vouchers_options.grid(column=1, row=0, sticky='n')

        self.add_voucher_button = tkinter.Button(self.vouchers_options, text="Add voucher",
                                                 command=self.add_voucher, pady=15, padx=15, width=20)
        self.add_voucher_button.grid(column=0, row=0)
        self.view_voucher_button = tkinter.Button(self.vouchers_options, text="View voucher",
                                                  command=self.view_voucher, pady=15, padx=15, width=20)
        self.view_voucher_button.grid(column=0, row=1)
        self.edit_voucher_button = tkinter.Button(self.vouchers_options, text="Edit voucher",
                                                  command=self.edit_voucher, pady=15, padx=15, width=20)
        self.edit_voucher_button.grid(column=0, row=2)
        self.storno_voucher_button = tkinter.Button(self.vouchers_options, text="Storno voucher",
                                                    command=self.storno_voucher, pady=15, padx=15, width=20)
        self.storno_voucher_button.grid(column=0, row=3)

        # SQL command
        self.sql_command = f'''
            SELECT no_journal, journal_entry_date, doc_type, doc_date, description,
            COALESCE(journal.dt_account_num, '') AS dt_account_num,
            COALESCE(dt.account_name, '') AS dt_account_name,
            COALESCE(journal.ct_account_num, '') AS ct_account_num,
            COALESCE(ct.account_name, '') AS ct_account_name,
            TO_CHAR(COALESCE(CAST(amount AS DECIMAL(1000, 2)),0), 'fm999G999G999G990.00') amount,
            COALESCE(journal.cust_id, 0) AS cust_id, COALESCE(customers.cust_name,'') AS customer_name,
            doc_number, int_doc_number, COALESCE(vat_id,'') AS vat_id, vat_date, COALESCE(status, '') AS status
            FROM journal
            LEFT JOIN customers
            ON journal.cust_id = customers.cust_id
            LEFT JOIN chart_of_accounts AS dt
            ON journal.dt_account_num = dt.account_num
            LEFT JOIN chart_of_accounts AS ct
            ON journal.ct_account_num = ct.account_num
            '''
        self.order_by = ' ORDER BY doc_date ASC'

    def vouchers_treeview(self):
        """Create vouchers treeview"""
        # Connect with SQL database
        sql_command = f"SELECT doc_type, doc_date, doc_number, " \
                      f"TO_CHAR(COALESCE(CAST(SUM(amount) AS DECIMAL(1000, 2)),0), 'fm999G999G999G990.00') amount, " \
                      f"COALESCE(status, '') AS status " \
                      f"FROM journal WHERE doc_type='Journal voucher' " \
                      f"GROUP BY (doc_date, doc_type, doc_number, status) " \
                      f"ORDER BY doc_date"

        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)

        column_names = execute['column_names']
        self.vouchers_tree = ttk.Treeview(self.vouchers_list_frame, columns=column_names, show='headings', height=35)
        self.vouchers_tree_scroll.config(command=self.vouchers_tree.yview)

        column = 0
        for _ in column_names:
            self.vouchers_tree.heading(column_names[column], text=f'{column_names[column]}')
            column += 1

        # Adjust column width
        self.vouchers_tree.column(column_names[0], width=100)
        self.vouchers_tree.column(column_names[1], width=100)
        self.vouchers_tree.column(column_names[2], width=150)
        self.vouchers_tree.column(column_names[3], width=150, anchor='e')
        self.vouchers_tree.column(column_names[4], width=120, anchor='center')

        self.vouchers_tree.grid(column=0, row=0)

        records = execute['records']
        record = 0
        for _ in records:
            self.vouchers_tree.insert('', tkinter.END, values=records[record])
            record += 1

    def selected_voucher(self):
        """Take selected customer"""
        selected = self.vouchers_tree.focus()
        cust = self.vouchers_tree.item(selected).get('values')
        return cust

    def add_voucher(self):
        """Open new window to add journal voucher"""
        JournalVoucher(self, "Journal voucher")

    def view_voucher(self):
        """Open window of journal document to view"""
        try:
            doc_type = self.selected_voucher()[0]
            doc_date = self.selected_voucher()[1]
            int_doc_number = self.selected_voucher()[2]
            ViewJournalVoucher(self, doc_type, doc_type, doc_date, int_doc_number)
        except:
            tkinter.messagebox.showerror(title="ERROR", message="Select document", parent=self)

    def edit_voucher(self):
        """Open window of journal document to edit"""
        try:
            if self.selected_voucher()[4] == "Storno":
                tkinter.messagebox.showerror(title="ERROR", message="Cannot edit storno document", parent=self)
            else:
                doc_type = self.selected_voucher()[0]
                doc_date = self.selected_voucher()[1]
                int_doc_number = self.selected_voucher()[2]
                self.journal_voucher = EditJournalVoucher(self, doc_type, doc_type, doc_date, int_doc_number)
                self.journal_voucher.on_close(self.refresh_vouchers_tree)

        except:
            tkinter.messagebox.showerror(title="ERROR", message="Select document", parent=self)

    def storno_voucher(self):
        """Create negative debit or credit amounts to reverse original journal account entries"""
        try:
            answer = tkinter.messagebox.askyesno(title="WARNING", message="Storno document?", parent=self)
            if answer:
                if self.selected_voucher()[4] == "Storno":
                    tkinter.messagebox.showerror(title="ERROR", message="Storn document cannot be storned", parent=self)
                else:
                    select = self.selected_voucher()
                    # Get document data from SQL base
                    conn = sqlcommand.SqlCommand()
                    execute = conn.sql_execute(f"""
                            {self.sql_command} WHERE 
                            doc_type='{select[0]}' 
                            AND doc_date='{select[1]}' 
                            AND doc_number='{select[2]}'
                            {self.order_by}
                            """)

                    records = execute['records']

                    doc_type = []
                    doc_date = []
                    description = []
                    dt_account = []
                    ct_account = []
                    amount = []
                    cust_id = []
                    doc_number = []
                    vat_id = []
                    vat_date = []

                    lines = len(records)

                    for item in range(len(records)):
                        doc_type.append(records[item][2])
                        doc_date.append(records[item][3])
                        description.append(f"[STORNO] - {records[item][4]}")
                        dt_account.append(records[item][5])
                        ct_account.append(records[item][7])
                        amount.append(records[item][9] if
                                        records[item][9] == '0.00' else f'-{records[item][9].replace(" ", "")}')
                        cust_id.append('null' if records[item][10] == 0 else records[item][10])
                        doc_number.append(f"[STORNO] - {records[item][12]}")
                        vat_id.append('null' if records[item][14] == '' else f"'{records[item][14]}'")
                        vat_date.append('null' if records[item][15] is None else f"'{records[item][15]}'")

                    for item in range(len(dt_account)):
                        if dt_account[item] == '':
                            dt_account[item] = 'null'
                        else:
                            dt_account[item] = f"'{dt_account[item]}'"

                    for item in range(len(ct_account)):
                        if ct_account[item] == '':
                            ct_account[item] = 'null'
                        else:
                            ct_account[item] = f"'{ct_account[item]}'"

                    insert_sql = f'INSERT INTO journal(doc_type, doc_date, description, ' \
                                 f'dt_account_num, ct_account_num, amount,' \
                                 f'cust_id, doc_number, int_doc_number, vat_id, vat_date, status) ' \
                                 f'VALUES\n'

                    n = 0
                    values_string = []
                    for _ in range(lines):
                        values_string.append(f"('{doc_type[0 + n]}', '{doc_date[0 + n]}', "
                                             f"'{description[0 + n]}', {dt_account[0 + n]}, "
                                             f"{ct_account[0 + n]}, {amount[0 + n]}, {cust_id[0 + n]}, "
                                             f"'{doc_number[0 + n]}', '{doc_number[0 + n]}', {vat_id[0 + n]}, "
                                             f"{vat_date[0 + n]}, 'Storno'),\n")
                        n += 1

                    for values in range(lines):
                        insert_sql += values_string[values]

                    sql_command = insert_sql[:-2]

                    conn = sqlcommand.SqlCommand()
                    conn.sql_execute(sql_command)

                    sql_command = f"UPDATE journal SET status='Storno' WHERE doc_type='{select[0]}' " \
                                  f"AND doc_date='{select[1]}' AND doc_number='{select[2]}'"
                    conn = sqlcommand.SqlCommand()
                    conn.sql_execute(sql_command)

                    self.refresh_vouchers_tree()
        except:
            tkinter.messagebox.showerror(title="ERROR", message="Select document", parent=self)

    def refresh_vouchers_tree(self):
        """Refresh customer tree"""
        self.vouchers_tree.delete(*self.vouchers_tree.get_children())
        self.vouchers_treeview()
