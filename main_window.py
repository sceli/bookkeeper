import tkinter
import bank_cash_register
import customer_settlements
import open_new_year
import sql_parameters
import chart_of_accounts
import company
import journal
import customers
import journal_voucher
import login_window
import invoice
import trial_balance
import vat_rates
import invoice_indexes


class MainWindow(tkinter.Tk):

    def __init__(self):
        super().__init__()

        self.title(f"Bookkeeper - {sql_parameters.database}")
        self.resizable(False, False)

        self.menubar = tkinter.Menu()
        self.bookkeeper_menu = tkinter.Menu(self.menubar, tearoff=0)
        self.bookkeeper_menu.add_command(label="Company", command=self.company)
        self.bookkeeper_menu.add_separator()
        self.bookkeeper_menu.add_command(label="Log out", command=self.log_out)
        self.menubar.add_cascade(label="Bookkeeper", menu=self.bookkeeper_menu)
        self.config(menu=self.menubar)

        options_frame = tkinter.Frame(self, bg='#c3c3c3')

        general_ledger_btn = tkinter.Button(options_frame, text='General ledger', font=('Bold', 15), cursor='hand2',
                                            fg='#158aff', bd=0, bg='#c3c3c3', activebackground='#c3c3c3',
                                            command=lambda: self.indicate(self.general_ledger_indicate,
                                                                          self.general_ledger))
        general_ledger_btn.place(x=10, y=50)
        self.general_ledger_indicate = tkinter.Label(options_frame, text='', bg='#c3c3c3')
        self.general_ledger_indicate.place(x=3, y=50, width=5, height=40)

        settlements_btn = tkinter.Button(options_frame, text='Settlements', font=('Bold', 15), cursor='hand2',
                                         fg='#158aff', bd=0, bg='#c3c3c3', activebackground='#c3c3c3',
                                         command=lambda: self.indicate(self.settlements_indicate, self.settlements))
        settlements_btn.place(x=10, y=100)
        self.settlements_indicate = tkinter.Label(options_frame, text='', bg='#c3c3c3')
        self.settlements_indicate.place(x=3, y=100, width=5, height=40)

        customers_btn = tkinter.Button(options_frame, text='Customers', font=('Bold', 15), cursor='hand2',
                                       fg='#158aff', bd=0, bg='#c3c3c3', activebackground='#c3c3c3',
                                       command=lambda: self.indicate(self.customers_indicate, self.customers))
        customers_btn.place(x=10, y=150)
        self.customers_indicate = tkinter.Label(options_frame, text='', bg='#c3c3c3')
        self.customers_indicate.place(x=3, y=150, width=5, height=40)

        settings_btn = tkinter.Button(options_frame, text='Settings', font=('Bold', 15), cursor='hand2',
                                      fg='#158aff', bd=0, bg='#c3c3c3', activebackground='#c3c3c3',
                                      command=lambda: self.indicate(self.settings_indicate, self.settings))
        settings_btn.place(x=10, y=200)
        self.settings_indicate = tkinter.Label(options_frame, text='', bg='#c3c3c3')
        self.settings_indicate.place(x=3, y=200, width=5, height=40)

        options_frame.pack(side='left')
        options_frame.pack_propagate(False)
        options_frame.configure(width=200, height=720)

        self.main_frame = tkinter.Frame(self, highlightbackground='black', highlightthickness=2)

        self.main_frame.pack(side='left')
        self.main_frame.pack_propagate(False)
        self.main_frame.configure(width=1080, height=720)

    def general_ledger(self):
        general_ledger_frame = tkinter.Frame(self.main_frame)

        self.lb = tkinter.Label(general_ledger_frame, text='General ledger', font=('Bold', 30))
        self.lb.pack(pady=(0, 50))

        self.chart_of_accounts_button = tkinter.Button(general_ledger_frame, text="Chart of accounts",
                                                       relief='flat', overrelief='flat', bd=0,
                                                       cursor='hand2', font=('Bold', 20),
                                                       command=self.chart_of_accounts)
        self.chart_of_accounts_button.pack()

        self.vouchers_button = tkinter.Button(general_ledger_frame, text="Vouchers",
                                              relief='flat', overrelief='flat', bd=0,
                                              cursor='hand2', font=('Bold', 20),
                                              command=self.vouchers)
        self.vouchers_button.pack()

        self.journal_button = tkinter.Button(general_ledger_frame, text="Journal",
                                             relief='flat', overrelief='flat', bd=0,
                                             cursor='hand2', font=('Bold', 20),
                                             command=self.journal)
        self.journal_button.pack()

        self.trial_balance_button = tkinter.Button(general_ledger_frame, text="Trial balance",
                                                   relief='flat', overrelief='flat', bd=0,
                                                   cursor='hand2', font=('Bold', 20),
                                                   command=self.trial_balance)
        self.trial_balance_button.pack()

        general_ledger_frame.pack(pady=20)

    def settlements(self):
        settlements_frame = tkinter.Frame(self.main_frame)

        self.lb = tkinter.Label(settlements_frame, text='Settlements', font=('Bold', 30))
        self.lb.pack(pady=(0, 50))

        self.cust_rec_liab_button = tkinter.Button(settlements_frame, text="Customers receivables and liabilities",
                                                   relief='flat', overrelief='flat', bd=0,
                                                   cursor='hand2', font=('Bold', 20),
                                                   command=self.cust_rec_liab)
        self.cust_rec_liab_button.pack()

        self.bank_button = tkinter.Button(settlements_frame, text="Bank",
                                          relief='flat', overrelief='flat', bd=0,
                                          cursor='hand2', font=('Bold', 20),
                                          command=self.bank)
        self.bank_button.pack()

        self.cash_register_button = tkinter.Button(settlements_frame, text="Cash register",
                                                   relief='flat', overrelief='flat', bd=0,
                                                   cursor='hand2', font=('Bold', 20),
                                                   command=self.cash_register)
        self.cash_register_button.pack()

        settlements_frame.pack(pady=20)

    def customers(self):
        customers_frame = tkinter.Frame(self.main_frame)

        self.lb = tkinter.Label(customers_frame, text='Customers', font=('Bold', 30))
        self.lb.pack(pady=(0, 50))

        self.customers_list_button = tkinter.Button(customers_frame, text="Customers list",
                                                    relief='flat', overrelief='flat', bd=0,
                                                    cursor='hand2', font=('Bold', 20),
                                                    command=self.customers_list)
        self.customers_list_button.pack()

        self.service_sales_invoice_register_button = tkinter.Button(customers_frame,
                                                                    text="Service Sales Invoice Register",
                                                                    relief='flat', overrelief='flat', bd=0,
                                                                    cursor='hand2', font=('Bold', 20),
                                                                    command=self.service_sales_invoice_register)
        self.service_sales_invoice_register_button.pack()

        self.cost_purchase_invoice_register_button = tkinter.Button(customers_frame,
                                                                    text="Cost Purchase Invoice Register",
                                                                    relief='flat', overrelief='flat', bd=0,
                                                                    cursor='hand2', font=('Bold', 20),
                                                                    command=self.cost_purchase_invoice_register)
        self.cost_purchase_invoice_register_button.pack()

        customers_frame.pack(pady=20)

    def settings(self):
        settings_frame = tkinter.Frame(self.main_frame)

        self.lb = tkinter.Label(settings_frame, text='Settings', font=('Bold', 30))
        self.lb.pack(pady=(0, 50))

        self.edit_company_button = tkinter.Button(settings_frame, text="Edit company",
                                                  relief='flat', overrelief='flat', bd=0,
                                                  cursor='hand2', font=('Bold', 20),
                                                  command=self.edit_company)
        self.edit_company_button.pack()

        self.invoice_indexes_button = tkinter.Button(settings_frame, text="Invoice indexes",
                                                     relief='flat', overrelief='flat', bd=0,
                                                     cursor='hand2', font=('Bold', 20),
                                                     command=self.invoice_indexes)
        self.invoice_indexes_button.pack()

        self.vat_rates_button = tkinter.Button(settings_frame, text="Vat rates",
                                               relief='flat', overrelief='flat', bd=0,
                                               cursor='hand2', font=('Bold', 20),
                                               command=self.vat_rates)
        self.vat_rates_button.pack()

        self.invoice_settings_button = tkinter.Button(settings_frame, text="Invoice settings",
                                                      relief='flat', overrelief='flat', bd=0,
                                                      cursor='hand2', font=('Bold', 20),
                                                      command=self.invoice_settings)
        self.invoice_settings_button.pack()

        self.open_new_year_button = tkinter.Button(settings_frame, text="Open new year",
                                                   relief='flat', overrelief='flat', bd=0,
                                                   cursor='hand2', font=('Bold', 20),
                                                   command=self.open_new_year)
        self.open_new_year_button.pack()

        self.db_conn_config_button = tkinter.Button(settings_frame, text="Database connection configure",
                                                    relief='flat', overrelief='flat', bd=0,
                                                    cursor='hand2', font=('Bold', 20),
                                                    command=self.db_conn_config)
        self.db_conn_config_button.pack()

        settings_frame.pack(pady=20)

    def hide_indicators(self):
        self.general_ledger_indicate.config(bg='#c3c3c3')
        self.settlements_indicate.config(bg='#c3c3c3')
        self.customers_indicate.config(bg='#c3c3c3')
        self.settings_indicate.config(bg='#c3c3c3')

    def delete_pages(self):
        for frame in self.main_frame.winfo_children():
            frame.destroy()

    def indicate(self, lb, page):
        self.hide_indicators()
        lb.config(bg='#158aff')
        self.delete_pages()
        page()

    def company(self):
        company_window = company.Company(self)
        company_window.grab_set()

    def bank(self):
        bank_cash_register.ListOfRegister(self, 'Bank')

    def cash_register(self):
        bank_cash_register.ListOfRegister(self, 'Cash register')

    def cust_rec_liab(self):
        customer_settlements.CustomersReceivablesLiabilities(self)

    def chart_of_accounts(self):
        chart_of_accounts.ChartOfAccounts(self)

    def trial_balance(self):
        trial_balance.SetPeriod(self)

    def journal(self):
        journal.SetPeriod(self)

    def vouchers(self):
        journal_voucher.Vouchers(self)

    def service_sales_invoice_register(self):
        invoice.InvoiceRegister(self, 'Service Sales Invoice')

    def cost_purchase_invoice_register(self):
        invoice.InvoiceRegister(self, 'Cost Purchase Invoice')

    def customers_list(self):
        customers.Customers(self)

    def invoice_settings(self):
        invoice.InvoiceSettings(self)

    def invoice_indexes(self):
        invoice_indexes.InvoiceIndexes(self)

    def vat_rates(self):
        vat_rates.VatRates(self)

    def journal_voucher(self):
        journal_voucher.JournalVoucher(self, "Journal voucher")

    def service_sales_invoice(self):
        invoice.Invoice(self, 'Service Sales Invoice')

    def stock_sales_invoice(self):
        invoice.Invoice(self, 'Stock Sales Invoice')

    def cost_purchase_invoice(self):
        invoice.Invoice(self, 'Cost Purchase Invoice')

    def stock_purchase_invoice(self):
        invoice.Invoice(self, 'Stock Purchase Invoice')

    def edit_company(self):
        company.EditCompany(self)

    def open_new_year(self):
        open_new_year.OpenNewYear(self)

    def db_conn_config(self):
        sql_parameters.SqlConfigWindow(self)

    def log_out(self):
        MainWindow.destroy(self)
        window = login_window.LoginWindow()
        window.mainloop()
