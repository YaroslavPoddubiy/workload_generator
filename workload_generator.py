import json
import numpy as np
import csv
from datetime import datetime
import plot
import db


class MarkovChain:
    def __init__(self, states=4):
        self.__states = states
        self.__transition_matrix = {
            "CPU": np.zeros((states, states)),
            "RAM": np.zeros((states, states)),
            "CHANNEL": np.zeros((states, states)),
        }
        self.__timeseries = [{
            "Date": [],
            "Time": [],
            "CPU": [],
            "RAM": [],
            "CHANNEL": [],
        }]
        self.__current_states = {'CPU': 0, 'RAM': 0, 'CHANNEL': 0}
        self.__is_configured = False
        self.__config_id = 0

    @property
    def transition_matrix(self):
        return self.__transition_matrix

    def set_config(self):
        try:
            self.load_config()
        except (FileNotFoundError, json.decoder.JSONDecodeError, ValueError):
            self.configure()

    def first_state(self, key):
        states_probabilities_sum = [0 for _ in range(self.__states)]
        for i in range(self.__states):
            for j in range(self.__states):
                states_probabilities_sum[j] += self.__transition_matrix[key][i][j]
        return states_probabilities_sum.index(max(states_probabilities_sum))

    @staticmethod
    def prepare_count_matrix(transition_count_matrix):
        for key in transition_count_matrix:
            for i in range(len(transition_count_matrix[key])):
                for j in range(len(transition_count_matrix[key][i])):
                    if transition_count_matrix[key][i][j] == 0:
                        transition_count_matrix[key][i][j] = 1

    def get_state_from_value(self, value):
        for i in range(1, self.__states + 1):
            if value <= i * (100 / self.__states):
                return i - 1

    def count_transitions(self, dataset):
        transition_count = {
            'CPU': [[0 for _ in range(self.__states)] for _ in range(self.__states)],
            'RAM': [[0 for _ in range(self.__states)] for _ in range(self.__states)],
            'CHANNEL': [[0 for _ in range(self.__states)] for _ in range(self.__states)],
        }

        current_states = {'CPU': self.get_state_from_value(dataset['CPU'][0]),
                          'RAM': self.get_state_from_value(dataset['RAM'][0]),
                          'CHANNEL': self.get_state_from_value(dataset['CHANNEL'][0])}

        for i in range(1, len(dataset['Date'])):
            next_cpu_state = self.get_state_from_value(dataset['CPU'][i])
            transition_count['CPU'][current_states['CPU']][next_cpu_state] += 1
            current_states['CPU'] = next_cpu_state

            next_ram_state = self.get_state_from_value(dataset['RAM'][i])
            transition_count['RAM'][current_states['RAM']][next_ram_state] += 1
            current_states['RAM'] = next_ram_state

            next_network_state = self.get_state_from_value(dataset['CHANNEL'][i])
            transition_count['CHANNEL'][current_states['CHANNEL']][next_network_state] += 1
            current_states['CHANNEL'] = next_network_state

        return transition_count

    def create_transition_matrix(self, transition_count):
        for key in transition_count:
            for i in range(len(transition_count[key])):
                self.prepare_count_matrix(transition_count)
                state_count_sum = sum(transition_count[key][i])
                multiplier = 1 / state_count_sum
                for j in range(len(transition_count[key][i]) - 1):
                    self.__transition_matrix[key][i][j] = multiplier * transition_count[key][i][j]
                self.__transition_matrix[key][i][-1] = 1 - sum(self.__transition_matrix[key][i])

    def configure(self, name="timeseries.csv"):
        if name not in db.get_datasets_names():
            raise FileNotFoundError("Такого датасету не існує")
        transition_matrix = db.get_config_for_dataset(name, self.__states)
        if transition_matrix:
            self.__transition_matrix = transition_matrix
            self.__is_configured = True
            return
        dataset = db.get_dataset_by_name(name)
        transition_count = self.count_transitions(dataset)

        self.create_transition_matrix(transition_count)

        self.__is_configured = True
        self.save_config(name)

    @staticmethod
    def prepare_config_to_json(transition_matrix: dict):
        json_transition_matrix = transition_matrix.copy()
        for key in transition_matrix:
            json_transition_matrix[key] = transition_matrix[key].tolist()
        return json_transition_matrix

    def set_states(self, states):
        if not isinstance(states, int):
            raise TypeError("states must be an integer")
        if states < 1 or states > 20:
            raise ValueError("states must be between 1 and 20")
        self.__states = states
        self.__transition_matrix = {
            "CPU": np.zeros((states, states)),
            "RAM": np.zeros((states, states)),
            "CHANNEL": np.zeros((states, states)),
        }

    def save_config(self, dataset_path):
        db.save_auto_config(self.__transition_matrix, dataset_path)

    def load_config(self, path="config.json"):
        transition_matrix = db.get_config_by_name(path)
        if len(transition_matrix['CPU']) != self.__states:
            raise ValueError(f"Кількість станів навантаження в конфігураційому файлі ({len(transition_matrix['CPU'])})"
                             f" не збігається з заданою кількістю станів ({self.__states})")
        self.__transition_matrix = transition_matrix
        self.__is_configured = True

    def __next_value(self, current_state, component):
        next_state = np.random.choice(self.__states, p=self.__transition_matrix[component][current_state])
        self.__current_states[component] = next_state
        bottom_state_value = int(100 / self.__states) * next_state
        top_state_value = int(100 / self.__states) * (next_state + 1)
        return np.random.randint(bottom_state_value, top_state_value)

    def __generate_timeseries(self, from_timestamp, to_timestamp, step=1000):
        timeseries = {"Date": [],
                      "Time": [],
                      "CPU": [],
                      "RAM": [],
                      "CHANNEL": []}
        self.__current_states = {'CPU': self.first_state('CPU'),
                                 'RAM': self.first_state('RAM'),
                                 'CHANNEL': self.first_state('CHANNEL')}

        for timestamp in range(from_timestamp, to_timestamp + 1, step):
            timeseries['Date'].append(datetime.fromtimestamp(timestamp).date())
            timeseries['Time'].append(datetime.fromtimestamp(timestamp).time())

            timeseries['CPU'].append(self.__next_value(self.__current_states['CPU'], 'CPU'))
            timeseries['RAM'].append(self.__next_value(self.__current_states['RAM'], 'RAM'))
            timeseries['CHANNEL'].append(self.__next_value(self.__current_states['CHANNEL'], 'CHANNEL'))

        return timeseries

    def generate(self, from_timestamp, to_timestamp, step=1000, count=1):
        self.__timeseries = []
        if not self.__is_configured:
            raise ValueError("Потрібно налаштувати матрицю переходів")
        if (to_timestamp - from_timestamp) / step < 100:
            raise ValueError('Кількість генерованих значень повинна бути більшою за 100\n'
                             'Спробуйте збільшити інтервал генерування, або зменшити часовий крок')
        if (to_timestamp - from_timestamp) / step > 100000:
            raise ValueError('Кількість генерованих значень не повинна перевищувати 100 000\n'
                             'Спробуйте зменшити інтервал генерування, або збільшити часовий крок')
        for i in range(count):
            self.__timeseries.append(self.__generate_timeseries(from_timestamp, to_timestamp, step))


        return self.__timeseries.copy()

    def save_to_db(self, group_name):
        names = db.get_datasets_names()
        group_names = []
        for name in names:
            last_slash_index = name.rfind("/")
            if last_slash_index == -1:
                group_names.append(name)
            else:
                group_names.append(name[:last_slash_index])
        if group_name in group_names:
            raise ValueError('Група мікросервісів з такою назвою вже існує')
        db.save_timeseries(self.__timeseries, group_name)

    def save_file(self, directory='timeseries'):
        for num, timeseries in enumerate(self.__timeseries):
            with open(f'{directory}/{num + 1}.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Time', 'CPU', 'RAM', 'CHANNEL'])
                for i in range(0, len(timeseries['Date'])):
                    writer.writerow([timeseries['Date'][i], timeseries['Time'][i], timeseries['CPU'][i], timeseries['RAM'][i], timeseries['CHANNEL'][i]])

    def show_plot(self, index):
        if index < 0 or index >= len(self.__timeseries):
            raise IndexError("Index out of range")
        dataset = self.__timeseries[index]
        plot.plot_dataset(dataset)
