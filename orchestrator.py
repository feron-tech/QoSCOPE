import time
import docker
import socket
from helper import Helper
import gparams
class Orchestrator:
	def __init__(self):
		self.orch = docker.from_env()
		self.helper=Helper()
	def get_all_ifaces(self):
		final_list = []
		list_of_tuples = socket.if_nameindex()
		for tuple in list_of_tuples:
			try:
				final_list.append(tuple[1])
			except:
				pass
		return final_list

	def clean_all(self):
		# todo
		pass

	def activate(self,image,detach=True,env=None,network_mode='bridge',port_dict=None):
		try:
			print('(Orch) DBG: Activation...')
			initial_list_of_ifaces=self.get_all_ifaces()

			if env is None:
				if port_dict is None:
					self.orch.containers.run(image, detach=detach, remove=True, network_mode=network_mode)
				else:
					self.orch.containers.run(image, detach=detach, remove=True,
					                         network_mode=network_mode,ports=port_dict)
			else:
				if port_dict is None:
					self.orch.containers.run(image, detach=detach, remove=True, network_mode=network_mode, environment=env)
				else:
					self.orch.containers.run(image, detach=detach, remove=True,
					                         network_mode=network_mode, environment=env,ports=port_dict)

			print('(Orch) DBG: Activated container OK')

			attempt=1
			res=None
			while (res is None):
				print('(Orch) DBG: Seaching for iface (attempt=' + str(attempt) + ')...')

				if attempt > 1:
					self.helper.wait(gparams._WAIT_SEC_BACKEND_READ_INPUT_SOURCES)

				final_list_of_ifaces=self.get_all_ifaces()
				for final_iface in final_list_of_ifaces:
					if (final_iface not in initial_list_of_ifaces) and ('veth' in final_iface):
						res=final_iface
						print('(Orch) DBG: Iface found='+str(res))
						break

				attempt = attempt + 1

				if attempt >= gparams._ATTEMPTS_BACKEND_READ_INPUT_SOURCES:
					print('(Orch) ERROR: Cannot find iface during activation!')
					return None
			return res
		except Exception as ex:
			print('(Orch) ERROR: Failed to activate container=' + str(ex))
			return None

	def deactivate_old(self,image):
		try:
			print('(Orch) DBG: Container deactivation...')
			initial_list_of_ifaces = self.get_all_ifaces()

			found=False
			container_list=self.orch.containers.list()
			for cont in container_list:
				if cont.attrs['Config']['Image']==image:
					cont.stop()
					found=True
					print('(Orch) DBG: De-activated container OK!')
					return 200
			if not found:
				print('(Orch) ERROR: Failed to find image during container dactivation, image=' + str(image))
				return None

			attempt = 1
			res = None
			while (res is None):
				print('(Orch) DBG: Seaching for iface (attempt=' + str(attempt) + ')...')

				if attempt > 1:
					self.helper.wait(gparams._WAIT_SEC_BACKEND_READ_INPUT_SOURCES)

				final_list_of_ifaces = self.get_all_ifaces()
				for init_iface in initial_list_of_ifaces:
					if (init_iface not in final_list_of_ifaces) and ('veth' in init_iface):
						res = init_iface
						print('(Orch) DBG: Iface found=' + str(res))
						break

				attempt = attempt + 1

				if attempt >= gparams._ATTEMPTS_BACKEND_READ_INPUT_SOURCES:
					print('(Orch) ERROR: Cannot find iface during DE-activation!')
					return None
			return res

		except Exception as ex:
			print('(Orch) ERROR: Failed to de-activate container=' + str(ex))
			return None

	def misc(self):
		#container.attrs['Config']['Image']
		#orch.images.pull('nginx')
		#orch.images.list()
		pass






import subprocess
import threading
import time

class VethOrchestrator:
    def __init__(self):
        self.ns_name = None
        self.veth_host = None
        self.veth_ns = None
        self.stop_event = threading.Event()
        self.monitor_thread = None

    def run(self, cmd, check=True):
        print(f"[CMD] {' '.join(cmd)}")
        subprocess.run(cmd, check=check)

    def create_namespace(self, ns_name, veth_host, veth_ns, host_ip, ns_ip, wwan_if):
        self.ns_name = ns_name
        self.veth_host = veth_host
        self.veth_ns = veth_ns
        self.host_ip = host_ip
        self.ns_ip = ns_ip
        self.wwan_if = wwan_if

        # Cleanup existing
        subprocess.run(["ip", "netns", "del", ns_name], stderr=subprocess.DEVNULL)
        subprocess.run(["ip", "link", "del", veth_host], stderr=subprocess.DEVNULL)

        # Create netns and veth pair
        self.run(["ip", "netns", "add", ns_name])
        self.run(["ip", "link", "add", veth_host, "type", "veth", "peer", "name", veth_ns])

        self.run(["ip", "addr", "add", f"{host_ip}/24", "dev", veth_host])
        self.run(["ip", "link", "set", veth_host, "up"])

        self.run(["ip", "link", "set", veth_ns, "netns", ns_name])
        self.run(["ip", "netns", "exec", ns_name, "ip", "addr", "add", f"{ns_ip}/24", "dev", veth_ns])
        self.run(["ip", "netns", "exec", ns_name, "ip", "link", "set", veth_ns, "up"])
        self.run(["ip", "netns", "exec", ns_name, "ip", "link", "set", "lo", "up"])
        self.run(["ip", "netns", "exec", ns_name, "ip", "route", "add", "default", "via", host_ip])

        self.run(["sysctl", "-w", "net.ipv4.ip_forward=1"])

        # Setup NAT masquerade and forwarding rules
        check_rule = subprocess.run(
            ["iptables", "-t", "nat", "-C", "POSTROUTING", "-s", f"{ns_ip}/24", "-o", wwan_if, "-j", "MASQUERADE"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if check_rule.returncode != 0:
            self.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", f"{ns_ip}/24", "-o", wwan_if, "-j", "MASQUERADE"])
        self.run(["iptables", "-I", "FORWARD", "1", "-i", veth_host, "-o", wwan_if, "-j", "ACCEPT"])
        self.run(["iptables", "-I", "FORWARD", "1", "-i", wwan_if, "-o", veth_host, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"])

    def cleanup(self):
        print("[*] Cleaning up...")
        if self.ns_name:
            subprocess.run(["ip", "netns", "del", self.ns_name], stderr=subprocess.DEVNULL)
        if self.veth_host:
            subprocess.run(["ip", "link", "del", self.veth_host], stderr=subprocess.DEVNULL)
        if self.ns_ip and self.wwan_if:
            subprocess.run(["iptables", "-t", "nat", "-D", "POSTROUTING", "-s", f"{self.ns_ip}/24", "-o", self.wwan_if, "-j", "MASQUERADE"], stderr=subprocess.DEVNULL)
        # Remove forwarding rules ignoring errors
        subprocess.run(["iptables", "-D", "FORWARD", "-i", self.veth_host, "-o", self.wwan_if, "-j", "ACCEPT"], stderr=subprocess.DEVNULL)
        subprocess.run(["iptables", "-D", "FORWARD", "-i", self.wwan_if, "-o", self.veth_host, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"], stderr=subprocess.DEVNULL)

    def read_bytes(self, interface):
        try:
            with open(f"/sys/class/net/{interface}/statistics/rx_bytes") as f:
                rx = int(f.read())
            with open(f"/sys/class/net/{interface}/statistics/tx_bytes") as f:
                tx = int(f.read())
            return rx, tx
        except Exception as e:
            print(f"[!] Error reading stats for {interface}: {e}")
            return None, None

    def monitor_traffic(self):
        print(f"[*] Starting traffic monitor on {self.veth_host}")
        prev_rx, prev_tx = self.read_bytes(self.veth_host)
        if prev_rx is None:
            print(f"[!] Cannot monitor traffic on {self.veth_host} because stats are unavailable")
            return

        while not self.stop_event.is_set():
            time.sleep(1)
            curr_rx, curr_tx = self.read_bytes(self.veth_host)
            if curr_rx is None:
                print(f"[!] Stopping traffic monitor on {self.veth_host}")
                break
            rx_rate = (curr_rx - prev_rx) / 1024  # KB/s
            tx_rate = (curr_tx - prev_tx) / 1024
            print(f"[App running - Traffic] RX: {rx_rate:.2f} KB/s, TX: {tx_rate:.2f} KB/s")
            prev_rx, prev_tx = curr_rx, curr_tx

    def activate(self, client_app_cmd, env=None):
        if not all([self.ns_name, self.veth_host, self.veth_ns]):
            raise Exception("Namespace and veth interfaces not set up. Call create_namespace() first.")

        # Prepare environment variables as inline command if env provided
        env_str = ''
        if env:
            env_str = ' '.join(f'{k}="{v}"' for k,v in env.items())

        # Build full command string to run in namespace with env vars
        cmd = f"ip netns exec {self.ns_name} env {env_str} {client_app_cmd}" if env_str else f"ip netns exec {self.ns_name} {client_app_cmd}"
        print(f"[*] Running client app: {cmd}")

        # Start traffic monitor thread
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self.monitor_traffic, daemon=True)
        self.monitor_thread.start()

        # Run client app (blocking)
        proc = subprocess.Popen(cmd, shell=True)

        return proc

    def deactivate(self, proc):
        print("[*] Deactivating client app and cleaning up")
        if proc:
            proc.terminate()
            proc.wait()
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join()
        self.cleanup()
