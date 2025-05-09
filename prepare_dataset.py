import csv


path = "datasets/workload_dataset/dataset.csv"


data = []


with open(path, "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter=";")
    headers = next(reader)
    indexes = []
    for i in range(len(headers)):
        if headers[i].lower() in ("timestamp", "cpu usage", "memory usage", "network received", "network transmitted"):
            indexes.append(i)

    data.append([headers[i] for i in indexes])

    for row in reader:
        data.append([row[i] for i in indexes])


with open("datasets/workload_dataset/workload.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=",")
    writer.writerows(data)