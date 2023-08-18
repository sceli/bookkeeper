import tkinter
from tkinter import messagebox
import psycopg2
import sql_parameters


class SqlCommand:

    def sql_execute(self, sql):
        """Create connection to sql database, execute command and return records and column names"""
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
            cur.execute(sql)
            records = cur.fetchall()
            column_names = [desc[0] for desc in cur.description]

            return {'records': records, 'column_names': column_names}

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
