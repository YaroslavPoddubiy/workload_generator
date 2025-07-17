from datetime import datetime, timedelta
import mysql.connector


connection = mysql.connector.connect(
    host='localhost',
    user='root',
    passwd='12345678',
    database='railway'
)


cursor = connection.cursor()


def setup():
    cursor.execute("CREATE TABLE IF NOT EXISTS raw_metrics ("
                       "id INTEGER AUTO_INCREMENT PRIMARY KEY,"
                       "service_name VARCHAR(255) NOT NULL,"
                       "metric_type ENUM('CPU', 'RAM', 'CHANNEL'),"
                       "date DATE NOT NULL,"
                       "time TIME NOT NULL,"
                       "value JSON NOT NULL,"
                       "UNIQUE (date, time, service_name, metric_type)"
                       ")")

    cursor.execute("CREATE TABLE IF NOT EXISTS Configurations ("
                       "id INTEGER NOT NULL,"
                       "states INTEGER NOT NULL,"
                       "is_auto_generated INTEGER NOT NULL DEFAULT 1,"
                       "name TEXT,"
                       "service_name VARCHAR(255),"
                       "from_state INTEGER NOT NULL,"
                       "to_state INTEGER NOT NULL,"
                       "CPU FLOAT NOT NULL,"
                       "RAM FLOAT NOT NULL,"
                       "CHANNEL FLOAT NOT NULL,"
                       "UNIQUE (id, from_state, to_state)"
                       ")")

    cursor.execute("CREATE TABLE IF NOT EXISTS time_steps ("
                   "service_name VARCHAR(255) NOT NULL,"
                   "step INTEGER NOT NULL"
                   ")")

    connection.commit()


def insert_auto_config(row):
    cursor.execute(
        "INSERT INTO Configurations(id, states, is_auto_generated, service_name, from_state, to_state, CPU, RAM, CHANNEL) "
        "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", tuple(row))
    connection.commit()


def save_auto_config(transition_matrix, dataset_name):
    states = len(transition_matrix['CPU'])
    config = {
        "States": states,
        "is_auto_generated": 1,
        "dataset_name": dataset_name,
        "MarkovChain": transition_matrix
    }
    index = cursor.execute("SELECT id FROM Configurations ORDER BY id DESC LIMIT 1")
    index = cursor.fetchone()
    if not index:
        index = 1
    else:
        index = index[0] + 1
    for i in range(config["States"]):
        for j in range(config["States"]):
            insert_auto_config((index, config["States"], config["is_auto_generated"], config["dataset_name"], i, j,
                                  transition_matrix['CPU'][i][j], transition_matrix['RAM'][i][j],
                                  transition_matrix['CHANNEL'][i][j]))


def insert_manual_config(row):
    cursor.execute(
        "INSERT INTO Configurations(id, states, is_auto_generated, name, from_state, to_state, CPU, RAM, CHANNEL) "
        "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", tuple(row))
    connection.commit()


def save_manual_config(config, name):
    config["is_auto_generated"] = 0
    config["name"] = name
    transition_matrix = config["MarkovChain"]
    cursor.execute("SELECT id FROM Configurations ORDER BY id DESC LIMIT 1")
    index = cursor.fetchone()
    if not index:
        index = 1
    else:
        index = index[0] + 1
    for i in range(config["States"]):
        for j in range(config["States"]):
            insert_manual_config((index, config["States"], config["is_auto_generated"], config["name"], i, j,
                                  transition_matrix['CPU'][i][j], transition_matrix['RAM'][i][j], transition_matrix['CHANNEL'][i][j]))


def save_dataset(dataset: dict, dataset_name: str):
    metrics = list(dataset.keys())
    metrics.remove('Date')
    metrics.remove('Time')

    for metric in metrics:
        cursor.execute(
            "INSERT INTO raw_metrics(service_name, metric_type, date, time, value) VALUES(%s, %s, %s, %s, %s)",
            (dataset_name, metric, dataset['Date'][0], dataset['Time'][0], str(dataset[metric])))

    first_datetime = datetime.combine(dataset['Date'][0], dataset['Time'][0])
    next_datetime = datetime.combine(dataset['Date'][1], dataset['Time'][1])
    step = (next_datetime - first_datetime).total_seconds()

    cursor.execute("INSERT INTO time_steps(service_name, step) VALUES(%s, %s)", (dataset_name, step))

    connection.commit()


def save_timeseries(timeseries, directory_name):
    for i in range(0, len(timeseries)):
        save_dataset(timeseries[i], directory_name + '/' + str(i + 1))


def get_datasets_names() -> list[str]:
    cursor.execute("SELECT DISTINCT service_name FROM raw_metrics")
    datasets_names = cursor.fetchall()
    datasets_names = [record[0] for record in datasets_names]
    return datasets_names


def get_manual_configs_names():
    cursor.execute("SELECT DISTINCT name FROM Configurations WHERE is_auto_generated=0 ORDER BY id ")
    configs_names = cursor.fetchall()
    configs_names = [record[0] for record in configs_names]
    return configs_names


def get_dataset_by_name(dataset_name: str):
    cursor.execute("SELECT date, time, metric_type, value FROM raw_metrics WHERE service_name = %s",
                   (dataset_name,))
    rows = cursor.fetchall()
    cursor.execute("SELECT step FROM time_steps WHERE service_name = %s", (dataset_name,))
    step = cursor.fetchone()
    if not step:
        step = 30
    else:
        step = step[0]
    prev_datetime = datetime.combine(rows[0][0], datetime.min.time()) + rows[0][1] - timedelta(0, step)
    dataset = {"Date": [], "Time": [], "CPU": [], "RAM": [], "CHANNEL": []}
    for row in rows:
        dataset[row[2]] = [float(value) for value in row[3][1:-1].split(',')]
    for i in range(len(dataset['CPU'])):
        date_time = prev_datetime + timedelta(0, step)
        if not (len(dataset['Date']) != 0 and date_time.date() == dataset['Date'][-1] and date_time.time() == dataset['Time'][-1]):
            dataset['Date'].append(date_time.date())
            dataset['Time'].append(date_time.time())
        prev_datetime = date_time
    return dataset


def get_config_by_id(index):
    cursor.execute("SELECT states, from_state, to_state, CPU, RAM, CHANNEL FROM Configurations WHERE id = %s", (index,))
    rows = cursor.fetchall()
    if not rows:
        return None
    states = rows[0][0]
    transition_matrix = {
        "CPU": [[0 for _ in range(states)] for _ in range(states)],
        "RAM": [[0 for _ in range(states)] for _ in range(states)],
        "CHANNEL": [[0 for _ in range(states)] for _ in range(states)]}
    for row in rows:
        transition_matrix['CPU'][int(row[1])][int(row[2])] = float(row[3])
        transition_matrix['RAM'][int(row[1])][int(row[2])] = float(row[4])
        transition_matrix['CHANNEL'][int(row[1])][int(row[2])] = float(row[5])
    return transition_matrix


def get_config_by_name(config_name: str):
    cursor.execute("SELECT id FROM Configurations WHERE name = %s LIMIT 1", (config_name,))
    index = cursor.fetchone()
    if not index:
        return None
    index = int(index[0])
    config = get_config_by_id(index)
    return config


def get_config_for_dataset(dataset_name: str, states: int):
    cursor.execute("SELECT id FROM Configurations WHERE service_name = %s AND states = %s LIMIT 1", (dataset_name, states))
    index = cursor.fetchone()
    if not index:
        return None
    config = get_config_by_id(int(index[0]))
    return config
