#!/usr/bin/env python3

import argparse
import copy
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import serial
except ImportError:
    print("ERROR: pyserial is not installed.")
    print("Install it with: python -m pip install pyserial")
    sys.exit(1)


PHY_FIELDS = {
    "timestamp": None,
    "camp_name": None,
    "mode_pref": None,
    "oper": None,
    "act": None,
    "rssi": None,
    "ber": None,
    "qrsrp_prx": None,
    "qrsrp_drx": None,
    "qrsrp_rx2": None,
    "qrsrp_rx3": None,
    "qrsrp_sysmode": None,
    "rsrq_prx": None,
    "rsrq_drx": None,
    "rsrq_rx2": None,
    "rsrq_rx3": None,
    "rsrq_sysmode": None,
    "sinr_prx": None,
    "sinr_drx": None,
    "sinr_rx2": None,
    "sinr_rx3": None,
    "sinr_sysmode": None,
    "net_info": None,
    "serving_cell_info": None,
}


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def mkdir_parent(path):
    parent = Path(path).expanduser().parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)


def write_db(loc, mystr):
    mkdir_parent(loc)
    with open(Path(loc).expanduser(), "a", encoding="utf-8") as f:
        f.write(str(mystr))
        if not str(mystr).endswith("\n"):
            f.write("\n")


def write_dict2json(loc, mydict):
    mkdir_parent(loc)
    with open(Path(loc).expanduser(), "a", encoding="utf-8") as f:
        f.write(json.dumps(mydict, ensure_ascii=False))
        f.write("\n")


def extract_values(pattern, response):
    match = re.search(pattern, response)
    if match:
        return match.groupdict()
    return None


class Modem:
    def __init__(self, rawfile=None, echo=True):
        self.connected = False
        self.ppp = None
        self.serial = None
        self.apn = None
        self.data_over_ppp = True
        self.rawfile = rawfile
        self.echo = echo

    def initialize_port(self, port, baud_rate, timeout):
        self.serial = serial.Serial(port, baud_rate, timeout=timeout)

    def close(self):
        try:
            if self.serial is not None and self.serial.is_open:
                self.serial.close()
        except Exception:
            pass

    def raw_log(self, mystr):
        if self.rawfile:
            write_db(self.rawfile, mystr)

    def send_at_command(self, command, timeout=0.5):
        try:
            self.raw_log(">>> " + str(command))
            self.serial.write((command + "\r\n").encode())
            time.sleep(timeout + 0.1)
            response = self.serial.read_all().decode(errors="replace")

            if self.echo:
                print(response)

            self.raw_log(response)
            return response

        except Exception as e:
            msg = "Error: " + str(e)
            self.raw_log(msg)
            return msg

    def is_alive(self):
        return self.send_at_command("AT", 0.5)

    def print_status(self):
        self.send_at_command("AT+CFUN?")
        self.send_at_command("AT+CMEE=2")
        self.send_at_command("AT+CPIN?")
        self.send_at_command("AT+QDSIM?")
        self.send_at_command("AT+QSIMVOL?")
        self.send_at_command("AT+QSIMDET?")

    def get_prefered_mode(self):
        response = self.send_at_command('AT+QNWPREFCFG="mode_pref"')
        pattern = r'QNWPREFCFG: \"mode_pref\",(.*)'
        match = re.search(pattern, response)

        if match:
            modes = match.group(1).split(":")
            return [mode.strip() for mode in modes]

        return []

    def set_prefered_mode(self, mode):
        return self.send_at_command('AT+QNWPREFCFG="mode_pref",' + mode)

    def get_oper_and_mode(self):
        response = self.send_at_command("AT+COPS?")
        pattern = r'\+COPS: \d+,\d+,"([^"]+)",(\d+)'
        match = re.search(pattern, response)

        if match:
            operator = match.group(1)
            act = match.group(2)
            return operator, act

        return None, None

    def get_apn(self):
        response = self.send_at_command("AT+CGDCONT?")
        pattern = r'\+CGDCONT: (\d+),"([^"]+)","([^"]+)"'
        matches = re.findall(pattern, response)

        if not matches:
            return None

        return matches[0][2]

    def set_apn(self, apn):
        return self.send_at_command('AT+CGDCONT=1,"IP","' + apn + '"')

    def get_csq(self):
        response = self.send_at_command("AT+CSQ")
        pattern = r'\+CSQ: (\d+),(\d+)'
        match = re.search(pattern, response)

        if not match:
            return None, None

        rssi_x = int(match.group(1))

        if rssi_x == 0:
            rssi = -113
        elif rssi_x == 1:
            rssi = -111
        elif rssi_x == 31:
            rssi = -51
        elif rssi_x == 99:
            rssi = 99
        else:
            rssi = -109 + 2 * (float(rssi_x) - 2)

        ber_x = int(match.group(2))

        if ber_x == 0:
            ber = 0.001
        elif ber_x == 1:
            ber = 0.003
        elif ber_x == 2:
            ber = 0.0064
        elif ber_x == 3:
            ber = 0.013
        elif ber_x == 4:
            ber = 0.027
        elif ber_x == 5:
            ber = 0.054
        elif ber_x == 6:
            ber = 0.11
        elif ber_x == 7:
            ber = 0.15
        elif ber_x == 99:
            ber = 99
        else:
            ber = float(ber_x)

        return rssi, ber

    def get_qrsrp(self):
        response = self.send_at_command("AT+QRSRP")
        pattern = r'\+QRSRP: (-?\d+),(-?\d+),(-?\d+),(-?\d+),(\w+)'

        rsrp_prx_list = []
        rsrp_drx_list = []
        rsrp_rx2_list = []
        rsrp_rx3_list = []
        rsrp_sysmode_list = []

        for line in response.splitlines():
            match = re.search(pattern, line)

            if match:
                rsrp_prx_list.append(match.group(1))
                rsrp_drx_list.append(match.group(2))
                rsrp_rx2_list.append(match.group(3))
                rsrp_rx3_list.append(match.group(4))
                rsrp_sysmode_list.append(match.group(5))

        return rsrp_prx_list, rsrp_drx_list, rsrp_rx2_list, rsrp_rx3_list, rsrp_sysmode_list

    def get_qrsrq(self):
        response = self.send_at_command("AT+QRSRQ")
        pattern = r'\+QRSRQ: (-?\d+),(-?\d+),(-?\d+),(-?\d+),(\w+)'

        rsrq_prx_list = []
        rsrq_drx_list = []
        rsrq_rx2_list = []
        rsrq_rx3_list = []
        rsrq_sysmode_list = []

        for line in response.splitlines():
            match = re.search(pattern, line)

            if match:
                rsrq_prx_list.append(match.group(1))
                rsrq_drx_list.append(match.group(2))
                rsrq_rx2_list.append(match.group(3))
                rsrq_rx3_list.append(match.group(4))
                rsrq_sysmode_list.append(match.group(5))

        return rsrq_prx_list, rsrq_drx_list, rsrq_rx2_list, rsrq_rx3_list, rsrq_sysmode_list

    def get_qsinr(self):
        response = self.send_at_command("AT+QSINR")
        pattern = r'\+QSINR: (-?\d+),(-?\d+),(-?\d+),(-?\d+),(\w+)'

        sinr_prx_list = []
        sinr_drx_list = []
        sinr_rx2_list = []
        sinr_rx3_list = []
        sinr_sysmode_list = []

        for line in response.splitlines():
            match = re.search(pattern, line)

            if match:
                sinr_prx_list.append(match.group(1))
                sinr_drx_list.append(match.group(2))
                sinr_rx2_list.append(match.group(3))
                sinr_rx3_list.append(match.group(4))
                sinr_sysmode_list.append(match.group(5))

        return sinr_prx_list, sinr_drx_list, sinr_rx2_list, sinr_rx3_list, sinr_sysmode_list

    def get_net_info(self):
        response = self.send_at_command("AT+QNWINFO")
        pattern = r'\+QNWINFO: "([^"]+)","([^"]+)","([^"]+)",(\d+)'
        matches = re.findall(pattern, response)

        qnwinfo_info = []

        for match in matches:
            network_type = match[0]
            operator_code = match[1]
            band = match[2]
            channel = match[3]

            qnwinfo_info.append({
                "network_type": network_type,
                "operator_code": operator_code,
                "band": band,
                "channel": channel
            })

        return qnwinfo_info

    def serving_cell(self):
        response = self.send_at_command('AT+QENG="servingcell"')

        lte_pattern = (
            r'"LTE",'
            r'"(?P<is_tdd>[^"]+)",'
            r'(?P<MCC>\d+),'
            r'(?P<MNC>\d+),'
            r'(?P<cellID>\d+),'
            r'(?P<PCID>\d+),'
            r'(?P<earfcn>\d+),'
            r'(?P<freq_band_ind>\d+),'
            r'(?P<UL_bandwidth>\d+),'
            r'(?P<DL_bandwidth>\d+),'
            r'(?P<TAC>[A-Za-z0-9]+),'
            r'(?P<RSRP>-?\d+),'
            r'(?P<RSRQ>-?\d+),'
            r'(?P<RSSI>-?\d+),'
            r'(?P<SINR>-?\d+),'
            r'(?P<CQI>\d+),'
            r'(?P<tx_power>-?\d+|-),'
            r'(?P<srxlev>-?\d+|-)'
        )

        nrnsa_pattern = (
            r'\+QENG: "NR5G-NSA",'
            r'(?P<MCC>\d+),'
            r'(?P<MNC>\d+),'
            r'(?P<PCID>\d+),'
            r'(?P<RSRP>-?\d+),'
            r'(?P<SINR>-?\d+),'
            r'(?P<RSRQ>-?\d+),'
            r'(?P<ARFCN>\d+),'
            r'(?P<band>\w+),'
            r'(?P<NR_DL_bandwidth>\d+),'
            r'(?P<scs>\d+)'
        )

        nrsa_pattern = (
            r'"NR5G-SA",'
            r'"(?P<is_tdd>[^"]+)",'
            r'(?P<MCC>\d+),'
            r'(?P<MNC>\d+),'
            r'(?P<cellID>\d+),'
            r'(?P<PCID>\d+),'
            r'(?P<TAC>[A-Za-z0-9]+),'
            r'(?P<arfcn>\d+),'
            r'(?P<freq_band_ind>\d+),'
            r'(?P<NR_DL_bandwidth>\d+),'
            r'(?P<RSRP>-?\d+),'
            r'(?P<RSRQ>-?\d+),'
            r'(?P<SINR>-?\d+),'
            r'(?P<scs>\d+),'
            r'(?P<srxlev>-?\d+)'
        )

        values_lte = extract_values(lte_pattern, response)
        values_nr5g_nsa = extract_values(nrnsa_pattern, response)
        values_nr5g_sa = extract_values(nrsa_pattern, response)

        print("LTE Values:", values_lte)
        print("NR5G-NSA Values:", values_nr5g_nsa)
        print("NR5G-SA Values:", values_nr5g_sa)

        return response


def main(port, baud_rate, myapn, camp_name, outfile, rawfile, serial_timeout, force_mode, echo):
    myjson_line = copy.deepcopy(PHY_FIELDS)

    try:
        myjson_line["camp_name"] = str(camp_name)
        write_db(rawfile, str(camp_name))
    except Exception:
        pass

    try:
        stamp = timestamp()
        myjson_line["timestamp"] = str(stamp)
        write_db(rawfile, str(stamp))
    except Exception:
        pass

    try:
        my_modem = Modem(rawfile=rawfile, echo=echo)
        my_modem.initialize_port(port, baud_rate, serial_timeout)
        res = my_modem.is_alive()
        print("(Phy) DBG: modem AT response=" + str(res).strip())
    except Exception as ex:
        print("(Phy) ERROR during modem init= " + str(ex))
        return None

    try:
        mode_pref = my_modem.get_prefered_mode()

        if force_mode is not None:
            my_modem.set_prefered_mode(force_mode)

        myjson_line["mode_pref"] = mode_pref
        print("(Phy) DBG: 01 get_mode=" + str(mode_pref))
    except Exception as ex:
        print("(Phy) ERROR: get_mode=" + str(ex))

    try:
        oper, act = my_modem.get_oper_and_mode()
        myjson_line["oper"] = oper
        myjson_line["act"] = act
        print("(Phy) DBG: 02 get_oper_and_mode=" + str(oper) + "," + str(act))
    except Exception as ex:
        print("(Phy) ERROR: get_oper_and_mode=" + str(ex))

    try:
        rssi, ber = my_modem.get_csq()
        myjson_line["rssi"] = rssi
        myjson_line["ber"] = ber
        print("(Phy) DBG: 03 get_csq=" + str(rssi) + "," + str(ber))
    except Exception as ex:
        print("(Phy) ERROR: get_csq=" + str(ex))

    try:
        qrsrp_prx, qrsrp_drx, qrsrp_rx2, qrsrp_rx3, qrsrp_sysmode = my_modem.get_qrsrp()
        myjson_line["qrsrp_prx"] = qrsrp_prx
        myjson_line["qrsrp_drx"] = qrsrp_drx
        myjson_line["qrsrp_rx2"] = qrsrp_rx2
        myjson_line["qrsrp_rx3"] = qrsrp_rx3
        myjson_line["qrsrp_sysmode"] = qrsrp_sysmode
        print("(Phy) DBG: 04 get_qrsrp=" + str(qrsrp_prx) + "," +
              str(qrsrp_drx) + "," + str(qrsrp_rx2) + "," +
              str(qrsrp_rx3) + "," + str(qrsrp_sysmode))
    except Exception as ex:
        print("(Phy) ERROR: get_qrsrp=" + str(ex))

    try:
        rsrq_prx, rsrq_drx, rsrq_rx2, rsrq_rx3, rsrq_sysmode = my_modem.get_qrsrq()
        myjson_line["rsrq_prx"] = rsrq_prx
        myjson_line["rsrq_drx"] = rsrq_drx
        myjson_line["rsrq_rx2"] = rsrq_rx2
        myjson_line["rsrq_rx3"] = rsrq_rx3
        myjson_line["rsrq_sysmode"] = rsrq_sysmode
        print("(Phy) DBG: 05 get_qrsrq=" + str(rsrq_prx) + "," +
              str(rsrq_drx) + "," + str(rsrq_rx2) + "," +
              str(rsrq_rx3) + "," + str(rsrq_sysmode))
    except Exception as ex:
        print("(Phy) ERROR: get_qrsrq=" + str(ex))

    try:
        sinr_prx, sinr_drx, sinr_rx2, sinr_rx3, sinr_sysmode = my_modem.get_qsinr()
        myjson_line["sinr_prx"] = sinr_prx
        myjson_line["sinr_drx"] = sinr_drx
        myjson_line["sinr_rx2"] = sinr_rx2
        myjson_line["sinr_rx3"] = sinr_rx3
        myjson_line["sinr_sysmode"] = sinr_sysmode
        print("(Phy) DBG: 06 get_qsinr=" + str(sinr_prx) + "," +
              str(sinr_drx) + "," + str(sinr_rx2) + "," +
              str(sinr_rx3) + "," + str(sinr_sysmode))
    except Exception as ex:
        print("(Phy) ERROR: get_qsinr=" + str(ex))

    try:
        qnwinfo_info = my_modem.get_net_info()
        myjson_line["net_info"] = qnwinfo_info
        print("(Phy) DBG: 07 get_net_info=" + str(qnwinfo_info))
    except Exception as ex:
        print("(Phy) ERROR: get_net_info=" + str(ex))

    try:
        serving_cell_info = my_modem.serving_cell()
        myjson_line["serving_cell_info"] = serving_cell_info
        print("(Phy) DBG: 08 serving_cell=" + str(serving_cell_info))
    except Exception as ex:
        print("(Phy) ERROR: serving_cell=" + str(ex))

    try:
        write_dict2json(outfile, myjson_line)
    except Exception as ex:
        print("(Physical) ERROR: write output=" + str(ex))

    try:
        my_modem.close()
    except Exception:
        pass

    print("(Physical) DBG: Completed serial physical measurements")
    print("+++++++++++++++++++++++")
    return myjson_line


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--port", required=True)
    parser.add_argument("--baud", required=True, type=int)
    parser.add_argument("--apn", required=True)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--outfile", required=True)
    parser.add_argument("--rawfile", required=True)

    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=0.0)
    parser.add_argument("--serial-timeout", type=float, default=1.0)
    parser.add_argument("--force-mode", default="NR5G-SA")
    parser.add_argument("--quiet-at", action="store_true")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    force_mode = args.force_mode
    if force_mode == "":
        force_mode = None

    while True:
        main(
            port=args.port,
            baud_rate=args.baud,
            myapn=args.apn,
            camp_name=args.campaign,
            outfile=args.outfile,
            rawfile=args.rawfile,
            serial_timeout=args.serial_timeout,
            force_mode=force_mode,
            echo=not args.quiet_at
        )

        if args.once:
            break

        if args.interval > 0:
            time.sleep(args.interval)

