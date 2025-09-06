import subprocess
import time
import threading
import signal
import sys
import os

NS_NAME = "appns"
VETH_HOST = "veth-host"
VETH_NS = "veth-ns"
HOST_IP = "10.200.1.1"
NS_IP = "10.200.1.2"
WWAN_IF = "wwan0"

MQTT_CLIENT_SCRIPT = "client_app_mqtt.py"  # adjust path as needed
PYTHON_EXEC = sys.executable  # Use current python (conda env)

# MQTT client args example (replace with your target)
MQTT_ARGS = ["172.25.2.172", "1883", "1", "1000"]

stop_event = threading.Event()

def run(cmd, check=True):
    print(f"[CMD] {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=check)
    except subprocess.CalledProcessError as e:
        print(f"[!] Command failed: {' '.join(cmd)}")
        print(f"    Return code: {e.returncode}")
        if e.output:
            print(f"    Output: {e.output.decode()}")
        if check:
            raise e

def add_forwarding_rules():
    # Insert ACCEPT rules at top of FORWARD chain for traffic between veth-host and wwan0
    run(["iptables", "-I", "FORWARD", "1", "-i", VETH_HOST, "-o", WWAN_IF, "-j", "ACCEPT"], check=False)
    run(["iptables", "-I", "FORWARD", "1", "-i", WWAN_IF, "-o", VETH_HOST, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"], check=False)

def remove_forwarding_rules():
    # Remove the ACCEPT rules inserted earlier; ignore errors if rules not found
    subprocess.run(["iptables", "-D", "FORWARD", "-i", VETH_HOST, "-o", WWAN_IF, "-j", "ACCEPT"], stderr=subprocess.DEVNULL)
    subprocess.run(["iptables", "-D", "FORWARD", "-i", WWAN_IF, "-o", VETH_HOST, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"], stderr=subprocess.DEVNULL)

def cleanup():
    print("[*] Cleaning up...")
    subprocess.run(["ip", "netns", "del", NS_NAME], stderr=subprocess.DEVNULL)
    subprocess.run(["ip", "link", "del", VETH_HOST], stderr=subprocess.DEVNULL)
    subprocess.run(["iptables", "-t", "nat", "-D", "POSTROUTING", "-s", f"{NS_IP}/24", "-o", WWAN_IF, "-j", "MASQUERADE"], stderr=subprocess.DEVNULL)
    remove_forwarding_rules()

def check_interface_exists(interface):
    try:
        subprocess.check_output(["ip", "link", "show", interface], stderr=subprocess.STDOUT)
        print(f"[+] Interface {interface} exists.")
        return True
    except subprocess.CalledProcessError:
        print(f"[!] Interface {interface} does NOT exist.")
        return False

def check_namespace_exists(ns_name):
    try:
        output = subprocess.check_output(["ip", "netns", "list"], stderr=subprocess.STDOUT).decode()
        if ns_name in output:
            print(f"[+] Namespace {ns_name} exists.")
            return True
        else:
            print(f"[!] Namespace {ns_name} does NOT exist.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to list namespaces: {e}")
        return False

def setup_namespace():
    cleanup()

    run(["ip", "netns", "add", NS_NAME])

    if not check_namespace_exists(NS_NAME):
        raise RuntimeError("Namespace creation failed")

    run(["ip", "link", "add", VETH_HOST, "type", "veth", "peer", "name", VETH_NS])

    if not (check_interface_exists(VETH_HOST) and check_interface_exists(VETH_NS)):
        raise RuntimeError("veth pair creation failed")

    run(["ip", "addr", "add", f"{HOST_IP}/24", "dev", VETH_HOST])
    run(["ip", "link", "set", VETH_HOST, "up"])

    run(["ip", "link", "set", VETH_NS, "netns", NS_NAME])

    run(["ip", "netns", "exec", NS_NAME, "ip", "addr", "add", f"{NS_IP}/24", "dev", VETH_NS])
    run(["ip", "netns", "exec", NS_NAME, "ip", "link", "set", VETH_NS, "up"])

    run(["ip", "netns", "exec", NS_NAME, "ip", "link", "set", "lo", "up"])

    run(["ip", "netns", "exec", NS_NAME, "ip", "route", "add", "default", "via", HOST_IP])

    run(["sysctl", "-w", "net.ipv4.ip_forward=1"])

    # Add NAT masquerade rule if not already present
    check_rule = subprocess.run(
        ["iptables", "-t", "nat", "-C", "POSTROUTING", "-s", f"{NS_IP}/24", "-o", WWAN_IF, "-j", "MASQUERADE"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if check_rule.returncode != 0:
        run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", f"{NS_IP}/24", "-o", WWAN_IF, "-j", "MASQUERADE"])

    # Add forwarding ACCEPT rules
    add_forwarding_rules()

def read_bytes(interface):
    try:
        with open(f"/sys/class/net/{interface}/statistics/rx_bytes") as f:
            rx = int(f.read())
        with open(f"/sys/class/net/{interface}/statistics/tx_bytes") as f:
            tx = int(f.read())
        return rx, tx
    except Exception as e:
        print(f"[!] Error reading stats for {interface}: {e}")
        return None, None

def monitor_traffic(interface):
    print(f"[*] Starting traffic monitor on {interface}")
    prev_rx, prev_tx = read_bytes(interface)
    if prev_rx is None:
        print(f"[!] Cannot monitor traffic on {interface} because stats are unavailable")
        return

    while not stop_event.is_set():
        time.sleep(1)
        curr_rx, curr_tx = read_bytes(interface)
        if curr_rx is None:
            print(f"[!] Stopping traffic monitor on {interface}")
            break
        rx_rate = (curr_rx - prev_rx) / 1024  # KB/s
        tx_rate = (curr_tx - prev_tx) / 1024
        print(f"[Traffic] RX: {rx_rate:.2f} KB/s, TX: {tx_rate:.2f} KB/s")
        prev_rx, prev_tx = curr_rx, curr_tx

def run_mqtt_client():
    cmd = ["ip", "netns", "exec", NS_NAME, PYTHON_EXEC, MQTT_CLIENT_SCRIPT] + MQTT_ARGS
    print(f"[*] Running MQTT client: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def signal_handler(sig, frame):
    print("[*] Signal received, stopping...")
    stop_event.set()
    cleanup()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        setup_namespace()
    except Exception as e:
        print(f"[!] Namespace setup failed: {e}")
        cleanup()
        sys.exit(1)

    monitor_thread = threading.Thread(target=monitor_traffic, args=(VETH_HOST,), daemon=True)
    monitor_thread.start()

    try:
        run_mqtt_client()
    except subprocess.CalledProcessError as e:
        print(f"[!] MQTT client error: {e}")
    finally:
        stop_event.set()
        monitor_thread.join()
        cleanup()

if __name__ == "__main__":
    main()
