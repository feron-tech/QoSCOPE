import pandas as pd
import json
from pathlib import Path
from functools import reduce
import gparams
import os

class Monitor:
    def __init__(self, data_dir: str=gparams._DB_DIR, remove_app_features: bool = False, only_app_features: bool = False):
        self.data_dir = Path(data_dir)
        self.remove_app_features = remove_app_features
        self.only_app_features=only_app_features
        print(f"New monitor function with remove_app_features={remove_app_features}")
    # --- Helper functions ---
    def _load_json_lines(self, file_path):
        with open(file_path) as f:
            return [json.loads(line) for line in f]

    def _add_prefix(self, df, prefix, keep_cols):
        df = df[keep_cols]
        df = df.rename(columns={col: f"{prefix}{col}" for col in df.columns if col not in ['camp_name','repeat_id','exp_id']})
        return df

    # --- Processing functions ---
    def _process_owamp(self, df):
        df['owamp_delay_ns'] = df['rx_time'] - df['tx_time']
        df = df[['camp_name','repeat_id','exp_id','direction','tx_err_perc','rx_err_perc','owamp_delay_ns']]
        grouped = df.groupby(['camp_name','repeat_id','exp_id','direction']).mean()
        grouped = grouped.unstack('direction')
        grouped.columns = [f'owamp_{col}_{dir}' for col, dir in grouped.columns]
        return grouped.reset_index()

    def _process_twamp(self, df):
        df['twamp_rtt_ns'] = df['rx_time'] - df['tx_time']
        df['twamp_fwd_delay_txrx_ns'] = df['reflect_tx_time'] - df['tx_time']
        df['twamp_rev_delay_rxtx_ns'] = df['rx_time'] - df['reflect_tx_time']
        grouped = df.groupby(['camp_name','repeat_id','exp_id']).agg(
            twamp_rtt_ns=('twamp_rtt_ns','mean'),
            twamp_fwd_delay_txrx_ns=('twamp_fwd_delay_txrx_ns','mean'),
            twamp_rev_delay_rxtx_ns=('twamp_rev_delay_rxtx_ns','mean'),
            tx_err_perc=('tx_err_perc','mean'),
            tx_rx_err_perc=('tx_rx_err_perc','mean'),
            rx_err_perc=('rx_err_perc','mean'),
            reflect_tx_err_perc=('reflect_tx_err_perc','mean')
        )
        return grouped.reset_index()

    def _process_udpping(self, df):
        grouped = df.groupby(['camp_name','repeat_id','exp_id']).agg(
            udpping_client2server_ns=('client2server_ns', 'mean'),
            udpping_server2client_ns=('server2client_ns', 'mean'),
            udpping_rtt_ns=('rtt_ns', 'mean')
        )
        return grouped.reset_index()

    def _process_app(self, df):
        df['pack_len_bytes'] = df['pack_len_bytes'].astype(float)
        df['rtt'] = df['rtt'].astype(float)

        def agg_func(x):
            mean_rtt_ms = x['rtt'].mean() * 1000
            total_bits = x['pack_len_bytes'].sum() * 8
            total_time_s = x['rtt'].sum() if x['rtt'].sum() > 0 else 1e-9
            throughput_mbps = (total_bits / total_time_s) / 1e6
            return pd.Series({
                'rtt_ms': mean_rtt_ms,
                'throughput_mbps': throughput_mbps
            })

        grouped = df.groupby(['camp_name','repeat_id','exp_id','app_name']).apply(agg_func)
        grouped = grouped.unstack('app_name')
        grouped.columns = [f"app_{col}_{app}" for col, app in grouped.columns]
        return grouped.reset_index()

    # --- Main method ---
    def get_dataframe(self, samples: int = None) -> pd.DataFrame:
        mega_dfs = []

        if not self.only_app_features:
            # ICMP
            icmp_keep = [
                'camp_name','repeat_id','exp_id',
                'min_rtt_ms','avg_rtt_ms','max_rtt_ms',
                'packet_loss_0to1','jitter_ms'
            ]
            icmp_path = self.data_dir / 'icmp.json'
            icmp_df = pd.DataFrame(self._load_json_lines(icmp_path))
            mega_dfs.append(self._add_prefix(icmp_df, 'icmp_', icmp_keep))

            # IPERF
            iperf_keep = [
                'camp_name','repeat_id','exp_id',
                'tcp_dl_retransmits','tcp_dl_sent_bps','tcp_dl_sent_bytes','tcp_dl_received_bps','tcp_dl_received_bytes',
                'tcp_ul_retransmits','tcp_ul_sent_bps','tcp_ul_sent_bytes','tcp_ul_received_bps','tcp_ul_received_bytes',
                'udp_dl_bytes','udp_dl_bps','udp_dl_jitter_ms','udp_dl_lost_percent',
                'udp_ul_bytes','udp_ul_bps','udp_ul_jitter_ms','udp_ul_lost_percent'
            ]
            iperf_path = self.data_dir / 'iperf.json'
            iperf_df = pd.DataFrame(self._load_json_lines(iperf_path))
            mega_dfs.append(self._add_prefix(iperf_df, 'iperf_', iperf_keep))

            # OWAMP
            owamp_path = self.data_dir / 'owamp.json'
            owamp_df = pd.DataFrame(self._load_json_lines(owamp_path))
            mega_dfs.append(self._process_owamp(owamp_df))

            # TWAMP
            twamp_path = self.data_dir / 'twamp.json'
            twamp_df = pd.DataFrame(self._load_json_lines(twamp_path))
            mega_dfs.append(self._process_twamp(twamp_df))

            # UDP Ping
            udpping_path = self.data_dir / 'udpping.json'
            udpping_df = pd.DataFrame(self._load_json_lines(udpping_path))
            mega_dfs.append(self._process_udpping(udpping_df))

        # APP
        if not self.remove_app_features:
            app_path = self.data_dir / 'app.json'
            app_df = pd.DataFrame(self._load_json_lines(app_path))
            mega_dfs.append(self._process_app(app_df))

        # Merge
        mega_file = reduce(lambda left, right: pd.merge(left, right, on=['camp_name','repeat_id','exp_id'], how='outer'), mega_dfs)

        # Sort by repeat_id (or another logical ordering)
        if 'repeat_id' in mega_file.columns:
            mega_file = mega_file.sort_values(by='repeat_id')

        # Keep last N samples if requested
        if samples is not None:
            if samples > 0:
                mega_file = mega_file.tail(samples)  # last N
            elif samples < 0:
                mega_file = mega_file.head(-samples)  # first N

        # Add backup app features filled with zeros if remove_app_features is True
        if self.remove_app_features:
            backup_features=gparams._AI["backup_features"]

            for col in backup_features:
                if col not in mega_file.columns:
                    mega_file[col] = 0
        if self.only_app_features:
            name='test_app.csv'
        else:
            name='test.csv'
        mega_file.to_csv(name, index=False)

        return mega_file
