import tkinter
from tkinter import messagebox, ttk
import bank_cash_register
import invoice
import journal_voucher
import sqlcommand
from datetime import datetime
import ast
import re
from functools import partial


class CustomersReceivablesLiabilities(tkinter.Toplevel):

    def __init__(self, parent):
        """Displays customers receivables and liabilities"""
        super().__init__(parent)

        self.config(padx=5, pady=5)
        self.state('zoomed')
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)

        # Top options frame
        self.top_options_frame = tkinter.Frame(self)
        self.top_options_frame.grid(column=2, row=0, sticky='w')

        self.show_unsettled_button = tkinter.Button(self.top_options_frame, text='Show unsettled',
                                                    command=self.show_unsettled_button_command, width=15)
        self.show_unsettled_button.grid(column=0, row=0, padx=(5, 0))

        self.show_settled_button = tkinter.Button(self.top_options_frame, text='Show settled',
                                                  command=self.show_settled_button_command, width=15)
        self.show_settled_button.grid(column=1, row=0)
        # Pressed at start
        self.show_unsettled_button.configure(relief="sunken", bg="light grey")

        # Customers list frame
        self.cust_list_frame = tkinter.Frame(self, pady=5, padx=5)
        self.cust_list_frame.grid(column=0, row=1, columnspan=2, sticky='ns')

        self.cust_list_scroll = tkinter.Scrollbar(self.cust_list_frame)
        self.cust_list_scroll.grid(column=1, row=0, sticky='ns')

        self.cust_list_frame.columnconfigure(0, weight=1)
        self.cust_list_frame.rowconfigure(0, weight=1)

        # Customers receivables and liabilities table
        self.show_unsettled = True
        self.show_settled = False
        self.cust_settlements_frame = tkinter.Frame(self, pady=5, padx=5)
        self.cust_settlements_frame.grid(column=2, row=1, sticky="nsew")

        self.cust_settlements_frame.columnconfigure(0, weight=1)
        self.cust_settlements_frame.rowconfigure(0, weight=1)

        self.cust_set_scroll = tkinter.Scrollbar(self.cust_settlements_frame)
        self.cust_set_scroll.grid(column=1, row=0, sticky='ns')

        # Summary frame
        self.summary_labels_frame = tkinter.Frame(self)
        self.summary_labels_frame.grid(column=0, row=2, sticky='w')
        self.summary_frame = tkinter.Frame(self)
        self.summary_frame.grid(column=1, row=2, sticky='e')

        self.receivables_label = tkinter.Label(self.summary_labels_frame, fg='green', anchor='w', width=10,
                                               text="Receivables:")
        self.receivables_label.grid(column=0, row=0, padx=5)
        self.liabilities_label = tkinter.Label(self.summary_labels_frame, fg='red', anchor='w', width=10,
                                               text="Liabilities:")
        self.liabilities_label.grid(column=0, row=1, padx=5)
        self.balance_label = tkinter.Label(self.summary_labels_frame, anchor='w', width=10, text="Balance:")
        self.balance_label.grid(column=0, row=2, padx=5)

        self.receivables_sum_label = tkinter.Label(self.summary_frame, fg='green', anchor='e', width=16)
        self.receivables_sum_label.grid(column=0, row=0, padx=5)
        self.liabilities_sum_label = tkinter.Label(self.summary_frame, fg='red', anchor='e', width=16)
        self.liabilities_sum_label.grid(column=0, row=1, padx=5)
        self.balance_sum_label = tkinter.Label(self.summary_frame, anchor='e', width=16)
        self.balance_sum_label.grid(column=0, row=2, padx=5)

        # Bottom options frame
        self.bottom_options_frame = tkinter.Frame(self)
        self.bottom_options_frame.grid(column=2, row=2, sticky='e')

        self.show_document_button = tkinter.Button(self.bottom_options_frame, text="Show original document",
                                                   command=self.show_document_button_command,
                                                   padx=15, pady=15, width=20)
        self.show_document_button.grid(column=0, row=0, rowspan=2)

        self.show_settlements_button = tkinter.Button(self.bottom_options_frame, text='Show settlements',
                                                      command=self.show_settlements_command,
                                                      padx=15, pady=15, width=20)
        self.show_settlements_button.grid(column=1, row=0, rowspan=2)

        self.settle_document_button = tkinter.Button(self.bottom_options_frame, text='Settle document',
                                                     command=self.settle_document_button_command,
                                                     padx=15, pady=15, width=20)
        self.settle_document_button.grid(column=2, row=0, rowspan=2, padx=(0, 5))

        # Searchbar
        self.search_entry = tkinter.Entry(self, width=20)
        self.search_entry.bind('<Return>', self.search)
        self.search_entry.grid(column=0, row=0, columnspan=2, padx=5, sticky='w')

        self.search_button = tkinter.Button(self, text="search", command=lambda: self.search(event=None))
        self.search_button.grid(column=1, row=0)

        # Call customers list and set first customer
        self.cl_column_names = []
        self.order_by_cl_trv = 'cust_name'
        self.customers_list_treeview()

        # Sort
        self.cl_column_names[1] = f"▲ {self.cl_column_names[1]}"
        self.cust_list_tree.config(columns=self.cl_column_names)
        for col in self.cl_column_names:
            self.cust_list_tree.heading(col, text=col, command=lambda col=col: self.on_header_click_cl_trv(col))
        # Adjust column width
        self.cust_list_tree.column(self.cl_column_names[0], width=50)
        self.cust_list_tree.column(self.cl_column_names[1], width=150)

        # Select first customer from customers_list_treeview
        self.customer = self.cust_list_tree.item(self.first_item).get('values')
        # Set title with selected customer name
        self.title(f"Customers receivables and liabilities - {self.customer[0]} - {self.customer[1]}")

        # Create customer_settlements_treeview
        self.cs_column_names = []
        self.order_by_cs_trv = 'inv_due_date'
        self.customer_settlements_treeview()

        # Sort
        self.cs_column_names[11] = f"▲ {self.cs_column_names[11]}"

        self.cust_set_tree.config(columns=self.cs_column_names)
        for col in self.cs_column_names:
            self.cust_set_tree.heading(col, text=col, command=lambda col=col: self.on_header_click_cs_trv(col))

            # Adjust column width
            self.cust_set_tree.column(self.cs_column_names[1], width=120)
            self.cust_set_tree.column(self.cs_column_names[2], width=100, anchor='center')
            self.cust_set_tree.column(self.cs_column_names[3], width=100, anchor='e')
            self.cust_set_tree.column(self.cs_column_names[4], width=150)
            self.cust_set_tree.column(self.cs_column_names[5], width=150, anchor='e')
            self.cust_set_tree.column(self.cs_column_names[6], width=150, anchor='e')
            self.cust_set_tree.column(self.cs_column_names[7], width=150, anchor='e')
            self.cust_set_tree.column(self.cs_column_names[8], width=150, anchor='e')
            self.cust_set_tree.column(self.cs_column_names[9], width=150, anchor='e')
            self.cust_set_tree.column(self.cs_column_names[10], width=50, anchor='center')
            self.cust_set_tree.column(self.cs_column_names[11], width=100, anchor='center')
            self.cust_set_tree.column(self.cs_column_names[12], width=100)
            self.cust_set_tree.column(self.cs_column_names[13], width=100, anchor='e')
            self.cust_set_tree.column(self.cs_column_names[14], width=150)
            self.cust_set_tree.column(self.cs_column_names[15], width=170)

            self.cust_set_tree["displaycolumns"] = (self.cs_column_names[1:-6])

    def customers_list_treeview(self):
        """Create customers treeview"""
        sql_command_list = f"""
        SELECT customers.cust_id, cust_name FROM customers
        LEFT JOIN journal
        ON customers.cust_id = journal.cust_id
        WHERE 
        amount IS NOT NULL AND cust_name ILIKE '%{self.search_entry.get()}%'
        OR amount IS NOT NULL AND tax_id_num LIKE '{self.search_entry.get()}%'
        OR amount IS NOT NULL AND REPLACE(tax_id_num, '-','') LIKE '{self.search_entry.get()}%'
        OR amount IS NOT NULL 
        AND customers.cust_id={int(self.search_entry.get()) if self.search_entry.get().isdigit() else 'Null'}
        GROUP BY customers.cust_id
        ORDER BY {self.order_by_cl_trv}
        """
        # Connect with SQL database
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command_list)

        self.cl_column_names = execute['column_names']
        self.cust_list_tree = ttk.Treeview(self.cust_list_frame, columns=self.cl_column_names,
                                           show='headings', height=35, selectmode='browse',
                                           yscrollcommand=self.cust_list_scroll.set)
        self.cust_list_scroll.config(command=self.cust_list_tree.yview)

        self.cust_list_tree.grid(column=0, row=0, sticky="ns")

        # Bind with selected customer
        self.cust_list_tree.bind('<Double-Button-1>', self.selected_customer)

        # Color tags
        self.cust_list_tree.tag_configure("selected", foreground="white", background='dark grey',
                                          font='TkDefaultFont 10 bold')
        self.cust_list_tree.tag_configure("black", foreground="black")

        # Add records to tree
        records = execute['records']
        record = 0
        for _ in records:
            self.cust_list_tree.insert('', tkinter.END, values=records[record])
            record += 1

        # Set first item
        children = self.cust_list_tree.get_children()
        if children:
            self.first_item = children[0]
            self.cust_list_tree.selection_set(self.first_item)
            self.cust_list_tree.item(self.first_item, tags=("selected",))

        self.previous_selection = self.first_item

    def search(self, event):
        try:
            self.on_header_click_cl_trv(col='cust_name')
            self.customer = self.cust_list_tree.item(self.first_item).get('values')
            self.on_header_click_cs_trv(col='inv_due_date')
        except Exception:
            pass

    def on_header_click_cl_trv(self, col):
        """Take clicked header and sort table"""
        if '▲' in col:
            col = col.replace('▲ ', '')
            self.order_by_cl_trv = f"{col} DESC"
            self.customers_list_treeview()
            self.customer = self.cust_list_tree.item(self.first_item).get('values')
            self.on_header_click_cs_trv(col='inv_due_date')
            self.cl_column_names[self.cl_column_names.index(col)] = f"▼ {col}"
            self.cust_list_tree.config(columns=self.cl_column_names)
            for col in self.cl_column_names:
                self.cust_list_tree.heading(col, text=col, command=lambda col=col: self.on_header_click_cl_trv(col))
        else:
            col = col.replace('▼ ', '')
            self.order_by_cl_trv = f"{col} ASC"
            self.customers_list_treeview()
            self.customer = self.cust_list_tree.item(self.first_item).get('values')
            self.on_header_click_cs_trv(col='inv_due_date')
            self.cl_column_names[self.cl_column_names.index(col)] = f"▲ {col}"
            self.cust_list_tree.config(columns=self.cl_column_names)
            for col in self.cl_column_names:
                self.cust_list_tree.heading(col, text=col, command=lambda col=col: self.on_header_click_cl_trv(col))
        # Adjust column width
        self.cust_list_tree.column(self.cl_column_names[0], width=50)
        self.cust_list_tree.column(self.cl_column_names[1], width=150)

    def selected_customer(self, event):
        """Take selected customer"""
        selected_cust = self.cust_list_tree.focus()
        self.cust_list_tree.item(self.previous_selection, tags=("black",))
        self.cust_list_tree.item(selected_cust, tags=("selected",))
        self.customer = self.cust_list_tree.item(selected_cust).get('values')
        self.on_header_click_cs_trv(col='inv_due_date')
        self.previous_selection = selected_cust

    def customer_settlements_treeview(self):
        """Create customer settlements treeview"""
        self.title(f"Customers receivables and liabilities - {self.customer[0]} - {self.customer[1]}")
        sql_command = f"""
        SELECT
            no_journal,
            doc_type,
            doc_date,
            CASE WHEN dt.customer_settlement = 'True' THEN dt_account_num ELSE ct_account_num END AS account_num,
            CASE WHEN dt.customer_settlement = 'True' THEN dt.account_name ELSE ct.account_name END,
            doc_number,
            TO_CHAR(
                COALESCE(
                    CAST(CASE WHEN dt.customer_settlement = 'True' THEN amount END AS DECIMAL(1000, 2)),
                    0
                ),
                'fm999G999G999G990.00'
            ) AS receivables,
            TO_CHAR(
                COALESCE(
                    CAST(CASE WHEN ct.customer_settlement = 'True' THEN amount END AS DECIMAL(1000, 2)),
                    0
                ),
                'fm999G999G999G990.00'
            ) AS liabilities,
            TO_CHAR(
                COALESCE(amount, 0) - COALESCE((
                    SELECT SUM(value::numeric)
                    FROM (
                        SELECT split_part(dict_pair, ':', 1)::integer AS key, 
                        split_part(dict_pair, ':', 2)::numeric AS value
                        FROM UNNEST(STRING_TO_ARRAY(REGEXP_REPLACE(journal.settlement, '[{{}}]', '', 'g'), ', ')) 
                        AS dict_pair
                    ) AS d
                ), 0),
                'fm999G999G999G990.00'
            ) AS left_to_settle,
            TO_CHAR(
                COALESCE((
                    SELECT SUM(value::numeric)
                    FROM (
                        SELECT split_part(dict_pair, ':', 2)::numeric AS value
                        FROM UNNEST(STRING_TO_ARRAY(REGEXP_REPLACE(journal.settlement, '[{{}}]', '', 'g'), ', ')) 
                        AS dict_pair
                    ) AS d
                ), 0),
                'fm999G999G999G990.00'
            ) AS settled_amount,
            CASE WHEN (COALESCE(amount, 0) - COALESCE((
                SELECT SUM(value::numeric)
                FROM (
                    SELECT split_part(dict_pair, ':', 1)::integer AS key, 
                    split_part(dict_pair, ':', 2)::numeric AS value
                    FROM UNNEST(STRING_TO_ARRAY(REGEXP_REPLACE(journal.settlement, '[{{}}]', '', 'g'), ', ')) 
                    AS dict_pair
                ) AS d
            ), 0)) = 0 THEN '✔' ELSE '-' END AS settled,
            inv_due_date,
            COALESCE(inv_payment_method, '') AS inv_payment_method,
            journal.cust_id,
            customers.cust_name,
            journal_entry_date,
            cor_orig_doc_number,
            description,
            int_doc_number
        FROM
            journal
        LEFT JOIN customers ON journal.cust_id = customers.cust_id
        LEFT JOIN chart_of_accounts AS dt ON journal.dt_account_num = dt.account_num
        LEFT JOIN chart_of_accounts AS ct ON journal.ct_account_num = ct.account_num
        WHERE
            (dt.customer_settlement = 'True' OR ct.customer_settlement = 'True')
            AND journal.cust_id = {self.customer[0]}
        ORDER BY
            {self.order_by_cs_trv}
        """
        # Connect with SQL database
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)

        self.cs_column_names = execute['column_names']
        self.cust_set_tree = ttk.Treeview(self.cust_settlements_frame, columns=self.cs_column_names,
                                          show='headings', height=35, selectmode='browse',
                                          yscrollcommand=self.cust_set_scroll.set)
        self.cust_set_scroll.config(command=self.cust_set_tree.yview)

        self.cust_set_tree.grid(column=0, row=0, sticky="nsew")

        records = execute['records']

        # Color tags
        self.cust_set_tree.tag_configure("green", foreground="green")
        self.cust_set_tree.tag_configure("red", foreground="red")

        record = 0
        for value in records:
            if value[10] == '✔':
                if self.show_settled:
                    self.cust_set_tree.insert('', tkinter.END, values=records[record], tags='green')
            else:
                if self.show_unsettled:
                    if value[11] is not None:
                        if value[11] < datetime.now().date():
                            self.cust_set_tree.insert('', tkinter.END, values=records[record], tags='red')
                        else:
                            self.cust_set_tree.insert('', tkinter.END, values=records[record])
                    else:
                        self.cust_set_tree.insert('', tkinter.END, values=records[record])
            record += 1

        # Calculate receivables and liabilities
        receivables = 0
        for value in records:
            if float(value[6].replace('\xa0', '')) == 0:
                pass
            else:
                receivables += float(value[6].replace('\xa0', ''))
                receivables -= float(value[9].replace('\xa0', ''))

        liabilities = 0
        for value in records:
            if float(value[7].replace('\xa0', '')) == 0:
                pass
            else:
                liabilities -= float(value[7].replace('\xa0', ''))
                liabilities += float(value[9].replace('\xa0', ''))

        balance = receivables + liabilities

        self.receivables_sum_label.configure(text=f"{'{:,.2f}'.format(receivables).replace(',', ' ')}")
        self.liabilities_sum_label.configure(text=f"{'{:,.2f}'.format(liabilities).replace(',', ' ')}")
        self.balance_sum_label.configure(text=f"{'{:,.2f}'.format(balance).replace(',', ' ')}")

    def on_header_click_cs_trv(self, col):
        """Take clicked header and sort table"""
        if '▲' in col:
            col = col.replace('▲ ', '')
            self.order_by_cs_trv = f"{col} DESC"
            self.customer_settlements_treeview()
            self.cs_column_names[self.cs_column_names.index(col)] = f"▼ {col}"
            self.cust_set_tree.config(columns=self.cs_column_names)
            for col in self.cs_column_names:
                self.cust_set_tree.heading(col, text=col, command=lambda col=col: self.on_header_click_cs_trv(col))
        else:
            col = col.replace('▼ ', '')
            self.order_by_cs_trv = f"{col} ASC"
            self.customer_settlements_treeview()
            self.cs_column_names[self.cs_column_names.index(col)] = f"▲ {col}"
            self.cust_set_tree.config(columns=self.cs_column_names)
            for col in self.cs_column_names:
                self.cust_set_tree.heading(col, text=col, command=lambda col=col: self.on_header_click_cs_trv(col))

        # Adjust column width
        self.cust_set_tree.column(self.cs_column_names[1], width=120)
        self.cust_set_tree.column(self.cs_column_names[2], width=100, anchor='center')
        self.cust_set_tree.column(self.cs_column_names[3], width=100, anchor='e')
        self.cust_set_tree.column(self.cs_column_names[4], width=150)
        self.cust_set_tree.column(self.cs_column_names[5], width=150, anchor='e')
        self.cust_set_tree.column(self.cs_column_names[6], width=150, anchor='e')
        self.cust_set_tree.column(self.cs_column_names[7], width=150, anchor='e')
        self.cust_set_tree.column(self.cs_column_names[8], width=150, anchor='e')
        self.cust_set_tree.column(self.cs_column_names[9], width=150, anchor='e')
        self.cust_set_tree.column(self.cs_column_names[10], width=50, anchor='center')
        self.cust_set_tree.column(self.cs_column_names[11], width=100, anchor='center')
        self.cust_set_tree.column(self.cs_column_names[12], width=100)
        self.cust_set_tree.column(self.cs_column_names[13], width=100, anchor='e')
        self.cust_set_tree.column(self.cs_column_names[14], width=150)
        self.cust_set_tree.column(self.cs_column_names[15], width=170)

        self.cust_set_tree["displaycolumns"] = (self.cs_column_names[1:-6])

    def selected_document(self):
        """Take selected document"""
        selected_doc = self.cust_set_tree.focus()
        document = self.cust_set_tree.item(selected_doc).get('values')
        return document

    def settle_document_button_command(self):
        """Open new window to settle customers receivables and liabilities"""
        if self.selected_document() == '':
            pass
        elif self.selected_document()[10] == '✔':
            tkinter.messagebox.showerror(title="ERROR", message="This document is already settled", parent=self)
        else:
            no_journal = self.selected_document()[0]
            cust_account = self.selected_document()[3]
            cust_id = self.selected_document()[13]
            cust_name = self.selected_document()[14]
            settlement_type = ''
            if float(self.selected_document()[6].replace('\xa0', '')) != 0:
                settlement_type = "liabilities"
            elif float(self.selected_document()[7].replace('\xa0', '')) != 0:
                settlement_type = "receivables"
            cust_settlements_class = CustomerSettlements(self, no_journal, cust_account, settlement_type, cust_id,
                                                         cust_name)
            cust_settlements_class.on_close(self.refresh_cust_set_tree)

    def show_unsettled_button_command(self):
        """Show unsettled documents when button is pressed"""
        if self.show_unsettled_button["relief"] == "sunken":
            self.show_unsettled_button["relief"] = "raised"
            self.show_unsettled_button.configure(relief="raised", bg="SystemButtonFace")
            self.show_unsettled = False
        else:
            self.show_unsettled_button["relief"] = "sunken"
            self.show_unsettled_button.configure(relief="sunken", bg="light grey")
            self.show_unsettled = True
        self.refresh_cust_set_tree()

    def show_settled_button_command(self):
        """Show settled documents when button is pressed"""
        if self.show_settled_button["relief"] == "sunken":
            self.show_settled_button["relief"] = "raised"
            self.show_settled_button.configure(relief="raised", bg="SystemButtonFace")
            self.show_settled = False
        else:
            self.show_settled_button["relief"] = "sunken"
            self.show_settled_button.configure(relief="sunken", bg="light grey")
            self.show_settled = True
        self.refresh_cust_set_tree()

    def refresh_cust_set_tree(self):
        """Refresh chart of accounts tree"""
        self.cust_set_tree.delete(*self.cust_set_tree.get_children())
        self.on_header_click_cs_trv(col='inv_due_date')

    def show_settlements_command(self):
        """Open new window and show how documents were settled"""
        if self.selected_document() == '':
            pass
        elif self.selected_document()[9] == '0.00':
            tkinter.messagebox.showerror(title="ERROR", message="This document has no settlements", parent=self)
        else:
            selected = self.selected_document()
            cust_id = selected[13]
            cust_name = selected[14]
            doc_number = selected[5]
            receivables = selected[6]
            liabilities = selected[7]
            no_journal = selected[0]
            show_settlements = ShowSettlements(self, cust_id, cust_name, doc_number,
                                               receivables, liabilities, no_journal)
            show_settlements.on_delete(self.refresh_cust_set_tree)

    def show_document_button_command(self):
        if self.selected_document() == '':
            pass
        else:
            doc_type = self.selected_document()[1]
            doc_date = self.selected_document()[2]
            journal_entry_date = self.selected_document()[15]
            doc_number = self.selected_document()[5]
            cust_id = self.selected_document()[13]
            cust_name = self.selected_document()[14]
            orig_doc_number = self.selected_document()[16]
            account_num = self.selected_document()[3]
            account_name = self.selected_document()[4]
            description = self.selected_document()[17]
            int_doc_number = self.selected_document()[18]

            if doc_type == 'purchase costs':
                doc_type = 'Cost Purchase Invoice'
                invoice.ViewInvoice(self, doc_type, journal_entry_date, doc_number, cust_id, cust_name)
            elif doc_type == 'sale service':
                doc_type = 'Service Sales Invoice'
                invoice.ViewInvoice(self, doc_type, journal_entry_date, doc_number, cust_id, cust_name)

            elif doc_type == '[COR] purchase costs':
                doc_type = 'Cost Purchase Invoice'
                invoice.ViewCorrectingInvoice(self, doc_type, journal_entry_date, doc_number, cust_id, cust_name,
                                              orig_doc_number, 'view')
            elif doc_type == '[COR] sale service':
                doc_type = 'Service Sales Invoice'
                invoice.ViewCorrectingInvoice(self, doc_type, journal_entry_date, doc_number, cust_id, cust_name,
                                              orig_doc_number, 'view')
            elif doc_type == 'Bank' or doc_type == "Cash register":
                doc_type = ''
                amount = ''
                if self.selected_document()[6] == '0.00':
                    doc_type = 'Deposit'
                    amount = self.selected_document()[7]
                elif self.selected_document()[7] == '0.00':
                    doc_type = 'Withdrawal'
                    amount = self.selected_document()[6]
                bank_cash = bank_cash_register.WithdrawDeposit(self, cash_flow_type=None, register=None,
                                                               register_number=None, register_date=None,
                                                               reg_account=None, doc_type=doc_type)
                bank_cash.account_entry.config(text=f"{account_num} ~ {account_name}", state='disabled')
                bank_cash.customer_entry.config(text=f"{cust_id} ~ {cust_name}", state='disabled')
                bank_cash.amount_entry.insert('end', amount)
                bank_cash.amount_entry.config(state='readonly')
                bank_cash.description_entry.insert('end', description)
                bank_cash.description_entry.config(state='readonly')
                bank_cash.save_button.config(state='disabled')
            else:
                journal_voucher.ViewJournalVoucher(self, 'Journal voucher', doc_type, doc_date, int_doc_number)


class ShowSettlements(tkinter.Toplevel):
    def __init__(self, parent, cust_id, cust_name, doc_number, receivables, liabilities, no_journal):
        """Open new window and show how documents were settled"""
        super().__init__(parent)

        self.cust_id = cust_id
        self.cust_name = cust_name
        self.doc_number = doc_number
        self.receivables = receivables
        self.liabilities = liabilities
        self.no_journal = no_journal

        self.config(padx=10, pady=10)
        self.title(f"Cust: {self.cust_id} - {self.cust_name}")
        self.grab_set()
        self.resizable(False, False)

        # Labels
        doc_number_label = tkinter.Label(self, text=f"Document number:   {self.doc_number}")
        doc_number_label.grid(column=0, row=0)
        doc_val = "{:,.2f}".format(float(self.receivables.replace('\xa0', '')) +
                                   float(self.liabilities.replace('\xa0', ''))).replace(',', ' ')
        doc_value_label = tkinter.Label(self, text=f"Document value:   {doc_val}")
        doc_value_label.grid(column=0, row=1)

        # Connect to SQL database to get settlements
        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(f"SELECT settlement FROM journal WHERE no_journal={self.no_journal}")
        records = execute['records']

        settlement_list = []
        for item in records:
            try:
                settlement_dict = ast.literal_eval(item[0])
                settlement_list.append(settlement_dict)
            except Exception:
                pass
        key_str = ''
        for item in settlement_list:
            for key in item:
                key_str += f"{key}, "

        sql_command = f"SELECT no_journal, doc_type, doc_date, doc_number, settlement AS settled_amount " \
                      f"FROM journal WHERE no_journal IN ({key_str[:-2]}) ORDER BY doc_date"

        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)

        column_names = execute['column_names']
        self.settlements_tree = ttk.Treeview(self, columns=column_names, show='headings', height=10)
        column = 0
        for _ in column_names:
            self.settlements_tree.heading(column_names[column], text=f'{column_names[column]}')
            column += 1

        # Adjust column width
        self.settlements_tree.column(column_names[1], width=120)
        self.settlements_tree.column(column_names[2], width=100, anchor='center')
        self.settlements_tree.column(column_names[3], width=150, anchor='e')
        self.settlements_tree.column(column_names[4], width=150, anchor='e')

        self.settlements_tree["displaycolumns"] = (column_names[1:])

        self.settlements_tree.grid(column=0, row=2)

        self.records = execute['records']

        # Get settlement values from dictionary
        values = []
        for item in self.records:
            lst = list(item)
            for d in settlement_list:
                if item[0] in d:
                    lst[4] = '{:,.2f}'.format(d.get(item[0])).replace(',', ' ')
            values.append(lst)

        # Insert records
        record = 0
        for _ in values:
            self.settlements_tree.insert('', tkinter.END, values=values[record])
            record += 1

        delete_settlement_button = tkinter.Button(self, text="Delete settlement",
                                                  command=self.delete_settlement_button_command)
        delete_settlement_button.grid(column=0, row=3)

    def delete_settlement_button_command(self):
        """Delete settlement from selected document"""
        try:
            answer = tkinter.messagebox.askyesno(title='Warning', message='Delete settlement?', parent=self)
            if answer:
                selected = self.settlements_tree.focus()
                doc_to_delete_settle = self.settlements_tree.item(selected).get('values')[0]

                # Delete settlement from first document
                set_dict = None
                for item in self.records:
                    if item[0] == doc_to_delete_settle:
                        set_dict = ast.literal_eval(item[4])
                        del set_dict[self.no_journal]

                # Get second document settlements dictionary
                conn = sqlcommand.SqlCommand()
                execute = conn.sql_execute(f"SELECT settlement FROM journal WHERE no_journal={self.no_journal}")
                set_dict_2 = execute['records'][0][0]
                set_dict_2 = ast.literal_eval(set_dict_2)
                # Delete settlement from second document
                del set_dict_2[doc_to_delete_settle]

                sql_command = f"UPDATE journal AS j SET " \
                              f"settlement = c.settlement " \
                              f"FROM (VALUES \n" \
                              f"({doc_to_delete_settle}, '{set_dict}'), \n" \
                              f"({self.no_journal}, '{set_dict_2}') \n" \
                              f") AS c(no_journal, settlement) " \
                              f"WHERE c.no_journal = j.no_journal "

                conn = sqlcommand.SqlCommand()
                conn.sql_execute(sql_command)

                # Delete selected position from treeview
                self.settlements_tree.delete(selected)

                self.deleted_callback()
        except:
            pass

    def on_delete(self, callback):
        self.callback = callback

    def deleted_callback(self):
        self.callback()


class CustomerSettlements(tkinter.Toplevel):

    def __init__(self, parent, no_journal, cust_account, settlement_type, cust_id, cust_name):
        """Settle customers receivables and liabilities"""
        super().__init__(parent)

        self.no_journal = no_journal
        self.cust_account = cust_account
        self.settlement_type = settlement_type
        self.cust_id = cust_id
        self.cust_name = cust_name

        self.title(f"{cust_id} - {cust_name} - Customer settlement")
        self.config(pady=20, padx=20)
        self.resizable(False, False)

        # Headers
        self.account_num_header = tkinter.Label(self, text='Acc num', width=10)
        self.account_num_header.grid(column=0, row=0)
        self.account_name_header = tkinter.Label(self, text='Account name', width=20)
        self.account_name_header.grid(column=1, row=0)
        self.due_date_header = tkinter.Label(self, text='Due date', width=15)
        self.due_date_header.grid(column=2, row=0)
        self.payment_method_header = tkinter.Label(self, text='Payment method', width=20)
        self.payment_method_header.grid(column=3, row=0)
        self.doc_date_header = tkinter.Label(self, text='Document date', width=15)
        self.doc_date_header.grid(column=4, row=0)
        self.doc_type_header = tkinter.Label(self, text='Document type', width=20)
        self.doc_type_header.grid(column=5, row=0)
        self.doc_number_header = tkinter.Label(self, text='Document number', width=20)
        self.doc_number_header.grid(column=6, row=0)
        self.doc_value_header = tkinter.Label(self, text='Document value', width=20)
        self.doc_value_header.grid(column=7, row=0)
        self.left_to_settle_header = tkinter.Label(self, text='Left to settle', width=20)
        self.left_to_settle_header.grid(column=8, row=0)
        self.settle_amount_header = tkinter.Label(self, text='Settle amount', width=25)
        self.settle_amount_header.grid(column=9, row=0)

        # Add scrollbar
        self.frame = tkinter.Frame(self)
        self.frame.grid(column=0, row=1, columnspan=10)

        self.scrollbar = tkinter.Scrollbar(self.frame)
        self.scrollbar.grid(column=10, row=0, sticky='ns')

        self.canvas = tkinter.Canvas(self.frame, yscrollcommand=self.scrollbar.set, width=1330, height=482,
                                     highlightthickness=0, borderwidth=1, relief='groove')
        self.canvas.grid(column=0, row=0, columnspan=10)

        self.lines_frame = tkinter.Frame(self.canvas)
        self.lines_frame.grid(column=0, row=0, columnspan=10)

        self.lines_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.lines_frame, anchor='nw')

        self.canvas.config(yscrollcommand=self.scrollbar.set)

        self.scrollbar.config(command=self.canvas.yview)

        # Connect to SQL database to get customer settlements
        sql_command = f"""
        SELECT 
        CASE WHEN dt.customer_settlement = 'True' THEN dt_account_num ELSE ct_account_num END AS account_num,
        CASE WHEN dt.customer_settlement = 'True' THEN dt.account_name ELSE ct.account_name END,
        inv_due_date, COALESCE(inv_payment_method,'') AS inv_payment_method, doc_date, doc_type, doc_number,
        CASE WHEN dt.customer_settlement = 'True' THEN amount ELSE amount * -1 END AS amount, settlement,
        no_journal,
        CASE WHEN dt.customer_settlement = 'True' THEN amount END AS receivables,
        CASE WHEN ct.customer_settlement = 'True' THEN amount END AS liabilities
        FROM journal 
        LEFT JOIN customers
        ON journal.cust_id = customers.cust_id
        LEFT JOIN chart_of_accounts AS dt
        ON journal.dt_account_num = dt.account_num
        LEFT JOIN chart_of_accounts AS ct
        ON journal.ct_account_num = ct.account_num
        WHERE dt.customer_settlement = 'True' AND journal.cust_id = {self.cust_id}
        OR ct.customer_settlement = 'True' AND journal.cust_id = {self.cust_id}
        ORDER BY inv_due_date, no_journal
        """

        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)
        records = execute['records']

        # List for all added lines
        self.account_num_list = []
        self.account_name_list = []
        self.due_date_list = []
        self.payment_method_list = []
        self.doc_date_list = []
        self.doc_type_list = []
        self.doc_number_list = []
        self.doc_value_list = []
        self.left_to_settle_button_list = []
        self.left_to_settle_hidden_list = []
        self.settle_amount_entry_list = []
        self.no_journal_hidden_list = []

        self.list_of_str_var = []

        # Take current settled document type
        current_doc_type = ''
        for record in records:
            if record[9] == self.no_journal:
                current_doc_type = record[5]
                # Take current settled doc previous settlements
                self.settled_doc_previous_settlements = record[8]

        n = 0
        self.previous_settlements_list = []
        self.changed_sign = []
        for record in records:
            # Check if record is current settled document to not add it to list
            if record[9] == self.no_journal:
                # Take current settled document value
                if record[8] is None:
                    if record[10] == None:
                        self.document_value = float(record[11])
                    else:
                        self.document_value = float(record[10])
                else:
                    # Calculate current settled document value and subtract previous settlements
                    try:
                        set_dict = ast.literal_eval(record[8])
                        settled = sum(set_dict.values())
                    except Exception:
                        settled = 0
                    if record[10] == None:
                        self.document_value = float(record[11]) - settled
                    else:
                        self.document_value = float(record[10]) - settled
            # Check if document is settled already
            else:
                try:
                    set_dict = ast.literal_eval(record[8])
                    settled = sum(set_dict.values())
                except Exception:
                    settled = 0
                if record[10] == None:
                    value_to_settle = float(record[11]) - settled
                else:
                    value_to_settle = float(record[10] * -1) + settled
                # If document is settled then pass
                if value_to_settle == 0 or record[5] == current_doc_type and record[5] != 'transfer':
                    pass
                # If document is not settled then add to list
                else:
                    # Append previous settlement to list
                    self.previous_settlements_list.append(record[8])
                    self.account_num = tkinter.Label(self.lines_frame, text=record[0], relief='sunken', width=10)
                    self.account_num.grid(column=0, row=1 + n)
                    self.account_name = tkinter.Label(self.lines_frame, text=record[1], relief='sunken', width=20,
                                                      anchor='w')
                    self.account_name.grid(column=1, row=1 + n)
                    # Red foreground color if due date is expired, green if is not expired
                    if record[2] == None:
                        self.due_date = tkinter.Label(self.lines_frame, text=record[2], relief='sunken', width=15)
                    elif record[2] < datetime.now().date():
                        self.due_date = tkinter.Label(self.lines_frame, text=record[2], relief='sunken', width=15,
                                                      fg='red')
                    else:
                        self.due_date = tkinter.Label(self.lines_frame, text=record[2], relief='sunken', width=15,
                                                      fg='green')
                    self.due_date.grid(column=2, row=1 + n)
                    self.payment_method = tkinter.Label(self.lines_frame, text=record[3], relief='sunken', width=20,
                                                        anchor='w')
                    self.payment_method.grid(column=3, row=1 + n)
                    self.doc_date = tkinter.Label(self.lines_frame, text=record[4], relief='sunken', width=15)
                    self.doc_date.grid(column=4, row=1 + n)
                    self.doc_type = tkinter.Label(self.lines_frame, text=record[5], relief='sunken', width=20,
                                                  anchor='w')
                    self.doc_type.grid(column=5, row=1 + n)
                    self.doc_number = tkinter.Label(self.lines_frame, text=record[6], relief='sunken', width=20,
                                                    anchor='w')
                    self.doc_number.grid(column=6, row=1 + n)
                    # Take value depending on document type
                    if record[10] is None:
                        doc_value = float(record[11])
                    else:
                        doc_value = float(record[10])
                    self.doc_value = tkinter.Label(self.lines_frame, text='{:,.2f}'.format(doc_value).replace(',', ' '),
                                                   relief='sunken', width=20, anchor='e')
                    self.doc_value.grid(column=7, row=1 + n)
                    # Take value depending on document type
                    if record[8] is None:
                        if record[10] is None:
                            if self.settlement_type == 'liabilities':
                                left_to_settle = float(record[11])
                            else:
                                left_to_settle = float(record[11]) * -1
                                # Append to list if sign has been changed
                                self.changed_sign.append(record[9])
                        else:
                            if self.settlement_type == 'receivables':
                                left_to_settle = float(record[10])
                            else:
                                left_to_settle = float(record[10]) * -1
                                # Append to list if sign has been changed
                                self.changed_sign.append(record[9])
                    else:
                        # Subtract previous settlements
                        try:
                            set_dict = ast.literal_eval(record[8])
                            settled = sum(set_dict.values())
                        except Exception:
                            settled = 0
                        if record[10] is None:
                            if self.settlement_type == 'liabilities':
                                left_to_settle = float(record[11]) - settled
                            else:
                                left_to_settle = (float(record[11]) - settled) * -1
                                # Append to list if sign has been changed
                                self.changed_sign.append(record[9])
                        else:
                            if self.settlement_type == 'receivables':
                                left_to_settle = float(record[10]) - settled
                            else:
                                left_to_settle = (float(record[10]) - settled) * -1
                                # Append to list if sign has been changed
                                self.changed_sign.append(record[9])
                    self.left_to_settle_button = tkinter.Button(
                        self.lines_frame, text='{:,.2f}'.format(left_to_settle).replace(',', ' '), relief='ridge', width=20,
                        fg='blue', anchor='e', command=self.fill_amount_entry, overrelief='groove')
                    self.left_to_settle_button.grid(column=8, row=1 + n)
                    self.left_to_settle_hidden = tkinter.Label(text=left_to_settle)

                    self.amount_str_var = tkinter.StringVar()
                    self.amount_str_var.set('0.00')
                    self.settle_amount_entry = tkinter.Entry(self.lines_frame, textvariable=self.amount_str_var,
                                                             width=25, justify='right')
                    self.settle_amount_entry.grid(column=9, row=1 + n)

                    self.no_journal_hidden = tkinter.Label(text=record[9])
                    n += 1

                    # Bind name of widget with function
                    self.settle_amount_entry.bind('<FocusOut>', self.check_entry)
                    self.left_to_settle_button.bind('<Button-1>', self.clicked_button)

                    # Append all created lines to list
                    self.account_num_list.append(self.account_num)
                    self.account_name_list.append(self.account_name)
                    self.due_date_list.append(self.due_date)
                    self.payment_method_list.append(self.payment_method)
                    self.doc_date_list.append(self.doc_date)
                    self.doc_type_list.append(self.doc_type)
                    self.doc_number_list.append(self.doc_number)
                    self.doc_value_list.append(self.doc_value)
                    self.left_to_settle_button_list.append(self.left_to_settle_button)
                    self.left_to_settle_hidden_list.append(self.left_to_settle_hidden)
                    self.settle_amount_entry_list.append(self.settle_amount_entry)
                    self.no_journal_hidden_list.append(self.no_journal_hidden)

                    self.list_of_str_var.append(self.amount_str_var)

        for item in range(int(len(self.list_of_str_var))):
            self.list_of_str_var[item].trace(
                'w', partial(self.entry_fill, self.settle_amount_entry_list[item]))

        # Bottom widgets
        self.amount_to_be_settled_label = tkinter.Label(self, text="Amount to be settled: ")
        self.amount_to_be_settled_label.grid(column=8, row=2 + n, pady=(20, 10), sticky='e')
        self.amount_to_be_settled_entry = tkinter.Entry(self, width=25, justify='right')
        self.amount_to_be_settled_entry.insert('end', '{:,.2f}'.format(self.document_value).replace(',', ' '))
        self.amount_to_be_settled_entry.config(state='readonly')
        self.amount_to_be_settled_entry.grid(column=9, row=2 + n, pady=(20, 10))
        self.left_to_be_settled_label = tkinter.Label(self, text="Left to be settled: ")
        self.left_to_be_settled_label.grid(column=8, row=3 + n, pady=(0, 20), sticky='e')
        self.left_to_be_settled_entry = tkinter.Entry(self, width=25, justify='right', state='readonly')
        self.left_to_be_settled_entry.grid(column=9, row=3 + n, pady=(0, 20))
        self.reset_button = tkinter.Button(self, text="Reset", command=self.reset_button_command, padx=30, pady=10)
        self.reset_button.grid(column=8, row=4 + n)
        self.settle_button = tkinter.Button(self, text="Settle", command=self.settle_button_command, padx=30, pady=10)
        self.settle_button.grid(column=9, row=4 + n)

        self.calculate_left_to_be_settled_entry()

    def check_entry(self, event):
        """Check and corrects values in entries if values are exceeded"""
        entry = event.widget
        entry_value = entry.get().replace(' ', '')
        pos_left_to_settle = float(self.left_to_settle_hidden_list[self.settle_amount_entry_list.index(entry)]['text'])
        if entry_value == '':
            pass
        elif pos_left_to_settle < 0:
            if float(entry_value) > 0:
                entry.delete(0, 'end')
                entry.insert('end', '{:,.2f}'.format(float(entry_value) * -1).replace(',', ' '))
            if float(entry.get().replace(' ', '')) < pos_left_to_settle:
                entry.delete(0, 'end')
                entry.insert('end', '{:,.2f}'.format(pos_left_to_settle).replace(',', ' '))
        elif pos_left_to_settle > 0:
            if float(entry_value) < 0:
                entry.delete(0, 'end')
                entry.insert('end', '{:,.2f}'.format(float(entry_value) * -1).replace(',', ' '))
            if float(entry.get().replace(' ', '')) > pos_left_to_settle:
                entry.delete(0, 'end')
                entry.insert('end', '{:,.2f}'.format(pos_left_to_settle).replace(',', ' '))

        self.calculate_left_to_settle()

    def calculate_left_to_settle(self):
        """Calculate how many left to settle when entry with settlement is filled"""
        lines = int(len(self.no_journal_hidden_list))
        for n in range(lines):
            settle_entry = 0
            if self.settle_amount_entry_list[n].get() == '':
                pass
            else:
                settle_entry = float(self.settle_amount_entry_list[n].get().replace(' ', ''))
            left_to_settle = float(self.left_to_settle_hidden_list[n]['text'])
            left_to_settle_actualized = '{:,.2f}'.format(left_to_settle - settle_entry).replace(',', ' ')
            self.left_to_settle_button_list[n].config(text=left_to_settle_actualized)
        # Calculate total left to be settled
        self.calculate_left_to_be_settled_entry()

    def clicked_button(self, event):
        """Return clicked button"""
        self.clicked_btn = event.widget

    def fill_amount_entry(self):
        """Fill amount entry when left to settle button is pressed"""
        amount_to_be_settled = float(self.amount_to_be_settled_entry.get().replace(' ', ''))
        left_to_be_settled = float(self.left_to_be_settled_entry.get().replace(' ', ''))
        entry = self.settle_amount_entry_list[self.left_to_settle_button_list.index(self.clicked_btn)]
        pos_left_to_settle = \
            float(self.left_to_settle_hidden_list[self.left_to_settle_button_list.index(self.clicked_btn)]['text'])
        to_fill = 0
        if amount_to_be_settled > 0:
            if float(self.clicked_btn['text'].replace(' ', '')) >= left_to_be_settled:
                current_entry = 0 if entry.get() == '' else float(entry.get().replace(' ', ''))
                if left_to_be_settled < 0:
                    to_fill = "%.2f" % pos_left_to_settle
                else:
                    to_fill = "%.2f" % (left_to_be_settled + current_entry)
            elif float(self.clicked_btn['text'].replace(' ', '')) < left_to_be_settled:
                to_fill = "%.2f" % pos_left_to_settle
        elif amount_to_be_settled < 0:
            if float(self.clicked_btn['text'].replace(' ', '')) <= left_to_be_settled:
                current_entry = 0 if entry.get() == '' else float(entry.get().replace(' ', ''))
                if left_to_be_settled > 0:
                    to_fill = "%.2f" % pos_left_to_settle
                else:
                    to_fill = "%.2f" % (left_to_be_settled + current_entry)
            elif float(self.clicked_btn['text'].replace(' ', '')) > left_to_be_settled:
                to_fill = "%.2f" % pos_left_to_settle

        entry.delete(0, 'end')
        entry.insert('end', to_fill)
        btn_pos_left_to_settle = float(entry.get().replace(' ', '')) - float(pos_left_to_settle)
        self.clicked_btn.config(text='{:,.2f}'.format(btn_pos_left_to_settle).replace(',', ' '))

        # Calculate left to be settled
        self.calculate_left_to_settle()
        # Calculate total left to be settled
        self.calculate_left_to_be_settled_entry()

    def calculate_left_to_be_settled_entry(self):
        """Calculates amount which left to settle"""
        total = float(self.amount_to_be_settled_entry.get().replace(' ', ''))
        lines = int(len(self.no_journal_hidden_list))
        settled = 0
        for n in range(lines):
            if self.settle_amount_entry_list[n].get() == '':
                pass
            else:
                settled += float(self.settle_amount_entry_list[n].get().replace(' ', ''))
        result = '{:,.2f}'.format(total - settled).replace(',', ' ')
        self.left_to_be_settled_entry.config(state='normal')
        self.left_to_be_settled_entry.delete(0, 'end')
        self.left_to_be_settled_entry.insert('end', result)
        self.left_to_be_settled_entry.config(state='readonly')

    def reset_button_command(self):
        """Reset all settlements and delete all entries"""
        lines = int(len(self.no_journal_hidden_list))
        for n in range(lines):
            self.settle_amount_entry_list[n].delete(0, 'end')
            self.settle_amount_entry_list[n].insert('end', '0.00')
        self.calculate_left_to_settle()

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

    def settle_button_command(self):
        """Save settlement in SQL database"""
        if float(self.amount_to_be_settled_entry.get().replace(' ', '')) > 0 and \
                float(self.amount_to_be_settled_entry.get().replace(' ', '')) < \
                float(self.left_to_be_settled_entry.get().replace(' ', '')) or \
                float(self.amount_to_be_settled_entry.get().replace(' ', '')) > 0 and \
                float(self.left_to_be_settled_entry.get().replace(' ', '')) < 0 or \
                float(self.amount_to_be_settled_entry.get().replace(' ', '')) < 0 and \
                float(self.amount_to_be_settled_entry.get().replace(' ', '')) > \
                float(self.left_to_be_settled_entry.get().replace(' ', '')) or \
                float(self.amount_to_be_settled_entry.get().replace(' ', '')) < 0 and \
                float(self.left_to_be_settled_entry.get().replace(' ', '')) > 0:
            tkinter.messagebox.showerror(title="ERROR",
                                         message="The settlement amount is greater than the document amount",
                                         parent=self)
        else:
            lines = int(len(self.no_journal_hidden_list))
            x = 0
            update_list = []
            settlement_dict = ''
            different_accounts = False
            for n in range(lines):
                values = ''
                if float(self.settle_amount_entry_list[n].get().replace(' ', '')) == 0:
                    pass
                # Check if all accounts are the same
                elif self.account_num_list[n]['text'] != str(self.cust_account):
                    different_accounts = True
                else:
                    # Check if the sign has been changed
                    if self.no_journal_hidden_list[n]['text'] in self.changed_sign:
                        mark = -1
                    else:
                        mark = 1
                    # Settled documents
                    set_dict = \
                        {self.no_journal: float(self.settle_amount_entry_list[n].get().replace(' ', '')) * mark}
                    # Check if there were other settlements before
                    if self.previous_settlements_list[x] == None:
                        update_string = f"({self.no_journal_hidden_list[n]['text']}, '{set_dict}')"
                        update_list.append(update_string)
                    else:
                        # Gather all dictionaries and look for duplicated keys to sum values and delete duplicates
                        previous_settlement = ast.literal_eval(self.previous_settlements_list[x])
                        actual_settlement = set_dict

                        merged_dict = {}

                        # Add keys and values from previous_settlement
                        for key, value in previous_settlement.items():
                            if key in merged_dict:
                                merged_dict[key] += value
                            else:
                                merged_dict[key] = value

                        # Add keys and values from actual_settlement
                        for key, value in actual_settlement.items():
                            if key in merged_dict:
                                merged_dict[key] += value
                            else:
                                merged_dict[key] = value

                        update_string = f"({self.no_journal_hidden_list[n]['text']}, '{merged_dict}')"
                        update_list.append(update_string)

                    values += str(float(self.settle_amount_entry_list[n].get().replace(' ', '')))
                    settlement_dict += f"{self.no_journal_hidden_list[n]['text']}: {values}, "

                x += 1

            # Break if accounts are not the same
            if different_accounts == True:
                tkinter.messagebox.showerror(title="ERROR",
                                             message="Only documents with the same account can be settled",
                                             parent=self)
            else:
                # Gather all dictionaries and look for duplicated keys to sum values and delete duplicates
                # Check if there were other settlements before
                if self.settled_doc_previous_settlements == None:
                    all_dict = f"{{{settlement_dict[:-2]}}}"
                else:
                    previous_settlement = ast.literal_eval(self.settled_doc_previous_settlements)
                    actual_settlement = ast.literal_eval(f"{{{settlement_dict[:-2]}}}")

                    all_dict = {}

                    # Add keys and values from previous_settlement
                    for key, value in previous_settlement.items():
                        if key in all_dict:
                            all_dict[key] += value
                        else:
                            all_dict[key] = value

                    # Add keys and values from actual_settlement
                    for key, value in actual_settlement.items():
                        if key in all_dict:
                            all_dict[key] += value
                        else:
                            all_dict[key] = value

                update_string = f"({self.no_journal}, '{all_dict}')"
                update_list.append(update_string)

                update_list_string = ''
                for item in update_list:
                    update_list_string += f"{item}, \n"

                sql_command = f"UPDATE journal AS j SET " \
                              f"settlement = c.settlement " \
                              f"FROM (VALUES \n" \
                              f"{update_list_string[:-3]} \n" \
                              f") AS c(no_journal, settlement) " \
                              f"WHERE c.no_journal = j.no_journal " \

                conn = sqlcommand.SqlCommand()
                conn.sql_execute(sql_command)

                self.close()

    def on_close(self, callback):
        self.callback = callback

    def close(self):
        self.callback()
        self.destroy()
