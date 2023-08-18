import tkinter
from tkinter import messagebox
import csv
import psycopg2
import sql_parameters
import sqlcommand


class CreateCompany(tkinter.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)

        if self.check_connection() is True:
            self.title("Create Company")
            self.config(pady=10, padx=10)
            self.resizable(False, False)

            self.database_name_label = tkinter.Label(self, text="Database name")
            self.database_name_label.grid(column=0, row=0)
            self.database_name_entry = tkinter.Entry(self, width=60)
            self.database_name_entry.grid(column=1, row=0)

            self.company_name_label = tkinter.Label(self, text="Company name")
            self.company_name_label.grid(column=0, row=1)
            self.company_name_entry = tkinter.Entry(self, width=60)
            self.company_name_entry.grid(column=1, row=1)

            self.tax_identification_number_label = tkinter.Label(self, text="Tax identification number")
            self.tax_identification_number_label.grid(column=0, row=2)
            self.tax_identification_number_entry = tkinter.Entry(self, width=60)
            self.tax_identification_number_entry.grid(column=1, row=2)

            self.street_label = tkinter.Label(self, text="Street")
            self.street_label.grid(column=0, row=3)
            self.street_entry = tkinter.Entry(self, width=60)
            self.street_entry.grid(column=1, row=3)

            self.street_number_label = tkinter.Label(self, text="Street number")
            self.street_number_label.grid(column=0, row=4)
            self.street_number_entry = tkinter.Entry(self, width=60)
            self.street_number_entry.grid(column=1, row=4)

            self.zip_code_label = tkinter.Label(self, text="ZIP code")
            self.zip_code_label.grid(column=0, row=5)
            self.zip_code_entry = tkinter.Entry(self, width=60)
            self.zip_code_entry.grid(column=1, row=5)

            self.city_label = tkinter.Label(self, text="City")
            self.city_label.grid(column=0, row=6)
            self.city_entry = tkinter.Entry(self, width=60)
            self.city_entry.grid(column=1, row=6)

            self.country_label = tkinter.Label(self, text="Country")
            self.country_label.grid(column=0, row=7)
            self.country_entry = tkinter.Entry(self, width=60)
            self.country_entry.grid(column=1, row=7)

            self.country_code_label = tkinter.Label(self, text="Country code")
            self.country_code_label.grid(column=0, row=8)
            self.country_code_entry = tkinter.Entry(self, width=60)
            self.country_code_entry.grid(column=1, row=8)

            self.create_company_button = tkinter.Button(self, text="CREATE COMPANY", command=self.create_company)
            self.create_company_button.grid(column=1, row=9)

        else:
            self.destroy()

    def check_connection(self):
        """Check if there is connection to SQL"""
        try:
            # Database connection settings (change accordingly for your database)
            connection = psycopg2.connect(
                host=sql_parameters.hostname,
                user=sql_parameters.username,
                password=sql_parameters.pwd,
                port=sql_parameters.port_id
            )

            # Create a cursor object
            cursor = connection.cursor()

            cursor.execute("SELECT version();")
            cursor.fetchone()

            # Close cursor and connection
            cursor.close()
            connection.close()

            return True

        except psycopg2.Error as e:
            tkinter.messagebox.showerror(title="ERROR",
                                         message=f"An error occurred while trying to connect to the database: {e}",
                                         parent=self)

    def create_company(self):
        """Create SQL database"""
        # Check if database name has no spaces
        if ' ' in self.database_name_entry.get():
            tkinter.messagebox.showerror(title="ERROR", message="Database name must not contain spaces. \n"
                                                                "Use '_' symbol instead.", parent=self)
        # Check if all necessary entries are filled
        if self.database_name_entry.get() == '' or self.company_name_entry.get() == '' \
            or self.tax_identification_number_entry.get() == '' or self.street_entry.get() == '' \
                or self.street_number_entry.get() == '' or self.zip_code_entry.get() == '' \
                or self.city_entry.get() == '' or self.country_entry.get() == '' \
                or self.country_code_entry.get() == '':
            tkinter.messagebox.showerror(title="ERROR", message="Fill all entries!", parent=self)
        else:
            with open('companies.csv', 'a', newline='') as csv_file:
                new_company = [self.database_name_entry.get()]
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(new_company)

            create_database_cmd = f"CREATE DATABASE {self.database_name_entry.get()}"
            conn = sqlcommand.SqlCommand()
            conn.sql_execute(create_database_cmd)

            create_table_company = '''
            CREATE TABLE company(
            company_name VARCHAR(100) NOT NULL,
            tax_id_num VARCHAR(50) NOT NULL,
            street VARCHAR(100) NOT NULL,
            street_num VARCHAR(50) NOT NULL,
            zip_code VARCHAR(50) NOT NULL,
            city VARCHAR(50) NOT NULL,
            country VARCHAR(50) NOT NULL,
            country_code VARCHAR(20) NOT NULL,
            bank_accounts VARCHAR
            )
            '''
            self.sql_execute(create_table_company)

            insert_into_company = f'''
            INSERT INTO company 
            (company_name, tax_id_num, street, street_num, zip_code, city, country, country_code) 
            VALUES 
            ('{self.company_name_entry.get()}', 
            '{self.tax_identification_number_entry.get()}', '{self.street_entry.get()}', 
            '{self.street_number_entry.get()}', '{self.zip_code_entry.get()}', 
            '{self.city_entry.get()}', '{self.country_entry.get()}', '{self.country_code_entry.get()}')
            '''
            self.sql_execute(insert_into_company)

            create_table_chart_of_accounts = '''
            CREATE TABLE chart_of_accounts(
            account_num VARCHAR(100) UNIQUE NOT NULL,
            account_name VARCHAR(250) NOT NULL,
            customer_settlement BOOLEAN NOT NULL,
            vat_settlement BOOLEAN NOT NULL,
            nominal_account BOOLEAN NOT NULL
            )
            '''
            self.sql_execute(create_table_chart_of_accounts)

            create_table_bank_cash_list = '''
            CREATE TABLE bank_cash_list(
            register_type VARCHAR(30) NOT NULL,
            register VARCHAR(50) NOT NULL UNIQUE,
            reg_short VARCHAR(15) NOT NULL UNIQUE,
            account_num VARCHAR(30) REFERENCES chart_of_accounts(account_num) NOT NULL UNIQUE
            )
            '''
            self.sql_execute(create_table_bank_cash_list)

            create_table_bank_cash_register = '''
            CREATE TABLE bank_cash_register(
            register_type VARCHAR(30),
            register VARCHAR(50) REFERENCES bank_cash_list(register),
            register_date DATE,
            register_number VARCHAR(30),
            balance DECIMAL,
            withdrawals DECIMAL,
            deposits DECIMAL
            )
            '''
            self.sql_execute(create_table_bank_cash_register)

            create_table_customers = '''
            CREATE TABLE customers(
            cust_id SERIAL UNIQUE NOT NULL,
            cust_name VARCHAR(50) NOT NULL,
            tax_id_num VARCHAR(50) NOT NULL,
            street VARCHAR(50) NOT NULL,
            street_num VARCHAR(50) NOT NULL,
            zip_code VARCHAR(50),
            city VARCHAR(50) NOT NULL,
            country VARCHAR(50) NOT NULL,
            country_code VARCHAR(50) NOT NULL,
            email VARCHAR(250),
            phone VARCHAR(100),
            bank_accounts VARCHAR
            )
            '''
            self.sql_execute(create_table_customers)

            create_table_document_numbers = '''
            CREATE TABLE document_numbers(
            doc_name VARCHAR(100) NOT NULL,
            doc_num INTEGER NOT NULL,
            doc_month INTEGER NOT NULL,
            doc_year INTEGER NOT NULL
            )
            '''
            self.sql_execute(create_table_document_numbers)

            create_table_invoice_settings = '''
            CREATE TABLE invoice_settings(
            invoice_type VARCHAR(100) NOT NULL UNIQUE,
            inv_type_short VARCHAR(50) NOT NULL UNIQUE,
            cust_account_num VARCHAR(30) REFERENCES chart_of_accounts(account_num) 
            )
            '''
            self.sql_execute(create_table_invoice_settings)

            insert_into_invoice_settings = '''
            INSERT INTO invoice_settings(invoice_type, inv_type_short)
            VALUES
            ('Service Sales Invoice', 'sale service'),
            ('Cost Purchase Invoice', 'purchase costs')
            '''
            self.sql_execute(insert_into_invoice_settings)

            create_table_vat_rates = '''
            CREATE TABLE vat_rates(
            vat_id VARCHAR(30) PRIMARY KEY,
            vat_rate INTEGER NOT NULL,
            sales_account_num VARCHAR(30) REFERENCES chart_of_accounts(account_num) NOT NULL,
            purchase_account_num VARCHAR(30) REFERENCES chart_of_accounts(account_num) NOT NULL
            )
            '''
            self.sql_execute(create_table_vat_rates)

            create_table_invoice_indexes = '''
            CREATE TABLE invoice_indexes(
            inv_index_id VARCHAR(50) PRIMARY KEY,
            inv_index_description VARCHAR(250) NOT NULL,
            sales_account_num VARCHAR(30) REFERENCES chart_of_accounts(account_num),
            purchase_account_num VARCHAR(30) REFERENCES chart_of_accounts(account_num),
            vat_id VARCHAR(30) REFERENCES vat_rates(vat_id),
            vat_rate INTEGER
            )
            '''
            self.sql_execute(create_table_invoice_indexes)

            create_table_journal = '''
            CREATE TABLE journal(
            no_journal BIGSERIAL UNIQUE NOT NULL,
            journal_entry_date TIMESTAMP DEFAULT NOW() NOT NULL,
            doc_type VARCHAR(30) NOT NULL,
            doc_date DATE NOT NULL,
            description VARCHAR(250) NOT NULL,
            dt_account_num VARCHAR(30) REFERENCES chart_of_accounts(account_num),
            ct_account_num VARCHAR(30) REFERENCES chart_of_accounts(account_num),
            amount DECIMAL NOT NULL,
            cust_id INTEGER REFERENCES customers(cust_id),
            doc_number VARCHAR(100) NOT NULL,
            int_doc_number VARCHAR(100) NOT NULL,
            vat_id VARCHAR(30) REFERENCES vat_rates(vat_id),
            vat_date DATE,
            status VARCHAR(30),
            inv_index_id VARCHAR(50) REFERENCES invoice_indexes(inv_index_id),
            index_vat_value DECIMAL,
            inv_due_date DATE,
            inv_payment_method VARCHAR(30),
            cor_orig_entry_date TIMESTAMP,
            cor_orig_doc_number VARCHAR(100),
            cor_reason VARCHAR(100),
            cor_orig_position INTEGER,
            settlement VARCHAR
            )
            '''
            self.sql_execute(create_table_journal)

            self.master.destroy()
            tkinter.messagebox.showinfo(title="Success", message="A new company has been created!")

    def sql_execute(self, sql):
        """Create connection to sql database, execute command"""
        conn = None
        cur = None

        try:
            conn = psycopg2.connect(
                host=sql_parameters.hostname,
                dbname=self.database_name_entry.get(),
                user=sql_parameters.username,
                password=sql_parameters.pwd,
                port=sql_parameters.port_id
            )

            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(sql)

        except Exception as error:
            if str(error) == 'no results to fetch':
                pass
            else:
                print(error)
                tkinter.messagebox.showerror(title="ERROR", message=str(error))

        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                conn.close()
