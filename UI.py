import sys
import os
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5 import QtCore
import workload_generator
import json
from datetime import datetime


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.__workload_generator = workload_generator.MarkovChain()
        self.__dataset_path = 'datasets/workload_dataset/workload.csv'
        self.__config_path = 'middle_config.json'
        self.__configure_mode = 'config'
        self.setup()

    def setup(self):
        loadUi("layout/MainWindow.ui", self)
        self.chooseDatasetRadioButton.toggled.connect(lambda: self.__set_configure_mode("dataset"))
        self.chooseDatasetButton.clicked.connect(lambda : self.debug(self.choose_dataset))
        self.chooseConfigRadioButton.toggled.connect(lambda: self.__set_configure_mode("config"))
        self.chooseConfigButton.clicked.connect(lambda : self.debug(self.choose_config))
        self.generateButton.clicked.connect(lambda: self.debug(self.generate))
        (self.plotButton.clicked.connect(
            lambda: self.__workload_generator.show_plot(self.microserviceNumberComboBox.currentIndex()))
        )
        self.startDateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        self.endDateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(3600))
        self.startDateTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.endDateTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.actionSave.triggered.connect(lambda: self.debug(self.save_dataset))

    @staticmethod
    def debug(function, *args):
        try:
            function(*args)
        except Exception as ex:
            msg = QMessageBox()
            msg.setText(str(ex))
            msg.exec_()

    def __set_dataset_path(self, dataset_path):
        self.__dataset_path = dataset_path

    def __set_configure_mode(self, mode: str):
        self.__configure_mode = mode

    def config_from_dataset(self):
        if not os.path.isfile("config.json"):
            self.__workload_generator.configure(self.__dataset_path)
        else:
            with open("config.json", "r", encoding='utf-8') as f:
                data = f.read()
                if data == "":
                    self.__workload_generator.configure(self.__dataset_path)
                else:
                    json_data = json.loads(data)
                    json_data = json_data["DatasetPath"]
                    if json_data != self.__dataset_path:
                        self.__workload_generator.configure(self.__dataset_path)
                    else:
                        try:
                            self.__workload_generator.load_config()
                        except Exception as ex:
                            self.__workload_generator.configure(self.__dataset_path)

    def generate(self):
        if self.__configure_mode == 'config':
            self.__workload_generator.load_config(self.__config_path)
        else:
            self.config_from_dataset()

        from_timestamp = int(datetime.strptime(self.startDateTimeEdit.dateTime().toString(self.startDateTimeEdit.displayFormat()), "%Y-%m-%d %H:%M:%S").timestamp())
        to_timestamp = int(datetime.strptime(self.endDateTimeEdit.dateTime().toString(self.endDateTimeEdit.displayFormat()), "%Y-%m-%d %H:%M:%S").timestamp())
        self.__workload_generator.generate(from_timestamp, to_timestamp, self.stepSpinBox.value(), self.microservicesCountSpinBox.value())

        msg = QMessageBox()
        msg.setText("Часовий ряд згенеровано успішно!")
        msg.exec_()

        self.plotButton.setEnabled(True)

        self.microserviceNumberComboBox.addItems(list(str(i) for i in range(1, self.microservicesCountSpinBox.value() + 1)))

    def choose_dataset(self):
        fname = QFileDialog(self).getOpenFileName(self, 'Open file',
                                                  os.path.dirname(os.path.abspath(__file__)), "CSV files (*.csv)")
        if fname[0]:
            self.chooseDatasetLineEdit.setText(fname[0])
            self.__dataset_path = fname[0]

    def choose_config(self):
        fname = QFileDialog(self).getOpenFileName(self, 'Open file',
                                                  os.path.dirname(os.path.abspath(__file__)), "JSON files (*.json)")
        if fname[0]:
            self.chooseDatasetLineEdit.setText(fname[0])
            self.__config_path = fname[0]

    def save_dataset(self):
        options = QFileDialog.ShowDirsOnly
        fname = QFileDialog.getExistingDirectory(self, "Select Directory", "", options=options)
        if not fname:
            return
        self.__workload_generator.save(fname)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()