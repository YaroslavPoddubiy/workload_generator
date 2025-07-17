import os
import PyQt5
from PyQt5.QtGui import QCloseEvent
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QWidget, QVBoxLayout, QTabWidget, \
    QTableWidget, QTableWidgetItem, QLabel
from PyQt5 import QtCore
import db
import workload_generator
import json
from datetime import datetime
import load_data
import plot



class TransitionMatrixWindow(QWidget):
    def __init__(self, matrix_data):
        super().__init__()
        self.setWindowTitle("Матриці переходів")
        self.resize(600, 400)

        layout = QVBoxLayout()
        tabs = QTabWidget()

        for label, matrix in matrix_data.items():
            tab = QWidget()
            tab_layout = QVBoxLayout()

            table = QTableWidget()
            num_rows = len(matrix)
            num_cols = len(matrix[0]) if num_rows else 0

            table.setRowCount(num_rows)
            table.setColumnCount(num_cols)

            for i in range(num_rows):
                for j in range(num_cols):
                    item = QTableWidgetItem(f"{matrix[i][j]:.2f}")
                    item.setTextAlignment(PyQt5.QtCore.Qt.AlignCenter)
                    table.setItem(i, j, item)

            tab_layout.addWidget(QLabel(f"Матриця переходів для {label}:"))
            tab_layout.addWidget(table)
            tab.setLayout(tab_layout)
            tabs.addTab(tab, label)

        layout.addWidget(tabs)
        self.setLayout(layout)


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.__workload_generator = workload_generator.MarkovChain()
        self.__dataset_path = 'datasets/workload_dataset/workload.csv'
        self.__config_path = 'middle_config.json'
        self.__configure_mode = 'config'
        self.__transition_matrix_window = None
        self.setup()

    def setup(self):
        loadUi("layout/MainWindow.ui", self)
        self.chooseDatasetRadioButton.toggled.connect(lambda: self.__set_configure_mode("dataset"))
        self.addDatasetButton.clicked.connect(lambda : self.debug(self.choose_dataset))
        self.chooseConfigRadioButton.toggled.connect(lambda: self.__set_configure_mode("config"))
        self.addConfigButton.clicked.connect(lambda : self.debug(self.choose_config))
        self.generateButton.clicked.connect(lambda: self.debug(self.generate))
        (self.plotButton.clicked.connect(
            lambda: self.__workload_generator.show_plot(self.microserviceNumberComboBox.currentIndex()))
        )
        self.startDateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        self.endDateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(3600))
        self.startDateTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.endDateTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.actionSave.triggered.connect(lambda: self.debug(self.save_dataset))
        self.saveTimeseriesToDBButton.clicked.connect(lambda: self.debug(self.save_timeseries_to_db))
        self.plotDatasetButton.clicked.connect(lambda: self.debug(self.plot_dataset))
        self.chooseDatasetComboBox.addItems(db.get_datasets_names())
        self.chooseConfigComboBox.addItems(db.get_manual_configs_names())
        self.showTransitionMatrixButton.clicked.connect(lambda: self.debug(self.show_transition_matrix))
        self.load_config()

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

    def plot_dataset(self):
        if self.chooseDatasetComboBox.currentText():
            plot.plot_dataset(db.get_dataset_by_name(self.chooseDatasetComboBox.currentText()))

    def load_config(self):
        try:
            with open('ui_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'configMode' in config:
                    if config['configMode'] in ('dataset', 'config'):
                        self.__configure_mode = config['configMode']
                    if config['configMode'] == 'config':
                        self.chooseConfigRadioButton.setChecked(True)
                        self.chooseDatasetRadioButton.setChecked(False)
                    elif config['configMode'] == 'dataset':
                        self.chooseConfigRadioButton.setChecked(False)
                        self.chooseDatasetRadioButton.setChecked(True)
                if 'statesSpinBox' in config:
                    self.statesSpinBox.setValue(int(config['statesSpinBox']))
                if 'chooseConfigComboBox' in config:
                    self.chooseConfigComboBox.setCurrentText(config['chooseConfigComboBox'])
                if 'chooseDatasetComboBox' in config:
                    self.chooseDatasetComboBox.setCurrentText(config['chooseDatasetComboBox'])
                if 'stepSpinBox' in config:
                    self.stepSpinBox.setValue(int(config['stepSpinBox']))
                if 'microservicesCountSpinBox' in config:
                    self.microservicesCountSpinBox.setValue(int(config['microservicesCountSpinBox']))
        except Exception as ex:
            pass

    def save_config(self):
        config = {
            'configMode': 'config' if self.__configure_mode == 'config' else 'dataset',
            "statesSpinBox": self.statesSpinBox.value(),
            "chooseConfigComboBox": self.chooseConfigComboBox.currentText(),
            "chooseDatasetComboBox": self.chooseDatasetComboBox.currentText(),
            "stepSpinBox": self.stepSpinBox.value(),
            "microservicesCountSpinBox": self.microservicesCountSpinBox.value(),
        }
        with open('ui_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False)

    def config_from_dataset(self):
        self.__workload_generator.configure(self.chooseDatasetComboBox.currentText())

    def generate(self):
        self.__workload_generator.set_states(self.statesSpinBox.value())
        if self.__configure_mode == 'config':
            self.__workload_generator.load_config(self.chooseConfigComboBox.currentText())
        else:
            self.config_from_dataset()

        from_timestamp = int(datetime.strptime(self.startDateTimeEdit.dateTime().toString(self.startDateTimeEdit.displayFormat()), "%Y-%m-%d %H:%M:%S").timestamp())
        to_timestamp = int(datetime.strptime(self.endDateTimeEdit.dateTime().toString(self.endDateTimeEdit.displayFormat()), "%Y-%m-%d %H:%M:%S").timestamp())
        self.__workload_generator.generate(from_timestamp, to_timestamp, self.stepSpinBox.value(), self.microservicesCountSpinBox.value())

        msg = QMessageBox()
        msg.setText("Часовий ряд згенеровано успішно!")
        msg.exec_()

        self.plotButton.setEnabled(True)
        self.saveTimeseriesToDBButton.setEnabled(True)
        self.showTransitionMatrixButton.setEnabled(True)
        self.microserviceNumberComboBox.clear()
        self.microserviceNumberComboBox.addItems(list(str(i) for i in range(1, self.microservicesCountSpinBox.value() + 1)))

    def choose_dataset(self):
        fname = QFileDialog(self).getOpenFileName(self, 'Open file',
                                                  os.path.dirname(os.path.abspath(__file__)), "CSV files (*.csv)")
        if fname[0]:
            dataset = load_data.load_dataset(fname[0])
            db.save_dataset(dataset, fname[0])
            self.chooseDatasetComboBox.addItem(fname[0])
            self.chooseDatasetComboBox.setCurrentText(fname[0])
            self.__dataset_path = fname[0]

    def show_transition_matrix(self):
        transition_matrix = self.__workload_generator.transition_matrix
        self.__transition_matrix_window = TransitionMatrixWindow(transition_matrix)
        self.__transition_matrix_window.show()

    def choose_config(self):
        fname = QFileDialog(self).getOpenFileName(self, 'Open file',
                                                  os.path.dirname(os.path.abspath(__file__)), "JSON files (*.json)")
        if fname[0]:
            config = load_data.load_config(fname[0])
            db.save_manual_config(config, fname[0])
            self.chooseConfigComboBox.addItem(fname[0])
            self.chooseConfigComboBox.setCurrentText(fname[0])
            self.__config_path = fname[0]

    def save_timeseries_to_db(self):
        name = self.microservicesGroupNameLineEdit.text()
        if not name:
            raise ValueError("Вкажіть назву групи мікросервісів")

        self.__workload_generator.save_to_db(name)

        self.chooseDatasetComboBox.addItems(
            [f'{name}/{i + 1}' for i in range(self.microservicesCountSpinBox.value())])

        msg = QMessageBox()
        msg.setText("Часовий ряд збережено в базу даних!")
        msg.exec_()

    def save_dataset(self):
        options = QFileDialog.ShowDirsOnly
        fname = QFileDialog.getExistingDirectory(self, "Select Directory", "", options=options)
        if not fname:
            return
        self.__workload_generator.save_file(fname)

    def closeEvent(self, event: QCloseEvent):
        self.save_config()
        event.accept()
