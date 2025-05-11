import csv


def load_dataset(path):
    dataset = {
            "Timestamp": [],
            "CPU": [],
            "Memory": [],
            "Network": [],
        }
    with open(path, "r", encoding='utf-8') as f:
        reader = csv.reader(f)
        first_row = next(reader)
        if len(first_row) != 4 or first_row[0] != "Timestamp" or first_row[1] != "CPU" or first_row[2] != "Memory" or first_row[3] != "Network":
            raise ValueError("Датасет повинен містити параметри: Timestamp, CPU, Memory, Network")
        for row in reader:
            dataset["Timestamp"].append(int(row[0]))
            dataset["CPU"].append(float(row[1]))
            dataset["Memory"].append(float(row[2]))
            dataset["Network"].append(float(row[3]))

    return dataset