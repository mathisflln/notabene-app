# main.py
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from database.db_manager import DatabaseManager
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    app.setApplicationName("GestionProf")
    app.setOrganizationName("MonApp")
    
    db = DatabaseManager("nota.db")
    db.connect()
    
    window = MainWindow()
    window.show()
    
    exit_code = app.exec()
    
    db.close()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()