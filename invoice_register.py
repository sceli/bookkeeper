import tkinter
from tkinter import ttk, messagebox
import invoice
import sqlcommand


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

        self.invoice_register_treeview()

        # Create Options Frame
        self.invoice_reg_options = tkinter.Frame(self)
        self.invoice_reg_options.grid(column=1, row=0, sticky='n')

        self.view_document_button = tkinter.Button(self.invoice_reg_options, text="View document",
                                                   command=self.view_invoice, pady=15, padx=15, width=20)
        self.view_document_button.grid(column=0, row=0)
        self.edit_document_button = tkinter.Button(self.invoice_reg_options, text="Edit document",
                                                   command=self.edit_invoice, pady=15, padx=15, width=20)
        self.edit_document_button.grid(column=0, row=1)
        self.correcting_invoice_button = tkinter.Button(self.invoice_reg_options, text="Correcting invoice",
                                                        command=self.correcting_invoice, pady=15, padx=15, width=20)
        self.correcting_invoice_button.grid(column=0, row=2)

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

        self.invoice_reg_tree = ttk.Treeview(self.invoice_reg_frame, columns=column_names, show='headings', height=35)

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

    def view_invoice(self):
        """Open new window with view invoice mode"""
        if self.selected_invoice()[6] == f'[COR] {self.inv_type_short}':
            self.view_correcting_invoice()
        else:
            journal_entry_date = self.selected_invoice()[8]
            doc_number = self.selected_invoice()[2]
            cust_id = self.selected_invoice()[4]
            cust_name = self.selected_invoice()[5]
            invoice.ViewInvoice(self, self.invoice_type, journal_entry_date, doc_number, cust_id, cust_name)

    def edit_invoice(self):
        """Open new window with edit invoice mode"""
        if self.selected_invoice()[6] == f'[COR] {self.inv_type_short}':
            self.edit_correcting_invoice()
        else:
            journal_entry_date = self.selected_invoice()[8]
            doc_number = self.selected_invoice()[2]
            cust_id = self.selected_invoice()[4]
            cust_name = self.selected_invoice()[5]
            invoice.EditInvoice(self, self.invoice_type, journal_entry_date, doc_number, cust_id, cust_name)

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
            invoice.CorrectingInvoice(self, self.invoice_type, journal_entry_date, doc_number, cust_id, cust_name,
                                      orig_doc_number, 'create')

    def view_correcting_invoice(self):
        """Open new window with view correcting invoice mode"""
        journal_entry_date = self.selected_invoice()[8]
        doc_number = self.selected_invoice()[2]
        cust_id = self.selected_invoice()[4]
        cust_name = self.selected_invoice()[5]
        orig_doc_number = self.selected_invoice()[10]

        self.cor_inv_window = invoice.ViewCorrectingInvoice(self, self.invoice_type, journal_entry_date, doc_number,
                                                            cust_id, cust_name, orig_doc_number, 'view')

    def edit_correcting_invoice(self):
        """Open new window with edit correcting invoice mode"""
        journal_entry_date = self.selected_invoice()[8]
        doc_number = self.selected_invoice()[2]
        cust_id = self.selected_invoice()[4]
        cust_name = self.selected_invoice()[5]
        orig_doc_number = self.selected_invoice()[10]

        self.cor_inv_window = invoice.EditCorrectingInvoice(self, self.invoice_type, journal_entry_date, doc_number,
                                                            cust_id, cust_name, orig_doc_number, 'view')

    def refresh_inv_reg_tree(self):
        """Refresh customer tree"""
        self.invoice_reg_tree.delete(*self.invoice_reg_tree.get_children())
        self.invoice_register_treeview()
