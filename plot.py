import matplotlib
import matplotlib.pyplot as plt
import pandas as pd


matplotlib.use("TkAgg")


def plot_dataset(dataset):
    df = pd.DataFrame(dataset)

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')

    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(12, 10), sharex=True)
    fig.suptitle('Time Series of Individual Parameters')

    axes[0].plot(df['Timestamp'], df['CPU'], label='CPU', marker='o', linestyle='-')
    axes[0].set_ylabel('CPU Usage (%)')
    axes[0].legend()
    axes[0].grid(True)

    axes[1].plot(df['Timestamp'], df['Memory'], label='Memory', marker='o', linestyle='-')
    axes[1].set_ylabel('Memory Usage (%)')
    axes[1].legend()
    axes[1].grid(True)

    axes[2].plot(df['Timestamp'], df['Network'], label='Network', marker='o', linestyle='-')
    axes[2].set_ylabel('Network Usage (units)')
    axes[2].set_xlabel('Timestamp')
    axes[2].legend()
    axes[2].grid(True)

    plt.tight_layout(rect=(0.0, 0.03, 1.0, 0.95))
    plt.show()