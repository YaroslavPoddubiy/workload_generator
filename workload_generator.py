import json
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import os.path
import csv
from datetime import datetime


matplotlib.use("TkAgg")


class MarkovChain:
    def __init__(self, states=4):
        self.__states = states
        self.__transition_matrix = {
            "CPU": np.zeros((states, states)),
            "Memory": np.zeros((states, states)),
            "Network": np.zeros((states, states)),
        }
        self.__timeseries = [{
            "Timestamp": [],
            "CPU": [],
            "Memory": [],
            "Network": [],
        }]
        self.__current_state = 0
        self.__is_configured = False

    @property
    def current_state(self):
        return self.__current_state

    def next_state(self):
        pass

    def set_config(self):
        try:
            self.load_config()
        except (FileNotFoundError, json.decoder.JSONDecodeError, ValueError) as e:
            self.configure()

    @staticmethod
    def prepare_count_matrix(transition_count_matrix):
        for key in transition_count_matrix:
            for i in range(len(transition_count_matrix[key])):
                for j in range(len(transition_count_matrix[key][i])):
                    if transition_count_matrix[key][i][j] == 0:
                        transition_count_matrix[key][i][j] = 1

    def configure(self, path="timeseries.csv"):
        transition_count = {
            "CPU": [[0 for i in range(self.__states)] for j in range(self.__states)],
            "Memory": [[0 for i in range(self.__states)] for j in range(self.__states)],
            "Network": [[0 for i in range(self.__states)] for j in range(self.__states)],
        }
        with open(path, "r") as f:
            reader = csv.reader(f)
            reader.__next__()
            first_row = next(reader)
            current_states = {"CPU": 0, "Memory": 0, "Network": 0}

            for i in range(1, self.__states + 1):
                if float(first_row[1]) <= i * 20:
                    current_states["CPU"] = i - 1
            for i in range(1, self.__states + 1):
                if float(first_row[2]) <= i * 20:
                    current_states["Memory"] = i - 1
            for i in range(1, self.__states + 1):
                if float(first_row[3]) <= i * 20:
                    current_states["Network"] = i - 1

            for row in reader:
                for i in range(1, self.__states + 1):
                    if float(row[1]) <= i * 20:
                        transition_count["CPU"][current_states["CPU"]][i - 1] += 1
                        current_states["CPU"] = i - 1
                for i in range(1, self.__states + 1):
                    if float(row[2]) <= i * 20:
                        transition_count["Memory"][current_states["Memory"]][i - 1] += 1
                        current_states["Memory"] = i - 1
                for i in range(1, self.__states + 1):
                    if float(row[3]) <= i * 20:
                        transition_count["Network"][current_states["Network"]][i - 1] += 1
                        current_states["Network"] = i - 1

        for key in transition_count:
            for i in range(len(transition_count[key])):
                self.prepare_count_matrix(transition_count)
                state_count_sum = sum(transition_count[key][i])

                # якщо переходів з певного стану не відбувалося, ймовірності переходів в різні стани будуть однакові
                # if state_count_sum == 0:
                #     for j in range(len(transition_count[key][i])):
                #         self.__transition_matrix[key][i][j] = 1 / self.__states
                #     multiplier = 1 / self.__states
                # else:
                #     multiplier = 1 / state_count_sum
                multiplier = 1 / state_count_sum
                for j in range(len(transition_count[key][i]) - 1):
                    # якщо переходів з одного стану в певний інший не відбувалося, то ставимо мінімальну ймовірність
                    # if transition_count[key][i][j] == 0:
                    #     self.__transition_matrix[key][i][j] = 0.01
                    # else:
                    #     self.__transition_matrix[key][i][j] = multiplier * transition_count[key][i][j]
                    self.__transition_matrix[key][i][j] = multiplier * transition_count[key][i][j]
                self.__transition_matrix[key][i][-1] = 1 - sum(self.__transition_matrix[key][i])

        self.__is_configured = True
        self.save_config(path)

    @staticmethod
    def prepare_config_to_json(transition_matrix: dict):
        json_transition_matrix = transition_matrix.copy()
        for key in transition_matrix:
            json_transition_matrix[key] = transition_matrix[key].tolist()
        return json_transition_matrix

    def save_config(self, dataset_path):
        json_data = {"DatasetPath": dataset_path, "MarkovChain": self.prepare_config_to_json(self.__transition_matrix)}
        with open("config.json", "w", encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False)

    def config_is_correct(self, dataset):
        if len(dataset["CPU"]) != len(self.__transition_matrix["CPU"]) or \
                len(dataset["Memory"]) != len(self.__transition_matrix["Memory"]) or \
                len(dataset["Network"]) != len(self.__transition_matrix["Network"]):
            return False
        for i in range(len(dataset["CPU"])):
            if len(dataset["CPU"][i]) != len(self.__transition_matrix["CPU"][i]) or \
                    len(dataset["Memory"][i]) != len(self.__transition_matrix["Memory"][i]) or \
                    len(dataset["Network"][i]) != len(self.__transition_matrix["Network"][i]):
                return False
        for key in dataset:
            for state_probabilities in dataset[key]:
                if sum(state_probabilities) != 1:
                    return False
        return True

    def load_config(self, path="config.json"):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"No {path} file")
        with open(path, "r", encoding='UTF-8') as f:
            json_data = json.load(f)
            json_data = json_data["MarkovChain"]
            if not self.config_is_correct(json_data):
                raise ValueError("Invalid configuration")
            self.__transition_matrix = json_data
            self.__is_configured = True

    def __generate_timeseries(self, from_timestamp, to_timestamp, step=1000):
        first_state = np.random.randint(0, self.__states)
        steps = int((to_timestamp - from_timestamp) / step)
        timeseries = {"Timestamp": [from_timestamp], "CPU": [first_state], "Memory": [first_state],
                             "Network": [first_state]}
        current_states = (first_state, first_state, first_state)

        for i in range(1, steps):
            timeseries['Timestamp'].append(i * step + from_timestamp)

            next_cpu_state = np.random.choice(self.__states, p=self.__transition_matrix['CPU'][current_states[0]])
            timeseries['CPU'].append(
                np.random.randint(int(100 / self.__states) * next_cpu_state,
                                  int(100 / self.__states) * (next_cpu_state + 1)))

            next_memory_state = np.random.choice(self.__states, p=self.__transition_matrix['Memory'][current_states[0]])
            timeseries['Memory'].append(
                np.random.randint(int(100 / self.__states) * next_memory_state,
                                  int(100 / self.__states) * (next_memory_state + 1)))

            next_network_state = np.random.choice(self.__states,
                                                  p=self.__transition_matrix['Network'][current_states[0]])
            timeseries['Network'].append(
                np.random.randint(int(100 / self.__states) * next_network_state,
                                  int(100 / self.__states) * (next_network_state + 1)))

            current_states = (next_cpu_state, next_memory_state, next_network_state)
        return timeseries

    def generate(self, from_timestamp, to_timestamp, step=1000, count=1):
        self.__timeseries = []
        if not self.__is_configured:
            raise ValueError("Invalid configuration")
        for i in range(count):
            self.__timeseries.append(self.__generate_timeseries(from_timestamp, to_timestamp, step))
        return self.__timeseries.copy()

    def save(self, directory='timeseries'):
        for num, timeseries in enumerate(self.__timeseries):
            with open(f'{directory}/{num + 1}.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'CPU', 'Memory', 'Network'])
                for i in range(0, len(timeseries['Timestamp'])):
                    writer.writerow([timeseries['Timestamp'][i], timeseries['CPU'][i], timeseries['Memory'][i], timeseries['Network'][i]])

    def show_plot(self, index):
        # Create DataFrame
        if index < 0 or index >= len(self.__timeseries):
            raise IndexError("Index out of range")
        df = pd.DataFrame(self.__timeseries[index])

        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')

        # Create subplots
        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(12, 10), sharex=True)
        fig.suptitle('Time Series of Individual Parameters')

        # Plot CPU usage
        axes[0].plot(df['Timestamp'], df['CPU'], label='CPU', marker='o', linestyle='-')
        axes[0].set_ylabel('CPU Usage (%)')  # Adjust y-axis label
        axes[0].legend()
        axes[0].grid(True)

        # Plot Memory usage
        axes[1].plot(df['Timestamp'], df['Memory'], label='Memory', marker='o', linestyle='-')
        axes[1].set_ylabel('Memory Usage (%)')  # Adjust y-axis label
        axes[1].legend()
        axes[1].grid(True)

        # Plot Network usage
        axes[2].plot(df['Timestamp'], df['Network'], label='Network', marker='o', linestyle='-')
        axes[2].set_ylabel('Network Usage (units)')  # Adjust y-axis label
        axes[2].set_xlabel('Timestamp')
        axes[2].legend()
        axes[2].grid(True)
        # axes[2].tick_params(axis='x', rotation=45, ha='right')

        plt.tight_layout(rect=(0.0, 0.03, 1.0, 0.95))  # Adjust layout to prevent overlap and make space for suptitle
        plt.show()

    def __str__(self):
        return str(self.__transition_matrix)


class TimeSeriesModelling:
    def __init__(self):
        pass


class WorkloadGenerator:
    def __init__(self):
        self.__markov_chain = MarkovChain()
        self.__time_series_modelling = TimeSeriesModelling()


def main():
    markov_chain = MarkovChain()
    print(markov_chain)
    markov_chain.generate(int(datetime.now().timestamp()), int(datetime.now().timestamp()) + 3600, 10)
    markov_chain.show_plot()


if __name__ == '__main__':
    main()
