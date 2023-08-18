import main_window
import sql_parameters


sql_parameters.database = 'test_comp'

if __name__ == "__main__":

    window = main_window.MainWindow()
    window.mainloop()
