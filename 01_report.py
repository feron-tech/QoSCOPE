import json
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

import gparams

# 01 Physical Layer Analytics
jsonfile = Path(gparams._DB_DIR) / "phy.json"

# Friendly names for metrics (add RSSI and BER optionally)
METRIC_LABELS = {
    "qrsrp_prx": "RSRP (dBm)",
    "rsrq_prx": "RSRQ (dB)",
    "sinr_prx": "SINR (dB)",
    "rssi": "RSSI (dBm)",   # optional
    "ber": "BER (%)"         # optional
}

# Thresholds for benchmarks (same color as actual measurement)
THRESHOLDS = {
    "qrsrp_prx": -100,
    "rsrq_prx": -15,
    "sinr_prx": 0,
}

INVALID_VALUES = [-32768, None]

def load_phy_measurements(filepath):
    records = []
    with open(filepath, "r") as f:
        for line in f:
            try:
                rec = json.loads(line)
                records.append(rec)
            except json.JSONDecodeError:
                continue

    df = pd.DataFrame(records)

    def parse_val(x):
        try:
            vals = eval(x) if isinstance(x, str) and x.startswith('[') else [x]
            filtered = [float(v) for v in vals if v not in INVALID_VALUES]
            return filtered[0] if filtered else None
        except:
            return None

    for col in METRIC_LABELS.keys():
        if col in df.columns:
            df[col] = df[col].apply(parse_val)

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Compute relative time in hours from start
    start_time = df["timestamp"].min()
    df["rel_hours"] = (df["timestamp"] - start_time).dt.total_seconds() / 3600.0

    return df


def stability_table(df):
    stats = {}
    for col, label in METRIC_LABELS.items():
        if col in df.columns:
            series = df[col].dropna()
            if len(series) > 0:
                stats[label] = [
                    series.mean(),
                    series.std(),
                    series.quantile(0.25),
                    series.quantile(0.75),
                    series.quantile(0.99),
                ]

    table = pd.DataFrame(stats, index=["Average", "Std", "25%", "75%", "99%"]).T
    print("\n=== Updated PHY Layer Stability Table ===")
    print(table.round(2))
    return table


def plot_timeseries(df):
    plt.figure(figsize=(16, 8))

    for col, label in METRIC_LABELS.items():
        if col in df.columns:
            line, = plt.plot(
                df["rel_hours"] + 1,
                df[col],
                label=label,
                linewidth=2.5
            )
            color = line.get_color()

            if col in THRESHOLDS:
                plt.axhline(
                    THRESHOLDS[col],
                    color=color,
                    linestyle="--",
                    linewidth=2,
                    label=f"TH {label}"
                )

    plt.xlabel("Time (hours)", fontsize=26, fontweight="bold")
    plt.ylabel("Signal Quality (dB)", fontsize=26, fontweight="bold")
    plt.xticks(fontsize=22, fontweight="bold")
    plt.yticks(fontsize=22, fontweight="bold")

    plt.xlim(df["rel_hours"].min() + 1, df["rel_hours"].max() + 1)
    # Auto Y-axis limits with small margin
    y_min = df[list(METRIC_LABELS.keys())].min().min() - 5
    y_max = df[list(METRIC_LABELS.keys())].max().max() + 5
    plt.ylim(y_min, y_max)

    plt.legend(fontsize=18, frameon=True, loc='best', ncol=2)
    plt.grid(True, linestyle="--", linewidth=1, alpha=0.6)
    plt.tight_layout()
    plt.show()

    print("\nExplanation:")
    print("The figure shows PHY metrics (RSRP, RSRQ, SINR, optionally RSSI/BER) over time in hours.")
    print("Dashed lines indicate commercial benchmark thresholds, plotted in the same color as the corresponding metric.")
    print("Values consistently above thresholds indicate stable and high-quality 5G performance.")


if __name__ == "__main__":
    df = load_phy_measurements(jsonfile)
    stability_table(df)
    plot_timeseries(df)
