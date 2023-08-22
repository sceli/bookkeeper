import json
import tkinter
from tkinter import messagebox
import os


def read_config():
    """Open and read config file"""
    config_file = 'config_sql.json'

    if not os.path.exists(config_file):
        # Creating an empty dictionary with default empty values
        default_config = {
            "hostname": "",
            "username": "",
            "pwd": "",
            "port_id": ""
        }

        # Saving the dictionary as a JSON file
        with open(config_file, 'w') as file:
            json.dump(default_config, file, indent=4)

    # Reading the configuration from a file
    with open('config_sql.json', 'r') as file:
        config_data = json.load(file)
    return config_data


try:
    # Try to open config file
    config = read_config()

    hostname = config["hostname"]
    database = ''
    username = config["username"]
    pwd = config["pwd"]
    port_id = config["port_id"]

except Exception as e:
    # Show error if there was a problem opening the file
    tkinter.messagebox.showerror(title="ERROR", message="An error occurred while trying to open the config file")


class SqlConfigWindow(tkinter.Toplevel):

    def __init__(self, parent):
        """SQL config window"""
        super().__init__(parent)

        self.title("Database connection configure")
        self.config(padx=10, pady=10)
        self.resizable(False, False)

        # Entries
        self.hostname_label = tkinter.Label(self, text="Hostname", width=20)
        self.hostname_label.grid(column=0, row=0)
        self.hostname_entry = tkinter.Entry(self, width=30)
        self.hostname_entry.grid(column=1, row=0)

        self.username_label = tkinter.Label(self, text="Username")
        self.username_label.grid(column=0, row=1)
        self.username_entry = tkinter.Entry(self, width=30)
        self.username_entry.grid(column=1, row=1)

        self.password_label = tkinter.Label(self, text="Password")
        self.password_label.grid(column=0, row=2)
        self.password_entry = tkinter.Entry(self, width=30)
        self.password_entry.grid(column=1, row=2)

        self.port_id_label = tkinter.Label(self, text="Port ID")
        self.port_id_label.grid(column=0, row=3)
        self.port_id_entry = tkinter.Entry(self, width=30)
        self.port_id_entry.grid(column=1, row=3)

        self.save_button = tkinter.Button(self, text="Save", command=self.save_changes)
        self.save_button.grid(column=1, row=4)

        # Fill entries
        self.hostname_entry.insert('end', hostname)
        self.username_entry.insert('end', username)
        self.password_entry.insert('end', pwd)
        self.port_id_entry.insert('end', port_id)

    def save_changes(self):
        """Save changes in 'config_sql.json' file"""
        data = {'hostname': self.hostname_entry.get(), 'username': self.username_entry.get(),
                'pwd': self.password_entry.get(), 'port_id': self.port_id_entry.get()}

        with open('config_sql.json', 'w') as file:
            json.dump(data, file, indent=4)

        self.destroy()
        tkinter.messagebox.showinfo(title="INFO",
                                    message="Changes saved! "
                                            "The program must be restarted for the changes to take effect.")
        self.master.destroy()
