import tkinter
from tkinter import ttk, messagebox
import journal_voucher
import sqlcommand


class OpenNewYear(tkinter.Toplevel):

    def __init__(self, parent):
        """New window with open new year settings"""
        super().__init__(parent)

        self.title("Open new year")
        self.resizable(False, False)

        # Tree frame
        self.tree_frame = tkinter.Frame(self)
        self.tree_frame.grid(column=0, row=0)

        self.open_year_treeview()

        # Options frame
        self.options_frame = tkinter.Frame(self)
        self.options_frame.grid(column=1, row=0, sticky='n')

        self.open_new_year_button = tkinter.Button(self.options_frame, text="Open new year", width=18,
                                                   command=self.open_new_year_button_command)
        self.open_new_year_button.grid(column=0, row=0)
        self.opening_balance_button = tkinter.Button(self.options_frame, text="Opening balance", width=18,
                                                     command=self.opening_balance_button_command)
        self.opening_balance_button.grid(column=0, row=1)

    def open_year_treeview(self):
        """Create tree with opened years"""
        sql_command = f"SELECT doc_year AS year FROM document_numbers GROUP BY doc_year ORDER BY doc_year DESC"

        conn = sqlcommand.SqlCommand()
        execute = conn.sql_execute(sql_command)

        column_names = execute['column_names']
        self.open_year_tree = ttk.Treeview(self.tree_frame, columns=column_names, show='headings', height=10,
                                           selectmode='browse')
        column = 0
        for _ in column_names:
            self.open_year_tree.heading(column_names[column], text=column_names[column])
            column += 1

        self.open_year_tree.grid(column=0, row=0)

        self.records = execute['records']
        record = 0
        for _ in self.records:
            self.open_year_tree.insert('', tkinter.END, values=self.records[record])
            record += 1

    def selected_year(self):
        """Take selected year"""
        selected = self.open_year_tree.focus()
        self.selected_y = self.open_year_tree.item(selected).get('values')
        return self.selected_y

    def open_new_year_button_command(self):
        """Open new window to create new year"""
        self.create_new_year_window = tkinter.Toplevel(padx=10, pady=10)
        self.create_new_year_window.title("Open new year")
        self.create_new_year_window.grab_set()
        self.create_new_year_window.resizable(False, False)

        # Inputs
        new_year_label = tkinter.Label(self.create_new_year_window, text="Year")
        new_year_label.grid(column=0, row=0)
        self.new_year_entry = tkinter.Entry(self.create_new_year_window, width=20)
        self.new_year_entry.grid(column=1, row=0)
        create_new_year_button = tkinter.Button(self.create_new_year_window, text="Open new year",
                                                command=self.open_new_year)
        create_new_year_button.grid(column=2, row=0)

    def open_new_year(self):
        """Add new year in SQL database, create table with document numbers"""
        new_year = self.new_year_entry.get()
        if new_year.isdigit():
            answer = tkinter.messagebox.askyesno(title='WARNING', message=f'Open {new_year} year?',
                                                 parent=self.create_new_year_window)
            if answer:
                if (int(new_year),) in self.records:
                    tkinter.messagebox.showerror(title="ERROR", message=f"{new_year} year is already opened",
                                                 parent=self.create_new_year_window)
                else:
                    sql_insert = "INSERT INTO document_numbers (doc_name, doc_num, doc_month, doc_year) VALUES "
                    documents = ['Journal voucher', 'Service Sales Invoice', '[COR] Service Sales Invoice',
                                 'Cost Purchase Invoice', '[COR] Cost Purchase Invoice']
                    insert_string_list = []
                    for doc in documents:
                        for month in range(12):
                            insert_string = f"('{doc}', 1, {month + 1}, {new_year}), \n"
                            insert_string_list.append(insert_string)

                    for item in insert_string_list:
                        sql_insert += item

                    sql_command = sql_insert[:-3]

                    # Connect to sql database to add new year
                    conn = sqlcommand.SqlCommand()
                    conn.sql_execute(sql_command)

                    self.refresh_open_year_tree()
                    self.create_new_year_window.destroy()
        else:
            tkinter.messagebox.showerror(title='ERROR', message="Only digits are allowed",
                                         parent=self.create_new_year_window)

    def opening_balance_button_command(self):
        """Open window with opening balance to edit"""
        if self.selected_year() == '':
            pass
        else:
            sql_command = f"SELECT doc_type, doc_date, int_doc_number FROM journal " \
                          f"WHERE doc_type='Opening balance' " \
                          f"AND EXTRACT(YEAR FROM doc_date) = {self.selected_year()[0]}"
            conn = sqlcommand.SqlCommand()
            execute = conn.sql_execute(sql_command)
            records = execute['records']
            if records == []:
                open_balance = journal_voucher.JournalVoucher(self, 'Opening balance')
                open_balance.doc_date_entry.set_date(f"01-01-{self.selected_year()[0]}")
                open_balance.doc_date_entry.config(state='disabled')
                open_balance.vat_date_entry.config(state='disabled')
            else:
                doc_type = records[0][0]
                doc_date = records[0][1]
                int_doc_number = records[0][2]

                open_balance = journal_voucher.EditJournalVoucher(self, doc_type, doc_type, doc_date, int_doc_number)
                open_balance.doc_date_entry.set_date(f"01-01-{self.selected_year()[0]}")
                open_balance.doc_date_entry.config(state='disabled')
                open_balance.vat_date_entry.config(state='disabled')

    def refresh_open_year_tree(self):
        """Refresh customer tree"""
        self.open_year_tree.delete(*self.open_year_tree.get_children())
        self.open_year_treeview()
