import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from monitor import Monitor
import pandas as pd

mymon=Monitor(only_app_features=True)
df=mymon.get_dataframe(samples=None)

numeric_df = df.select_dtypes(include='number')
rtt_cols = ["app_rtt_ms_MQTT", "app_rtt_ms_video"]
summary_rtt = pd.DataFrame({
    "mean": df[rtt_cols].mean(),
    "std": df[rtt_cols].std(),
    "min": df[rtt_cols].min(),
    "25%": df[rtt_cols].quantile(0.25),
    "median": df[rtt_cols].median(),
    "75%": df[rtt_cols].quantile(0.75),
    "max": df[rtt_cols].max(),
    "cv": df[rtt_cols].std() / df[rtt_cols].mean()
})

summary_rtt.index = ["MQTT app", "Video app"]
summary_rtt = summary_rtt.round(3)  # optional rounding for readability
print("\n=== Enhanced RTT Summary ===")
print(summary_rtt)

# Create experiment index
df["index"] = range(len(df))

# Convert index to hours (each experiment ≈ 0.5 min)
df["time_mins"] = df["index"] * 0.5

# --- Plot ---
plt.figure(figsize=(12,6))

# MQTT curve
plt.plot(df["time_mins"], df["app_rtt_ms_MQTT"],
         label="MQTT app", color="tab:blue", linewidth=2)

# Video curve
plt.plot(df["time_mins"], df["app_rtt_ms_video"],
         label="Video app", color="tab:orange", linewidth=2)

# --- Academic style formatting ---
plt.xlabel("Time (minutes)", fontsize=32, fontweight="bold")
plt.ylabel("RTT (ms)", fontsize=26, fontweight="bold")
plt.xticks(fontsize=26, fontweight="bold")
plt.yticks(fontsize=26, fontweight="bold")
plt.grid(True, which="major", linestyle="--", linewidth=0.9, alpha=0.6)
plt.grid(True, which="minor", linestyle="-.", linewidth=0.7, alpha=0.4)
plt.legend(fontsize=20, frameon=True, loc="best")
plt.tight_layout()

# Save & show
plt.savefig("app_rtt_vs_time.png", dpi=300)
plt.show()