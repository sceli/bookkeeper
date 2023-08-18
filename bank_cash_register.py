import tkinter
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import customer_settlements
import customers
import sqlcommand
import chart_of_accounts
import re
import ast
from functools import partial
from datetime import datetime, timedelta


class ListOfRegister(tkinter.Toplevel):

    def __init__(self, parent, cash_flow_type):
        """Open window with list of Bank / Check reckonings"""
        super().__init__(parent)

        # Specify cash flow type
        self.cash_flow_type = cash_flow_type
        self.title(f'Select {self.cash_flow_type}')
        self.resizable(False, False)

        self.select_frame = tkinter.Frame(self)
        self.select_frame.grid(column=0, row=0)

        self.registers_treeview()

        # Create Options Frame
        self.select_options = tkinter.Frame(self)
        self.select_options.grid(column=1, row=0, sticky='n')

        self.select_button = tkinter.Button(self.select_options, text='Select',
                                            command=self.select_command, pady=15, padx=15, width=20)
        self.select_button.grid(column=0, row=0)

        self.add_new = tkinter.Button(self.select_options, text='Add new',
                                      command=self.add_new_window, pady=15, padx=15, width=20)
        self.add_new.grid(column=0, row=1)

        self.edit = tkinter.Button(self.select_options, text='Edit', command=self.edit_window,
                                   pady=15, padx=15, width=20)
        self.edit.grid(column=0, row=2)

        self.delete = tkinter.Button(self.select_options, text='Delete', command=self.delete,
                                     pady=15, padx=15, width=20)
        self.delete.grid(column=0, row=3)

    def registers_treeview(self):
        """Create register treeview"""
        # Connect to sql database to add account
        self.sql_command = f"SELECT * FROM bank_cash_list " \
                           f"WHERE register_type='{self.cash_flow_type}' " \
                           f"ORDER BY bank_cash_list"
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(self.sql_command)

        column_names = execute['column_names']
        self.registers_tree = ttk.Treeview(self.select_frame, columns=column_names, show='headings', height=10)
        column = 0
        for _ in column_names:
            self.registers_tree.heading(column_names[column], text=f'{column_names[column]}')
            column += 1
        self.registers_tree.grid(column=0, row=0)

        self.registers_tree["displaycolumns"] = (column_names[1:])

        records = execute['records']
        record = 0
        for _ in records:
            self.registers_tree.insert('', tkinter.END, values=records[record])
            record += 1

    def selected_register(self):
        """Take selected account details"""
        selected = self.registers_tree.focus()
        self.selected_reg = self.registers_tree.item(selected).get('values')
        return self.selected_reg

    def select_command(self):
        """Open new window with Register"""
        if self.selected_register() == '':
            pass
        else:
            RegistersList(self, self.cash_flow_type, self.selected_register()[1], self.selected_register()[2],
                          self.selected_register()[3])
            self.withdraw()

    def add_new_window(self):
        """Open new window to create new register"""
        self.add_new_win = tkinter.Toplevel()
        self.add_new_win.title('Add new')
        self.add_new_win.config(padx=5, pady=5)
        self.add_new_win.resizable(False, False)

        register_label = tkinter.Label(self.add_new_win, text=f'{self.cash_flow_type} name', width=15, anchor='e')
        register_label.grid(column=0, row=0)
        self.register_entry = tkinter.Entry(self.add_new_win, width=25)
        self.register_entry.grid(column=1, row=0)
        short_reg_label = tkinter.Label(self.add_new_win, text=f'Short name', width=15, anchor='e')
        short_reg_label.grid(column=0, row=1)
        self.short_reg_entry = tkinter.Entry(self.add_new_win, width=25)
        self.short_reg_entry.grid(column=1, row=1)
        account_label = tkinter.Label(self.add_new_win, text='Account', width=15, anchor='e')
        account_label.grid(column=0, row=2)
        self.account_number = tkinter.Button(self.add_new_win, text='', command=self.select_account, width=21,
                                               highlightbackground='grey', borderwidth=1, relief='sunken', anchor='w')
        self.account_number.grid(column=1, row=2)
        add_button = tkinter.Button(self.add_new_win, text='Create', command=self.add_new_command)
        add_button.grid(column=1, row=3)

    def select_account(self):
        """Open new window with account to choose"""
        self.account_window = chart_of_accounts.ChartOfAccounts(self)
        self.account_window.grab_set()
        add_customer_button = tkinter.Button(self.account_window, text='Select account',
                                             command=self.select_account_dt_command, font=30)
        add_customer_button.grid(column=0, row=1, columnspan=2)

    def select_account_dt_command(self):
        """Get selected account from account window"""
        self.acc_details = self.account_window.selected_account()
        self.acc_num = self.account_window.selected_account_num()
        self.account_number.config(text=f"{self.acc_num}")
        self.account_window.destroy()

    def add_new_command(self):
        """Connect to SQL database and create register"""
        sql_command = f"INSERT INTO bank_cash_list(register_type, register, reg_short, account_num) " \
                      f"VALUES" \
                      f"('{self.cash_flow_type}', '{self.register_entry.get()}', " \
                      f"'{self.short_reg_entry.get()}', '{self.account_number['text']}')"

        # Connect to sql database to add account
        conn = sqlcommand.SqlCommand()
        conn.sql_execute(sql_command)

        self.add_new_win.destroy()

        # Refresh chart of accounts tree
        self.refresh_registers_tree()

    def edit_window(self):
        """Open new window to change register name"""
        if self.selected_register() == '':
            pass
        else:
            name = self.selected_register()[1]
            account = self.selected_register()[2]
            # Create window
            self.edit_win = tkinter.Toplevel()
            self.edit_win.title('Edit')
            self.edit_win.config(padx=5, pady=5)
            self.edit_win.resizable(False, False)

            register_label = tkinter.Label(self.edit_win, text=f'{self.cash_flow_type} name', width=10)
            register_label.grid(column=0, row=0)
            self.register_entry = tkinter.Entry(self.edit_win, width=25)
            self.register_entry.insert('end', name)
            self.register_entry.grid(column=1, row=0)

            account_label = tkinter.Label(self.edit_win, text='Account', width=10)
            account_label.grid(column=0, row=1)
            self.account_number = tkinter.Button(self.edit_win, text=account, command=self.select_account, width=21,
                                                 highlightbackground='grey', borderwidth=1, relief='sunken', anchor='w')
            self.account_number.grid(column=1, row=1)

            change_name_button = tkinter.Button(self.edit_win, text='Save changes',
                                                command=self.edit_command)
            change_name_button.grid(column=1, row=2)

    def edit_command(self):
        """Connect to SQL database to update register"""
        sql_command = f"UPDATE bank_cash_list SET " \
                      f"register='{self.register_entry.get()}', " \
                      f"account_num='{self.account_number['text']}' " \
                      f"WHERE register='{self.selected_register()[1]}'"

        # Connect to sql database to delete account
        conn = sqlcommand.SqlCommand()
        conn.sql_execute(sql_command)

        # Refresh chart of accounts tree
        self.refresh_registers_tree()
        self.edit_win.destroy()

    def delete(self):
        """Connect to sql database and delete register"""
        if self.selected_register() == '':
            pass
        else:
            self.selected_register()
            # Ask if delete account
            answer = tkinter.messagebox.askyesno(title="WARNING",
                                                 message=f"Delete '{self.selected_register()[1]}'?",
                                                 parent=self)
            if answer:
                sql_command = f"DELETE FROM bank_cash_list WHERE register='{self.selected_register()[1]}'"

                # Connect to sql database to delete account
                conn = sqlcommand.SqlCommand()
                conn.sql_execute(sql_command)

                # Refresh chart of accounts tree
                self.refresh_registers_tree()

    def refresh_registers_tree(self):
        """Refresh chart of accounts tree"""
        self.registers_tree.delete(*self.registers_tree.get_children())
        self.registers_treeview()


class RegistersList(tkinter.Toplevel):

    def __init__(self, parent, cash_flow_type, register, reg_short, reg_account):
        """Registers list of Bank statements and Cash reckonings"""
        super().__init__(parent)

        # Specify cash flow type
        self.cash_flow_type = cash_flow_type
        self.register = register
        self.reg_short = reg_short
        self.reg_account = reg_account

        self.title(self.register)
        self.resizable(False, False)

        self.register_frame = tkinter.Frame(self)
        self.register_frame.grid(column=0, row=0)

        self.register_list_treeview()

        # Create Options Frame
        self.register_options = tkinter.Frame(self)
        self.register_options.grid(column=1, row=0, sticky='n')

        open_btn_txt = ''
        if self.cash_flow_type == 'Bank':
            open_btn_txt = "Open bank statement"
        elif self.cash_flow_type == 'Cash register':
            open_btn_txt = "Open cash register"
        self.open_bank_cash_statement_button = tkinter.Button(self.register_options, text=open_btn_txt,
                                                              command=self.open_register, pady=15, padx=15, width=20)
        self.open_bank_cash_statement_button.grid(column=0, row=0)

        new_btn_txt = ''
        if self.cash_flow_type == 'Bank':
            new_btn_txt = "New bank statement"
        elif self.cash_flow_type == 'Cash register':
            new_btn_txt = "New cash register"
        self.new_bank_cash_button = tkinter.Button(self.register_options, text=new_btn_txt,
                                                   command=self.new_register, pady=15, padx=15, width=20)
        self.new_bank_cash_button.grid(column=0, row=1)

        delete_btn_txt = ''
        if self.cash_flow_type == 'Bank':
            delete_btn_txt = "Delete bank statement"
        elif self.cash_flow_type == 'Cash register':
            delete_btn_txt = "Delete cash register"
        self.delete_register_button = tkinter.Button(self.register_options, text=delete_btn_txt,
                                                     command=self.delete_register, pady=15, padx=15, width=20)
        self.delete_register_button.grid(column=0, row=2)

    def register_list_treeview(self):
        """Create register treeview"""
        self.sql_command = f"SELECT register_type, register, register_date, register_number, " \
                           f"TO_CHAR(COALESCE(CAST(balance AS DECIMAL(1000, 2)),0), 'fm999G999G999G990.00') balance, " \
                           f"TO_CHAR(COALESCE(CAST(withdrawals AS DECIMAL(1000, 2)),0), 'fm999G999G999G990.00') " \
                           f"withdrawals, " \
                           f"TO_CHAR(COALESCE(CAST(deposits AS DECIMAL(1000, 2)),0), 'fm999G999G999G990.00')deposits " \
                           f"FROM bank_cash_register WHERE register='{self.register}' ORDER BY register_date"
        conn = sqlcommand.SqlCommand()
        self.execute = conn.sql_execute(self.sql_command)

        column_names = self.execute['column_names']
        self.register_list_tree = ttk.Treeview(self.register_frame, columns=column_names, show='headings', height=35)
        column = 0
        for _ in column_names:
            self.register_list_tree.heading(column_names[column], text=f'{column_names[column]}')
            column += 1

        # Adjust column width
        self.register_list_tree.column(column_names[0], width=100)
        self.register_list_tree.column(column_names[1], width=170)
        self.register_list_tree.column(column_names[2], width=100)
        self.register_list_tree.column(column_names[3], width=100)
        self.register_list_tree.column(column_names[4], width=130, anchor='e')
        self.register_list_tree.column(column_names[5], width=130, anchor='e')
        self.register_list_tree.column(column_names[6], width=130, anchor='e')

        self.register_list_tree.grid(column=0, row=0)

        records = self.execute['records']
        record = 0
        for _ in records:
            self.register_list_tree.insert('', tkinter.END, values=records[record])
            record += 1

    def selected_register(self):
        """Take selected account details"""
        selected = self.register_list_tree.focus()
        self.selected_reg_l = self.register_list_tree.item(selected).get('values')
        return self.selected_reg_l

    def open_register(self):
        """Open new window with register"""
        if self.selected_register() == '':
            pass
        else:
            # Get previous balance from previous date
            sql_command = f"SELECT * FROM bank_cash_register " \
                          f"WHERE register_date<'{self.selected_register()[2]}' AND register='{self.register}' " \
                          f"ORDER BY register_date DESC LIMIT 1"
            conn = sqlcommand.SqlCommand()
            execute = conn.sql_execute(sql_command)
            try:
                previous_balance = execute['records'][0][4]
            except:
                previous_balance = '0.00'

            # Change date format
            register_date = self.selected_register()[2]
            date = datetime.strptime(register_date, "%Y-%m-%d")
            new_date_string = date.strftime("%d-%m-%Y")

            register_window = BankCashRegister(self, self.cash_flow_type, self.register, self.selected_register()[3],
                                               new_date_string, self.reg_account, self.selected_register()[4],
                                               previous_balance)
            self.withdraw()
            register_window.lift()

    def new_register(self):
        """Open new window to create new register"""
        new_number = f"1/{self.reg_short}"
        new_date_string = datetime.now()
        self.last_date = None
        if self.execute['records'] == []:
            pass
        else:
            # Take number and date from last register
            last_number = self.execute['records'][-1][3]
            self.last_date = self.execute['records'][-1][2]

            # Suggest new number and date
            new_number = str(int(re.sub('\D', '', last_number)) + 1) + f"/{self.reg_short}"
            new_date = self.last_date + timedelta(days=1)
            new_date_string = new_date.strftime("%d-%m-%Y")

        self.new_register_window = tkinter.Toplevel(pady=10, padx=10)
        self.new_register_window.title(f"Add new - {self.register}")
        self.new_register_window.resizable(False, False)

        register_number_label = tkinter.Label(self.new_register_window, text='Number', width=10, anchor='w')
        register_number_label.grid(column=0, row=0)
        self.register_number_entry = tkinter.Entry(self.new_register_window, width=15)
        self.register_number_entry.insert('end', new_number)
        self.register_number_entry.grid(column=1, row=0)
        if new_number != '':
            self.register_number_entry.config(state='readonly')
        register_date_label = tkinter.Label(self.new_register_window, text='Date', width=10, anchor='w')
        register_date_label.grid(column=0, row=1)
        self.register_date_entry = DateEntry(self.new_register_window, selectmode='day', locale='en_US',
                                          date_pattern='dd-mm-y')
        self.register_date_entry.set_date(new_date_string)
        self.register_date_entry.grid(column=1, row=1)
        create_button = tkinter.Button(self.new_register_window, text='Add', command=self.create_button_command)
        create_button.grid(column=1, row=2)

    def create_button_command(self):
        """Add new register"""
        # Check if new register date is not earlier than last register
        if self.last_date != None and \
                self.last_date >= datetime.strptime(self.register_date_entry.get(), '%d-%m-%Y').date():
            tkinter.messagebox.showerror(title="ERROR", message="Date cannot be earlier than last register",
                                         parent=self.new_register_window)
        else:
            previous_balance = 0.00
            if self.execute['records'] == []:
                pass
            else:
                # Get previous balance from previous date
                sql_command = f"SELECT * FROM bank_cash_register " \
                              f"WHERE register_date<'{datetime.now()}' AND register='{self.register}' " \
                              f"ORDER BY register_date DESC LIMIT 1"
                conn = sqlcommand.SqlCommand()
                execute = conn.sql_execute(sql_command)
                try:
                    previous_balance = execute['records'][0][4]
                except:
                    previous_balance = 0.00

            sql_command = f"INSERT INTO bank_cash_register" \
                          f"(register_type, register, register_date, register_number, balance, " \
                          f"deposits, withdrawals) " \
                          f"VALUES \n" \
                          f"('{self.cash_flow_type}', '{self.register}', " \
                          f"TO_DATE('{self.register_date_entry.get()}', 'dd-mm-yyyy'), " \
                          f"'{self.register_number_entry.get()}', {previous_balance}, 0.00, 0.00)"

            conn = sqlcommand.SqlCommand()
            conn.sql_execute(sql_command)

            register_window = BankCashRegister(self, self.cash_flow_type, self.register,
                                               self.register_number_entry.get(), self.register_date_entry.get(),
                                               self.reg_account, previous_balance, previous_balance)
            self.withdraw()
            self.new_register_window.destroy()
            register_window.lift()

    def delete_register(self):
        if self.selected_register() == '':
            pass
        else:
            answer = tkinter.messagebox.askyesno(title="WARNING", message=f"Delete {self.selected_register()[3]}?",
                                                 parent=self)
            if answer:
                if self.selected_register()[5] == '0.00' and self.selected_register()[6] == '0.00':
                    sql_command = f"DELETE FROM bank_cash_register " \
                                  f"WHERE register_number = '{self.selected_register()[3]}'"
                    conn = sqlcommand.SqlCommand()
                    conn.sql_execute(sql_command)

                    # Refresh register list
                    self.register_list_treeview()
                else:
                    tkinter.messagebox.showerror(
                        title="ERROR", message="Cannot delete document if it has deposits or withdrawals.", parent=self)

    def refresh_coa_tree(self):
        """Refresh register list tree"""
        self.register_list_tree.delete(*self.register_list_tree.get_children())
        self.register_list_treeview()


class BankCashRegister(tkinter.Toplevel):

    def __init__(self, parent, cash_flow_type, register, register_number, register_date, reg_account, balance,
                 previous_balance):
        """Bank statement / Cash main window"""
        super().__init__(parent)

        # Specify cash flow type
        self.cash_flow_type = cash_flow_type
        self.register = register
        self.register_number = register_number
        self.register_date = register_date
        self.reg_account = reg_account
        self.balance = balance
        self.previous_balance = previous_balance

        self.title(f'{self.register} - {self.register_number}')
        self.config(padx=15, pady=15)
        self.resizable(False, False)

        # Top options Frame left
        self.top_options_frame_left = tkinter.Frame(self)
        self.top_options_frame_left.grid(column=0, row=0, sticky='w')

        self.doc_date_label = tkinter.Label(self.top_options_frame_left, text="Document date")
        self.doc_date_label.grid(column=0, row=0)
        self.doc_date_entry = DateEntry(self.top_options_frame_left, selectmode='day', locale='en_US',
                                        date_pattern='dd-mm-y')
        self.doc_date_entry.set_date(self.register_date)
        self.doc_date_entry.config(state='disabled')
        self.doc_date_entry.grid(column=0, row=1, pady=(0, 10))

        if self.cash_flow_type == 'Bank':
            self.doc_number_label = tkinter.Label(self.top_options_frame_left, text="Bank statement number")
        elif self.cash_flow_type == 'Cash register':
            self.doc_number_label = tkinter.Label(self.top_options_frame_left, text="Cash reckoning number")
        self.doc_number_label.grid(column=0, row=2)
        self.doc_number_entry = tkinter.Entry(self.top_options_frame_left, width=30)
        self.doc_number_entry.insert('end', self.register_number)
        self.doc_number_entry.config(state='readonly')
        self.doc_number_entry.grid(column=0, row=3, pady=(0, 10))

        # Top options Frame right
        self.top_options_frame_right = tkinter.Frame(self)
        self.top_options_frame_right.grid(column=1, row=0, sticky='se')

        self.add_withdrawal_button = tkinter.Button(self.top_options_frame_right, text='- Add Withdrawal',
                                                    command=self.add_withdrawal_button_command,
                                                    width=15, padx=5, pady=5)
        self.add_withdrawal_button.grid(column=0, row=0)

        self.add_deposit_button = tkinter.Button(self.top_options_frame_right, text='+ Add Deposit',
                                                 command=self.add_deposit_button_command, width=15, padx=5, pady=5)
        self.add_deposit_button.grid(column=1, row=0, padx=20)

        self.edit_button = tkinter.Button(self.top_options_frame_right, text='Edit',
                                          command=self.edit_button_command, width=15, padx=5, pady=5)
        self.edit_button.grid(column=2, row=0)

        self.delete_button = tkinter.Button(self.top_options_frame_right, text='Delete',
                                            command=self.delete_button_command, width=15, padx=5, pady=5)
        self.delete_button.grid(column=3, row=0)

        self.prev_balance_label = tkinter.Label(self.top_options_frame_right, text='Previous balance: ',
                                           width=16, anchor='e')
        self.prev_balance_label.grid(column=2, row=1, padx=5, pady=5)
        self.prev_balance_entry = tkinter.Entry(self.top_options_frame_right, width=20, justify='right')
        self.prev_balance_entry.insert('end', '{:,.2f}'.format(float(self.previous_balance)).replace(',', ' '))
        self.prev_balance_entry.config(state='readonly')
        self.prev_balance_entry.grid(column=3, row=1, padx=20, pady=5)

        # Treeview Frame
        self.treeview_frame = tkinter.Frame(self)
        self.treeview_frame.grid(column=0, row=1, columnspan=2)

        self.tree_scroll = tkinter.Scrollbar(self.treeview_frame)
        self.tree_scroll.grid(column=1, row=0, sticky='ns')

        self.bank_cash_register_treeview()

        # Bottom options Frame right
        self.bottom_options_frame_right = tkinter.Frame(self)
        self.bottom_options_frame_right.grid(column=1, row=2, sticky='e')

        self.balance_label = tkinter.Label(self.bottom_options_frame_right, text='Balance: ', width=16, anchor='e')
        self.balance_label.grid(column=0, row=0, padx=5, pady=5)
        self.balance_entry = tkinter.Entry(self.bottom_options_frame_right, width=20, justify='right')
        self.balance_entry.insert('end', self.balance)
        self.balance_entry.config(state='readonly')
        self.balance_entry.grid(column=1, row=0, padx=20, pady=5)

        self.show_settlements_button = tkinter.Button(self.bottom_options_frame_right, text='Show settlements',
                                                      command=self.show_settlements_command,
                                                      width=15, padx=5, pady=5)
        self.show_settlements_button.grid(column=0, row=1)

        self.settle_document_button = tkinter.Button(self.bottom_options_frame_right, text='Settle document',
                                                     command=self.settle_document_button_command,
                                                     width=15, padx=5, pady=5)
        self.settle_document_button.grid(column=1, row=1, padx=20)

        # Bottom options Frame left
        self.bottom_options_frame_left = tkinter.Frame(self)
        self.bottom_options_frame_left.grid(column=0, row=2, sticky='w')

    def edit_button_command(self):
        """Open new window to edit withdraw or deposit"""
        if self.selected_document() == '':
            pass
        else:
            self.doc_type = ''
            self.orig_amount = ''
            if self.selected_document()[6] == '':
                self.doc_type = 'Deposit'
                self.orig_amount = self.selected_document()[7]
            elif self.selected_document()[7] == '':
                self.doc_type = 'Withdrawal'
                self.orig_amount = self.selected_document()[6]
            self.withdraw_deposit = WithdrawDeposit(self, self.cash_flow_type, self.register, self.register_number,
                                                    self.register_date, self.reg_account, self.doc_type)
            if self.doc_type == 'Withdrawal':
                self.withdraw_deposit.on_close(self.on_edit_withdraw_close)
            elif self.doc_type == 'Deposit':
                self.withdraw_deposit.on_close(self.on_edit_deposit_close)

            # Insert data
            self.withdraw_deposit.amount_entry.insert('end', self.orig_amount)
            self.withdraw_deposit.description_entry.insert('end', self.selected_document()[3])
            self.withdraw_deposit.account_entry.config(
                text=f"{self.selected_document()[4]} ~ {self.selected_document()[5]}")
            if self.selected_document()[8] == 0:
                pass
            else:
                self.withdraw_deposit.customer_entry.config(
                    state='active', text=f"{self.selected_document()[8]} ~ {self.selected_document()[9]}")
            # Change button command
            self.withdraw_deposit.save_button.config(command=self.save_changes)

    def on_edit_withdraw_close(self):
        """Refresh register tree and open settlements window"""
        self.refresh_bank_cash_register_tree()
        self.calculate_balance()

        # Check if customer is selected
        if self.edit_cust_id == '':
            pass
        else:
            # Open customer settlements
            cust_set = customer_settlements.CustomerSettlements(self, self.edit_no_journal, self.edit_ct_account_num,
                                                                'liabilities', self.edit_cust_id, self.edit_cust_name)
            cust_set.on_close(self.refresh_bank_cash_register_tree)

    def on_edit_deposit_close(self):
        """Refresh register tree and open settlements window"""
        self.refresh_bank_cash_register_tree()
        self.calculate_balance()

        # Check if customer is selected
        if self.edit_cust_id == '':
            pass
        else:
            # Open customer settlements
            cust_set = customer_settlements.CustomerSettlements(self, self.edit_no_journal, self.edit_ct_account_num,
                                                                'receivables', self.edit_cust_id, self.edit_cust_name)
            cust_set.on_close(self.refresh_bank_cash_register_tree)

    def save_changes(self):
        """Saves changes in withdraw deposit edit mode"""
        # Take values to check whether the amount after correction is not lower than the settlements
        amount = float(self.withdraw_deposit.amount_entry.get().replace(' ', ''))
        left_to_settle = float(self.selected_document()[10].replace(' ', ''))
        document_value = 0
        if self.doc_type == 'Deposit':
            document_value = float(self.selected_document()[7].replace('\xa0', ''))
        elif self.doc_type == 'Withdrawal':
            document_value = float(self.selected_document()[6].replace('\xa0', ''))
        settled_amount = document_value - left_to_settle
        # Check whether the amount after correction is not lower than the settlements
        if settled_amount > amount:
            tkinter.messagebox.showerror(title='ERROR', message='Settled amount is greater than document amount',
                                         parent=self.withdraw_deposit)
        else:
            # Save
            amount_after_cor = self.withdraw_deposit.amount_entry.get()
            description = self.withdraw_deposit.description_entry.get()
            self.edit_dt_account_num = self.reg_account if self.doc_type == 'Deposit' \
                else self.withdraw_deposit.account_entry['text'][
                     0:self.withdraw_deposit.account_entry['text'].rfind(" ~ ")]
            self.edit_ct_account_num = self.reg_account if self.doc_type == 'Withdrawal' \
                else self.withdraw_deposit.account_entry['text'][
                     0:self.withdraw_deposit.account_entry['text'].rfind(" ~ ")]
            self.edit_cust_id = \
                self.withdraw_deposit.customer_entry['text'][
                    0:self.withdraw_deposit.customer_entry['text'].rfind(" ~ ")]
            self.edit_cust_name = self.withdraw_deposit.customer_entry['text'].split(" ~ ")[1]
            self.edit_no_journal = self.selected_document()[0]

            amount_difference = float(self.orig_amount.replace('\xa0', '')) - float(amount_after_cor.replace(' ', ''))
            mark = ''
            column = ''
            if self.doc_type == 'Withdrawal':
                mark = '+'
                column = 'withdrawals'
            elif self.doc_type == 'Deposit':
                mark = '-'
                column = 'deposits'
            sql_command = f"UPDATE bank_cash_register " \
                          f"SET " \
                          f"balance = balance {mark} {amount_difference}, " \
                          f"{column} = {column} - {amount_difference} " \
                          f"WHERE register_date >= TO_DATE('{self.register_date}', 'dd-mm-yyyy') " \
                          f"AND register='{self.register}'"
            conn = sqlcommand.SqlCommand()
            conn.sql_execute(sql_command)

            sql_command = f"UPDATE journal " \
                          f"SET " \
                          f"description='{description}', " \
                          f"dt_account_num='{self.edit_dt_account_num}', " \
                          f"ct_account_num='{self.edit_ct_account_num}', " \
                          f"amount={amount}, " \
                          f"cust_id={self.edit_cust_id} " \
                          f"WHERE no_journal={self.edit_no_journal} "
            conn = sqlcommand.SqlCommand()
            conn.sql_execute(sql_command)

            self.withdraw_deposit.close()

    def delete_button_command(self):
        """Delete position from register"""
        if self.selected_document() == '':
            pass
        else:
            selected = self.selected_document()
            # Ask if delete position
            answer = tkinter.messagebox.askyesno(title="WARNING", message="Delete position?", parent=self)
            if answer:
                # Check if there are settlements
                doc_value = float(selected[6].replace('\xa0', '')) if selected[7] == '' \
                    else float(selected[7].replace('\xa0', ''))
                if selected[8] != 0 and float(selected[10].replace(' ', '')) != doc_value:
                    tkinter.messagebox.showerror(title="ERROR", message="Delete all settlements first", parent=self)
                else:
                    sql_command = f"DELETE FROM journal WHERE no_journal={selected[0]}"
                    # Connect to SQL database to delete position
                    conn = sqlcommand.SqlCommand()
                    conn.sql_execute(sql_command)

                    # Update balance
                    mark = ''
                    amount = ''
                    column = ''
                    if selected[6] == '':
                        mark = '-'
                        amount = selected[7].replace('\xa0', '')
                        column = 'deposits'
                    elif selected[7] == '':
                        mark = '+'
                        amount = selected[6].replace('\xa0', '')
                        column = 'withdrawals'
                    sql_command = f"UPDATE bank_cash_register " \
                                  f"SET " \
                                  f"balance = balance {mark} {amount}, " \
                                  f"{column} = {column} - {amount} " \
                                  f"WHERE register_date >= TO_DATE('{self.register_date}', 'dd-mm-yyyy') " \
                                  f"AND register='{self.register}'"
                    conn = sqlcommand.SqlCommand()
                    conn.sql_execute(sql_command)

                    # Refresh register tree and calculate balance
                    self.refresh_bank_cash_register_tree()
                    self.calculate_balance()

    def show_settlements_command(self):
        """Open new window and show how documents were settled"""
        if self.selected_document() == '':
            pass
        elif self.selected_document()[8] == 0:
            tkinter.messagebox.showerror(title="ERROR", message="Select customer settlements account", parent=self)
        else:
            cust_id = self.selected_document()[8]
            cust_name = self.selected_document()[9]
            doc_number = self.doc_number_entry.get()
            receivables = '0' if self.selected_document()[6] == '' else self.selected_document()[6]
            liabilities = '0' if self.selected_document()[7] == '' else self.selected_document()[7]
            settled_amount = float(receivables.replace('\xa0', '')) + float(liabilities.replace('\xa0', '')) - \
                             float(self.selected_document()[10].replace(' ', ''))
            no_journal = self.selected_document()[0]
            if settled_amount == 0:
                tkinter.messagebox.showerror(title="ERROR", message="This document has no settlements", parent=self)
            else:
                show_settlements = customer_settlements.ShowSettlements(self, cust_id, cust_name, doc_number,
                                                                        receivables, liabilities, no_journal)
                show_settlements.on_delete(self.refresh_bank_cash_register_tree)

    def settle_document_button_command(self):
        """Open new window with customer documents to settle"""
        if self.selected_document() == '':
            pass
        elif self.selected_document()[8] == 0:
            tkinter.messagebox.showerror(title="ERROR", message="Select customer settlements account", parent=self)
        elif self.selected_document()[10] == '0.00':
            tkinter.messagebox.showerror(title="ERROR", message="This document is already settled", parent=self)
        else:
            no_journal = self.selected_document()[0]
            cust_account = self.selected_document()[4]
            cust_id = self.selected_document()[8]
            cust_name = self.selected_document()[9]
            settlement_type = ''
            if self.selected_document()[6] != '':
                settlement_type = "liabilities"
            elif self.selected_document()[7] != '':
                settlement_type = "receivables"
            cust_settlements_class = customer_settlements.CustomerSettlements(self, no_journal, cust_account,
                                                                              settlement_type, cust_id, cust_name)
            cust_settlements_class.on_close(self.refresh_bank_cash_register_tree)

    def bank_cash_register_treeview(self):
        """Create bank / cash register treeview"""
        sql_command = f"SELECT no_journal, journal_entry_date, ROW_NUMBER() OVER (ORDER BY no_journal) AS no_order,  " \
                      f"description, " \
                      f"CASE WHEN dt_account_num='{self.reg_account}' THEN ct_account_num ELSE dt_account_num " \
                      f"END AS account, " \
                      f"CASE WHEN dt_account_num='{self.reg_account}' THEN ct.account_name ELSE dt.account_name " \
                      f"END AS account_name, " \
                      f"CASE WHEN ct_account_num='{self.reg_account}' " \
                      f"THEN TO_CHAR(COALESCE(CAST(amount AS DECIMAL(1000, 2)),0), 'fm999G999G999G990.00') " \
                      f"ELSE '' END AS withdrawal, " \
                      f"CASE WHEN dt_account_num='{self.reg_account}' " \
                      f"THEN TO_CHAR(COALESCE(CAST(amount AS DECIMAL(1000, 2)),0), 'fm999G999G999G990.00') " \
                      f"ELSE '' END AS deposit, " \
                      f"COALESCE(journal.cust_id, 0) AS cust_id, COALESCE(customers.cust_name,'') AS customer_name, " \
                      f"COALESCE(settlement, '') AS left_to_settle " \
                      f"FROM journal " \
                      f"LEFT JOIN customers " \
                      f"ON journal.cust_id = customers.cust_id " \
                      f"LEFT JOIN chart_of_accounts AS dt " \
                      f"ON journal.dt_account_num = dt.account_num " \
                      f"LEFT JOIN chart_of_accounts AS ct " \
                      f"ON journal.ct_account_num = ct.account_num " \
                      f"WHERE doc_number='{self.register_number}' " \
                      f"ORDER BY no_journal"

        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)

        column_names = execute['column_names']
        self.bank_cash_register_tree = ttk.Treeview(self.treeview_frame, columns=column_names, show='headings',
                                                    height=25, selectmode='browse', yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.config(command=self.bank_cash_register_tree.yview)

        column = 0
        for _ in column_names:
            self.bank_cash_register_tree.heading(column_names[column], text=column_names[column])
            column += 1

        # Adjust column width
        self.bank_cash_register_tree.column(column_names[0], width=0)
        self.bank_cash_register_tree.column(column_names[1], width=0)
        self.bank_cash_register_tree.column(column_names[2], width=40, anchor='e')
        self.bank_cash_register_tree.column(column_names[3], width=170)
        self.bank_cash_register_tree.column(column_names[4], width=70, anchor='e')
        self.bank_cash_register_tree.column(column_names[5], width=170)
        self.bank_cash_register_tree.column(column_names[6], width=100, anchor='e')
        self.bank_cash_register_tree.column(column_names[7], width=100, anchor='e')
        self.bank_cash_register_tree.column(column_names[8], width=100, anchor='e')
        self.bank_cash_register_tree.column(column_names[9], width=130)
        self.bank_cash_register_tree.column(column_names[10], width=130, anchor='e')

        self.bank_cash_register_tree["displaycolumns"] = (column_names[2:])

        self.bank_cash_register_tree.grid(column=0, row=0)

        records = execute['records']

        # Get settlement values
        self.values = []
        for item in records:
            lst = list(item)
            try:
                set_dict = ast.literal_eval(lst[10])
                settlement_sum = float(sum(set_dict.values()))
            except Exception:
                settlement_sum = 0
            if lst[9] == '':
                pass
            else:
                # Calculate left to settle
                if lst[6] == '':
                    lst[10] = "{:,.2f}".format(float(lst[7].replace('\xa0', '')) - settlement_sum).replace(',', ' ')
                elif lst[7] == '':
                    lst[10] = "{:,.2f}".format(float(lst[6].replace('\xa0', '')) - settlement_sum).replace(',', ' ')
            self.values.append(lst)

        record = 0
        for _ in records:
            self.bank_cash_register_tree.insert('', tkinter.END, values=self.values[record])
            record += 1

    def selected_document(self):
        """Take selected document"""
        selected = self.bank_cash_register_tree.focus()
        document = self.bank_cash_register_tree.item(selected).get('values')
        return document

    def calculate_balance(self):
        """Calculate actual balance"""
        balance = float(self.previous_balance)
        for record in self.values:
            if record[6] == '':
                balance += float(record[7].replace('\xa0', ''))
            elif record[7] == '':
                balance -= float(record[6].replace('\xa0', ''))
        self.balance_entry.config(state='normal')
        self.balance_entry.delete(0, 'end')
        self.balance_entry.insert('end', str("{:,.2f}".format(balance).replace(',', ' ')))
        self.balance_entry.config(state='readonly')

    def add_withdrawal_button_command(self):
        """Open new window to enter withdraw to register"""
        withdraw_deposit_class = WithdrawDeposit(self, self.cash_flow_type, self.register, self.register_number,
                                                 self.register_date, self.reg_account, 'Withdrawal')
        withdraw_deposit_class.on_close(self.on_withdraw_close)

    def add_deposit_button_command(self):
        """Open new window to enter deposit to register"""
        withdraw_deposit_class = WithdrawDeposit(self, self.cash_flow_type, self.register, self.register_number,
                                                 self.register_date, self.reg_account, 'Deposit')
        withdraw_deposit_class.on_close(self.on_deposit_close)

    def on_withdraw_close(self):
        """Refresh register tree and open settlements window"""
        self.refresh_bank_cash_register_tree()
        self.calculate_balance()

        # Check if customer is selected
        if self.values[-1][8] == 0:
            pass
        else:
            # Open customer settlements
            cust_set = customer_settlements.CustomerSettlements(
                self, self.values[-1][0], self.values[-1][4], 'liabilities', self.values[-1][8], self.values[-1][9])
            cust_set.on_close(self.refresh_bank_cash_register_tree)

    def on_deposit_close(self):
        """Refresh register tree and open settlements window"""
        self.refresh_bank_cash_register_tree()
        self.calculate_balance()

        # Check if customer is selected
        if self.values[-1][8] == 0:
            pass
        else:
            # Open customer settlements
            cust_set = customer_settlements.CustomerSettlements(
                self, self.values[-1][0], self.values[-1][4], 'receivables', self.values[-1][8], self.values[-1][9])
            cust_set.on_close(self.refresh_bank_cash_register_tree)

    def refresh_bank_cash_register_tree(self):
        """Refresh bank cash register tree"""
        self.bank_cash_register_tree.delete(*self.bank_cash_register_tree.get_children())
        self.bank_cash_register_treeview()


class WithdrawDeposit(tkinter.Toplevel):

    def __init__(self, parent, cash_flow_type, register, register_number, register_date, reg_account,
                 doc_type):
        """Withdrawal / Deposit window"""
        super().__init__(parent)

        self.grab_set()

        self.cash_flow_type = cash_flow_type
        self.register = register
        self.register_number = register_number
        self.register_date = register_date
        self.reg_account = reg_account
        self.doc_type = doc_type

        self.title(self.doc_type)
        self.config(padx=10, pady=10)
        self.resizable(False, False)

        self.account_label = tkinter.Label(self, text='Account', width=10)
        self.account_label.grid(column=0, row=0)
        self.account_entry = tkinter.Button(self, text='', command=self.select_account, width=30,
                                            highlightbackground='grey', borderwidth=1, relief='sunken', anchor='w')
        self.account_entry.grid(column=1, row=0, sticky='w')
        self.customer_label = tkinter.Label(self, text='Customer', width=10)
        self.customer_label.grid(column=0, row=1)
        self.customer_entry = tkinter.Button(self, text="", command=self.select_customer, width=30,
                                             highlightbackground='grey', borderwidth=1, relief='sunken', anchor='w',
                                             state='disabled')
        self.customer_entry.grid(column=1, row=1, sticky='w')

        self.amount_label = tkinter.Label(self, text='Amount', width=10)
        self.amount_label.grid(column=0, row=2, pady=(40, 0))

        self.amount_str_var = tkinter.StringVar()
        self.amount_str_var.set('0.00')
        self.amount_entry = tkinter.Entry(self, textvariable=self.amount_str_var, width=20, justify='right')
        self.amount_entry.grid(column=0, row=3, sticky='w')
        self.amount_str_var.trace('w', partial(self.entry_fill, self.amount_entry))

        self.description_label = tkinter.Label(self, text='Description', width=10)
        self.description_label.grid(column=0, row=4, pady=(15, 0))
        self.description_entry = tkinter.Entry(self, width=80)
        self.description_entry.grid(column=0, row=5, columnspan=4)

        self.save_button = tkinter.Button(self, text="Save", command=self.save_button_command,
                                          padx=5, pady=5, width=15)
        self.save_button.grid(column=3, row=6, pady=(10, 0))

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
        self.customer_entry.config(text=f"{cust_details[0]} ~ {cust_details[1]}")
        self.customer_window.destroy()

    def select_account(self):
        """Open new window with account to choose"""
        self.account_window = chart_of_accounts.ChartOfAccounts(self)
        self.account_window.grab_set()
        add_customer_button = tkinter.Button(self.account_window, text='Select account',
                                             command=self.select_account_command, font=30)
        add_customer_button.grid(column=0, row=1, columnspan=2)

    def select_account_command(self):
        """Get selected account from account window"""
        self.acc_details = self.account_window.selected_account()
        self.acc_num = self.account_window.selected_account_num()
        self.account_entry.config(text=f"{self.acc_num} ~ {self.acc_details[1]}")
        self.account_window.destroy()
        if self.acc_details[2] == "✔":
            self.select_customer()
            self.customer_entry.config(state='active')
        else:
            self.customer_entry.config(text='', state='disabled')

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

    def save_button_command(self):
        """Add line to journal"""
        doc_type = self.cash_flow_type
        doc_date = self.register_date
        description = self.description_entry.get()
        dt_account = ''
        ct_account = ''
        if self.doc_type == 'Withdrawal':
            dt_account = self.account_entry['text'][0:self.account_entry['text'].rfind(" ~ ")]
            ct_account = self.reg_account
        elif self.doc_type == 'Deposit':
            dt_account = self.reg_account
            ct_account = self.account_entry['text'][0:self.account_entry['text'].rfind(" ~ ")]
        amount = self.amount_entry.get().replace(' ', '')
        cust_id = 'null' if self.customer_entry['text'] == '' else \
            self.customer_entry['text'][0:self.customer_entry['text'].rfind(" ~ ")]
        doc_number = self.register_number

        sql_command = f"INSERT INTO journal(doc_type, doc_date, description, " \
                      f"dt_account_num, ct_account_num, amount, cust_id, doc_number, int_doc_number) " \
                      f"VALUES" \
                      f"('{doc_type}', TO_DATE('{doc_date}', 'dd-mm-yyyy'), " \
                      f"'{description}', '{dt_account}', " \
                      f"'{ct_account}', {amount}, {cust_id}, " \
                      f"'{doc_number}', '{doc_number}') "

        conn = sqlcommand.SqlCommand()
        conn.sql_execute(sql_command)

        mark = ''
        column = ''
        if self.doc_type == 'Withdrawal':
            mark = '-'
            column = 'withdrawals'
        elif self.doc_type == 'Deposit':
            mark = '+'
            column = 'deposits'
        sql_command = f"UPDATE bank_cash_register " \
                      f"SET " \
                      f"balance = balance {mark} {amount}, " \
                      f"{column} = {column} + {amount} " \
                      f"WHERE register_date >= TO_DATE('{doc_date}', 'dd-mm-yyyy') AND register='{self.register}'"

        conn = sqlcommand.SqlCommand()
        conn.sql_execute(sql_command)

        self.close()

    def on_close(self, callback):
        self.callback = callback

    def close(self):
        self.callback()
        self.destroy()
