import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------
# Load CSV
# -----------------------------
my_csv = Path("test.csv")
df = pd.read_csv(my_csv)

# -----------------------------
# Preprocessing
# -----------------------------
df_sorted = df.sort_values(by=["camp_name", "repeat_id", "exp_id"]).reset_index(drop=True)
df_sorted.replace([np.inf, -np.inf], np.nan, inplace=True)
df_sorted.fillna(0, inplace=True)

# -----------------------------
# Convert delays from ns to ms
# -----------------------------
delay_ns_cols = [
    "owamp_owamp_delay_ns_dl", "owamp_owamp_delay_ns_ul",
    "twamp_rtt_ns", "twamp_fwd_delay_txrx_ns", "twamp_rev_delay_rxtx_ns",
    "udpping_client2server_ns", "udpping_server2client_ns", "udpping_rtt_ns"
]
for col in delay_ns_cols:
    df_sorted[col] = df_sorted[col] / 1e6

# -----------------------------
# Throughput conversion to Mbps
# -----------------------------
throughput_cols = [
    "iperf_tcp_dl_received_bps","iperf_tcp_dl_sent_bps",
    "iperf_tcp_ul_received_bps","iperf_tcp_ul_sent_bps",
    "iperf_udp_dl_bps","iperf_udp_ul_bps"
]
for col in throughput_cols:
    df_sorted[col] = df_sorted[col] / 1e6

# UDP DL adjustment
df_sorted["iperf_udp_dl_bps"] /= 7

# TCP retransmits percentage
TOTAL_PACKETS = 100_000
for col in ["iperf_tcp_dl_retransmits", "iperf_tcp_ul_retransmits"]:
    df_sorted[col] = df_sorted[col] / TOTAL_PACKETS * 100

# UDP DL loss adjustment
df_sorted["iperf_udp_dl_lost_percent"] /= 4

# -----------------------------
# Helper function to clip extreme values (1st–99th percentile)
# -----------------------------
def clip_percentiles(series):
    low, high = series.quantile(0.01), series.quantile(0.99)
    return series.clip(lower=low, upper=high)

# -----------------------------
# Styling parameters
# -----------------------------
BOX_LINEWIDTH = 2
WHISKER_LINEWIDTH = 2
CAP_LINEWIDTH = 2
LABEL_FONT = 23
TICKS_FONT = 23
LEGEND_FONT = 23

# -----------------------------
# Helper function for summary table
# -----------------------------
def summary_table(df, columns):
    data = {col: clip_percentiles(df[col]) for col in columns}
    table_df = pd.DataFrame(data)
    stats = pd.DataFrame({
        "Mean": table_df.mean(),
        "Std": table_df.std()
    })
    return stats.round(2)

# -----------------------------
# 1) RTTs Boxplot & Table
# -----------------------------
rtt_cols = ["icmp_avg_rtt_ms", "twamp_rtt_ns", "udpping_rtt_ns"]
rtt_df = pd.DataFrame({k: clip_percentiles(df_sorted[v]) for k, v in zip(["ICMP RTT","TWAMP RTT","UDP Ping RTT"], rtt_cols)})

plt.figure(figsize=(10,6))
sns.boxplot(data=rtt_df, whis=[0,100], showfliers=False,
            linewidth=BOX_LINEWIDTH, boxprops=dict(linewidth=BOX_LINEWIDTH),
            whiskerprops=dict(linewidth=WHISKER_LINEWIDTH), capprops=dict(linewidth=CAP_LINEWIDTH))
plt.ylabel("RTT (ms)", fontsize=LABEL_FONT, fontweight="bold")
plt.xticks(fontsize=TICKS_FONT, fontweight="bold")
plt.yticks(fontsize=TICKS_FONT, fontweight="bold")
plt.xlabel("", fontsize=LABEL_FONT, fontweight="bold")
plt.grid(True, linestyle="--", linewidth=1, alpha=0.6)
plt.tight_layout()
plt.savefig("aggregated_rtt_boxplot.png")
plt.show()

rtt_stats = summary_table(df_sorted, rtt_cols)
rtt_stats.index = ["ICMP RTT","TWAMP RTT","UDP Ping RTT"]
rtt_stats.to_csv("aggregated_rtt_stats.csv")
print("\n=== RTTs Summary ===")
print(rtt_stats)

# -----------------------------
# 2) Throughput Boxplot & Table
# -----------------------------
throughput_cols = ["iperf_tcp_dl_received_bps","iperf_tcp_ul_received_bps","iperf_udp_dl_bps","iperf_udp_ul_bps"]
throughput_df = pd.DataFrame({k: clip_percentiles(df_sorted[v]) for k, v in zip(["TCP DL","TCP UL","UDP DL","UDP UL"], throughput_cols)})

plt.figure(figsize=(10,6))
sns.boxplot(data=throughput_df, whis=[0,100], showfliers=False,
            linewidth=BOX_LINEWIDTH, boxprops=dict(linewidth=BOX_LINEWIDTH),
            whiskerprops=dict(linewidth=WHISKER_LINEWIDTH), capprops=dict(linewidth=CAP_LINEWIDTH))
plt.ylabel("Throughput (Mbps)", fontsize=LABEL_FONT, fontweight="bold")
plt.xticks(fontsize=TICKS_FONT, fontweight="bold")
plt.yticks(fontsize=TICKS_FONT, fontweight="bold")
plt.xlabel("", fontsize=LABEL_FONT, fontweight="bold")
plt.grid(True, linestyle="--", linewidth=1, alpha=0.6)
plt.tight_layout()
plt.savefig("aggregated_throughput_boxplot.png")
plt.show()

throughput_stats = summary_table(df_sorted, throughput_cols)
throughput_stats.index = ["TCP DL","TCP UL","UDP DL","UDP UL"]
throughput_stats.to_csv("aggregated_throughput_stats.csv")
print("\n=== Throughput Summary (Mbps) ===")
print(throughput_stats)

# -----------------------------
# 3) Packet Loss Boxplot & Table
# -----------------------------
loss_cols = ["icmp_packet_loss_0to1","iperf_udp_dl_lost_percent","iperf_udp_ul_lost_percent"]
loss_df = pd.DataFrame({k: clip_percentiles(df_sorted[v]) for k, v in zip(["ICMP Packet Loss","UDP DL Packet Loss","UDP UL Packet Loss"], loss_cols)})

plt.figure(figsize=(10,6))
sns.boxplot(data=loss_df, whis=[0,100], showfliers=False,
            linewidth=BOX_LINEWIDTH, boxprops=dict(linewidth=BOX_LINEWIDTH),
            whiskerprops=dict(linewidth=WHISKER_LINEWIDTH), capprops=dict(linewidth=CAP_LINEWIDTH))
plt.ylabel("Packet Loss (%)", fontsize=LABEL_FONT, fontweight="bold")
plt.xticks(fontsize=TICKS_FONT, fontweight="bold")
plt.yticks(fontsize=TICKS_FONT, fontweight="bold")
plt.xlabel("", fontsize=LABEL_FONT, fontweight="bold")
plt.grid(True, linestyle="--", linewidth=1, alpha=0.6)
plt.tight_layout()
plt.savefig("aggregated_packet_loss_boxplot.png")
plt.show()

loss_stats = summary_table(df_sorted, loss_cols)
loss_stats.index = ["ICMP Packet Loss","UDP DL Packet Loss","UDP UL Packet Loss"]
loss_stats.to_csv("aggregated_packet_loss_stats.csv")
print("\n=== Packet Loss Summary (%) ===")
print(loss_stats)

# -----------------------------
# 4) TCP Retransmits Boxplot & Table
# -----------------------------
retrans_cols = ["iperf_tcp_dl_retransmits","iperf_tcp_ul_retransmits"]
retrans_df = pd.DataFrame({k: clip_percentiles(df_sorted[v]) for k, v in zip(["TCP DL","TCP UL"], retrans_cols)})

plt.figure(figsize=(10,6))
sns.boxplot(data=retrans_df, whis=[0,100], showfliers=False,
            linewidth=BOX_LINEWIDTH, boxprops=dict(linewidth=BOX_LINEWIDTH),
            whiskerprops=dict(linewidth=WHISKER_LINEWIDTH), capprops=dict(linewidth=CAP_LINEWIDTH))
plt.ylabel("TCP Retransmits (%)", fontsize=LABEL_FONT, fontweight="bold")
plt.xticks(fontsize=TICKS_FONT, fontweight="bold")
plt.yticks(fontsize=TICKS_FONT, fontweight="bold")
plt.xlabel("", fontsize=LABEL_FONT, fontweight="bold")
plt.grid(True, linestyle="--", linewidth=1, alpha=0.6)
plt.tight_layout()
plt.savefig("aggregated_tcp_retransmits_boxplot.png")
plt.show()

retrans_stats = summary_table(df_sorted, retrans_cols)
retrans_stats.index = ["TCP DL","TCP UL"]
retrans_stats.to_csv("aggregated_tcp_retransmits_stats.csv")
print("\n=== TCP Retransmits Summary (%) ===")
print(retrans_stats)
