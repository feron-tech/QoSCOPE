import os

#########################  input params  ########################
if os.name == 'nt': # windows OS
    _ROOT_DIR='C:\\Pycharm\\Projects\\golden_unit'
else: # linux OS
    _ROOT_DIR='/home/targetx/git/golden_unit'

_CONDA_EXEC = '/home/targetx/anaconda3/envs/golden_unit/bin/python'

# Namespace config - hardcoded 
"""
Helping bash script:

echo "Available veth interfaces:"
ip link show | grep veth

echo "Available network interfaces:"
ip link show

echo "Check current IPs:"
ip addr show veth-host
ip addr show veth-ns

echo "NetworkManager devices:"
nmcli device status
"""
_NS_NAME = "appns"
_VETH_HOST = "veth-host"
_VETH_NS = "veth-ns"
_HOST_IP = "10.200.1.1"
_NS_IP = "10.200.1.2"
_WWAN_IF = "wwan0"

_LOCAL_TEST=False
_SHARK_TEMP_OUT_FILE=os.path.join('/tmp/','mypcap.pcap')
_SHARK_VIDEO_TIME_SEC=30
_SHARK_VIDEO_PACKS=50
##################################################################

######################### fixed values (DO NOT ALTER!) ###############################
# folder settings
_DB_DIR=os.path.join(_ROOT_DIR,'db')
_UDPPING_ROOT=os.path.join(os.path.join(_ROOT_DIR,'client'),'udp-ping')
_UDPPING_DELIMITER=';'
_OWAMP_DELIMITER=';'
_TWAMP_DELIMITER=';'
_DELIMITER=';'

## timeouts
_ATTEMPTS_BACKEND_READ_INPUT_SOURCES=1e6
_WAIT_SEC_BACKEND_READ_INPUT_SOURCES=15

## ports
_PORT_SERVER_IPERF=5201
_PORT_SERVER_MQTT1=1883
_PORT_SERVER_MQTT2=8883
_PORT_SERVER_OPENCV=8888
_PORT_SERVER_UDP_PING=1234
_PORT_CLIENT_GUI=8050
_PORT_CLIENT_UDP_PING=1234
##################################################################


######################### data schemas ###############################
_RES_FILE_LOC_GUI_APP=os.path.join(_DB_DIR,'gui_app.json')
_RES_FILE_FIELDS_GUI_APP={
    'RTT (msec)': None,
    'app_name': None,
    'Throughput (Mbps)': None,
    'timestamp': None,
}

_RES_FILE_LOC_APP=os.path.join(_DB_DIR,'app.json')
_RES_FILE_FIELDS_APP={
    'camp_name': None,
    'repeat_id': None,
    'exp_id': None,
    'timestamp': None,
    'app_name': None,
    'pack_id': None,
    'sniff_time':None,
    'sniff_timestamp': None,
    'protocol': None,
    'pack_len_bytes': None,
    'addr_src': None,
    'port_src': None,
    'addr_dest': None,
    'port_dest': None,
    'rtt': None,
    'drop_flag': None,
}


_RES_FILE_LOC_PHY_RAW=os.path.join(_DB_DIR,'phy_raw.json')

_RES_FILE_LOC_PHY=os.path.join(_DB_DIR,'phy.json')
_RES_FILE_FIELDS_PHY={
    'camp_name': None,
    'timestamp':None,
    'mode_pref':None,
    'oper':None,
    'act':None,
    'apn':None,
    'resp1':None,
    'rssi':None,
    'ber':None,
    'qrsrp_prx':None,
    'qrsrp_drx':None,
    'qrsrp_rx2':None,
    'qrsrp_rx3':None,
    'qrsrp_sysmode':None,
    'rsrq_prx':None,
    'rsrq_drx':None,
    'rsrq_rx2':None,
    'rsrq_rx3':None,
    'rsrq_sysmode':None,
    'sinr_prx':None,
    'sinr_drx':None,
    'sinr_rx2':None,
    'sinr_rx3':None,
    'sinr_sysmode':None,
    'net_info':None,
    'serving_cell_info':None,
}

_RES_FILE_LOC_IPERF=os.path.join(_DB_DIR,'iperf.json')
_RES_FILE_FIELDS_IPERF={
    'camp_name': None,
    'repeat_id': None,
    'exp_id': None,
    'timestamp': None,
    'tcp_dl_retransmits': None,
    'tcp_dl_sent_bps': None,
    'tcp_dl_sent_bytes': None,
    'tcp_dl_received_bps': None,
    'tcp_dl_received_bytes': None,
    'tcp_ul_retransmits': None,
    'tcp_ul_sent_bps': None,
    'tcp_ul_sent_bytes': None,
    'tcp_ul_received_bps': None,
    'tcp_ul_received_bytes': None,
    'udp_dl_bytes': None,
    'udp_dl_bps': None,
    'udp_dl_jitter_ms': None,
    'udp_dl_lost_percent': None,
    'udp_ul_bytes': None,
    'udp_ul_bps': None,
    'udp_ul_jitter_ms': None,
    'udp_ul_lost_percent': None
}

_RES_FILE_LOC_ICMP=os.path.join(_DB_DIR,'icmp.json')
_RES_FILE_FIELDS_ICMP={
    'camp_name': None,
    'repeat_id': None,
    'exp_id': None,
    'timestamp': None,
    'min_rtt_ms': None,
    'avg_rtt_ms': None,
    'max_rtt_ms': None,
    'rtts_ms': None,
    'packets_sent': None,
    'packets_received': None,
    'packet_loss_0to1': None,
    'jitter_ms': None
}

_RES_FILE_LOC_UDPPING=os.path.join(_DB_DIR,'udpping.json')
_RES_FILE_FIELDS_UDPPING=[
    'seq_nr',
    'send_time',
    'server_time',
    'receive_time',
    'client2server_ns',
    'server2client_ns',
    'rtt_ns'
]

_RES_FILE_LOC_OWAMP=os.path.join(_DB_DIR,'owamp.json')
_RES_FILE_FIELDS_OWAMP=[
    'seq_nr',
    'tx_time',
    'tx_sync',
    'tx_err_perc',
    'rx_time',
    'rx_sync',
    'rx_err_perc',
    'ttl'
]
_KEY_WORD_OWAMP='seq_nr'
_DBG_KEY_WORD_OWAMP='tx_sync'

_RES_FILE_LOC_TWAMP=os.path.join(_DB_DIR,'twamp.json')
_RES_FILE_FIELDS_TWAMP=[
'tx_seq_nr',
'tx_time',
'tx_sync',
'tx_err_perc',
'tx_rx_time',
'tx_rx_sync',
'tx_rx_err_perc',
'tx_ttl',
'reflect_seq_nr',
'reflect_tx_time',
'reflect_tx_sync',
'reflect_tx_err_perc',
'rx_time',
'rx_sync',
'rx_err_perc',
'reflect_ttl',
]
_DBG_KEY_WORD_TWAMP='tx_sync'

_DB_FILE_LOC_IN_USER=os.path.join(_DB_DIR,'in_user.json')
_DB_FILE_FIELDS_IN_USER={
    'Network': {
        'Client IP': '192.168.1.1',
        'Server IP': '192.200.0.1',
        'APN': 'internet.vodafone.gr',
        'Modem port': '/dev/ttyUSB3',
        'Baud rate': '115200'
    },
    'Measurement': {
        'Campaign name': 'Test01',
        'Experiments per campaign': '1',
        'Repetitions per campaign': '1',
        'Repetition time gap (hours)': '1'
    },
    'Experiment': {
        'Baseline': {
            'iperf': {
                'enable': 'True',
                'protocols': 'All',
                'payload (bytes)': '50',
                'bitrate (Mbps)': '2000',
                'duration (sec)': '10'
            },
            'icmp': {
                'enable': 'True',
                'payload (bytes)': '56',
                'interval (ms)': '20',
                'packets': '1000'
            },
            'udp ping': {
                'enable': 'True',
                'payload (bytes)': '56',
                'interval (ms)': '20',
                'packets': '1000'
            },
            'wamp': {
                'enable': 'True',
                'payload (bytes)': '56',
                'interval (ms)': '20',
                'packets': '1000'
            }
        },
        'Application': {
            'Wireshark': {
                'capture time (sec)': '60',
                'max packets': '500'
            },
            'MQTT': {
                'enable': 'True',
                'payload (bytes)': '50',
                'interval (ms)': '20'
            },
            'Video': {
                'enable': 'True',
                'fps': '30',
                'width': '400',
                'height': '400'
            },
            'Profinet': {
                'enable': 'False'
            }
        }
    }
}

_DB_FILE_LOC_OUT_LOG=os.path.join(_DB_DIR,'out_log.json')
_DB_FILE_FIELDS_OUT_LOG={
    'time': None,
    'description': None
}
##################################################################



