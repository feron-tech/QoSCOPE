import re
import logging
import serial
import time
from helper import Helper
import gparams
import os
import helper

# Perform the regex search and extraction
def extract_values(pattern, response):
    match = re.search(pattern, response)
    if match:
        return match.groupdict()
    else:
        return None

class Modem:
    def __init__(self):
        self.connected = False
        self.ppp = None
        self.serial = None
        self.apn = None
        self.data_over_ppp = True

    def initialize_port(self, port, baud_rate, timeout):
        self.serial = serial.Serial(port, baud_rate, timeout=timeout)

    def send_at_command(self, command, timeout=0.5):
        try:
            # Open the serial port
            self.serial.write((command + '\r\n').encode())
            time.sleep(timeout + 0.1)
            # Read the response
            response = self.serial.read_all().decode()
            print(response)
            return response

        except Exception as e:
            return f"Error: {e}"

    def is_alive(self):
        status = self.send_at_command("AT", 0.5)
        return status

    def print_status(self):
        self.send_at_command("AT+CFUN?")
        self.send_at_command("AT+CMEE=2")
        self.send_at_command("AT+CPIN?")
        self.send_at_command("AT+QDSIM?")
        self.send_at_command("AT+QSIMVOL?")
        self.send_at_command("AT+QSIMDET?")

    def get_prefered_mode(self):

        helper=Helper()
        ## log cmd in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW,mystr="AT+QNWPREFCFG=\"mode_pref\"")
        except:
            pass

        response = self.send_at_command("AT+QNWPREFCFG=\"mode_pref\"")

        ## log res in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW,mystr=str(response))
        except:
            pass

        # Define the regular expression to match the mode preferences
        pattern = r'QNWPREFCFG: \"mode_pref\",(.*)'
        # Search for the pattern in the response
        match = re.search(pattern, response)
        if match:
            # Extract the modes from the matched group
            modes = match.group(1).split(':')
            return [mode.strip() for mode in modes]
        else:
            return []

    def set_prefered_mode(self, mode):
        response = self.send_at_command("AT+QNWPREFCFG=\"mode_pref\"," + mode)
        return response

    def get_oper_and_mode(self):

        helper = Helper()
        ## log cmd in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr="AT+COPS?")
        except:
            pass

        response = self.send_at_command("AT+COPS?")

        ## log res in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr=str(response))
        except:
            pass

        pattern = r'\+COPS: \d+,\d+,"([^"]+)",(\d+)'

        # Search for the pattern in the response
        match = re.search(pattern, response)
        if match:
            operator = match.group(1)
            act = match.group(2)
            return operator, act
        else:
            return None, None

    def get_apn(self):

        helper = Helper()
        ## log cmd in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr="AT+CGDCONT?")
        except:
            pass

        response = self.send_at_command("AT+CGDCONT?")

        ## log res in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr=str(response))
        except:
            pass

        # Define the regular expression to match the CGDCONT response
        pattern = r'\+CGDCONT: (\d+),"([^"]+)","([^"]+)"'

        # Find all matches in the response
        matches = re.findall(pattern, response)
        # Dictionary to store the CID and corresponding APN
        cgdcont_info = {}
        for match in matches:
            cid = match[0]
            apn = match[2]
            cgdcont_info[cid] = apn
        return apn

    def set_apn(self, apn):
        response = self.send_at_command("AT+CGDCONT=1,\"IP\",\"" + apn + "\"")
        return response

    def get_csq(self):

        helper = Helper()
        ## log cmd in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr="AT+CSQ")
        except:
            pass

        response = self.send_at_command("AT+CSQ")

        ## log res in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr=str(response))
        except:
            pass

        # Define the regular expression to match the CSQ response
        pattern = r'\+CSQ: (\d+),(\d+)'
        # Search for the pattern in the response
        match = re.search(pattern, response)

        if match:
            rssiX = match.group(1)
            if rssiX == 0:
                rssi = -113
            elif rssiX == 1:
                rssi = -111
            elif rssiX == 31:
                rssi = -51
            elif rssiX == 99:
                rssi = 99
            else:
                rssi = -109 + 2 * (float(rssiX) - 2)

            ber = float(match.group(2))
            if ber == 0:
                ber = 0.001
            elif ber == 1:
                ber = 0.003
            elif ber == 2:
                ber = 0.0064
            elif ber == 3:
                ber = 0.013
            elif ber == 4:
                ber = 0.027
            elif ber == 5:
                ber = 0.054
            elif ber == 6:
                ber = 0.11
            elif ber == 7:
                ber = 0.15
            elif ber == 99:
                ber = 99

            return rssi, ber
        else:
            return None, None

    def get_qrsrp(self):

        helper = Helper()
        ## log cmd in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr="AT+QRSRP")
        except:
            pass

        response = self.send_at_command("AT+QRSRP")

        ## log res in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr=str(response))
        except:
            pass

        # Define the regular expression to match the QRSRP response
        pattern = r'\+QRSRP: (-?\d+),(-?\d+),(-?\d+),(-?\d+),(\w+)'

        # Search for the pattern in the response
        rsrp_prx_list, rsrp_drx_list, rsrp_rx2_list, rsrp_rx3_list, rsrp_sysmode_list=[],[],[],[],[]

        for line in response.splitlines():
            match = re.search(pattern, line)

            if match:
                rsrp_prx = match.group(1)
                rsrp_drx = match.group(2)
                rsrp_rx2 = match.group(3)
                rsrp_rx3 = match.group(4)
                rsrp_sysmode = match.group(5)

                rsrp_prx_list.append(rsrp_prx)
                rsrp_drx_list.append(rsrp_drx)
                rsrp_rx2_list.append(rsrp_rx2)
                rsrp_rx3_list.append(rsrp_rx3)
                rsrp_sysmode_list.append(rsrp_sysmode)
        return rsrp_prx_list, rsrp_drx_list, rsrp_rx2_list, rsrp_rx3_list, rsrp_sysmode_list

    def get_qrsrq(self):

        helper = Helper()
        ## log cmd in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr="AT+QRSRQ")
        except:
            pass

        response = self.send_at_command("AT+QRSRQ")

        ## log res in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr=str(response))
        except:
            pass

        # Define the regular expression to match the QRSRP response
        pattern = r'\+QRSRQ: (-?\d+),(-?\d+),(-?\d+),(-?\d+),(\w+)'

        # Search for the pattern in the response
        rsrq_prx_list, rsrq_drx_list, rsrq_rx2_list, rsrq_rx3_list, rsrq_sysmode_list = [], [], [], [], []

        for line in response.splitlines():
            match = re.search(pattern, line)

            if match:
                rsrq_prx = match.group(1)
                rsrq_drx = match.group(2)
                rsrq_rx2 = match.group(3)
                rsrq_rx3 = match.group(4)
                rsrq_sysmode = match.group(5)

                rsrq_prx_list.append(rsrq_prx)
                rsrq_drx_list.append(rsrq_drx)
                rsrq_rx2_list.append(rsrq_rx2)
                rsrq_rx3_list.append(rsrq_rx3)
                rsrq_sysmode_list.append(rsrq_sysmode)

        return rsrq_prx_list, rsrq_drx_list, rsrq_rx2_list, rsrq_rx3_list, rsrq_sysmode_list

    def get_qsinr(self):

        helper = Helper()
        ## log cmd in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr="AT+QSINR")
        except:
            pass

        response = self.send_at_command("AT+QSINR")

        ## log res in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr=str(response))
        except:
            pass


        # Define the regular expression to match the QRSRP response
        pattern = r'\+QSINR: (-?\d+),(-?\d+),(-?\d+),(-?\d+),(\w+)'

        # Search for the pattern in the response
        sinr_prx_list, sinr_drx_list, sinr_rx2_list, sinr_rx3_list, sinr_sysmode_list = [], [], [], [], []

        for line in response.splitlines():
            match = re.search(pattern, line)

            if match:
                sinr_prx = match.group(1)
                sinr_drx = match.group(2)
                sinr_rx2 = match.group(3)
                sinr_rx3 = match.group(4)
                sinr_sysmode = match.group(5)

                sinr_prx_list.append(sinr_prx)
                sinr_drx_list.append(sinr_drx)
                sinr_rx2_list.append(sinr_rx2)
                sinr_rx3_list.append(sinr_rx3)
                sinr_sysmode_list.append(sinr_sysmode)

        return sinr_prx_list, sinr_drx_list, sinr_rx2_list, sinr_rx3_list, sinr_sysmode_list

    def get_net_info(self):

        helper = Helper()
        ## log cmd in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr="AT+QNWINFO")
        except:
            pass

        response = self.send_at_command("AT+QNWINFO")

        ## log res in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr=str(response))
        except:
            pass


        # Define the regular expression to match the QNWINFO response
        pattern = r'\+QNWINFO: "([^"]+)","([^"]+)","([^"]+)",(\d+)'
        # Find all matches in the response
        matches = re.findall(pattern, response)
        qnwinfo_info = []

        for match in matches:
            network_type = match[0]
            operator_code = match[1]
            band = match[2]
            channel = match[3]
            qnwinfo_info.append({
                'network_type': network_type,
                'operator_code': operator_code,
                'band': band,
                'channel': channel
            })

        return qnwinfo_info

    def serving_cell(self):

        helper = Helper()
        ## log cmd in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr="AT+QENG=\"servingcell\"")
        except:
            pass

        response = self.send_at_command("AT+QENG=\"servingcell\"")

        ## log res in log file
        try:
            helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr=str(response))
        except:
            pass


        # Define the regex pattern with named groups
        lte_pattern = (
            r'"LTE",'
            r'"(?P<is_tdd>[^"]+)",'  # Matches the is_tdd (quoted string)
            r'(?P<MCC>\d+),'  # Matches the MCC (digits)
            r'(?P<MNC>\d+),'  # Matches the MNC (digits)
            r'(?P<cellID>\d+),'  # Matches the cellID (digits)
            r'(?P<PCID>\d+),'  # Matches the PCID (digits)
            r'(?P<earfcn>\d+),'  # Matches the earfcn (digits)
            r'(?P<freq_band_ind>\d+),'  # Matches the freq_band_ind (digits)
            r'(?P<UL_bandwidth>\d+),'  # Matches the UL_bandwidth (digits)
            r'(?P<DL_bandwidth>\d+),'  # Matches the DL_bandwidth (digits)
            r'(?P<TAC>[A-Za-z0-9]+),'  # Matches the TAC (alphanumeric)
            r'(?P<RSRP>-?\d+),'  # Matches the RSRP (integer, can be negative)
            r'(?P<RSRQ>-?\d+),'  # Matches the RSRQ (integer, can be negative)
            r'(?P<RSSI>-?\d+),'  # Matches the RSSI (integer, can be negative)
            r'(?P<SINR>-?\d+),'  # Matches the SINR (integer, can be negative)
            r'(?P<CQI>\d+),'  # Matches the CQI (digits)
            r'(?P<tx_power>-?\d+|-),'  # Matches the tx_power (integer or "-")
            r'(?P<srxlev>-?\d+|-)'
            # r'(?P<srxlev>-?[^,]+)'          # Matches the srxlev (integer, can be negative)

        )

        nrnsa_pattern = (
            r'\+QENG: "NR5G-NSA",'  # Matches the initial part of the response
            r'(?P<MCC>\d+),'  # Matches the MCC (digits)
            r'(?P<MNC>\d+),'  # Matches the MNC (digits)
            r'(?P<PCID>\d+),'  # Matches the PCID (digits)
            r'(?P<RSRP>-?\d+),'  # Matches the RSRP (integer, can be negative)
            r'(?P<SINR>-?\d+),'  # Matches the SINR (integer, can be negative)
            r'(?P<RSRQ>-?\d+),'  # Matches the RSRQ (integer, can be negative)
            r'(?P<ARFCN>\d+),'  # Matches the ARFCN (digits)
            r'(?P<band>\w+),'  # Matches the band (alphanumeric)
            r'(?P<NR_DL_bandwidth>\d+),'  # Matches the NR_DL_bandwidth (digits)
            r'(?P<scs>\d+)'  # Matches the scs (digits)
        )

        nrsa_pattern = (
            r'"NR5G-SA",'  # Matches the initial part of the response
            r'"(?P<is_tdd>[^"]+)",'  # Matches the is_tdd (quoted string)
            r'(?P<MCC>\d+),'  # Matches the MCC (digits)
            r'(?P<MNC>\d+),'  # Matches the MNC (digits)
            r'(?P<cellID>\d+),'  # Matches the cellID (digits)
            r'(?P<PCID>\d+),'  # Matches the PCID (digits)
            r'(?P<TAC>[A-Za-z0-9]+),'  # Matches the TAC (alphanumeric)
            r'(?P<arfcn>\d+),'  # Matches the arfcn (digits)
            r'(?P<freq_band_ind>\d+),'  # Matches the freq_band_ind (digits)
            r'(?P<NR_DL_bandwidth>\d+),'  # Matches the NR_DL_bandwidth (digits)
            r'(?P<RSRP>-?\d+),'  # Matches the RSRP (integer, can be negative)
            r'(?P<RSRQ>-?\d+),'  # Matches the RSRQ (integer, can be negative)
            r'(?P<SINR>-?\d+),'  # Matches the SINR (integer, can be negative)
            r'(?P<scs>\d+)'  # Matches the scs (digits)
            r'(?P<srxlev>-?\d+)'  # Matches the srxlev (integer, can be negative)
        )

        # Check if a match is found and extract the values into variables
        values_lte = extract_values(lte_pattern, response)
        values_nr5g_nsa = extract_values(nrnsa_pattern, response)
        values_nr5g_sa = extract_values(nrsa_pattern, response)

        # Print the extracted values
        print('LTE Values:', values_lte)
        print('NR5G-NSA Values:', values_nr5g_nsa)
        print('NR5G-SA Values:', values_nr5g_sa)

        return response


def main(port='/dev/ttyUSB3',baud_rate=115200,command='AT',myapn='internet.vodafone.gr',camp_name='test'):
    # prepare logging phy.json, phy_raw.json
    helper=Helper()
    myjson_line=gparams._RES_FILE_FIELDS_PHY

    try:
        myjson_line['camp_name'] = str(camp_name)
        helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr=str(camp_name))
    except:
        pass

    try:
        stamp=helper.get_str_timestamp()
        myjson_line['timestamp']=str(stamp)
        helper.write_db(loc=gparams._RES_FILE_LOC_PHY_RAW, mystr=str(stamp))
    except:
        pass

    # init modem
    try:
        my_modem = Modem()
        my_modem.initialize_port(port, baud_rate, 1)
        res = my_modem.is_alive()
    except Exception as ex:
        print('(Phy) ERROR during modem init= '+str(ex))
        return None

    ## 01 get mode
    mode_pref = my_modem.get_prefered_mode()
    my_modem.set_prefered_mode("NR5G-SA")
    # log
    try:
        myjson_line['mode_pref'] = str(mode_pref)
    except:
        pass
    print('(Phy) DBG: 01 get_mode='+str(mode_pref))

    ## 02 get oper and act
    oper, act = my_modem.get_oper_and_mode()
    # log
    try:
        myjson_line['oper'] = str(oper)
    except:
        pass
    try:
        myjson_line['act'] = str(act)
    except:
        pass
    print('(Phy) DBG: 02 get_oper_and_mode='+str(oper)+','+str(act))

    #apn = my_modem.get_apn()
    #resp1 = my_modem.set_apn(myapn)
    #print(apn)
    #print(resp1)

    ## 03 get csq
    rssi, ber = my_modem.get_csq()
    # log
    try:
        myjson_line['rssi'] = str(rssi)
    except:
        pass
    try:
        myjson_line['ber'] = str(ber)
    except:
        pass
    print('(Phy) DBG: 03 get_csq='+str(rssi)+','+str(ber))

    ## 04 get get_qrsrp
    qrsrp_prx, qrsrp_drx, qrsrp_rx2, qrsrp_rx3, qrsrp_sysmode = my_modem.get_qrsrp()
    try:
        myjson_line['qrsrp_prx'] = str(qrsrp_prx)
    except:
        pass
    try:
        myjson_line['qrsrp_drx'] = str(qrsrp_drx)
    except:
        pass
    try:
        myjson_line['qrsrp_rx2'] = str(qrsrp_rx2)
    except:
        pass
    try:
        myjson_line['qrsrp_rx3'] = str(qrsrp_rx3)
    except:
        pass
    try:
        myjson_line['qrsrp_sysmode'] = str(qrsrp_sysmode)
    except:
        pass
    print('(Phy) DBG: 04 get_qrsrp=' + str(qrsrp_prx) + ',' +
          str(qrsrp_drx)+','+str(qrsrp_rx2)+','+str(qrsrp_rx3)+','+str(qrsrp_sysmode))

    ## 05 get get_qrsrq
    rsrq_prx, rsrq_drx, rsrq_rx2, rsrq_rx3, rsrq_sysmode = my_modem.get_qrsrq()
    try:
        myjson_line['rsrq_prx'] = str(rsrq_prx)
    except:
        pass
    try:
        myjson_line['rsrq_drx'] = str(rsrq_drx)
    except:
        pass
    try:
        myjson_line['rsrq_rx2'] = str(rsrq_rx2)
    except:
        pass
    try:
        myjson_line['rsrq_rx3'] = str(rsrq_rx3)
    except:
        pass
    try:
        myjson_line['rsrq_sysmode'] = str(rsrq_sysmode)
    except:
        pass
    print('(Phy) DBG: 05 get_qrsrq=' + str(rsrq_prx) + ',' +
          str(rsrq_drx)+','+str(rsrq_rx2)+','+str(rsrq_rx3)+','+str(rsrq_sysmode))

    ## 06 get get_qsinr
    sinr_prx, sinr_drx, sinr_rx2, sinr_rx3, sinr_sysmode = my_modem.get_qsinr()
    try:
        myjson_line['sinr_prx'] = str(sinr_prx)
    except:
        pass
    try:
        myjson_line['sinr_drx'] = str(sinr_drx)
    except:
        pass
    try:
        myjson_line['sinr_rx2'] = str(sinr_rx2)
    except:
        pass
    try:
        myjson_line['sinr_rx3'] = str(sinr_rx3)
    except:
        pass
    try:
        myjson_line['sinr_sysmode'] = str(sinr_sysmode)
    except:
        pass
    print('(Phy) DBG: 06 get_qsinr=' + str(sinr_prx) + ',' +
          str(sinr_drx)+','+str(sinr_rx2)+','+str(sinr_rx3)+','+str(sinr_sysmode))

    ## 07 get get_net_info
    qnwinfo_info = my_modem.get_net_info()
    try:
        myjson_line['net_info'] = str(qnwinfo_info)
    except:
        pass
    print('(Phy) DBG: 07 get_net_info=' + str(qnwinfo_info))

    ## 08 get get_net_info
    serving_cell_info=my_modem.serving_cell()
    try:
        myjson_line['serving_cell_info'] = str(serving_cell_info)
    except:
        pass
    print('(Phy) DBG: 08 serving_cell=' + str(serving_cell_info))

    helper.write_dict2json(loc=gparams._RES_FILE_LOC_PHY,mydict=myjson_line,clean=False)
    print('(Physical) DBG: Completed serial physical measurements in parallel')
    print("+++++++++++++++++++++++")

def read_input():
    helper=Helper()
    res = None
    attempt = 1
    while (res is None):
        print('(Physical) DBG: Reading input sources (attempt=' + str(attempt) + ')...')

        if attempt > 1:
            helper.wait(gparams._WAIT_SEC_BACKEND_READ_INPUT_SOURCES)

        res = helper.read_json2dict(loc=gparams._DB_FILE_LOC_IN_USER)
        attempt = attempt + 1

        if attempt >= gparams._ATTEMPTS_BACKEND_READ_INPUT_SOURCES:
            print('(Physical) ERROR: Cannot read input sources!')
            return None

    print('(Physical) DBG: Read input sources - Success')
    return res

if __name__ == "__main__":
    res=read_input()
    _camp_name = res['Measurement']['Campaign name']
    _port=str(res['Network']['Modem port'])
    _baud=int(res['Network']['Baud rate'])
    _apn = str(res['Network']['APN'])

    while True:
        main(port=_port, baud_rate=_baud, command='AT', myapn=_apn,camp_name=_camp_name)
