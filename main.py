from PySide6.QtWidgets import QApplication
from API.main_window import MainWindow
import sys

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(800, 600)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    