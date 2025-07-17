import sys

from PyQt5.QtWidgets import QApplication

from UI import MainWindow
import db


def main():
    db.setup()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
