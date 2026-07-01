#!/usr/bin/env python3

import argparse
import json
import math
import os
import statistics
import subprocess
import time
from datetime import datetime
from io import StringIO

import pandas as pd
import pyshark
import psutil
from icmplib import ping

from orchestrator import Orchestrator, VethOrchestrator


DB_FILE_FIELDS_OUT_LOG = {
    "time": None,
    "description": None,
}

RES_FILE_FIELDS_ICMP = {
    "camp_name": None,
    "repeat_id": None,
    "exp_id": None,
    "timestamp": None,
    "min_rtt_ms": None,
    "avg_rtt_ms": None,
    "max_rtt_ms": None,
    "rtts_ms": None,
    "packets_sent": None,
    "packets_received": None,
    "packet_loss_0to1": None,
    "jitter_ms": None,
}

RES_FILE_FIELDS_IPERF = {
    "camp_name": None,
    "repeat_id": None,
    "exp_id": None,
    "timestamp": None,
    "tcp_dl_retransmits": None,
    "tcp_dl_sent_bps": None,
    "tcp_dl_sent_bytes": None,
    "tcp_dl_received_bps": None,
    "tcp_dl_received_bytes": None,
    "tcp_ul_retransmits": None,
    "tcp_ul_sent_bps": None,
    "tcp_ul_sent_bytes": None,
    "tcp_ul_received_bps": None,
    "tcp_ul_received_bytes": None,
    "udp_dl_bytes": None,
    "udp_dl_bps": None,
    "udp_dl_jitter_ms": None,
    "udp_dl_lost_percent": None,
    "udp_ul_bytes": None,
    "udp_ul_bps": None,
    "udp_ul_jitter_ms": None,
    "udp_ul_lost_percent": None,
}

RES_FILE_FIELDS_APP = {
    "camp_name": None,
    "repeat_id": None,
    "exp_id": None,
    "timestamp": None,
    "app_name": None,
    "pack_id": None,
    "sniff_time": None,
    "sniff_timestamp": None,
    "protocol": None,
    "pack_len_bytes": None,
    "addr_src": None,
    "port_src": None,
    "addr_dest": None,
    "port_dest": None,
    "rtt": None,
    "drop_flag": None,
}

RES_FILE_FIELDS_GUI_APP = {
    "timestamp": None,
    "app_name": None,
    "RTT (msec)": None,
    "Throughput (Mbps)": None,
}

RES_FILE_FIELDS_UDPPING = [
    "seq",
    "send_time_ns",
    "server_time_ns",
    "receive_time_ns",
    "client_to_server_ns",
    "server_to_client_ns",
    "rtt_ns",
]

RES_FILE_FIELDS_OWAMP = [
    "seq",
    "tx_timestamp",
    "tx_sync",
    "tx_error_estimate",
    "rx_timestamp",
    "rx_sync",
    "rx_error_estimate",
    "ttl",
]

RES_FILE_FIELDS_TWAMP = [
    "fw_seq",
    "fw_tx_timestamp",
    "fw_tx_sync",
    "fw_tx_error_estimate",
    "fw_rx_timestamp",
    "fw_rx_sync",
    "fw_rx_error_estimate",
    "fw_ttl",
    "rv_seq",
    "rv_tx_timestamp",
    "rv_tx_sync",
    "rv_tx_error_estimate",
    "rv_rx_timestamp",
    "rv_rx_sync",
    "rv_rx_error_estimate",
    "rv_ttl",
]


class Backend:
    def __init__(self, args):
        self.args = args
        self.cnt_exp = 0
        self.cnt_repet = 0
        self.df_out_monitor = None

        self.init_dbs()

    def get_str_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    def wait(self, sec):
        time.sleep(sec)

    def ensure_parent(self, loc):
        parent = os.path.dirname(os.path.abspath(os.path.expanduser(loc)))
        if parent:
            os.makedirs(parent, exist_ok=True)

    def init_db(self, loc):
        self.ensure_parent(loc)
        with open(os.path.expanduser(loc), "w", encoding="utf-8"):
            pass

    def write_dict2json(self, loc, mydict, clean=False):
        self.ensure_parent(loc)
        mode = "w" if clean else "a"
        with open(os.path.expanduser(loc), mode, encoding="utf-8") as f:
            f.write(json.dumps(mydict, ensure_ascii=False))
            f.write("\n")

    def write_log(self, description):
        line = dict(DB_FILE_FIELDS_OUT_LOG)
        line["time"] = self.get_str_timestamp()
        line["description"] = str(description)
        self.write_dict2json(self.args.out_log, line, clean=False)
        print("(Backend) DBG: " + str(description))

    def init_dbs(self):
        if self.args.clean_start:
            files = [
                self.args.out_log,
                self.args.iperf_out,
                self.args.icmp_out,
                self.args.udpping_out,
                self.args.owamp_out,
                self.args.twamp_out,
                self.args.app_out,
                self.args.gui_app_out,
            ]

            for loc in files:
                try:
                    self.init_db(loc)
                except Exception as ex:
                    print("(Backend) ERROR init db " + str(loc) + ": " + str(ex))

    def kill_process_tree(self, pid, including_parent=True):
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)

        for child in children:
            child.kill()

        psutil.wait_procs(children, timeout=5)

        if including_parent:
            parent.kill()
            parent.wait(5)

    def run_forever(self):
        self.write_log(
            "Initiating standalone backend, campaign="
            + str(self.args.campaign)
            + ", interval_sec="
            + str(self.args.interval)
        )

        while True:
            try:
                self.run_exp()
            except KeyboardInterrupt:
                self.write_log("Backend stopped by user")
                break
            except Exception as ex:
                self.write_log("ERROR in measurement cycle: " + str(ex))

            self.cnt_exp += 1

            if self.args.once:
                break

            if self.args.interval > 0:
                time.sleep(self.args.interval)

        self.write_log("Completed standalone backend")

    def run_exp(self):
        my_event = "Initiating exp:" + str(self.cnt_exp)
        self.write_log(my_event)

        print("--- --- --- --- --- --- --- --- ---")

        self.get_baseline_measurements()
        self.get_app_measurements()

        my_event = "Completed exp:" + str(self.cnt_exp)
        self.write_log(my_event)

        print("--- --- --- --- --- --- --- --- ---")

    def get_baseline_measurements(self):
        self.get_iperf()
        self.get_icmp()
        self.get_udpping()
        self.get_owamp()
        self.get_twamp()

    def get_app_measurements(self):
        self.get_app_mqtt()
        self.get_app_video()
        self.get_app_profinet()

    def get_app_mqtt(self):
        try:
            if not self.args.mqtt_enable:
                print("(Backend) DBG: MQTT test deactivated")
                return None

            print("(Backend) DBG: Init MQTT test ................")

            sleep_sec = self.args.mqtt_interval_ms * 1e-3
            client_app_cmd = f"{self.args.conda_exec} {self.args.mqtt_script}"

            config_dict = {
                "app_name": "MQTT",
                "client_app_cmd": client_app_cmd,
                "camp_name": self.args.campaign,
                "env": {
                    "ENV_SERVER_IP": self.args.mqtt_server_ip or self.args.server_ip,
                    "ENV_SERVER_PORT": str(self.args.mqtt_port),
                    "SLEEP_SEC": str(sleep_sec),
                    "MAX_PAYLOAD_SIZE_BYTES": str(self.args.mqtt_payload_bytes),
                },
                "shark_captime_sec": self.args.shark_capture_time,
                "shark_max_packs": self.args.shark_max_packets,
            }

            return self.activate_app(config_dict=config_dict)

        except Exception as ex:
            print("(Backend) ERROR: Init MQTT: " + str(ex))
            return None

    def get_app_video(self):
        try:
            if not self.args.video_enable:
                print("(Backend) DBG: Video test deactivated")
                return None

            print("(Backend) DBG: Init Video test ................")

            client_app_cmd = f"{self.args.conda_exec} {self.args.video_script}"

            config_dict = {
                "app_name": "video",
                "client_app_cmd": client_app_cmd,
                "camp_name": self.args.campaign,
                "env": {
                    "ENV_SERVER_IP": self.args.video_server_ip or self.args.server_ip,
                    "ENV_SERVER_PORT": str(self.args.video_port),
                    "ENV_FPS": str(self.args.video_fps),
                    "ENV_FRAME_WIDTH": str(self.args.video_width),
                    "ENV_FRAME_HEIGHT": str(self.args.video_height),
                },
                "shark_captime_sec": self.args.video_shark_capture_time,
                "shark_max_packs": self.args.video_shark_max_packets,
            }

            return self.activate_app(config_dict=config_dict)

        except Exception as ex:
            print("(Backend) ERROR: Init Video: " + str(ex))
            return None

    def get_app_profinet(self):
        return None

    def activate_app(self, config_dict):
        try:
            app_name = config_dict["app_name"]
            client_app_cmd = config_dict["client_app_cmd"]
            env = config_dict.get("env", {})
            shark_captime_sec = config_dict["shark_captime_sec"]
            shark_max_packs = config_dict["shark_max_packs"]
            camp_name = config_dict["camp_name"]

            print(
                "(Backend) DBG: Activating app="
                + str(app_name)
                + " in namespace="
                + str(self.args.ns_name)
                + "..."
            )

        except Exception as ex:
            print("(Backend) ERROR: Activate app: " + str(ex))
            return None

        proc = None
        orch = None

        try:
            orch = VethOrchestrator()
            orch.create_namespace(
                self.args.ns_name,
                self.args.veth_host,
                self.args.veth_ns,
                self.args.host_ip,
                self.args.ns_ip,
                self.args.wwan_if,
            )

            proc = orch.activate(client_app_cmd=client_app_cmd, env=env)

            self.get_pyshark_kpis(
                my_iface=self.args.veth_host,
                display_filter=None,
                max_packs=shark_max_packs,
                captime_sec=shark_captime_sec,
                camp_name=camp_name,
                app_name=app_name,
            )

        except Exception as ex:
            print("(Backend) ERROR: activate_app runtime: " + str(ex))

        finally:
            try:
                print("(Backend) DBG: Stopping app gracefully...")
                if proc is not None and proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=5)
            except Exception as ex:
                print("(Backend) Warning: process terminate failed: " + str(ex))
                try:
                    if proc is not None:
                        proc.kill()
                except Exception:
                    pass

            try:
                print("(Backend) DBG: Deactivating app in the orchestrator...")
                if orch is not None:
                    orch.deactivate(proc)
            except Exception as ex:
                print("(Backend) Warning: orchestrator deactivate failed: " + str(ex))

    def get_pyshark_kpis(
        self,
        my_iface="Ethernet",
        display_filter=None,
        max_packs=5000,
        captime_sec=10,
        camp_name="",
        app_name="",
    ):
        print("(Backend) DBG: Initiate pyshark kpis ...")

        try:
            os.remove(self.args.shark_temp_file)
            print("(Backend) DBG: Previous temp capture removed OK")
        except Exception as ex:
            print("(Backend) Warning: Temp capture remove=" + str(ex))

        try:
            print("(Backend) DBG: Initiate capture for iface=" + str(my_iface) + "...")
            cap = pyshark.LiveCapture(
                interface=my_iface,
                display_filter=display_filter,
                output_file=self.args.shark_temp_file,
            )

            print(
                "(Backend) DBG: Will capture for max packs="
                + str(max_packs)
                + " OR max duration sec="
                + str(captime_sec)
                + "..."
            )

            pack_cnt = 0
            start_time = time.time()
            sniff_duration_sec = 0

            for pack in cap.sniff_continuously():
                sniff_duration_sec = time.time() - start_time

                if pack_cnt > max_packs or sniff_duration_sec > captime_sec:
                    print("(Backend) DBG: Stopping capture loop due to limits.")
                    break

                pack_cnt += 1

            print(
                "(Backend) DBG: Capture OK, final pack_cnt="
                + str(pack_cnt)
                + ", duration sec="
                + str(sniff_duration_sec)
            )

            self.close_pyshark_processes(cap)
            res = 200

        except Exception as ex:
            print("(Backend) ERROR during capture: " + str(ex))
            res = 500

        if res != 200:
            print("(Backend) ERROR: Exiting pyshark KPI")
            return None

        try:
            min_sniff_timestamp = math.inf
            max_sniff_timestamp = 0
            sum_packet_len_bytes = 0
            rtt_list = []
            max_timestamp = "1999-01-01 00:00:00.000000"

            print("(Backend) DBG: Capture analysis...")
            cap = pyshark.FileCapture(input_file=self.args.shark_temp_file)

            pack_cnt = 0

            for pack in cap:
                myjson_line = dict(RES_FILE_FIELDS_APP)

                try:
                    myjson_line["camp_name"] = camp_name
                except Exception:
                    pass

                try:
                    myjson_line["repeat_id"] = str(self.cnt_repet)
                except Exception:
                    pass

                try:
                    myjson_line["exp_id"] = str(self.cnt_exp)
                except Exception:
                    pass

                try:
                    res = self.get_str_timestamp()
                    myjson_line["timestamp"] = res
                    max_timestamp = max(max_timestamp, res)
                except Exception:
                    pass

                try:
                    myjson_line["app_name"] = app_name
                except Exception:
                    pass

                try:
                    myjson_line["pack_id"] = str(pack_cnt)
                except Exception:
                    pass

                try:
                    myjson_line["sniff_time"] = str(pack.sniff_time)
                except Exception:
                    pass

                try:
                    res = pack.sniff_timestamp
                    myjson_line["sniff_timestamp"] = str(res)
                    min_sniff_timestamp = min(min_sniff_timestamp, float(res))
                    max_sniff_timestamp = max(max_sniff_timestamp, float(res))
                except Exception:
                    pass

                try:
                    myjson_line["protocol"] = str(pack.highest_layer)
                except Exception:
                    pass

                try:
                    res = pack.length
                    myjson_line["pack_len_bytes"] = str(res)
                    sum_packet_len_bytes += int(res)
                except Exception:
                    pass

                try:
                    myjson_line["addr_src"] = str(pack.ip.src)
                except Exception:
                    pass

                try:
                    myjson_line["port_src"] = str(pack[pack.transport_layer].srcport)
                except Exception:
                    pass

                try:
                    myjson_line["addr_dest"] = str(pack.ip.dst)
                except Exception:
                    pass

                try:
                    myjson_line["port_dest"] = str(pack[pack.transport_layer].dstport)
                except Exception:
                    pass

                try:
                    res = pack.tcp.analysis_ack_rtt
                    myjson_line["rtt"] = str(res)
                    rtt_list.append(float(res))
                except Exception:
                    pass

                try:
                    str_p = str(pack)
                    if (
                        "TCP Dup ACK" in str_p
                        or "TCP Previous" in str_p
                        or "TCP Retransmission" in str_p
                        or "TCP Fast Retransmission" in str_p
                        or "Out-Of-Order" in str_p
                        or "TCP Spurious Retransmission" in str_p
                    ):
                        res = True
                    else:
                        res = False

                    myjson_line["drop_flag"] = str(res)
                except Exception:
                    pass

                pack_cnt += 1
                self.write_dict2json(self.args.app_out, myjson_line, clean=False)

                if pack_cnt < 2:
                    print(
                        "(Backend) DBG: Capture example pack addr dest="
                        + str(myjson_line["addr_dest"])
                    )

            try:
                cap.close()
            except Exception:
                pass

            print("(Backend) DBG: Capture read OK")

        except Exception as ex:
            print("(Backend) ERROR: Capture read=" + str(ex))

        try:
            myjson_line = dict(RES_FILE_FIELDS_GUI_APP)
            time_diff = max_sniff_timestamp - min_sniff_timestamp

            if time_diff > 0:
                thru_bps = float((sum_packet_len_bytes * 8) / time_diff)
            else:
                thru_bps = 0.0

            try:
                myjson_line["RTT (msec)"] = str(statistics.mean(rtt_list) * 1e3)
            except Exception:
                pass

            try:
                myjson_line["app_name"] = app_name
            except Exception:
                pass

            try:
                myjson_line["Throughput (Mbps)"] = str(thru_bps * 1e-6)
            except Exception:
                pass

            try:
                myjson_line["timestamp"] = str(max_timestamp)
            except Exception:
                pass

            self.write_dict2json(self.args.gui_app_out, myjson_line, clean=False)
            print("(Backend) DBG: Capture write OK")

        except Exception as ex:
            print("(Backend) ERROR: Capture write=" + str(ex))

        try:
            os.remove(self.args.shark_temp_file)
            print("(Backend) DBG: Temp capture removed OK")
        except Exception as ex:
            print("(Backend) ERROR: Temp capture remove=" + str(ex))
            return None

        print("(Backend) DBG: Capture analysis OK")
        return 200

    def close_pyshark_processes(self, cap):
        try:
            if hasattr(cap, "close"):
                cap.close()
        except Exception as ex:
            print("(Backend) Warning: cap.close failed: " + str(ex))

        try:
            if hasattr(cap, "_running_processes"):
                for proc in cap._running_processes:
                    if hasattr(proc, "is_alive"):
                        if proc.is_alive():
                            print(
                                "(Backend) DBG: Terminating multiprocessing.Process PID="
                                + str(proc.pid)
                                + "..."
                            )
                            proc.terminate()
                            proc.join(timeout=5)

                    elif hasattr(proc, "poll"):
                        if proc.poll() is None:
                            print(
                                "(Backend) DBG: Terminating subprocess.Popen PID="
                                + str(proc.pid)
                                + "..."
                            )
                            proc.terminate()

                            try:
                                proc.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                print(
                                    "(Backend) DBG: Killing subprocess.Popen PID="
                                    + str(proc.pid)
                                    + " after timeout..."
                                )
                                proc.kill()
                                proc.wait()
            else:
                print("(Backend) Warning: no _running_processes attribute found in cap")
        except Exception as ex:
            print("(Backend) Warning: close_pyshark_processes failed: " + str(ex))

    def get_iperf(self):
        try:
            if not self.args.iperf_enable:
                print("(Backend) DBG: Iperf test deactivated")
                return None

            print("(Backend) DBG: Init iperf test ................")

            protocol = self.args.iperf_protocols
            payload_bytes = self.args.iperf_payload_bytes
            target_rate_mbps = self.args.iperf_bitrate_mbps
            duration_sec = self.args.iperf_duration
            server_ip = self.args.iperf_server_ip or self.args.server_ip
            camp_name = self.args.campaign

        except Exception as ex:
            print("(Backend) ERROR: Init iperf: " + str(ex))
            return None

        myjson_line = dict(RES_FILE_FIELDS_IPERF)
        myjson_line["camp_name"] = camp_name
        myjson_line["repeat_id"] = str(self.cnt_repet)
        myjson_line["exp_id"] = str(self.cnt_exp)
        myjson_line["timestamp"] = self.get_str_timestamp()

        if protocol in ["TCP", "All"]:
            data = self.get_iperf_stats(
                server_ip=server_ip,
                port=self.args.iperf_port,
                flag_udp=False,
                flag_downlink=True,
                duration=duration_sec,
                bitrate=None,
                pack_len=payload_bytes,
            )

            if data is not None:
                try:
                    myjson_line["tcp_dl_retransmits"] = data["end"]["sum_sent"]["retransmits"]
                    myjson_line["tcp_dl_sent_bps"] = data["end"]["sum_sent"]["bits_per_second"]
                    myjson_line["tcp_dl_sent_bytes"] = data["end"]["sum_sent"]["bytes"]
                    myjson_line["tcp_dl_received_bps"] = data["end"]["sum_received"]["bits_per_second"]
                    myjson_line["tcp_dl_received_bytes"] = data["end"]["sum_received"]["bytes"]
                    print("(Backend) DBG: TCP downlink bps " + str(myjson_line["tcp_dl_received_bps"]))
                except Exception as ex:
                    print("(Backend) ERROR: TCP downlink write " + str(ex))

            data = self.get_iperf_stats(
                server_ip=server_ip,
                port=self.args.iperf_port,
                flag_udp=False,
                flag_downlink=False,
                duration=duration_sec,
                bitrate=None,
                pack_len=payload_bytes,
            )

            if data is not None:
                try:
                    myjson_line["tcp_ul_retransmits"] = data["end"]["sum_sent"]["retransmits"]
                    myjson_line["tcp_ul_sent_bps"] = data["end"]["sum_sent"]["bits_per_second"]
                    myjson_line["tcp_ul_sent_bytes"] = data["end"]["sum_sent"]["bytes"]
                    myjson_line["tcp_ul_received_bps"] = data["end"]["sum_received"]["bits_per_second"]
                    myjson_line["tcp_ul_received_bytes"] = data["end"]["sum_received"]["bytes"]
                    print("(Backend) DBG: TCP uplink bps " + str(myjson_line["tcp_ul_received_bps"]))
                except Exception as ex:
                    print("(Backend) ERROR: TCP uplink write " + str(ex))

        if protocol in ["UDP", "All"]:
            bitrate = str(target_rate_mbps) + "M"

            data = self.get_iperf_stats(
                server_ip=server_ip,
                port=self.args.iperf_port,
                flag_udp=True,
                flag_downlink=True,
                duration=duration_sec,
                bitrate=bitrate,
                pack_len=payload_bytes,
            )

            if data is not None:
                try:
                    myjson_line["udp_dl_bytes"] = data["end"]["sum"]["bytes"]
                    myjson_line["udp_dl_bps"] = data["end"]["sum"]["bits_per_second"]
                    myjson_line["udp_dl_jitter_ms"] = data["end"]["sum"]["jitter_ms"]
                    myjson_line["udp_dl_lost_percent"] = data["end"]["sum"]["lost_percent"]
                    print("(Backend) DBG: UDP downlink bps " + str(myjson_line["udp_dl_bps"]))
                except Exception as ex:
                    print("(Backend) ERROR: UDP downlink write " + str(ex))

            data = self.get_iperf_stats(
                server_ip=server_ip,
                port=self.args.iperf_port,
                flag_udp=True,
                flag_downlink=False,
                duration=duration_sec,
                bitrate=bitrate,
                pack_len=payload_bytes,
            )

            if data is not None:
                try:
                    myjson_line["udp_ul_bytes"] = data["end"]["sum"]["bytes"]
                    myjson_line["udp_ul_bps"] = data["end"]["sum"]["bits_per_second"]
                    myjson_line["udp_ul_jitter_ms"] = data["end"]["sum"]["jitter_ms"]
                    myjson_line["udp_ul_lost_percent"] = data["end"]["sum"]["lost_percent"]
                    print("(Backend) DBG: UDP uplink bps " + str(myjson_line["udp_ul_bps"]))
                except Exception as ex:
                    print("(Backend) ERROR: UDP uplink write " + str(ex))

        self.write_dict2json(self.args.iperf_out, myjson_line, clean=False)

    def get_iperf_stats(
        self,
        server_ip,
        port=5201,
        flag_udp=False,
        flag_downlink=False,
        duration=10,
        bitrate=None,
        pack_len=None,
    ):
        print("(Backend) DBG: Entered iperf3 stats at:" + str(self.get_str_timestamp()))
        print(
            "(Backend) DBG: Settings: UDP="
            + str(flag_udp)
            + ",Downlink="
            + str(flag_downlink)
            + ",bitrate="
            + str(bitrate)
            + ",duration="
            + str(duration)
            + ",pack_len="
            + str(pack_len)
            + "..."
        )

        cmd = ["iperf3"]
        cmd.append("--client")
        cmd.append(str(server_ip))
        cmd.append("--port")
        cmd.append(str(port))
        cmd.append("--time")
        cmd.append(str(duration))

        if bitrate is not None:
            cmd.append("--bitrate")
            cmd.append(str(bitrate))

        if flag_downlink:
            cmd.append("--reverse")

        if flag_udp:
            cmd.append("--udp")

        if pack_len is not None:
            cmd.append("--length")
            cmd.append(str(pack_len))

        cmd.append("--json")

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout

        try:
            data = json.loads(output)
            return data
        except Exception as ex:
            print("(Monitor) ERROR in iperf3 output json=" + str(ex))
            if result.stderr:
                print("(Monitor) iperf3 stderr=" + str(result.stderr))
            return None

    def get_icmp(self):
        try:
            if not self.args.icmp_enable:
                print("(Backend) DBG: ICMP ping test deactivated")
                return None

            print("(Backend) DBG: Init ICMP ping test ................")

            payload_bytes = self.args.icmp_payload_bytes
            interval_ms = self.args.icmp_interval_ms
            packets = self.args.icmp_packets
            server_ip = self.args.icmp_server_ip or self.args.server_ip
            camp_name = self.args.campaign

        except Exception as ex:
            print("(Backend) ERROR: Init ICMP ping: " + str(ex))
            return None

        myjson_line = dict(RES_FILE_FIELDS_ICMP)
        myjson_line["camp_name"] = camp_name
        myjson_line["repeat_id"] = str(self.cnt_repet)
        myjson_line["exp_id"] = str(self.cnt_exp)
        myjson_line["timestamp"] = self.get_str_timestamp()

        interval_sec = interval_ms * 1e-3

        data = self.get_icmp_stats(
            server_ip=server_ip,
            packs=packets,
            interval_sec=interval_sec,
            payload_bytes=payload_bytes,
        )

        if data is not None:
            try:
                myjson_line["min_rtt_ms"] = data.min_rtt
                myjson_line["avg_rtt_ms"] = data.avg_rtt
                myjson_line["max_rtt_ms"] = data.max_rtt
                myjson_line["rtts_ms"] = data.rtts
                myjson_line["packets_sent"] = data.packets_sent
                myjson_line["packets_received"] = data.packets_received
                myjson_line["packet_loss_0to1"] = data.packet_loss
                myjson_line["jitter_ms"] = data.jitter
            except Exception as ex:
                print("(Backend) ERROR: ICMP ping write=" + str(ex))

        self.write_dict2json(self.args.icmp_out, myjson_line, clean=False)

    def get_icmp_stats(self, server_ip, packs=50, interval_sec=1, payload_bytes=64):
        print("(Monitor) DBG: Entered ICMP ping stats at:" + str(self.get_str_timestamp()))
        print(
            "(Monitor) DBG: Settings: server_ip="
            + str(server_ip)
            + ",num_packets="
            + str(packs)
            + ",interval_sec="
            + str(interval_sec)
            + ",payload_bytes="
            + str(payload_bytes)
            + " ..."
        )

        try:
            res = ping(
                server_ip,
                count=packs,
                interval=interval_sec,
                payload_size=payload_bytes,
                privileged=False,
                timeout=self.args.icmp_timeout,
            )

            print("(Monitor) DBG: Ping res=" + str(res))

            if res.is_alive:
                print("(Monitor) DBG: Ping alive!")
                return res

            print("(Monitor) DBG: Ping NOT alive!")
            return None

        except Exception as ex:
            print("(Monitor) ERROR: Ping failed=" + str(ex))
            return None

    def get_udpping(self):
        try:
            if not self.args.udpping_enable:
                print("(Backend) DBG: UDP ping test deactivated")
                return None

            print("(Backend) DBG: Init UDP ping test ................")

            payload_bytes = self.args.udpping_payload_bytes
            interval_ms = self.args.udpping_interval_ms
            packets = self.args.udpping_packets
            server_ip = self.args.udpping_server_ip or self.args.server_ip
            camp_name = self.args.campaign

        except Exception as ex:
            print("(Backend) ERROR: Init UDP ping: " + str(ex))
            return None

        data_df = self.get_udpping_stats(
            server_ip=server_ip,
            payload_bytes=payload_bytes,
            packs=packets,
            interval_ms=interval_ms,
            port=self.args.udpping_port,
        )

        if data_df is not None:
            try:
                data_df["camp_name"] = camp_name
                data_df["repeat_id"] = str(self.cnt_repet)
                data_df["exp_id"] = str(self.cnt_exp)
                data_df["timestamp"] = self.get_str_timestamp()

                self.ensure_parent(self.args.udpping_out)
                with open(os.path.expanduser(self.args.udpping_out), "a", encoding="utf-8") as f:
                    data_df.to_json(f, orient="records", lines=True)

            except Exception as ex:
                print("(Backend) ERROR: UDP ping write=" + str(ex))

    def get_udpping_stats(self, server_ip, payload_bytes=1250, packs=5000, interval_ms=20, port=1234):
        print("(Monitor) DBG: Entered udpPing at:" + str(self.get_str_timestamp()))
        print(
            "(Monitor) DBG: Settings: payload_bytes="
            + str(payload_bytes)
            + ",packs="
            + str(packs)
            + ",interval_ms="
            + str(interval_ms)
            + "..."
        )

        try:
            cmd = []
            cmd.append("./udpClient")
            cmd.append("-a")
            cmd.append(str(server_ip))
            cmd.append("-p")
            cmd.append(str(port))
            cmd.append("-s")
            cmd.append(str(payload_bytes))
            cmd.append("-n")
            cmd.append(str(packs))
            cmd.append("-i")
            cmd.append(str(interval_ms))

            out = subprocess.check_output(cmd, cwd=self.args.udpping_root)
            out = out.decode(errors="replace")

            my_strs = out.split("RTT (all times in ns)")
            temp_str = my_strs[1].split("out of")
            final_str = temp_str[0]
            final_str = final_str.replace("\\n", "$")
            final_str = final_str.replace("\n", "$")
            final_str = final_str.replace("$", "\n")

            df_str = StringIO(final_str)
            df = pd.read_table(df_str, sep=self.args.udpping_delimiter, header=None, engine="python")
            df = df.dropna(axis=1, how="all")
            if len(df.columns) != len(RES_FILE_FIELDS_UDPPING):
                print("(Backend) ERROR cannot process udpPing=unexpected columns " + str(len(df.columns)) + ", expected " + str(len(RES_FILE_FIELDS_UDPPING)))
                print(final_str)
                return None
            df.columns = RES_FILE_FIELDS_UDPPING

            temp_df = df.head(1)
            print("(Backend) Result=" + str(temp_df))

            return df

        except Exception as ex:
            print("(Backend) ERROR cannot process udpPing=" + str(ex))
            return None

    def get_owamp(self):
        try:
            if not self.args.owamp_enable:
                print("(Backend) DBG: OWAMP test deactivated")
                return None

            print("(Backend) DBG: Init OWAMP test ................")

            payload_bytes = self.args.wamp_payload_bytes
            interval_ms = self.args.wamp_interval_ms
            packets = self.args.wamp_packets
            server_ip = self.args.owamp_server_ip or self.args.server_ip
            camp_name = self.args.campaign

        except Exception as ex:
            print("(Backend) ERROR: Init OWAMP: " + str(ex))
            return None

        data_df = self.get_owamp_stats(
            server_ip=server_ip,
            payload_bytes=payload_bytes,
            packs=packets,
            interval_ms=interval_ms,
        )

        if data_df is not None:
            try:
                data_df["camp_name"] = camp_name
                data_df["repeat_id"] = str(self.cnt_repet)
                data_df["exp_id"] = str(self.cnt_exp)
                data_df["timestamp"] = self.get_str_timestamp()

                self.ensure_parent(self.args.owamp_out)
                with open(os.path.expanduser(self.args.owamp_out), "a", encoding="utf-8") as f:
                    data_df.to_json(f, orient="records", lines=True)

            except Exception as ex:
                print("(Backend) ERROR: OWAMP write=" + str(ex))

    def get_owamp_stats(self, server_ip, payload_bytes=1250, packs=5000, interval_ms=20):
        print("(Monitor) DBG: Entered OWAMP at:" + str(self.get_str_timestamp()))
        print(
            "(Monitor) DBG: Settings: payload_bytes="
            + str(payload_bytes)
            + ",packs="
            + str(packs)
            + ",interval_ms="
            + str(interval_ms)
            + "..."
        )

        try:
            cmd = ["owping"]
            cmd.append("-c")
            cmd.append(str(packs))
            cmd.append("-s")
            cmd.append(str(payload_bytes))

            interval_sec = interval_ms * 1e-3
            cmd.append("-i")
            cmd.append(str(interval_sec))
            cmd.append("-R")
            cmd.append(str(server_ip))

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout
            df_str = StringIO(output)
            df = pd.read_table(df_str, sep=r"\s+", header=None, engine="python")
            df = df.dropna(axis=1, how="all")

            if len(df.columns) != len(RES_FILE_FIELDS_OWAMP):
                print("(Backend) ERROR: OWAMP unexpected columns=" + str(len(df.columns)))
                print(output)
                return None

            df.columns = RES_FILE_FIELDS_OWAMP

            df["direction"] = "unknown"
            sep_idx = df.index[df["seq"].diff() < 0].tolist()
            if sep_idx:
                sep = sep_idx[0]
                df.loc[:sep - 1, "direction"] = "fw"
                df.loc[sep:, "direction"] = "rv"

            print("(Backend) DBG OWAMP tx sync status=" + str(df["tx_sync"].mean()))
            return df

        except Exception as ex:
            print("(Backend) ERROR cannot process OWAMP=" + str(ex))
            return None

    def get_twamp(self):
        try:
            if not self.args.twamp_enable:
                print("(Backend) DBG: TWAMP test deactivated")
                return None

            print("(Backend) DBG: Init TWAMP test ................")

            payload_bytes = self.args.wamp_payload_bytes
            interval_ms = self.args.wamp_interval_ms
            packets = self.args.wamp_packets
            server_ip = self.args.twamp_server_ip or self.args.server_ip
            camp_name = self.args.campaign

        except Exception as ex:
            print("(Backend) ERROR: Init TWAMP: " + str(ex))
            return None

        data_df = self.get_twamp_stats(
            server_ip=server_ip,
            payload_bytes=payload_bytes,
            packs=packets,
            interval_ms=interval_ms,
        )

        if data_df is not None:
            try:
                data_df["camp_name"] = camp_name
                data_df["repeat_id"] = str(self.cnt_repet)
                data_df["exp_id"] = str(self.cnt_exp)
                data_df["timestamp"] = self.get_str_timestamp()

                self.ensure_parent(self.args.twamp_out)
                with open(os.path.expanduser(self.args.twamp_out), "a", encoding="utf-8") as f:
                    data_df.to_json(f, orient="records", lines=True)

            except Exception as ex:
                print("(Backend) ERROR: TWAMP write=" + str(ex))

    def get_twamp_stats(self, server_ip, payload_bytes=1250, packs=5000, interval_ms=20):
        print("(Monitor) DBG: Entered TWAMP at:" + str(self.get_str_timestamp()))
        print(
            "(Monitor) DBG: Settings: payload_bytes="
            + str(payload_bytes)
            + ",packs="
            + str(packs)
            + ",interval_ms="
            + str(interval_ms)
            + "..."
        )

        try:
            cmd = ["twping"]
            cmd.append("-c")
            cmd.append(str(packs))
            cmd.append("-s")
            cmd.append(str(payload_bytes))

            interval_sec = interval_ms * 1e-3
            cmd.append("-i")
            cmd.append(str(interval_sec))
            cmd.append("-R")
            cmd.append(str(server_ip))

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout
            df_str = StringIO(output)
            df = pd.read_table(df_str, sep=r"\s+", header=None, engine="python")
            df = df.dropna(axis=1, how="all")

            if len(df.columns) != len(RES_FILE_FIELDS_TWAMP):
                print("(Backend) ERROR: TWAMP unexpected columns=" + str(len(df.columns)))
                print(output)
                return None

            df.columns = RES_FILE_FIELDS_TWAMP

            print("(Backend) DBG TWAMP fw tx sync status=" + str(df["fw_tx_sync"].mean()))
            print("(Backend) DBG TWAMP rv tx sync status=" + str(df["rv_tx_sync"].mean()))
            return df

        except Exception as ex:
            print("(Monitor) ERROR cannot process TWAMP=" + str(ex))
            return None


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--server-ip", required=True)
    parser.add_argument("--iperf-server-ip", default=None)
    parser.add_argument("--icmp-server-ip", default=None)
    parser.add_argument("--udpping-server-ip", default=None)
    parser.add_argument("--owamp-server-ip", default=None)
    parser.add_argument("--twamp-server-ip", default=None)
    parser.add_argument("--mqtt-server-ip", default=None)
    parser.add_argument("--video-server-ip", default=None)
    parser.add_argument("--campaign", default="test")
    parser.add_argument("--interval", type=float, default=0.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--clean-start", action="store_true")

    parser.add_argument("--out-log", default="./out_log.json")
    parser.add_argument("--iperf-out", default="./iperf.json")
    parser.add_argument("--icmp-out", default="./icmp.json")
    parser.add_argument("--udpping-out", default="./udpping.json")
    parser.add_argument("--owamp-out", default="./owamp.json")
    parser.add_argument("--twamp-out", default="./twamp.json")
    parser.add_argument("--app-out", default="./app.json")
    parser.add_argument("--gui-app-out", default="./gui_app.json")

    parser.add_argument("--iperf-enable", action="store_true")
    parser.add_argument("--iperf-port", type=int, default=5201)
    parser.add_argument("--iperf-protocols", choices=["TCP", "UDP", "All"], default="All")
    parser.add_argument("--iperf-payload-bytes", type=int, default=1250)
    parser.add_argument("--iperf-bitrate-mbps", type=int, default=10)
    parser.add_argument("--iperf-duration", type=int, default=10)

    parser.add_argument("--icmp-enable", action="store_true")
    parser.add_argument("--icmp-payload-bytes", type=int, default=64)
    parser.add_argument("--icmp-interval-ms", type=int, default=1000)
    parser.add_argument("--icmp-packets", type=int, default=10)
    parser.add_argument("--icmp-timeout", type=float, default=0.5)

    parser.add_argument("--udpping-enable", action="store_true")
    parser.add_argument("--udpping-root", default="./")
    parser.add_argument("--udpping-payload-bytes", type=int, default=1250)
    parser.add_argument("--udpping-interval-ms", type=int, default=20)
    parser.add_argument("--udpping-packets", type=int, default=5000)
    parser.add_argument("--udpping-port", type=int, default=1234)
    parser.add_argument("--udpping-delimiter", default=";")

    parser.add_argument("--owamp-enable", action="store_true")
    parser.add_argument("--twamp-enable", action="store_true")
    parser.add_argument("--wamp-payload-bytes", type=int, default=1250)
    parser.add_argument("--wamp-interval-ms", type=int, default=20)
    parser.add_argument("--wamp-packets", type=int, default=5000)
    parser.add_argument("--owamp-delimiter", default=r"\s+")
    parser.add_argument("--twamp-delimiter", default=r"\s+")
    parser.add_argument("--owamp-key-word", default="send_time")
    parser.add_argument("--owamp-dbg-key-word", default="sync")

    parser.add_argument("--mqtt-enable", action="store_true")
    parser.add_argument("--mqtt-script", default="client_app_mqtt.py")
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--mqtt-payload-bytes", type=int, default=1250)
    parser.add_argument("--mqtt-interval-ms", type=float, default=20)

    parser.add_argument("--video-enable", action="store_true")
    parser.add_argument("--video-script", default="client_app_video_ul.py")
    parser.add_argument("--video-port", type=int, default=5000)
    parser.add_argument("--video-fps", type=int, default=30)
    parser.add_argument("--video-width", type=int, default=640)
    parser.add_argument("--video-height", type=int, default=480)

    parser.add_argument("--conda-exec", default="python")

    parser.add_argument("--ns-name", default="qoscope-ns")
    parser.add_argument("--veth-host", default="veth-host")
    parser.add_argument("--veth-ns", default="veth-ns")
    parser.add_argument("--host-ip", default="10.200.1.1/24")
    parser.add_argument("--ns-ip", default="10.200.1.2/24")
    parser.add_argument("--wwan-if", default="wwan0")

    parser.add_argument("--shark-temp-file", default="./temp_capture.pcap")
    parser.add_argument("--shark-capture-time", type=int, default=10)
    parser.add_argument("--shark-max-packets", type=int, default=5000)
    parser.add_argument("--video-shark-capture-time", type=int, default=10)
    parser.add_argument("--video-shark-max-packets", type=int, default=5000)

    return parser.parse_args()


if __name__ == "__main__":
    print("(Backend) DBG: Backend initialized")
    pd.options.mode.chained_assignment = None

    args = parse_args()
    backend = Backend(args)
    backend.run_forever()

