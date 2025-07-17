import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime


matplotlib.use("TkAgg")


def plot_dataset(dataset):
    df = pd.DataFrame(dataset)

    df['Datetime'] = [datetime.combine(d, t) for d, t in zip(df["Date"], df["Time"])]
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(12, 10), sharex=True)
    fig.suptitle('Навантаження мікросервісу')

    axes[0].plot(df['Datetime'], df['CPU'], label='CPU', marker='o', linestyle='-', linewidth=0.5, markersize=3)
    axes[0].set_ylabel('CPU Usage (%)')
    axes[0].legend()
    axes[0].grid(True)

    axes[1].plot(df['Datetime'], df['RAM'], label='RAM', marker='o', linestyle='-', linewidth=0.5, markersize=3)
    axes[1].set_ylabel('RAM Usage (%)')
    axes[1].legend()
    axes[1].grid(True)

    axes[2].plot(df['Datetime'], df['CHANNEL'], label='CHANNEL', marker='o', linestyle='-', linewidth=0.5, markersize=3)
    axes[2].set_ylabel('CHANNEL Usage (%)')
    axes[2].set_xlabel('Datetime')
    axes[2].legend()
    axes[2].grid(True)

    plt.tight_layout(rect=(0.0, 0.03, 1.0, 0.95))
    plt.show()