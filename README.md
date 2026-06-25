# Golden Unit

## Installation
Tested in Unix (ubuntu)
### Client-side
```python
## Step 1: Download source code
cd {GOLDEN_UNIT_ROOT} 
git clone https://github.com/geodranas/golden_unit.git
```
```python
# Step 2: Install perfsonar (OWAMP/TWAMP)
sudo snap install curl
sudo su
curl -s https://downloads.perfsonar.net/install | sh -s - tools
sudo apt install perfsonar-tools
sudo apt install owamp-server
sudo apt install owamp-client
sudo apt install twamp-server
sudo apt install twamp-client
exit
```
```python
# Step 3: Install iperf
sudo apt-get install iperf3
```
```python
# Step 4: Install wireshark
sudo apt install tshark
sudo apt-get install wireshark
sudo dpkg-reconfigure wireshark-common 
sudo usermod -a -G wireshark $USER                                  
```
```python
# Step 5: Install and activate docker
sudo apt-get install docker # if it fails, try with docker.io
sudo groupadd docker
sudo gpasswd -a $USER docker
sudo reboot
```
```python
# Step 6: Install udp-ping
cd /{GOLDEN_UNIT_ROOT}/golden_unit/client
git clone https://github.com/EricssonResearch/udp-ping.git
sudo apt-get install build-essential
sudo apt-get install libboost-program-options-dev
sudo apt-get install cmake
cd /{GOLDEN_UNIT_ROOT}/golden_unit/client/udp-ping
g++ -o udpServer udpServer.cpp -lboost_program_options
g++ -o udpClient udpClient.cpp -lboost_program_options
```
```python
# Step 7: Install Python/Anaconda (recommended)
<install anaconda>
conda create --name golden_unit python=3.8
conda activate golden_unit 
pip install iperf3 pyshark pandas docker icmplib pyserial 
pip install paho-mqtt dash dash-bootstrap-components matplotlib fsspec
```
```python
# Step 8: Build Client-side docker images
cd {GOLDEN_UNIT_ROOT}/golden_unit/client/client_stream
docker build -t client_stream .
cd {GOLDEN_UNIT_ROOT}/golden_unit/client/client_mqtt
docker build -t client_mqtt .
docker images # you should see all images generated
```
### Server-side
```python
# Repeat Steps: 1-7 from client-side installation
```
```python
# (optional) Step 2: Disable firewalls if exposure of interfaces is blocked
sudo ufw disable
```
```python
# Step 3: Server-side docker images
cd {GOLDEN_UNIT_ROOT}/golden_unit/server/server_stream
docker build -t server_stream .
docker images # you should see all images generated
```

## Execution
### Option 1: Server-side (bare-metal)
```python
# Terminal 1: Activate iperf
 iperf3 --server
```
```python
# Terminal 2: Activate udp-ping
cd /{GOLDEN_UNIT_ROOT}/golden_unit/server/udp-ping
./udpServer
```
```python
# Terminal 3: Activate OWAMP/TWAMP
(normally no action is required in the server-side)
```
```python
# Terminal 4: Activate Dockers at server-side
docker run -d --rm -p 1883:1883 -p 8883:8883 --name nanomq emqx/nanomq:latest
docker run -it --rm -e ENV_SERVER_IP={GOLDEN_UNIT_CLIENT_IP} -e ENV_SERVER_PORT=8888 --network=bridge server_stream
(the streamer image needs to be regularly checked and occasionally restarted - check logs)
```

### Option 2: Server-side (helm)
# Components
The EaaS deployment runs:

* `qoscope-measurement-tools`

  * `iperf3` server on TCP/UDP `5201`
  * `udp-ping` server on UDP `1234`
* `NanoMQ`

  * MQTT broker on TCP `1883`
  * MQTTS on TCP `8883`
* `qoscope-server-stream`

  * UL video receiver logic
  * connects to the UE/video-source IP and port

# Docker images
The Helm chart expects the following images:

```text
ghcr.io/feron-tech/qoscope-measurement-tools:latest
ghcr.io/feron-tech/qoscope-server-stream:latest
emqx/nanomq:latest
```

# Configure the Helm chart before EaaS deployment
Edit:

```bash
eaas/application/Artifacts/MCIOPs/qoscope-server/values.yaml
```

Important fields:

```yaml
images:
  measurementTools: ghcr.io/feron-tech/qoscope-measurement-tools:latest
  serverStream: ghcr.io/feron-tech/qoscope-server-stream:latest
  nanomq: emqx/nanomq:latest

video:
  sourceIP: "<UE_REACHABLE_IP>"
  sourcePort: "8888"

services:
  iperfNodePortTcp: 32101
  iperfNodePortUdp: 32102
  udpPingNodePort: 32103
  mqttNodePort: 32104
  mqttsNodePort: 32105
```

`video.sourceIP` must be set to the reachable UE/video-source IP.

# Rebuild the Helm package
After changing `values.yaml`, rebuild the Helm `.tgz`:

```bash
cd eaas/application/Artifacts/MCIOPs
helm package qoscope-server
```

This creates:

```text
qoscope-server-0.1.0.tgz
```

# EaaS application package
The EaaS application package should include:

```text
application/
├── QoSCOPEApplication.yaml
├── QoSCOPEApplication.mf
└── Artifacts/
    └── MCIOPs/
        └── qoscope-server-0.1.0.tgz
```

The application YAML must reference:

```yaml
mciopId: Artifacts/MCIOPs/qoscope-server-0.1.0.tgz
```

Then zip the application folder according to the EaaS example format:

```bash
cd eaas/application
zip -r app.zip QoSCOPEApplication.yaml QoSCOPEApplication.mf Artifacts/
```

Upload `app.zip` to the EaaS platform.


### Client-side (bare-metal)
```python
# Terminal 1: Set root dir & activate tool
cd /{GOLDEN_UNIT_ROOT}/golden_unit/
nano gparams.py # (settings)
<set your "ROOT_DIR" depending on your OS>
<disable "LOCAL_TEST" flag>
<save and exit>
```
```python
# Terminal 2: Initiate backend
cd /{GOLDEN_UNIT_ROOT}/golden_unit/
# check that conda env is activated
python main_backend.py
(note that existing Docker containers will be removed)
```
```python
# Terminal 3: Enable PHY layer measurements
cd /{GOLDEN_UNIT_ROOT}/golden_unit/
{ROOT}/envs/golden_unit/bin/python physical.py # use python bin to run physical.py script
```
```python
# Terminal 4: Initiate GUI
cd /{GOLDEN_UNIT_ROOT}/golden_unit/
# check that conda env is activated
python main_gui.py
```
## GUI - Live monitoring

* Baseline statistics
    * Requires at least 2 experiments for visualization
    * Live (aggregated) stats
        * Mean packet throughput - TCP (UL/DL) from iperf3
        * Mean packet throughput - UDP from iperf3
        * Packet RTT & Jitter from icmp ping

* Application-specific statistics
    * Requires at least 2 experiments for visualization
    * Live (aggregated) stats
        * Mean throughput for each application
        * Mean RTT for each application
        
* Event log
    * Shows information in regards to the campaign's progress       

* Save stats button
    * Downloads raw experiment data (packet-level)
    * This might require several mins depending on the experiment's settings

## Results
```python
# Method 1
Download from GUI at client side: "Save stats" button

# Method 2
cd /{GOLDEN_UNIT_ROOT}/golden_unit/ #At client-side
<results are shown in the "db" folder>
```
## Output
### iperf test
* File: iperf.json
* Stats frequency: per iperf experiment

| **Feature**           | **Description**                                                     |
|-----------------------|---------------------------------------------------------------------|
| camp_name             | Measurement campaign name                                           |
| repeat_id             | Repetition ID (if campaign is repeated)                             |
| exp_id                | Campaign's experiment ID (if campaign includes several experiments) |
| timestamp             | UNIX timestamp of the measurement                                   |
| tcp_dl_retransmits    | iperf TCP Downlink - # retransmissions                              |
| tcp_dl_sent_bps       | iperf TCP Downlink - sent rate (bps)                                |
| tcp_dl_sent_bytes     | iperf TCP Downlink - sent payload (bytes)                           |
| tcp_dl_received_bps   | iperf TCP Downlink - received rate (bps)                            |
| tcp_dl_received_bytes | iperf TCP Downlink - received payload (bytes)                       |
| tcp_ul_retransmits    | iperf TCP Uplink - # retransmissions                                |
| tcp_ul_sent_bps       | iperf TCP Uplink - sent rate (bps)                                  |
| tcp_ul_sent_bytes     | iperf TCP Uplink - sent payload (bytes)                             |
| tcp_ul_received_bps   | iperf TCP Uplink - received rate (bps)                              |
| tcp_ul_received_bytes | iperf TCP Uplink - received payload (bytes)                         |
| udp_dl_bytes          | iperf UDP Downlink - payload (bytes)                                |
| udp_dl_bps            | iperf UDP Downlink - rate (bps)                                     |
| udp_dl_jitter_ms      | iperf UDP Downlink - jitter (ms)                                    |
| udp_dl_lost_percent   | iperf UDP Downlink - lost packet percentage (%)                     |
| udp_ul_bytes          | iperf UDP Uplink - payload (bytes)                                  |
| udp_ul_bps            | iperf UDP Uplink - rate (bps)                                       |
| udp_ul_jitter_ms      | iperf UDP Uplink - jitter (ms)                                      |
| udp_ul_lost_percent   | iperf UDP Uplink - lost packet percentage (%)                       |


### icmp ping test
* File: icmp.json
* Stats frequency: per icmp experiment

| **Feature**           | **Description**                                                     |
|-----------------------|---------------------------------------------------------------------|
| camp_name             | Measurement campaign name                                           |
| repeat_id             | Repetition ID (if campaign is repeated)                             |
| exp_id                | Campaign's experiment ID (if campaign includes several experiments) |
| timestamp             | UNIX timestamp of the measurement                                   |
| min_rtt_ms            | minimum round-trip-time of all packets (ms)                              |
| avg_rtt_ms            | average round-trip-time of all packets (ms)
| max_rtt_ms            | maximum round-trip-time of all packets (ms)                          |
| rtts_ms               | round-trip-times for all packets (ms)                            |
| packets_sent          | total packets sent                       |
| packets_received      | total packets received
| packet_loss_0to1      | packet loss ratio (minimum 0, maximum 1)                                  |
| jitter_ms             | total jitter (standard deviation of rtt in ms)                             |

### udp ping test
* File: udpping.json
* Stats frequency: per packet

| **Feature**           | **Description**                                                     |
|-----------------------|---------------------------------------------------------------------|
| camp_name             | Measurement campaign name                                           |
| repeat_id             | Repetition ID (if campaign is repeated)                             |
| exp_id                | Campaign's experiment ID (if campaign includes several experiments) |
| timestamp             | UNIX timestamp of the measurement                                   |
| seq_nr                | sequency (packet) number                             |
| send_time             | send timestamp
| server_time           | server timestamp                          |
| receive_time          | receive timestamp                            |
| client2server_ns      | client-to-server delay (ns)                       |
| server2client_ns      | server-to-client delay (ns)
| rtt_ns                | round-trip delay (ns)                                  |
  
### owamp test
* File: owamp.json
* Stats frequency: per packet

| **Feature**           | **Description**                                                     |
|-----------------------|---------------------------------------------------------------------|
| camp_name             | Measurement campaign name                                           |
| repeat_id             | Repetition ID (if campaign is repeated)                             |
| exp_id                | Campaign's experiment ID (if campaign includes several experiments) |
| timestamp             | UNIX timestamp of the measurement                                   |
| seq_nr                | sequence number (unsigned long)                           |
| tx_time             | sendtime (owptimestamp - PRIu64)
| tx_sync           | send synchronized flag   (boolean unsigned)                     |
| tx_err_perc          | send err estimate   (float %)                            |
| rx_time      | recvtime (owptimestamp - PRIu64)                       |
| rx_sync      | recv synchronized flag  (boolean unsigned)
| rx_err_perc      |  recv err estimate   (float %)
| ttl                | ttl (unsigned short)                                 |
| direction                | direction (ul/dl) aka client to/from server   (string)                                  |

### twamp test
* File: owamp.json
* Stats frequency: per packet

| **Feature**           | **Description**                                                     |
|-----------------------|---------------------------------------------------------------------|
| camp_name             | Measurement campaign name                                           |
| repeat_id             | Repetition ID (if campaign is repeated)                             |
| exp_id                | Campaign's experiment ID (if campaign includes several experiments) |
| timestamp             | UNIX timestamp of the measurement                                   |
| tx_seq_nr                | send sequence number (unsigned long)                          |
| tx_time                | sendtime (owptimestamp - PRIu64)                          |
| tx_sync                | send synchronized flag (boolean unsigned)                          |
| tx_err_perc                | send err estimate (float %)                          |
| tx_rx_time                | send (receive) time (owptimestamp - PRIu64)                          |
| tx_rx_sync                | send (receive) synchronized flag (boolean unsigned)                          |
| tx_rx_err_perc                | send (receive) err estimate (float %)                          |
| tx_ttl                | send ttl (unsigned short)                          |
| reflect_seq_nr                | reflect sequence number (unsigned long)                          |
| reflect_tx_time                | reflected (send) time (owptimestamp - PRIu64)                          |
| reflect_tx_sync                | reflected (send) synchronized (boolean unsigned)                          |
| reflect_tx_err_perc                | reflected (send) err estimate (float %)                          |
| rx_time                | recvtime (owptimestamp - PRIu64)                          |
| rx_sync                | recv synchronized flag (boolean unsigned)                          |
| rx_err_perc                | recv err estimate (float %g)                          |
| reflect_ttl                | reflected ttl  (unsigned short)                          |

### application-based tests
* File: app.json
* Stats frequency: per application per packet

| **Feature**           | **Description**                                                     |
|-----------------------|---------------------------------------------------------------------|
| camp_name             | Measurement campaign name                                           |
| repeat_id             | Repetition ID (if campaign is repeated)                             |
| exp_id                | Campaign's experiment ID (if campaign includes several experiments) |
| timestamp             | UNIX timestamp of the measurement                                   |
| app_name                | application name (string)                          |
| pack_id                | packet id (wireshark)                        |
| sniff_time                | sniffing time (wireshark)                        |
| sniff_timestamp                | sniffing timestamp (wireshark)                        |
| protocol                | packet protocol (TCP, UDP, ICMP, etc.)                        |
| pack_len_bytes                | packet length (bytes)                        |
| addr_src                | source IP address                        |
| port_src                | source port                        |
| addr_dest                | destination IP address                        |
| port_dest                | destination port                        |
| rtt                | round-trip-time (sec)|
| drop_flag                | if packet is lost (boolean)|

* File: gui_app.json
* Stats frequency: per experiment (aggregated app statistics)

| **Feature**           | **Description**                                                     |
|-----------------------|---------------------------------------------------------------------|
| RTT (msec)             | Mean Round-trip-time of all application packets (msec)                                           |
| app_name             | Application name                             |
| Throughput (Mbps)    | Application throughput during the experiment(Mbps) |
| timestamp            | Measurement UNIX timestamp                                   |


### physical layer test
* File: phy.json
* Stats frequency: serial connection (async w.r.t. to the experiment)

| **Feature**           | **Description**                                                     |
|-----------------------|---------------------------------------------------------------------|
| camp_name             | Measurement campaign name   |  
| timestamp             | UNIX timestamp                                           |
| mode_pref             | RAN mode (LTE/5G)                            |
| oper             | Operator                           |
| act             | Operator response                            |
| apn             | APN                            |
| resp1             | APN response                            |
| rssi             | RSSI                            |
| ber             | Bit-error rate                            |
| qrsrp_prx             | QRSRP                            |
| qrsrp_drx             | QRSRP                            |
| qrsrp_rx2             | QRSRP                            |
| qrsrp_rx3             | QRSRP                            |
| qrsrp_sysmode             | QRSRP                            |
| rsrq_prx             | RSRQ                            |
| rsrq_drx             | RSRQ                            |
| rsrq_rx2             | RSRQ                            |
| rsrq_rx3             | RSRQ                            |
| rsrq_sysmode             | RSRQ                            |
| sinr_prx             | SINR                            |
| sinr_drx             | SINR                            |
| sinr_rx2             | SINR                            |
| sinr_rx3             | SINR                            |
| sinr_sysmode             | SINR                            |
| net_info             | Network param info                            |
| serving_cell_info             | Serving cell param info                            |


* File: phy_raw.json
* Raw responses of the modem's AT cmds

### input user settings
* File: in_user.json

### campaign log file
* File: out_log.json

## Tools repository
* https://docs.perfsonar.net/manage_regular_tests.html
* https://github.com/perfsonar/owamp
* https://github.com/nokia/twampy
* https://github.com/emirica/twamp-protocol
* https://github.com/perfsonar/toolkit
* https://data.mendeley.com/datasets/8cjkkw79z2/1
* https://github.com/sonata-nfv/tng-sdk-benchmark
* https://github.com/EricssonResearch/udp-ping
* https://github.com/rtlabs-com/p-net
